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
from app.common.auth import get_current_user
from app.common.dependencies import get_graph_repo
from app.common.openapi_responses import UNAUTHORIZED_RESPONSE
from app.data_access.arango.graph_repository import ArangoGraphRepository

router = APIRouter(
    prefix="/family-relationships",
    tags=["family-relationships"],
    dependencies=[Depends(get_current_user)],
    responses=UNAUTHORIZED_RESPONSE,
)


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


@router.post("/pest-risk", status_code=201, response_model=FamilyRelationshipCreatedResponse)
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


@router.post("/compatible", status_code=201, response_model=FamilyRelationshipCreatedResponse)
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


@router.post("/incompatible", status_code=201, response_model=FamilyRelationshipCreatedResponse)
def set_family_incompatible(body: FamilyIncompatibleSet, graph: ArangoGraphRepository = Depends(get_graph_repo)):
    """Create or update an incompatible-neighbour edge between two families."""
    graph.set_family_incompatible(
        body.a_family_key,
        body.b_family_key,
        body.reason,
        body.severity,
    )
    return {"status": "created"}
