from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.repositories.csv_repository import CSVRepository
from app.services.calculations import calculate_difference, calculate_expected_consumption, calculate_ide_from_formula, calculate_percentage_difference, classify_compliance


CSV_DIR = Path(__file__).resolve().parents[2] / "data" / "csv"


TABLE_COLUMNS: dict[str, list[str]] = {
    "energy_systems": ["id", "code", "name", "company", "description", "active"],
    "energy_areas": ["id", "energy_system_id", "name", "type", "area_name", "area_type", "company", "region", "description", "active"],
    "energy_uses": ["id", "energy_system_id", "area_id", "name", "energy_source", "description", "is_significant", "active"],
    "bne_energy_consumption": [
        "id",
        "energy_system_id",
        "year",
        "company",
        "area",
        "plant_name",
        "region",
        "energy_source",
        "transaction_category",
        "quantity_input",
        "quantity_output",
        "unit",
        "conversion_factor",
        "energy_input_tcal",
        "energy_output_tcal",
        "energy_total_tcal",
        "energy_total_kwh",
        "source",
    ],
    "energy_use_base_year": [
        "id",
        "energy_system_id",
        "base_year",
        "area_id",
        "area_name",
        "installation_name",
        "energy_source",
        "use_category",
        "consumption_value",
        "consumption_unit",
        "consumption_tcal",
        "percentage",
        "accumulated_percentage",
        "difference_vs_latest_year",
        "percentage_difference_vs_latest_year",
        "is_candidate_use",
        "is_significant_use",
        "source",
        "notes",
        "active",
    ],
    "significant_energy_uses": [
        "id",
        "energy_system_id",
        "energy_use_base_year_id",
        "area_id",
        "name",
        "use_name",
        "energy_source",
        "selection_status",
        "selection_criteria",
        "physical_consumption",
        "physical_unit",
        "energy_consumption_tcal",
        "relevant_variables_text",
        "current_energy_performance",
        "current_energy_performance_unit",
        "measurement_date",
        "influential_personnel",
        "deviation_range",
        "observations",
        "active",
    ],
    "baseline_models": [
        "id",
        "energy_system_id",
        "significant_energy_use_id",
        "baseline_code",
        "baseline_name",
        "name",
        "area_id",
        "area_name",
        "energy_use_id",
        "dependent_variable",
        "dependent_variable_unit",
        "model_type",
        "formula_text",
        "intercept",
        "coefficients",
        "r_squared",
        "adjusted_r_squared",
        "reference_period_start",
        "reference_period_end",
        "valid_from",
        "valid_to",
        "static_factors",
        "routine_adjustments",
        "non_routine_adjustments",
        "active",
    ],
    "baseline_variables": [
        "id",
        "baseline_model_id",
        "variable_name",
        "variable_code",
        "variable_type",
        "unit",
        "required",
        "min_value",
        "max_value",
        "description",
        "measurement_reason",
        "collection_method",
        "storage_location",
        "responsible_area",
        "responsible_person",
        "frequency",
        "missing_data_procedure",
        "display_order",
        "active",
    ],
    "ide_definitions": [
        "id",
        "energy_system_id",
        "significant_energy_use_id",
        "baseline_model_id",
        "area_id",
        "energy_use_id",
        "ide_code",
        "ide_name",
        "definition",
        "purpose",
        "area_monitored",
        "formula_text",
        "numerator",
        "denominator",
        "unit",
        "frequency",
        "monitoring_period",
        "expected_range_min",
        "expected_range_max",
        "warning_threshold_percentage",
        "critical_threshold_percentage",
        "data_origin",
        "protocol_description",
        "active",
    ],
    "monthly_measurements": [
        "id",
        "energy_system_id",
        "significant_energy_use_id",
        "baseline_model_id",
        "ide_id",
        "area_id",
        "energy_use_id",
        "year",
        "month",
        "month_number",
        "real_consumption",
        "consumption_unit",
        "expected_consumption",
        "ide_real",
        "ide_expected",
        "difference",
        "percentage_difference",
        "energy_savings",
        "accumulated_savings",
        "compliance_status",
        "comments",
        "status",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
    ],
    "monthly_measurement_variables": ["id", "monthly_measurement_id", "baseline_variable_id", "variable_code", "variable_name", "value", "unit", "created_at", "updated_at"],
    "tracking_trends": ["id", "energy_system_id", "year", "month", "month_number", "baseline_model_id", "baseline_code", "metric_name", "percentage_difference", "trend_status", "notes"],
    "data_collection_plan": [
        "id",
        "energy_system_id",
        "baseline_model_id",
        "significant_energy_use_id",
        "element",
        "description",
        "data_measured",
        "measurement_reason",
        "collection_method",
        "storage_location",
        "responsible_area",
        "responsible_person",
        "frequency",
        "missing_data_procedure",
        "report_section",
        "active",
    ],
    "equipment_characterization": [
        "id",
        "energy_system_id",
        "area_id",
        "unit",
        "equipment",
        "brand",
        "classification",
        "quantity_per_center",
        "power_kw",
        "total_power_kw",
        "hours_per_day",
        "has_consumption_meter",
        "connected_to_grid",
        "powered_by_generator",
        "daily_energy_consumption_kwh",
        "monthly_energy_consumption_kwh",
        "associated_significant_energy_use_id",
        "notes",
        "active",
    ],
    "operational_controls": [
        "id",
        "energy_system_id",
        "significant_energy_use_id",
        "control_name",
        "technical_criteria",
        "administrative_criteria",
        "maintenance_criteria",
        "responsible_area",
        "responsible_person",
        "record_type",
        "record_frequency",
        "training_required",
        "last_training_date",
        "effectiveness_evaluation_method",
        "status",
        "active",
    ],
    "alert_rules": ["id", "energy_system_id", "baseline_model_id", "ide_id", "metric", "operator", "threshold_value", "threshold_percentage", "severity", "message_template", "active"],
    "alert_events": [
        "id",
        "energy_system_id",
        "monthly_measurement_id",
        "baseline_model_id",
        "ide_id",
        "alert_rule_id",
        "severity",
        "message",
        "value_detected",
        "threshold_value",
        "status",
        "created_at",
        "closed_at",
        "closed_by",
        "comments",
    ],
    "measurement_audit_log": ["id", "monthly_measurement_id", "user_id", "action", "field_name", "old_value", "new_value", "comment", "created_at"],
    "users": ["id", "username", "full_name", "email", "role", "active"],
}


