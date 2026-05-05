from __future__ import annotations

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EnergySystem(Base):
    __tablename__ = "energy_systems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    areas = relationship("EnergyArea", back_populates="energy_system", cascade="all, delete-orphan")
    uses = relationship("EnergyUse", back_populates="energy_system", cascade="all, delete-orphan")
    baselines = relationship("BaselineModel", back_populates="energy_system", cascade="all, delete-orphan")
    ides = relationship("IdeDefinition", back_populates="energy_system", cascade="all, delete-orphan")
    alert_rules = relationship("AlertRule", back_populates="energy_system", cascade="all, delete-orphan")
    measurements = relationship("MonthlyMeasurement", back_populates="energy_system")
    energy_use_base_years = relationship("EnergyUseBaseYear", back_populates="energy_system", cascade="all, delete-orphan")
    significant_energy_uses = relationship("SignificantEnergyUse", back_populates="energy_system", cascade="all, delete-orphan")
    operational_controls = relationship("OperationalControl", back_populates="energy_system", cascade="all, delete-orphan")


class EnergyArea(Base):
    __tablename__ = "energy_areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    energy_system_id: Mapped[int] = mapped_column(ForeignKey("energy_systems.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    energy_system = relationship("EnergySystem", back_populates="areas")
    uses = relationship("EnergyUse", back_populates="area")
    baselines = relationship("BaselineModel", back_populates="area")


