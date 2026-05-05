from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.measurement import AlertEvent, MonthlyMeasurement
from app.schemas.common import AlertSummary, DashboardKpis, DashboardResponse, PerformanceSummaryResponse, TrendPoint


def get_dashboard_response(db: Session, system_id: int) -> DashboardResponse:
    measurements = db.query(MonthlyMeasurement).filter(MonthlyMeasurement.energy_system_id == system_id).all()
    open_alerts = db.query(func.count(AlertEvent.id)).filter(AlertEvent.energy_system_id == system_id, AlertEvent.status == "open").scalar() or 0
    real_total = sum(float(item.real_consumption or 0) for item in measurements)
    expected_total = sum(float(item.expected_consumption or 0) for item in measurements)
    percentage_difference = 0.0 if expected_total == 0 else round(((real_total - expected_total) / expected_total) * 100, 4)
    recent_alerts = (
        db.query(AlertEvent)
        .filter(AlertEvent.energy_system_id == system_id)
        .order_by(AlertEvent.created_at.desc())
        .limit(5)
        .all()
    )
    grouped: dict[int, list[MonthlyMeasurement]] = defaultdict(list)
    for measurement in measurements:
        grouped[measurement.month].append(measurement)
    real_vs_expected = [
        TrendPoint(
            month=month,
            real_consumption=round(sum(item.real_consumption for item in items), 4),
            expected_consumption=round(sum(item.expected_consumption or 0 for item in items), 4),
            ide_real=round(sum(item.ide_real or 0 for item in items), 4) if items else None,
            ide_expected=round(sum(item.ide_expected or 0 for item in items), 4) if items else None,
        )
        for month, items in sorted(grouped.items())
    ]
    ide_trend = [
        TrendPoint(
            month=month,
            real_consumption=round(sum(item.real_consumption for item in items), 4),
            expected_consumption=round(sum(item.expected_consumption or 0 for item in items), 4),
            ide_real=round(sum(item.ide_real or 0 for item in items) / max(len(items), 1), 4),
            ide_expected=round(sum(item.ide_expected or 0 for item in items) / max(len(items), 1), 4),
        )
        for month, items in sorted(grouped.items())
    ]
    return DashboardResponse(
        kpis=DashboardKpis(
            real_consumption=round(real_total, 4),
            expected_consumption=round(expected_total, 4),
            percentage_difference=percentage_difference,
            open_alerts=int(open_alerts),
        ),
        real_vs_expected=real_vs_expected,
        ide_trend=ide_trend,
        recent_alerts=[
            AlertSummary(
                id=item.id,
                severity=item.severity,
                message=item.message,
                status=item.status,
                created_at=item.created_at,
            )
            for item in recent_alerts
        ],
    )


def get_performance_summary(db: Session, system_id: int) -> PerformanceSummaryResponse:
    measurements = db.query(MonthlyMeasurement).filter(MonthlyMeasurement.energy_system_id == system_id).all()
    total = len(measurements)
    compliant = sum(1 for item in measurements if item.compliance_status == "compliant")
    warning = sum(1 for item in measurements if item.compliance_status == "warning")
    non_compliant = sum(1 for item in measurements if item.compliance_status == "non_compliant")
    incomplete = sum(1 for item in measurements if item.compliance_status == "incomplete")
    open_alerts = db.query(func.count(AlertEvent.id)).filter(AlertEvent.energy_system_id == system_id, AlertEvent.status == "open").scalar() or 0
    return PerformanceSummaryResponse(
        total_measurements=total,
        compliant=compliant,
        warning=warning,
        non_compliant=non_compliant,
        incomplete=incomplete,
        open_alerts=int(open_alerts),
        compliance_rate=round((compliant / total) * 100, 2) if total else 0.0,
    )


def get_monthly_trends(db: Session, system_id: int) -> list[TrendPoint]:
    measurements = db.query(MonthlyMeasurement).filter(MonthlyMeasurement.energy_system_id == system_id).all()
    grouped: dict[int, list[MonthlyMeasurement]] = defaultdict(list)
    for measurement in measurements:
        grouped[measurement.month].append(measurement)
    return [
        TrendPoint(
            month=month,
            real_consumption=round(sum(item.real_consumption for item in items), 4),
            expected_consumption=round(sum(item.expected_consumption or 0 for item in items), 4),
            ide_real=round(sum(item.ide_real or 0 for item in items) / max(len(items), 1), 4),
            ide_expected=round(sum(item.ide_expected or 0 for item in items) / max(len(items), 1), 4),
        )
        for month, items in sorted(grouped.items())
    ]

