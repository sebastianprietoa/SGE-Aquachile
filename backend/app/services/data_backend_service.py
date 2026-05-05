from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.energy import BaselineModel, BaselineVariable, EnergyArea, EnergySystem, EnergyUse, EnergyUseBaseYear, IdeDefinition, OperationalControl, SignificantEnergyUse
from app.models.measurement import AlertEvent, MeasurementAuditLog, MonthlyMeasurement, MonthlyMeasurementVariable, User
from app.repositories.csv_repository import CSVRepository
from app.repositories.repository_factory import PostgresRepository, RepositoryFactory
from app.schemas.common import AlertEventRead, AlertRuleCreate, AlertRuleRead, AlertRuleUpdate, AlertSummary, ApiMessage, BaselineModelCreate, BaselineModelRead, BaselineModelUpdate, BaselineVariableCreate, BaselineVariableRead, BaselineVariableUpdate, DashboardKpis, DashboardResponse, EnergyAreaCreate, EnergyAreaRead, EnergyAreaUpdate, EnergySystemRead, EnergyUseCreate, EnergyUseRead, EnergyUseUpdate, IdeDefinitionCreate, IdeDefinitionRead, IdeDefinitionUpdate, MonthlyMeasurementRead, MeasurementAuditLogRead, PerformanceSummaryResponse, TokenResponse, TrendPoint, UserRead
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
from app.services.alerts import build_default_alerts
from app.services.calculations import calculate_difference, calculate_expected_consumption, calculate_ide_from_formula, calculate_percentage_difference, classify_compliance


_MONTH_LABELS = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        text = value.strip().replace(",", ".")
        if text == "":
            return None
        return float(text)
    return float(value)


def _as_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _parse_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _coerce_measurement_dict(item: dict[str, Any]) -> dict[str, Any]:
    payload = dict(item)
    payload["variables"] = payload.get("variables", [])
    return payload


