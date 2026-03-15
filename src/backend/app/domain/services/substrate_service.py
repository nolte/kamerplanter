from typing import TYPE_CHECKING

from app.common.exceptions import NotFoundError, ValidationError
from app.domain.engines.substrate_lifecycle_manager import SubstrateLifecycleManager
from app.domain.engines.substrate_mix_engine import calculate_mix_properties
from app.domain.models.substrate import MixComponent, Substrate, SubstrateBatch

if TYPE_CHECKING:
    from datetime import date

    from app.common.enums import IrrigationStrategy, SubstrateType
    from app.common.types import BatchKey, SlotKey, SubstrateKey
    from app.domain.interfaces.substrate_repository import ISubstrateRepository


class SubstrateService:
    def __init__(self, substrate_repo: ISubstrateRepository) -> None:
        self._repo = substrate_repo
        self._lifecycle_mgr = SubstrateLifecycleManager(substrate_repo)

    def list_substrates(self, offset: int = 0, limit: int = 50) -> tuple[list[Substrate], int]:
        return self._repo.get_all_substrates(offset, limit)

    def get_substrate(self, key: SubstrateKey) -> Substrate:
        substrate = self._repo.get_substrate_by_key(key)
        if substrate is None:
            raise NotFoundError("Substrate", key)
        return substrate

    def create_substrate(self, substrate: Substrate) -> Substrate:
        return self._repo.create_substrate(substrate)

    def update_substrate(self, key: SubstrateKey, substrate: Substrate) -> Substrate:
        self.get_substrate(key)
        return self._repo.update_substrate(key, substrate)

    def delete_substrate(self, key: SubstrateKey) -> bool:
        self.get_substrate(key)
        return self._repo.delete_substrate(key)

    def list_batches(self, substrate_key: SubstrateKey) -> list[SubstrateBatch]:
        self.get_substrate(substrate_key)
        return self._repo.get_batches_by_substrate(substrate_key)

    def get_batch(self, key: BatchKey) -> SubstrateBatch:
        batch = self._repo.get_batch_by_key(key)
        if batch is None:
            raise NotFoundError("SubstrateBatch", key)
        return batch

    def create_batch(self, batch: SubstrateBatch) -> SubstrateBatch:
        self.get_substrate(batch.substrate_key)
        return self._repo.create_batch(batch)

    def update_batch(self, key: BatchKey, batch: SubstrateBatch) -> SubstrateBatch:
        self.get_batch(key)
        return self._repo.update_batch(key, batch)

    def delete_batch(self, key: BatchKey) -> bool:
        self.get_batch(key)
        return self._repo.delete_batch(key)

    def check_reusability(
        self,
        batch_key: BatchKey,
    ) -> tuple[bool, list[str], list[dict[str, str | float]], float, date | None]:
        self.get_batch(batch_key)
        return self._lifecycle_mgr.check_reusability(batch_key)

    def prepare_reuse(self, batch_key: BatchKey) -> dict:
        batch = self.get_batch(batch_key)
        self.get_substrate(batch.substrate_key)
        can_reuse, issues, prep_steps, prep_time, ready_date = self._lifecycle_mgr.check_reusability(batch_key)
        if not can_reuse:
            return {
                "can_reuse": False,
                "issues": issues,
                "preparation_steps": [],
                "estimated_prep_time_hours": 0,
                "ready_date": None,
            }
        return {
            "can_reuse": True,
            "issues": [],
            "preparation_steps": prep_steps,
            "estimated_prep_time_hours": prep_time,
            "ready_date": ready_date,
        }

    def assign_batch_to_slot(self, batch_key: BatchKey, slot_key: SlotKey) -> dict:
        self.get_batch(batch_key)
        return self._repo.assign_batch_to_slot(batch_key, slot_key)

    def create_mix(
        self,
        components: list[MixComponent],
        name_de: str = "",
        name_en: str = "",
    ) -> Substrate:
        """Create a substrate mix from multiple component substrates."""
        if len(components) < 2:
            raise ValidationError("A mix requires at least 2 components.")
        total = sum(c.fraction for c in components)
        if abs(total - 1.0) > 0.01:
            raise ValidationError(f"Component fractions must sum to 1.0, got {total:.4f}.")

        # Resolve all component substrates
        substrate_map: dict[str, Substrate] = {}
        for comp in components:
            sub = self._repo.get_substrate_by_key(comp.substrate_key)
            if sub is None:
                raise NotFoundError("Substrate", comp.substrate_key)
            if sub.is_mix:
                raise ValidationError(f"Cannot use mix '{comp.substrate_key}' as a component (no nested mixes).")
            substrate_map[comp.substrate_key] = sub

        props = calculate_mix_properties(components, substrate_map)

        mix = Substrate(
            type=props["type"],
            brand=None,
            name_de=name_de,
            name_en=name_en,
            is_mix=True,
            mix_components=components,
            ph_base=props["ph_base"],
            ec_base_ms=props["ec_base_ms"],
            water_retention=props["water_retention"],
            air_porosity_percent=props["air_porosity_percent"],
            composition=props["composition"],
            buffer_capacity=props["buffer_capacity"],
            reusable=props["reusable"],
            max_reuse_cycles=props["max_reuse_cycles"],
            water_holding_capacity_percent=props["water_holding_capacity_percent"],
            easily_available_water_percent=props["easily_available_water_percent"],
            cec_meq_per_100g=props["cec_meq_per_100g"],
            bulk_density_g_per_l=props["bulk_density_g_per_l"],
            irrigation_strategy=props["irrigation_strategy"],
        )
        return self._repo.create_substrate(mix)

    def preview_mix(self, components: list[MixComponent]) -> dict:
        """Calculate blended properties without saving."""
        if len(components) < 2:
            raise ValidationError("A mix requires at least 2 components.")

        substrate_map: dict[str, Substrate] = {}
        for comp in components:
            sub = self._repo.get_substrate_by_key(comp.substrate_key)
            if sub is None:
                raise NotFoundError("Substrate", comp.substrate_key)
            substrate_map[comp.substrate_key] = sub

        return calculate_mix_properties(components, substrate_map)

    @staticmethod
    def get_irrigation_strategy(substrate_type: SubstrateType) -> IrrigationStrategy:
        return SubstrateLifecycleManager.get_irrigation_strategy(substrate_type)
