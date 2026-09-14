"""REQ-022 / #1422 round 3 — a new plant gets its care profile at creation.

**The circle this breaks.** `get_or_create_profile` is the only thing that creates a
`CareProfile`. The nightly generator (`app/tasks/care_tasks.py`) iterates **stored
profiles**. The first confirmation needs a task the generator produced, and the
generator needs a profile. Nothing closed that loop on purpose: it was closed by a
side effect, because `GET .../profile` and the tenant care dashboard both persisted a
profile when they were *read*.

Round 2 of this PR removed those writes — a read must not write, least of all one a
viewer can trigger for every plant of the tenant at once. That was right, and it
exposed what had been leaning on them: without a bootstrap, a freshly created plant
would never receive a care task at all. The feature would have stopped silently,
which is the worst way for one to stop.

So the profile is created with the plant, where it belongs, and this file is what
keeps the circle from quietly closing again.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from app.domain.models.plant_instance import PlantInstance
from app.domain.services.plant_instance_service import PlantInstanceService


def _service(bootstrap=None) -> tuple[PlantInstanceService, MagicMock]:
    repo = MagicMock()
    repo.create.side_effect = lambda plant: plant.model_copy(update={"key": "pi-new"})
    service = PlantInstanceService(
        repo,
        site_repo=MagicMock(),
        rotation_validator=MagicMock(),
        companion_engine=MagicMock(),
        care_profile_bootstrap=bootstrap,
    )
    service._verify_site_ownership = lambda plant: None  # type: ignore[method-assign]
    service._sync_overwintering_for_site = lambda plant: None  # type: ignore[method-assign]
    return service, repo


def _plant() -> PlantInstance:
    return PlantInstance(
        instance_id="p-1",
        species_key="sp-1",
        planted_on=date(2026, 1, 1),
        tenant_key="tenant-a",
    )


def test_creating_a_plant_creates_its_care_profile():
    """The bootstrap runs, and it runs with the stored plant.

    With the *stored* one, not the argument: the profile is keyed on the plant's
    document key, which only exists after the insert.
    """
    bootstrap = MagicMock()
    service, _repo = _service(bootstrap)

    created = service.create_plant(_plant(), skip_validation=True)

    bootstrap.assert_called_once()
    assert bootstrap.call_args.args[0].key == created.key == "pi-new"


def test_a_failing_bootstrap_does_not_fail_the_plant():
    """Best-effort, like the overwintering materialisation beside it.

    A care profile that could not be written is a missing reminder; a plant that
    could not be created because of it is lost work the user already did.
    """
    bootstrap = MagicMock(side_effect=RuntimeError("care service unavailable"))
    service, repo = _service(bootstrap)

    created = service.create_plant(_plant(), skip_validation=True)

    assert created.key == "pi-new"
    repo.create.assert_called_once()


def test_the_service_still_works_without_a_bootstrap():
    """The collaborator is optional, as every other one on this service is.

    Without this, wiring it as required would break every test and caller that
    constructs the service directly — and there are many.
    """
    service, _repo = _service(bootstrap=None)

    assert service.create_plant(_plant(), skip_validation=True).key == "pi-new"
