from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.energy import BaselineModel, BaselineVariable, EnergySystem, EnergyUseBaseYear, IdeDefinition, OperationalControl, SignificantEnergyUse
from app.models.measurement import AlertEvent, MeasurementAuditLog, MonthlyMeasurement, MonthlyMeasurementVariable, User
from app.schemas.energy_v2 import (
    AlertEventReadV2,
    BaselineModelBaseV2,
    BaselineModelReadV2,
    BaselineModelUpdateV2,
    BaselineVariableCreateV2,
    BaselineVariableReadV2,
    BaselineVariableUpdateV2,
    DataCollectionPlanItem,
    EnergyUseBaseYearCreate,
    EnergyUseBaseYearRead,
    IdeDefinitionCreateV2,
    IdeDefinitionReadV2,
    IdeDefinitionUpdateV2,
    MonthlyMeasurementCreateV2,
    MonthlyMeasurementReadV2,
    MonthlyMeasurementUpdateV2,
    OperationalControlCreate,
    OperationalControlRead,
    OperationalControlUpdate,
    ParetoItem,
    SignificantEnergyUseCreate,
    SignificantEnergyUseRead,
    SignificantEnergyUseUpdate,
    TrackingMonthlyRow,
    TrackingSummary,
)
from app.services.energy_alert_service import generate_alerts_for_measurement
from app.services.calculations import calculate_difference, calculate_expected_consumption, calculate_ide_value, calculate_percentage_difference, classify_compliance


def _audit(db: Session, measurement: MonthlyMeasurement, action: str, user_id: int | None, field_name: str | None, old_value: str | None, new_value: str | None, comment: str | None = None) -> MeasurementAuditLog:
    audit = MeasurementAuditLog(
        monthly_measurement_id=measurement.id,
        user_id=user_id,
        action=action,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        comment=comment,
    )
    db.add(audit)
    return audit


def _serialize(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _required_variable_codes(baseline_variables: Iterable[BaselineVariable]) -> list[str]:
    return [item.variable_code for item in baseline_variables if item.required]


def _variable_map_for_measurement(
    db: Session,
    baseline_model_id: int,
    items: list[dict | object],
) -> tuple[dict[str, float], list[BaselineVariable]]:
    baseline_variables = (
        db.query(BaselineVariable)
        .filter(BaselineVariable.baseline_model_id == baseline_model_id, BaselineVariable.active.is_(True))
        .order_by(BaselineVariable.display_order.asc(), BaselineVariable.id.asc())
        .all()
    )
    by_id = {item.id: item for item in baseline_variables}
    variable_map: dict[str, float] = {}
    for raw_item in items:
        item_dict = raw_item if isinstance(raw_item, dict) else raw_item.model_dump()
        baseline_variable_id = item_dict["baseline_variable_id"]
        variable_code = item_dict["variable_code"]
        baseline_variable = by_id.get(baseline_variable_id)
        if baseline_variable is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"La variable {variable_code} no pertenece a la línea base seleccionada")
        if baseline_variable.variable_code != variable_code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El código {variable_code} no coincide con la definición de la línea base")
        variable_map[variable_code] = float(item_dict["value"])
    return variable_map, baseline_variables


def _compute_expected(baseline: BaselineModel, variable_map: dict[str, float]) -> float | None:
    coefficients = baseline.coefficients or {}
    missing = [code for code in coefficients if code not in variable_map]
    if missing:
        return None
    return round(float(baseline.intercept or 0.0) + sum(float(coeff) * float(variable_map[code]) for code, coeff in coefficients.items()), 4)


def _find_denominator_value(ide: IdeDefinition, variable_map: dict[str, float]) -> float | None:
    if not ide.denominator:
        return None
    return variable_map.get(ide.denominator)


def _compute_measurement_metrics(
    baseline: BaselineModel,
    ide: IdeDefinition,
    variable_map: dict[str, float],
    real_consumption: float,
) -> tuple[float | None, float | None, float | None, float | None, float | None, str]:
    expected = _compute_expected(baseline, variable_map)
    denominator_value = _find_denominator_value(ide, variable_map)
    ide_real = calculate_ide_value(real_consumption, denominator_value)
    ide_expected = calculate_ide_value(expected, denominator_value) if expected is not None else None
    difference = calculate_difference(real_consumption, expected)
    percentage_difference = calculate_percentage_difference(difference, expected)
    compliance_status = classify_compliance(
        percentage_difference,
        expected is not None and real_consumption > 0 and bool(variable_map),
        real_consumption,
        expected,
    )
    return expected, ide_real, ide_expected, difference, percentage_difference, compliance_status


