from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.energy import EnergySystem, IdeDefinition
from app.schemas.common import IdeDefinitionCreate, IdeDefinitionRead, IdeDefinitionUpdate

router = APIRouter(tags=["ides"])


@router.get("/systems/{system_id}/ides", response_model=list[IdeDefinitionRead])
def list_ides(system_id: int, db: Session = Depends(get_db)) -> list[IdeDefinitionRead]:
    if not db.get(EnergySystem, system_id):
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    items = db.query(IdeDefinition).filter(IdeDefinition.energy_system_id == system_id).order_by(IdeDefinition.id.asc()).all()
    return [IdeDefinitionRead.model_validate(item) for item in items]


@router.post("/systems/{system_id}/ides", response_model=IdeDefinitionRead)
def create_ide(system_id: int, payload: IdeDefinitionCreate, db: Session = Depends(get_db)) -> IdeDefinitionRead:
    if not db.get(EnergySystem, system_id):
        raise HTTPException(status_code=404, detail="Sistema no encontrado")
    ide = IdeDefinition(energy_system_id=system_id, **payload.model_dump())
    db.add(ide)
    db.commit()
    db.refresh(ide)
    return IdeDefinitionRead.model_validate(ide)


@router.put("/ides/{ide_id}", response_model=IdeDefinitionRead)
def update_ide(ide_id: int, payload: IdeDefinitionUpdate, db: Session = Depends(get_db)) -> IdeDefinitionRead:
    ide = db.get(IdeDefinition, ide_id)
    if not ide:
        raise HTTPException(status_code=404, detail="IDE no encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(ide, key, value)
    db.commit()
    db.refresh(ide)
    return IdeDefinitionRead.model_validate(ide)

