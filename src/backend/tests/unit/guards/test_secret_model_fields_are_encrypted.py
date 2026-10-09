"""#2113 — a domain-model field whose name denotes a secret is stored encrypted or hashed, or is decided.

The defect #2113 measured: ``HomeAssistantSettings.ha_access_token`` and
``PlantIdentificationSettings.plantnet_api_key`` were plain ``str`` fields, written
to ``system_settings`` as the admin typed them, while the OpenWeatherMap key in the
same document was Fernet ciphertext (``openweathermap_global_api_key_encrypted``).
Nothing made the difference visible: a reviewer reading the model saw a field
called ``…_token`` and no rule said that name had to carry its storage form.

This is that rule, for every pydantic model under ``app/domain/models``: a field
whose **name ends in a secret noun** (``token``, ``secret``, ``password``,
``passwd``, ``api_key``/``apikey``, ``access_key``, ``private_key``,
``credential(s)``) fails unless the name says how it is stored — it ends in
``_encrypted`` (Fernet, ``EncryptionEngine``) or ``_hash`` — or it is listed in
:data:`DECIDED` with the measured reason. ``token_url``, ``token_type``,
``token_expires_at``, ``max_tokens`` do not end in a secret noun and are not
secrets.

What this does NOT see, stated rather than discovered later:

* a secret kept under a **dict key** of a free-form field —
  ``ChannelPreference.config["urls"]`` (Apprise) is one; it is sealed by
  ``ArangoNotificationPreferenceRepository`` and measured on the stored document by
  ``tests/integration/test_integration_secrets_at_rest.py``;
* a secret field named without a secret noun (``api_key_ref`` holds Fernet
  ciphertext and passes; a plaintext field called ``bot`` would pass too);
* models outside ``app/domain/models`` (API request schemas carry the plaintext
  *inbound* — that is their job — and are not persisted).
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import re

import pytest
from pydantic import BaseModel

import app.domain.models as models_pkg

#: A field name that ends in a secret noun.
SECRET_NAME = re.compile(r"(?:^|_)(?:token|secret|password|passwd|api_?key|access_key|private_key|credentials?)$")

#: Suffixes that state the storage form.
STORAGE_FORM = re.compile(r"_(?:encrypted|hash)$")

#: (module.Class, field) → why the plaintext name is correct. Every entry is
#: re-checked: an entry that no longer names a matching field fails.
DECIDED: dict[tuple[str, str], str] = {
    ("auth.TokenPair", "access_token"): "response DTO handed to the client once; never persisted",
    ("invitation.InvitationLink", "token"): (
        "response DTO returned to the inviting lead once; the stored invitation keeps token_hash only"
    ),
    ("tenant_erasure.TenantDeletionConfirmation", "password"): "request body of a tenant deletion; never persisted",
    ("tenant_erasure.TenantDeletionConfirmation", "step_up_token"): (
        "request body of a tenant deletion; never persisted"
    ),
    ("tenant_erasure.TenantErasureCancelConfirmation", "password"): (
        "request body of cancelling a scheduled tenant deletion (#2123); never persisted"
    ),
    ("tenant_erasure.TenantErasureCancelConfirmation", "step_up_token"): (
        "request body of cancelling a scheduled tenant deletion (#2123); never persisted"
    ),
    ("service_account.ServiceAccountCreated", "api_key"): (
        "response DTO of a service-account creation (#2137): the first key's metadata and its raw value, shown "
        "once; never persisted - the stored ApiKey keeps key_hash only"
    ),
    ("service_account.ServiceAccountKeyRotated", "api_key"): (
        "response DTO of a key rotation (#2137): the new key, shown once; never persisted - the stored ApiKey "
        "keeps key_hash only"
    ),
    ("calendar.CalendarFeed", "token"): (
        "persisted in clear: the iCal endpoint looks the feed up BY the token value, so Fernet (random IV) cannot "
        "serve the lookup; hashing it is the fix and is a separate change (#2113 class sweep, reported)"
    ),
}


def secret_named_fields(model: type[BaseModel]) -> list[str]:
    """The fields of *model* whose name denotes a secret and does not state its storage form."""
    return [name for name in model.model_fields if SECRET_NAME.search(name) and not STORAGE_FORM.search(name)]


def _domain_models() -> list[tuple[str, type[BaseModel]]]:
    found: list[tuple[str, type[BaseModel]]] = []
    for info in pkgutil.walk_packages(models_pkg.__path__, models_pkg.__name__ + "."):
        module = importlib.import_module(info.name)
        for _name, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, BaseModel) and cls.__module__ == module.__name__:
                found.append((f"{info.name.removeprefix(models_pkg.__name__ + '.')}.{cls.__name__}", cls))
    return found


def _hits() -> set[tuple[str, str]]:
    return {(where, field) for where, cls in _domain_models() for field in secret_named_fields(cls)}


def test_every_secret_named_model_field_is_encrypted_hashed_or_decided() -> None:
    undecided = sorted(f"{where}.{field}" for where, field in _hits() - DECIDED.keys())

    assert undecided == [], (
        "a domain-model field named like a secret is stored as typed — encrypt it through EncryptionEngine and "
        "name it '<field>_encrypted' (or hash it, '<field>_hash'), or add it to DECIDED with the measured "
        "reason:\n  " + "\n  ".join(undecided)
    )


def test_every_decided_entry_still_names_a_field() -> None:
    stale = sorted(f"{where}.{field}" for where, field in DECIDED.keys() - _hits())

    assert stale == [], f"DECIDED entries that no longer match a secret-named field: {stale}"


def test_the_scan_reaches_the_models_it_is_about() -> None:
    """Anti-vacuity: the walk finds the system-settings models and the stored-secret siblings."""
    names = {where for where, _cls in _domain_models()}

    assert {"system_settings.HomeAssistantSettings", "system_settings.PlantIdentificationSettings"} <= names
    assert {"auth.AuthProvider", "oidc_config.OidcProviderConfig", "inventree.InvenTreeConnection"} <= names


# ── self-tests: the rule fires on the shape it is about and passes its siblings ──


@pytest.mark.parametrize(
    "field",
    [
        "ha_access_token",
        "plantnet_api_key",
        "apikey",
        "client_secret",
        "smtp_password",
        "s3_secret_access_key",
        "ssh_private_key",
        "credentials",
        "token",
    ],
)
def test_a_plaintext_secret_name_is_caught(field: str) -> None:
    model = type("Probe", (BaseModel,), {"__annotations__": {field: str | None}, field: None})

    assert secret_named_fields(model) == [field]


@pytest.mark.parametrize(
    "field",
    [
        "ha_access_token_encrypted",
        "plantnet_api_key_encrypted",
        "token_hash",
        "password_hash",
        "token_url",
        "token_type",
        "token_expires_at",
        "max_tokens",
        "api_key_ref",
        "requires_api_key_flag",
    ],
)
def test_a_storage_form_or_a_non_secret_name_passes(field: str) -> None:
    model = type("Probe", (BaseModel,), {"__annotations__": {field: str | None}, field: None})

    assert secret_named_fields(model) == []
