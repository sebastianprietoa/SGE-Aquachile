from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.energy import AlertRule, BaselineModel, BaselineVariable, EnergyArea, EnergySystem, EnergyUse, IdeDefinition


class SystemRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_systems(self) -> list[EnergySystem]:
        return self.db.query(EnergySystem).order_by(EnergySystem.id.asc()).all()

    def get_system(self, system_id: int) -> EnergySystem | None:
        return self.db.get(EnergySystem, system_id)

    def list_areas(self, system_id: int) -> list[EnergyArea]:
        return self.db.query(EnergyArea).filter(EnergyArea.energy_system_id == system_id).order_by(EnergyArea.id.asc()).all()

    def list_uses(self, system_id: int) -> list[EnergyUse]:
        return self.db.query(EnergyUse).filter(EnergyUse.energy_system_id == system_id).order_by(EnergyUse.id.asc()).all()

    def list_baselines(self, system_id: int) -> list[BaselineModel]:
        return self.db.query(BaselineModel).filter(BaselineModel.energy_system_id == system_id).order_by(BaselineModel.id.asc()).all()

    def list_ide_definitions(self, system_id: int) -> list[IdeDefinition]:
        return self.db.query(IdeDefinition).filter(IdeDefinition.energy_system_id == system_id).order_by(IdeDefinition.id.asc()).all()

    def list_alert_rules(self, system_id: int) -> list[AlertRule]:
        return self.db.query(AlertRule).filter(AlertRule.energy_system_id == system_id).order_by(AlertRule.id.asc()).all()

