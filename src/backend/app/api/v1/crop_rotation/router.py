from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.v1.crop_rotation.schemas import (
    RotationSuccessorCreatedResponse,
    RotationSuccessorResponse,
    RotationSuccessorSet,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_graph_repo
from app.common.openapi_responses import UNAUTHORIZED_RESPONSE
from app.data_access.arango.graph_repository import ArangoGraphRepository

router = APIRouter(
    prefix="/crop-rotation",
    tags=["crop-rotation"],
    dependencies=[Depends(get_current_user)],
    responses=UNAUTHORIZED_RESPONSE,
)


@router.get("/counts", response_model=dict[str, int])
def get_rotation_successor_counts(graph: ArangoGraphRepository = Depends(get_graph_repo)) -> dict[str, int]:
    """Return per-family rotation-successor counts for the whole catalogue."""
    # Whole-catalogue aggregate keyed by family_key: one batch AQL request feeds
    # the per-family successor-count chips in the "Von Familie" dropdown (no N+1).
    # Family rotation data is global reference data — no tenant scoping needed.
    return graph.get_rotation_successor_counts()


@router.get("/families/{family_key}/successors", response_model=list[RotationSuccessorResponse])
def get_rotation_successors(
    family_key: Annotated[str, Path(description="Document key of the botanical family.")],
    graph: ArangoGraphRepository = Depends(get_graph_repo),
):
    """List the botanical families that may follow the given family in crop rotation."""
    raw = graph.get_rotation_successors(family_key)
    # The graph vertex already carries the full family document (common_name_de/_en,
    # rotation_category); pass those through verbatim so the presentation layer can
    # lead with the German common name and humanise the rotation-category code
    # without a second query (REQ-567/A).
    return [
        {
            "family_key": item["family"].get("_key", ""),
            "name": item["family"].get("name"),
            "common_name_de": item["family"].get("common_name_de", ""),
            "common_name_en": item["family"].get("common_name_en", ""),
            "rotation_category": item["family"].get("rotation_category", ""),
            "wait_years": item.get("wait_years", 1),
            "benefit_score": item.get("benefit_score", 0.0),
            "benefit_reason": item.get("benefit_reason", ""),
        }
        for item in raw
    ]


@router.post("/successors", status_code=201, response_model=RotationSuccessorCreatedResponse)
def set_rotation_successor(body: RotationSuccessorSet, graph: ArangoGraphRepository = Depends(get_graph_repo)):
    """Create or update a rotation-successor edge between two botanical families."""
    graph.set_rotation_successor(
        body.from_family_key,
        body.to_family_key,
        body.wait_years,
        benefit_score=body.benefit_score,
        benefit_reason=body.benefit_reason,
    )
    return {"status": "created"}
