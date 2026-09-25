from arango.database import StandardDatabase

from app.common.types import UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.erasure_executor import ArangoErasureExecutor
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.user import User


class ArangoUserRepository(BaseArangoRepository[User], IUserRepository):
    _model_cls = User

    #: Full-replace null semantics for ``users`` (#1525, the #1516 class).
    #:
    #: **What it repairs.** In the inherited merge mode a field a writer set to
    #: ``None`` is dropped from the payload and the stored value survives. Three
    #: consequences, all of them credential-bearing:
    #:
    #: * ``UserService.delete_account`` nulls ``password_hash`` and ``avatar_url``
    #:   while ``is_active``/``email``/``display_name`` *are* written — the record
    #:   reads as deleted and keeps the bcrypt hash.
    #: * ``PrivacyService.request_erasure`` nulls ``password_hash`` on the DSGVO
    #:   Art. 17 path, 90 days before the hard delete runs (NFR-011 R-01).
    #: * :meth:`update_fields` is **not** a ``keep_none=True`` path here — the
    #:   override below re-materialises a full ``User`` and goes through
    #:   :meth:`BaseArangoRepository.update`, so every ``None`` in ``fields`` was
    #:   dropped too. That silently defeated ``AuthService.reset_password`` and
    #:   ``change_password``, which clear ``password_reset_token`` /
    #:   ``password_reset_expires`` and say in a comment that they rely on the
    #:   explicit ``None`` being persisted: a used reset token stayed valid for its
    #:   full hour, and ``verify_email`` likewise could not burn its token.
    #:
    #: **Why the flag and not a per-call ``update_fields``.** No writer of ``users``
    #: can lose a field it never mentioned, because every one of them goes through
    #: :meth:`update_fields`, which re-reads the stored user inside the call and
    #: applies ``model_copy(update=fields)`` to it (re-measured 2026-09-18 over every
    #: call site; the grep is ``user_repo.update`` / ``update_fields`` plus the check
    #: that nothing writes ``col.USERS`` through the driver). ``fields`` is an
    #: explicit allow-list everywhere, so a ``None`` in it is an intended clear:
    #:
    #: * ``UserService.update_profile`` / ``delete_account`` / ``admin_update_user``
    #: * ``PrivacyService.confirm_email_change`` / ``request_erasure``
    #: * the seven ``AuthService`` sites (login success/failure, verify_email,
    #:   request/reset password, change_password, OAuth login)
    #:
    #: Those first four used to hand over a **full model** read at the top of their
    #: method. #1525 SCR-003 narrowed them, because full-replace makes that shape
    #: strictly worse than it was: a stale snapshot no longer merely *loses* a field a
    #: parallel request set in between, it **removes** the attribute — and the field
    #: in question is typically ``password_reset_token`` or ``locked_until``.
    #:
    #: The alternative — routing those clears through a second
    #: ``update_fields(..., keep_none=True)`` write at each call site — is the #948
    #: class: a guard opted into per call site, which the next writer does not opt
    #: into. This flag is a property of the collection.
    #:
    #: **Residual risk, stated rather than implied.** :meth:`update_fields` is itself
    #: read-modify-write (#1018), so it is *not* the base class's commuting partial
    #: update: two concurrent calls naming disjoint fields still serialise on the full
    #: document and the loser's field can be lost. Narrowing shrank the window from
    #: "one request, across a bcrypt verify" to "one repository call"; it did not
    #: close it. A genuinely commuting write for ``users`` needs a partial AQL
    #: ``UPDATE ... WITH`` that keeps the model re-validation #1018 came for — filed
    #: as its own issue rather than smuggled in here.
    #:
    #: Full-replace is still a *merge* at the storage level: an attribute the model
    #: does not declare (``tenant_key`` from the backfill, legacy attributes) keeps
    #: its stored value. Only an explicit ``None`` removes its attribute.
    #:
    #: ``tests/integration/test_merge_mode_null_clearing.py`` measures this against a
    #: real server.
    _update_is_full_replace = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.USERS)

    def update_fields(self, key: UserKey, fields: dict) -> User | None:
        """Merge ``fields`` into the stored user and rewrite it (#1018, mirrors #968 §2).

        Read-modify-write, exactly like :meth:`ArangoTenantRepository.update_fields`:
        the stored ``User`` is loaded, ``fields`` is applied through
        ``model_copy(update=...)`` and the merged model is written via the
        inherited full-model :meth:`update`, which re-validates it in ``_to_doc``
        (#982/#996), strips ArangoDB system attributes and maps a 1202 onto
        :class:`NotFoundError`. That is the set of guards the platform-admin
        router bypassed by writing ``collection.update`` itself (#1018).

        **Caller obligation.** ``fields`` is applied key-by-key, so it must be
        built from named fields or a validated schema's ``model_dump()`` — never
        from a raw request body.

        **A ``None`` in ``fields`` clears the stored attribute.** Because this
        override goes through the full-model :meth:`update`, the base class's
        ``keep_none=True`` merge does *not* apply here; the null semantics are the
        ones :attr:`_update_is_full_replace` declares. Until #1525 that flag was
        ``False``, so an explicit ``None`` was dropped and the clears in
        ``AuthService.reset_password`` / ``change_password`` / ``verify_email``
        never reached the store.

        Deliberately not the base class's dict-merge :meth:`update_fields`, which
        writes the dict straight through unchecked; materialising a full ``User``
        here is what gets the payload validated. The price is that method's
        lost-update commutativity for disjoint concurrent fields.

        Returns ``None`` when no user carries ``key``.
        """
        existing = self.get_by_key(key)
        if not existing:
            return None
        merged = existing.model_copy(update=fields)
        return super().update(key, merged)

    def get_by_email(self, email: str) -> User | None:
        query = "FOR doc IN @@collection FILTER LOWER(doc.email) == LOWER(@email) LIMIT 1 RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.USERS, "email": email})
        docs = list(cursor)
        if not docs:
            return None
        return User(**self._from_doc(docs[0]))

    def get_by_email_verification_token(self, token: str) -> User | None:
        """The user carrying this email-verification token, or ``None`` (#1556).

        Was hand-written AQL inside ``AuthService.verify_email``, executed against
        ``self._user_repo._db`` — NFR-001's Business Logic → Data Access →
        Persistence with the middle layer skipped, and the
        ``# type: ignore[attr-defined]`` was the type checker saying so.

        Conversion is ``User(**self._from_doc(doc))``, the same one
        :meth:`get_by_email` uses. That is *identical* to the ``{**doc, "_key":
        doc.get("_key", doc.get("_id", "").split("/")[-1])}`` the service spelled
        out by hand, so this move changes no behaviour — it is a layering repair,
        not a validation repair.
        """
        return self._get_by_token("email_verification_token", token)

    def get_by_password_reset_token(self, token: str) -> User | None:
        """The user carrying this password-reset token, or ``None`` (#1556).

        The reset-path twin of :meth:`get_by_email_verification_token`.
        """
        return self._get_by_token("password_reset_token", token)

    def _get_by_token(self, attribute: str, token: str) -> User | None:
        """One user by an exact match on a token attribute, or ``None``.

        ``attribute`` is interpolated because AQL cannot bind an attribute name;
        it is a code constant at both call sites and never a caller value.
        ``token`` is bound.

        A ``token`` of ``None`` would otherwise match every user that has no such
        token — the whole collection — and hand the first of them back as if it
        had presented a credential. The callers type it ``str``, which is not an
        enforcement, so the empty case is refused here rather than assumed away.
        """
        if not token:
            return None
        query = f"""
        FOR doc IN @@collection
          FILTER doc.{attribute} == @token
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.USERS, "token": token})
        docs = list(cursor)
        if not docs:
            return None
        return User(**self._from_doc(docs[0]))

    def delete(self, key: UserKey) -> bool:
        """Delete a user and cascade every account-owned artefact (#1019, #1622, #1664).

        Runs the ``account_cascade`` slice of the declared erasure plan through
        :class:`ArangoErasureExecutor` — the same executor the full account
        erasure (:meth:`PrivacyService.erase_account`) uses, so there is one
        walk of the inventory and not two. Until #1664 this method carried its
        own copy of that walk; a second copy is how the #1622 inventories
        drifted.

        This is the *narrow* delete: auth providers, sessions, API keys,
        preferences, onboarding state, memberships with the location assignments
        hanging off them (#1700 — registration creates a membership before the
        address is verified) and the user document. It does not apply the
        anonymisation rules, so the personal tenant registration created keeps
        its owner reference and name. It therefore has **no production caller**:
        every account deletion — the unverified-account cleanup included since
        the #1700 review (``auth_tasks.cleanup_unverified_accounts``) — goes
        through ``PrivacyService.erase_account``. It stays as the
        ``UserRepository`` interface's delete and for tests of the cascade slice.

        Returns whether the user document was removed.
        """
        report = ArangoErasureExecutor(self._db).run_erasure_plan(
            ErasureEngine().build_erasure_plan(key),
            tombstone=None,
            executors=("account_cascade",),
        )
        return report.affected(self._collection_name) > 0

    def list_all(self) -> list[User]:
        """Every user, newest first (platform-admin listing, #1019)."""
        docs = self._find_docs([], sort="created_at", sort_direction="DESC")
        return self._wrap_many(docs)

    def count(self, *, active_only: bool = False) -> int:
        """Number of user documents; ``active_only`` counts ``is_active`` ones (#1019)."""
        if not active_only:
            return self.collection.count()
        query = """
        FOR doc IN @@collection
          FILTER doc.is_active == true
          COLLECT WITH COUNT INTO cnt
          RETURN cnt
        """
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.USERS})
        return next(cursor, 0)

    def get_unverified_before(self, cutoff_iso: str) -> list[User]:
        """Abandoned half-registrations, for `cleanup_unverified_accounts` to purge.

        **An account with a linked federated provider is excluded, and that
        exclusion is load-bearing rather than tidy.** The task this feeds runs
        the full Art. 17 erasure on what it returns (``PrivacyService.erase_account``,
        #1700 review). So a row returned here in error costs the user their
        account, their memberships, and leaves their personal tenant and its
        plant data anonymised and ownerless.

        The predicate used to be `email_verified == false` alone. That was
        survivable only because nothing ever created a federated account in that
        state: `_register_oauth_user` stamped `email_verified=True`
        unconditionally. #1403 made it read the provider's claim instead, which is
        correct — and a provider that omits `email_verified` (GitHub without the
        `user:email` scope, and many OIDC deployments) then produces exactly such
        a row. The reaper would have deleted a working account once the NFR-011
        R-02 period (``RETENTION_UNVERIFIED_ACCOUNT_DAYS``) passed after its owner
        signed in with it.

        The distinction the task actually wants is "can this person still get in?",
        not "did they confirm an address". Someone who signs in through a provider
        can, today and every day after, so they are not an abandoned registration
        whatever `email_verified` says.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc.email_verified == false AND doc.created_at < @cutoff
          LET linked = LENGTH(
            FOR provider IN @@providers
              FILTER provider.user_key == doc._key
              LIMIT 1
              RETURN 1
          )
          FILTER linked == 0
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": col.USERS, "@providers": col.AUTH_PROVIDERS, "cutoff": cutoff_iso},
        )
        return [User(**self._from_doc(doc)) for doc in cursor]
