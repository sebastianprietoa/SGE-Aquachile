from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.energy import BaselineModel, BaselineVariable, EnergyArea, EnergySystem, EnergyUse, EnergyUseBaseYear, IdeDefinition, OperationalControl, SignificantEnergyUse
from app.models.measurement import AlertEvent, MonthlyMeasurement, MonthlyMeasurementVariable
from app.services.calculations import calculate_difference, calculate_expected_consumption, calculate_ide_value, calculate_percentage_difference, classify_compliance


def _get_or_create_system(db: Session, code: str, name: str, company: str, description: str) -> EnergySystem:
    record = db.query(EnergySystem).filter(EnergySystem.code == code).one_or_none()
    if record:
        return record
    record = EnergySystem(code=code, name=name, company=company, description=description, active=True)
    db.add(record)
    db.flush()
    return record


def _get_or_create_area(db: Session, system: EnergySystem, name: str, area_type: str, description: str) -> EnergyArea:
    record = (
        db.query(EnergyArea)
        .filter(EnergyArea.energy_system_id == system.id, EnergyArea.name == name)
        .one_or_none()
    )
    if record:
        return record
    record = EnergyArea(energy_system_id=system.id, name=name, type=area_type, description=description, active=True)
    db.add(record)
    db.flush()
    return record


def _get_or_create_energy_use(db: Session, system: EnergySystem, area: EnergyArea, name: str, source: str, description: str, significant: bool = True) -> EnergyUse:
    record = (
        db.query(EnergyUse)
        .filter(EnergyUse.energy_system_id == system.id, EnergyUse.area_id == area.id, EnergyUse.name == name)
        .one_or_none()
    )
    if record:
        return record
    record = EnergyUse(
        energy_system_id=system.id,
        area_id=area.id,
        name=name,
        energy_source=source,
        description=description,
        is_significant=significant,
        active=True,
    )
    db.add(record)
    db.flush()
    return record


def _get_or_create_base_year(
    db: Session,
    system: EnergySystem,
    *,
    base_year: int,
    area: EnergyArea | None,
    area_name: str,
    installation_name: str,
    energy_source: str,
    use_category: str,
    consumption_value: float,
    consumption_unit: str,
    consumption_tcal: float,
    percentage: float,
    accumulated_percentage: float,
    source: str,
    candidate: bool,
    significant: bool,
    notes: str,
) -> EnergyUseBaseYear:
    record = (
        db.query(EnergyUseBaseYear)
        .filter(EnergyUseBaseYear.energy_system_id == system.id, EnergyUseBaseYear.base_year == base_year, EnergyUseBaseYear.installation_name == installation_name)
        .one_or_none()
    )
    if record:
        return record
    record = EnergyUseBaseYear(
        energy_system_id=system.id,
        base_year=base_year,
        area_id=area.id if area else None,
        area_name=area_name,
        installation_name=installation_name,
        energy_source=energy_source,
        use_category=use_category,
        consumption_value=consumption_value,
        consumption_unit=consumption_unit,
        consumption_tcal=consumption_tcal,
        percentage=percentage,
        accumulated_percentage=accumulated_percentage,
        source=source,
        is_candidate_use=candidate,
        is_significant_use=significant,
        notes=notes,
        active=True,
    )
    db.add(record)
    db.flush()
    return record


def _get_or_create_significant_use(
    db: Session,
    system: EnergySystem,
    base_year: EnergyUseBaseYear,
    *,
    area: EnergyArea,
    name: str,
    energy_source: str,
    consumption_value: float,
    consumption_unit: str,
    selection_criteria: str,
    current_energy_performance: float,
    current_energy_performance_unit: str,
    relevant_personnel: str,
    operational_control_required: str,
    improvement_opportunities: str,
) -> SignificantEnergyUse:
    record = (
        db.query(SignificantEnergyUse)
        .filter(SignificantEnergyUse.energy_system_id == system.id, SignificantEnergyUse.name == name)
        .one_or_none()
    )
    if record:
        return record
    record = SignificantEnergyUse(
        energy_system_id=system.id,
        energy_use_base_year_id=base_year.id,
        area_id=area.id,
        name=name,
        energy_source=energy_source,
        consumption_value=consumption_value,
        consumption_unit=consumption_unit,
        selection_criteria=selection_criteria,
        current_energy_performance=current_energy_performance,
        current_energy_performance_unit=current_energy_performance_unit,
        relevant_personnel=relevant_personnel,
        operational_control_required=operational_control_required,
        improvement_opportunities=improvement_opportunities,
        active=True,
    )
    db.add(record)
    db.flush()
    return record