def _create_measurement_variables(db: Session, measurement: MonthlyMeasurement, baseline_variables: list[BaselineVariable], variable_map: dict[str, float]) -> None:
    for baseline_variable in baseline_variables:
        if baseline_variable.variable_code not in variable_map:
            continue
        db.add(
            MonthlyMeasurementVariable(
                monthly_measurement_id=measurement.id,
                baseline_variable_id=baseline_variable.id,
                variable_name=baseline_variable.variable_name,
                variable_code=baseline_variable.variable_code,
                value=variable_map[baseline_variable.variable_code],
                unit=baseline_variable.unit,
            )
        )


def _measurement_variable_payload(measurement: MonthlyMeasurement) -> list[dict[str, object]]:
    return [
        {
            "baseline_variable_id": item.baseline_variable_id,
            "variable_code": item.variable_code or item.variable_name,
            "value": item.value,
        }
        for item in measurement.variables
    ]


def _attach_alerts(
    db: Session,
    measurement: MonthlyMeasurement,
    *,
    baseline_variables: list[BaselineVariable],
    variable_map: dict[str, float],
    percentage_difference: float | None,
    ide_definition: IdeDefinition,
) -> None:
    alerts = generate_alerts_for_measurement(
        measurement,
        baseline_variables=baseline_variables,
        variable_map=variable_map,
        percentage_difference=percentage_difference,
        ide_definition=ide_definition,
    )
    for alert in alerts:
        db.add(
            AlertEvent(
                energy_system_id=measurement.energy_system_id,
                monthly_measurement_id=measurement.id,
                alert_rule_id=None,
                severity=alert.severity,
                message=alert.message,
                value_detected=alert.value_detected,
                threshold_value=alert.threshold_value,
                status="open",
            )
        )


