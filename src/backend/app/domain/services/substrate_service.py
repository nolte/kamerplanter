from collections.abc import Callable
from datetime import date

from app.common.enums import IrrigationStrategy, SubstrateType, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.common.types import BatchKey, SlotKey, SubstrateKey
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.substrate_lifecycle_manager import SubstrateLifecycleManager
from app.domain.engines.substrate_mix_engine import calculate_mix_properties
from app.domain.interfaces.substrate_repository import ISubstrateRepository
from app.domain.models.substrate import MixComponent, Substrate, SubstrateBatch
from app.domain.services.catalogue_authorization import (
    require_platform_admin_for_global_catalogue,
    require_role_for_catalogue_create,
)


class SubstrateService:
    def __init__(self, substrate_repo: ISubstrateRepository) -> None:
        self._repo = substrate_repo
        self._lifecycle_mgr = SubstrateLifecycleManager(substrate_repo)

    # ── Substrate catalogue — hybrid, like species (#1195) ───────────────

    def list_substrates(
        self, offset: int = 0, limit: int = 50, query: str | None = None, *, tenant_key: str | None = None
    ) -> tuple[list[Substrate], int]:
        return self._repo.get_all_substrates(offset, limit, query, tenant_key=tenant_key)

    def get_substrate(self, key: SubstrateKey, *, tenant_key: str | None = None) -> Substrate:
        """Return one substrate, tenant-scoped when ``tenant_key`` is given (#1195).

        ``None`` is the unscoped system-context load internal callers use (the
        mix resolver, the seed loaders, and this service's own gate loads).

        A string admits the caller's own mixes plus the global media and answers
        a *foreign* tenant's mix with :class:`NotFoundError` — a 404, never a 403,
        so the by-key route cannot be used as a cross-tenant existence oracle.
        Same shape as ``SpeciesService.get_species``.
        """
        substrate = self._repo.get_substrate_or_raise(key)
        if tenant_key is not None and substrate.tenant_key not in (tenant_key, ""):
            raise NotFoundError("Substrate", key)
        return substrate

    def get_growing_medium(self, key: SubstrateKey, *, tenant_key: str | None = None) -> Substrate:
        """Resolve a substrate that a plant is to grow **in**, refusing an amendment.

        ``BioBizz Pre·Mix`` is a soil conditioner: 30 % peat and the rest bone meal,
        blood meal, guano, dolomite, seaweed and leonardite. Nothing is planted in
        it, but it sat in the same catalogue as the media and was therefore offered
        as one (#1152 §E).

        The predicate lives here rather than at each call site, because that is the
        failure this repository keeps paying for: a guard written into one route and
        not its siblings. Resolution is the caller's scope, so a foreign medium
        still answers 404 before the medium/amendment question is even asked.
        """
        substrate = self.get_substrate(key, tenant_key=tenant_key)
        if substrate.is_amendment:
            raise ValidationError(
                f"Substrate '{substrate.name_de or substrate.name_en or key}' is a soil amendment, "
                "not a growing medium — a plant cannot be planted in it."
            )
        return substrate

    def create_substrate(
        self,
        substrate: Substrate,
        *,
        caller_role: TenantRole | None = None,
        is_platform_admin: bool = False,
    ) -> Substrate:
        """Create a catalogue entry — a base medium or a tenant's own mix.

        The gate is the shared create gate every hybrid catalogue uses
        (:func:`_authorize_tenant_owned_create` in ``SpeciesService``, SEC-005):
        a viewer may not create, a platform admin bypasses the domain rank, and
        ``caller_role is None`` stays the system-context escape the seed loaders
        need. Ownership itself is stamped by the route from the active tenant.
        """
        require_role_for_catalogue_create(
            plural_noun="substrates", caller_role=caller_role, is_platform_admin=is_platform_admin
        )
        return self._repo.create_substrate(substrate)

    def update_substrate(
        self,
        key: SubstrateKey,
        substrate: Substrate,
        *,
        tenant_key: str | None = None,
        caller_role: TenantRole | None = None,
        is_platform_admin: bool = False,
    ) -> Substrate:
        existing = self.get_substrate(key)
        self._authorize_write(
            existing, key, tenant_key, caller_role, is_platform_admin, MembershipEngine.can_edit_resource
        )
        # Ownership is assigned once, at create time, and afterwards only by an
        # explicit migration — a full-replace update must not be able to move a
        # tenant's mix into the global catalogue, nor claim a global medium.
        substrate.tenant_key = existing.tenant_key
        return self._repo.update_substrate(key, substrate)

    def delete_substrate(
        self,
        key: SubstrateKey,
        *,
        tenant_key: str | None = None,
        caller_role: TenantRole | None = None,
        is_platform_admin: bool = False,
    ) -> bool:
        existing = self.get_substrate(key)
        self._authorize_write(
            existing, key, tenant_key, caller_role, is_platform_admin, MembershipEngine.can_delete_resource
        )
        return self._repo.delete_substrate(key)

    # ── Batches — strictly owned, no global arm (#1195) ──────────────────

    def list_batches(self, substrate_key: SubstrateKey, *, tenant_key: str | None = None) -> list[SubstrateBatch]:
        self.get_substrate(substrate_key, tenant_key=tenant_key)
        return self._repo.get_batches_by_substrate(substrate_key, tenant_key=tenant_key)

    def get_batch(self, key: BatchKey, *, tenant_key: str | None = None) -> SubstrateBatch:
        """Return one batch, refusing a foreign one with 404 (#1195).

        Strict equality, not the catalogue's union: a batch has exactly one owner
        and ``""`` is not a shareable global marker here but the mark of a row the
        ``v0043`` backfill could not attribute.
        """
        batch = self._repo.get_batch_or_raise(key)
        if tenant_key is not None and batch.tenant_key != tenant_key:
            raise NotFoundError("SubstrateBatch", key)
        return batch

    def create_batch(
        self,
        batch: SubstrateBatch,
        *,
        tenant_key: str | None = None,
        caller_role: TenantRole | None = None,
        is_platform_admin: bool = False,
    ) -> SubstrateBatch:
        # The parent substrate is resolved in the caller's scope, so a batch can
        # never be hung off a foreign tenant's mix.
        self.get_substrate(batch.substrate_key, tenant_key=tenant_key)
        require_role_for_catalogue_create(
            plural_noun="substrates", caller_role=caller_role, is_platform_admin=is_platform_admin
        )
        if tenant_key is not None:
            batch.tenant_key = tenant_key
        return self._repo.create_batch(batch)

    def update_batch(
        self,
        key: BatchKey,
        batch: SubstrateBatch,
        *,
        tenant_key: str | None = None,
        caller_role: TenantRole | None = None,
        is_platform_admin: bool = False,
    ) -> SubstrateBatch:
        existing = self.get_batch(key, tenant_key=tenant_key)
        self._authorize_batch_write(caller_role, is_platform_admin, MembershipEngine.can_edit_resource)
        batch.tenant_key = existing.tenant_key
        return self._repo.update_batch(key, batch)

    def delete_batch(
        self,
        key: BatchKey,
        *,
        tenant_key: str | None = None,
        caller_role: TenantRole | None = None,
        is_platform_admin: bool = False,
    ) -> bool:
        self.get_batch(key, tenant_key=tenant_key)
        self._authorize_batch_write(caller_role, is_platform_admin, MembershipEngine.can_delete_resource)
        return self._repo.delete_batch(key)

    # ── the two gates ────────────────────────────────────────────────────

    @staticmethod
    def _authorize_write(
        existing: Substrate,
        key: str,
        tenant_key: str | None,
        caller_role: TenantRole | None,
        is_platform_admin: bool,
        can_role_write: Callable[[TenantRole], bool],
    ) -> None:
        """The hybrid-catalogue write gate, identical in shape to the species one.

        Four arms: system context passes, a *foreign* mix is 404 (ownership
        hiding), the *global* base catalogue is platform-admin only (the #1120
        rule), and an *own* mix needs a writing role.
        """
        if tenant_key is None:
            return
        if existing.tenant_key not in (tenant_key, ""):
            raise NotFoundError("Substrate", key)
        if existing.tenant_key == "":
            require_platform_admin_for_global_catalogue(is_platform_admin=is_platform_admin, entity="Substrate")
            return
        if not is_platform_admin and not (caller_role is not None and can_role_write(caller_role)):
            raise ForbiddenError("Your role may not modify substrates in this tenant.")

    @staticmethod
    def _authorize_batch_write(
        caller_role: TenantRole | None,
        is_platform_admin: bool,
        can_role_write: Callable[[TenantRole], bool],
    ) -> None:
        """Batches have no global arm, so the gate is only the role check.

        Ownership was already decided by :meth:`get_batch`, which 404s a foreign
        batch before this runs — the same load-then-gate order the species writes
        use, and the reason a foreign key and an absent key are indistinguishable.
        """
        if caller_role is None and not is_platform_admin:
            return
        if not is_platform_admin and not (caller_role is not None and can_role_write(caller_role)):
            raise ForbiddenError("Your role may not modify substrate batches in this tenant.")

    def check_reusability(
        self,
        batch_key: BatchKey,
        *,
        tenant_key: str | None = None,
    ) -> tuple[bool, list[str], list[dict[str, str | float]], float, date | None]:
        # Scoped through the same by-key gate the reads use (#1195): a reusability
        # verdict quotes the batch's pH/EC history and cycle count back to the
        # caller, so an unscoped check is a read of a foreign batch wearing an
        # assessment as cover.
        self.get_batch(batch_key, tenant_key=tenant_key)
        return self._lifecycle_mgr.check_reusability(batch_key)

    def prepare_reuse(self, batch_key: BatchKey, *, tenant_key: str | None = None) -> dict:
        batch = self.get_batch(batch_key, tenant_key=tenant_key)
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
        *,
        tenant_key: str | None = None,
        caller_role: TenantRole | None = None,
        is_platform_admin: bool = False,
    ) -> Substrate:
        """Create a substrate mix from multiple component substrates.

        The mix is **owned by the tenant that made it** (operator decision on
        #1098): a community garden that blends its own medium keeps it in its own
        catalogue rather than pushing it into the one every tenant reads.

        Components are resolved *in the caller's scope*, so a mix can never be
        built out of a foreign tenant's medium — and, because a foreign component
        answers the same 404 an absent one does, the resolution cannot be used to
        probe which mixes other tenants hold.
        """
        if len(components) < 2:
            raise ValidationError("A mix requires at least 2 components.")
        total = sum(c.fraction for c in components)
        if abs(total - 1.0) > 0.01:
            raise ValidationError(f"Component fractions must sum to 1.0, got {total:.4f}.")

        require_role_for_catalogue_create(
            plural_noun="substrate mixes", caller_role=caller_role, is_platform_admin=is_platform_admin
        )

        # Resolve all component substrates — in the caller's scope (#1195).
        substrate_map: dict[str, Substrate] = {}
        for comp in components:
            sub = self.get_substrate(comp.substrate_key, tenant_key=tenant_key)
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
            # A blend of a limed medium and an inert one is still limed (#1175).
            # `is_amendment` is deliberately *not* carried over: an amendment is a
            # legal component, but what you get by blending it into a medium is a
            # medium.
            additives=props["additives"],
            buffer_capacity=props["buffer_capacity"],
            reusable=props["reusable"],
            max_reuse_cycles=props["max_reuse_cycles"],
            water_holding_capacity_percent=props["water_holding_capacity_percent"],
            easily_available_water_percent=props["easily_available_water_percent"],
            cec_meq_per_100cm3=props["cec_meq_per_100cm3"],
            bulk_density_g_per_l=props["bulk_density_g_per_l"],
            irrigation_strategy=props["irrigation_strategy"],
            tenant_key=tenant_key or "",
        )
        return self._repo.create_substrate(mix)

    def preview_mix(self, components: list[MixComponent], *, tenant_key: str | None = None) -> dict:
        """Calculate blended properties without saving.

        Scoped like :meth:`create_mix` even though it persists nothing: a preview
        that resolved components unscoped would report a foreign tenant's medium
        properties — pH, EC, CEC, composition — back to the caller, which is a
        read of that tenant's data wearing a calculation as cover.
        """
        if len(components) < 2:
            raise ValidationError("A mix requires at least 2 components.")

        substrate_map: dict[str, Substrate] = {}
        for comp in components:
            sub = self.get_substrate(comp.substrate_key, tenant_key=tenant_key)
            substrate_map[comp.substrate_key] = sub

        return calculate_mix_properties(components, substrate_map)

    @staticmethod
    def get_irrigation_strategy(substrate_type: SubstrateType) -> IrrigationStrategy:
        return SubstrateLifecycleManager.get_irrigation_strategy(substrate_type)
