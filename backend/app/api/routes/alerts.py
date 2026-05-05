from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.energy import AlertRule, EnergySystem
from app.models.measurement import AlertEvent
from app.schemas.common import AlertEventRead, AlertRuleCreate, AlertRuleRead, AlertRuleUpdate

router = APIRouter(tags=["alerts"])


@router.get("/systems/{system_id}/alerts", response_model=list[AlertEventRead])
def list_system_alerts(system_id: int, db: Session = Depends(get_db)) -> list[AlertEventRead]:
    if not db.get(EnergySystem, system_id):
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    items = db.query(AlertEvent).filter(AlertEvent.energy_system_id == system_id).order_by(AlertEvent.created_at.desc()).all()
    return [AlertEventRead.model_validate(item) for item in items]


@router.post("/alert-rules", response_model=AlertRuleRead)
def create_alert_rule(payload: AlertRuleCreate, db: Session = Depends(get_db)) -> AlertRuleRead:
    if not db.get(EnergySystem, payload.energy_system_id):
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    rule = AlertRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return AlertRuleRead.model_validate(rule)


@router.put("/alert-rules/{alert_rule_id}", response_model=AlertRuleRead)
def update_alert_rule(alert_rule_id: int, payload: AlertRuleUpdate, db: Session = Depends(get_db)) -> AlertRuleRead:
    rule = db.get(AlertRule, alert_rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return AlertRuleRead.model_validate(rule)

