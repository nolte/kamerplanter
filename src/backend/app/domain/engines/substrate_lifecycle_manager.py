from app.common.exceptions import SubstrateExhaustedError
from app.domain.interfaces.substrate_repository import ISubstrateRepository


class SubstrateLifecycleManager:
    """Manages substrate batch reuse and lifecycle."""

    def __init__(self, substrate_repo: ISubstrateRepository) -> None:
        self._substrate_repo = substrate_repo

    def check_reusability(self, batch_key: str) -> tuple[bool, list[str]]:
        """Check if a substrate batch can be reused.
        Returns (can_reuse, treatments_needed).
        """
        batch = self._substrate_repo.get_batch_by_key(batch_key)
        if batch is None:
            return False, ["Batch not found"]

        substrate = self._substrate_repo.get_substrate_by_key(batch.substrate_key)
        if substrate is None:
            return False, ["Substrate type not found"]

        if not substrate.reusable:
            return False, ["Substrate type is not reusable"]

        if batch.cycles_used >= substrate.max_reuse_cycles:
            return False, [f"Max reuse cycles exceeded ({batch.cycles_used}/{substrate.max_reuse_cycles})"]

        treatments: list[str] = []

        # pH check
        if batch.ph_current is not None and (batch.ph_current < 5.5 or batch.ph_current > 7.0):
            treatments.append(f"pH adjustment needed (current: {batch.ph_current})")

        # EC check
        if batch.ec_current_ms is not None and batch.ec_current_ms > 1.0:
            treatments.append(f"Flush required to lower EC (current: {batch.ec_current_ms} mS)")

        treatments.append("Sanitize before reuse")

        return True, treatments

    def check_or_raise(self, batch_key: str) -> None:
        can_reuse, issues = self.check_reusability(batch_key)
        if not can_reuse:
            batch = self._substrate_repo.get_batch_by_key(batch_key)
            cycles = batch.cycles_used if batch else 0
            raise SubstrateExhaustedError(batch_key, cycles)
