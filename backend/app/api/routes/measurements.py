from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.measurement import AlertEvent, MeasurementAuditLog, MonthlyMeasurement
from app.schemas.common import AlertEventRead, ApiMessage, MeasurementAuditLogRead, MonthlyMeasurementCreate, MonthlyMeasurementRead, MonthlyMeasurementUpdate
from app.services.measurement_service import (
    add_measurement_audit_comment,
    create_monthly_measurement,
    get_measurement_by_id,
    list_measurement_alerts,
    list_measurements,
    transition_measurement_status,
    update_monthly_measurement,
)

router = APIRouter(tags=["measurements"])


@router.get("/systems/{system_id}/measurements", response_model=list[MonthlyMeasurementRead])
def list_system_measurements(
    system_id: int,
    year: int | None = None,
    month: int | None = None,
    area_id: int | None = None,
    energy_use_id: int | None = None,
    status_value: str | None = None,
    db: Session = Depends(get_db),
) -> list[MonthlyMeasurementRead]:
    items = list_measurements(db, system_id, year=year, month=month, area_id=area_id, energy_use_id=energy_use_id, status_value=status_value)
    return [MonthlyMeasurementRead.model_validate(item) for item in items]


@router.get("/measurements/{measurement_id}", response_model=MonthlyMeasurementRead)
def get_measurement(measurement_id: int, db: Session = Depends(get_db)) -> MonthlyMeasurementRead:
    measurement = get_measurement_by_id(db, measurement_id)
    if not measurement:
        raise HTTPException(status_code=404, detail="Medición no encontrada")
    return MonthlyMeasurementRead.model_validate(measurement)


@router.post("/systems/{system_id}/measurements", response_model=MonthlyMeasurementRead)
def create_measurement(system_id: int, payload: MonthlyMeasurementCreate, db: Session = Depends(get_db)) -> MonthlyMeasurementRead:
    measurement = create_monthly_measurement(db, energy_system_id=system_id, payload=payload, user=None)
    return MonthlyMeasurementRead.model_validate(measurement)


@router.put("/measurements/{measurement_id}", response_model=MonthlyMeasurementRead)
def update_measurement(measurement_id: int, payload: MonthlyMeasurementUpdate, db: Session = Depends(get_db)) -> MonthlyMeasurementRead:
    measurement = update_monthly_measurement(db, measurement_id, payload, user=None)
    return MonthlyMeasurementRead.model_validate(measurement)


@router.post("/measurements/{measurement_id}/submit", response_model=MonthlyMeasurementRead)
def submit_measurement(measurement_id: int, db: Session = Depends(get_db)) -> MonthlyMeasurementRead:
    measurement = transition_measurement_status(db, measurement_id, "submitted", user=None, comment="Envío a revisión")
    return MonthlyMeasurementRead.model_validate(measurement)


@router.post("/measurements/{measurement_id}/approve", response_model=MonthlyMeasurementRead)
def approve_measurement(measurement_id: int, db: Session = Depends(get_db)) -> MonthlyMeasurementRead:
    measurement = transition_measurement_status(db, measurement_id, "approved", user=None, comment="Aprobación de medición")
    return MonthlyMeasurementRead.model_validate(measurement)


@router.post("/measurements/{measurement_id}/reject", response_model=MonthlyMeasurementRead)
def reject_measurement(measurement_id: int, db: Session = Depends(get_db)) -> MonthlyMeasurementRead:
    measurement = transition_measurement_status(db, measurement_id, "rejected", user=None, comment="Rechazo de medición")
    return MonthlyMeasurementRead.model_validate(measurement)


@router.get("/measurements/{measurement_id}/audit-log", response_model=list[MeasurementAuditLogRead])
def measurement_audit_log(measurement_id: int, db: Session = Depends(get_db)) -> list[MeasurementAuditLogRead]:
    items = db.query(MeasurementAuditLog).filter(MeasurementAuditLog.monthly_measurement_id == measurement_id).order_by(MeasurementAuditLog.created_at.desc()).all()
    return [MeasurementAuditLogRead.model_validate(item) for item in items]


@router.get("/measurements/{measurement_id}/alerts", response_model=list[AlertEventRead])
def measurement_alerts(measurement_id: int, db: Session = Depends(get_db)) -> list[AlertEventRead]:
    items = list_measurement_alerts(db, measurement_id)
    return [AlertEventRead.model_validate(item) for item in items]

