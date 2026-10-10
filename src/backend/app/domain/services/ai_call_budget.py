"""REQ-031 §3 (#2110, MT-013) — daily budgets of LLM calls per account and per tenant.

Every KI route that puts a prompt in front of an LLM charges this budget
**before** the call — tip and daily-tip generation, "why?", a chat message, a
free-form knowledge question (``/ai/knowledge/ask``, #2175), a glossary
generation on the tenant path and the KI diagnosis. Three daily
counters, each per UTC day and each switched off by a ``0`` setting:

* ``user_calls`` — calls one account starts in one tenant
  (``AI_BUDGET_USER_CALLS_PER_DAY``),
* ``tenant_calls`` — calls all members of a tenant start together
  (``AI_BUDGET_TENANT_CALLS_PER_DAY``),
* ``tenant_tokens`` — LLM tokens a tenant spent, as the knowledge service
  reports them after each answer (``AI_BUDGET_TENANT_TOKENS_PER_DAY``). The
  token count is only known after a call, so the check refuses the next call
  once the day's total has reached the budget; one answer can overshoot it.

The per-minute bound is not here: the generating routes carry the shared
slowapi ``rate_limit_inference`` keyed on the account (``user_rate_limit_key``).

**Order.** The account's counter is charged first and a refusal there stops
before the tenant counter is touched. Otherwise one member hammering past the
personal budget would use up the tenant's budget and lock every other member
out — the noisy neighbour this budget exists to prevent, moved inside a tenant.

**Fail-closed.** When Valkey cannot be reached the call is refused with 503
(:class:`AiBudgetUnavailableError`) whatever the provider. The backend cannot
tell which LLM answers: the knowledge service picks its model from its own
environment, the ``/ask`` request names no provider and the answer reports none
(measured for #2110), so "this is a local model, fail open" is not a fact the
budget could rely on. A paid provider would turn an outage into unbounded cost,
a shared GPU into an unbounded queue.

The counters are also what makes the cost of a tenant countable: the day's
calls and tokens per tenant are readable with :meth:`AiCallBudget.usage`, and
every audited call carries its token counts (``ai_audit_log``).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

import structlog

from app.common.exceptions import AiBudgetExceededError, AiBudgetUnavailableError
from app.common.log_privacy import log_tenant, loggable_error

logger = structlog.get_logger(__name__)

#: Counters are keyed by the UTC day, so they never need resetting; the TTL only
#: lets Valkey drop a finished day. Two days outlive any clock skew at midnight.
_COUNTER_TTL_SECONDS = 2 * 86_400

USER_CALLS = "user_calls"
TENANT_CALLS = "tenant_calls"
TENANT_TOKENS = "tenant_tokens"


class AiBudgetClock(Protocol):
    """Where the budget reads the time — a seam for tests."""

    def now(self) -> datetime: ...


class UtcClock:
    """The wall clock, in UTC."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class AiBudgetStore(Protocol):
    """The four commands of a ``decode_responses=True`` Valkey client the budget uses."""

    def get(self, name: str) -> str | None: ...

    def incr(self, name: str) -> int: ...

    def incrby(self, name: str, amount: int) -> int: ...

    def expire(self, name: str, time: int) -> bool: ...


@dataclass(frozen=True)
class AiBudgetLimits:
    """The three daily budgets; ``0`` switches one off."""

    user_calls_per_day: int
    tenant_calls_per_day: int
    tenant_tokens_per_day: int


@dataclass(frozen=True)
class AiTenantUsage:
    """What one tenant spent on one UTC day."""

    day: str
    calls: int
    tokens: int


