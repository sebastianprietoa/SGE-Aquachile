from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.system_repository import SystemRepository
from app.schemas.common import EnergySystemRead, DashboardResponse, PerformanceSummaryResponse, TrendPoint
from app.services.dashboard_service import get_dashboard_response, get_monthly_trends, get_performance_summary

router = APIRouter(prefix="/systems", tags=["systems"])


@router.get("", response_model=list[EnergySystemRead])
def list_systems(db: Session = Depends(get_db)) -> list[EnergySystemRead]:
    repo = SystemRepository(db)
    return [EnergySystemRead.model_validate(item) for item in repo.list_systems()]


@router.get("/{system_id}", response_model=EnergySystemRead)
def get_system(system_id: int, db: Session = Depends(get_db)) -> EnergySystemRead:
    repo = SystemRepository(db)
    system = repo.get_system(system_id)
    if not system:
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    return EnergySystemRead.model_validate(system)


@router.get("/{system_id}/dashboard", response_model=DashboardResponse)
def dashboard(system_id: int, db: Session = Depends(get_db)) -> DashboardResponse:
    return get_dashboard_response(db, system_id)


@router.get("/{system_id}/performance-summary", response_model=PerformanceSummaryResponse)
def performance_summary(system_id: int, db: Session = Depends(get_db)) -> PerformanceSummaryResponse:
    return get_performance_summary(db, system_id)


@router.get("/{system_id}/monthly-trends", response_model=list[TrendPoint])
def monthly_trends(system_id: int, db: Session = Depends(get_db)) -> list[TrendPoint]:
    return get_monthly_trends(db, system_id)

