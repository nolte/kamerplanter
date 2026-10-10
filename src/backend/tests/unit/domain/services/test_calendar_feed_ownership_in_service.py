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
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.domain.models.calendar import CalendarFeed
from app.domain.services.calendar_service import CalendarService

OWNER = "tenant-a"
OTHER = "tenant-b"


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
    repo.update.side_effect = lambda key, feed: feed
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
            service.update_feed("f1", CalendarFeed(name="Hijacked"), tenant_key=tenant_key)
        repo.update.assert_not_called()

    def test_delete(self, service, repo, tenant_key) -> None:
        with pytest.raises(NotFoundError):
            service.delete_feed("f1", tenant_key=tenant_key)
        repo.delete.assert_not_called()

    def test_regenerate_token(self, service, repo, tenant_key) -> None:
        with pytest.raises(NotFoundError):
            service.regenerate_token("f1", tenant_key=tenant_key)
        repo.update.assert_not_called()


class TestTheOwnerIsServed:
    def test_get(self, service) -> None:
        assert service.get_feed("f1", tenant_key=OWNER).key == "f1"

    def test_delete(self, service) -> None:
        assert service.delete_feed("f1", tenant_key=OWNER) is True

    def test_regenerate_token(self, service) -> None:
        issued = service.regenerate_token("f1", tenant_key=OWNER)
        assert issued.token and issued.feed.token_hash not in ("digest", issued.token)

    def test_update_keeps_owner_and_token_hash(self, service, repo) -> None:
        service.update_feed("f1", CalendarFeed(name="Renamed", is_active=False), tenant_key=OWNER)

        written = repo.update.call_args.args[1]
        assert (written.name, written.is_active) == ("Renamed", False)
        assert (written.tenant_key, written.user_key, written.token_hash) == (OWNER, "u1", "digest")


def test_the_tenant_is_required_and_keyword_only(service) -> None:
    with pytest.raises(TypeError):
        service.get_feed("f1")  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        service.delete_feed("f1", OWNER)  # type: ignore[misc]
