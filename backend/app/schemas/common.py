from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserRead(ORMBase):
    id: int
    username: str
    full_name: str
    email: str
    role: str
    active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserRead


class LoginRequest(BaseModel):
    username: str
    password: str


class EnergySystemBase(ORMBase):
    code: str
    name: str
    company: str
    description: str | None = None
    active: bool = True


class EnergySystemRead(EnergySystemBase):
    id: int


class EnergyAreaBase(ORMBase):
    name: str
    type: str
    description: str | None = None
    active: bool = True


class EnergyAreaCreate(EnergyAreaBase):
    pass


class EnergyAreaUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    active: bool | None = None


class EnergyAreaRead(EnergyAreaBase):
    id: int
    energy_system_id: int


class EnergyUseBase(ORMBase):
    name: str
    energy_source: str
    description: str | None = None
    is_significant: bool = False
    active: bool = True


class EnergyUseCreate(EnergyUseBase):
    area_id: int


class EnergyUseUpdate(BaseModel):
    area_id: int | None = None
    name: str | None = None
    energy_source: str | None = None
    description: str | None = None
    is_significant: bool | None = None
    active: bool | None = None


class EnergyUseRead(EnergyUseBase):
    id: int
    energy_system_id: int
    area_id: int


class BaselineVariableBase(ORMBase):
    variable_name: str
    variable_code: str
    variable_type: str
    unit: str | None = None
    required: bool = True
    min_value: float | None = None
    max_value: float | None = None
    description: str | None = None
    display_order: int = 0
    active: bool = True


class BaselineVariableCreate(BaselineVariableBase):
    pass


class BaselineVariableUpdate(BaseModel):
    variable_name: str | None = None
    variable_code: str | None = None
    variable_type: str | None = None
    unit: str | None = None
    required: bool | None = None
    min_value: float | None = None
    max_value: float | None = None
    description: str | None = None
    display_order: int | None = None
    active: bool | None = None


class BaselineVariableRead(BaselineVariableBase):
    id: int
    baseline_model_id: int


class BaselineModelBase(ORMBase):
    name: str
    dependent_variable: str
    dependent_variable_unit: str
    formula_text: str | None = None
    model_type: str = "linear"
    coefficients: dict[str, float] | None = None
    intercept: float = 0.0
    r_squared: float | None = None
    adjusted_r_squared: float | None = None
    reference_period_start: date | None = None
    reference_period_end: date | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    active: bool = True


class BaselineModelCreate(BaselineModelBase):
    area_id: int
    energy_use_id: int


class BaselineModelUpdate(BaseModel):
    area_id: int | None = None
    energy_use_id: int | None = None
    name: str | None = None
    dependent_variable: str | None = None
    dependent_variable_unit: str | None = None
    formula_text: str | None = None
    model_type: str | None = None
    coefficients: dict[str, float] | None = None
    intercept: float | None = None
    r_squared: float | None = None
    adjusted_r_squared: float | None = None
    reference_period_start: date | None = None
    reference_period_end: date | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    active: bool | None = None


class BaselineModelRead(BaselineModelBase):
    id: int
    energy_system_id: int
    area_id: int
    energy_use_id: int


class IdeDefinitionBase(ORMBase):
    ide_code: str
    ide_name: str
    formula_text: str | None = None
    numerator: str | None = None
    denominator: str | None = None
    unit: str | None = None
    expected_range_min: float | None = None
    expected_range_max: float | None = None
    alert_threshold_percentage: float | None = None
    active: bool = True


class IdeDefinitionCreate(IdeDefinitionBase):
    area_id: int
    energy_use_id: int
    baseline_model_id: int


class IdeDefinitionUpdate(BaseModel):
    area_id: int | None = None
    energy_use_id: int | None = None
    baseline_model_id: int | None = None
    ide_code: str | None = None
    ide_name: str | None = None
    formula_text: str | None = None
    numerator: str | None = None
    denominator: str | None = None
    unit: str | None = None
    expected_range_min: float | None = None
    expected_range_max: float | None = None
    alert_threshold_percentage: float | None = None
    active: bool | None = None


class IdeDefinitionRead(IdeDefinitionBase):
    id: int
    energy_system_id: int
    area_id: int
    energy_use_id: int
    baseline_model_id: int


class MeasurementVariableInput(BaseModel):
    baseline_variable_id: int
    variable_code: str
    value: float


