from fastapi import APIRouter, Depends

from app.api.v1.crop_rotation.schemas import RotationSuccessorSet
from app.common.auth import get_current_user
from app.common.dependencies import get_graph_repo
from app.data_access.arango.graph_repository import ArangoGraphRepository

router = APIRouter(prefix="/crop-rotation", tags=["crop-rotation"], dependencies=[Depends(get_current_user)])


@router.get("/families/{family_key}/successors")
def get_rotation_successors(family_key: str, graph: ArangoGraphRepository = Depends(get_graph_repo)):
    raw = graph.get_rotation_successors(family_key)
    return [
        {
            "family_key": item["family"].get("_key", ""),
            "name": item["family"].get("name"),
            "wait_years": item.get("wait_years", 1),
            "benefit_score": item.get("benefit_score", 0.0),
            "benefit_reason": item.get("benefit_reason", ""),
        }
        for item in raw
    ]


@router.post("/successors", status_code=201)
def set_rotation_successor(body: RotationSuccessorSet, graph: ArangoGraphRepository = Depends(get_graph_repo)):
    graph.set_rotation_successor(
        body.from_family_key,
        body.to_family_key,
        body.wait_years,
        benefit_score=body.benefit_score,
        benefit_reason=body.benefit_reason,
    )
    return {"status": "created"}