BASELINE_SPECS: list[dict[str, Any]] = [
    {
        "id": 1,
        "energy_system_id": 1,
        "significant_energy_use_id": 6,
        "baseline_code": "LBEN_CEEA",
        "baseline_name": "LBEn Centros de engorda Empresas AquaChile",
        "name": "LBEn Centros de engorda Empresas AquaChile",
        "area_id": 3,
        "area_name": "Centros XI Empresas AquaChile",
        "energy_use_id": 6,
        "dependent_variable": "Consumo diésel",
        "dependent_variable_unit": "Litros",
        "model_type": "Regresión lineal",
        "formula_text": "Consumo Petróleo = 56.405 * Horas Blower - 3576.8",
        "intercept": -3576.8,
        "coefficients": {"horas_blower": 56.405},
        "r_squared": 0.9424,
        "adjusted_r_squared": None,
        "reference_period_start": "2023-08-01",
        "reference_period_end": "2024-10-31",
        "valid_from": "2024-01-01",
        "valid_to": "",
        "static_factors": {"generadores": "2 por centro", "energetico": "Petróleo diésel"},
        "routine_adjustments": {},
        "non_routine_adjustments": {},
        "active": True,
        "variables": [
            {
                "id": 1,
                "baseline_model_id": 1,
                "variable_name": "Horas Blower",
                "variable_code": "horas_blower",
                "variable_type": "operating_hours",
                "unit": "h",
                "required": True,
                "min_value": 100,
                "max_value": 2000,
                "description": "Horas de uso de blower",
                "measurement_reason": "Variable independiente de LBEn",
                "collection_method": "Wireless Smart System",
                "storage_location": "Plataforma SGE",
                "responsible_area": "Mantenimiento Centros",
                "responsible_person": "",
                "frequency": "Mensual",
                "missing_data_procedure": "Revisar dato con jefe de centro",
                "display_order": 1,
                "active": True,
            }
        ],
        "ide": {
            "id": 1,
            "ide_code": "IDE_1_CEEA",
            "ide_name": "Intensidad energética del petróleo en Centros de engorda Empresas AquaChile",
            "definition": "Relación entre consumo de petróleo diésel y horas de uso de sopladores",
            "purpose": "Medir eficiencia del consumo de combustible y uso óptimo de sopladores",
            "area_monitored": "Mantenimiento de Centros",
            "formula_text": "real_consumption / horas_blower",
            "numerator": "consumo_diesel_real",
            "denominator": "horas_blower",
            "unit": "L/h",
            "frequency": "Mensual",
            "monitoring_period": "Mensual",
            "expected_range_min": 45,
            "expected_range_max": 70,
            "warning_threshold_percentage": 10,
            "critical_threshold_percentage": 20,
            "data_origin": "SAP/Excel + Wireless Smart System",
            "protocol_description": "",
            "active": True,
        },
        "operational_control": {
            "control_name": "Control operación blower",
            "technical_criteria": "Verificar régimen horario y caudal de blower",
            "administrative_criteria": "Registro mensual de operación",
            "maintenance_criteria": "Mantenimiento preventivo mensual",
            "responsible_area": "Mantenimiento Centros",
            "responsible_person": "Jefe de centros",
            "record_type": "Bitácora",
            "record_frequency": "Mensual",
            "training_required": True,
            "last_training_date": "2024-01-15",
            "effectiveness_evaluation_method": "Revisión de desviación IDE",
            "status": "active",
            "active": True,
        },
        "equipment": [
            {
                "equipment": "blower",
                "brand": "Generic",
                "classification": "Soplador",
                "quantity_per_center": 4,
                "power_kw": 7.5,
                "hours_per_day": 14,
                "has_consumption_meter": True,
                "connected_to_grid": True,
                "powered_by_generator": False,
            },
            {
                "equipment": "generador diésel",
                "brand": "Cummins",
                "classification": "Generación respaldo",
                "quantity_per_center": 2,
                "power_kw": 120,
                "hours_per_day": 6,
                "has_consumption_meter": True,
                "connected_to_grid": False,
                "powered_by_generator": True,
            },
        ],
    },
    {
        "id": 2,
        "energy_system_id": 1,
        "significant_energy_use_id": 4,
        "baseline_code": "LBEN_CEAM",
        "baseline_name": "LBEn Centros de engorda AquaChile Magallanes",
        "name": "LBEn Centros de engorda AquaChile Magallanes",
        "area_id": 2,
        "area_name": "Centros XII AquaChile Magallanes",
        "energy_use_id": 4,
        "dependent_variable": "Consumo diésel",
        "dependent_variable_unit": "Litros",
        "model_type": "Regresión múltiple",
        "formula_text": "Consumo Petróleo = -27226.62 -53.98*Horas Blower + 1.951*Kwh Blower",
        "intercept": -27226.62,
        "coefficients": {"horas_blower": -53.9796, "kwh_blower": 1.9511},
        "r_squared": 0.8387,
        "adjusted_r_squared": 0.8064,
        "reference_period_start": "2023-10-01",
        "reference_period_end": "2024-10-31",
        "valid_from": "2024-01-01",
        "valid_to": "",
        "static_factors": {"generadores": "2 por centro", "energetico": "Petróleo diésel"},
        "routine_adjustments": {},
        "non_routine_adjustments": {},
        "active": True,
        "variables": [
            {
                "id": 2,
                "baseline_model_id": 2,
                "variable_name": "Horas Blower",
                "variable_code": "horas_blower",
                "variable_type": "operating_hours",
                "unit": "h",
                "required": True,
                "min_value": 0,
                "max_value": 3000,
                "description": "Horas de uso de blower",
                "measurement_reason": "Variable independiente de LBEn",
                "collection_method": "Wireless Smart System",
                "storage_location": "Plataforma SGE",
                "responsible_area": "Mantenimiento Centros",
                "responsible_person": "",
                "frequency": "Mensual",
                "missing_data_procedure": "Revisar dato con jefe de centro",
                "display_order": 1,
                "active": True,
            },
            {
                "id": 3,
                "baseline_model_id": 2,
                "variable_name": "Energía consumida Blower",
                "variable_code": "kwh_blower",
                "variable_type": "electricity_consumption",
                "unit": "kWh",
                "required": True,
                "min_value": 0,
                "max_value": 200000,
                "description": "Energía eléctrica consumida por blower",
                "measurement_reason": "Variable independiente de LBEn",
                "collection_method": "Medidor eléctrico / WSS",
                "storage_location": "Plataforma SGE",
                "responsible_area": "Mantenimiento Centros",
                "responsible_person": "",
                "frequency": "Mensual",
                "missing_data_procedure": "Revisar medidor o estimar con respaldo",
                "display_order": 2,
                "active": True,
            },
        ],
        "ide": {
            "id": 2,
            "ide_code": "IDE_2_CEAM",
            "ide_name": "Intensidad energética del petróleo en Centros de engorda Magallanes",
            "definition": "Relación entre consumo de petróleo diésel horas de uso y consumo eléctrico blower",
            "purpose": "Medir eficiencia del consumo de combustible y uso óptimo de sopladores",
            "area_monitored": "Mantenimiento de Centros",
            "formula_text": "real_consumption * 1000 / (kwh_blower * horas_blower)",
            "numerator": "consumo_diesel_real",
            "denominator": "kwh_blower",
            "unit": "L/(kWh*h)",
            "frequency": "Mensual",
            "monitoring_period": "Mensual",
            "expected_range_min": 0.15,
            "expected_range_max": 0.45,
            "warning_threshold_percentage": 10,
            "critical_threshold_percentage": 20,
            "data_origin": "SAP/Excel + Wireless Smart System",
            "protocol_description": "",
            "active": True,
        },
        "operational_control": {
            "control_name": "Control consumo diésel centros",
            "technical_criteria": "Verificar horas blower y consumo de diésel",
            "administrative_criteria": "Registro mensual de operación",
            "maintenance_criteria": "Mantenimiento preventivo mensual",
            "responsible_area": "Mantenimiento Centros",
            "responsible_person": "Jefe de centros",
            "record_type": "Bitácora",
            "record_frequency": "Mensual",
            "training_required": True,
            "last_training_date": "2024-01-20",
            "effectiveness_evaluation_method": "Revisión de desviación IDE",
            "status": "active",
            "active": True,
        },
        "equipment": [
            {
                "equipment": "blower",
                "brand": "Generic",
                "classification": "Soplador",
                "quantity_per_center": 5,
                "power_kw": 8.2,
                "hours_per_day": 15,
                "has_consumption_meter": True,
                "connected_to_grid": True,
                "powered_by_generator": False,
            },
            {
                "equipment": "generador diésel",
                "brand": "Caterpillar",
                "classification": "Generación respaldo",
                "quantity_per_center": 2,
                "power_kw": 150,
                "hours_per_day": 7,
                "has_consumption_meter": True,
                "connected_to_grid": False,
                "powered_by_generator": True,
            },
        ],
    },
    {
        "id": 3,
        "energy_system_id": 1,
        "significant_energy_use_id": 1,
        "baseline_code": "LBEN_CALDERA_GLP",
        "baseline_name": "LBEn Hollemberg Caldera GLP",
        "name": "LBEn Hollemberg Caldera GLP",
        "area_id": 1,
        "area_name": "Hollemberg",
        "energy_use_id": 1,
        "dependent_variable": "Consumo GLP",
        "dependent_variable_unit": "Litros",
        "model_type": "Regresión múltiple",
        "formula_text": "Consumo GLP = 10000 + 5000*dummy_mes + 300*delta_temperatura - 250*temperatura_ambiente",
        "intercept": 10000,
        "coefficients": {"dummy_mes": 5000, "delta_temperatura": 300, "temperatura_ambiente": -250},
        "r_squared": 0.82,
        "adjusted_r_squared": None,
        "reference_period_start": "2022-02-01",
        "reference_period_end": "2025-12-31",
        "valid_from": "2024-01-01",
        "valid_to": "",
        "static_factors": {"equipo": "Caldera", "energetico": "GLP"},
        "routine_adjustments": {},
        "non_routine_adjustments": {},
        "active": True,
        "variables": [
            {
                "id": 4,
                "baseline_model_id": 3,
                "variable_name": "Temperatura ambiente",
                "variable_code": "temperatura_ambiente",
                "variable_type": "ambient_temperature",
                "unit": "°C",
                "required": True,
                "min_value": -10,
                "max_value": 30,
                "description": "Temperatura mensual ambiente",
                "measurement_reason": "Ajuste rutinario de caldera",
                "collection_method": "Registro meteorológico",
                "storage_location": "Planilla SGE",
                "responsible_area": "Piscicultura Hollemberg",
                "responsible_person": "",
                "frequency": "Mensual",
                "missing_data_procedure": "Usar promedio mensual validado",
                "display_order": 1,
                "active": True,
            },
            {
                "id": 5,
                "baseline_model_id": 3,
                "variable_name": "Dummy mes",
                "variable_code": "dummy_mes",
                "variable_type": "other",
                "unit": "adimensional",
                "required": True,
                "min_value": 0,
                "max_value": 1,
                "description": "Variable estacional de la LBEn",
                "measurement_reason": "Ajuste estadístico",
                "collection_method": "Calculado automáticamente",
                "storage_location": "Sistema SGE",
                "responsible_area": "Piscicultura Hollemberg",
                "responsible_person": "",
                "frequency": "Mensual",
                "missing_data_procedure": "Asignar según mes",
                "display_order": 2,
                "active": True,
            },
            {
                "id": 6,
                "baseline_model_id": 3,
                "variable_name": "Diferencia de temperatura",
                "variable_code": "delta_temperatura",
                "variable_type": "other",
                "unit": "K",
                "required": True,
                "min_value": 0,
                "max_value": 400,
                "description": "Diferencia térmica del proceso",
                "measurement_reason": "Variable independiente de LBEn",
                "collection_method": "Calculado automáticamente",
                "storage_location": "Sistema SGE",
                "responsible_area": "Piscicultura Hollemberg",
                "responsible_person": "",
                "frequency": "Mensual",
                "missing_data_procedure": "Recalcular desde temperaturas",
                "display_order": 3,
                "active": True,
            },
        ],
        "ide": {
            "id": 3,
            "ide_code": "IDE_3_CALDERA_GLP",
            "ide_name": "Intensidad energética Caldera GLP",
            "definition": "Relación entre consumo GLP y variable térmica",
            "purpose": "Medir eficiencia de la caldera",
            "area_monitored": "Piscicultura Hollemberg",
            "formula_text": "real_consumption / delta_temperatura",
            "numerator": "consumo_glp_real",
            "denominator": "delta_temperatura",
            "unit": "L/K",
            "frequency": "Mensual",
            "monitoring_period": "Mensual",
            "expected_range_min": 100,
            "expected_range_max": 500,
            "warning_threshold_percentage": 10,
            "critical_threshold_percentage": 20,
            "data_origin": "Planilla + sensor temperatura",
            "protocol_description": "",
            "active": True,
        },
        "operational_control": {
            "control_name": "Control operación caldera GLP",
            "technical_criteria": "Verificar temperatura y consumo GLP",
            "administrative_criteria": "Registro mensual de operación",
            "maintenance_criteria": "Mantenimiento preventivo mensual",
            "responsible_area": "Piscicultura Hollemberg",
            "responsible_person": "Jefe de piscicultura",
            "record_type": "Bitácora",
            "record_frequency": "Mensual",
            "training_required": True,
            "last_training_date": "2024-01-10",
            "effectiveness_evaluation_method": "Revisión de desviación IDE",
            "status": "active",
            "active": True,
        },
        "equipment": [
            {
                "equipment": "caldera GLP",
                "brand": "Baxi",
                "classification": "Caldera",
                "quantity_per_center": 1,
                "power_kw": 85,
                "hours_per_day": 10,
                "has_consumption_meter": True,
                "connected_to_grid": False,
                "powered_by_generator": True,
            },
            {
                "equipment": "generador GLP",
                "brand": "Generac",
                "classification": "Generación principal",
                "quantity_per_center": 1,
                "power_kw": 90,
                "hours_per_day": 8,
                "has_consumption_meter": True,
                "connected_to_grid": False,
                "powered_by_generator": True,
            },
        ],
    },
    {
        "id": 4,
        "energy_system_id": 1,
        "significant_energy_use_id": 2,
        "baseline_code": "LBEN_GEN_GLP",
        "baseline_name": "LBEn Hollemberg Generador GLP",
        "name": "LBEn Hollemberg Generador GLP",
        "area_id": 1,
        "area_name": "Hollemberg",
        "energy_use_id": 2,
        "dependent_variable": "Consumo GLP",
        "dependent_variable_unit": "Litros",
        "model_type": "Regresión lineal",
        "formula_text": "Consumo GLP = 8703.8 + 0.7354 * kwh_generados",
        "intercept": 8703.8,
        "coefficients": {"kwh_generados": 0.7354},
        "r_squared": 0.8167,
        "adjusted_r_squared": None,
        "reference_period_start": "2023-01-01",
        "reference_period_end": "2025-12-31",
        "valid_from": "2024-01-01",
        "valid_to": "",
        "static_factors": {"equipo": "Generador GLP"},
        "routine_adjustments": {},
        "non_routine_adjustments": {},
        "active": True,
        "variables": [
            {
                "id": 7,
                "baseline_model_id": 4,
                "variable_name": "Electricidad generada",
                "variable_code": "kwh_generados",
                "variable_type": "generated_energy",
                "unit": "kWh",
                "required": True,
                "min_value": 0,
                "max_value": 1000000,
                "description": "Energía generada por generador GLP",
                "measurement_reason": "Variable independiente de LBEn",
                "collection_method": "Medidor generador",
                "storage_location": "Plataforma SGE",
                "responsible_area": "Piscicultura Hollemberg",
                "responsible_person": "",
                "frequency": "Mensual",
                "missing_data_procedure": "Revisar horómetro/medidor",
                "display_order": 1,
                "active": True,
            }
        ],
        "ide": {
            "id": 4,
            "ide_code": "IDE_4_PGEN_GLP",
            "ide_name": "Intensidad energética Generador GLP",
            "definition": "Relación entre GLP consumido y electricidad generada",
            "purpose": "Medir eficiencia de generación GLP",
            "area_monitored": "Piscicultura Hollemberg",
            "formula_text": "real_consumption / kwh_generados",
            "numerator": "consumo_glp_real",
            "denominator": "kwh_generados",
            "unit": "L/kWh",
            "frequency": "Mensual",
            "monitoring_period": "Mensual",
            "expected_range_min": 5,
            "expected_range_max": 30,
            "warning_threshold_percentage": 10,
            "critical_threshold_percentage": 20,
            "data_origin": "Planilla + medidor generador",
            "protocol_description": "",
            "active": True,
        },
        "operational_control": {
            "control_name": "Control generador GLP",
            "technical_criteria": "Verificar consumo y salida eléctrica",
            "administrative_criteria": "Registro mensual de operación",
            "maintenance_criteria": "Mantenimiento preventivo mensual",
            "responsible_area": "Piscicultura Hollemberg",
            "responsible_person": "Jefe de piscicultura",
            "record_type": "Bitácora",
            "record_frequency": "Mensual",
            "training_required": True,
            "last_training_date": "2024-01-10",
            "effectiveness_evaluation_method": "Revisión de desviación IDE",
            "status": "active",
            "active": True,
        },
        "equipment": [
            {
                "equipment": "generador GLP",
                "brand": "Generac",
                "classification": "Generación principal",
                "quantity_per_center": 1,
                "power_kw": 110,
                "hours_per_day": 8,
                "has_consumption_meter": True,
                "connected_to_grid": False,
                "powered_by_generator": True,
            }
        ],
    },
    {
        "id": 5,
        "energy_system_id": 1,
        "significant_energy_use_id": 3,
        "baseline_code": "LBEN_GEN_DIESEL",
        "baseline_name": "LBEn Hollemberg Generador Diésel",
        "name": "LBEn Hollemberg Generador Diésel",
        "area_id": 1,
        "area_name": "Hollemberg",
        "energy_use_id": 3,
        "dependent_variable": "Consumo diésel",
        "dependent_variable_unit": "Litros",
        "model_type": "Regresión lineal",
        "formula_text": "Consumo Diésel = 25088 + 0.2139 * kwh_generados",
        "intercept": 25088,
        "coefficients": {"kwh_generados": 0.2139},
        "r_squared": 0.8167,
        "adjusted_r_squared": None,
        "reference_period_start": "2022-01-01",
        "reference_period_end": "2025-12-31",
        "valid_from": "2024-01-01",
        "valid_to": "",
        "static_factors": {"equipo": "Generador diésel"},
        "routine_adjustments": {},
        "non_routine_adjustments": {},
        "active": True,
        "variables": [
            {
                "id": 8,
                "baseline_model_id": 5,
                "variable_name": "Electricidad generada",
                "variable_code": "kwh_generados",
                "variable_type": "generated_energy",
                "unit": "kWh",
                "required": True,
                "min_value": 0,
                "max_value": 1000000,
                "description": "Energía generada por generador diésel",
                "measurement_reason": "Variable independiente de LBEn",
                "collection_method": "Medidor generador",
                "storage_location": "Plataforma SGE",
                "responsible_area": "Piscicultura Hollemberg",
                "responsible_person": "",
                "frequency": "Mensual",
                "missing_data_procedure": "Revisar horómetro/medidor",
                "display_order": 1,
                "active": True,
            }
        ],
        "ide": {
            "id": 5,
            "ide_code": "IDE_5_PGEN_DIESEL",
            "ide_name": "Intensidad energética Generador Diésel",
            "definition": "Relación entre diésel consumido y electricidad generada",
            "purpose": "Medir eficiencia de generación diésel",
            "area_monitored": "Piscicultura Hollemberg",
            "formula_text": "real_consumption / kwh_generados",
            "numerator": "consumo_diesel_real",
            "denominator": "kwh_generados",
            "unit": "L/kWh",
            "frequency": "Mensual",
            "monitoring_period": "Mensual",
            "expected_range_min": 10,
            "expected_range_max": 50,
            "warning_threshold_percentage": 10,
            "critical_threshold_percentage": 20,
            "data_origin": "Planilla + medidor generador",
            "protocol_description": "",
            "active": True,
        },
        "operational_control": {
            "control_name": "Control generador diésel",
            "technical_criteria": "Verificar consumo y salida eléctrica",
            "administrative_criteria": "Registro mensual de operación",
            "maintenance_criteria": "Mantenimiento preventivo mensual",
            "responsible_area": "Piscicultura Hollemberg",
            "responsible_person": "Jefe de piscicultura",
            "record_type": "Bitácora",
            "record_frequency": "Mensual",
            "training_required": True,
            "last_training_date": "2024-01-10",
            "effectiveness_evaluation_method": "Revisión de desviación IDE",
            "status": "active",
            "active": True,
        },
        "equipment": [
            {
                "equipment": "generador diésel",
                "brand": "Perkins",
                "classification": "Generación respaldo",
                "quantity_per_center": 1,
                "power_kw": 120,
                "hours_per_day": 7,
                "has_consumption_meter": True,
                "connected_to_grid": False,
                "powered_by_generator": True,
            }
        ],
    },
]


