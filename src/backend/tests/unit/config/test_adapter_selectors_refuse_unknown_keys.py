"""An unknown adapter / backend selector stops the start instead of picking another one — #1887.

``IDENTIFICATION_PRIMARY_ADAPTER`` and ``PEST_DETECTION_PRIMARY_ADAPTER`` were
plain ``str`` and their registries silently returned the first *other*
configured adapter for a key nobody registered — possibly a provider the
operator never chose. ``STORAGE_BACKEND`` failed only at first use. All three
are now refused when the settings load, with a value-free message that names
the variable and the allowed values (the ``load_settings`` contract of #1832).
"""

from __future__ import annotations

import pytest

from app.config.settings import Settings, SettingsError, load_settings

SELECTORS = [
    ("IDENTIFICATION_PRIMARY_ADAPTER", "plantnet", "identification_primary_adapter"),
    ("PEST_DETECTION_PRIMARY_ADAPTER", "local_pest_symptom", "pest_detection_primary_adapter"),
    ("STORAGE_BACKEND", "local-fs", "storage_backend"),
]
TYPO = "plantnett-secret-looking-typo"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for variable, _, _ in SELECTORS:
        monkeypatch.delenv(variable, raising=False)


@pytest.mark.parametrize(("variable", "default", "_field"), SELECTORS)
def test_an_unknown_value_refuses_to_load_without_echoing_it(monkeypatch, variable, default, _field):
    monkeypatch.setenv(variable, TYPO)
    with pytest.raises(SettingsError) as raised:
        load_settings()
    message = str(raised.value)
    assert variable in message
    assert default in message  # the allowed values are named ...
    assert TYPO not in message  # ... the configured value is not


@pytest.mark.parametrize(("variable", "default", "field"), SELECTORS)
def test_an_unset_variable_keeps_the_documented_default(variable, default, field):
    assert getattr(load_settings(), field) == default


@pytest.mark.parametrize(("variable", "default", "field"), SELECTORS)
def test_every_allowed_value_loads(monkeypatch, variable, default, field):
    allowed = Settings.model_fields[field].annotation.__args__
    assert default in allowed
    for value in allowed:
        monkeypatch.setenv(variable, value)
        assert getattr(load_settings(), field) == value


def test_the_allowed_values_are_exactly_the_registered_adapter_keys():
    """The ``Literal``s cannot import the registries (they import settings), so pin them."""
    import app.data_access.external.demo_pest_adapter
    import app.data_access.external.kindwise_pest_adapter
    import app.data_access.external.local_embedding_adapter
    import app.data_access.external.local_pest_adapters
    import app.data_access.external.plantnet_adapter  # noqa: F401 — import registers the adapter
    import app.data_access.storage.registry  # noqa: F401
    from app.data_access.storage.registry import StorageAdapterRegistry
    from app.domain.services.identification_registry import IdentificationAdapterRegistry
    from app.domain.services.pest_detection_registry import PestDetectionAdapterRegistry

    fields = Settings.model_fields
    assert set(fields["identification_primary_adapter"].annotation.__args__) == set(
        IdentificationAdapterRegistry.all_keys()
    )
    assert set(fields["pest_detection_primary_adapter"].annotation.__args__) == set(
        PestDetectionAdapterRegistry.all_keys()
    )
    assert set(fields["storage_backend"].annotation.__args__) == set(StorageAdapterRegistry.all_keys())
