"""#1970 class — ``sync_actuator_states`` must not write a whole-actuator snapshot back.

The task reads every actuator, asks Home Assistant about each one (a network round trip
per actuator), then persists the online flag. A whole-document write reverts an edit of
the actuator that landed in between; the double below replaces on ``update_actuator``
like the real repository, so only a field-level write survives the interleaved edit.
"""

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest


class _Actuator(SimpleNamespace):
    def model_copy(self, update):
        return _Actuator(**{**vars(self), **update})


class _ReplacingActuatorRepo:
    def __init__(self, doc: dict):
        self.doc = doc

    def get_all(self, offset=0, limit=50, *, all_tenants=False):
        return [_Actuator(**self.doc)], 1

    def update_actuator(self, key, actuator):
        self.doc = dict(vars(actuator))  # replaces, like the real repository
        return actuator

    def update_fields(self, key, fields):
        self.doc = {**self.doc, **fields}


@pytest.fixture
def deps(monkeypatch):
    module = ModuleType("app.common.dependencies")
    module.get_actuator_repo = MagicMock()  # type: ignore[attr-defined]
    module.get_ha_client = MagicMock()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.common.dependencies", module)
    from app.config.settings import settings

    monkeypatch.setattr(settings, "actuator_control_loop_enabled", True)
    return module


def test_an_edit_landing_during_the_ha_round_trip_survives(deps):
    repo = _ReplacingActuatorRepo({"key": "a1", "name": "Fan", "ha_entity_id": "switch.fan", "is_online": True})

    def ha_state(_entity_id):
        repo.doc["name"] = "Fan (renamed)"  # an edit lands while HA is asked
        return None  # the entity is offline

    deps.get_actuator_repo.return_value = repo
    deps.get_ha_client.return_value = SimpleNamespace(get_state=ha_state)

    from app.tasks.actuator_tasks import sync_actuator_states

    result = sync_actuator_states.run()

    assert result["synced"] == 1
    assert repo.doc["is_online"] is False
    assert repo.doc["name"] == "Fan (renamed)"
