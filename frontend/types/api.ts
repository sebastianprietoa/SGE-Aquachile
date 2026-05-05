export interface EnergySystem {
  id: number;
  code: string;
  name: string;
  company: string;
  description?: string | null;
  active: boolean;
}

export interface EnergyArea {
  id: number;
  energy_system_id: number;
  name: string;
  type: string;
  description?: string | null;
  active: boolean;
}

export interface EnergyUse {
  id: number;
  energy_system_id: number;
  area_id: number;
  name: string;
  energy_source: string;
  description?: string | null;
  is_significant: boolean;
  active: boolean;
}

export interface BaselineModel {
  id: number;
  energy_system_id: number;
  area_id: number;
  energy_use_id: number;
  name: string;
  dependent_variable: string;
  dependent_variable_unit: string;
  formula_text?: string | null;
  model_type: string;
  coefficients?: Record<string, number> | null;
  intercept: number;
  r_squared?: number | null;
  adjusted_r_squared?: number | null;
  reference_period_start?: string | null;
  reference_period_end?: string | null;
  valid_from?: string | null;
  valid_to?: string | null;
  active: boolean;
}

export interface BaselineVariable {
  id: number;
  baseline_model_id: number;
  variable_name: string;
  variable_code: string;
  variable_type: string;
  unit?: string | null;
  required: boolean;
  min_value?: number | null;
  max_value?: number | null;
  description?: string | null;
  display_order: number;
  active: boolean;
}

export interface IdeDefinition {
  id: number;
  energy_system_id: number;
  area_id: number;
  energy_use_id: number;
  baseline_model_id: number;
  ide_code: string;
  ide_name: string;
  formula_text?: string | null;
  numerator?: string | null;
  denominator?: string | null;
  unit?: string | null;
  expected_range_min?: number | null;
  expected_range_max?: number | null;
  alert_threshold_percentage?: number | null;
  active: boolean;
}

export interface MonthlyMeasurementVariable {
  id: number;
  monthly_measurement_id: number;
  baseline_variable_id: number;
  variable_name: string;
  value: number;
  unit?: string | null;
  created_at: string;
  updated_at: string;
}

export interface MonthlyMeasurement {
  id: number;
  energy_system_id: number;
  area_id: number;
  energy_use_id: number;
  baseline_model_id: number;
  ide_id: number;
  year: number;
  month: number;
  real_consumption: number;
  consumption_unit: string;
  expected_consumption?: number | null;
  ide_real?: number | null;
  ide_expected?: number | null;
  difference?: number | null;
  percentage_difference?: number | null;
  compliance_status: string;
  comments?: string | null;
  status: string;
  created_by?: number | null;
  created_at: string;
  updated_by?: number | null;
  updated_at: string;
  variables: MonthlyMeasurementVariable[];
}

export interface MeasurementAuditLog {
  id: number;
  monthly_measurement_id: number;
  user_id?: number | null;
  action: string;
  field_name?: string | null;
  old_value?: string | null;
  new_value?: string | null;
  comment?: string | null;
  created_at: string;
}

export interface AlertEvent {
  id: number;
  energy_system_id: number;
  monthly_measurement_id: number;
  alert_rule_id?: number | null;
  severity: string;
  message: string;
  value_detected?: number | null;
  threshold_value?: number | null;
  status: string;
  created_at: string;
}

export interface AlertRule {
  id?: number;
  energy_system_id: number;
  baseline_model_id: number;
  ide_id?: number | null;
  metric: string;
  operator: string;
  threshold_value?: number | null;
  threshold_percentage?: number | null;
  severity: string;
  message_template: string;
  active: boolean;
}

export interface DashboardResponse {
  kpis: {
    real_consumption: number;
    expected_consumption: number;
    percentage_difference: number;
    open_alerts: number;
  };
  real_vs_expected: TrendPoint[];
  ide_trend: TrendPoint[];
  recent_alerts: {
    id: number;
    severity: string;
    message: string;
    status: string;
    created_at: string;
  }[];
}

export interface TrendPoint {
  month: number;
  real_consumption: number;
  expected_consumption: number;
  ide_real?: number | null;
  ide_expected?: number | null;
}

export interface PerformanceSummaryResponse {
  total_measurements: number;
  compliant: number;
  warning: number;
  non_compliant: number;
  incomplete: number;
  open_alerts: number;
  compliance_rate: number;
}

export interface MonthlyMeasurementVariableInput {
  baseline_variable_id: number;
  variable_code: string;
  value: number;
}

export interface MonthlyMeasurementCreatePayload {
  area_id: number;
  energy_use_id: number;
  baseline_model_id: number;
  ide_id: number;
  year: number;
  month: number;
  real_consumption: number;
  consumption_unit: string;
  comments?: string | null;
  status: "draft" | "submitted" | "reviewed" | "approved" | "rejected";
  variables: MonthlyMeasurementVariableInput[];
}

export interface MonthlyMeasurementUpdatePayload extends Partial<MonthlyMeasurementCreatePayload> {}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  user: {
    id: number;
    username: string;
    full_name: string;
    email: string;
    role: string;
    active: boolean;
  };
}

