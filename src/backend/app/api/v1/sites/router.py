from fastapi import APIRouter, Depends, Query

from app.api.v1.sites.schemas import SiteCreate, SiteResponse
from app.common.dependencies import get_site_service
from app.domain.models.site import Site
from app.domain.services.site_service import SiteService

router = APIRouter(prefix="/sites", tags=["sites"])

@router.get("", response_model=list[SiteResponse])
def list_sites(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: SiteService = Depends(get_site_service),
):
    items, total = service.list_sites(offset, limit)
    return [SiteResponse(key=s.key or "", **s.model_dump(exclude={"key"})) for s in items]

@router.get("/{key}", response_model=SiteResponse)
def get_site(key: str, service: SiteService = Depends(get_site_service)):
    s = service.get_site(key)
    return SiteResponse(key=s.key or "", **s.model_dump(exclude={"key"}))

@router.post("", response_model=SiteResponse, status_code=201)
def create_site(body: SiteCreate, service: SiteService = Depends(get_site_service)):
    site = Site(**body.model_dump())
    created = service.create_site(site)
    return SiteResponse(key=created.key or "", **created.model_dump(exclude={"key"}))

@router.put("/{key}", response_model=SiteResponse)
def update_site(key: str, body: SiteCreate, service: SiteService = Depends(get_site_service)):
    site = Site(**body.model_dump())
    updated = service.update_site(key, site)
    return SiteResponse(key=updated.key or "", **updated.model_dump(exclude={"key"}))

@router.delete("/{key}", status_code=204)
def delete_site(key: str, service: SiteService = Depends(get_site_service)):
    service.delete_site(key)
