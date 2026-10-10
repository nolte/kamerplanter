"""The calendar-feed service checks the owner itself, whoever calls it (#2119 follow-up).

``CalendarService.get_feed(key, tenant_key="")`` skipped the ownership check for an
empty tenant, and ``update_feed`` / ``delete_feed`` / ``regenerate_token`` called it
exactly that way — they were safe only because the router checked first. The check
now lives in the service and fails closed: a foreign feed, and any feed for an empty
caller tenant, answers 404. The one deliberately tenant-less path is the public iCal
URL, which authenticates by the feed token (``generate_ical_for_feed``), not by key.

Also pinned here: a ``PUT`` builds a fresh :class:`CalendarFeed` without owner
fields, and ``update_feed`` used to write that model as-is — the stored feed lost its
``tenant_key`` and ``user_key`` and vanished from its owner's list.

And one level below the tenant (#2171 review W-1): a feed belongs to one member
(REQ-015 CF-002). Changing, rotating or deleting it is the owner's - or a lead's -
business; for any other member of the same tenant the feed answers 404 like an
unknown one, so a grower can neither break nor take over a colleague's subscription.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.calendar import CalendarFeed
from app.domain.services.calendar_service import CalendarService

OWNER = "tenant-a"
OTHER = "tenant-b"
FEED_OWNER = "u1"
COLLEAGUE = "u2"

#: The caller as the feed's owner, a grower of the same tenant.
MINE = {"user_key": FEED_OWNER, "role": TenantRole.GROWER}


def _feed() -> CalendarFeed:
    return CalendarFeed(_key="f1", name="Mine", tenant_key=OWNER, user_key="u1", token_hash="digest")


@pytest.fixture
def repo() -> MagicMock:
    repo = MagicMock()

    def get_or_raise(key: str) -> CalendarFeed:
        if key != "f1":
            raise NotFoundError("CalendarFeed", key)
        return _feed()

    repo.get_or_raise.side_effect = get_or_raise
    # A field merge answers with the stored feed, the merged fields applied.
    repo.update_fields.side_effect = lambda key, fields: CalendarFeed.model_validate(
        {**_feed().model_dump(by_alias=True), **fields}
    )
    repo.delete.return_value = True
    return repo


@pytest.fixture
def service(repo: MagicMock) -> CalendarService:
    return CalendarService(feed_repo=repo, aggregation_engine=MagicMock(), source_repo=MagicMock())


@pytest.mark.parametrize("tenant_key", [OTHER, ""])
class TestAForeignOrTenantlessCallerIsRefused:
    def test_get(self, service, tenant_key) -> None:
        with pytest.raises(NotFoundError):
            service.get_feed("f1", tenant_key=tenant_key)

    def test_update(self, service, repo, tenant_key) -> None:
        with pytest.raises(NotFoundError):
            service.update_feed("f1", CalendarFeed(name="Hijacked"), tenant_key=tenant_key, **MINE)
        repo.update_fields.assert_not_called()
        repo.update.assert_not_called()

    def test_delete(self, service, repo, tenant_key) -> None:
        with pytest.raises(NotFoundError):
            service.delete_feed("f1", tenant_key=tenant_key, user_key=FEED_OWNER, role=TenantRole.LEAD)
        repo.delete.assert_not_called()

    def test_regenerate_token(self, service, repo, tenant_key) -> None:
        with pytest.raises(NotFoundError):
            service.regenerate_token("f1", tenant_key=tenant_key, **MINE)
        repo.update_fields.assert_not_called()
        repo.update.assert_not_called()


class TestTheOwnerIsServed:
    def test_get(self, service) -> None:
        assert service.get_feed("f1", tenant_key=OWNER).key == "f1"

    def test_delete(self, service) -> None:
        assert service.delete_feed("f1", tenant_key=OWNER, user_key=FEED_OWNER, role=TenantRole.LEAD) is True

    def test_regenerate_token(self, service) -> None:
        issued = service.regenerate_token("f1", tenant_key=OWNER, **MINE)
        assert issued.token and issued.feed.token_hash not in ("digest", issued.token)

    def test_update_writes_name_filters_and_state_only(self, service, repo) -> None:
        updated = service.update_feed("f1", CalendarFeed(name="Renamed", is_active=False), tenant_key=OWNER, **MINE)

        # Exactly the allow-list: no owner field, no token digest, no expiry (W-2) -
        # what is not written cannot put back a value read before a rotation.
        key, fields = repo.update_fields.call_args.args
        assert key == "f1"
        assert set(fields) == {"name", "filters", "is_active"}
        assert (fields["name"], fields["is_active"]) == ("Renamed", False)
        repo.update.assert_not_called()
        assert (updated.tenant_key, updated.user_key, updated.token_hash) == (OWNER, FEED_OWNER, "digest")

    def test_rotation_writes_the_new_digest_only(self, service, repo) -> None:
        issued = service.regenerate_token("f1", tenant_key=OWNER, **MINE)

        key, fields = repo.update_fields.call_args.args
        assert key == "f1"
        assert fields == {"token_hash": TokenEngine.hash_token(issued.token)}
        repo.update.assert_not_called()


@pytest.mark.parametrize("role", [TenantRole.GROWER, TenantRole.VIEWER])
class TestAColleaguesFeedIsRefused:
    """Same tenant, another member's feed: 404, and nothing is written (W-1)."""

    def test_update(self, service, repo, role) -> None:
        with pytest.raises(NotFoundError):
            service.update_feed("f1", CalendarFeed(name="Hijacked"), tenant_key=OWNER, user_key=COLLEAGUE, role=role)
        repo.update_fields.assert_not_called()
        repo.update.assert_not_called()

    def test_regenerate_token(self, service, repo, role) -> None:
        with pytest.raises(NotFoundError):
            service.regenerate_token("f1", tenant_key=OWNER, user_key=COLLEAGUE, role=role)
        repo.update_fields.assert_not_called()
        repo.update.assert_not_called()

    def test_delete(self, service, repo, role) -> None:
        with pytest.raises(NotFoundError):
            service.delete_feed("f1", tenant_key=OWNER, user_key=COLLEAGUE, role=role)
        repo.delete.assert_not_called()

    def test_an_empty_caller_never_matches(self, service, repo, role) -> None:
        with pytest.raises(NotFoundError):
            service.regenerate_token("f1", tenant_key=OWNER, user_key="", role=role)
        repo.update_fields.assert_not_called()
        repo.update.assert_not_called()


