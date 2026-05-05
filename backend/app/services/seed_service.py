from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.energy import AlertRule, BaselineModel, BaselineVariable, EnergyArea, EnergySystem, EnergyUse, IdeDefinition
from app.models.measurement import AlertEvent, MonthlyMeasurement, MonthlyMeasurementVariable
from app.services.auth_service import seed_admin_user
from app.services.calculations import calculate_difference, calculate_expected_consumption, calculate_ide_value, calculate_percentage_difference, classify_compliance


def _create_measurement(db: Session, *, system: EnergySystem, area: EnergyArea, use: EnergyUse, baseline: BaselineModel, ide: IdeDefinition, year: int, month: int, real_consumption: float, consumption_unit: str, variable_values: dict[str, float], status_value: str = "approved") -> MonthlyMeasurement:
    variable_map = {item.variable_code: item for item in baseline.variables}
    expected = calculate_expected_consumption(baseline.intercept, baseline.coefficients, variable_values) or 0
    denominator = variable_values.get(ide.denominator or "")
    ide_real = calculate_ide_value(real_consumption, denominator)
    ide_expected = calculate_ide_value(expected, denominator)
    difference = calculate_difference(real_consumption, expected)
    percentage_difference = calculate_percentage_difference(difference, expected)
    compliance_status = classify_compliance(percentage_difference, True, real_consumption, expected)
    measurement = MonthlyMeasurement(
        energy_system_id=system.id,
        area_id=area.id,
        energy_use_id=use.id,
        baseline_model_id=baseline.id,
        ide_id=ide.id,
        year=year,
        month=month,
        real_consumption=real_consumption,
        consumption_unit=consumption_unit,
        expected_consumption=expected,
        ide_real=ide_real,
        ide_expected=ide_expected,
        difference=difference,
        percentage_difference=percentage_difference,
        compliance_status=compliance_status,
        comments="Registro de ejemplo",
        status=status_value,
    )
    db.add(measurement)
    db.flush()
    for code, value in variable_values.items():
        baseline_variable = variable_map[code]
        db.add(
            MonthlyMeasurementVariable(
                monthly_measurement_id=measurement.id,
                baseline_variable_id=baseline_variable.id,
                variable_name=baseline_variable.variable_name,
                value=value,
                unit=baseline_variable.unit,
            )
        )
    if percentage_difference is not None and abs(percentage_difference) > 10:
        db.add(
            AlertEvent(
                energy_system_id=system.id,
                monthly_measurement_id=measurement.id,
                alert_rule_id=None,
                severity="high" if abs(percentage_difference) > 20 else "medium",
                message="Alerta generada por desviación en dato seed",
                value_detected=percentage_difference,
                threshold_value=20 if abs(percentage_difference) > 20 else 10,
                status="open",
            )
        )
    return measurement


