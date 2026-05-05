from app.services.alerts import build_default_alerts
from app.services.calculations import calculate_difference, calculate_expected_consumption, calculate_percentage_difference, classify_compliance


def test_calculate_expected_consumption_linear_model() -> None:
    result = calculate_expected_consumption(
        120,
        {"production_monthly": 0.42, "ambient_temperature": 1.1, "operating_hours": 2.8},
        {"production_monthly": 4300, "ambient_temperature": 18, "operating_hours": 290},
    )
    assert result == 2757.8


def test_calculate_difference_and_percentage() -> None:
    difference = calculate_difference(2120, 2000)
    percentage = calculate_percentage_difference(difference, 2000)
    assert difference == 120
    assert percentage == 6.0


def test_classification_thresholds() -> None:
    assert classify_compliance(8, True, 100, 100) == "compliant"
    assert classify_compliance(15, True, 100, 100) == "warning"
    assert classify_compliance(25, True, 100, 100) == "non_compliant"
    assert classify_compliance(None, False, None, None) == "incomplete"


def test_alert_generation_rules() -> None:
    alerts = build_default_alerts(
        missing_required=True,
        real_consumption=-1,
        percentage_difference=24,
        ide_real=7.2,
        ide_expected_min=0.5,
        ide_expected_max=4.5,
        variable_issues=[],
    )
    severities = [item.severity for item in alerts]
    assert "critical" in severities
    assert "high" in severities
