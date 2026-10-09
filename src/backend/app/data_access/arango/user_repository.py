from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase
from arango.exceptions import AQLQueryExecuteError
from pydantic import BaseModel

from app.common.types import UserKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.erasure_executor import ArangoErasureExecutor
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.user import User

#: An instant comparison (#1784), and a missing or unreadable ``created_at`` selects nothing.
_REGISTERED_BEFORE_CUTOFF = (
    "DATE_TIMESTAMP(doc.created_at) != null AND DATE_TIMESTAMP(doc.created_at) < DATE_TIMESTAMP(@cutoff)"
)

#: The one predicate behind R-02's selector, its dry-run count and its held counter (#2010).
#: Selector and counters share these lines so a counter can never describe a different set than
#: the selector it reports on (AK-14b). ``age`` is the only part that differs between "selected"
#: and "held". A module constant, so the catalogue guard can read the query text.
_UNVERIFIED_QUERY = """
        FOR doc IN @@collection
          FILTER doc.email_verified == false
            AND doc.email_verified_lowered_at == null
            AND doc.last_login_at == null
            AND {age}
          LET linked = LENGTH(
            FOR provider IN @@providers
              FILTER provider.user_key == doc._key{federated_only}
              LIMIT 1
              RETURN 1
          )
          FILTER linked == 0{human_only}{extra}
          {tail}
        """

#: Only the dry-run count: the account has at least one provider row (all of them ``local``).
_HAS_A_PROVIDER_ROW = """
          FILTER LENGTH(
            FOR any_row IN @@providers
              FILTER any_row.user_key == doc._key
              LIMIT 1
              RETURN 1
          ) > 0"""


