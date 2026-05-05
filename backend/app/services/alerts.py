from __future__ import annotations

from dataclasses import dataclass

from app.services.calculations import VariableValidationIssue


@dataclass(slots=True)
class AlertDraft:
    severity: str
    message: str
    value_detected: float | None = None
    threshold_value: float | None = None
    status: str = "open"


def build_default_alerts(
    *,
    missing_required: bool,
    real_consumption: float | None,
    percentage_difference: float | None,
    ide_real: float | None,
    ide_expected_min: float | None,
    ide_expected_max: float | None,
    variable_issues: list[VariableValidationIssue],
) -> list[AlertDraft]:
    alerts: list[AlertDraft] = []

    if missing_required:
        alerts.append(
            AlertDraft(
                severity="critical",
                message="Existen variables requeridas sin información para la medición mensual.",
            )
        )

    if real_consumption is not None and real_consumption <= 0:
        alerts.append(
            AlertDraft(
                severity="critical",
                message="El consumo real es cero o negativo.",
                value_detected=real_consumption,
            )
        )

    if percentage_difference is not None:
        abs_diff = abs(percentage_difference)
        if abs_diff > 20:
            alerts.append(
                AlertDraft(
                    severity="high",
                    message="La desviación porcentual supera el 20%.",
                    value_detected=percentage_difference,
                    threshold_value=20,
                )
            )
        elif abs_diff > 10:
            alerts.append(
                AlertDraft(
                    severity="medium",
                    message="La desviación porcentual supera el 10% y requiere revisión.",
                    value_detected=percentage_difference,
                    threshold_value=10,
                )
            )

    if ide_real is not None:
        if ide_expected_min is not None and ide_real < ide_expected_min:
            alerts.append(
                AlertDraft(
                    severity="high",
                    message="El IDE real está fuera del rango esperado por debajo del mínimo.",
                    value_detected=ide_real,
                    threshold_value=ide_expected_min,
                )
            )
        if ide_expected_max is not None and ide_real > ide_expected_max:
            alerts.append(
                AlertDraft(
                    severity="high",
                    message="El IDE real está fuera del rango esperado sobre el máximo.",
                    value_detected=ide_real,
                    threshold_value=ide_expected_max,
                )
            )

    for issue in variable_issues:
        alerts.append(
            AlertDraft(
                severity=issue.severity,
                message=f"{issue.variable_code}: {issue.message}",
            )
        )

    return alerts