class MeasurementVariableRead(ORMBase):
    id: int
    monthly_measurement_id: int
    baseline_variable_id: int
    variable_name: str
    value: float
    unit: str | None = None
    created_at: datetime
    updated_at: datetime


class MonthlyMeasurementBase(ORMBase):
    area_id: int
    energy_use_id: int
    baseline_model_id: int
    ide_id: int
    year: int
    month: int
    real_consumption: float
    consumption_unit: str
    comments: str | None = None
    status: Literal["draft", "submitted", "reviewed", "approved", "rejected"] = "draft"
    variables: list[MeasurementVariableInput] = Field(default_factory=list)

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: int) -> int:
        if not 1 <= value <= 12:
            raise ValueError("month must be between 1 and 12")
        return value

    @field_validator("real_consumption")
    @classmethod
    def validate_consumption(cls, value: float) -> float:
        if value is None:
            raise ValueError("real_consumption is required")
        return value


class MonthlyMeasurementCreate(MonthlyMeasurementBase):
    pass


class MonthlyMeasurementUpdate(BaseModel):
    area_id: int | None = None
    energy_use_id: int | None = None
    baseline_model_id: int | None = None
    ide_id: int | None = None
    year: int | None = None
    month: int | None = None
    real_consumption: float | None = None
    consumption_unit: str | None = None
    comments: str | None = None
    status: Literal["draft", "submitted", "reviewed", "approved", "rejected"] | None = None
    variables: list[MeasurementVariableInput] | None = None


class MonthlyMeasurementRead(ORMBase):
    id: int
    energy_system_id: int
    area_id: int
    energy_use_id: int
    baseline_model_id: int
    ide_id: int
    year: int
    month: int
    real_consumption: float
    consumption_unit: str
    expected_consumption: float | None = None
    ide_real: float | None = None
    ide_expected: float | None = None
    difference: float | None = None
    percentage_difference: float | None = None
    compliance_status: str
    comments: str | None = None
    status: str
    created_by: int | None = None
    created_at: datetime
    updated_by: int | None = None
    updated_at: datetime
    variables: list[MeasurementVariableRead] = Field(default_factory=list)


class MeasurementAuditLogRead(ORMBase):
    id: int
    monthly_measurement_id: int
    user_id: int | None
    action: str
    field_name: str | None
    old_value: str | None
    new_value: str | None
    comment: str | None
    created_at: datetime


class AlertRuleBase(ORMBase):
    metric: str
    operator: str
    threshold_value: float | None = None
    threshold_percentage: float | None = None
    severity: str
    message_template: str
    active: bool = True


class AlertRuleCreate(AlertRuleBase):
    energy_system_id: int
    baseline_model_id: int
    ide_id: int | None = None


class AlertRuleUpdate(BaseModel):
    energy_system_id: int | None = None
    baseline_model_id: int | None = None
    ide_id: int | None = None
    metric: str | None = None
    operator: str | None = None
    threshold_value: float | None = None
    threshold_percentage: float | None = None
    severity: str | None = None
    message_template: str | None = None
    active: bool | None = None


class AlertRuleRead(AlertRuleBase):
    id: int
    energy_system_id: int
    baseline_model_id: int
    ide_id: int | None = None


class AlertEventRead(ORMBase):
    id: int
    energy_system_id: int
    monthly_measurement_id: int
    alert_rule_id: int | None
    severity: str
    message: str
    value_detected: float | None
    threshold_value: float | None
    status: str
    created_at: datetime


class DashboardKpis(BaseModel):
    real_consumption: float
    expected_consumption: float
    percentage_difference: float
    open_alerts: int


class TrendPoint(BaseModel):
    month: int
    real_consumption: float
    expected_consumption: float
    ide_real: float | None = None
    ide_expected: float | None = None


class AlertSummary(BaseModel):
    id: int
    severity: str
    message: str
    status: str
    created_at: datetime


class DashboardResponse(BaseModel):
    kpis: DashboardKpis
    real_vs_expected: list[TrendPoint]
    ide_trend: list[TrendPoint]
    recent_alerts: list[AlertSummary]


class PerformanceSummaryResponse(BaseModel):
    total_measurements: int
    compliant: int
    warning: int
    non_compliant: int
    incomplete: int
    open_alerts: int
    compliance_rate: float


class ApiMessage(BaseModel):
    message: str

