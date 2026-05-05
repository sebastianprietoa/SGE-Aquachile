from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_data_backend_service
from app.schemas.common import EnergyAreaCreate, EnergyAreaRead, EnergyAreaUpdate
from app.services.data_backend_service import DataBackendService

router = APIRouter(tags=["areas"])


@router.get("/systems/{system_id}/areas", response_model=list[EnergyAreaRead])
def list_areas(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[EnergyAreaRead]:
    return service.list_areas(system_id)


@router.post("/systems/{system_id}/areas", response_model=EnergyAreaRead)
def create_area(system_id: int, payload: EnergyAreaCreate, service: DataBackendService = Depends(get_data_backend_service)) -> EnergyAreaRead:
    return service.create_area(system_id, payload)


@router.put("/areas/{area_id}", response_model=EnergyAreaRead)
def update_area(area_id: int, payload: EnergyAreaUpdate, service: DataBackendService = Depends(get_data_backend_service)) -> EnergyAreaRead:
    return service.update_area(area_id, payload)