class TestALeadManagesEveryFeedOfTheTenant:
    LEAD = {"user_key": COLLEAGUE, "role": TenantRole.LEAD}

    def test_update(self, service, repo) -> None:
        updated = service.update_feed("f1", CalendarFeed(name="Renamed"), tenant_key=OWNER, **self.LEAD)
        assert repo.update_fields.call_args.args[1]["name"] == "Renamed"
        assert (updated.name, updated.user_key) == ("Renamed", FEED_OWNER)

    def test_regenerate_token(self, service) -> None:
        assert service.regenerate_token("f1", tenant_key=OWNER, **self.LEAD).token

    def test_delete(self, service) -> None:
        assert service.delete_feed("f1", tenant_key=OWNER, **self.LEAD) is True

    def test_but_not_a_foreign_tenants_feed(self, service, repo) -> None:
        with pytest.raises(NotFoundError):
            service.regenerate_token("f1", tenant_key=OTHER, **self.LEAD)
        repo.update_fields.assert_not_called()
        repo.update.assert_not_called()


def test_the_tenant_is_required_and_keyword_only(service) -> None:
    with pytest.raises(TypeError):
        service.get_feed("f1")  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        service.delete_feed("f1", OWNER)  # type: ignore[misc]
    with pytest.raises(TypeError):
        service.regenerate_token("f1", tenant_key=OWNER)  # type: ignore[call-arg]