def _now_text() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_directory(reset: bool) -> None:
    if reset and CSV_DIR.exists():
        shutil.rmtree(CSV_DIR)
    CSV_DIR.mkdir(parents=True, exist_ok=True)


def _ordered_row(columns: list[str], data: dict[str, Any]) -> dict[str, Any]:
    row = {column: data.get(column) for column in columns}
    for key, value in data.items():
        if key not in row:
            row[key] = value
    return row


def _base_energy_systems() -> list[dict[str, Any]]:
    return [
        _ordered_row(
            TABLE_COLUMNS["energy_systems"],
            {
                "id": 1,
                "code": "AQUACHILE",
                "name": "Empresas AquaChile / AquaChile Magallanes",
                "company": "AquaChile",
                "description": "Sistema de Gestión de Energía AquaChile",
                "active": True,
            },
        )
    ]


def _base_areas() -> list[dict[str, Any]]:
    rows = [
        {"id": 1, "energy_system_id": 1, "name": "Hollemberg", "type": "Piscicultura", "area_name": "Hollemberg", "area_type": "Piscicultura", "company": "AquaChile Magallanes", "region": "Región de Magallanes", "description": "Piscicultura Hollemberg", "active": True},
        {"id": 2, "energy_system_id": 1, "name": "Centros Magallanes", "type": "Centros de engorda", "area_name": "Centros Magallanes", "area_type": "Centros de engorda", "company": "AquaChile Magallanes", "region": "Región de Magallanes", "description": "Centros de engorda Magallanes", "active": True},
        {"id": 3, "energy_system_id": 1, "name": "Centros XI", "type": "Centros de engorda", "area_name": "Centros XI", "area_type": "Centros de engorda", "company": "Empresas AquaChile", "region": "Región de Aysén", "description": "Centros de engorda Empresas AquaChile", "active": True},
        {"id": 4, "energy_system_id": 1, "name": "Planta Cardonal", "type": "Planta de proceso", "area_name": "Planta Cardonal", "area_type": "Planta de proceso", "company": "Empresas AquaChile", "region": "Región de Los Lagos", "description": "Planta de procesos Cardonal", "active": True},
        {"id": 5, "energy_system_id": 1, "name": "Centros X", "type": "Centros de engorda", "area_name": "Centros X", "area_type": "Centros de engorda", "company": "Empresas AquaChile", "region": "Región de Los Lagos", "description": "Centros de engorda Región de Los Lagos", "active": True},
    ]
    return [_ordered_row(TABLE_COLUMNS["energy_areas"], row) for row in rows]


