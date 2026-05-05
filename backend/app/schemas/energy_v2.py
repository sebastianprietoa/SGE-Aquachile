from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EnergyUseBaseYearBase(ORMBase):
    base_year: int
    area_id: int | None = None
    area_name: str
    installation_name: str
    energy_source: str
    use_category: str
    consumption_value: float
    consumption_unit: str
    consumption_tcal: float | None = None
    percentage: float | None = None
    accumulated_percentage: float | None = None
    source: str
    is_candidate_use: bool = False
    is_significant_use: bool = False
    notes: str | None = None
    active: bool = True


class EnergyUseBaseYearCreate(EnergyUseBaseYearBase):
    pass


class EnergyUseBaseYearRead(EnergyUseBaseYearBase):
    id: int
    energy_system_id: int


class SignificantEnergyUseBase(ORMBase):
    energy_use_base_year_id: int
    area_id: int | None = None
    name: str
    energy_source: str
    consumption_value: float | None = None
    consumption_unit: str | None = None
    selection_criteria: str | None = None
    current_energy_performance: float | None = None
    current_energy_performance_unit: str | None = None
    relevant_personnel: str | None = None
    operational_control_required: str | None = None
    improvement_opportunities: str | None = None
    active: bool = True


class SignificantEnergyUseCreate(SignificantEnergyUseBase):
    pass


class SignificantEnergyUseUpdate(BaseModel):
    energy_use_base_year_id: int | None = None
    area_id: int | None = None
    name: str | None = None
    energy_source: str | None = None
    consumption_value: float | None = None
    consumption_unit: str | None = None
    selection_criteria: str | None = None
    current_energy_performance: float | None = None
    current_energy_performance_unit: str | None = None
    relevant_personnel: str | None = None
    operational_control_required: str | None = None
    improvement_opportunities: str | None = None
    active: bool | None = None


class SignificantEnergyUseRead(SignificantEnergyUseBase):
    id: int
    energy_system_id: int


class BaselineVariableReadV2(ORMBase):
    id: int
    baseline_model_id: int
    variable_name: str
    variable_code: str
    variable_type: str
    unit: str | None = None
    required: bool
    min_value: float | None = None
    max_value: float | None = None
    description: str | None = None
    measurement_reason: str | None = None
    collection_method: str | None = None
    storage_location: str | None = None
    responsible_area: str | None = None
    responsible_person: str | None = None
    frequency: str | None = None
    missing_data_procedure: str | None = None
    display_order: int
    active: bool


class BaselineVariableCreateV2(BaseModel):
    variable_name: str
    variable_code: str
    variable_type: str
    unit: str | None = None
    required: bool = True
    min_value: float | None = None
    max_value: float | None = None
    description: str | None = None
    measurement_reason: str | None = None
    collection_method: str | None = None
    storage_location: str | None = None
    responsible_area: str | None = None
    responsible_person: str | None = None
    frequency: str | None = None
    missing_data_procedure: str | None = None
    display_order: int = 0
    active: bool = True


class BaselineVariableUpdateV2(BaseModel):
    variable_name: str | None = None
    variable_code: str | None = None
    variable_type: str | None = None
    unit: str | None = None
    required: bool | None = None
    min_value: float | None = None
    max_value: float | None = None
    description: str | None = None
    measurement_reason: str | None = None
    collection_method: str | None = None
    storage_location: str | None = None
    responsible_area: str | None = None
    responsible_person: str | None = None
    frequency: str | None = None
    missing_data_procedure: str | None = None
    display_order: int | None = None
    active: bool | None = None


class BaselineModelBaseV2(ORMBase):
    significant_energy_use_id: int | None = None
    area_id: int
    energy_use_id: int
    name: str
    dependent_variable: str
    dependent_variable_unit: str
    model_type: str = "linear"
    formula_text: str | None = None
    coefficients: dict[str, float] | None = None
    intercept: float = 0.0
    r_squared: float | None = None
    adjusted_r_squared: float | None = None
    reference_period_start: date | None = None
    reference_period_end: date | None = None
    static_factors: dict | None = None
    routine_adjustments: dict | None = None
    non_routine_adjustments: dict | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    active: bool = True


class BaselineModelCreateV2(BaselineModelBaseV2):
    pass


class BaselineModelUpdateV2(BaseModel):
    significant_energy_use_id: int | None = None
    area_id: int | None = None
    energy_use_id: int | None = None
    name: str | None = None
    dependent_variable: str | None = None
    dependent_variable_unit: str | None = None
    model_type: str | None = None
    formula_text: str | None = None
    coefficients: dict[str, float] | None = None
    intercept: float | None = None
    r_squared: float | None = None
    adjusted_r_squared: float | None = None
    reference_period_start: date | None = None
    reference_period_end: date | None = None
    static_factors: dict | None = None
    routine_adjustments: dict | None = None
    non_routine_adjustments: dict | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    active: bool | None = None


class BaselineModelReadV2(BaselineModelBaseV2):
    id: int
    energy_system_id: int


class IdeDefinitionBaseV2(ORMBase):
    significant_energy_use_id: int | None = None
    baseline_model_id: int
    area_id: int
    energy_use_id: int
    ide_code: str
    ide_name: str
    formula_text: str | None = None
    numerator: str | None = None
    denominator: str | None = None
    unit: str | None = None
    purpose: str | None = None
    frequency: str | None = None
    expected_range_min: float | None = None
    expected_range_max: float | None = None
    warning_threshold_percentage: float | None = None
    critical_threshold_percentage: float | None = None
    protocol_description: str | None = None
    active: bool = True


