"""A notification always has a recipient; one without is nobody's — MT-045.8 (#2144).

Measured before deciding (audit: "empty ``user_key`` = tenant broadcast,
undocumented"):

* **No reader treats it as a broadcast.** ``list_for_user`` and ``count_unread``
  filter ``doc.user_key == @user_key``; a row with ``""`` appears in nobody's inbox
  and nobody's badge.
* **No writer produces one today.** The care beat refuses a task without an
  assignee (``_ActiveMembers`` asks for ``("", tenant)``, #2114), the propagation
  service creates ``task.due`` only with a resolvable recipient, every other
  ``Notification(...)`` names its user.
* **But the by-key routes did.** ``get_notification``/``mark_read``/``mark_acted``
  skipped the owner check when the row had no ``user_key``
  (``if user_key and notif.user_key and ...``) — any member of the tenant could
  read, mark and *act on* (the §4.2 callback confirms a care task) a row that no
  inbox ever showed them.

Decision: mandatory, not documented-as-broadcast. The field is required on every
write (the repository refuses ``""``), and the by-key reads fail closed on a row
without one. A real tenant broadcast would need its own reader semantics first.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.notification_repository import ArangoNotificationRepository
from app.domain.models.notification import Notification
from app.domain.services.notification_service import NotificationService


def _service(stored: Notification) -> tuple[NotificationService, MagicMock]:
    repo = MagicMock()
    repo.get.return_value = stored
    repo.mark_read.return_value = stored
    repo.mark_acted.return_value = stored
    return NotificationService(engine=MagicMock(), notification_repo=repo, preference_repo=MagicMock()), repo


def _ownerless() -> Notification:
    return Notification(_key="n1", tenant_key="t1", user_key="", notification_type="care.watering", title="t", body="b")


def test_a_member_cannot_read_a_notification_without_a_recipient() -> None:
    service, _ = _service(_ownerless())

    assert service.get_notification("n1", "t1", user_key="u-member") is None


def test_a_member_cannot_mark_or_act_on_a_notification_without_a_recipient() -> None:
    service, repo = _service(_ownerless())

    assert service.mark_read("n1", "t1", user_key="u-member") is None
    assert service.mark_acted("n1", "t1", "confirm", user_key="u-member") is None
    repo.mark_read.assert_not_called()
    repo.mark_acted.assert_not_called()


def test_the_recipient_still_reads_their_own() -> None:
    own = Notification(_key="n1", tenant_key="t1", user_key="u1", notification_type="x", title="t", body="b")
    service, repo = _service(own)

    assert service.get_notification("n1", "t1", user_key="u1") is own
    assert service.mark_read("n1", "t1", user_key="u1") is own
    repo.mark_read.assert_called_once()


def test_the_repository_refuses_to_write_a_notification_without_a_recipient() -> None:
    db = MagicMock()
    repo = ArangoNotificationRepository(db)

    with pytest.raises(ValueError, match="recipient"):
        repo.create(_ownerless())

    db.collection.return_value.insert.assert_not_called()