def _base_energy_uses() -> list[dict[str, Any]]:
    rows = [
        {"id": 1, "energy_system_id": 1, "area_id": 1, "name": "Piscicultura Hollemberg - Caldera GLP", "energy_source": "GLP", "description": "Uso energético de caldera GLP", "is_significant": True, "active": True},
        {"id": 2, "energy_system_id": 1, "area_id": 1, "name": "Piscicultura Hollemberg - Generador GLP", "energy_source": "GLP", "description": "Uso energético de generador GLP", "is_significant": True, "active": True},
        {"id": 3, "energy_system_id": 1, "area_id": 1, "name": "Piscicultura Hollemberg - Generador Diésel", "energy_source": "Petróleo Diésel", "description": "Uso energético de generador diésel", "is_significant": True, "active": True},
        {"id": 4, "energy_system_id": 1, "area_id": 2, "name": "Centros XII AquaChile Magallanes - Generador Diésel", "energy_source": "Petróleo Diésel", "description": "Uso energético de generador diésel", "is_significant": True, "active": True},
        {"id": 5, "energy_system_id": 1, "area_id": 2, "name": "Centros XII AquaChile Magallanes - Blower Electricidad", "energy_source": "Electricidad", "description": "Uso energético de blower eléctrico", "is_significant": True, "active": True},
        {"id": 6, "energy_system_id": 1, "area_id": 3, "name": "Centros XI Empresas AquaChile - Generador Diésel", "energy_source": "Petróleo Diésel", "description": "Uso energético de generador diésel", "is_significant": True, "active": True},
        {"id": 7, "energy_system_id": 1, "area_id": 3, "name": "Centros XI Empresas AquaChile - Blower Electricidad", "energy_source": "Electricidad", "description": "Uso energético de blower eléctrico", "is_significant": True, "active": True},
        {"id": 8, "energy_system_id": 1, "area_id": 4, "name": "Planta Cardonal - Proceso", "energy_source": "MIXTO", "description": "Uso energético de proceso", "is_significant": False, "active": True},
        {"id": 9, "energy_system_id": 1, "area_id": 5, "name": "Centros X - Soporte", "energy_source": "MIXTO", "description": "Uso energético de soporte", "is_significant": False, "active": True},
    ]
    return [_ordered_row(TABLE_COLUMNS["energy_uses"], row) for row in rows]