def _widening(include_local_registrations: bool) -> dict[str, str]:
    """The two fragments (#2010) that narrow R-02's provider exclusion to federated rows."""
    if not include_local_registrations:
        return {"federated_only": "", "human_only": ""}
    return {
        "federated_only": " AND provider.provider != @local_provider",
        "human_only": " AND doc.account_type != 'service'",
    }


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
    #:   ``change_password``, which clear ``password_reset_token_hash`` /
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
    #: in question is typically ``password_reset_token_hash`` or ``locked_until``.
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

    #: Account attributes this repository never writes (#2116). They are owned by
    #: ``ArangoRefreshTokenRepository``, which moves them in the same AQL statement
    #: that revokes the sessions. Every write here is a rewrite of a model read
    #: moments earlier (see ``_update_is_full_replace``), so a writer that read the
    #: account before a "log out everywhere" would otherwise put the old counter
    #: back and revive every access token the revocation ended. Left out of the
    #: payload, the stored value survives any such rewrite (the update is a merge
    #: at the storage level); a new account simply has none, which reads as ``0``.
    _STORE_OWNED_FIELDS: frozenset[str] = frozenset({"session_generation", "access_token_generation"})

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.USERS)

    def _to_doc(self, model: BaseModel, *, exclude_none: bool = True) -> dict[str, Any]:
        """The base serialisation without the session counters (:data:`_STORE_OWNED_FIELDS`)."""
        doc = super()._to_doc(model, exclude_none=exclude_none)
        for name in self._STORE_OWNED_FIELDS:
            doc.pop(name, None)
        return doc

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

    def move_email(self, key: UserKey, expected_email: str, fields: dict) -> User | None:
        """Compare-and-set on the address in one AQL write (#1848).

        The e-mail confirmation and the revert each read the account, check, then
        write it. Two of them racing — a confirmation in flight against the
        owner's revert, or the reverts of two chained changes — both saw the
        address they expected; this write lands only for the one whose
        expectation still holds. ``fields`` is a fixed, named set (address,
        verified flag, cleared reset token), so the partial ``UPDATE`` needs none
        of :meth:`update_fields`' model re-validation; ``keepNull`` makes a
        ``None`` clear its attribute, as the full-replace mode of this collection
        does.
        """
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key AND LOWER(doc.email) == LOWER(@expected)
          UPDATE doc WITH MERGE(@fields, { updated_at: @now }) IN @@collection OPTIONS { keepNull: true }
          RETURN NEW
        """
        try:
            cursor = self._db.aql.execute(
                query,
                bind_vars={
                    "@collection": col.USERS,
                    "key": key,
                    "expected": expected_email,
                    "fields": fields,
                    "now": self._now(),
                },
            )
        except AQLQueryExecuteError as exc:
            mapped = self._mapped_insert_error(exc, col.USERS, fields)
            if mapped is not None:
                raise mapped from exc
            raise
        docs = list(cursor)
        return User(**self._from_doc(docs[0])) if docs else None

    def get_by_email(self, email: str) -> User | None:
        query = "FOR doc IN @@collection FILTER LOWER(doc.email) == LOWER(@email) LIMIT 1 RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars={"@collection": col.USERS, "email": email})
        docs = list(cursor)
        if not docs:
            return None
        return User(**self._from_doc(docs[0]))

    def get_by_email_verification_token_hash(self, token_hash: str) -> User | None:
        """The user carrying this email-verification token digest, or ``None`` (#1556, #2158).

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
        return self._get_by_token("email_verification_token_hash", token_hash)

    def get_by_password_reset_token_hash(self, token_hash: str) -> User | None:
        """The user carrying this password-reset token digest, or ``None`` (#1556, #2158).

        The reset-path twin of :meth:`get_by_email_verification_token_hash`.
        """
        return self._get_by_token("password_reset_token_hash", token_hash)

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

    def list_all(self, *, offset: int | None = None, limit: int | None = None) -> list[User]:
        """Users, newest first (platform-admin listing, #1019).

        ``offset``/``limit`` read one window (MT-035, #2131); both ``None`` reads
        every user. ``_key`` breaks ``created_at`` ties so pages never overlap.
        """
        docs = self._find_docs(
            [], sort="created_at", sort_direction="DESC", offset=offset, limit=limit, tiebreak_key=True
        )
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

    def get_unverified_before(self, cutoff_iso: str, *, include_local_registrations: bool = False) -> list[User]:
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

        **A demoted account is excluded too (#1992).** ``email_verified_lowered_at`` is
        stamped when an administrator lowers ``email_verified`` on a verified account.
        Such an account was verified once and is established; ``email_verified == false``
        alone made one ``PATCH`` enough to hand it to this reaper. The marker is the
        record of that transition, so the selector never treats it as abandoned. A
        demotion made before the marker existed left no record; ``last_login_at`` is
        the second, conservative signal for those: an account that ever signed in is
        in use, whatever ``email_verified`` says now.

        The distinction the task actually wants is "can this person still get in?",
        not "did they confirm an address". Someone who signs in through a provider
        can, today and every day after, so they are not an abandoned registration
        whatever `email_verified` says.

        **A locally registered account is excluded by default, and that is the
        measured gap of #2010.** Registration writes a ``LOCAL`` ``auth_providers`` row
        for every account, and by default *any* provider row counts as linked, so the
        default selector reaches provider-less accounts only (seeds, imports, legacy
        rows). ``include_local_registrations=True`` narrows the exclusion to federated
        rows (``provider != 'local'``): an abandoned local registration is then
        selected too. Widening also drops ``account_type == 'service'`` (a machine
        account has no mailbox to confirm). The caller widens only after the operator
        has seen the dry-run count (:meth:`count_unverified_local_registrations_before`).

        ``created_at`` is compared as an instant (#1784, see
        :mod:`app.data_access.arango.query_builder`); an account whose creation
        time is missing or unreadable is not selected — its age is unknown, and
        every account this returns is erased.
        """
        query = _UNVERIFIED_QUERY.format(
            age=_REGISTERED_BEFORE_CUTOFF, extra="", tail="RETURN doc", **_widening(include_local_registrations)
        )
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.USERS,
                "@providers": col.AUTH_PROVIDERS,
                "cutoff": cutoff_iso,
                **self._local_bind(include_local_registrations),
            },
        )
        return [User(**self._from_doc(doc)) for doc in cursor]

    @staticmethod
    def _local_bind(include_local_registrations: bool) -> dict[str, str]:
        return {"local_provider": "local"} if include_local_registrations else {}

    def count_unverified_local_registrations_before(self, cutoff_iso: str) -> int:
        """Dry run (#2010): abandoned local registrations the widened selector would add.

        Exactly the accounts ``get_unverified_before(cutoff, include_local_registrations=True)``
        returns beyond the default selector — those with at least one provider row, all of
        them ``local``. Nothing is erased by counting; the number is what the operator reads
        before releasing the real run.
        """
        query = _UNVERIFIED_QUERY.format(
            age=_REGISTERED_BEFORE_CUTOFF,
            extra=_HAS_A_PROVIDER_ROW,
            tail="COLLECT WITH COUNT INTO pending RETURN pending",
            **_widening(True),
        )
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                query,
                bind_vars={
                    "@collection": col.USERS,
                    "@providers": col.AUTH_PROVIDERS,
                    "cutoff": cutoff_iso,
                    **self._local_bind(True),
                },
            ),
        )
        return int(next(iter(cursor), 0))

    def count_unverified_undated(self, *, include_local_registrations: bool = False) -> int:
        """Unverified, unlinked accounts that :meth:`get_unverified_before` can never select (#1806 GDPR-003).

        The R-02 selector skips an account whose ``created_at`` is missing or
        unreadable — its age is unknown and everything it returns is erased, so
        skipping is the safe side. The price is that such a row is held for ever
        without anyone being told. This counts exactly those rows (same predicate
        as the selector, with the date test inverted, and the same
        ``include_local_registrations`` so it describes the selector actually in
        use, #2010) so the task can report the number next to its other counters,
        like R-06's ``held_without_tombstone``.
        """
        query = _UNVERIFIED_QUERY.format(
            age="DATE_TIMESTAMP(doc.created_at) == null",
            extra="",
            tail="COLLECT WITH COUNT INTO held RETURN held",
            **_widening(include_local_registrations),
        )
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                query,
                bind_vars={
                    "@collection": col.USERS,
                    "@providers": col.AUTH_PROVIDERS,
                    **self._local_bind(include_local_registrations),
                },
            ),
        )
        return int(next(iter(cursor), 0))
