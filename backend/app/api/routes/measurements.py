from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_data_backend_service
from app.schemas.energy_v2 import AlertEventReadV2, MonthlyMeasurementCreateV2, MonthlyMeasurementReadV2, MonthlyMeasurementUpdateV2
from app.services.data_backend_service import DataBackendService

router = APIRouter(tags=["measurements"])


@router.get("/systems/{system_id}/measurements", response_model=list[MonthlyMeasurementReadV2])
def list_system_measurements(
    system_id: int,
    baseline_id: int | None = None,
    use_id: int | None = None,
    year: int | None = None,
    month: int | None = None,
    service: DataBackendService = Depends(get_data_backend_service),
) -> list[MonthlyMeasurementReadV2]:
    return service.list_measurements(system_id, baseline_id=baseline_id, use_id=use_id, year=year, month=month)


@router.get("/measurements/{measurement_id}", response_model=MonthlyMeasurementReadV2)
def get_measurement_route(measurement_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> MonthlyMeasurementReadV2:
    measurement = service.get_measurement(measurement_id)
    if not measurement:
        raise HTTPException(status_code=404, detail="Medición no encontrada")
    return measurement


@router.post("/systems/{system_id}/measurements", response_model=MonthlyMeasurementReadV2)
def create_measurement(system_id: int, payload: MonthlyMeasurementCreateV2, service: DataBackendService = Depends(get_data_backend_service)) -> MonthlyMeasurementReadV2:
    return service.create_monthly_measurement(system_id=system_id, payload=payload, user=None)


@router.put("/measurements/{measurement_id}", response_model=MonthlyMeasurementReadV2)
def update_measurement(measurement_id: int, payload: MonthlyMeasurementUpdateV2, service: DataBackendService = Depends(get_data_backend_service)) -> MonthlyMeasurementReadV2:
    return service.update_monthly_measurement(measurement_id, payload, user=None)


@router.post("/measurements/{measurement_id}/submit", response_model=MonthlyMeasurementReadV2)
def submit_measurement(measurement_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> MonthlyMeasurementReadV2:
    return service.transition_measurement_status(measurement_id, "submitted", user=None, comment="Envío a revisión")


@router.post("/measurements/{measurement_id}/approve", response_model=MonthlyMeasurementReadV2)
def approve_measurement(measurement_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> MonthlyMeasurementReadV2:
    return service.transition_measurement_status(measurement_id, "approved", user=None, comment="Aprobación de medición")


@router.post("/measurements/{measurement_id}/reject", response_model=MonthlyMeasurementReadV2)
def reject_measurement(measurement_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> MonthlyMeasurementReadV2:
    return service.transition_measurement_status(measurement_id, "rejected", user=None, comment="Rechazo de medición")


@router.get("/measurements/{measurement_id}/audit-log", response_model=list[dict])
def measurement_audit_log(measurement_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[dict]:
    return service.list_measurement_audit_log(measurement_id)


@router.get("/measurements/{measurement_id}/alerts", response_model=list[AlertEventReadV2])
def measurement_alerts(measurement_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[AlertEventReadV2]:
    return service.list_measurement_alerts(measurement_id)

