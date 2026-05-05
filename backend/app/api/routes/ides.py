from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_data_backend_service
from app.schemas.common import IdeDefinitionCreate, IdeDefinitionRead, IdeDefinitionUpdate
from app.services.data_backend_service import DataBackendService

router = APIRouter(tags=["ides"])


@router.get("/systems/{system_id}/ides", response_model=list[IdeDefinitionRead])
def list_ides(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[IdeDefinitionRead]:
    return service.list_ides(system_id)


@router.post("/systems/{system_id}/ides", response_model=IdeDefinitionRead)
def create_ide(system_id: int, payload: IdeDefinitionCreate, service: DataBackendService = Depends(get_data_backend_service)) -> IdeDefinitionRead:
    return service.create_ide(system_id, payload)


@router.put("/ides/{ide_id}", response_model=IdeDefinitionRead)
def update_ide(ide_id: int, payload: IdeDefinitionUpdate, service: DataBackendService = Depends(get_data_backend_service)) -> IdeDefinitionRead:
    return service.update_ide(ide_id, payload)

