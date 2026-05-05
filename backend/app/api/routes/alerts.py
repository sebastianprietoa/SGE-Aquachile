from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_data_backend_service
from app.schemas.common import AlertEventRead, AlertRuleCreate, AlertRuleRead, AlertRuleUpdate
from app.services.data_backend_service import DataBackendService

router = APIRouter(tags=["alerts"])


@router.get("/systems/{system_id}/alerts", response_model=list[AlertEventRead])
def list_system_alerts(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[AlertEventRead]:
    return service.list_system_alerts(system_id)


@router.post("/alert-rules", response_model=AlertRuleRead)
def create_alert_rule(payload: AlertRuleCreate, service: DataBackendService = Depends(get_data_backend_service)) -> AlertRuleRead:
    return service.create_alert_rule(payload)


@router.put("/alert-rules/{alert_rule_id}", response_model=AlertRuleRead)
def update_alert_rule(alert_rule_id: int, payload: AlertRuleUpdate, service: DataBackendService = Depends(get_data_backend_service)) -> AlertRuleRead:
    return service.update_alert_rule(alert_rule_id, payload)

