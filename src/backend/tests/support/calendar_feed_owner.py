"""Owner-standing stores for a ``CalendarService`` whose test is not about standing (#2226 review SEC-001).

``CalendarService.generate_ical_for_feed`` serves a feed only while its owner's
account, membership and tenant are active, and refuses every feed when the
three stores are not wired. A test about something else - the token at rest,
the tenant of the event reads, expiry - wires these doubles, under which every
owner stands. The standing itself is tested in
``tests/api/test_calendar_feed_ics_route.py`` and
``tests/unit/domain/services/test_calendar_service.py``.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock


def every_owner_stands() -> dict[str, Any]:
    """``membership_repo`` / ``user_repo`` / ``tenant_repo`` keyword arguments under which every owner stands."""
    active = SimpleNamespace(is_active=True)
    memberships = MagicMock()
    memberships.get_by_user_and_tenant.return_value = active
    users = MagicMock()
    users.get_by_key.return_value = active
    tenants = MagicMock()
    tenants.get_by_key.return_value = active
    return {"membership_repo": memberships, "user_repo": users, "tenant_repo": tenants}