def create_energy_use_base_year(db: Session, system_id: int, payload: EnergyUseBaseYearCreate) -> EnergyUseBaseYear:
    record = EnergyUseBaseYear(energy_system_id=system_id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def create_significant_energy_use(db: Session, system_id: int, payload: SignificantEnergyUseCreate) -> SignificantEnergyUse:
    record = SignificantEnergyUse(energy_system_id=system_id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_significant_energy_use(db: Session, use_id: int, payload: SignificantEnergyUseUpdate) -> SignificantEnergyUse:
    record = db.get(SignificantEnergyUse, use_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="USE no encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


def create_baseline_model(db: Session, system_id: int, payload: BaselineModelBaseV2) -> BaselineModel:
    record = BaselineModel(energy_system_id=system_id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_baseline_model(db: Session, baseline_id: int, payload: BaselineModelUpdateV2) -> BaselineModel:
    record = db.get(BaselineModel, baseline_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Línea base no encontrada")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


def create_ide_definition(db: Session, system_id: int, payload: IdeDefinitionCreateV2) -> IdeDefinition:
    record = IdeDefinition(energy_system_id=system_id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_ide_definition(db: Session, ide_id: int, payload: IdeDefinitionUpdateV2) -> IdeDefinition:
    record = db.get(IdeDefinition, ide_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IDE no encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


def create_operational_control(db: Session, system_id: int, payload: OperationalControlCreate) -> OperationalControl:
    record = OperationalControl(energy_system_id=system_id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_operational_control(db: Session, control_id: int, payload: OperationalControlUpdate) -> OperationalControl:
    record = db.get(OperationalControl, control_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control operacional no encontrado")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


def create_monthly_measurement(
    db: Session,
    *,
    system_id: int,
    payload: MonthlyMeasurementCreateV2,
    user: User | None,
) -> MonthlyMeasurement:
    if not payload.baseline_model_id or not payload.significant_energy_use_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La medición mensual requiere USE y línea base")

    baseline = db.get(BaselineModel, payload.baseline_model_id)
    ide = db.get(IdeDefinition, payload.ide_id)
    significant_use = db.get(SignificantEnergyUse, payload.significant_energy_use_id)
    if not baseline or not ide or not significant_use:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contexto energético no encontrado")
    if baseline.energy_system_id != system_id or ide.energy_system_id != system_id or significant_use.energy_system_id != system_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El contexto no pertenece al sistema seleccionado")
    if baseline.significant_energy_use_id and baseline.significant_energy_use_id != significant_use.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La línea base no corresponde al USE seleccionado")
    if ide.baseline_model_id != baseline.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El IDE no corresponde a la línea base")

    variable_map, baseline_variables = _variable_map_for_measurement(db, baseline.id, payload.variables)
    expected, ide_real, ide_expected, difference, percentage_difference, compliance_status = _compute_measurement_metrics(
        baseline,
        ide,
        variable_map,
        payload.real_consumption,
    )
    if any(item.required and item.variable_code not in variable_map for item in baseline_variables):
        compliance_status = "incomplete"
        expected = None
        ide_real = None
        ide_expected = None
        difference = None
        percentage_difference = None

    measurement = MonthlyMeasurement(
        energy_system_id=system_id,
        significant_energy_use_id=significant_use.id,
        area_id=payload.area_id,
        energy_use_id=payload.energy_use_id,
        baseline_model_id=baseline.id,
        ide_id=ide.id,
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
    _create_measurement_variables(db, measurement, baseline_variables, variable_map)
    _audit(db, measurement, "created", user.id if user else None, None, None, None, "Creación de seguimiento mensual")
    _attach_alerts(db, measurement, baseline_variables=baseline_variables, variable_map=variable_map, percentage_difference=percentage_difference, ide_definition=ide)
    db.commit()
    db.refresh(measurement)
    return measurement


def update_monthly_measurement(db: Session, measurement_id: int, payload: MonthlyMeasurementUpdateV2, user: User | None) -> MonthlyMeasurement:
    measurement = db.get(MonthlyMeasurement, measurement_id)
    if not measurement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medición no encontrada")
    update_data = payload.model_dump(exclude_unset=True)
    if update_data.get("baseline_model_id") or update_data.get("ide_id") or update_data.get("significant_energy_use_id"):
        baseline = db.get(BaselineModel, update_data.get("baseline_model_id", measurement.baseline_model_id))
        ide = db.get(IdeDefinition, update_data.get("ide_id", measurement.ide_id))
        significant_use = db.get(SignificantEnergyUse, update_data.get("significant_energy_use_id", measurement.significant_energy_use_id))
        if not baseline or not ide or not significant_use:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contexto energético no encontrado")
        if baseline.significant_energy_use_id and baseline.significant_energy_use_id != significant_use.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La línea base no corresponde al USE seleccionado")
        if ide.baseline_model_id != baseline.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El IDE no corresponde a la línea base")
    baseline = db.get(BaselineModel, update_data.get("baseline_model_id", measurement.baseline_model_id))
    ide = db.get(IdeDefinition, update_data.get("ide_id", measurement.ide_id))
    should_recalculate = "variables" in update_data or "real_consumption" in update_data or "baseline_model_id" in update_data or "ide_id" in update_data

    for field in ["significant_energy_use_id", "area_id", "energy_use_id", "baseline_model_id", "ide_id", "year", "month", "real_consumption", "consumption_unit", "comments", "status"]:
        if field in update_data:
            old_value = getattr(measurement, field)
            new_value = update_data[field]
            if old_value != new_value:
                setattr(measurement, field, new_value)
                _audit(db, measurement, "updated", user.id if user else None, field, _serialize(old_value), _serialize(new_value), "Actualización de seguimiento mensual")

    if should_recalculate:
        variable_inputs = update_data["variables"] if update_data.get("variables") is not None else _measurement_variable_payload(measurement)
        variable_map, baseline_variables = _variable_map_for_measurement(db, measurement.baseline_model_id, variable_inputs)
        expected, ide_real, ide_expected, difference, percentage_difference, compliance_status = _compute_measurement_metrics(
            baseline,
            ide,
            variable_map,
            measurement.real_consumption,
        )
        measurement.expected_consumption = expected
        measurement.ide_real = ide_real
        measurement.ide_expected = ide_expected
        measurement.difference = difference
        measurement.percentage_difference = percentage_difference
        measurement.compliance_status = compliance_status
        db.query(MonthlyMeasurementVariable).filter(MonthlyMeasurementVariable.monthly_measurement_id == measurement.id).delete(synchronize_session=False)
        _create_measurement_variables(db, measurement, baseline_variables, variable_map)
        db.query(AlertEvent).filter(AlertEvent.monthly_measurement_id == measurement.id).delete(synchronize_session=False)
        _attach_alerts(db, measurement, baseline_variables=baseline_variables, variable_map=variable_map, percentage_difference=percentage_difference, ide_definition=ide)

    measurement.updated_by = user.id if user else None
    measurement.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(measurement)
    return measurement


def list_energy_use_base_year(db: Session, system_id: int) -> list[EnergyUseBaseYear]:
    return db.query(EnergyUseBaseYear).filter(EnergyUseBaseYear.energy_system_id == system_id).order_by(EnergyUseBaseYear.accumulated_percentage.desc().nullslast(), EnergyUseBaseYear.percentage.desc().nullslast()).all()


def pareto_energy_use_base_year(db: Session, system_id: int) -> list[ParetoItem]:
    items = list_energy_use_base_year(db, system_id)
    return [
        ParetoItem(
            label=item.installation_name,
            value=float(item.consumption_tcal or item.consumption_value),
            percentage=float(item.percentage or 0),
            accumulated_percentage=float(item.accumulated_percentage or 0),
        )
        for item in items
    ]


def list_significant_uses(db: Session, system_id: int) -> list[SignificantEnergyUse]:
    return db.query(SignificantEnergyUse).filter(SignificantEnergyUse.energy_system_id == system_id).order_by(SignificantEnergyUse.id.asc()).all()


def get_significant_use(db: Session, use_id: int) -> SignificantEnergyUse | None:
    return db.get(SignificantEnergyUse, use_id)


def list_baselines(db: Session, system_id: int) -> list[BaselineModel]:
    return db.query(BaselineModel).filter(BaselineModel.energy_system_id == system_id).order_by(BaselineModel.id.asc()).all()


def get_baseline(db: Session, baseline_id: int) -> BaselineModel | None:
    return db.get(BaselineModel, baseline_id)


def list_ide_definitions(db: Session, system_id: int) -> list[IdeDefinition]:
    return db.query(IdeDefinition).filter(IdeDefinition.energy_system_id == system_id).order_by(IdeDefinition.id.asc()).all()


def get_ide(db: Session, ide_id: int) -> IdeDefinition | None:
    return db.get(IdeDefinition, ide_id)


def list_operational_controls(db: Session, system_id: int) -> list[OperationalControl]:
    return db.query(OperationalControl).filter(OperationalControl.energy_system_id == system_id).order_by(OperationalControl.id.asc()).all()


def list_data_collection_plan(db: Session, system_id: int) -> list[DataCollectionPlanItem]:
    plans: list[DataCollectionPlanItem] = []
    uses = list_significant_uses(db, system_id)
    for use in uses:
        baselines = db.query(BaselineModel).filter(BaselineModel.significant_energy_use_id == use.id).all()
        for baseline in baselines:
            for variable in baseline.variables:
                plans.append(
                    DataCollectionPlanItem(
                        variable_name=variable.variable_name,
                        variable_code=variable.variable_code,
                        use_name=use.name,
                        baseline_name=baseline.name,
                        what_is_measured=variable.measurement_reason,
                        why_it_is_measured=variable.measurement_reason,
                        collection_method=variable.collection_method,
                        storage_location=variable.storage_location,
                        responsible_area=variable.responsible_area,
                        responsible_person=variable.responsible_person,
                        frequency=variable.frequency,
                        missing_data_procedure=variable.missing_data_procedure,
                        min_value=variable.min_value,
                        max_value=variable.max_value,
                        active=variable.active,
                    )
                )
    return plans


def list_measurements(db: Session, system_id: int, baseline_id: int | None = None, use_id: int | None = None, year: int | None = None, month: int | None = None) -> list[MonthlyMeasurement]:
    query = db.query(MonthlyMeasurement).filter(
        MonthlyMeasurement.energy_system_id == system_id,
        MonthlyMeasurement.significant_energy_use_id.is_not(None),
    )
    if baseline_id is not None:
        query = query.filter(MonthlyMeasurement.baseline_model_id == baseline_id)
    if use_id is not None:
        query = query.filter(MonthlyMeasurement.significant_energy_use_id == use_id)
    if year is not None:
        query = query.filter(MonthlyMeasurement.year == year)
    if month is not None:
        query = query.filter(MonthlyMeasurement.month == month)
    return query.order_by(MonthlyMeasurement.year.asc(), MonthlyMeasurement.month.asc()).all()


def get_tracking_summary(db: Session, system_id: int) -> TrackingSummary:
    measurements = list_measurements(db, system_id)
    total = len(measurements)
    compliant = sum(1 for item in measurements if item.compliance_status == "compliant")
    warning = sum(1 for item in measurements if item.compliance_status == "warning")
    non_compliant = sum(1 for item in measurements if item.compliance_status == "non_compliant")
    incomplete = sum(1 for item in measurements if item.compliance_status == "incomplete")
    avg_diff = round(sum(abs(float(item.percentage_difference or 0)) for item in measurements) / total, 2) if total else 0.0
    open_alerts = db.query(AlertEvent).filter(AlertEvent.energy_system_id == system_id, AlertEvent.status == "open").count()
    return TrackingSummary(
        total_measurements=total,
        compliant=compliant,
        warning=warning,
        non_compliant=non_compliant,
        incomplete=incomplete,
        average_percentage_difference=avg_diff,
        open_alerts=int(open_alerts),
    )


def get_baseline_tracking(db: Session, baseline_id: int) -> list[TrackingMonthlyRow]:
    measurements = db.query(MonthlyMeasurement).filter(MonthlyMeasurement.baseline_model_id == baseline_id).order_by(MonthlyMeasurement.year.asc(), MonthlyMeasurement.month.asc()).all()
    return [
        TrackingMonthlyRow(
            id=item.id,
            year=item.year,
            month=item.month,
            real_consumption=item.real_consumption,
            expected_consumption=item.expected_consumption,
            ide_real=item.ide_real,
            ide_expected=item.ide_expected,
            difference=item.difference,
            percentage_difference=item.percentage_difference,
            compliance_status=item.compliance_status,
            status=item.status,
            comments=item.comments,
        )
        for item in measurements
    ]


def get_tracking_for_use(db: Session, use_id: int) -> list[TrackingMonthlyRow]:
    measurements = db.query(MonthlyMeasurement).filter(MonthlyMeasurement.significant_energy_use_id == use_id).order_by(MonthlyMeasurement.year.asc(), MonthlyMeasurement.month.asc()).all()
    return [
        TrackingMonthlyRow(
            id=item.id,
            year=item.year,
            month=item.month,
            real_consumption=item.real_consumption,
            expected_consumption=item.expected_consumption,
            ide_real=item.ide_real,
            ide_expected=item.ide_expected,
            difference=item.difference,
            percentage_difference=item.percentage_difference,
            compliance_status=item.compliance_status,
            status=item.status,
            comments=item.comments,
        )
        for item in measurements
    ]


def get_system_tracking(db: Session, system_id: int) -> list[TrackingMonthlyRow]:
    return [
        TrackingMonthlyRow(
            id=item.id,
            year=item.year,
            month=item.month,
            real_consumption=item.real_consumption,
            expected_consumption=item.expected_consumption,
            ide_real=item.ide_real,
            ide_expected=item.ide_expected,
            difference=item.difference,
            percentage_difference=item.percentage_difference,
            compliance_status=item.compliance_status,
            status=item.status,
            comments=item.comments,
        )
        for item in list_measurements(db, system_id)
    ]


def list_alerts(db: Session, system_id: int) -> list[AlertEvent]:
    return db.query(AlertEvent).filter(AlertEvent.energy_system_id == system_id).order_by(AlertEvent.created_at.desc()).all()


def list_measurement_alerts(db: Session, measurement_id: int) -> list[AlertEvent]:
    return db.query(AlertEvent).filter(AlertEvent.monthly_measurement_id == measurement_id).order_by(AlertEvent.created_at.desc()).all()


def get_measurement(db: Session, measurement_id: int) -> MonthlyMeasurement | None:
    return db.get(MonthlyMeasurement, measurement_id)


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


def get_measurement_audit_log(db: Session, measurement_id: int) -> list[MeasurementAuditLog]:
    return (
        db.query(MeasurementAuditLog)
        .filter(MeasurementAuditLog.monthly_measurement_id == measurement_id)
        .order_by(MeasurementAuditLog.created_at.desc())
        .all()
    )
