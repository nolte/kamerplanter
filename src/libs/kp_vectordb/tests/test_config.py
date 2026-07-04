"""Tests for the shared VectorDbConfig dataclass."""

import dataclasses

import pytest

from kp_vectordb import VectorDbConfig


def _config() -> VectorDbConfig:
    return VectorDbConfig(
        host="db",
        port=5432,
        database="vec",
        username="user",
        password="secret",
        pool_min_size=1,
        pool_max_size=5,
    )


def test_config_is_immutable() -> None:
    cfg = _config()
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.host = "other"  # type: ignore[misc]


def test_config_has_no_password_default() -> None:
    # Every field is required — there is deliberately no insecure default.
    with pytest.raises(TypeError):
        VectorDbConfig(  # type: ignore[call-arg]
            host="db",
            port=5432,
            database="vec",
            username="user",
            pool_min_size=1,
            pool_max_size=5,
        )
