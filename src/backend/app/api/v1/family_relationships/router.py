from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.v1.family_relationships.schemas import (
    FamilyCompatibleResponse,
    FamilyCompatibleSet,
    FamilyIncompatibleResponse,
    FamilyIncompatibleSet,
    FamilyPestRiskResponse,
    FamilyRelationshipCreatedResponse,
    PestRiskSet,
)
from app.common.auth import get_current_user, get_is_platform_admin
from app.common.dependencies import get_graph_repo
from app.common.openapi_responses import UNAUTHORIZED_RESPONSE
from app.data_access.arango.graph_repository import ArangoGraphRepository
from app.domain.services.catalogue_authorization import require_platform_admin_for_global_catalogue

router = APIRouter(
    prefix="/family-relationships",
    tags=["family-relationships"],
    dependencies=[Depends(get_current_user)],
    responses=UNAUTHORIZED_RESPONSE,
)


def _require_platform_admin(is_platform_admin: bool = Depends(get_is_platform_admin)) -> None:
    """Gate the three mutating routes on platform-admin (#1156).

    These edges join **botanical families** — global reference data with no
    ``tenant_key``, read by every tenant. Until now the router was gated by
    ``get_current_user`` and nothing else, so any authenticated member, a viewer
    included, could declare that two families share a pest risk or are
    incompatible neighbours, and every other tenant's companion-planting and
    crop-rotation recommendations changed accordingly. REQ-001 §4 already lists
    "CompanionPlanting (Graph-Beziehungen)" and "CropRotation (Graph-Beziehungen)"
    as platform-admin writes; the routes simply never enforced it.

    Shares its refusal with the species, cultivar and botanical-family catalogues
    (#1110) rather than restating it, so the four global-reference surfaces cannot
    drift into answering differently.

    Written as a **route dependency**, unlike the sibling gate in the
    botanical-families router which is a plain call in each handler. The three
    routes here want the identical decision with no per-route variation, so
    declaring it on the decorator both removes the chance of a fourth mutating
    route being added without it and puts the 403 in the generated OpenAPI
    document.
    """
    require_platform_admin_for_global_catalogue(is_platform_admin=is_platform_admin, entity="family relationship")


@router.get("/families/{family_key}/pest-risks", response_model=list[FamilyPestRiskResponse])
def get_pest_risks(
    family_key: Annotated[str, Path(description="Document key of the botanical family.")],
    graph: ArangoGraphRepository = Depends(get_graph_repo),
):
    """List the families that share pest/disease risk with the given family."""
    raw = graph.get_pest_risks(family_key)
    return [
        {
            "family_key": item["family"].get("_key", ""),
            "name": item["family"].get("name"),
            "shared_pests": item.get("shared_pests", []),
            "shared_diseases": item.get("shared_diseases", []),
            "risk_level": item.get("risk_level", "low"),
        }
        for item in raw
    ]


@router.post(
    "/pest-risk",
    status_code=201,
    response_model=FamilyRelationshipCreatedResponse,
    dependencies=[Depends(_require_platform_admin)],
)
def set_pest_risk(body: PestRiskSet, graph: ArangoGraphRepository = Depends(get_graph_repo)):
    """Create or update a shared pest/disease-risk edge between two families."""
    graph.set_pest_risk(
        body.a_family_key,
        body.b_family_key,
        body.shared_pests,
        body.shared_diseases,
        body.risk_level,
    )
    return {"status": "created"}


@router.get("/families/{family_key}/compatible", response_model=list[FamilyCompatibleResponse])
def get_family_compatible(
    family_key: Annotated[str, Path(description="Document key of the botanical family.")],
    graph: ArangoGraphRepository = Depends(get_graph_repo),
):
    """List the families that are beneficial companions of the given family."""
    raw = graph.get_family_compatible(family_key)
    return [
        {
            "family_key": item["family"].get("_key", ""),
            "name": item["family"].get("name"),
            "benefit_type": item.get("benefit_type", ""),
            "compatibility_score": item.get("compatibility_score", 0.0),
            "notes": item.get("notes", ""),
        }
        for item in raw
    ]


@router.post(
    "/compatible",
    status_code=201,
    response_model=FamilyRelationshipCreatedResponse,
    dependencies=[Depends(_require_platform_admin)],
)
def set_family_compatible(body: FamilyCompatibleSet, graph: ArangoGraphRepository = Depends(get_graph_repo)):
    """Create or update a beneficial-companion edge between two families."""
    graph.set_family_compatible(
        body.a_family_key,
        body.b_family_key,
        body.benefit_type,
        body.compatibility_score,
        body.notes,
    )
    return {"status": "created"}


@router.get("/families/{family_key}/incompatible", response_model=list[FamilyIncompatibleResponse])
def get_family_incompatible(
    family_key: Annotated[str, Path(description="Document key of the botanical family.")],
    graph: ArangoGraphRepository = Depends(get_graph_repo),
):
    """List the families that are incompatible neighbours of the given family."""
    raw = graph.get_family_incompatible(family_key)
    return [
        {
            "family_key": item["family"].get("_key", ""),
            "name": item["family"].get("name"),
            "reason": item.get("reason", ""),
            "severity": item.get("severity", "moderate"),
        }
        for item in raw
    ]


@router.post(
    "/incompatible",
    status_code=201,
    response_model=FamilyRelationshipCreatedResponse,
    dependencies=[Depends(_require_platform_admin)],
)
def set_family_incompatible(body: FamilyIncompatibleSet, graph: ArangoGraphRepository = Depends(get_graph_repo)):
    """Create or update an incompatible-neighbour edge between two families."""
    graph.set_family_incompatible(
        body.a_family_key,
        body.b_family_key,
        body.reason,
        body.severity,
    )
    return {"status": "created"}
