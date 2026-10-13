"""The IPM rows a plant-info seed file carries: pests, diseases, treatments and their edges.

Why this module exists
======================

``seed_plant_info`` and ``seed_adventskalender`` each read ``data.get("pests")``,
``"diseases"``, ``"treatments"``, ``"pest_treatments"`` and ``"disease_treatments"``.
Their files spell the keys as ``plant_info.schema.yaml`` declares them —
``new_pests``, ``new_diseases``, ``new_treatments``, ``treatment_pest_edges``,
``treatment_disease_edges`` — so every read returned the empty default and not one
of these rows was ever seeded. Measured on ArangoDB 3.12.8 after a full seed run:
``Bemisia tabaci``, ``Septoria apiicola`` and ``Ferramol`` absent, 34 pests, 34
diseases, 40 treatments. ``seed_plant_info`` additionally indexed every edge as a
mapping (``target["treatment"]``) while the files write ``[treatment, target]`` pairs —
the fix of the key alone would have raised ``TypeError`` on the first edge.

What the files carry that the models spell differently
======================================================

The schema admits a disease named by ``name`` instead of ``common_name`` and its parts
as ``affected_parts`` (``adventskalender.yaml`` writes both); they are read as
``common_name`` and ``affected_plant_parts``. Nothing is filled in that the file does
not say: a row the model still refuses (a chemical treatment without a safety
interval) is skipped and logged as ``ipm_seed_row_invalid``, the other rows are seeded.

Identity
========

A pest or disease that exists by ``scientific_name``, and a treatment that exists by
``name`` — the unique indexes of the three collections — is not written again. Edges
name their ends by common name; a file may call an existing pest differently than the
row that created it (``Cabbage White Butterfly`` for the stored ``Large Cabbage
White``), so the file's own common name of such a row is mapped onto the existing key.
An edge whose end resolves to nothing is logged (``ipm_seed_edge_unresolved``) and
skipped. Edges are written with ``create_edge_if_absent`` over the unique vertex-pair
index (#2001). The seed registry runs under the migration lock (#2028), so two replicas
never interleave here.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from typing import Any, Final

import structlog
from pydantic import BaseModel, ValidationError

from app.data_access.arango.base_repository import read_all_pages
from app.domain.interfaces.ipm_repository import IIpmRepository
from app.domain.models.ipm import Disease, Pest, Treatment

logger = structlog.get_logger()

#: The keys of ``plant_info.schema.yaml``. ``tests/unit/migrations/test_seed_ipm_rows.py``
#: fails when a seed file carrying one of them is read by no loader.
PESTS_KEY: Final = "new_pests"
DISEASES_KEY: Final = "new_diseases"
TREATMENTS_KEY: Final = "new_treatments"
TREATMENT_PEST_EDGES_KEY: Final = "treatment_pest_edges"
TREATMENT_DISEASE_EDGES_KEY: Final = "treatment_disease_edges"
IPM_KEYS: Final = (PESTS_KEY, DISEASES_KEY, TREATMENTS_KEY, TREATMENT_PEST_EDGES_KEY, TREATMENT_DISEASE_EDGES_KEY)


def _disease_row(entry: dict[str, Any]) -> dict[str, Any]:
    """A disease row with the schema's alternative spellings read as the model's fields."""
    row = dict(entry)
    if not row.get("common_name") and row.get("name"):
        row["common_name"] = row["name"]
    if "affected_plant_parts" not in row and "affected_parts" in row:
        row["affected_plant_parts"] = row["affected_parts"]
    return row


def _build[M: BaseModel](
    rows: Iterable[dict[str, Any]],
    model: type[M],
    *,
    source: str,
    kind: str,
    prepare: Callable[[dict[str, Any]], dict[str, Any]] = dict,
) -> list[M]:
    """Validate every row; skip and log one the model refuses."""
    built: list[M] = []
    for entry in rows:
        row = prepare(entry)
        try:
            built.append(model.model_validate(row))
        except ValidationError as exc:
            logger.warning(
                "ipm_seed_row_invalid",
                source=source,
                kind=kind,
                row=str(row.get("scientific_name") or row.get("name") or ""),
                errors=[f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in exc.errors()],
            )
    return built


def build_pests(data: dict[str, Any], *, source: str) -> list[Pest]:
    """The valid pests of a seed file (``new_pests``)."""
    return _build(data.get(PESTS_KEY) or [], Pest, source=source, kind="pest")


def build_diseases(data: dict[str, Any], *, source: str) -> list[Disease]:
    """The valid diseases of a seed file (``new_diseases``)."""
    return _build(data.get(DISEASES_KEY) or [], Disease, source=source, kind="disease", prepare=_disease_row)


def build_treatments(data: dict[str, Any], *, source: str) -> list[Treatment]:
    """The valid treatments of a seed file (``new_treatments``)."""
    return _build(data.get(TREATMENTS_KEY) or [], Treatment, source=source, kind="treatment")


def _pairs(entries: Iterable[Any], *, source: str, key: str) -> list[tuple[str, str]]:
    """The ``[treatment, target]`` pairs of ``key``; anything else is logged and skipped.

    ``adventskalender.yaml`` carries a stray ``- Lamiaceae`` under
    ``treatment_disease_edges`` (a half commented-out block); indexed as a pair it
    read as treatment ``L``, disease ``a``.
    """
    pairs: list[tuple[str, str]] = []
    for entry in entries:
        if isinstance(entry, list | tuple) and len(entry) == 2:
            pairs.append((str(entry[0]), str(entry[1])))
        else:
            logger.warning("ipm_seed_edge_malformed", source=source, key=key, entry=str(entry)[:80])
    return pairs


def build_target_edges(data: dict[str, Any], *, source: str) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """``(treatment, pest)`` and ``(treatment, disease)`` pairs, by name / common name."""
    return (
        _pairs(data.get(TREATMENT_PEST_EDGES_KEY) or [], source=source, key=TREATMENT_PEST_EDGES_KEY),
        _pairs(data.get(TREATMENT_DISEASE_EDGES_KEY) or [], source=source, key=TREATMENT_DISEASE_EDGES_KEY),
    )


@dataclass(frozen=True)
class IpmSeedCounts:
    """What one file's IPM rows did: created rows, edges linked (created or already there), unresolved."""

    pests_created: int
    diseases_created: int
    treatments_created: int
    edges_linked: int
    edges_unresolved: int


