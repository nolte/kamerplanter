from abc import ABC, abstractmethod

from app.common.types import UserKey
from app.domain.models.privacy import ConsentRecord, ConsentRecordKey


class IConsentRepository(ABC):
    @abstractmethod
    def create(self, consent: ConsentRecord) -> ConsentRecord: ...

    @abstractmethod
    def get_by_key(self, key: ConsentRecordKey) -> ConsentRecord | None: ...

    @abstractmethod
    def get_by_user_and_purpose(self, user_key: UserKey, purpose: str) -> ConsentRecord | None: ...

    @abstractmethod
    def update(self, key: ConsentRecordKey, consent: ConsentRecord) -> ConsentRecord: ...

    @abstractmethod
    def list_by_user(self, user_key: UserKey) -> list[ConsentRecord]: ...

    @abstractmethod
    def delete(self, key: ConsentRecordKey) -> bool: ...

    @abstractmethod
    def delete_all_for_user(self, user_key: UserKey) -> int: ...

    @abstractmethod
    def list_unanonymized_ips_before(self, cutoff_iso: str) -> list[tuple[str, str]]:
        """``(key, ip_address)`` of every consent record recorded before the cutoff whose IP is still plain (R-04a)."""

    @abstractmethod
    def mark_ip_anonymized(
        self, key: ConsentRecordKey, previous_ip: str, anonymized_ip: str, anonymized_at_iso: str
    ) -> bool:
        """Replace a consent record's IP with its anonymised form, but only if it is still *previous_ip* (R-04a).

        A conditional write (#1800 security review, SEC-003): a concurrent
        re-grant (:meth:`grant_consent`) can write a fresh IP onto the same row
        between selection and this write. An unconditional overwrite would
        stamp the row anonymised with a hash of the *stale* address while the
        fresh one goes untouched. Returns whether the write actually happened.
        """

    @abstractmethod
    def delete_revoked_before(self, cutoff_iso: str) -> int:
        """Hard-delete every consent record revoked before the cutoff (NFR-011 R-04)."""

    @abstractmethod
    def revoke_all_unrevoked(self, user_key: UserKey, now_iso: str) -> int:
        """Mark every consent record of *user_key* with no ``revoked_at`` as revoked *now* (NFR-011 R-04).

        Called at account erasure, before the row is pseudonymised: a consent
        never explicitly revoked would otherwise be pseudonymised with
        ``revoked_at`` still null, and the R-04 purge (a destructive selector
        that excludes null on purpose) would never reach it — unbounded
        retention past account erasure (#1800 security review). Not gated by
        :meth:`ConsentEngine.validate_consent_change`'s required-purpose rule:
        once the account itself is being erased, no account remains for a
        mandatory purpose to apply to.
        """