class AiCallBudget:
    """Charges an LLM call against the daily budgets of an account and its tenant."""

    def __init__(
        self,
        redis_client: AiBudgetStore,
        limits: AiBudgetLimits,
        *,
        clock: AiBudgetClock | None = None,
    ) -> None:
        self._redis = redis_client
        self._limits = limits
        self._clock: AiBudgetClock = clock if clock is not None else UtcClock()

    # ── keys ───────────────────────────────────────────────────────────

    @staticmethod
    def _user_key(day: str, tenant_key: str, user_key: str) -> str:
        return f"ai_budget:{day}:calls:t:{tenant_key}:u:{user_key}"

    @staticmethod
    def _tenant_key(day: str, tenant_key: str) -> str:
        return f"ai_budget:{day}:calls:t:{tenant_key}"

    @staticmethod
    def _tokens_key(day: str, tenant_key: str) -> str:
        return f"ai_budget:{day}:tokens:t:{tenant_key}"

    def _day_and_retry_after(self) -> tuple[str, int]:
        now: datetime = self._clock.now()
        # recurrence-owner-ok: the budget window is the current UTC calendar day;
        # its end is only the Retry-After of a refusal, nothing recurs on it.
        next_midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), tzinfo=UTC)
        remaining: timedelta = next_midnight - now
        return now.date().isoformat(), max(1, int(remaining.total_seconds()))

    # ── charging ───────────────────────────────────────────────────────

    def charge(self, *, tenant_key: str, user_key: str) -> None:
        """Count one LLM call, or refuse it.

        Raises:
            AiBudgetExceededError: one of the daily budgets is used up (429,
                ``Retry-After`` until the UTC day ends).
            AiBudgetUnavailableError: Valkey cannot be reached (503, fail-closed).
        """
        day, retry_after = self._day_and_retry_after()
        try:
            if self._limits.tenant_tokens_per_day > 0:
                spent = int(self._redis.get(self._tokens_key(day, tenant_key)) or 0)
                if spent >= self._limits.tenant_tokens_per_day:
                    raise self._refuse(TENANT_TOKENS, retry_after, tenant_key)
            if self._limits.user_calls_per_day > 0:
                calls = self._increment(self._user_key(day, tenant_key, user_key))
                if calls > self._limits.user_calls_per_day:
                    raise self._refuse(USER_CALLS, retry_after, tenant_key)
            if self._limits.tenant_calls_per_day > 0:
                calls = self._increment(self._tenant_key(day, tenant_key))
                if calls > self._limits.tenant_calls_per_day:
                    raise self._refuse(TENANT_CALLS, retry_after, tenant_key)
        except AiBudgetExceededError:
            raise
        except Exception as exc:  # noqa: BLE001 — any store failure is an outage, refused below
            logger.warning("ai_budget_unavailable", tenant=log_tenant(tenant_key), error=loggable_error(exc))
            raise AiBudgetUnavailableError() from exc

    def record_usage(self, *, tenant_key: str, usage: Mapping[str, int] | None) -> None:
        """Add the tokens of a finished call to the tenant's day (best effort).

        The call already happened and its answer is on the way to the user; a
        lost count must not turn it into an error. The next :meth:`charge` hits
        the same store and refuses there if it is still down.
        """
        tokens = _token_total(usage)
        if tokens <= 0:
            return
        day, _ = self._day_and_retry_after()
        key = self._tokens_key(day, tenant_key)
        try:
            self._redis.incrby(key, tokens)
            self._redis.expire(key, _COUNTER_TTL_SECONDS)
        except Exception as exc:  # noqa: BLE001 — best effort, see docstring
            logger.warning("ai_budget_usage_not_recorded", tenant=log_tenant(tenant_key), error=loggable_error(exc))

    def usage(self, tenant_key: str) -> AiTenantUsage:
        """Calls and tokens *tenant_key* spent today (UTC)."""
        day, _ = self._day_and_retry_after()
        calls = int(self._redis.get(self._tenant_key(day, tenant_key)) or 0)
        tokens = int(self._redis.get(self._tokens_key(day, tenant_key)) or 0)
        return AiTenantUsage(day=day, calls=calls, tokens=tokens)

    # ── internals ──────────────────────────────────────────────────────

    def _increment(self, key: str) -> int:
        count = int(self._redis.incr(key))
        if count == 1:
            self._redis.expire(key, _COUNTER_TTL_SECONDS)
        return count

    @staticmethod
    def _refuse(scope: str, retry_after: int, tenant_key: str) -> AiBudgetExceededError:
        logger.info("ai_budget_exceeded", scope=scope, tenant=log_tenant(tenant_key))
        return AiBudgetExceededError(scope, retry_after)


def _token_total(usage: Mapping[str, int] | None) -> int:
    return sum(token_counts(usage))


def token_counts(usage: Mapping[str, int] | None) -> tuple[int, int]:
    """``(prompt_tokens, completion_tokens)`` of an answer's usage, non-negative."""
    if not usage:
        return (0, 0)
    prompt = usage.get("prompt_tokens", 0)
    completion = usage.get("completion_tokens", 0)
    return (
        prompt if isinstance(prompt, int) and prompt > 0 else 0,
        completion if isinstance(completion, int) and completion > 0 else 0,
    )