def _key_map(stored: Iterable[Any], name_of: Callable[[Any], str]) -> dict[str, str]:
    return {name_of(row): row.key or "" for row in stored}


def _link_edges(
    edges: list[tuple[str, str]],
    treatment_keys: dict[str, str],
    target_keys: dict[str, str],
    link: Callable[[str, str], None],
    source: str,
    kind: str,
) -> tuple[int, int]:
    """Link every pair whose both ends resolve; return ``(linked, unresolved)``."""
    linked = 0
    unresolved = 0
    for treatment_name, target_name in edges:
        t_key = treatment_keys.get(treatment_name, "")
        x_key = target_keys.get(target_name, "")
        if not (t_key and x_key):
            unresolved += 1
            logger.info(
                "ipm_seed_edge_unresolved",
                source=source,
                kind=kind,
                treatment=treatment_name,
                target=target_name,
                treatment_found=bool(t_key),
                target_found=bool(x_key),
            )
            continue
        link(t_key, x_key)
        linked += 1
    return linked, unresolved


def seed_ipm_rows(ipm_repo: IIpmRepository, data: dict[str, Any], *, source: str) -> IpmSeedCounts:
    """Create the file's absent pests, diseases and treatments, then their target edges.

    Args:
        ipm_repo: The IPM repository the seed writes through.
        data: The parsed seed file.
        source: The file name, for the log.

    Returns:
        The counts of what was created and what could not be linked.
    """
    pests = build_pests(data, source=source)
    diseases = build_diseases(data, source=source)
    treatments = build_treatments(data, source=source)
    pest_edges, disease_edges = build_target_edges(data, source=source)

    stored_pests = {p.scientific_name: p for p in read_all_pages(ipm_repo.get_all_pests)}
    pest_keys = _key_map(stored_pests.values(), lambda p: p.common_name)
    pests_created = 0
    for pest in pests:
        found = stored_pests.get(pest.scientific_name)
        if found is None:
            found = ipm_repo.create_pest(pest)
            stored_pests[pest.scientific_name] = found
            pests_created += 1
        pest_keys[pest.common_name] = found.key or ""

    stored_diseases = {d.scientific_name: d for d in read_all_pages(ipm_repo.get_all_diseases)}
    disease_keys = _key_map(stored_diseases.values(), lambda d: d.common_name)
    diseases_created = 0
    for disease in diseases:
        found_disease = stored_diseases.get(disease.scientific_name)
        if found_disease is None:
            found_disease = ipm_repo.create_disease(disease)
            stored_diseases[disease.scientific_name] = found_disease
            diseases_created += 1
        disease_keys[disease.common_name] = found_disease.key or ""

    stored_treatments = {t.name: t for t in read_all_pages(ipm_repo.get_all_treatments)}
    treatments_created = 0
    for treatment in treatments:
        if treatment.name not in stored_treatments:
            stored_treatments[treatment.name] = ipm_repo.create_treatment(treatment)
            treatments_created += 1
    treatment_keys = _key_map(stored_treatments.values(), lambda t: t.name)

    pest_linked, pest_unresolved = _link_edges(
        pest_edges, treatment_keys, pest_keys, lambda t, x: ipm_repo.create_targets_pest_edge(t, x), source, "pest"
    )
    disease_linked, disease_unresolved = _link_edges(
        disease_edges,
        treatment_keys,
        disease_keys,
        lambda t, x: ipm_repo.create_targets_disease_edge(t, x),
        source,
        "disease",
    )
    linked = pest_linked + disease_linked
    unresolved = pest_unresolved + disease_unresolved

    counts = IpmSeedCounts(
        pests_created=pests_created,
        diseases_created=diseases_created,
        treatments_created=treatments_created,
        edges_linked=linked,
        edges_unresolved=unresolved,
    )
    logger.info("ipm_seed_rows", source=source, **asdict(counts))
    return counts
