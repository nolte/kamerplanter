"""The one place a support reference ID is minted (#1158).

Every error response carries an ``error_id`` the caller is told to quote. It was
minted independently in four places as ``f"err_{uuid.uuid4()}"`` — identical
strings, no shared definition, which is the drift shape this repository has been
burned by often enough to name.

**Why it is not just a `uuid4()`.** A UUID's final group is twelve hex characters.
When all twelve happen to be decimal digits *and* the result passes the Luhn
checksum, the identifier is indistinguishable from a payment-card number. That is
not hypothetical: the post-merge ZAP scan of ``57ee6a2c`` raised a **High**-risk
"PII Disclosure — Credit Card Type detected: Maestro" on
``POST /api/v1/privacy/erasure`` with the evidence ``576481450749``, which is
exactly such a group (#1158).

Measured over 200 000 generated ids: **0.035 %** carry a Luhn-valid 12-digit run —
about one in 2 800. An API scan makes thousands of requests, most of the error
paths among them, so this recurs. Each recurrence is a *blocking* finding that
files an issue and fails a scan, and a blocking finding that fires at random is
worse than none: it teaches everyone to read red in that lane as noise, and the
next genuine PII disclosure arrives already discounted (the #1178 pattern).

**Why the fix is here and not in the scanner's rule file.** The gate's rule format
(``tests/security/zap-*.tsv``) tunes a whole plugin id; suppressing 10062 would
switch off PII detection for the entire API surface to hide one false positive.
That trades a real capability for a cosmetic quiet. And ZAP is not the only
consumer: an operator's own log pipeline, an SIEM, or a customer's DLP rule will
apply the same heuristic to the same string. An opaque identifier that reads as a
card number is a defect of the identifier, however small.

So the id keeps its shape — ``err_<uuid4>``, unchanged for logs, docs and support —
and is simply re-drawn on the rare occasion it would look like a card. The expected
number of re-draws is 0.00035 per call.
"""

from __future__ import annotations

import re
import uuid

#: Runs of decimal digits long enough for a card-number heuristic to consider.
#: Twelve is the shortest Maestro length, which is what ZAP matched; the upper
#: bound is open because a longer run is at least as suspicious.
_DIGIT_RUN = re.compile(r"\d{12,}")


def _passes_luhn(digits: str) -> bool:
    """The checksum every card-number heuristic applies before raising."""
    total = 0
    for index, char in enumerate(reversed(digits)):
        value = int(char)
        if index % 2:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def looks_like_a_card_number(value: str) -> bool:
    """Whether ``value`` contains a run a PII scanner would flag as a card.

    Checks every 12-digit window inside a longer run, not just the run itself: a
    16-digit sequence whose *first twelve* digits are Luhn-valid is flagged just
    the same, and a check that only tested the whole run would miss it.
    """
    for run in _DIGIT_RUN.findall(value):
        for start in range(len(run) - 11):
            if _passes_luhn(run[start : start + 12]):
                return True
    return False


def new_error_id() -> str:
    """A support reference id that cannot be mistaken for a payment card.

    Same shape as before — ``err_`` plus a UUID4 — so nothing downstream changes.
    The loop is not a retry over a flaky operation: each draw is independent and
    the rejected ones are rejected for a property that is decidable on the spot.
    """
    while True:
        candidate = f"err_{uuid.uuid4()}"
        if not looks_like_a_card_number(candidate):
            return candidate
