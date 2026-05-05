from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.energy import BaselineModel, BaselineVariable, EnergySystem
from app.schemas.common import BaselineModelCreate, BaselineModelRead, BaselineModelUpdate, BaselineVariableCreate, BaselineVariableRead, BaselineVariableUpdate

router = APIRouter(tags=["baselines"])


@router.get("/systems/{system_id}/baselines", response_model=list[BaselineModelRead])
def list_baselines(system_id: int, db: Session = Depends(get_db)) -> list[BaselineModelRead]:
    if not db.get(EnergySystem, system_id):
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    items = db.query(BaselineModel).filter(BaselineModel.energy_system_id == system_id).order_by(BaselineModel.id.asc()).all()
    return [BaselineModelRead.model_validate(item) for item in items]


@router.get("/baselines/{baseline_id}", response_model=BaselineModelRead)
def get_baseline(baseline_id: int, db: Session = Depends(get_db)) -> BaselineModelRead:
    baseline = db.get(BaselineModel, baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Línea base no encontrada")
    return BaselineModelRead.model_validate(baseline)


@router.post("/systems/{system_id}/baselines", response_model=BaselineModelRead)
def create_baseline(system_id: int, payload: BaselineModelCreate, db: Session = Depends(get_db)) -> BaselineModelRead:
    if not db.get(EnergySystem, system_id):
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    baseline = BaselineModel(energy_system_id=system_id, **payload.model_dump())
    db.add(baseline)
    db.commit()
    db.refresh(baseline)
    return BaselineModelRead.model_validate(baseline)


@router.put("/baselines/{baseline_id}", response_model=BaselineModelRead)
def update_baseline(baseline_id: int, payload: BaselineModelUpdate, db: Session = Depends(get_db)) -> BaselineModelRead:
    baseline = db.get(BaselineModel, baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Línea base no encontrada")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(baseline, key, value)
    db.commit()
    db.refresh(baseline)
    return BaselineModelRead.model_validate(baseline)


@router.get("/baselines/{baseline_id}/variables", response_model=list[BaselineVariableRead])
def list_baseline_variables(baseline_id: int, db: Session = Depends(get_db)) -> list[BaselineVariableRead]:
    items = (
        db.query(BaselineVariable)
        .filter(BaselineVariable.baseline_model_id == baseline_id)
        .order_by(BaselineVariable.display_order.asc(), BaselineVariable.id.asc())
        .all()
    )
    return [BaselineVariableRead.model_validate(item) for item in items]


@router.post("/baselines/{baseline_id}/variables", response_model=BaselineVariableRead)
def create_baseline_variable(baseline_id: int, payload: BaselineVariableCreate, db: Session = Depends(get_db)) -> BaselineVariableRead:
    baseline = db.get(BaselineModel, baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Línea base no encontrada")
    variable = BaselineVariable(baseline_model_id=baseline_id, **payload.model_dump())
    db.add(variable)
    db.commit()
    db.refresh(variable)
    return BaselineVariableRead.model_validate(variable)


@router.put("/baseline-variables/{variable_id}", response_model=BaselineVariableRead)
def update_baseline_variable(variable_id: int, payload: BaselineVariableUpdate, db: Session = Depends(get_db)) -> BaselineVariableRead:
    variable = db.get(BaselineVariable, variable_id)
    if not variable:
        raise HTTPException(status_code=404, detail="Variable de línea base no encontrada")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(variable, key, value)
    db.commit()
    db.refresh(variable)
    return BaselineVariableRead.model_validate(variable)

