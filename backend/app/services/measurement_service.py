from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.energy import AlertRule, BaselineModel, BaselineVariable, EnergyArea, EnergySystem, EnergyUse, IdeDefinition
from app.models.measurement import AlertEvent, MeasurementAuditLog, MonthlyMeasurement, MonthlyMeasurementVariable, User
from app.schemas.common import MeasurementVariableInput, MonthlyMeasurementCreate, MonthlyMeasurementUpdate
from app.services.alerts import build_default_alerts
from app.services.calculations import (
    calculate_difference,
    calculate_expected_consumption,
    calculate_ide_value,
    calculate_percentage_difference,
    classify_compliance,
    get_denominator_value,
    has_all_required_variables,
    validate_variable_ranges,
)


def _validate_context(
    db: Session,
    *,
    energy_system_id: int,
    area_id: int,
    energy_use_id: int,
    baseline_model_id: int,
    ide_id: int,
) -> tuple[EnergySystem, EnergyArea, EnergyUse, BaselineModel, IdeDefinition]:
    system = db.get(EnergySystem, energy_system_id)
    area = db.get(EnergyArea, area_id)
    energy_use = db.get(EnergyUse, energy_use_id)
    baseline = db.get(BaselineModel, baseline_model_id)
    ide = db.get(IdeDefinition, ide_id)

    if not system or not area or not energy_use or not baseline or not ide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contexto energético no encontrado")
    if baseline.energy_system_id != energy_system_id or ide.energy_system_id != energy_system_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La línea base o IDE no pertenece al sistema seleccionado")
    if area.energy_system_id != energy_system_id or energy_use.energy_system_id != energy_system_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Área o uso energético no pertenece al sistema seleccionado")
    if baseline.area_id != area_id or baseline.energy_use_id != energy_use_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La línea base no corresponde al área o uso energético")
    if ide.area_id != area_id or ide.energy_use_id != energy_use_id or ide.baseline_model_id != baseline_model_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El IDE no corresponde al contexto seleccionado")
    return system, area, energy_use, baseline, ide


def _normalize_variable_payload(variables: list[MeasurementVariableInput]) -> dict[int, MeasurementVariableInput]:
    return {item.baseline_variable_id: item for item in variables}


def _audit(db: Session, measurement: MonthlyMeasurement, action: str, user_id: int | None, field_name: str | None, old_value: str | None, new_value: str | None, comment: str | None = None) -> MeasurementAuditLog:
    log = MeasurementAuditLog(
        monthly_measurement_id=measurement.id,
        user_id=user_id,
        action=action,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        comment=comment,
    )
    db.add(log)
    return log


def _serialize_value(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _ensure_unique_measurement(db: Session, payload: MonthlyMeasurementCreate, energy_system_id: int, measurement_id: int | None = None) -> None:
    query = (
        db.query(MonthlyMeasurement)
        .filter(
            MonthlyMeasurement.energy_system_id == energy_system_id,
            MonthlyMeasurement.area_id == payload.area_id,
            MonthlyMeasurement.energy_use_id == payload.energy_use_id,
            MonthlyMeasurement.baseline_model_id == payload.baseline_model_id,
            MonthlyMeasurement.year == payload.year,
            MonthlyMeasurement.month == payload.month,
        )
    )
    if measurement_id is not None:
        query = query.filter(MonthlyMeasurement.id != measurement_id)
    if query.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe una medición para esa combinación de sistema, área, uso, línea base, año y mes")


def _collect_variable_map(db: Session, baseline_model_id: int, variables: list[MeasurementVariableInput]) -> tuple[dict[str, float], list[BaselineVariable]]:
    baseline_vars = (
        db.query(BaselineVariable)
        .filter(BaselineVariable.baseline_model_id == baseline_model_id, BaselineVariable.active.is_(True))
        .order_by(BaselineVariable.display_order.asc(), BaselineVariable.id.asc())
        .all()
    )
    allowed_by_id = {item.id: item for item in baseline_vars}
    allowed_codes = {item.variable_code for item in baseline_vars}
    variable_map: dict[str, float] = {}
    for item in variables:
        baseline_variable = allowed_by_id.get(item.baseline_variable_id)
        if baseline_variable is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"La variable {item.variable_code} no pertenece a la línea base seleccionada")
        if item.variable_code != baseline_variable.variable_code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El código de variable {item.variable_code} no coincide con la definición de la línea base")
        variable_map[item.variable_code] = float(item.value)
    extra_codes = set(variable_map) - allowed_codes
    if extra_codes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Variables no permitidas: {', '.join(sorted(extra_codes))}")
    return variable_map, baseline_vars


