from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_data_backend_service
from app.schemas.common import EnergyUseCreate, EnergyUseRead, EnergyUseUpdate
from app.services.data_backend_service import DataBackendService

router = APIRouter(tags=["energy-uses"])


@router.get("/systems/{system_id}/energy-uses", response_model=list[EnergyUseRead])
def list_energy_uses(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[EnergyUseRead]:
    return service.list_energy_uses(system_id)


@router.post("/systems/{system_id}/energy-uses", response_model=EnergyUseRead)
def create_energy_use(system_id: int, payload: EnergyUseCreate, service: DataBackendService = Depends(get_data_backend_service)) -> EnergyUseRead:
    return service.create_energy_use(system_id, payload)


@router.put("/energy-uses/{energy_use_id}", response_model=EnergyUseRead)
def update_energy_use(energy_use_id: int, payload: EnergyUseUpdate, service: DataBackendService = Depends(get_data_backend_service)) -> EnergyUseRead:
    return service.update_energy_use(energy_use_id, payload)

