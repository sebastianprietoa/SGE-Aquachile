from __future__ import annotations

from dataclasses import dataclass

from app.models.energy import BaselineVariable, IdeDefinition
from app.models.measurement import MonthlyMeasurement


@dataclass(slots=True)
class AlertDraft:
    severity: str
    message: str
    value_detected: float | None = None
    threshold_value: float | None = None


def detect_missing_required_variables(variable_map: dict[str, float], baseline_variables: list[BaselineVariable]) -> list[AlertDraft]:
    missing = [item.variable_name for item in baseline_variables if item.required and item.variable_code not in variable_map]
    if not missing:
        return []
    return [AlertDraft(severity="critical", message=f"Faltan variables requeridas: {', '.join(missing)}")]


def detect_out_of_range_variables(variable_map: dict[str, float], baseline_variables: list[BaselineVariable]) -> list[AlertDraft]:
    alerts: list[AlertDraft] = []
    for item in baseline_variables:
        if item.variable_code not in variable_map:
            continue
        value = float(variable_map[item.variable_code])
        if item.min_value is not None and value < item.min_value:
            alerts.append(AlertDraft(severity="medium", message=f"{item.variable_name} está bajo el mínimo permitido", threshold_value=item.min_value, value_detected=value))
        if item.max_value is not None and value > item.max_value:
            alerts.append(AlertDraft(severity="high", message=f"{item.variable_name} está sobre el máximo permitido", threshold_value=item.max_value, value_detected=value))
    return alerts


def detect_high_deviation(percentage_difference: float | None) -> list[AlertDraft]:
    if percentage_difference is None:
        return []
    deviation = abs(percentage_difference)
    if deviation > 20:
        return [AlertDraft(severity="high", message="Desviación crítica superior al 20%", threshold_value=20, value_detected=percentage_difference)]
    if deviation > 10:
        return [AlertDraft(severity="medium", message="Desviación sobre 10% y requiere revisión", threshold_value=10, value_detected=percentage_difference)]
    return []


def detect_ide_out_of_range(ide_real: float | None, ide_definition: IdeDefinition) -> list[AlertDraft]:
    if ide_real is None:
        return []
    alerts: list[AlertDraft] = []
    if ide_definition.expected_range_min is not None and ide_real < ide_definition.expected_range_min:
        alerts.append(AlertDraft(severity="high", message="IDE real bajo el rango esperado", threshold_value=ide_definition.expected_range_min, value_detected=ide_real))
    if ide_definition.expected_range_max is not None and ide_real > ide_definition.expected_range_max:
        alerts.append(AlertDraft(severity="high", message="IDE real sobre el rango esperado", threshold_value=ide_definition.expected_range_max, value_detected=ide_real))
    return alerts


def detect_zero_or_negative_consumption(real_consumption: float | None) -> list[AlertDraft]:
    if real_consumption is None or real_consumption > 0:
        return []
    return [AlertDraft(severity="critical", message="El consumo real es cero o negativo", value_detected=real_consumption)]


def generate_alerts_for_measurement(
    measurement: MonthlyMeasurement,
    *,
    baseline_variables: list[BaselineVariable],
    variable_map: dict[str, float],
    percentage_difference: float | None,
    ide_definition: IdeDefinition,
) -> list[AlertDraft]:
    alerts: list[AlertDraft] = []
    alerts.extend(detect_missing_required_variables(variable_map, baseline_variables))
    alerts.extend(detect_out_of_range_variables(variable_map, baseline_variables))
    alerts.extend(detect_high_deviation(percentage_difference))
    alerts.extend(detect_ide_out_of_range(measurement.ide_real, ide_definition))
    alerts.extend(detect_zero_or_negative_consumption(measurement.real_consumption))
    return alerts

