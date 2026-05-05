from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.energy import EnergyArea, EnergySystem
from app.schemas.common import EnergyAreaCreate, EnergyAreaRead, EnergyAreaUpdate

router = APIRouter(tags=["areas"])


@router.get("/systems/{system_id}/areas", response_model=list[EnergyAreaRead])
def list_areas(system_id: int, db: Session = Depends(get_db)) -> list[EnergyAreaRead]:
    if not db.get(EnergySystem, system_id):
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    items = db.query(EnergyArea).filter(EnergyArea.energy_system_id == system_id).order_by(EnergyArea.id.asc()).all()
    return [EnergyAreaRead.model_validate(item) for item in items]


@router.post("/systems/{system_id}/areas", response_model=EnergyAreaRead)
def create_area(system_id: int, payload: EnergyAreaCreate, db: Session = Depends(get_db)) -> EnergyAreaRead:
    if not db.get(EnergySystem, system_id):
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    area = EnergyArea(energy_system_id=system_id, **payload.model_dump())
    db.add(area)
    db.commit()
    db.refresh(area)
    return EnergyAreaRead.model_validate(area)


@router.put("/areas/{area_id}", response_model=EnergyAreaRead)
def update_area(area_id: int, payload: EnergyAreaUpdate, db: Session = Depends(get_db)) -> EnergyAreaRead:
    area = db.get(EnergyArea, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(area, key, value)
    db.commit()
    db.refresh(area)
    return EnergyAreaRead.model_validate(area)

