from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_data_backend_service
from app.schemas.common import BaselineModelCreate, BaselineModelRead, BaselineModelUpdate, BaselineVariableCreate, BaselineVariableRead, BaselineVariableUpdate
from app.services.data_backend_service import DataBackendService

router = APIRouter(tags=["baselines"])


@router.get("/systems/{system_id}/baselines", response_model=list[BaselineModelRead])
def list_baselines(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[BaselineModelRead]:
    return service.list_baselines(system_id)


@router.get("/baselines/{baseline_id}", response_model=BaselineModelRead)
def get_baseline(baseline_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> BaselineModelRead:
    baseline = service.get_baseline(baseline_id)
    if not baseline:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Línea base no encontrada")
    return baseline


@router.post("/systems/{system_id}/baselines", response_model=BaselineModelRead)
def create_baseline(system_id: int, payload: BaselineModelCreate, service: DataBackendService = Depends(get_data_backend_service)) -> BaselineModelRead:
    return service.create_baseline_model(system_id, payload)


@router.put("/baselines/{baseline_id}", response_model=BaselineModelRead)
def update_baseline(baseline_id: int, payload: BaselineModelUpdate, service: DataBackendService = Depends(get_data_backend_service)) -> BaselineModelRead:
    return service.update_baseline_model(baseline_id, payload)


@router.get("/baselines/{baseline_id}/variables", response_model=list[BaselineVariableRead])
def list_baseline_variables(baseline_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[BaselineVariableRead]:
    return service.list_baseline_variables(baseline_id)


@router.post("/baselines/{baseline_id}/variables", response_model=BaselineVariableRead)
def create_baseline_variable(baseline_id: int, payload: BaselineVariableCreate, service: DataBackendService = Depends(get_data_backend_service)) -> BaselineVariableRead:
    return service.create_baseline_variable(baseline_id, payload)


@router.put("/baseline-variables/{variable_id}", response_model=BaselineVariableRead)
def update_baseline_variable(variable_id: int, payload: BaselineVariableUpdate, service: DataBackendService = Depends(get_data_backend_service)) -> BaselineVariableRead:
    return service.update_baseline_variable(variable_id, payload)

