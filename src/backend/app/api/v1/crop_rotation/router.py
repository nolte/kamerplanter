from fastapi import APIRouter, Depends

from app.api.v1.crop_rotation.schemas import RotationSuccessorSet
from app.common.dependencies import get_graph_repo
from app.data_access.arango.collections import BOTANICAL_FAMILIES
from app.data_access.arango.graph_repository import ArangoGraphRepository

router = APIRouter(prefix="/crop-rotation", tags=["crop-rotation"])

@router.get("/families/{family_key}/successors")
def get_rotation_successors(family_key: str, graph: ArangoGraphRepository = Depends(get_graph_repo)):
    return graph.get_rotation_successors(f"{BOTANICAL_FAMILIES}/{family_key}")

@router.post("/successors", status_code=201)
def set_rotation_successor(body: RotationSuccessorSet, graph: ArangoGraphRepository = Depends(get_graph_repo)):
    graph.set_rotation_successor(
        f"{BOTANICAL_FAMILIES}/{body.from_family_key}",
        f"{BOTANICAL_FAMILIES}/{body.to_family_key}",
        body.wait_years,
    )
    return {"status": "created"}