def _bne_rows() -> list[dict[str, Any]]:
    rows = [
        {"id": 1, "energy_system_id": 1, "year": 2022, "company": "AquaChile Magallanes", "area": "Hollemberg", "plant_name": "Hollemberg", "region": "Región de Magallanes", "energy_source": "MIXTO", "transaction_category": "Consumo base", "quantity_input": 26523, "quantity_output": 26523, "unit": "tcal", "conversion_factor": 1.0, "energy_input_tcal": 26.523, "energy_output_tcal": 26.523, "energy_total_tcal": 26.523, "energy_total_kwh": 30846804, "source": "BNE 2022"},
        {"id": 2, "energy_system_id": 1, "year": 2022, "company": "AquaChile Magallanes", "area": "Centros Magallanes", "plant_name": "Centros Magallanes", "region": "Región de Magallanes", "energy_source": "DIÉSEL", "transaction_category": "Consumo base", "quantity_input": 9216, "quantity_output": 9216, "unit": "tcal", "conversion_factor": 1.0, "energy_input_tcal": 9.216, "energy_output_tcal": 9.216, "energy_total_tcal": 9.216, "energy_total_kwh": 10718473, "source": "BNE 2022"},
        {"id": 3, "energy_system_id": 1, "year": 2022, "company": "Empresas AquaChile", "area": "Centros XI", "plant_name": "Centros XI", "region": "Región de Aysén", "energy_source": "MIXTO", "transaction_category": "Consumo base", "quantity_input": 8059, "quantity_output": 8059, "unit": "tcal", "conversion_factor": 1.0, "energy_input_tcal": 8.059, "energy_output_tcal": 8.059, "energy_total_tcal": 8.059, "energy_total_kwh": 9370000, "source": "BNE 2022"},
        {"id": 4, "energy_system_id": 1, "year": 2022, "company": "Empresas AquaChile", "area": "Planta Cardonal", "plant_name": "Planta Cardonal", "region": "Región de Los Lagos", "energy_source": "MIXTO", "transaction_category": "Consumo base", "quantity_input": 6666, "quantity_output": 6666, "unit": "tcal", "conversion_factor": 1.0, "energy_input_tcal": 6.666, "energy_output_tcal": 6.666, "energy_total_tcal": 6.666, "energy_total_kwh": 7750000, "source": "BNE 2022"},
        {"id": 5, "energy_system_id": 1, "year": 2022, "company": "Empresas AquaChile", "area": "Centros X", "plant_name": "Centros X", "region": "Región de Los Lagos", "energy_source": "MIXTO", "transaction_category": "Consumo base", "quantity_input": 2945, "quantity_output": 2945, "unit": "tcal", "conversion_factor": 1.0, "energy_input_tcal": 2.945, "energy_output_tcal": 2.945, "energy_total_tcal": 2.945, "energy_total_kwh": 3420000, "source": "BNE 2022"},
        {"id": 6, "energy_system_id": 1, "year": 2024, "company": "AquaChile Magallanes", "area": "Hollemberg", "plant_name": "Hollemberg", "region": "Región de Magallanes", "energy_source": "MIXTO", "transaction_category": "Actualización", "quantity_input": 28100, "quantity_output": 28100, "unit": "tcal", "conversion_factor": 1.0, "energy_input_tcal": 28.100, "energy_output_tcal": 28.100, "energy_total_tcal": 28.100, "energy_total_kwh": 32643800, "source": "BNE 2024"},
        {"id": 7, "energy_system_id": 1, "year": 2024, "company": "AquaChile Magallanes", "area": "Centros Magallanes", "plant_name": "Centros Magallanes", "region": "Región de Magallanes", "energy_source": "DIÉSEL", "transaction_category": "Actualización", "quantity_input": 9800, "quantity_output": 9800, "unit": "tcal", "conversion_factor": 1.0, "energy_input_tcal": 9.800, "energy_output_tcal": 9.800, "energy_total_tcal": 9.800, "energy_total_kwh": 11390000, "source": "BNE 2024"},
        {"id": 8, "energy_system_id": 1, "year": 2024, "company": "Empresas AquaChile", "area": "Centros XI", "plant_name": "Centros XI", "region": "Región de Aysén", "energy_source": "MIXTO", "transaction_category": "Actualización", "quantity_input": 8450, "quantity_output": 8450, "unit": "tcal", "conversion_factor": 1.0, "energy_input_tcal": 8.450, "energy_output_tcal": 8.450, "energy_total_tcal": 8.450, "energy_total_kwh": 9815000, "source": "BNE 2024"},
        {"id": 9, "energy_system_id": 1, "year": 2024, "company": "Empresas AquaChile", "area": "Planta Cardonal", "plant_name": "Planta Cardonal", "region": "Región de Los Lagos", "energy_source": "MIXTO", "transaction_category": "Actualización", "quantity_input": 6250, "quantity_output": 6250, "unit": "tcal", "conversion_factor": 1.0, "energy_input_tcal": 6.250, "energy_output_tcal": 6.250, "energy_total_tcal": 6.250, "energy_total_kwh": 7264000, "source": "BNE 2024"},
        {"id": 10, "energy_system_id": 1, "year": 2024, "company": "Empresas AquaChile", "area": "Centros X", "plant_name": "Centros X", "region": "Región de Los Lagos", "energy_source": "MIXTO", "transaction_category": "Actualización", "quantity_input": 2700, "quantity_output": 2700, "unit": "tcal", "conversion_factor": 1.0, "energy_input_tcal": 2.700, "energy_output_tcal": 2.700, "energy_total_tcal": 2.700, "energy_total_kwh": 3138000, "source": "BNE 2024"},
    ]
    return [_ordered_row(TABLE_COLUMNS["bne_energy_consumption"], row) for row in rows]


def _energy_use_base_year_rows() -> list[dict[str, Any]]:
    rows = [
        {"id": 1, "energy_system_id": 1, "base_year": 2022, "area_id": 1, "area_name": "Hollemberg", "installation_name": "Hollemberg", "energy_source": "MIXTO", "use_category": "Caldera GLP", "consumption_value": 26523, "consumption_unit": "kWh", "consumption_tcal": 26.523, "percentage": 0.4966, "accumulated_percentage": 0.4966, "difference_vs_latest_year": 1.577, "percentage_difference_vs_latest_year": 5.95, "is_candidate_use": True, "is_significant_use": True, "source": "BNE 2022", "notes": "", "active": True},
        {"id": 2, "energy_system_id": 1, "base_year": 2022, "area_id": 2, "area_name": "Centros Magallanes", "installation_name": "Centros Magallanes", "energy_source": "DIÉSEL", "use_category": "Generador Diésel", "consumption_value": 9216, "consumption_unit": "kWh", "consumption_tcal": 9.216, "percentage": 0.1726, "accumulated_percentage": 0.6692, "difference_vs_latest_year": 0.584, "percentage_difference_vs_latest_year": 6.34, "is_candidate_use": True, "is_significant_use": True, "source": "BNE 2022", "notes": "", "active": True},
        {"id": 3, "energy_system_id": 1, "base_year": 2022, "area_id": 3, "area_name": "Centros XI", "installation_name": "Centros XI", "energy_source": "MIXTO", "use_category": "Generador Diésel", "consumption_value": 8059, "consumption_unit": "kWh", "consumption_tcal": 8.059, "percentage": 0.1509, "accumulated_percentage": 0.8201, "difference_vs_latest_year": 0.391, "percentage_difference_vs_latest_year": 4.85, "is_candidate_use": True, "is_significant_use": True, "source": "BNE 2022", "notes": "", "active": True},
        {"id": 4, "energy_system_id": 1, "base_year": 2022, "area_id": 4, "area_name": "Planta Cardonal", "installation_name": "Planta Cardonal", "energy_source": "MIXTO", "use_category": "Planta de proceso", "consumption_value": 6666, "consumption_unit": "kWh", "consumption_tcal": 6.666, "percentage": 0.1248, "accumulated_percentage": 0.9449, "difference_vs_latest_year": -0.416, "percentage_difference_vs_latest_year": -6.24, "is_candidate_use": True, "is_significant_use": False, "source": "BNE 2022", "notes": "", "active": True},
        {"id": 5, "energy_system_id": 1, "base_year": 2022, "area_id": 5, "area_name": "Centros X", "installation_name": "Centros X", "energy_source": "MIXTO", "use_category": "Soporte operacional", "consumption_value": 2945, "consumption_unit": "kWh", "consumption_tcal": 2.945, "percentage": 0.0551, "accumulated_percentage": 1.0, "difference_vs_latest_year": -0.245, "percentage_difference_vs_latest_year": -8.32, "is_candidate_use": False, "is_significant_use": False, "source": "BNE 2022", "notes": "", "active": True},
    ]
    return [_ordered_row(TABLE_COLUMNS["energy_use_base_year"], row) for row in rows]