def _base_variable_summary(baseline_vars: Iterable[BaselineVariable]) -> list[tuple[str, float | None, float | None, bool]]:
    return [(var.variable_code, var.min_value, var.max_value, var.required) for var in baseline_vars]


def _upsert_measurement_variables(
    db: Session,
    measurement: MonthlyMeasurement,
    baseline_vars: list[BaselineVariable],
    payload_variables: list[MeasurementVariableInput],
    user_id: int | None,
) -> None:
    payload_map = _normalize_variable_payload(payload_variables)
    existing_by_baseline_id = {item.baseline_variable_id: item for item in measurement.variables}
    for baseline_var in baseline_vars:
        incoming = payload_map.get(baseline_var.id)
        if incoming is None:
            continue
        existing = existing_by_baseline_id.get(baseline_var.id)
        if existing:
            old_value = existing.value
            existing.value = float(incoming.value)
            existing.variable_name = baseline_var.variable_name
            existing.unit = baseline_var.unit
            if old_value != existing.value:
                _audit(db, measurement, "updated", user_id, baseline_var.variable_code, _serialize_value(old_value), _serialize_value(existing.value), "Actualización de variable mensual")
        else:
            db.add(
                MonthlyMeasurementVariable(
                    monthly_measurement_id=measurement.id,
                    baseline_variable_id=baseline_var.id,
                    variable_name=baseline_var.variable_name,
                    value=float(incoming.value),
                    unit=baseline_var.unit,
                )
            )
            _audit(db, measurement, "created", user_id, baseline_var.variable_code, None, _serialize_value(incoming.value), "Carga de variable mensual")


def _measurement_response(measurement: MonthlyMeasurement) -> MonthlyMeasurement:
    return measurement


def _compute_results(
    *,
    baseline: BaselineModel,
    ide: IdeDefinition,
    baseline_vars: list[BaselineVariable],
    variable_values: dict[str, float],
    real_consumption: float,
) -> tuple[float | None, float | None, float | None, float | None, str, list[object]]:
    required_codes = [item.variable_code for item in baseline_vars if item.required]
    has_required = has_all_required_variables(required_codes, variable_values)
    variable_issues = validate_variable_ranges(_base_variable_summary(baseline_vars), variable_values)
    expected = calculate_expected_consumption(baseline.intercept, baseline.coefficients, variable_values) if has_required else None
    denominator_value = get_denominator_value(ide.denominator, variable_values)
    ide_real = calculate_ide_value(real_consumption, denominator_value)
    ide_expected = calculate_ide_value(expected, denominator_value) if expected is not None else None
    difference = calculate_difference(real_consumption, expected)
    percentage_difference = calculate_percentage_difference(difference, expected)
    compliance_status = classify_compliance(percentage_difference, has_required and not variable_issues and real_consumption is not None and real_consumption > 0, real_consumption, expected)
    return expected, ide_real, ide_expected, difference, percentage_difference, compliance_status, variable_issues


def _create_alert_events(
    db: Session,
    measurement: MonthlyMeasurement,
    *,
    system_id: int,
    baseline: BaselineModel,
    ide: IdeDefinition,
    variable_issues: list[object],
    percentage_difference: float | None,
    real_consumption: float | None,
    ide_real: float | None,
    user_id: int | None,
) -> list[AlertEvent]:
    alerts = build_default_alerts(
        missing_required=measurement.compliance_status == "incomplete",
        real_consumption=real_consumption,
        percentage_difference=percentage_difference,
        ide_real=ide_real,
        ide_expected_min=ide.expected_range_min,
        ide_expected_max=ide.expected_range_max,
        variable_issues=variable_issues,
    )
    created_alerts: list[AlertEvent] = []
    for draft in alerts:
        alert = AlertEvent(
            energy_system_id=system_id,
            monthly_measurement_id=measurement.id,
            alert_rule_id=None,
            severity=draft.severity,
            message=draft.message,
            value_detected=draft.value_detected,
            threshold_value=draft.threshold_value,
            status=draft.status,
        )
        db.add(alert)
        created_alerts.append(alert)
    if alerts:
        _audit(db, measurement, "updated", user_id, "alerts", None, str(len(alerts)), "Generación automática de alertas")
    return created_alerts