class IdeDefinitionCreateV2(IdeDefinitionBaseV2):
    pass


class IdeDefinitionUpdateV2(BaseModel):
    significant_energy_use_id: int | None = None
    baseline_model_id: int | None = None
    area_id: int | None = None
    energy_use_id: int | None = None
    ide_code: str | None = None
    ide_name: str | None = None
    formula_text: str | None = None
    numerator: str | None = None
    denominator: str | None = None
    unit: str | None = None
    purpose: str | None = None
    frequency: str | None = None
    expected_range_min: float | None = None
    expected_range_max: float | None = None
    warning_threshold_percentage: float | None = None
    critical_threshold_percentage: float | None = None
    protocol_description: str | None = None
    active: bool | None = None


class IdeDefinitionReadV2(IdeDefinitionBaseV2):
    id: int
    energy_system_id: int


class MonthlyMeasurementVariableInputV2(BaseModel):
    baseline_variable_id: int
    variable_code: str
    value: float


class MonthlyMeasurementBaseV2(ORMBase):
    significant_energy_use_id: int | None = None
    baseline_model_id: int
    ide_id: int
    area_id: int
    energy_use_id: int
    year: int
    month: int
    real_consumption: float
    consumption_unit: str
    expected_consumption: float | None = None
    ide_real: float | None = None
    ide_expected: float | None = None
    difference: float | None = None
    percentage_difference: float | None = None
    compliance_status: str = "incomplete"
    comments: str | None = None
    status: str = "draft"
    variables: list[MonthlyMeasurementVariableInputV2] = Field(default_factory=list)


class MonthlyMeasurementCreateV2(MonthlyMeasurementBaseV2):
    pass


class MonthlyMeasurementUpdateV2(BaseModel):
    significant_energy_use_id: int | None = None
    baseline_model_id: int | None = None
    ide_id: int | None = None
    area_id: int | None = None
    energy_use_id: int | None = None
    year: int | None = None
    month: int | None = None
    real_consumption: float | None = None
    consumption_unit: str | None = None
    comments: str | None = None
    status: str | None = None
    variables: list[MonthlyMeasurementVariableInputV2] | None = None


class MonthlyMeasurementVariableReadV2(ORMBase):
    id: int
    monthly_measurement_id: int
    baseline_variable_id: int
    variable_name: str
    variable_code: str | None = None
    value: float
    unit: str | None = None
    created_at: datetime
    updated_at: datetime


class MonthlyMeasurementReadV2(ORMBase):
    id: int
    energy_system_id: int
    significant_energy_use_id: int | None = None
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
    variables: list[MonthlyMeasurementVariableReadV2] = Field(default_factory=list)


class AlertEventReadV2(ORMBase):
    id: int
    energy_system_id: int
    monthly_measurement_id: int
    alert_rule_id: int | None = None
    severity: str
    message: str
    value_detected: float | None = None
    threshold_value: float | None = None
    status: str
    created_at: datetime


class OperationalControlBase(ORMBase):
    significant_energy_use_id: int
    name: str
    technical_criteria: str | None = None
    administrative_criteria: str | None = None
    maintenance_criteria: str | None = None
    responsible_area: str | None = None
    responsible_person: str | None = None
    record_type: str | None = None
    record_frequency: str | None = None
    training_required: bool = False
    last_training_date: date | None = None
    effectiveness_evaluation_method: str | None = None
    active: bool = True


class OperationalControlCreate(OperationalControlBase):
    pass


class OperationalControlUpdate(BaseModel):
    significant_energy_use_id: int | None = None
    name: str | None = None
    technical_criteria: str | None = None
    administrative_criteria: str | None = None
    maintenance_criteria: str | None = None
    responsible_area: str | None = None
    responsible_person: str | None = None
    record_type: str | None = None
    record_frequency: str | None = None
    training_required: bool | None = None
    last_training_date: date | None = None
    effectiveness_evaluation_method: str | None = None
    active: bool | None = None


class OperationalControlRead(OperationalControlBase):
    id: int
    energy_system_id: int


class TrackingMonthlyRow(BaseModel):
    id: int
    year: int
    month: int
    real_consumption: float
    expected_consumption: float | None = None
    ide_real: float | None = None
    ide_expected: float | None = None
    difference: float | None = None
    percentage_difference: float | None = None
    compliance_status: str
    status: str
    comments: str | None = None


class TrackingSummary(BaseModel):
    total_measurements: int
    compliant: int
    warning: int
    non_compliant: int
    incomplete: int
    average_percentage_difference: float
    open_alerts: int


class ParetoItem(BaseModel):
    label: str
    value: float
    percentage: float
    accumulated_percentage: float


class DataCollectionPlanItem(BaseModel):
    variable_name: str
    variable_code: str
    use_name: str
    baseline_name: str
    what_is_measured: str | None = None
    why_it_is_measured: str | None = None
    collection_method: str | None = None
    storage_location: str | None = None
    responsible_area: str | None = None
    responsible_person: str | None = None
    frequency: str | None = None
    missing_data_procedure: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    active: bool = True