def _get_or_create_baseline(
    db: Session,
    system: EnergySystem,
    significant_use: SignificantEnergyUse,
    energy_use: EnergyUse,
    area: EnergyArea,
    *,
    name: str,
    dependent_variable: str,
    dependent_variable_unit: str,
    formula_text: str,
    model_type: str,
    coefficients: dict[str, float],
    intercept: float,
    r_squared: float,
    adjusted_r_squared: float,
    reference_period_start: date,
    reference_period_end: date,
    static_factors: dict | None = None,
    routine_adjustments: dict | None = None,
    non_routine_adjustments: dict | None = None,
) -> BaselineModel:
    record = db.query(BaselineModel).filter(BaselineModel.energy_system_id == system.id, BaselineModel.name == name).one_or_none()
    if record:
        return record
    record = BaselineModel(
        energy_system_id=system.id,
        significant_energy_use_id=significant_use.id,
        area_id=area.id,
        energy_use_id=energy_use.id,
        name=name,
        dependent_variable=dependent_variable,
        dependent_variable_unit=dependent_variable_unit,
        formula_text=formula_text,
        model_type=model_type,
        coefficients=coefficients,
        intercept=intercept,
        r_squared=r_squared,
        adjusted_r_squared=adjusted_r_squared,
        reference_period_start=reference_period_start,
        reference_period_end=reference_period_end,
        static_factors=static_factors,
        routine_adjustments=routine_adjustments,
        non_routine_adjustments=non_routine_adjustments,
        valid_from=date(2025, 1, 1),
        valid_to=None,
        active=True,
    )
    db.add(record)
    db.flush()
    return record


def _get_or_create_variable(db: Session, baseline: BaselineModel, **kwargs) -> BaselineVariable:
    record = (
        db.query(BaselineVariable)
        .filter(BaselineVariable.baseline_model_id == baseline.id, BaselineVariable.variable_code == kwargs["variable_code"])
        .one_or_none()
    )
    if record:
        return record
    record = BaselineVariable(baseline_model_id=baseline.id, **kwargs)
    db.add(record)
    db.flush()
    return record


def _get_or_create_ide(
    db: Session,
    system: EnergySystem,
    significant_use: SignificantEnergyUse,
    baseline: BaselineModel,
    area: EnergyArea,
    energy_use: EnergyUse,
    *,
    ide_code: str,
    ide_name: str,
    formula_text: str,
    numerator: str,
    denominator: str,
    unit: str,
    purpose: str,
    frequency: str,
    expected_range_min: float,
    expected_range_max: float,
    warning_threshold_percentage: float,
    critical_threshold_percentage: float,
    protocol_description: str,
) -> IdeDefinition:
    record = db.query(IdeDefinition).filter(IdeDefinition.energy_system_id == system.id, IdeDefinition.ide_code == ide_code).one_or_none()
    if record:
        return record
    record = IdeDefinition(
        energy_system_id=system.id,
        significant_energy_use_id=significant_use.id,
        area_id=area.id,
        energy_use_id=energy_use.id,
        baseline_model_id=baseline.id,
        ide_code=ide_code,
        ide_name=ide_name,
        formula_text=formula_text,
        numerator=numerator,
        denominator=denominator,
        unit=unit,
        purpose=purpose,
        frequency=frequency,
        expected_range_min=expected_range_min,
        expected_range_max=expected_range_max,
        warning_threshold_percentage=warning_threshold_percentage,
        critical_threshold_percentage=critical_threshold_percentage,
        protocol_description=protocol_description,
        active=True,
    )
    db.add(record)
    db.flush()
    return record


def _get_or_create_control(
    db: Session,
    system: EnergySystem,
    use: SignificantEnergyUse,
    *,
    name: str,
    technical_criteria: str,
    administrative_criteria: str,
    maintenance_criteria: str,
    responsible_area: str,
    responsible_person: str,
    record_type: str,
    record_frequency: str,
    training_required: bool,
    last_training_date: date,
    effectiveness_evaluation_method: str,
) -> OperationalControl:
    record = db.query(OperationalControl).filter(OperationalControl.energy_system_id == system.id, OperationalControl.name == name).one_or_none()
    if record:
        return record
    record = OperationalControl(
        energy_system_id=system.id,
        significant_energy_use_id=use.id,
        name=name,
        technical_criteria=technical_criteria,
        administrative_criteria=administrative_criteria,
        maintenance_criteria=maintenance_criteria,
        responsible_area=responsible_area,
        responsible_person=responsible_person,
        record_type=record_type,
        record_frequency=record_frequency,
        training_required=training_required,
        last_training_date=last_training_date,
        effectiveness_evaluation_method=effectiveness_evaluation_method,
        active=True,
    )
    db.add(record)
    db.flush()
    return record


