"""#2110 (MT-013) — ``AiCallBudget``: daily budgets per account and tenant, fail-closed."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.common.exceptions import AiBudgetExceededError, AiBudgetUnavailableError
from app.domain.services.ai_call_budget import AiBudgetLimits, AiCallBudget, token_counts


class FakeValkey:
    def __init__(self) -> None:
        self.values: dict[str, int] = {}
        self.expiries: dict[str, int] = {}

    def get(self, key: str) -> str | None:
        return str(self.values[key]) if key in self.values else None

    def incr(self, key: str) -> int:
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    def incrby(self, key: str, amount: int) -> int:
        self.values[key] = self.values.get(key, 0) + amount
        return self.values[key]

    def expire(self, key: str, seconds: int) -> bool:
        self.expiries[key] = seconds
        return True


class DownValkey(FakeValkey):
    def get(self, key: str) -> str | None:
        raise ConnectionError("valkey down")

    def incr(self, key: str) -> int:
        raise ConnectionError("valkey down")

    def incrby(self, key: str, amount: int) -> int:
        raise ConnectionError("valkey down")


_NOON = datetime(2026, 10, 5, 12, 0, 0, tzinfo=UTC)


class _FixedClock:
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


def _budget(store=None, *, user: int = 50, tenant: int = 500, tokens: int = 0, now: datetime = _NOON) -> AiCallBudget:
    return AiCallBudget(
        store if store is not None else FakeValkey(),
        AiBudgetLimits(user_calls_per_day=user, tenant_calls_per_day=tenant, tenant_tokens_per_day=tokens),
        clock=_FixedClock(now),
    )


def test_the_51st_call_of_a_day_is_refused_with_retry_after_until_midnight() -> None:
    budget = _budget()
    for _ in range(50):
        budget.charge(tenant_key="home", user_key="anna")

    with pytest.raises(AiBudgetExceededError) as refused:
        budget.charge(tenant_key="home", user_key="anna")

    assert refused.value.status_code == 429
    assert refused.value.details[0]["code"] == "user_calls"
    assert refused.value.retry_after == 12 * 3600  # noon → next UTC midnight


def test_the_users_budget_is_per_tenant() -> None:
    """Budget per (tenant, user): a member of two gardens has one budget in each."""
    budget = _budget(user=1)
    budget.charge(tenant_key="home", user_key="anna")
    budget.charge(tenant_key="club", user_key="anna")

    with pytest.raises(AiBudgetExceededError):
        budget.charge(tenant_key="home", user_key="anna")


def test_a_new_day_starts_a_new_budget() -> None:
    store = FakeValkey()
    _budget(store, user=1).charge(tenant_key="home", user_key="anna")

    tomorrow = datetime(2026, 10, 6, 0, 0, 1, tzinfo=UTC)
    _budget(store, user=1, now=tomorrow).charge(tenant_key="home", user_key="anna")


def test_a_refusal_at_the_user_budget_does_not_touch_the_tenant_counter() -> None:
    store = FakeValkey()
    budget = _budget(store, user=1, tenant=10)
    budget.charge(tenant_key="home", user_key="anna")
    for _ in range(20):
        with pytest.raises(AiBudgetExceededError):
            budget.charge(tenant_key="home", user_key="anna")

    assert budget.usage("home").calls == 1


def test_the_token_budget_refuses_once_the_day_is_spent() -> None:
    budget = _budget(tokens=1000)
    budget.charge(tenant_key="home", user_key="anna")
    budget.record_usage(tenant_key="home", usage={"prompt_tokens": 800, "completion_tokens": 250})

    with pytest.raises(AiBudgetExceededError) as refused:
        budget.charge(tenant_key="home", user_key="ben")
    assert refused.value.details[0]["code"] == "tenant_tokens"


def test_a_zero_switches_a_budget_off() -> None:
    budget = _budget(user=0, tenant=0, tokens=0)
    for _ in range(200):
        budget.charge(tenant_key="home", user_key="anna")


def test_an_unreachable_store_refuses_the_call_with_503() -> None:
    with pytest.raises(AiBudgetUnavailableError) as refused:
        _budget(DownValkey()).charge(tenant_key="home", user_key="anna")
    assert refused.value.status_code == 503


def test_a_lost_usage_count_does_not_fail_the_answered_call() -> None:
    _budget(DownValkey()).record_usage(tenant_key="home", usage={"prompt_tokens": 5, "completion_tokens": 5})


def test_counters_expire_after_the_day() -> None:
    store = FakeValkey()
    budget = _budget(store, tokens=10_000)
    budget.charge(tenant_key="home", user_key="anna")
    budget.record_usage(tenant_key="home", usage={"prompt_tokens": 3, "completion_tokens": 4})

    assert store.expiries and all(seconds == 2 * 86_400 for seconds in store.expiries.values())
    assert set(store.expiries) == set(store.values)


def test_the_cost_of_a_tenant_is_countable() -> None:
    budget = _budget(tokens=10_000)
    for user in ("anna", "ben"):
        budget.charge(tenant_key="home", user_key=user)
        budget.record_usage(tenant_key="home", usage={"prompt_tokens": 100, "completion_tokens": 20})
    budget.charge(tenant_key="club", user_key="anna")

    assert budget.usage("home").calls == 2
    assert budget.usage("home").tokens == 240
    assert budget.usage("club").tokens == 0


@pytest.mark.parametrize(
    ("usage", "expected"),
    [
        (None, (0, 0)),
        ({}, (0, 0)),
        ({"prompt_tokens": 12, "completion_tokens": 3}, (12, 3)),
        ({"prompt_tokens": -1, "completion_tokens": 3}, (0, 3)),
        ({"input_tokens": 9}, (0, 0)),
    ],
)
def test_token_counts_reads_the_knowledge_service_usage_shape(usage, expected) -> None:
    assert token_counts(usage) == expected
