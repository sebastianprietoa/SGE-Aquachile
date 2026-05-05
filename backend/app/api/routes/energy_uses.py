from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.energy import EnergyArea, EnergySystem, EnergyUse
from app.schemas.common import EnergyUseCreate, EnergyUseRead, EnergyUseUpdate

router = APIRouter(tags=["energy-uses"])


@router.get("/systems/{system_id}/energy-uses", response_model=list[EnergyUseRead])
def list_energy_uses(system_id: int, db: Session = Depends(get_db)) -> list[EnergyUseRead]:
    if not db.get(EnergySystem, system_id):
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    items = db.query(EnergyUse).filter(EnergyUse.energy_system_id == system_id).order_by(EnergyUse.id.asc()).all()
    return [EnergyUseRead.model_validate(item) for item in items]


@router.post("/systems/{system_id}/energy-uses", response_model=EnergyUseRead)
def create_energy_use(system_id: int, payload: EnergyUseCreate, db: Session = Depends(get_db)) -> EnergyUseRead:
    if not db.get(EnergySystem, system_id):
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    if not db.get(EnergyArea, payload.area_id):
        raise HTTPException(status_code=404, detail="Área no encontrada")
    energy_use = EnergyUse(energy_system_id=system_id, **payload.model_dump())
    db.add(energy_use)
    db.commit()
    db.refresh(energy_use)
    return EnergyUseRead.model_validate(energy_use)


@router.put("/energy-uses/{energy_use_id}", response_model=EnergyUseRead)
def update_energy_use(energy_use_id: int, payload: EnergyUseUpdate, db: Session = Depends(get_db)) -> EnergyUseRead:
    energy_use = db.get(EnergyUse, energy_use_id)
    if not energy_use:
        raise HTTPException(status_code=404, detail="Uso energético no encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(energy_use, key, value)
    db.commit()
    db.refresh(energy_use)
    return EnergyUseRead.model_validate(energy_use)