def create_monthly_measurement(
    db: Session,
    *,
    energy_system_id: int,
    payload: MonthlyMeasurementCreate,
    user: User | None,
) -> MonthlyMeasurement:
    if not payload.baseline_model_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La medición mensual requiere una línea base")
    _validate_context(
        db,
        energy_system_id=energy_system_id,
        area_id=payload.area_id,
        energy_use_id=payload.energy_use_id,
        baseline_model_id=payload.baseline_model_id,
        ide_id=payload.ide_id,
    )
    _ensure_unique_measurement(db, payload, energy_system_id)
    variable_map, baseline_vars = _collect_variable_map(db, payload.baseline_model_id, payload.variables)
    required_codes = [item.variable_code for item in baseline_vars if item.required]
    has_required = has_all_required_variables(required_codes, variable_map)
    variable_issues = validate_variable_ranges(_base_variable_summary(baseline_vars), variable_map)
    missing_required = not has_required
    expected, ide_real, ide_expected, difference, percentage_difference, compliance_status, variable_issues = _compute_results(
        baseline=db.get(BaselineModel, payload.baseline_model_id),
        ide=db.get(IdeDefinition, payload.ide_id),
        baseline_vars=baseline_vars,
        variable_values=variable_map,
        real_consumption=payload.real_consumption,
    )
    measurement = MonthlyMeasurement(
        energy_system_id=energy_system_id,
        area_id=payload.area_id,
        energy_use_id=payload.energy_use_id,
        baseline_model_id=payload.baseline_model_id,
        ide_id=payload.ide_id,
        year=payload.year,
        month=payload.month,
        real_consumption=payload.real_consumption,
        consumption_unit=payload.consumption_unit,
        expected_consumption=expected,
        ide_real=ide_real,
        ide_expected=ide_expected,
        difference=difference,
        percentage_difference=percentage_difference,
        compliance_status=compliance_status,
        comments=payload.comments,
        status=payload.status,
        created_by=user.id if user else None,
        updated_by=user.id if user else None,
    )
    db.add(measurement)
    db.flush()
    _upsert_measurement_variables(db, measurement, baseline_vars, payload.variables, user.id if user else None)
    _audit(db, measurement, "created", user.id if user else None, None, None, None, "Creación de medición mensual")
    _create_alert_events(
        db,
        measurement,
        system_id=energy_system_id,
        baseline=db.get(BaselineModel, payload.baseline_model_id),
        ide=db.get(IdeDefinition, payload.ide_id),
        variable_issues=variable_issues,
        percentage_difference=percentage_difference,
        real_consumption=payload.real_consumption,
        ide_real=ide_real,
        user_id=user.id if user else None,
    )
    db.commit()
    db.refresh(measurement)
    return measurement


