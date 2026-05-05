from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_data_backend_service
from app.services.data_backend_service import DataBackendService
from app.schemas.common import EnergySystemRead, DashboardResponse, PerformanceSummaryResponse, TrendPoint

router = APIRouter(prefix="/systems", tags=["systems"])


@router.get("", response_model=list[EnergySystemRead])
def list_systems(service: DataBackendService = Depends(get_data_backend_service)) -> list[EnergySystemRead]:
    return service.list_systems()


@router.get("/{system_id}", response_model=EnergySystemRead)
def get_system(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> EnergySystemRead:
    system = service.get_system(system_id)
    if not system:
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    return system


@router.get("/{system_id}/dashboard", response_model=DashboardResponse)
def dashboard(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> DashboardResponse:
    return service.get_dashboard_response(system_id)


@router.get("/{system_id}/performance-summary", response_model=PerformanceSummaryResponse)
def performance_summary(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> PerformanceSummaryResponse:
    return service.get_performance_summary(system_id)


@router.get("/{system_id}/monthly-trends", response_model=list[TrendPoint])
def monthly_trends(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[TrendPoint]:
    return service.get_monthly_trends(system_id)
