from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="admin", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class MonthlyMeasurement(Base):
    __tablename__ = "monthly_measurements"
    __table_args__ = (
        UniqueConstraint(
            "energy_system_id",
            "area_id",
            "energy_use_id",
            "baseline_model_id",
            "year",
            "month",
            name="uq_monthly_measurement_context",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    energy_system_id: Mapped[int] = mapped_column(ForeignKey("energy_systems.id", ondelete="CASCADE"), index=True, nullable=False)
    significant_energy_use_id: Mapped[int | None] = mapped_column(ForeignKey("significant_energy_uses.id", ondelete="SET NULL"), index=True, nullable=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("energy_areas.id", ondelete="CASCADE"), index=True, nullable=False)
    energy_use_id: Mapped[int] = mapped_column(ForeignKey("energy_uses.id", ondelete="CASCADE"), index=True, nullable=False)
    baseline_model_id: Mapped[int] = mapped_column(ForeignKey("baseline_models.id", ondelete="CASCADE"), index=True, nullable=False)
    ide_id: Mapped[int] = mapped_column(ForeignKey("ide_definitions.id", ondelete="RESTRICT"), index=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    real_consumption: Mapped[float] = mapped_column(Float, nullable=False)
    consumption_unit: Mapped[str] = mapped_column(String(50), nullable=False)
    expected_consumption: Mapped[float | None] = mapped_column(Float, nullable=True)
    ide_real: Mapped[float | None] = mapped_column(Float, nullable=True)
    ide_expected: Mapped[float | None] = mapped_column(Float, nullable=True)
    difference: Mapped[float | None] = mapped_column(Float, nullable=True)
    percentage_difference: Mapped[float | None] = mapped_column(Float, nullable=True)
    compliance_status: Mapped[str] = mapped_column(String(30), default="incomplete", nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    energy_system = relationship("EnergySystem", back_populates="measurements")
    area = relationship("EnergyArea")
    energy_use = relationship("EnergyUse")
    significant_energy_use = relationship("SignificantEnergyUse")
    baseline_model = relationship("BaselineModel", back_populates="measurements")
    ide_definition = relationship("IdeDefinition", back_populates="measurements")
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    variables = relationship("MonthlyMeasurementVariable", back_populates="measurement", cascade="all, delete-orphan")
    audit_logs = relationship("MeasurementAuditLog", back_populates="measurement", cascade="all, delete-orphan")
    alerts = relationship("AlertEvent", back_populates="measurement", cascade="all, delete-orphan")


class MonthlyMeasurementVariable(Base):
    __tablename__ = "monthly_measurement_variables"
    __table_args__ = (
        UniqueConstraint("monthly_measurement_id", "baseline_variable_id", name="uq_measurement_variable"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    monthly_measurement_id: Mapped[int] = mapped_column(ForeignKey("monthly_measurements.id", ondelete="CASCADE"), index=True, nullable=False)
    baseline_variable_id: Mapped[int] = mapped_column(ForeignKey("baseline_variables.id", ondelete="RESTRICT"), index=True, nullable=False)
    variable_name: Mapped[str] = mapped_column(String(255), nullable=False)
    variable_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    measurement = relationship("MonthlyMeasurement", back_populates="variables")
    baseline_variable = relationship("BaselineVariable", back_populates="measurement_variables")


class MeasurementAuditLog(Base):
    __tablename__ = "measurement_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    monthly_measurement_id: Mapped[int] = mapped_column(ForeignKey("monthly_measurements.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    measurement = relationship("MonthlyMeasurement", back_populates="audit_logs")
    user = relationship("User")


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    energy_system_id: Mapped[int] = mapped_column(ForeignKey("energy_systems.id", ondelete="CASCADE"), index=True, nullable=False)
    monthly_measurement_id: Mapped[int] = mapped_column(ForeignKey("monthly_measurements.id", ondelete="CASCADE"), index=True, nullable=False)
    alert_rule_id: Mapped[int | None] = mapped_column(ForeignKey("alert_rules.id", ondelete="SET NULL"), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    value_detected: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    energy_system = relationship("EnergySystem")
    measurement = relationship("MonthlyMeasurement", back_populates="alerts")
    alert_rule = relationship("AlertRule", back_populates="alert_events")