def update_monthly_measurement(
    db: Session,
    measurement_id: int,
    payload: MonthlyMeasurementUpdate,
    user: User | None,
) -> MonthlyMeasurement:
    measurement = db.get(MonthlyMeasurement, measurement_id)
    if not measurement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medición no encontrada")
    updated_data = payload.model_dump(exclude_unset=True)
    if "baseline_model_id" in updated_data or "ide_id" in updated_data or "area_id" in updated_data or "energy_use_id" in updated_data:
        context = {
            "area_id": updated_data.get("area_id", measurement.area_id),
            "energy_use_id": updated_data.get("energy_use_id", measurement.energy_use_id),
            "baseline_model_id": updated_data.get("baseline_model_id", measurement.baseline_model_id),
            "ide_id": updated_data.get("ide_id", measurement.ide_id),
        }
        _validate_context(
            db,
            energy_system_id=measurement.energy_system_id,
            area_id=context["area_id"],
            energy_use_id=context["energy_use_id"],
            baseline_model_id=context["baseline_model_id"],
            ide_id=context["ide_id"],
        )
    baseline = db.get(BaselineModel, updated_data.get("baseline_model_id", measurement.baseline_model_id))
    ide = db.get(IdeDefinition, updated_data.get("ide_id", measurement.ide_id))
    if "year" in updated_data or "month" in updated_data or "baseline_model_id" in updated_data or "area_id" in updated_data or "energy_use_id" in updated_data:
        class PayloadLike:
            pass

        payload_like = PayloadLike()
        payload_like.area_id = updated_data.get("area_id", measurement.area_id)
        payload_like.energy_use_id = updated_data.get("energy_use_id", measurement.energy_use_id)
        payload_like.baseline_model_id = updated_data.get("baseline_model_id", measurement.baseline_model_id)
        payload_like.year = updated_data.get("year", measurement.year)
        payload_like.month = updated_data.get("month", measurement.month)
        _ensure_unique_measurement(db, payload_like, measurement.energy_system_id, measurement.id)
    for field in ["area_id", "energy_use_id", "baseline_model_id", "ide_id", "year", "month", "real_consumption", "consumption_unit", "comments", "status"]:
        if field in updated_data:
            old_value = getattr(measurement, field)
            new_value = updated_data[field]
            if old_value != new_value:
                setattr(measurement, field, new_value)
                _audit(db, measurement, "updated", user.id if user else None, field, _serialize_value(old_value), _serialize_value(new_value), "Actualización de medición mensual")
    if "variables" in updated_data and updated_data["variables"] is not None:
        variable_map, baseline_vars = _collect_variable_map(db, measurement.baseline_model_id, updated_data["variables"])
        expected, ide_real, ide_expected, difference, percentage_difference, compliance_status, variable_issues = _compute_results(
            baseline=baseline,
            ide=ide,
            baseline_vars=baseline_vars,
            variable_values=variable_map,
            real_consumption=measurement.real_consumption,
        )
        measurement.expected_consumption = expected
        measurement.ide_real = ide_real
        measurement.ide_expected = ide_expected
        measurement.difference = difference
        measurement.percentage_difference = percentage_difference
        measurement.compliance_status = compliance_status
        _upsert_measurement_variables(db, measurement, baseline_vars, updated_data["variables"], user.id if user else None)
        for alert in measurement.alerts:
            alert.status = "resolved" if compliance_status == "compliant" else alert.status
        _create_alert_events(
            db,
            measurement,
            system_id=measurement.energy_system_id,
            baseline=baseline,
            ide=ide,
            variable_issues=variable_issues,
            percentage_difference=percentage_difference,
            real_consumption=measurement.real_consumption,
            ide_real=ide_real,
            user_id=user.id if user else None,
        )
    measurement.updated_by = user.id if user else None
    measurement.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(measurement)
    return measurement


def transition_measurement_status(db: Session, measurement_id: int, status_value: str, user: User | None, comment: str | None = None) -> MonthlyMeasurement:
    measurement = db.get(MonthlyMeasurement, measurement_id)
    if not measurement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medición no encontrada")
    old_status = measurement.status
    measurement.status = status_value
    measurement.updated_by = user.id if user else None
    measurement.updated_at = datetime.now(timezone.utc)
    _audit(db, measurement, status_value, user.id if user else None, "status", old_status, status_value, comment or f"Cambio de estado a {status_value}")
    db.commit()
    db.refresh(measurement)
    return measurement


def add_measurement_audit_comment(db: Session, measurement_id: int, user: User | None, comment: str) -> MeasurementAuditLog:
    measurement = db.get(MonthlyMeasurement, measurement_id)
    if not measurement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medición no encontrada")
    entry = _audit(db, measurement, "updated", user.id if user else None, "comment", None, comment, comment)
    db.commit()
    db.refresh(entry)
    return entry


def get_measurement_by_id(db: Session, measurement_id: int) -> MonthlyMeasurement | None:
    return db.get(MonthlyMeasurement, measurement_id)


def list_measurements(db: Session, system_id: int, year: int | None = None, month: int | None = None, area_id: int | None = None, energy_use_id: int | None = None, status_value: str | None = None) -> list[MonthlyMeasurement]:
    query = db.query(MonthlyMeasurement).filter(MonthlyMeasurement.energy_system_id == system_id)
    if year is not None:
        query = query.filter(MonthlyMeasurement.year == year)
    if month is not None:
        query = query.filter(MonthlyMeasurement.month == month)
    if area_id is not None:
        query = query.filter(MonthlyMeasurement.area_id == area_id)
    if energy_use_id is not None:
        query = query.filter(MonthlyMeasurement.energy_use_id == energy_use_id)
    if status_value:
        query = query.filter(MonthlyMeasurement.status == status_value)
    return query.order_by(MonthlyMeasurement.year.desc(), MonthlyMeasurement.month.desc(), MonthlyMeasurement.id.desc()).all()


def list_measurement_alerts(db: Session, measurement_id: int) -> list[AlertEvent]:
    return db.query(AlertEvent).filter(AlertEvent.monthly_measurement_id == measurement_id).order_by(AlertEvent.created_at.desc()).all()

