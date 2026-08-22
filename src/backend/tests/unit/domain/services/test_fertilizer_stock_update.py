"""Patching a fertilizer stock merges onto the stored row (#1265).

`FertilizerService.update_stock` never read the stored document. It constructed
a fresh `FertilizerStock(fertilizer_key="temp", current_volume_ml=0)`, applied
the patch fields to that, and handed it to `_repo.update_stock` — which is
`BaseArangoRepository.update`, a full REPLACE by its own docstring. So changing
one field detached the stock from its product (`fertilizer_key: "temp"`) and
reset every unpatched field to its model default.

The double returns real `FertilizerStock` / `Fertilizer` instances rather than
mocks, so the model's own validation is in play: a test cannot pass by
constructing a shape the product would reject.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.common.exceptions import NotFoundError
from app.domain.models.fertilizer import Fertilizer, FertilizerStock
from app.domain.services.fertilizer_service import FertilizerService

OWN_FERT = "fert-own"
FOREIGN_FERT = "fert-foreign"
TENANT = "tenant-a"


def _stock() -> FertilizerStock:
    return FertilizerStock(
        _key="stock-1",
        fertilizer_key=OWN_FERT,
        current_volume_ml=750.0,
        purchase_date=date(2026, 5, 1),
        expiry_date=date(2027, 5, 1),
        batch_number="B-123",
        cost_per_liter=12.5,
    )


class _Repo:
    def __init__(self, stocks: dict[str, FertilizerStock], ferts: dict[str, str]) -> None:
        self._stocks_by_key = stocks
        self._ferts = ferts
        self.written: list[tuple[str, FertilizerStock]] = []
        self.deleted: list[str] = []

    def get_stock_or_raise(self, key: str) -> FertilizerStock:
        if key not in self._stocks_by_key:
            raise NotFoundError("FertilizerStock", key)
        return self._stocks_by_key[key]

    def get_or_raise(self, key: str) -> Fertilizer:
        if key not in self._ferts:
            raise NotFoundError("Fertilizer", key)
        # The real required shape: `fertilizer_type` is mandatory. A shorthand
        # without it is rejected by the model, which is why the double uses the
        # real constructor rather than a mock.
        return Fertilizer(
            _key=key,
            product_name="P",
            fertilizer_type="base",
            tenant_key=self._ferts[key],
        )

    def update_stock(self, key: str, stock: FertilizerStock) -> FertilizerStock:
        self.written.append((key, stock))
        return stock

    def delete_stock(self, key: str) -> bool:
        self.deleted.append(key)
        return True


@pytest.fixture
def service() -> tuple[FertilizerService, _Repo]:
    repo = _Repo({"stock-1": _stock()}, {OWN_FERT: TENANT, FOREIGN_FERT: "tenant-b"})
    return FertilizerService(repo), repo  # type: ignore[arg-type]


class TestTheStoredRowSurvives:
    def test_the_stock_stays_attached_to_its_product(self, service) -> None:
        """The headline defect: a patch used to write `fertilizer_key: "temp"`."""
        svc, repo = service

        svc.update_stock("stock-1", {"batch_number": "B-999"}, fertilizer_key=OWN_FERT, tenant_key=TENANT)

        (_, written) = repo.written[0]
        assert written.fertilizer_key == OWN_FERT

    def test_unpatched_fields_are_not_reset(self, service) -> None:
        """`_repo.update` is a full replace, so anything absent from the written
        model is lost. Patching one field used to blank the rest."""
        svc, repo = service

        svc.update_stock("stock-1", {"batch_number": "B-999"}, fertilizer_key=OWN_FERT, tenant_key=TENANT)

        (_, written) = repo.written[0]
        assert written.current_volume_ml == 750.0
        assert written.purchase_date == date(2026, 5, 1)
        assert written.expiry_date == date(2027, 5, 1)
        assert written.cost_per_liter == 12.5
        assert written.batch_number == "B-999"

    def test_purchase_date_is_patchable(self, service) -> None:
        """It was absent from the old allowed-set, so it could only ever be
        blanked — never set."""
        svc, repo = service

        svc.update_stock("stock-1", {"purchase_date": date(2026, 6, 1)}, fertilizer_key=OWN_FERT, tenant_key=TENANT)

        assert repo.written[0][1].purchase_date == date(2026, 6, 1)

    def test_the_product_cannot_be_re_pointed_through_a_patch(self, service) -> None:
        """Moving a stock to another product is a different record, not an edit."""
        svc, repo = service

        svc.update_stock("stock-1", {"fertilizer_key": FOREIGN_FERT}, fertilizer_key=OWN_FERT, tenant_key=TENANT)

        assert repo.written[0][1].fertilizer_key == OWN_FERT


class TestPairing:
    def test_naming_the_wrong_product_is_refused(self, service) -> None:
        """The #1263 shape: the route checked the URL's product, then patched
        whatever stock key followed it."""
        svc, repo = service

        with pytest.raises(NotFoundError):
            svc.update_stock("stock-1", {"batch_number": "X"}, fertilizer_key=FOREIGN_FERT, tenant_key=TENANT)

        assert repo.written == []

    def test_a_stock_of_a_foreign_tenants_product_is_refused(self, service) -> None:
        svc, repo = service
        repo._stocks_by_key["stock-2"] = FertilizerStock(
            _key="stock-2", fertilizer_key=FOREIGN_FERT, current_volume_ml=100.0
        )

        with pytest.raises(NotFoundError):
            svc.update_stock("stock-2", {"batch_number": "X"}, fertilizer_key=FOREIGN_FERT, tenant_key=TENANT)

        assert repo.written == []

    def test_delete_is_pairing_checked_too(self, service) -> None:
        svc, repo = service

        with pytest.raises(NotFoundError):
            svc.delete_stock("stock-1", fertilizer_key=FOREIGN_FERT, tenant_key=TENANT)

        assert repo.deleted == []

    def test_an_own_stock_deletes(self, service) -> None:
        svc, repo = service

        assert svc.delete_stock("stock-1", fertilizer_key=OWN_FERT, tenant_key=TENANT) is True
        assert repo.deleted == ["stock-1"]


class TestTheGuardIsMandatory:
    @pytest.mark.parametrize("method", ["update_stock", "delete_stock"])
    def test_product_and_tenant_are_keyword_only(self, service, method) -> None:
        """#948 convention: a caller that forgets fails loudly, not unscoped."""
        import inspect

        svc, _ = service
        params = inspect.signature(getattr(svc, method)).parameters
        for name in ("fertilizer_key", "tenant_key"):
            assert params[name].kind is inspect.Parameter.KEYWORD_ONLY
            assert params[name].default is inspect.Parameter.empty