def _create_measurement(
    db: Session,
    *,
    system: EnergySystem,
    use: SignificantEnergyUse,
    baseline: BaselineModel,
    ide: IdeDefinition,
    area: EnergyArea,
    year: int,
    month: int,
    real_consumption: float,
    unit: str,
    variable_values: dict[str, float],
    comments: str,
    status: str = "approved",
) -> MonthlyMeasurement:
    record = (
        db.query(MonthlyMeasurement)
        .filter(
            MonthlyMeasurement.energy_system_id == system.id,
            MonthlyMeasurement.significant_energy_use_id == use.id,
            MonthlyMeasurement.baseline_model_id == baseline.id,
            MonthlyMeasurement.year == year,
            MonthlyMeasurement.month == month,
        )
        .one_or_none()
    )
    if record:
        return record
    expected = calculate_expected_consumption(baseline.intercept, baseline.coefficients, variable_values)
    ide_real = calculate_ide_value(real_consumption, variable_values.get(ide.denominator or ""))
    ide_expected = calculate_ide_value(expected, variable_values.get(ide.denominator or "")) if expected is not None else None
    difference = calculate_difference(real_consumption, expected)
    percentage_difference = calculate_percentage_difference(difference, expected)
    compliance_status = classify_compliance(percentage_difference, expected is not None, real_consumption, expected)
    record = MonthlyMeasurement(
        energy_system_id=system.id,
        significant_energy_use_id=use.id,
        area_id=area.id,
        energy_use_id=baseline.energy_use_id,
        baseline_model_id=baseline.id,
        ide_id=ide.id,
        year=year,
        month=month,
        real_consumption=real_consumption,
        consumption_unit=unit,
        expected_consumption=expected,
        ide_real=ide_real,
        ide_expected=ide_expected,
        difference=difference,
        percentage_difference=percentage_difference,
        compliance_status=compliance_status,
        comments=comments,
        status=status,
    )
    db.add(record)
    db.flush()
    for variable in baseline.variables:
        if variable.variable_code not in variable_values:
            continue
        db.add(
            MonthlyMeasurementVariable(
                monthly_measurement_id=record.id,
                baseline_variable_id=variable.id,
                variable_name=variable.variable_name,
                variable_code=variable.variable_code,
                value=variable_values[variable.variable_code],
                unit=variable.unit,
            )
        )
    if percentage_difference is not None and abs(percentage_difference) > 10:
        db.add(
            AlertEvent(
                energy_system_id=system.id,
                monthly_measurement_id=record.id,
                alert_rule_id=None,
                severity="high" if abs(percentage_difference) > 20 else "medium",
                message=f"Desviación mensual {percentage_difference:.1f}% en {baseline.name}",
                value_detected=percentage_difference,
                threshold_value=20 if abs(percentage_difference) > 20 else 10,
                status="open",
            )
        )
    if expected is None:
        db.add(
            AlertEvent(
                energy_system_id=system.id,
                monthly_measurement_id=record.id,
                alert_rule_id=None,
                severity="critical",
                message=f"Registro incompleto en {baseline.name}",
                value_detected=real_consumption,
                threshold_value=None,
                status="open",
            )
        )
    return record