def seed_database(db: Session) -> None:
    if db.query(EnergySystem).count() > 0:
        return

    settings = get_settings()
    admin = seed_admin_user(db, settings.seed_admin_username, settings.seed_admin_password, settings.seed_admin_email)

    elf = EnergySystem(code="ELF", name="ELF - Exportadora Los Fiordos", company="Exportadora Los Fiordos", description="Sistema energético ELF", active=True)
    aqua = EnergySystem(code="AQUA", name="Empresas AquaChile / AquaChile Magallanes", company="AquaChile", description="Sistema energético AquaChile Magallanes", active=True)
    db.add_all([elf, aqua])
    db.flush()

    elf_areas = [
        EnergyArea(energy_system_id=elf.id, name="Planta de proceso", type="planta", description="Área de proceso principal", active=True),
        EnergyArea(energy_system_id=elf.id, name="Frío industrial", type="instalación", description="Sistema de refrigeración", active=True),
        EnergyArea(energy_system_id=aqua.id, name="Salmonicultura", type="planta", description="Área de operación acuícola", active=True),
        EnergyArea(energy_system_id=aqua.id, name="PTAS", type="instalación", description="Tratamiento de aguas", active=True),
    ]
    db.add_all(elf_areas)
    db.flush()

    elf_use_1 = EnergyUse(energy_system_id=elf.id, area_id=elf_areas[0].id, name="Proceso productivo", energy_source="Electricidad", description="Uso significativo del proceso", is_significant=True, active=True)
    elf_use_2 = EnergyUse(energy_system_id=elf.id, area_id=elf_areas[1].id, name="Refrigeración", energy_source="Electricidad", description="Compresores y chillers", is_significant=True, active=True)
    aqua_use_1 = EnergyUse(energy_system_id=aqua.id, area_id=elf_areas[2].id, name="Producción acuícola", energy_source="Electricidad", description="Proceso productivo acuícola", is_significant=True, active=True)
    aqua_use_2 = EnergyUse(energy_system_id=aqua.id, area_id=elf_areas[3].id, name="Bombeo y tratamiento", energy_source="Electricidad", description="Bombas y blowers", is_significant=True, active=True)
    db.add_all([elf_use_1, elf_use_2, aqua_use_1, aqua_use_2])
    db.flush()

    elf_baseline = BaselineModel(
        energy_system_id=elf.id,
        area_id=elf_areas[0].id,
        energy_use_id=elf_use_1.id,
        name="LBE ELF Proceso",
        dependent_variable="production_monthly",
        dependent_variable_unit="ton",
        formula_text="intercept + production_monthly * 0.42 + ambient_temperature * 1.1 + operating_hours * 2.8",
        model_type="linear",
        coefficients={"production_monthly": 0.42, "ambient_temperature": 1.1, "operating_hours": 2.8},
        intercept=120.0,
        r_squared=0.91,
        adjusted_r_squared=0.89,
        reference_period_start=date(2024, 1, 1),
        reference_period_end=date(2024, 12, 31),
        valid_from=date(2025, 1, 1),
        valid_to=None,
        active=True,
    )
    aqua_baseline = BaselineModel(
        energy_system_id=aqua.id,
        area_id=elf_areas[2].id,
        energy_use_id=aqua_use_1.id,
        name="LBE AquaChile Producción",
        dependent_variable="tons_processed",
        dependent_variable_unit="ton",
        formula_text="intercept + tons_processed * 0.31 + generated_energy * 0.08 + operating_hours * 1.9 + flow * 0.12",
        model_type="linear",
        coefficients={"tons_processed": 0.31, "generated_energy": 0.08, "operating_hours": 1.9, "flow": 0.12},
        intercept=95.0,
        r_squared=0.88,
        adjusted_r_squared=0.85,
        reference_period_start=date(2024, 1, 1),
        reference_period_end=date(2024, 12, 31),
        valid_from=date(2025, 1, 1),
        valid_to=None,
        active=True,
    )
    db.add_all([elf_baseline, aqua_baseline])
    db.flush()

    elf_variables = [
        BaselineVariable(baseline_model_id=elf_baseline.id, variable_name="Producción mensual", variable_code="production_monthly", variable_type="production", unit="ton", required=True, min_value=0, max_value=None, description="Producción mensual total", display_order=1, active=True),
        BaselineVariable(baseline_model_id=elf_baseline.id, variable_name="Temperatura ambiente", variable_code="ambient_temperature", variable_type="ambient_temperature", unit="°C", required=True, min_value=-10, max_value=50, description="Temperatura promedio mensual", display_order=2, active=True),
        BaselineVariable(baseline_model_id=elf_baseline.id, variable_name="Horas de operación", variable_code="operating_hours", variable_type="operating_hours", unit="h", required=True, min_value=0, max_value=744, description="Horas operativas del mes", display_order=3, active=True),
    ]
    aqua_variables = [
        BaselineVariable(baseline_model_id=aqua_baseline.id, variable_name="Toneladas procesadas", variable_code="tons_processed", variable_type="tons_processed", unit="ton", required=True, min_value=0, max_value=None, description="Toneladas procesadas", display_order=1, active=True),
        BaselineVariable(baseline_model_id=aqua_baseline.id, variable_name="Energía generada", variable_code="generated_energy", variable_type="generated_energy", unit="kWh", required=True, min_value=0, max_value=None, description="Energía generada en el sistema", display_order=2, active=True),
        BaselineVariable(baseline_model_id=aqua_baseline.id, variable_name="Horas blower", variable_code="operating_hours", variable_type="operating_hours", unit="h", required=True, min_value=0, max_value=744, description="Horas de blower", display_order=3, active=True),
        BaselineVariable(baseline_model_id=aqua_baseline.id, variable_name="Caudal", variable_code="flow", variable_type="flow", unit="m3/h", required=True, min_value=0, max_value=None, description="Caudal promedio", display_order=4, active=True),
    ]
    db.add_all(elf_variables + aqua_variables)
    db.flush()

    elf_ide = IdeDefinition(
        energy_system_id=elf.id,
        area_id=elf_areas[0].id,
        energy_use_id=elf_use_1.id,
        baseline_model_id=elf_baseline.id,
        ide_code="IDE-ELF-01",
        ide_name="IDE ELF Proceso",
        formula_text="real_consumption / production_monthly",
        numerator="real_consumption",
        denominator="production_monthly",
        unit="kWh/ton",
        expected_range_min=0.5,
        expected_range_max=4.5,
        warning_threshold_percentage=10,
        critical_threshold_percentage=20,
        active=True,
    )
    aqua_ide = IdeDefinition(
        energy_system_id=aqua.id,
        area_id=elf_areas[2].id,
        energy_use_id=aqua_use_1.id,
        baseline_model_id=aqua_baseline.id,
        ide_code="IDE-AQUA-01",
        ide_name="IDE AquaChile Producción",
        formula_text="real_consumption / tons_processed",
        numerator="real_consumption",
        denominator="tons_processed",
        unit="kWh/ton",
        expected_range_min=0.4,
        expected_range_max=5.2,
        warning_threshold_percentage=10,
        critical_threshold_percentage=20,
        active=True,
    )
    db.add_all([elf_ide, aqua_ide])
    db.flush()

    db.add_all(
        [
            AlertRule(
                energy_system_id=elf.id,
                baseline_model_id=elf_baseline.id,
                ide_id=elf_ide.id,
                metric="percentage_difference",
                operator=">",
                threshold_value=20,
                threshold_percentage=20,
                severity="high",
                message_template="Desviación superior al 20% en ELF",
                active=True,
            ),
            AlertRule(
                energy_system_id=aqua.id,
                baseline_model_id=aqua_baseline.id,
                ide_id=aqua_ide.id,
                metric="percentage_difference",
                operator=">",
                threshold_value=20,
                threshold_percentage=20,
                severity="high",
                message_template="Desviación superior al 20% en AquaChile",
                active=True,
            ),
        ]
    )
    db.flush()

    _create_measurement(
        db,
        system=elf,
        area=elf_areas[0],
        use=elf_use_1,
        baseline=elf_baseline,
        ide=elf_ide,
        year=2025,
        month=1,
        real_consumption=1850,
        consumption_unit="kWh",
        variable_values={"production_monthly": 4300, "ambient_temperature": 18, "operating_hours": 290},
    )
    _create_measurement(
        db,
        system=elf,
        area=elf_areas[0],
        use=elf_use_1,
        baseline=elf_baseline,
        ide=elf_ide,
        year=2025,
        month=2,
        real_consumption=2120,
        consumption_unit="kWh",
        variable_values={"production_monthly": 4100, "ambient_temperature": 22, "operating_hours": 301},
    )
    _create_measurement(
        db,
        system=aqua,
        area=elf_areas[2],
        use=aqua_use_1,
        baseline=aqua_baseline,
        ide=aqua_ide,
        year=2025,
        month=1,
        real_consumption=3650,
        consumption_unit="kWh",
        variable_values={"tons_processed": 6900, "generated_energy": 220, "operating_hours": 310, "flow": 150},
    )
    _create_measurement(
        db,
        system=aqua,
        area=elf_areas[2],
        use=aqua_use_1,
        baseline=aqua_baseline,
        ide=aqua_ide,
        year=2025,
        month=2,
        real_consumption=4025,
        consumption_unit="kWh",
        variable_values={"tons_processed": 7050, "generated_energy": 195, "operating_hours": 298, "flow": 160},
    )

    db.commit()