class EnergyUse(Base):
    __tablename__ = "energy_uses"
    __table_args__ = (
        UniqueConstraint("energy_system_id", "area_id", "name", name="uq_energy_use_context"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    energy_system_id: Mapped[int] = mapped_column(ForeignKey("energy_systems.id", ondelete="CASCADE"), index=True, nullable=False)
    area_id: Mapped[int] = mapped_column(ForeignKey("energy_areas.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    energy_source: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_significant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    energy_system = relationship("EnergySystem", back_populates="uses")
    area = relationship("EnergyArea", back_populates="uses")
    baselines = relationship("BaselineModel", back_populates="energy_use")
    ide_definitions = relationship("IdeDefinition", back_populates="energy_use")


class BaselineModel(Base):
    __tablename__ = "baseline_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    energy_system_id: Mapped[int] = mapped_column(ForeignKey("energy_systems.id", ondelete="CASCADE"), index=True, nullable=False)
    area_id: Mapped[int] = mapped_column(ForeignKey("energy_areas.id", ondelete="CASCADE"), index=True, nullable=False)
    energy_use_id: Mapped[int] = mapped_column(ForeignKey("energy_uses.id", ondelete="CASCADE"), index=True, nullable=False)
    significant_energy_use_id: Mapped[int | None] = mapped_column(ForeignKey("significant_energy_uses.id", ondelete="SET NULL"), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dependent_variable: Mapped[str] = mapped_column(String(120), nullable=False)
    dependent_variable_unit: Mapped[str] = mapped_column(String(50), nullable=False)
    formula_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_type: Mapped[str] = mapped_column(String(80), default="linear", nullable=False)
    coefficients: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    intercept: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    r_squared: Mapped[float | None] = mapped_column(Float, nullable=True)
    adjusted_r_squared: Mapped[float | None] = mapped_column(Float, nullable=True)
    reference_period_start: Mapped[str | None] = mapped_column(Date, nullable=True)
    reference_period_end: Mapped[str | None] = mapped_column(Date, nullable=True)
    static_factors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    routine_adjustments: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    non_routine_adjustments: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    valid_from: Mapped[str | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[str | None] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    energy_system = relationship("EnergySystem", back_populates="baselines")
    area = relationship("EnergyArea", back_populates="baselines")
    energy_use = relationship("EnergyUse", back_populates="baselines")
    significant_energy_use = relationship("SignificantEnergyUse", back_populates="baselines")
    variables = relationship("BaselineVariable", back_populates="baseline_model", cascade="all, delete-orphan")
    ide_definitions = relationship("IdeDefinition", back_populates="baseline_model")
    measurements = relationship("MonthlyMeasurement", back_populates="baseline_model")
    alert_rules = relationship("AlertRule", back_populates="baseline_model")


class BaselineVariable(Base):
    __tablename__ = "baseline_variables"
    __table_args__ = (
        UniqueConstraint("baseline_model_id", "variable_code", name="uq_baseline_variable_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    baseline_model_id: Mapped[int] = mapped_column(ForeignKey("baseline_models.id", ondelete="CASCADE"), index=True, nullable=False)
    variable_name: Mapped[str] = mapped_column(String(255), nullable=False)
    variable_code: Mapped[str] = mapped_column(String(120), nullable=False)
    variable_type: Mapped[str] = mapped_column(String(80), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    min_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    measurement_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    collection_method: Mapped[str | None] = mapped_column(Text, nullable=True)
    storage_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    responsible_area: Mapped[str | None] = mapped_column(String(255), nullable=True)
    responsible_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(80), nullable=True)
    missing_data_procedure: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    baseline_model = relationship("BaselineModel", back_populates="variables")
    measurement_variables = relationship("MonthlyMeasurementVariable", back_populates="baseline_variable")


class IdeDefinition(Base):
    __tablename__ = "ide_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    energy_system_id: Mapped[int] = mapped_column(ForeignKey("energy_systems.id", ondelete="CASCADE"), index=True, nullable=False)
    significant_energy_use_id: Mapped[int | None] = mapped_column(ForeignKey("significant_energy_uses.id", ondelete="SET NULL"), index=True, nullable=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("energy_areas.id", ondelete="CASCADE"), index=True, nullable=False)
    energy_use_id: Mapped[int] = mapped_column(ForeignKey("energy_uses.id", ondelete="CASCADE"), index=True, nullable=False)
    baseline_model_id: Mapped[int] = mapped_column(ForeignKey("baseline_models.id", ondelete="CASCADE"), index=True, nullable=False)
    ide_code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    ide_name: Mapped[str] = mapped_column(String(255), nullable=False)
    formula_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    numerator: Mapped[str | None] = mapped_column(String(120), nullable=True)
    denominator: Mapped[str | None] = mapped_column(String(120), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(80), nullable=True)
    expected_range_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_range_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    warning_threshold_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    critical_threshold_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    protocol_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    energy_system = relationship("EnergySystem", back_populates="ides")
    significant_energy_use = relationship("SignificantEnergyUse", back_populates="ides")
    area = relationship("EnergyArea")
    energy_use = relationship("EnergyUse", back_populates="ide_definitions")
    baseline_model = relationship("BaselineModel", back_populates="ide_definitions")
    measurements = relationship("MonthlyMeasurement", back_populates="ide_definition")
    alert_rules = relationship("AlertRule", back_populates="ide")


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    energy_system_id: Mapped[int] = mapped_column(ForeignKey("energy_systems.id", ondelete="CASCADE"), index=True, nullable=False)
    baseline_model_id: Mapped[int] = mapped_column(ForeignKey("baseline_models.id", ondelete="CASCADE"), index=True, nullable=False)
    ide_id: Mapped[int | None] = mapped_column(ForeignKey("ide_definitions.id", ondelete="SET NULL"), index=True, nullable=True)
    metric: Mapped[str] = mapped_column(String(80), nullable=False)
    operator: Mapped[str] = mapped_column(String(8), nullable=False)
    threshold_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    message_template: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    energy_system = relationship("EnergySystem", back_populates="alert_rules")
    baseline_model = relationship("BaselineModel", back_populates="alert_rules")
    ide = relationship("IdeDefinition", back_populates="alert_rules")
    alert_events = relationship("AlertEvent", back_populates="alert_rule")


class EnergyUseBaseYear(Base):
    __tablename__ = "energy_use_base_years"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    energy_system_id: Mapped[int] = mapped_column(ForeignKey("energy_systems.id", ondelete="CASCADE"), index=True, nullable=False)
    base_year: Mapped[int] = mapped_column(Integer, nullable=False)
    area_id: Mapped[int | None] = mapped_column(ForeignKey("energy_areas.id", ondelete="SET NULL"), index=True, nullable=True)
    area_name: Mapped[str] = mapped_column(String(255), nullable=False)
    installation_name: Mapped[str] = mapped_column(String(255), nullable=False)
    energy_source: Mapped[str] = mapped_column(String(120), nullable=False)
    use_category: Mapped[str] = mapped_column(String(120), nullable=False)
    consumption_value: Mapped[float] = mapped_column(Float, nullable=False)
    consumption_unit: Mapped[str] = mapped_column(String(50), nullable=False)
    consumption_tcal: Mapped[float | None] = mapped_column(Float, nullable=True)
    percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    accumulated_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    is_candidate_use: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_significant_use: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    energy_system = relationship("EnergySystem", back_populates="energy_use_base_years")
    area = relationship("EnergyArea")
    significant_energy_uses = relationship("SignificantEnergyUse", back_populates="energy_use_base_year")


class SignificantEnergyUse(Base):
    __tablename__ = "significant_energy_uses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    energy_system_id: Mapped[int] = mapped_column(ForeignKey("energy_systems.id", ondelete="CASCADE"), index=True, nullable=False)
    energy_use_base_year_id: Mapped[int] = mapped_column(ForeignKey("energy_use_base_years.id", ondelete="CASCADE"), index=True, nullable=False)
    area_id: Mapped[int | None] = mapped_column(ForeignKey("energy_areas.id", ondelete="SET NULL"), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    energy_source: Mapped[str] = mapped_column(String(120), nullable=False)
    consumption_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    consumption_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    selection_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_energy_performance: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_energy_performance_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    relevant_personnel: Mapped[str | None] = mapped_column(Text, nullable=True)
    operational_control_required: Mapped[str | None] = mapped_column(Text, nullable=True)
    improvement_opportunities: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    energy_system = relationship("EnergySystem", back_populates="significant_energy_uses")
    energy_use_base_year = relationship("EnergyUseBaseYear", back_populates="significant_energy_uses")
    area = relationship("EnergyArea")
    baselines = relationship("BaselineModel", back_populates="significant_energy_use")
    ides = relationship("IdeDefinition", back_populates="significant_energy_use")
    operational_controls = relationship("OperationalControl", back_populates="significant_energy_use", cascade="all, delete-orphan")


class OperationalControl(Base):
    __tablename__ = "operational_controls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    energy_system_id: Mapped[int] = mapped_column(ForeignKey("energy_systems.id", ondelete="CASCADE"), index=True, nullable=False)
    significant_energy_use_id: Mapped[int] = mapped_column(ForeignKey("significant_energy_uses.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    technical_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    administrative_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    maintenance_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsible_area: Mapped[str | None] = mapped_column(String(255), nullable=True)
    responsible_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    record_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    record_frequency: Mapped[str | None] = mapped_column(String(80), nullable=True)
    training_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_training_date: Mapped[str | None] = mapped_column(Date, nullable=True)
    effectiveness_evaluation_method: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    energy_system = relationship("EnergySystem", back_populates="operational_controls")
    significant_energy_use = relationship("SignificantEnergyUse", back_populates="operational_controls")