def _baseline_model_rows() -> list[dict[str, Any]]:
    rows = []
    for spec in BASELINE_SPECS:
        rows.append(
            _ordered_row(
                TABLE_COLUMNS["baseline_models"],
                {
                    **spec,
                    "coefficients": spec["coefficients"],
                    "static_factors": spec["static_factors"],
                    "routine_adjustments": spec["routine_adjustments"],
                    "non_routine_adjustments": spec["non_routine_adjustments"],
                },
            )
        )
    return rows


def _baseline_variable_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in BASELINE_SPECS:
        rows.extend(_ordered_row(TABLE_COLUMNS["baseline_variables"], variable) for variable in spec["variables"])
    return rows


def _ide_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in BASELINE_SPECS:
        ide = dict(spec["ide"])
        rows.append(
            _ordered_row(
                TABLE_COLUMNS["ide_definitions"],
                {
                    "id": ide["id"],
                    "energy_system_id": 1,
                    "significant_energy_use_id": spec["significant_energy_use_id"],
                    "baseline_model_id": spec["id"],
                    "area_id": spec["area_id"],
                    "energy_use_id": spec["energy_use_id"],
                    "ide_code": ide["ide_code"],
                    "ide_name": ide["ide_name"],
                    "definition": ide["definition"],
                    "purpose": ide["purpose"],
                    "area_monitored": ide["area_monitored"],
                    "formula_text": ide["formula_text"],
                    "numerator": ide["numerator"],
                    "denominator": ide["denominator"],
                    "unit": ide["unit"],
                    "frequency": ide["frequency"],
                    "monitoring_period": ide["monitoring_period"],
                    "expected_range_min": ide["expected_range_min"],
                    "expected_range_max": ide["expected_range_max"],
                    "warning_threshold_percentage": ide["warning_threshold_percentage"],
                    "critical_threshold_percentage": ide["critical_threshold_percentage"],
                    "data_origin": ide["data_origin"],
                    "protocol_description": ide["protocol_description"],
                    "active": ide["active"],
                },
            )
        )
    return rows


def _plan_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    row_id = 1
    for spec in BASELINE_SPECS:
        for variable in spec["variables"]:
            rows.append(
                _ordered_row(
                    TABLE_COLUMNS["data_collection_plan"],
                    {
                        "id": row_id,
                        "energy_system_id": 1,
                        "baseline_model_id": spec["id"],
                        "significant_energy_use_id": spec["significant_energy_use_id"],
                        "element": variable["variable_name"],
                        "description": variable["description"],
                        "data_measured": variable["variable_name"],
                        "measurement_reason": variable["measurement_reason"],
                        "collection_method": variable["collection_method"],
                        "storage_location": variable["storage_location"],
                        "responsible_area": variable["responsible_area"],
                        "responsible_person": variable["responsible_person"] or "Sin asignar",
                        "frequency": variable["frequency"],
                        "missing_data_procedure": variable["missing_data_procedure"],
                        "report_section": "Art. 22",
                        "active": True,
                    },
                )
            )
            row_id += 1
    return rows


def _equipment_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    row_id = 1
    equipment_templates = [
        (1, 1, "blower", "BLOWER-01", "Sopladores", 2, 7.5, 14, True, True, False, 2100, 63000, 7),
        (1, 1, "generador diésel", "GEN-DIE-01", "Generadores", 2, 120, 7, True, False, True, 1800, 54000, 3),
        (1, 1, "generador GLP", "GEN-GLP-01", "Generadores", 1, 110, 8, True, False, True, 1500, 45000, 2),
        (1, 1, "caldera GLP", "CAL-GLP-01", "Calderas", 1, 85, 10, True, False, True, 1600, 48000, 1),
        (1, 2, "blower", "BLOWER-02", "Sopladores", 3, 8.2, 15, True, True, False, 2400, 72000, 5),
        (1, 3, "generador diésel", "GEN-DIE-03", "Generadores", 2, 150, 7, True, False, True, 2200, 66000, 6),
        (1, 3, "sistema de alimentación", "ALIM-01", "Alimentación", 2, 5.0, 12, True, True, False, 800, 24000, None),
    ]
    for energy_system_id, area_id, unit, equipment, classification, quantity, power_kw, hours_per_day, has_meter, connected, powered, daily_kwh, monthly_kwh, use_id in equipment_templates:
        rows.append(
            _ordered_row(
                TABLE_COLUMNS["equipment_characterization"],
                {
                    "id": row_id,
                    "energy_system_id": energy_system_id,
                    "area_id": area_id,
                    "unit": unit,
                    "equipment": equipment,
                    "brand": "AquaChile Base",
                    "classification": classification,
                    "quantity_per_center": quantity,
                    "power_kw": power_kw,
                    "total_power_kw": round(quantity * power_kw, 2),
                    "hours_per_day": hours_per_day,
                    "has_consumption_meter": has_meter,
                    "connected_to_grid": connected,
                    "powered_by_generator": powered,
                    "daily_energy_consumption_kwh": daily_kwh,
                    "monthly_energy_consumption_kwh": monthly_kwh,
                    "associated_significant_energy_use_id": use_id,
                    "notes": "",
                    "active": True,
                },
            )
        )
        row_id += 1
    return rows


def _operational_control_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    row_id = 1
    for spec in BASELINE_SPECS:
        control = dict(spec["operational_control"])
        rows.append(
            _ordered_row(
                TABLE_COLUMNS["operational_controls"],
                {
                    "id": row_id,
                    "energy_system_id": 1,
                    "significant_energy_use_id": spec["significant_energy_use_id"],
                    **control,
                },
            )
        )
        row_id += 1
    return rows


