"""#1175 — a soil amendment must not be selectable as the medium a plant grows in.

``BioBizz Pre·Mix`` is a soil conditioner: 30 % peat and the rest bone meal, blood
meal, guano, dolomite, seaweed and leonardite. It shipped typed ``peat`` and
therefore sat in the same catalogue as the growing media, offered by every picker
that lists substrates (#1152 §E).

The fix is a predicate in the service rather than a check at each call site,
because a guard written into one route and not its siblings is the drift this
repository keeps paying for. These tests assert the predicate itself and, for the
one backend surface that resolves a plant's medium today, that the surface calls
*it* and not the plain read.
"""

from __future__ import annotations

import pytest

from app.common.exceptions import NotFoundError, ValidationError
from app.domain.models.substrate import Substrate
from app.domain.services.substrate_service import SubstrateService


class _OneSubstrateRepo:
    """Serves exactly one record by key, and 404s anything else.

    Deliberately *not* a mock that returns whatever it is asked for: the point of
    this suite is that a real ``Substrate`` carrying ``is_amendment`` is refused,
    and a double that invented the flag on demand would certify nothing.
    """

    def __init__(self, substrate: Substrate) -> None:
        self._substrate = substrate

    def get_substrate_or_raise(self, key: str) -> Substrate:
        if key != self._substrate.key:
            raise NotFoundError("Substrate", key)
        return self._substrate


def _service(**overrides) -> SubstrateService:
    substrate = Substrate(_key="s1", name_de="BioBizz Pre·Mix (Bodenverbesserer)", **overrides)
    return SubstrateService(_OneSubstrateRepo(substrate))


def test_a_growing_medium_resolves_normally() -> None:
    """Control. Without it the rule below would also pass on a method that refused
    everything, which is the failure mode of a guard tested only in its red arm."""
    medium = _service(is_amendment=False).get_growing_medium("s1")

    assert medium.key == "s1"


def test_an_amendment_is_refused_as_a_growing_medium() -> None:
    with pytest.raises(ValidationError) as exc:
        _service(is_amendment=True).get_growing_medium("s1")

    # The message names the product, because the caller is an agent or a form that
    # has to tell the operator which of several selections was rejected.
    assert "Pre·Mix" in str(exc.value)


def test_the_plain_read_still_returns_the_amendment() -> None:
    """The catalogue keeps it, and so do the mix components.

    Blending Pre·Mix into a soil is what the product is *for*, and its detail page
    has to be reachable. The defect was never that the record exists — it was that
    it was offered as something to plant in. A fix that hid it from
    ``get_substrate`` would have broken the legitimate uses to close the illegitimate
    one.
    """
    assert _service(is_amendment=True).get_substrate("s1").is_amendment is True


def test_the_scope_check_runs_before_the_amendment_check() -> None:
    """A foreign amendment answers 404, not "that is an amendment".

    Otherwise the refusal message becomes a cross-tenant existence oracle: a caller
    could distinguish "exists elsewhere and is an amendment" from "does not exist".

    ``tenant_key="owner"`` and not the seeded ``""`` — the first version of this
    test used a global record and passed for the wrong reason, because the hybrid
    catalogue admits ``""`` to every tenant, so nothing foreign was ever being
    resolved.
    """
    service = _service(is_amendment=True, tenant_key="owner")

    with pytest.raises(NotFoundError):
        service.get_growing_medium("s1", tenant_key="other-tenant")