class DataBackendService:
    def __init__(self, db: Session | None = None) -> None:
        self.settings = get_settings()
        self.db = db
        self.repository = RepositoryFactory.create(db)
        self._is_csv = isinstance(self.repository, CSVRepository)

    # ------------------------------------------------------------------
    # Generic backend helpers
    # ------------------------------------------------------------------
    def _csv(self) -> CSVRepository:
        if not self._is_csv:
            raise RuntimeError("CSV backend no disponible en este modo")
        assert isinstance(self.repository, CSVRepository)
        return self.repository

    def _read(self, table_name: str) -> list[dict[str, Any]]:
        if self._is_csv:
            return self._csv().read_all(table_name)
        return self._read_postgres(table_name)

    def _read_postgres(self, table_name: str) -> list[dict[str, Any]]:
        assert self.db is not None
        if table_name == "energy_systems":
            return [
                {
                    "id": item.id,
                    "code": item.code,
                    "name": item.name,
                    "company": item.company,
                    "description": item.description,
                    "active": item.active,
                }
                for item in self.db.query(EnergySystem).order_by(EnergySystem.id.asc()).all()
            ]
        return []

    def _write(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        if self._is_csv:
            self._csv().write_all(table_name, rows)
            return
        raise NotImplementedError("Escritura en PostgreSQL será habilitada en una iteración posterior")

    def _create(self, table_name: str, data: dict[str, Any]) -> dict[str, Any]:
        if self._is_csv:
            return self._csv().create(table_name, data)
        raise NotImplementedError("Creación en PostgreSQL será habilitada en una iteración posterior")

    def _update(self, table_name: str, record_id: int | str, data: dict[str, Any]) -> dict[str, Any]:
        if self._is_csv:
            return self._csv().update(table_name, record_id, data)
        raise NotImplementedError("Actualización en PostgreSQL será habilitada en una iteración posterior")

    def _soft_delete(self, table_name: str, record_id: int | str) -> dict[str, Any]:
        if self._is_csv:
            return self._csv().soft_delete(table_name, record_id)
        raise NotImplementedError("Soft delete en PostgreSQL será habilitado en una iteración posterior")

    def _filter(self, table_name: str, **filters: Any) -> list[dict[str, Any]]:
        if self._is_csv:
            return self._csv().filter(table_name, **filters)
        return []

    def _get(self, table_name: str, record_id: int | str) -> dict[str, Any] | None:
        if self._is_csv:
            return self._csv().get_by_id(table_name, record_id)
        return None

    def _require_system(self, system_id: int) -> dict[str, Any]:
        system = self.get_system(system_id)
        if not system:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sistema no encontrado")
        return system

    # ------------------------------------------------------------------
    # Core catalog endpoints
    # ------------------------------------------------------------------
    def list_systems(self) -> list[dict[str, Any]]:
        if self._is_csv:
            return self._read("energy_systems")
        assert self.db is not None
        return [
            {
                "id": item.id,
                "code": item.code,
                "name": item.name,
                "company": item.company,
                "description": item.description,
                "active": item.active,
            }
            for item in self.db.query(EnergySystem).order_by(EnergySystem.id.asc()).all()
        ]

    def get_system(self, system_id: int) -> dict[str, Any] | None:
        return self._get("energy_systems", system_id)

    def list_areas(self, system_id: int) -> list[dict[str, Any]]:
        self._require_system(system_id)
        return self._filter("energy_areas", energy_system_id=system_id)

    def create_area(self, system_id: int, payload: EnergyAreaCreate | EnergyAreaUpdate) -> dict[str, Any]:
        self._require_system(system_id)
        data = payload.model_dump() if hasattr(payload, "model_dump") else dict(payload)
        data["energy_system_id"] = system_id
        data["area_name"] = data.get("name")
        data["area_type"] = data.get("type")
        return self._create("energy_areas", data)

    def update_area(self, area_id: int, payload: EnergyAreaUpdate) -> dict[str, Any]:
        data = payload.model_dump(exclude_unset=True)
        if "name" in data:
            data["area_name"] = data["name"]
        if "type" in data:
            data["area_type"] = data["type"]
        return self._update("energy_areas", area_id, data)

    def list_energy_uses(self, system_id: int) -> list[dict[str, Any]]:
        self._require_system(system_id)
        return self._filter("energy_uses", energy_system_id=system_id)

    def create_energy_use(self, system_id: int, payload: EnergyUseCreate) -> dict[str, Any]:
        self._require_system(system_id)
        data = payload.model_dump()
        data["energy_system_id"] = system_id
        return self._create("energy_uses", data)

    def update_energy_use(self, energy_use_id: int, payload: EnergyUseUpdate) -> dict[str, Any]:
        return self._update("energy_uses", energy_use_id, payload.model_dump(exclude_unset=True))

    def list_energy_use_base_year(self, system_id: int) -> list[dict[str, Any]]:
        self._require_system(system_id)
        items = self._filter("energy_use_base_year", energy_system_id=system_id)
        return sorted(items, key=lambda item: (-float(item.get("accumulated_percentage") or 0), -float(item.get("percentage") or 0), int(item.get("id") or 0)))

    @staticmethod
    def _normalize_percentage(value: Any) -> float:
        percentage = _as_float(value) or 0.0
        if abs(percentage) <= 1:
            percentage *= 100
        return round(percentage, 2)

    def _pareto_rows_from_base_year(self, system_id: int) -> list[dict[str, Any]]:
        rows = []
        for item in self.list_energy_use_base_year(system_id):
            value = _as_float(item.get("consumption_tcal") or item.get("consumption_value") or 0) or 0.0
            rows.append(
                {
                    "year": int(item.get("base_year") or 2022),
                    "label": item.get("installation_name") or item.get("area_name"),
                    "value": value,
                    "source": item.get("source") or "BNE 2022",
                }
            )
        return rows

    def _pareto_rows_from_bne(self, system_id: int, year: int | None = None) -> list[dict[str, Any]]:
        rows = []
        for item in self._filter("bne_energy_consumption", energy_system_id=system_id):
            item_year = int(item.get("year") or 0)
            if year is not None and item_year != year:
                continue
            if item_year == 2022:
                continue
            value = _as_float(item.get("energy_total_tcal") or item.get("energy_input_tcal") or item.get("energy_output_tcal") or 0) or 0.0
            rows.append(
                {
                    "year": item_year,
                    "label": item.get("area") or item.get("plant_name"),
                    "value": value,
                    "source": item.get("source") or f"BNE {item_year}",
                }
            )
        return rows

    def _build_pareto_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[int(row["year"])].append(row)

        output: list[dict[str, Any]] = []
        for year in sorted(grouped):
            year_rows = sorted(grouped[year], key=lambda item: (-float(item.get("value") or 0), str(item.get("label") or "")))
            total = sum(float(item.get("value") or 0) for item in year_rows)
            cumulative = 0.0
            for item in year_rows:
                value = float(item.get("value") or 0)
                cumulative += value
                percentage = round((value / total) * 100, 2) if total else 0.0
                accumulated_percentage = round((cumulative / total) * 100, 2) if total else 0.0
                output.append(
                    {
                        "year": year,
                        "label": item.get("label"),
                        "value": round(value, 3),
                        "percentage": percentage,
                        "accumulated_percentage": accumulated_percentage,
                        "source": item.get("source"),
                    }
                )
        return output

    def pareto_energy_use_base_year(self, system_id: int, year: int | None = None) -> list[dict[str, Any]]:
        self._require_system(system_id)
        rows = self._pareto_rows_from_base_year(system_id)
        rows.extend(self._pareto_rows_from_bne(system_id, year=year))
        if year is not None:
            rows = [item for item in rows if int(item["year"]) == year]
        return self._build_pareto_rows(rows)

    def create_energy_use_base_year(self, system_id: int, payload: EnergyUseBaseYearCreate) -> dict[str, Any]:
        self._require_system(system_id)
        data = payload.model_dump()
        data["energy_system_id"] = system_id
        return self._create("energy_use_base_year", data)

    def list_significant_energy_uses(self, system_id: int) -> list[dict[str, Any]]:
        self._require_system(system_id)
        return self._filter("significant_energy_uses", energy_system_id=system_id)

    def get_significant_energy_use(self, use_id: int) -> dict[str, Any] | None:
        return self._get("significant_energy_uses", use_id)

    def create_significant_energy_use(self, system_id: int, payload: SignificantEnergyUseCreate) -> dict[str, Any]:
        self._require_system(system_id)
        data = payload.model_dump()
        data["energy_system_id"] = system_id
        data["name"] = data.get("name") or data.get("use_name")
        data["use_name"] = data.get("name")
        return self._create("significant_energy_uses", data)

    def update_significant_energy_use(self, use_id: int, payload: SignificantEnergyUseUpdate) -> dict[str, Any]:
        data = payload.model_dump(exclude_unset=True)
        if "name" in data:
            data["use_name"] = data["name"]
        return self._update("significant_energy_uses", use_id, data)

    def list_baselines(self, system_id: int) -> list[dict[str, Any]]:
        self._require_system(system_id)
        return self._filter("baseline_models", energy_system_id=system_id)

    def get_baseline(self, baseline_id: int) -> dict[str, Any] | None:
        return self._get("baseline_models", baseline_id)

    def create_baseline_model(self, system_id: int, payload: BaselineModelBaseV2 | BaselineModelCreate) -> dict[str, Any]:
        self._require_system(system_id)
        data = payload.model_dump()
        data["energy_system_id"] = system_id
        data["baseline_name"] = data.get("name")
        if data.get("area_id"):
            area = self._get("energy_areas", data["area_id"])
            data["area_name"] = area.get("area_name") if area else None
        return self._create("baseline_models", data)

    def update_baseline_model(self, baseline_id: int, payload: BaselineModelUpdateV2 | BaselineModelUpdate) -> dict[str, Any]:
        data = payload.model_dump(exclude_unset=True)
        if "name" in data:
            data["baseline_name"] = data["name"]
        if "area_id" in data:
            area = self._get("energy_areas", data["area_id"])
            data["area_name"] = area.get("area_name") if area else None
        return self._update("baseline_models", baseline_id, data)

    def list_baseline_variables(self, baseline_id: int) -> list[dict[str, Any]]:
        baseline = self.get_baseline(baseline_id)
        if not baseline:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Línea base no encontrada")
        items = self._filter("baseline_variables", baseline_model_id=baseline_id)
        return sorted(items, key=lambda item: (int(item.get("display_order") or 0), int(item.get("id") or 0)))

    def create_baseline_variable(self, baseline_id: int, payload: BaselineVariableCreateV2 | BaselineVariableCreate) -> dict[str, Any]:
        self.get_baseline(baseline_id) or self._raise_not_found("Línea base no encontrada")
        data = payload.model_dump()
        data["baseline_model_id"] = baseline_id
        return self._create("baseline_variables", data)

    def update_baseline_variable(self, variable_id: int, payload: BaselineVariableUpdateV2 | BaselineVariableUpdate) -> dict[str, Any]:
        return self._update("baseline_variables", variable_id, payload.model_dump(exclude_unset=True))

    def list_ides(self, system_id: int) -> list[dict[str, Any]]:
        self._require_system(system_id)
        return self._filter("ide_definitions", energy_system_id=system_id)

    def get_ide(self, ide_id: int) -> dict[str, Any] | None:
        return self._get("ide_definitions", ide_id)

    def create_ide(self, system_id: int, payload: IdeDefinitionCreateV2 | IdeDefinitionCreate) -> dict[str, Any]:
        self._require_system(system_id)
        data = payload.model_dump()
        data["energy_system_id"] = system_id
        return self._create("ide_definitions", data)

    def update_ide(self, ide_id: int, payload: IdeDefinitionUpdateV2 | IdeDefinitionUpdate) -> dict[str, Any]:
        return self._update("ide_definitions", ide_id, payload.model_dump(exclude_unset=True))

    def list_alert_rules(self, system_id: int) -> list[dict[str, Any]]:
        self._require_system(system_id)
        return self._filter("alert_rules", energy_system_id=system_id)

    def create_alert_rule(self, payload: AlertRuleCreate) -> dict[str, Any]:
        self._require_system(payload.energy_system_id)
        return self._create("alert_rules", payload.model_dump())

    def update_alert_rule(self, alert_rule_id: int, payload: AlertRuleUpdate) -> dict[str, Any]:
        return self._update("alert_rules", alert_rule_id, payload.model_dump(exclude_unset=True))

    # ------------------------------------------------------------------
    # CSV-only supporting datasets
    # ------------------------------------------------------------------
    def list_data_collection_plan(self, system_id: int) -> list[dict[str, Any]]:
        self._require_system(system_id)
        rows = self._filter("data_collection_plan", energy_system_id=system_id)
        baselines = {int(item["id"]): item for item in self.list_baselines(system_id)}
        uses = {int(item["id"]): item for item in self.list_significant_energy_uses(system_id)}
        baseline_variables_by_baseline = {
            baseline_id: {var["variable_name"]: var for var in self.list_baseline_variables(baseline_id)}
            for baseline_id in baselines
        }
        return [
            {
                "variable_name": row.get("element") or row.get("data_measured"),
                "variable_code": baseline_variables_by_baseline.get(int(row["baseline_model_id"]), {}).get(row.get("element"), {}).get("variable_code")
                or str(row.get("element") or row.get("data_measured") or "").strip().lower().replace(" ", "_"),
                "use_name": uses.get(int(row["significant_energy_use_id"]), {}).get("name"),
                "baseline_name": baselines.get(int(row["baseline_model_id"]), {}).get("name"),
                "what_is_measured": row.get("data_measured") or row.get("description"),
                "why_it_is_measured": row.get("measurement_reason"),
                "collection_method": row.get("collection_method"),
                "storage_location": row.get("storage_location"),
                "responsible_area": row.get("responsible_area"),
                "responsible_person": row.get("responsible_person"),
                "frequency": row.get("frequency"),
                "missing_data_procedure": row.get("missing_data_procedure"),
                "min_value": row.get("min_value"),
                "max_value": row.get("max_value"),
                "active": row.get("active", True),
            }
            for row in rows
        ]

    def list_equipment_characterization(self, system_id: int) -> list[dict[str, Any]]:
        self._require_system(system_id)
        return self._filter("equipment_characterization", energy_system_id=system_id)

    def list_operational_controls(self, system_id: int) -> list[dict[str, Any]]:
        self._require_system(system_id)
        return [
            {
                **row,
                "name": row.get("name") or row.get("control_name"),
            }
            for row in self._filter("operational_controls", energy_system_id=system_id)
        ]

    def get_use_operational_controls(self, use_id: int) -> list[dict[str, Any]]:
        use = self.get_significant_energy_use(use_id)
        if not use:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="USE no encontrado")
        return [
            {
                **row,
                "name": row.get("name") or row.get("control_name"),
            }
            for row in self._filter("operational_controls", significant_energy_use_id=use_id)
        ]

    def create_operational_control(self, system_id: int, payload: OperationalControlCreate) -> dict[str, Any]:
        self._require_system(system_id)
        data = payload.model_dump()
        data["energy_system_id"] = system_id
        data["name"] = data.get("name") or data.get("control_name")
        data["control_name"] = data.get("name")
        return self._create("operational_controls", data)

    def update_operational_control(self, control_id: int, payload: OperationalControlUpdate) -> dict[str, Any]:
        data = payload.model_dump(exclude_unset=True)
        if "name" in data:
            data["control_name"] = data["name"]
        return self._update("operational_controls", control_id, data)

    # ------------------------------------------------------------------
    # Measurement storage and traceability
    # ------------------------------------------------------------------
    def _measurement_rows(self) -> list[dict[str, Any]]:
        return self._read("monthly_measurements")

    def _measurement_variables_rows(self) -> list[dict[str, Any]]:
        return self._read("monthly_measurement_variables")

    def _alert_events_rows(self) -> list[dict[str, Any]]:
        return self._read("alert_events")

    def _audit_rows(self) -> list[dict[str, Any]]:
        return self._read("measurement_audit_log")

    def _get_measurement_row(self, measurement_id: int) -> dict[str, Any] | None:
        return self._get("monthly_measurements", measurement_id)

    def _measurement_variables_for(self, measurement_id: int) -> list[dict[str, Any]]:
        rows = self._filter("monthly_measurement_variables", monthly_measurement_id=measurement_id)
        return sorted(rows, key=lambda item: int(item.get("baseline_variable_id") or 0))

    def _alerts_for(self, measurement_id: int) -> list[dict[str, Any]]:
        return sorted(self._filter("alert_events", monthly_measurement_id=measurement_id), key=lambda item: int(item.get("id") or 0), reverse=True)

    def _audit_for(self, measurement_id: int) -> list[dict[str, Any]]:
        return sorted(self._filter("measurement_audit_log", monthly_measurement_id=measurement_id), key=lambda item: item.get("created_at") or datetime.min, reverse=True)

    def _baseline_variable_map(self, baseline_id: int) -> dict[str, dict[str, Any]]:
        return {item["variable_code"]: item for item in self.list_baseline_variables(baseline_id)}

    def _measurement_variable_map(self, baseline_id: int, payload_variables: list[dict[str, Any]]) -> tuple[dict[str, float], list[dict[str, Any]]]:
        baseline_variables = self.list_baseline_variables(baseline_id)
        by_id = {int(item["id"]): item for item in baseline_variables}
        variable_map: dict[str, float] = {}
        seen_ids: set[int] = set()
        for item in payload_variables:
            baseline_variable_id = int(item["baseline_variable_id"])
            baseline_variable = by_id.get(baseline_variable_id)
            if baseline_variable is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La variable no pertenece a la línea base seleccionada")
            if baseline_variable_id in seen_ids:
                continue
            seen_ids.add(baseline_variable_id)
            variable_code = str(item["variable_code"])
            if variable_code != baseline_variable["variable_code"]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código de variable no coincide con la línea base")
            variable_map[variable_code] = float(item["value"])
        return variable_map, baseline_variables

    def _validate_measurement_context(self, system_id: int, baseline_id: int, ide_id: int, use_id: int | None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        baseline = self.get_baseline(baseline_id)
        ide = self.get_ide(ide_id)
        use = self.get_significant_energy_use(use_id) if use_id is not None else None
        if not baseline or not ide or not use:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contexto energético no encontrado")
        if int(baseline["energy_system_id"]) != system_id or int(ide["energy_system_id"]) != system_id or int(use["energy_system_id"]) != system_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El contexto no pertenece al sistema seleccionado")
        if baseline.get("significant_energy_use_id") and int(baseline["significant_energy_use_id"]) != int(use["id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La línea base no corresponde al USE seleccionado")
        if int(ide["baseline_model_id"]) != int(baseline["id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El IDE no corresponde a la línea base")
        return baseline, ide, use

    def _measurement_unique_check(self, system_id: int, area_id: int, use_id: int | None, baseline_id: int, year: int, month: int, measurement_id: int | None = None) -> None:
        for item in self._measurement_rows():
            if measurement_id is not None and int(item["id"]) == measurement_id:
                continue
            if (
                int(item["energy_system_id"]) == system_id
                and int(item["area_id"]) == area_id
                and int(item["baseline_model_id"]) == baseline_id
                and int(item["year"]) == year
                and int(item["month"]) == month
                and (use_id is None or int(item.get("significant_energy_use_id") or 0) == int(use_id))
            ):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe una medición para la misma combinación sistema + área + USE + línea base + año + mes")

    def _compute_measurement_metrics(
        self,
        baseline: dict[str, Any],
        ide: dict[str, Any],
        variable_map: dict[str, float],
        real_consumption: float,
    ) -> tuple[float | None, float | None, float | None, float | None, float | None, str]:
        required_codes = {item["variable_code"] for item in self.list_baseline_variables(int(baseline["id"])) if item["required"]}
        has_all_required = all(code in variable_map for code in required_codes)
        if not has_all_required:
            return None, None, None, None, None, "incomplete"
        expected_consumption = calculate_expected_consumption(float(baseline.get("intercept") or 0), baseline.get("coefficients"), variable_map)
        context = dict(variable_map)
        context["real_consumption"] = float(real_consumption)
        ide_real = calculate_ide_from_formula(ide.get("formula_text"), context)
        if expected_consumption is not None:
            context["real_consumption"] = float(expected_consumption)
            ide_expected = calculate_ide_from_formula(ide.get("formula_text"), context)
        else:
            ide_expected = None
        difference = calculate_difference(real_consumption, expected_consumption)
        percentage_difference = calculate_percentage_difference(difference, expected_consumption)
        compliance_status = classify_compliance(percentage_difference, has_all_required, real_consumption, expected_consumption)
        return expected_consumption, ide_real, ide_expected, difference, percentage_difference, compliance_status

    def _detect_alerts(
        self,
        *,
        system_id: int,
        baseline: dict[str, Any],
        ide: dict[str, Any],
        measurement_id: int,
        real_consumption: float,
        percentage_difference: float | None,
        ide_real: float | None,
        variable_map: dict[str, float],
        baseline_variables: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        rules = self.list_alert_rules(system_id)

        def _rule(metric: str, severity: str | None = None) -> int | None:
            for item in rules:
                if item.get("metric") == metric and (severity is None or item.get("severity") == severity):
                    return int(item["id"])
            return None

        missing_required = [item["variable_name"] for item in baseline_variables if item["required"] and item["variable_code"] not in variable_map]
        if missing_required:
            alerts.append(
                {
                    "energy_system_id": system_id,
                    "monthly_measurement_id": measurement_id,
                    "baseline_model_id": int(baseline["id"]),
                    "ide_id": int(ide["id"]),
                    "alert_rule_id": _rule("missing_required_variable", "critical"),
                    "severity": "critical",
                    "message": f"Faltan variables requeridas: {', '.join(missing_required)}",
                    "value_detected": None,
                    "threshold_value": None,
                    "status": "open",
                    "created_at": _utcnow(),
                }
            )

        for item in baseline_variables:
            if item["variable_code"] not in variable_map:
                continue
            value = float(variable_map[item["variable_code"]])
            if item.get("min_value") is not None and value < float(item["min_value"]):
                alerts.append(
                    {
                        "energy_system_id": system_id,
                        "monthly_measurement_id": measurement_id,
                        "baseline_model_id": int(baseline["id"]),
                        "ide_id": int(ide["id"]),
                        "alert_rule_id": _rule("variable_out_of_range", "medium"),
                        "severity": "medium",
                        "message": f"{item['variable_name']} está bajo el mínimo permitido",
                        "value_detected": value,
                        "threshold_value": float(item["min_value"]),
                        "status": "open",
                        "created_at": _utcnow(),
                    }
                )
            if item.get("max_value") is not None and value > float(item["max_value"]):
                alerts.append(
                    {
                        "energy_system_id": system_id,
                        "monthly_measurement_id": measurement_id,
                        "baseline_model_id": int(baseline["id"]),
                        "ide_id": int(ide["id"]),
                        "alert_rule_id": _rule("variable_out_of_range", "high"),
                        "severity": "high",
                        "message": f"{item['variable_name']} está sobre el máximo permitido",
                        "value_detected": value,
                        "threshold_value": float(item["max_value"]),
                        "status": "open",
                        "created_at": _utcnow(),
                    }
                )

        if real_consumption <= 0:
            alerts.append(
                {
                    "energy_system_id": system_id,
                    "monthly_measurement_id": measurement_id,
                    "baseline_model_id": int(baseline["id"]),
                    "ide_id": int(ide["id"]),
                    "alert_rule_id": _rule("real_consumption", "critical"),
                    "severity": "critical",
                    "message": "El consumo real es cero o negativo",
                    "value_detected": real_consumption,
                    "threshold_value": 0,
                    "status": "open",
                    "created_at": _utcnow(),
                }
            )

        if percentage_difference is not None:
            abs_diff = abs(float(percentage_difference))
            if abs_diff > 20:
                alerts.append(
                    {
                        "energy_system_id": system_id,
                        "monthly_measurement_id": measurement_id,
                        "baseline_model_id": int(baseline["id"]),
                        "ide_id": int(ide["id"]),
                        "alert_rule_id": _rule("percentage_difference", "high"),
                        "severity": "high",
                        "message": "Desviación crítica superior al 20%",
                        "value_detected": percentage_difference,
                        "threshold_value": 20,
                        "status": "open",
                        "created_at": _utcnow(),
                    }
                )
            elif abs_diff > 10:
                alerts.append(
                    {
                        "energy_system_id": system_id,
                        "monthly_measurement_id": measurement_id,
                        "baseline_model_id": int(baseline["id"]),
                        "ide_id": int(ide["id"]),
                        "alert_rule_id": _rule("percentage_difference", "medium"),
                        "severity": "medium",
                        "message": "Desviación sobre 10% y requiere revisión",
                        "value_detected": percentage_difference,
                        "threshold_value": 10,
                        "status": "open",
                        "created_at": _utcnow(),
                    }
                )

        if ide_real is not None:
            if ide.get("expected_range_min") is not None and ide_real < float(ide["expected_range_min"]):
                alerts.append(
                    {
                        "energy_system_id": system_id,
                        "monthly_measurement_id": measurement_id,
                        "baseline_model_id": int(baseline["id"]),
                        "ide_id": int(ide["id"]),
                        "alert_rule_id": _rule("ide_out_of_range", "high"),
                        "severity": "high",
                        "message": "IDE real bajo el rango esperado",
                        "value_detected": ide_real,
                        "threshold_value": float(ide["expected_range_min"]),
                        "status": "open",
                        "created_at": _utcnow(),
                    }
                )
            if ide.get("expected_range_max") is not None and ide_real > float(ide["expected_range_max"]):
                alerts.append(
                    {
                        "energy_system_id": system_id,
                        "monthly_measurement_id": measurement_id,
                        "baseline_model_id": int(baseline["id"]),
                        "ide_id": int(ide["id"]),
                        "alert_rule_id": _rule("ide_out_of_range", "high"),
                        "severity": "high",
                        "message": "IDE real sobre el rango esperado",
                        "value_detected": ide_real,
                        "threshold_value": float(ide["expected_range_max"]),
                        "status": "open",
                        "created_at": _utcnow(),
                    }
                )

        return alerts

    def _audit(self, measurement_id: int, user_id: int | None, action: str, field_name: str | None, old_value: Any, new_value: Any, comment: str | None = None) -> dict[str, Any]:
        record = {
            "monthly_measurement_id": measurement_id,
            "user_id": user_id,
            "action": action,
            "field_name": field_name,
            "old_value": None if old_value is None else str(old_value),
            "new_value": None if new_value is None else str(new_value),
            "comment": comment,
            "created_at": _utcnow(),
        }
        return self._create("measurement_audit_log", record)

    def _next_id_for(self, table_name: str) -> int:
        rows = self._read(table_name)
        ids = [int(row["id"]) for row in rows if row.get("id") is not None]
        return (max(ids) if ids else 0) + 1

    def _sync_measurement_variables(self, measurement_id: int, baseline_variables: list[dict[str, Any]], variable_map: dict[str, float]) -> None:
        rows = [row for row in self._measurement_variables_rows() if int(row["monthly_measurement_id"]) != measurement_id]
        next_id = self._next_id_for("monthly_measurement_variables")
        for item in baseline_variables:
            code = item["variable_code"]
            if code not in variable_map:
                continue
            rows.append(
                {
                    "id": next_id,
                    "monthly_measurement_id": measurement_id,
                    "baseline_variable_id": int(item["id"]),
                    "variable_code": code,
                    "variable_name": item["variable_name"],
                    "value": variable_map[code],
                    "unit": item.get("unit"),
                    "created_at": _utcnow(),
                    "updated_at": _utcnow(),
                }
            )
            next_id += 1
        self._write("monthly_measurement_variables", rows)

    def _sync_alert_events(self, measurement_id: int, alerts: list[dict[str, Any]]) -> None:
        rows = [row for row in self._alert_events_rows() if int(row["monthly_measurement_id"]) != measurement_id]
        next_id = self._next_id_for("alert_events")
        normalized_alerts = []
        for alert in alerts:
            normalized = dict(alert)
            normalized.setdefault("id", next_id)
            next_id += 1
            normalized_alerts.append(normalized)
        rows.extend(normalized_alerts)
        self._write("alert_events", rows)

    def _measurement_response(self, measurement: dict[str, Any]) -> dict[str, Any]:
        payload = dict(measurement)
        payload["variables"] = self._measurement_variables_for(int(measurement["id"]))
        return payload

    def create_monthly_measurement(self, system_id: int, payload: MonthlyMeasurementCreateV2, user: User | None = None) -> dict[str, Any]:
        baseline, ide, use = self._validate_measurement_context(system_id, payload.baseline_model_id, payload.ide_id, payload.significant_energy_use_id)
        self._measurement_unique_check(system_id, payload.area_id, payload.significant_energy_use_id, payload.baseline_model_id, payload.year, payload.month)
        variable_map, baseline_variables = self._measurement_variable_map(payload.baseline_model_id, [item.model_dump() for item in payload.variables])
        required_codes = {item["variable_code"] for item in baseline_variables if item["required"]}
        if not required_codes.issubset(variable_map.keys()):
            missing = ", ".join(sorted(required_codes - variable_map.keys()))
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Faltan variables requeridas: {missing}")
        extra_codes = set(variable_map.keys()) - {item["variable_code"] for item in baseline_variables}
        if extra_codes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Variables no permitidas para la línea base: {', '.join(sorted(extra_codes))}")

        expected_consumption, ide_real, ide_expected, difference, percentage_difference, compliance_status = self._compute_measurement_metrics(
            baseline,
            ide,
            variable_map,
            payload.real_consumption,
        )

        measurement = self._create(
            "monthly_measurements",
            {
                "energy_system_id": system_id,
                "significant_energy_use_id": use["id"],
                "area_id": payload.area_id,
                "energy_use_id": payload.energy_use_id,
                "baseline_model_id": payload.baseline_model_id,
                "ide_id": payload.ide_id,
                "year": payload.year,
                "month": payload.month,
                "real_consumption": payload.real_consumption,
                "consumption_unit": payload.consumption_unit,
                "expected_consumption": expected_consumption,
                "ide_real": ide_real,
                "ide_expected": ide_expected,
                "difference": difference,
                "percentage_difference": percentage_difference,
                "compliance_status": compliance_status,
                "comments": payload.comments,
                "status": payload.status,
                "created_by": user.id if user else None,
                "created_at": _utcnow(),
                "updated_by": user.id if user else None,
                "updated_at": _utcnow(),
            },
        )
        self._sync_measurement_variables(int(measurement["id"]), baseline_variables, variable_map)
        self._audit(int(measurement["id"]), user.id if user else None, "created", None, None, None, "Creación de seguimiento mensual")
        alerts = self._detect_alerts(
            system_id=system_id,
            baseline=baseline,
            ide=ide,
            measurement_id=int(measurement["id"]),
            real_consumption=payload.real_consumption,
            percentage_difference=percentage_difference,
            ide_real=ide_real,
            variable_map=variable_map,
            baseline_variables=baseline_variables,
        )
        self._sync_alert_events(int(measurement["id"]), alerts)
        measurement = self._update("monthly_measurements", int(measurement["id"]), {"updated_at": _utcnow()})
        return self._measurement_response(measurement)

    def update_monthly_measurement(self, measurement_id: int, payload: MonthlyMeasurementUpdateV2, user: User | None = None) -> dict[str, Any]:
        measurement = self._get_measurement_row(measurement_id)
        if not measurement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medición no encontrada")
        update_data = payload.model_dump(exclude_unset=True)
        baseline_id = int(update_data.get("baseline_model_id", measurement["baseline_model_id"]))
        ide_id = int(update_data.get("ide_id", measurement["ide_id"]))
        use_id = int(update_data.get("significant_energy_use_id", measurement.get("significant_energy_use_id") or 0)) if (update_data.get("significant_energy_use_id") or measurement.get("significant_energy_use_id")) else None
        baseline, ide, use = self._validate_measurement_context(int(measurement["energy_system_id"]), baseline_id, ide_id, use_id)

        for field in ["significant_energy_use_id", "area_id", "energy_use_id", "baseline_model_id", "ide_id", "year", "month", "real_consumption", "consumption_unit", "comments", "status"]:
            if field in update_data and update_data[field] != measurement.get(field):
                self._audit(measurement_id, user.id if user else None, "updated", field, measurement.get(field), update_data[field], "Actualización de seguimiento mensual")
                measurement[field] = update_data[field]

        if "variables" in update_data and update_data["variables"] is not None:
            variable_map, baseline_variables = self._measurement_variable_map(baseline_id, update_data["variables"])
        else:
            baseline_variables = self.list_baseline_variables(baseline_id)
            variable_map = {item["variable_code"]: float(item["value"]) for item in self._measurement_variables_for(measurement_id)}

        expected_consumption, ide_real, ide_expected, difference, percentage_difference, compliance_status = self._compute_measurement_metrics(
            baseline,
            ide,
            variable_map,
            float(update_data.get("real_consumption", measurement["real_consumption"])),
        )
        measurement.update(
            {
                "expected_consumption": expected_consumption,
                "ide_real": ide_real,
                "ide_expected": ide_expected,
                "difference": difference,
                "percentage_difference": percentage_difference,
                "compliance_status": compliance_status,
                "updated_by": user.id if user else None,
                "updated_at": _utcnow(),
            }
        )
        self._write("monthly_measurements", [row if int(row["id"]) != measurement_id else measurement for row in self._measurement_rows()])
        self._sync_measurement_variables(measurement_id, baseline_variables, variable_map)
        self._sync_alert_events(
            measurement_id,
            self._detect_alerts(
                system_id=int(measurement["energy_system_id"]),
                baseline=baseline,
                ide=ide,
                measurement_id=measurement_id,
                real_consumption=float(measurement["real_consumption"]),
                percentage_difference=percentage_difference,
                ide_real=ide_real,
                variable_map=variable_map,
                baseline_variables=baseline_variables,
            ),
        )
        return self._measurement_response(measurement)

    def transition_measurement_status(self, measurement_id: int, status_value: str, user: User | None, comment: str | None = None) -> dict[str, Any]:
        measurement = self._get_measurement_row(measurement_id)
        if not measurement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medición no encontrada")
        old_status = measurement.get("status")
        measurement["status"] = status_value
        measurement["updated_by"] = user.id if user else None
        measurement["updated_at"] = _utcnow()
        self._audit(measurement_id, user.id if user else None, status_value, "status", old_status, status_value, comment or f"Cambio de estado a {status_value}")
        self._write("monthly_measurements", [row if int(row["id"]) != measurement_id else measurement for row in self._measurement_rows()])
        return self._measurement_response(measurement)

    def list_measurements(self, system_id: int, baseline_id: int | None = None, use_id: int | None = None, year: int | None = None, month: int | None = None) -> list[dict[str, Any]]:
        self._require_system(system_id)
        rows = self._filter("monthly_measurements", energy_system_id=system_id)
        if baseline_id is not None:
            rows = [item for item in rows if int(item["baseline_model_id"]) == baseline_id]
        if use_id is not None:
            rows = [item for item in rows if int(item.get("significant_energy_use_id") or 0) == use_id]
        if year is not None:
            rows = [item for item in rows if int(item["year"]) == year]
        if month is not None:
            rows = [item for item in rows if int(item["month"]) == month]
        rows = sorted(rows, key=lambda item: (int(item["year"]), int(item["month"])))
        return [self._measurement_response(item) for item in rows]

    def get_measurement(self, measurement_id: int) -> dict[str, Any] | None:
        measurement = self._get_measurement_row(measurement_id)
        if not measurement:
            return None
        return self._measurement_response(measurement)

    def list_measurement_alerts(self, measurement_id: int) -> list[dict[str, Any]]:
        return self._alerts_for(measurement_id)

    def list_measurement_audit_log(self, measurement_id: int) -> list[dict[str, Any]]:
        return self._audit_for(measurement_id)

    def list_system_alerts(self, system_id: int) -> list[dict[str, Any]]:
        self._require_system(system_id)
        rows = self._filter("alert_events", energy_system_id=system_id)
        return sorted(rows, key=lambda item: item.get("created_at") or datetime.min, reverse=True)

    # ------------------------------------------------------------------
    # Tracking and dashboard
    # ------------------------------------------------------------------
    def get_baseline_tracking(self, baseline_id: int) -> list[dict[str, Any]]:
        baseline = self.get_baseline(baseline_id)
        if not baseline:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Línea base no encontrada")
        rows = [item for item in self._read("monthly_measurements") if int(item["baseline_model_id"]) == baseline_id]
        rows = sorted(rows, key=lambda item: (int(item["year"]), int(item["month"])))
        return [
            {
                "id": item["id"],
                "year": item["year"],
                "month": item["month"],
                "real_consumption": item["real_consumption"],
                "expected_consumption": item.get("expected_consumption"),
                "ide_real": item.get("ide_real"),
                "ide_expected": item.get("ide_expected"),
                "difference": item.get("difference"),
                "percentage_difference": item.get("percentage_difference"),
                "compliance_status": item.get("compliance_status") or "incomplete",
                "status": item.get("status") or "draft",
                "comments": item.get("comments"),
            }
            for item in rows
        ]

    def get_tracking_for_use(self, use_id: int) -> list[dict[str, Any]]:
        use = self.get_significant_energy_use(use_id)
        if not use:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="USE no encontrado")
        rows = [item for item in self._read("monthly_measurements") if int(item.get("significant_energy_use_id") or 0) == use_id]
        rows = sorted(rows, key=lambda item: (int(item["year"]), int(item["month"])))
        return [
            {
                "id": item["id"],
                "year": item["year"],
                "month": item["month"],
                "real_consumption": item["real_consumption"],
                "expected_consumption": item.get("expected_consumption"),
                "ide_real": item.get("ide_real"),
                "ide_expected": item.get("ide_expected"),
                "difference": item.get("difference"),
                "percentage_difference": item.get("percentage_difference"),
                "compliance_status": item.get("compliance_status") or "incomplete",
                "status": item.get("status") or "draft",
                "comments": item.get("comments"),
            }
            for item in rows
        ]

    def get_system_tracking(self, system_id: int) -> list[dict[str, Any]]:
        self._require_system(system_id)
        rows = self.list_measurements(system_id)
        return [
            {
                "id": item["id"],
                "year": item["year"],
                "month": item["month"],
                "real_consumption": item["real_consumption"],
                "expected_consumption": item.get("expected_consumption"),
                "ide_real": item.get("ide_real"),
                "ide_expected": item.get("ide_expected"),
                "difference": item.get("difference"),
                "percentage_difference": item.get("percentage_difference"),
                "compliance_status": item.get("compliance_status") or "incomplete",
                "status": item.get("status") or "draft",
                "comments": item.get("comments"),
            }
            for item in rows
        ]

    def get_tracking_summary(self, system_id: int) -> dict[str, Any]:
        measurements = self.list_measurements(system_id)
        total = len(measurements)
        compliant = sum(1 for item in measurements if item.get("compliance_status") == "compliant")
        warning = sum(1 for item in measurements if item.get("compliance_status") == "warning")
        non_compliant = sum(1 for item in measurements if item.get("compliance_status") == "non_compliant")
        incomplete = sum(1 for item in measurements if item.get("compliance_status") == "incomplete")
        avg_diff = round(sum(abs(float(item.get("percentage_difference") or 0)) for item in measurements) / total, 2) if total else 0.0
        open_alerts = sum(1 for item in self.list_system_alerts(system_id) if item.get("status") == "open")
        return {
            "total_measurements": total,
            "compliant": compliant,
            "warning": warning,
            "non_compliant": non_compliant,
            "incomplete": incomplete,
            "average_percentage_difference": avg_diff,
            "open_alerts": open_alerts,
        }

    def get_dashboard_response(self, system_id: int) -> dict[str, Any]:
        rows = self.list_measurements(system_id)
        if not rows:
            return {
                "kpis": {"real_consumption": 0, "expected_consumption": 0, "percentage_difference": 0, "open_alerts": 0},
                "real_vs_expected": [],
                "ide_trend": [],
                "recent_alerts": [],
            }
        latest = rows[-12:]
        real = sum(float(item["real_consumption"]) for item in latest)
        expected = sum(float(item.get("expected_consumption") or 0) for item in latest)
        diff = calculate_percentage_difference(calculate_difference(real, expected), expected) or 0
        alerts = self.list_system_alerts(system_id)[:5]
        return {
            "kpis": {
                "real_consumption": round(real, 2),
                "expected_consumption": round(expected, 2),
                "percentage_difference": round(diff, 2),
                "open_alerts": sum(1 for item in self.list_system_alerts(system_id) if item.get("status") == "open"),
            },
            "real_vs_expected": [
                {
                    "month": item["month"],
                    "real_consumption": item["real_consumption"],
                    "expected_consumption": item.get("expected_consumption") or 0,
                    "ide_real": item.get("ide_real"),
                    "ide_expected": item.get("ide_expected"),
                }
                for item in latest
            ],
            "ide_trend": [
                {
                    "month": item["month"],
                    "real_consumption": item["real_consumption"],
                    "expected_consumption": item.get("expected_consumption") or 0,
                    "ide_real": item.get("ide_real"),
                    "ide_expected": item.get("ide_expected"),
                }
                for item in latest
            ],
            "recent_alerts": [
                {
                    "id": item["id"],
                    "severity": item["severity"],
                    "message": item["message"],
                    "status": item["status"],
                    "created_at": item["created_at"],
                }
                for item in alerts
            ],
        }

    def get_performance_summary(self, system_id: int) -> dict[str, Any]:
        summary = self.get_tracking_summary(system_id)
        total = summary["total_measurements"] or 1
        return {
            **summary,
            "compliance_rate": round((summary["compliant"] / total) * 100, 2),
        }

    def get_monthly_trends(self, system_id: int) -> list[dict[str, Any]]:
        rows = self.list_measurements(system_id)
        return [
            {
                "month": item["month"],
                "real_consumption": item["real_consumption"],
                "expected_consumption": item.get("expected_consumption") or 0,
                "ide_real": item.get("ide_real"),
                "ide_expected": item.get("ide_expected"),
            }
            for item in rows
        ]

    def _raise_not_found(self, detail: str) -> None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------
    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        if self._is_csv:
            users = self._filter("users", username=username)
            return users[0] if users else None
        assert self.db is not None
        user = self.db.query(User).filter(User.username == username).one_or_none()
        if not user:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "active": user.active,
        }

    def authenticate_user(self, username: str, password: str) -> dict[str, Any] | None:
        user = self.get_user_by_username(username)
        if not user or not user.get("active", False):
            return None
        if self._is_csv:
            return user
        assert self.db is not None
        from app.services.auth_service import authenticate_user as authenticate_user_sqlalchemy

        authenticated = authenticate_user_sqlalchemy(self.db, username, password)
        if not authenticated:
            return None
        return {
            "id": authenticated.id,
            "username": authenticated.username,
            "full_name": authenticated.full_name,
            "email": authenticated.email,
            "role": authenticated.role,
            "active": authenticated.active,
        }