def _alert_rule_rows() -> dict[str, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    rule_id = 1
    rule_map: dict[str, list[dict[str, Any]]] = {}
    for spec in BASELINE_SPECS:
        rules_for_baseline = []
        templates = [
            ("percentage_difference", ">", None, 20, "high", "Desviación crítica superior al 20%"),
            ("percentage_difference", ">", None, 10, "medium", "Desviación sobre 10% y requiere revisión"),
            ("missing_required_variable", "=", 1, None, "critical", "Faltan variables requeridas"),
            ("real_consumption", "<=", 0, None, "critical", "El consumo real es cero o negativo"),
            ("variable_out_of_range", "=", 1, None, "medium", "Variable fuera de rango"),
        ]
        for metric, operator, threshold_value, threshold_percentage, severity, message in templates:
            rows.append(
                _ordered_row(
                    TABLE_COLUMNS["alert_rules"],
                    {
                        "id": rule_id,
                        "energy_system_id": 1,
                        "baseline_model_id": spec["id"],
                        "ide_id": spec["ide"]["id"],
                        "metric": metric,
                        "operator": operator,
                        "threshold_value": threshold_value,
                        "threshold_percentage": threshold_percentage,
                        "severity": severity,
                        "message_template": message,
                        "active": True,
                    },
                )
            )
            rules_for_baseline.append(rows[-1])
            rule_id += 1
        rule_map[str(spec["id"])] = rules_for_baseline
    return {"rows": rows, "rule_map": rule_map}


def _measurement_patterns(baseline_id: int, month: int) -> tuple[dict[str, float], float]:
    deviation_patterns = {
        1: [5, 12, 18, 7, 3, 22, -4, 15, 9, 11, 24, -2],
        2: [4, 9, 14, 6, 2, 18, -3, 21, 8, 10, 23, -1],
        3: [3, 11, 17, 5, 4, 19, -2, 16, 7, 13, 21, -3],
        4: [2, 8, 12, 5, 3, 15, -1, 18, 6, 9, 20, -2],
        5: [1, 7, 13, 4, 2, 16, -2, 19, 5, 8, 22, -1],
    }
    spec = next(item for item in BASELINE_SPECS if item["id"] == baseline_id)
    if baseline_id == 1:
        hours = 180 + month * 15
        variable_values = {"horas_blower": float(hours)}
    elif baseline_id == 2:
        hours = 200 + month * 8
        kwh = 24000 + month * 600
        variable_values = {"horas_blower": float(hours), "kwh_blower": float(kwh)}
    elif baseline_id == 3:
        temp = 12 + month * 0.6
        dummy = 1 if month in {6, 7, 8, 9} else 0
        delta = 35 + month * 1.8
        variable_values = {"temperatura_ambiente": float(round(temp, 2)), "dummy_mes": float(dummy), "delta_temperatura": float(round(delta, 2))}
    else:
        kwh = 900 + month * (45 if baseline_id == 4 else 55)
        variable_values = {"kwh_generados": float(kwh)}
    expected = calculate_expected_consumption(spec["intercept"], spec["coefficients"], variable_values) or 0
    deviation = deviation_patterns[baseline_id][month - 1]
    real = round(expected * (1 + deviation / 100), 2)
    return variable_values, real


def _measurement_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    measurements: list[dict[str, Any]] = []
    measurement_variables: list[dict[str, Any]] = []
    alerts: list[dict[str, Any]] = []
    audit_logs: list[dict[str, Any]] = []
    trend_rows: list[dict[str, Any]] = []
    measurement_id = 1
    variable_id = 1
    alert_id = 1
    audit_id = 1
    trend_id = 1
    cumulative_savings_by_baseline = {spec["id"]: 0.0 for spec in BASELINE_SPECS}
    alert_rule_rows = _alert_rule_rows()
    rule_map = alert_rule_rows["rule_map"]
    rule_lookup = {str(row["id"]): row for row in alert_rule_rows["rows"]}

    for spec in BASELINE_SPECS:
        for month in range(1, 13):
            variable_values, real = _measurement_patterns(spec["id"], month)
            expected = calculate_expected_consumption(spec["intercept"], spec["coefficients"], variable_values)
            ide_context = dict(variable_values)
            ide_context["real_consumption"] = real
            ide_real = calculate_ide_from_formula(spec["ide"]["formula_text"], ide_context)
            if expected is not None:
                ide_context["real_consumption"] = expected
                ide_expected = calculate_ide_from_formula(spec["ide"]["formula_text"], ide_context)
            else:
                ide_expected = None
            difference = calculate_difference(real, expected)
            percentage_difference = calculate_percentage_difference(difference, expected)
            compliance_status = classify_compliance(percentage_difference, True, real, expected)
            savings = round(max((expected or 0) - real, 0), 2)
            cumulative_savings_by_baseline[spec["id"]] += savings
            status = ["draft", "submitted", "reviewed", "approved"][month % 4]
            created_at = datetime(2024, month, 28, 12, 0, tzinfo=timezone.utc).isoformat()
            updated_at = datetime(2024, month, 28, 12, 30, tzinfo=timezone.utc).isoformat()
            measurement = _ordered_row(
                TABLE_COLUMNS["monthly_measurements"],
                {
                    "id": measurement_id,
                    "energy_system_id": 1,
                    "significant_energy_use_id": spec["significant_energy_use_id"],
                    "baseline_model_id": spec["id"],
                    "ide_id": spec["ide"]["id"],
                    "area_id": spec["area_id"],
                    "energy_use_id": spec["energy_use_id"],
                    "year": 2024,
                    "month": month,
                    "month_number": month,
                    "real_consumption": real,
                    "consumption_unit": spec["dependent_variable_unit"],
                    "expected_consumption": expected,
                    "ide_real": ide_real,
                    "ide_expected": ide_expected,
                    "difference": difference,
                    "percentage_difference": percentage_difference,
                    "energy_savings": savings,
                    "accumulated_savings": round(cumulative_savings_by_baseline[spec["id"]], 2),
                    "compliance_status": compliance_status,
                    "comments": f"Seguimiento mensual {spec['baseline_code']} {month:02d}/2024",
                    "status": status,
                    "created_by": 1,
                    "created_at": created_at,
                    "updated_by": 2,
                    "updated_at": updated_at,
                },
            )
            measurements.append(measurement)

            for variable in spec["variables"]:
                measurement_variables.append(
                    _ordered_row(
                        TABLE_COLUMNS["monthly_measurement_variables"],
                        {
                            "id": variable_id,
                            "monthly_measurement_id": measurement_id,
                            "baseline_variable_id": variable["id"],
                            "variable_code": variable["variable_code"],
                            "variable_name": variable["variable_name"],
                            "value": variable_values[variable["variable_code"]],
                            "unit": variable["unit"],
                            "created_at": created_at,
                            "updated_at": updated_at,
                        },
                    )
                )
                variable_id += 1

            trend_rows.append(
                _ordered_row(
                    TABLE_COLUMNS["tracking_trends"],
                    {
                        "id": trend_id,
                        "energy_system_id": 1,
                        "year": 2024,
                        "month": month,
                        "month_number": month,
                        "baseline_model_id": spec["id"],
                        "baseline_code": spec["baseline_code"],
                        "metric_name": "percentage_difference",
                        "percentage_difference": percentage_difference,
                        "trend_status": "high" if abs(percentage_difference or 0) > 20 else "medium" if abs(percentage_difference or 0) > 10 else "stable",
                        "notes": f"Mes {month:02d} / {spec['baseline_code']}",
                    },
                )
            )
            trend_id += 1

            if percentage_difference is not None and abs(percentage_difference) > 10:
                matched_rule = None
                for rule in rule_map[str(spec["id"])]:
                    if rule["metric"] == "percentage_difference" and rule["severity"] == ("high" if abs(percentage_difference) > 20 else "medium"):
                        matched_rule = rule
                        break
                alerts.append(
                    _ordered_row(
                        TABLE_COLUMNS["alert_events"],
                        {
                            "id": alert_id,
                            "energy_system_id": 1,
                            "monthly_measurement_id": measurement_id,
                            "baseline_model_id": spec["id"],
                            "ide_id": spec["ide"]["id"],
                            "alert_rule_id": matched_rule["id"] if matched_rule else None,
                            "severity": "high" if abs(percentage_difference) > 20 else "medium",
                            "message": "Desviación crítica superior al 20%" if abs(percentage_difference) > 20 else "Desviación sobre 10% y requiere revisión",
                            "value_detected": percentage_difference,
                            "threshold_value": 20 if abs(percentage_difference) > 20 else 10,
                            "status": "open",
                            "created_at": created_at,
                            "closed_at": "",
                            "closed_by": "",
                            "comments": "",
                        },
                    )
                )
                alert_id += 1

            audit_logs.append(
                _ordered_row(
                    TABLE_COLUMNS["measurement_audit_log"],
                    {
                        "id": audit_id,
                        "monthly_measurement_id": measurement_id,
                        "user_id": 1,
                        "action": "created",
                        "field_name": "",
                        "old_value": "",
                        "new_value": "",
                        "comment": "Creación de seguimiento mensual",
                        "created_at": created_at,
                    },
                )
            )
            audit_id += 1
            audit_logs.append(
                _ordered_row(
                    TABLE_COLUMNS["measurement_audit_log"],
                    {
                        "id": audit_id,
                        "monthly_measurement_id": measurement_id,
                        "user_id": 2,
                        "action": status,
                        "field_name": "status",
                        "old_value": "draft",
                        "new_value": status,
                        "comment": f"Cambio de estado a {status}",
                        "created_at": updated_at,
                    },
                )
            )
            audit_id += 1

            measurement_id += 1

    return measurements, measurement_variables, trend_rows, alerts, audit_logs, alert_rule_rows["rows"]


def build_seed_data() -> dict[str, list[dict[str, Any]]]:
    measurements, measurement_variables, trends, alerts, audit_logs, alert_rules = _measurement_rows()
    return {
        "energy_systems": _base_energy_systems(),
        "energy_areas": _base_areas(),
        "energy_uses": _base_energy_uses(),
        "bne_energy_consumption": _bne_rows(),
        "energy_use_base_year": _energy_use_base_year_rows(),
        "significant_energy_uses": [
            _ordered_row(
                TABLE_COLUMNS["significant_energy_uses"],
                {
                    "id": 1,
                    "energy_system_id": 1,
                    "energy_use_base_year_id": 1,
                    "area_id": 1,
                    "name": "Piscicultura Hollemberg - Caldera GLP",
                    "use_name": "Piscicultura Hollemberg - Caldera GLP",
                    "energy_source": "GLP",
                    "selection_status": "Con LBEn e IDEs",
                    "selection_criteria": "Consumo real",
                    "physical_consumption": 822938,
                    "physical_unit": "Litros",
                    "energy_consumption_tcal": 15.46,
                    "relevant_variables_text": "Temperatura ambiente; Temperatura de funcionamiento; Petróleo consumido; GLP consumido",
                    "current_energy_performance": 21.90,
                    "current_energy_performance_unit": "Litros/Kelvin",
                    "measurement_date": "2024-12",
                    "influential_personnel": "Jefe de piscicultura",
                    "deviation_range": "20% de desviación",
                    "observations": "",
                    "active": True,
                },
            ),
            _ordered_row(
                TABLE_COLUMNS["significant_energy_uses"],
                {
                    "id": 2,
                    "energy_system_id": 1,
                    "energy_use_base_year_id": 1,
                    "area_id": 1,
                    "name": "Piscicultura Hollemberg - Generador GLP",
                    "use_name": "Piscicultura Hollemberg - Generador GLP",
                    "energy_source": "GLP",
                    "selection_status": "Con LBEn e IDEs",
                    "selection_criteria": "Consumo real",
                    "physical_consumption": 1313743,
                    "physical_unit": "Litros",
                    "energy_consumption_tcal": 8.21,
                    "relevant_variables_text": "Electricidad generada; GLP consumido",
                    "current_energy_performance": 77.57,
                    "current_energy_performance_unit": "Litros/kWh",
                    "measurement_date": "2024-12",
                    "influential_personnel": "Jefe de piscicultura",
                    "deviation_range": "20% de desviación",
                    "observations": "",
                    "active": True,
                },
            ),
            _ordered_row(
                TABLE_COLUMNS["significant_energy_uses"],
                {
                    "id": 3,
                    "energy_system_id": 1,
                    "energy_use_base_year_id": 1,
                    "area_id": 1,
                    "name": "Piscicultura Hollemberg - Generador Diésel",
                    "use_name": "Piscicultura Hollemberg - Generador Diésel",
                    "energy_source": "Petróleo Diésel",
                    "selection_status": "Con LBEn e IDEs",
                    "selection_criteria": "Consumo real",
                    "physical_consumption": 1208800,
                    "physical_unit": "Litros",
                    "energy_consumption_tcal": 11.07,
                    "relevant_variables_text": "Electricidad generada; Petróleo consumido",
                    "current_energy_performance": 25.64,
                    "current_energy_performance_unit": "Litros/kWh",
                    "measurement_date": "2024-12",
                    "influential_personnel": "Jefe de piscicultura",
                    "deviation_range": "20% de desviación",
                    "observations": "",
                    "active": True,
                },
            ),
            _ordered_row(
                TABLE_COLUMNS["significant_energy_uses"],
                {
                    "id": 4,
                    "energy_system_id": 1,
                    "energy_use_base_year_id": 2,
                    "area_id": 2,
                    "name": "Centros XII AquaChile Magallanes - Generador Diésel",
                    "use_name": "Centros XII AquaChile Magallanes - Generador Diésel",
                    "energy_source": "Petróleo Diésel",
                    "selection_status": "Con LBEn e IDEs",
                    "selection_criteria": "Consumo real",
                    "physical_consumption": 1006578,
                    "physical_unit": "Litros",
                    "energy_consumption_tcal": 9.216,
                    "relevant_variables_text": "Horas de uso Blower; Energía consumida Blower; Petróleo consumido",
                    "current_energy_performance": 0.2925,
                    "current_energy_performance_unit": "Litros/Horas*kWh",
                    "measurement_date": "2024-12",
                    "influential_personnel": "Jefe de Centros Magallanes",
                    "deviation_range": "20% de desviación",
                    "observations": "",
                    "active": True,
                },
            ),
            _ordered_row(
                TABLE_COLUMNS["significant_energy_uses"],
                {
                    "id": 5,
                    "energy_system_id": 1,
                    "energy_use_base_year_id": 2,
                    "area_id": 2,
                    "name": "Centros XII AquaChile Magallanes - Blower Electricidad",
                    "use_name": "Centros XII AquaChile Magallanes - Blower Electricidad",
                    "energy_source": "Electricidad",
                    "selection_status": "Con LBEn e IDEs",
                    "selection_criteria": "Consumo real",
                    "physical_consumption": 4458700,
                    "physical_unit": "kWh",
                    "energy_consumption_tcal": 3.838,
                    "relevant_variables_text": "Horas de uso Blower; Energía consumida Blower",
                    "current_energy_performance": 0,
                    "current_energy_performance_unit": "kWh",
                    "measurement_date": "2024-12",
                    "influential_personnel": "Jefe de Centros Magallanes",
                    "deviation_range": "20% de desviación",
                    "observations": "",
                    "active": True,
                },
            ),
            _ordered_row(
                TABLE_COLUMNS["significant_energy_uses"],
                {
                    "id": 6,
                    "energy_system_id": 1,
                    "energy_use_base_year_id": 3,
                    "area_id": 3,
                    "name": "Centros XI Empresas AquaChile - Generador Diésel",
                    "use_name": "Centros XI Empresas AquaChile - Generador Diésel",
                    "energy_source": "Petróleo Diésel",
                    "selection_status": "Con LBEn e IDEs",
                    "selection_criteria": "Consumo real",
                    "physical_consumption": 868372,
                    "physical_unit": "Litros",
                    "energy_consumption_tcal": 7.951,
                    "relevant_variables_text": "Horas de uso Blower; Petróleo consumido",
                    "current_energy_performance": 43.31,
                    "current_energy_performance_unit": "L/hrs",
                    "measurement_date": "2024-12",
                    "influential_personnel": "Jefe de Centros XI",
                    "deviation_range": "20% de desviación",
                    "observations": "",
                    "active": True,
                },
            ),
            _ordered_row(
                TABLE_COLUMNS["significant_energy_uses"],
                {
                    "id": 7,
                    "energy_system_id": 1,
                    "energy_use_base_year_id": 3,
                    "area_id": 3,
                    "name": "Centros XI Empresas AquaChile - Blower Electricidad",
                    "use_name": "Centros XI Empresas AquaChile - Blower Electricidad",
                    "energy_source": "Electricidad",
                    "selection_status": "Con LBEn e IDEs",
                    "selection_criteria": "Consumo real",
                    "physical_consumption": 3843382,
                    "physical_unit": "kWh",
                    "energy_consumption_tcal": 3.311,
                    "relevant_variables_text": "Horas de uso Blower; Energía consumida Blower",
                    "current_energy_performance": 0,
                    "current_energy_performance_unit": "kWh",
                    "measurement_date": "2024-12",
                    "influential_personnel": "Jefe de Centros XI",
                    "deviation_range": "20% de desviación",
                    "observations": "",
                    "active": True,
                },
            ),
        ],
        "baseline_models": _baseline_model_rows(),
        "baseline_variables": _baseline_variable_rows(),
        "ide_definitions": _ide_rows(),
        "monthly_measurements": measurements,
        "monthly_measurement_variables": measurement_variables,
        "tracking_trends": trends,
        "data_collection_plan": _plan_rows(),
        "equipment_characterization": _equipment_rows(),
        "operational_controls": _operational_control_rows(),
        "alert_rules": alert_rules,
        "alert_events": alerts,
        "measurement_audit_log": audit_logs,
        "users": [
            _ordered_row(TABLE_COLUMNS["users"], {"id": 1, "username": "admin", "full_name": "Administrador SGE", "email": "admin@sge.local", "role": "admin", "active": True}),
            _ordered_row(TABLE_COLUMNS["users"], {"id": 2, "username": "gestor", "full_name": "Gestor Energético", "email": "gestor@sge.local", "role": "gestor_energetico", "active": True}),
            _ordered_row(TABLE_COLUMNS["users"], {"id": 3, "username": "viewer", "full_name": "Usuario Consulta", "email": "viewer@sge.local", "role": "viewer", "active": True}),
        ],
    }


def seed_csv(reset: bool = False) -> None:
    _ensure_directory(reset)
    repository = CSVRepository(CSV_DIR)
    seed_data = build_seed_data()
    for table_name, columns in TABLE_COLUMNS.items():
        rows = seed_data.get(table_name, [])
        prepared_rows = [_ordered_row(columns, row) for row in rows]
        if reset:
            repository.write_all(table_name, prepared_rows)
            continue
        existing_rows = repository.read_all(table_name)
        if not existing_rows:
            repository.write_all(table_name, prepared_rows)
            continue
        existing_by_id = {str(row.get("id")): row for row in existing_rows if row.get("id") is not None}
        for row in prepared_rows:
            existing_by_id[str(row.get("id"))] = row
        repository.write_all(table_name, list(existing_by_id.values()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed CSV local data for SGE Aquachile")
    parser.add_argument("--reset", action="store_true", help="Regenerate all CSV files from scratch")
    args = parser.parse_args()
    seed_csv(reset=bool(args.reset))


if __name__ == "__main__":
    main()