def seed_database_v2(db: Session) -> None:
    aqua = _get_or_create_system(
        db,
        "AQUA",
        "Empresas AquaChile / AquaChile Magallanes",
        "AquaChile",
        "Sistema energético principal para seguimiento mensual",
    )
    elf = _get_or_create_system(
        db,
        "ELF",
        "ELF - Exportadora Los Fiordos",
        "Exportadora Los Fiordos",
        "Sistema energético ELF",
    )

    aqua_hollemberg = _get_or_create_area(db, aqua, "Piscicultura Hollemberg", "planta", "Instalación Hollemberg")
    aqua_xi = _get_or_create_area(db, aqua, "Centros XI Empresas AquaChile", "centro", "Centros XI")
    aqua_magallanes = _get_or_create_area(db, aqua, "Centros AquaChile Magallanes", "centro", "Centros Magallanes")
    aqua_support = _get_or_create_area(db, aqua, "Soporte operacional", "soporte", "Soporte operacional y servicios auxiliares")
    elf_area = _get_or_create_area(db, elf, "Planta ELF", "planta", "Planta principal ELF")
    elf_support = _get_or_create_area(db, elf, "Soporte ELF", "soporte", "Soporte operacional ELF")

    # Energy use base year 2022
    _get_or_create_base_year(
        db,
        aqua,
        base_year=2022,
        area=aqua_hollemberg,
        area_name="Piscicultura Hollemberg",
        installation_name="Hollemberg",
        energy_source="GLP",
        use_category="Producción",
        consumption_value=26.52,
        consumption_unit="Tcal",
        consumption_tcal=26.52,
        percentage=49.7,
        accumulated_percentage=49.7,
        source="BD 2022",
        candidate=True,
        significant=True,
        notes="Principal consumo Hollemberg",
    )
    _get_or_create_base_year(
        db,
        aqua,
        base_year=2022,
        area=aqua_magallanes,
        area_name="Centros AquaChile Magallanes",
        installation_name="Centros Magallanes",
        energy_source="Electricidad",
        use_category="Operación",
        consumption_value=9.22,
        consumption_unit="Tcal",
        consumption_tcal=9.22,
        percentage=17.3,
        accumulated_percentage=66.9,
        source="BD 2022",
        candidate=True,
        significant=True,
        notes="Consumo significativo CEAM",
    )
    _get_or_create_base_year(
        db,
        aqua,
        base_year=2022,
        area=aqua_xi,
        area_name="Centros XI Empresas AquaChile",
        installation_name="Centros XI",
        energy_source="Diésel",
        use_category="Operación",
        consumption_value=8.06,
        consumption_unit="Tcal",
        consumption_tcal=8.06,
        percentage=15.1,
        accumulated_percentage=82.0,
        source="BD 2022",
        candidate=True,
        significant=True,
        notes="Consumo significativo CEEA",
    )
    _get_or_create_base_year(
        db,
        aqua,
        base_year=2022,
        area=aqua_support,
        area_name="Otros centros",
        installation_name="Otros centros",
        energy_source="Electricidad",
        use_category="Soporte",
        consumption_value=4.72,
        consumption_unit="Tcal",
        consumption_tcal=4.72,
        percentage=8.8,
        accumulated_percentage=90.8,
        source="BD 2022",
        candidate=False,
        significant=False,
        notes="Apoyo operacional",
    )
    _get_or_create_base_year(
        db,
        aqua,
        base_year=2022,
        area=aqua_support,
        area_name="Soporte operacional",
        installation_name="Soporte operacional",
        energy_source="Electricidad",
        use_category="Soporte",
        consumption_value=2.34,
        consumption_unit="Tcal",
        consumption_tcal=2.34,
        percentage=4.4,
        accumulated_percentage=95.2,
        source="BD 2022",
        candidate=False,
        significant=False,
        notes="Base de referencia complementaria",
    )
    elf_base_year = _get_or_create_base_year(
        db,
        elf,
        base_year=2022,
        area=elf_area,
        area_name="Planta ELF",
        installation_name="ELF Planta",
        energy_source="Diésel",
        use_category="Producción",
        consumption_value=11.6,
        consumption_unit="Tcal",
        consumption_tcal=11.6,
        percentage=84.2,
        accumulated_percentage=84.2,
        source="BD 2022",
        candidate=True,
        significant=True,
        notes="Consumo principal ELF",
    )
    _get_or_create_base_year(
        db,
        elf,
        base_year=2022,
        area=elf_support,
        area_name="Soporte ELF",
        installation_name="ELF Soporte",
        energy_source="Electricidad",
        use_category="Soporte",
        consumption_value=2.2,
        consumption_unit="Tcal",
        consumption_tcal=2.2,
        percentage=15.8,
        accumulated_percentage=100.0,
        source="BD 2022",
        candidate=False,
        significant=False,
        notes="Consumo de soporte",
    )

    # Significant uses
    base_year_map = {
        "Hollemberg": db.query(EnergyUseBaseYear).filter(EnergyUseBaseYear.energy_system_id == aqua.id, EnergyUseBaseYear.installation_name == "Hollemberg").one(),
        "Centros Magallanes": db.query(EnergyUseBaseYear).filter(EnergyUseBaseYear.energy_system_id == aqua.id, EnergyUseBaseYear.installation_name == "Centros Magallanes").one(),
        "Centros XI": db.query(EnergyUseBaseYear).filter(EnergyUseBaseYear.energy_system_id == aqua.id, EnergyUseBaseYear.installation_name == "Centros XI").one(),
    }
    use_caldera_glp = _get_or_create_significant_use(
        db,
        aqua,
        base_year_map["Hollemberg"],
        area=aqua_hollemberg,
        name="Piscicultura Hollemberg - Caldera GLP",
        energy_source="GLP",
        consumption_value=822_938,
        consumption_unit="L",
        selection_criteria="Mayor impacto en suministro térmico",
        current_energy_performance=1.8,
        current_energy_performance_unit="L/°C",
        relevant_personnel="Jefatura de planta, mantención, operaciones",
        operational_control_required="Control de temperatura y consumo específico",
        improvement_opportunities="Optimización de setpoints y aislamiento",
    )
    use_gen_glp = _get_or_create_significant_use(
        db,
        aqua,
        base_year_map["Hollemberg"],
        area=aqua_hollemberg,
        name="Piscicultura Hollemberg - Generador GLP",
        energy_source="GLP",
        consumption_value=1_313_743,
        consumption_unit="L",
        selection_criteria="Generación crítica para continuidad",
        current_energy_performance=1.1,
        current_energy_performance_unit="L/kWh",
        relevant_personnel="Operaciones, mantención, supervisión",
        operational_control_required="Arranque, carga y despacho",
        improvement_opportunities="Ajuste de carga base y mantenimiento preventivo",
    )
    use_gen_diesel = _get_or_create_significant_use(
        db,
        aqua,
        base_year_map["Hollemberg"],
        area=aqua_hollemberg,
        name="Piscicultura Hollemberg - Generador Diésel",
        energy_source="Diésel",
        consumption_value=1_208_800,
        consumption_unit="L",
        selection_criteria="Respaldo energético",
        current_energy_performance=1.3,
        current_energy_performance_unit="L/kWh",
        relevant_personnel="Operaciones y mantención",
        operational_control_required="Pruebas y seguimiento de carga",
        improvement_opportunities="Reducción de horas de marcha en vacío",
    )
    use_ceea_blower = _get_or_create_significant_use(
        db,
        aqua,
        base_year_map["Centros XI"],
        area=aqua_xi,
        name="Centros XI Empresas AquaChile - Blower electricidad",
        energy_source="Electricidad",
        consumption_value=3_843_382,
        consumption_unit="kWh",
        selection_criteria="Mayor potencial de ahorro",
        current_energy_performance=46.0,
        current_energy_performance_unit="L/h",
        relevant_personnel="Operaciones, mantenimiento, automatización",
        operational_control_required="Horas de blower, consigna y parada",
        improvement_opportunities="Control por demanda y mantención de difusores",
    )
    use_ceea_diesel = _get_or_create_significant_use(
        db,
        aqua,
        base_year_map["Centros XI"],
        area=aqua_xi,
        name="Centros XI Empresas AquaChile - Generador Diésel",
        energy_source="Diésel",
        consumption_value=868_372,
        consumption_unit="L",
        selection_criteria="Respaldo y criticidad operacional",
        current_energy_performance=54.0,
        current_energy_performance_unit="L/h",
        relevant_personnel="Operaciones, mantenimiento",
        operational_control_required="Control operacional y pruebas",
        improvement_opportunities="Optimización de pruebas y chequeos",
    )
    use_ceam_diesel = _get_or_create_significant_use(
        db,
        aqua,
        base_year_map["Centros Magallanes"],
        area=aqua_magallanes,
        name="Centros AquaChile Magallanes - Generador Diésel",
        energy_source="Diésel",
        consumption_value=1_006_578,
        consumption_unit="L",
        selection_criteria="Respaldo regional",
        current_energy_performance=48.0,
        current_energy_performance_unit="L/h",
        relevant_personnel="Operaciones y mantenimiento",
        operational_control_required="Pruebas y consumo de respaldo",
        improvement_opportunities="Reducción de horas en vacío",
    )
    use_ceam_blower = _get_or_create_significant_use(
        db,
        aqua,
        base_year_map["Centros Magallanes"],
        area=aqua_magallanes,
        name="Centros AquaChile Magallanes - Blower electricidad",
        energy_source="Electricidad",
        consumption_value=4_458_700,
        consumption_unit="kWh",
        selection_criteria="Uso significativo con potencial de optimización",
        current_energy_performance=52.0,
        current_energy_performance_unit="L/h",
        relevant_personnel="Operaciones, mantenimiento",
        operational_control_required="Horas blower y consumo específico",
        improvement_opportunities="Automatización y ajuste de caudal",
    )
    use_elf_diesel = _get_or_create_significant_use(
        db,
        elf,
        elf_base_year,
        area=elf_area,
        name="ELF - Generador Diésel",
        energy_source="Diésel",
        consumption_value=1_120_000,
        consumption_unit="L",
        selection_criteria="Principal carga operacional ELF",
        current_energy_performance=42.0,
        current_energy_performance_unit="L/h",
        relevant_personnel="Operaciones, mantención, supervisión",
        operational_control_required="Arranque, carga y despacho",
        improvement_opportunities="Optimización de carga y mantenimiento preventivo",
    )

    # Legacy energy uses linked to baselines
    legacy_ceea_diesel = _get_or_create_energy_use(db, aqua, aqua_xi, "Generador Diésel", "Diésel", "Generador eléctrico principal", True)
    legacy_ceam_blower = _get_or_create_energy_use(db, aqua, aqua_magallanes, "Blower", "Electricidad", "Blower de aireación", True)
    legacy_hollemberg_caldera = _get_or_create_energy_use(db, aqua, aqua_hollemberg, "Caldera GLP", "GLP", "Caldera Hollemberg", True)
    legacy_hollemberg_gen_glp = _get_or_create_energy_use(db, aqua, aqua_hollemberg, "Generador GLP", "GLP", "Generador GLP Hollemberg", True)
    legacy_hollemberg_gen_diesel = _get_or_create_energy_use(db, aqua, aqua_hollemberg, "Generador Diésel", "Diésel", "Generador diésel Hollemberg", True)
    legacy_ceam_diesel = _get_or_create_energy_use(db, aqua, aqua_magallanes, "Generador Diésel", "Diésel", "Generador diésel Magallanes", True)
    legacy_elf_diesel = _get_or_create_energy_use(db, elf, elf_area, "Generador Diésel", "Diésel", "Generador principal ELF", True)

    # Baselines
    baseline_ceea = _get_or_create_baseline(
        db,
        aqua,
        use_ceea_diesel,
        legacy_ceea_diesel,
        aqua_xi,
        name="LBEn CEEA Centros XI",
        dependent_variable="consumo_diesel_real",
        dependent_variable_unit="L",
        formula_text="intercept + 12.5 * horas_blower + 0.8 * kwh_blower",
        model_type="regresión lineal múltiple",
        coefficients={"horas_blower": 12.5, "kwh_blower": 0.8},
        intercept=1400.0,
        r_squared=0.86,
        adjusted_r_squared=0.84,
        reference_period_start=date(2022, 1, 1),
        reference_period_end=date(2024, 12, 31),
        static_factors={"instalación": "Centros XI"},
        routine_adjustments={"mantenimiento": "mensual"},
        non_routine_adjustments={"eventos": "paradas por clima"},
    )
    baseline_ceam = _get_or_create_baseline(
        db,
        aqua,
        use_ceam_blower,
        legacy_ceam_blower,
        aqua_magallanes,
        name="LBEn CEAM Magallanes",
        dependent_variable="consumo_diesel_real",
        dependent_variable_unit="L",
        formula_text="intercept + 10.2 * horas_blower + 0.55 * kwh_blower",
        model_type="regresión lineal múltiple",
        coefficients={"horas_blower": 10.2, "kwh_blower": 0.55},
        intercept=980.0,
        r_squared=0.79,
        adjusted_r_squared=0.77,
        reference_period_start=date(2022, 1, 1),
        reference_period_end=date(2024, 12, 31),
        static_factors={"instalación": "Magallanes"},
        routine_adjustments={"mantenimiento": "mensual"},
        non_routine_adjustments={"eventos": "clima extremo"},
    )
    baseline_caldera = _get_or_create_baseline(
        db,
        aqua,
        use_caldera_glp,
        legacy_hollemberg_caldera,
        aqua_hollemberg,
        name="LBEn Hollemberg Caldera GLP",
        dependent_variable="consumo_glp_real",
        dependent_variable_unit="L",
        formula_text="intercept + -150.2 * temperatura_ambiente + 48.0 * dummy_mes + 3.8 * delta_temperatura",
        model_type="regresión lineal múltiple",
        coefficients={"temperatura_ambiente": -150.2, "dummy_mes": 48.0, "delta_temperatura": 3.8},
        intercept=2800.0,
        r_squared=0.82,
        adjusted_r_squared=0.80,
        reference_period_start=date(2022, 1, 1),
        reference_period_end=date(2024, 12, 31),
        static_factors={"equipamiento": "caldera GLP"},
        routine_adjustments={"mantenimiento": "mensual"},
        non_routine_adjustments={"eventos": "cambios estacionales"},
    )
    baseline_gen_glp = _get_or_create_baseline(
        db,
        aqua,
        use_gen_glp,
        legacy_hollemberg_gen_glp,
        aqua_hollemberg,
        name="LBEn Hollemberg Generador GLP",
        dependent_variable="consumo_glp_real",
        dependent_variable_unit="L",
        formula_text="intercept + 0.85 * kwh_generados",
        model_type="regresión lineal simple",
        coefficients={"kwh_generados": 0.85},
        intercept=120.0,
        r_squared=0.88,
        adjusted_r_squared=0.87,
        reference_period_start=date(2022, 1, 1),
        reference_period_end=date(2024, 12, 31),
    )
    baseline_gen_diesel = _get_or_create_baseline(
        db,
        aqua,
        use_gen_diesel,
        legacy_hollemberg_gen_diesel,
        aqua_hollemberg,
        name="LBEn Hollemberg Generador Diésel",
        dependent_variable="consumo_diesel_real",
        dependent_variable_unit="L",
        formula_text="intercept + 0.92 * kwh_generados",
        model_type="regresión lineal simple",
        coefficients={"kwh_generados": 0.92},
        intercept=160.0,
        r_squared=0.84,
        adjusted_r_squared=0.83,
        reference_period_start=date(2022, 1, 1),
        reference_period_end=date(2024, 12, 31),
    )
    baseline_elf_diesel = _get_or_create_baseline(
        db,
        elf,
        use_elf_diesel,
        legacy_elf_diesel,
        elf_area,
        name="LBEn ELF Generador Diésel",
        dependent_variable="consumo_diesel_real",
        dependent_variable_unit="L",
        formula_text="intercept + 0.88 * kwh_generados",
        model_type="regresión lineal simple",
        coefficients={"kwh_generados": 0.88},
        intercept=110.0,
        r_squared=0.81,
        adjusted_r_squared=0.80,
        reference_period_start=date(2022, 1, 1),
        reference_period_end=date(2024, 12, 31),
        static_factors={"instalación": "ELF Planta"},
        routine_adjustments={"mantenimiento": "mensual"},
        non_routine_adjustments={"eventos": "paradas programadas"},
    )

    # Baseline variables
    for baseline, items in [
        (
            baseline_ceea,
            [
                dict(variable_name="Horas blower", variable_code="horas_blower", variable_type="operating_hours", unit="h", required=True, min_value=0, max_value=3000, description="Horas blower mensuales", measurement_reason="Principal variable operacional", collection_method="SCADA / planilla", storage_location="Base de datos energética", responsible_area="Operaciones", responsible_person="Jefe de planta", frequency="Mensual", missing_data_procedure="Revisión manual y estimación documentada", display_order=1, active=True),
                dict(variable_name="kWh blower", variable_code="kwh_blower", variable_type="generated_energy", unit="kWh", required=False, min_value=0, max_value=200000, description="Consumo asociado al blower", measurement_reason="Apoyo al cálculo", collection_method="Medidor eléctrico", storage_location="Base de datos energética", responsible_area="Operaciones", responsible_person="Encargado eléctrico", frequency="Mensual", missing_data_procedure="Tomar último dato válido", display_order=2, active=True),
            ],
        ),
        (
            baseline_ceam,
            [
                dict(variable_name="Horas blower", variable_code="horas_blower", variable_type="operating_hours", unit="h", required=True, min_value=0, max_value=3000, description="Horas blower", measurement_reason="Control operativo", collection_method="SCADA", storage_location="Base energética", responsible_area="Operaciones", responsible_person="Supervisor", frequency="Mensual", missing_data_procedure="Estimación temporal aprobada", display_order=1, active=True),
                dict(variable_name="kWh blower", variable_code="kwh_blower", variable_type="generated_energy", unit="kWh", required=True, min_value=0, max_value=200000, description="Energía blower", measurement_reason="Control energético", collection_method="Medidor", storage_location="Base energética", responsible_area="Operaciones", responsible_person="Supervisor", frequency="Mensual", missing_data_procedure="Revisión de telemetría", display_order=2, active=True),
            ],
        ),
        (
            baseline_caldera,
            [
                dict(variable_name="Temperatura ambiente", variable_code="temperatura_ambiente", variable_type="ambient_temperature", unit="°C", required=True, min_value=-10, max_value=50, description="Temperatura promedio mensual", measurement_reason="Variable térmica pertinente", collection_method="Estación meteorológica", storage_location="Base energética", responsible_area="Medio ambiente", responsible_person="Técnico clima", frequency="Mensual", missing_data_procedure="Promedio validado del mes", display_order=1, active=True),
                dict(variable_name="Dummy mes", variable_code="dummy_mes", variable_type="other", unit="1/0", required=True, min_value=0, max_value=1, description="Variable estacional", measurement_reason="Captura estacionalidad", collection_method="Cálculo interno", storage_location="Base energética", responsible_area="Planificación", responsible_person="Analista", frequency="Mensual", missing_data_procedure="Usar clasificación del período", display_order=2, active=True),
                dict(variable_name="Delta temperatura", variable_code="delta_temperatura", variable_type="other", unit="°C", required=True, min_value=-20, max_value=20, description="Diferencia térmica", measurement_reason="Relación térmica", collection_method="Cálculo interno", storage_location="Base energética", responsible_area="Ingeniería", responsible_person="Ingeniero energía", frequency="Mensual", missing_data_procedure="Mantener delta del mes anterior", display_order=3, active=True),
            ],
        ),
        (
            baseline_gen_glp,
            [
                dict(variable_name="kWh generados", variable_code="kwh_generados", variable_type="generated_energy", unit="kWh", required=True, min_value=0, max_value=None, description="Energía generada", measurement_reason="Base del indicador", collection_method="Contador de energía", storage_location="Base energética", responsible_area="Operaciones", responsible_person="Supervisor", frequency="Mensual", missing_data_procedure="Reconciliar con producción", display_order=1, active=True),
            ],
        ),
        (
            baseline_gen_diesel,
            [
                dict(variable_name="kWh generados", variable_code="kwh_generados", variable_type="generated_energy", unit="kWh", required=True, min_value=0, max_value=None, description="Energía generada", measurement_reason="Base del indicador", collection_method="Contador de energía", storage_location="Base energética", responsible_area="Operaciones", responsible_person="Supervisor", frequency="Mensual", missing_data_procedure="Reconciliar con producción", display_order=1, active=True),
            ],
        ),
        (
            baseline_elf_diesel,
            [
                dict(variable_name="kWh generados", variable_code="kwh_generados", variable_type="generated_energy", unit="kWh", required=True, min_value=0, max_value=220000, description="Energía generada por el sistema ELF", measurement_reason="Base del indicador", collection_method="Contador de energía", storage_location="Base energética", responsible_area="Operaciones", responsible_person="Supervisor ELF", frequency="Mensual", missing_data_procedure="Reconciliar con operación", display_order=1, active=True),
            ],
        ),
    ]:
        for item in items:
            _get_or_create_variable(db, baseline, **item)

    # IDEs
    ide_ceea = _get_or_create_ide(
        db,
        aqua,
        use_ceea_blower,
        baseline_ceea,
        aqua_xi,
        legacy_ceea_diesel,
        ide_code="IDE-CEEA-01",
        ide_name="IDE 1 CEEA",
        formula_text="litros_diesel / horas_blower",
        numerator="consumo_diesel_real",
        denominator="horas_blower",
        unit="L/h",
        purpose="Monitorear eficiencia del uso significativo de blower",
        frequency="Mensual",
        expected_range_min=35,
        expected_range_max=60,
        warning_threshold_percentage=10,
        critical_threshold_percentage=20,
        protocol_description="Comparación mensual contra la LBEn CEEA",
    )
    ide_ceam = _get_or_create_ide(
        db,
        aqua,
        use_ceam_blower,
        baseline_ceam,
        aqua_magallanes,
        legacy_ceam_blower,
        ide_code="IDE-CEAM-01",
        ide_name="IDE 2 CEAM",
        formula_text="litros_diesel / horas_blower",
        numerator="consumo_diesel_real",
        denominator="horas_blower",
        unit="L/h",
        purpose="Seguimiento de desempeño de CEAM",
        frequency="Mensual",
        expected_range_min=30,
        expected_range_max=55,
        warning_threshold_percentage=10,
        critical_threshold_percentage=20,
        protocol_description="Seguimiento mensual conforme a Art. 21",
    )
    ide_caldera = _get_or_create_ide(
        db,
        aqua,
        use_caldera_glp,
        baseline_caldera,
        aqua_hollemberg,
        legacy_hollemberg_caldera,
        ide_code="IDE-HCAL-01",
        ide_name="IDE 3 Caldera",
        formula_text="litros_glp / delta_temperatura",
        numerator="consumo_glp_real",
        denominator="delta_temperatura",
        unit="L/°C",
        purpose="Medir sensibilidad térmica de la caldera",
        frequency="Mensual",
        expected_range_min=0,
        expected_range_max=200,
        warning_threshold_percentage=10,
        critical_threshold_percentage=20,
        protocol_description="Uso de variables térmicas pertinentes",
    )
    ide_gen_glp = _get_or_create_ide(
        db,
        aqua,
        use_gen_glp,
        baseline_gen_glp,
        aqua_hollemberg,
        legacy_hollemberg_gen_glp,
        ide_code="IDE-HGGLP-01",
        ide_name="IDE 4 PGenGLP",
        formula_text="litros_glp / kwh_generados",
        numerator="consumo_glp_real",
        denominator="kwh_generados",
        unit="L/kWh",
        purpose="Seguimiento de eficiencia de generación GLP",
        frequency="Mensual",
        expected_range_min=0.4,
        expected_range_max=2.0,
        warning_threshold_percentage=10,
        critical_threshold_percentage=20,
        protocol_description="Comparación mensual real vs LBEn",
    )
    ide_gen_diesel = _get_or_create_ide(
        db,
        aqua,
        use_gen_diesel,
        baseline_gen_diesel,
        aqua_hollemberg,
        legacy_hollemberg_gen_diesel,
        ide_code="IDE-HGDIE-01",
        ide_name="IDE 5 PGenPE",
        formula_text="litros_diesel / kwh_generados",
        numerator="consumo_diesel_real",
        denominator="kwh_generados",
        unit="L/kWh",
        purpose="Seguimiento de eficiencia de generación diésel",
        frequency="Mensual",
        expected_range_min=0.5,
        expected_range_max=2.0,
        warning_threshold_percentage=10,
        critical_threshold_percentage=20,
        protocol_description="Comparación mensual real vs LBEn",
    )
    ide_elf_diesel = _get_or_create_ide(
        db,
        elf,
        use_elf_diesel,
        baseline_elf_diesel,
        elf_area,
        legacy_elf_diesel,
        ide_code="IDE-ELF-01",
        ide_name="IDE ELF Generador Diésel",
        formula_text="litros_diesel / kwh_generados",
        numerator="consumo_diesel_real",
        denominator="kwh_generados",
        unit="L/kWh",
        purpose="Seguimiento del generador principal ELF",
        frequency="Mensual",
        expected_range_min=0.4,
        expected_range_max=2.0,
        warning_threshold_percentage=10,
        critical_threshold_percentage=20,
        protocol_description="Comparación mensual real vs LBEn ELF",
    )

    # Operational controls
    for use, controls in [
        (
            use_ceea_blower,
            [
                dict(name="Control blower CEEA", technical_criteria="Horas blower por debajo del objetivo", administrative_criteria="Autorización de arranques", maintenance_criteria="Mantención mensual", responsible_area="Operaciones", responsible_person="Jefe CEEA", record_type="bitácora", record_frequency="Mensual", training_required=True, last_training_date=date(2025, 1, 15), effectiveness_evaluation_method="Revisión de desviación"),
            ],
        ),
        (
            use_ceam_blower,
            [
                dict(name="Control blower CEAM", technical_criteria="Operación por demanda", administrative_criteria="Reporte de uso", maintenance_criteria="Limpieza preventiva", responsible_area="Operaciones", responsible_person="Jefe CEAM", record_type="checklist", record_frequency="Mensual", training_required=True, last_training_date=date(2025, 2, 10), effectiveness_evaluation_method="Verificación de cumplimiento"),
            ],
        ),
        (
            use_elf_diesel,
            [
                dict(name="Control generador ELF", technical_criteria="Horas de operación dentro de objetivos", administrative_criteria="Autorización de despacho", maintenance_criteria="Mantención preventiva mensual", responsible_area="Operaciones", responsible_person="Jefe ELF", record_type="bitácora", record_frequency="Mensual", training_required=True, last_training_date=date(2025, 3, 12), effectiveness_evaluation_method="Revisión de desviación"),
            ],
        ),
    ]:
        owning_system = aqua if use in (use_ceea_blower, use_ceam_blower) else elf
        for control in controls:
            _get_or_create_control(db, owning_system, use, **control)

    # Measurements for tracking
    for month in range(1, 13):
        _create_measurement(
            db,
            system=aqua,
            use=use_ceea_blower,
            baseline=baseline_ceea,
            ide=ide_ceea,
            area=aqua_xi,
            year=2025,
            month=month,
            real_consumption=41_040 + month * 1_250,
            unit="L",
            variable_values={"horas_blower": 900 + month * 35, "kwh_blower": 12_500 + month * 250},
            comments="Seguimiento mensual CEEA",
        )
        _create_measurement(
            db,
            system=aqua,
            use=use_ceam_blower,
            baseline=baseline_ceam,
            ide=ide_ceam,
            area=aqua_magallanes,
            year=2025,
            month=month,
            real_consumption=31_000 + month * 980,
            unit="L",
            variable_values={"horas_blower": 780 + month * 24, "kwh_blower": 11_000 + month * 180},
            comments="Seguimiento mensual CEAM",
        )
        _create_measurement(
            db,
            system=aqua,
            use=use_caldera_glp,
            baseline=baseline_caldera,
            ide=ide_caldera,
            area=aqua_hollemberg,
            year=2025,
            month=month,
            real_consumption=8_200 + month * 240,
            unit="L",
            variable_values={"temperatura_ambiente": -2 + month * 1.7, "dummy_mes": 1, "delta_temperatura": 5 + month * 0.3},
            comments="Seguimiento mensual caldera GLP",
        )
        _create_measurement(
            db,
            system=aqua,
            use=use_gen_glp,
            baseline=baseline_gen_glp,
            ide=ide_gen_glp,
            area=aqua_hollemberg,
            year=2025,
            month=month,
            real_consumption=12_000 + month * 360,
            unit="L",
            variable_values={"kwh_generados": 1_500 + month * 45},
            comments="Seguimiento mensual generador GLP",
        )
        _create_measurement(
            db,
            system=aqua,
            use=use_gen_diesel,
            baseline=baseline_gen_diesel,
            ide=ide_gen_diesel,
            area=aqua_hollemberg,
            year=2025,
            month=month,
            real_consumption=9_500 + month * 290,
            unit="L",
            variable_values={"kwh_generados": 1_200 + month * 38},
            comments="Seguimiento mensual generador diésel",
        )
        _create_measurement(
            db,
            system=elf,
            use=use_elf_diesel,
            baseline=baseline_elf_diesel,
            ide=ide_elf_diesel,
            area=elf_area,
            year=2025,
            month=month,
            real_consumption=7_900 + month * 210,
            unit="L",
            variable_values={"kwh_generados": 1_000 + month * 30},
            comments="Seguimiento mensual ELF",
        )

    db.commit()
