from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(slots=True)
class VariableValidationIssue:
    variable_code: str
    message: str
    severity: str


def calculate_expected_consumption(intercept: float, coefficients: dict[str, float] | None, variable_values: dict[str, float]) -> float | None:
    coefficients = coefficients or {}
    missing_codes = [code for code in coefficients if code not in variable_values]
    if missing_codes:
        return None
    total = float(intercept or 0.0)
    for code, coefficient in coefficients.items():
        total += float(coefficient) * float(variable_values[code])
    return round(total, 4)


def calculate_difference(real_consumption: float | None, expected_consumption: float | None) -> float | None:
    if real_consumption is None or expected_consumption is None:
        return None
    return round(float(real_consumption) - float(expected_consumption), 4)


def calculate_percentage_difference(difference: float | None, expected_consumption: float | None) -> float | None:
    if difference is None or expected_consumption in (None, 0):
        return None
    return round((float(difference) / float(expected_consumption)) * 100, 4)


def classify_compliance(percentage_difference: float | None, has_all_required: bool, real_consumption: float | None, expected_consumption: float | None) -> str:
    if not has_all_required or real_consumption is None or expected_consumption in (None, 0):
        return "incomplete"
    if percentage_difference is None:
        return "incomplete"
    if abs(percentage_difference) <= 10:
        return "compliant"
    if abs(percentage_difference) <= 20:
        return "warning"
    return "non_compliant"


def calculate_ide_value(real_consumption: float | None, denominator_value: float | None) -> float | None:
    if real_consumption is None or denominator_value in (None, 0):
        return None
    return round(float(real_consumption) / float(denominator_value), 4)


def get_denominator_value(denominator_code: str | None, variable_values: dict[str, float]) -> float | None:
    if not denominator_code:
        return None
    return variable_values.get(denominator_code)


def validate_variable_ranges(
    baseline_variables: Iterable[tuple[str, float | None, float | None, bool]],
    variable_values: dict[str, float],
) -> list[VariableValidationIssue]:
    issues: list[VariableValidationIssue] = []
    for code, min_value, max_value, required in baseline_variables:
        if code not in variable_values:
            if required:
                issues.append(VariableValidationIssue(code, "Variable requerida no informada", "critical"))
            continue
        value = float(variable_values[code])
        if min_value is not None and value < min_value:
            issues.append(VariableValidationIssue(code, f"Valor bajo mínimo permitido ({min_value})", "medium"))
        if max_value is not None and value > max_value:
            issues.append(VariableValidationIssue(code, f"Valor sobre máximo permitido ({max_value})", "high"))
    return issues


def has_all_required_variables(required_codes: Iterable[str], variable_values: dict[str, float]) -> bool:
    return all(code in variable_values for code in required_codes)

