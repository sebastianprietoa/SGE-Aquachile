from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_data_backend_service
from app.schemas.energy_v2 import (
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
from app.services.data_backend_service import DataBackendService

router = APIRouter(tags=["energy-management"])


@router.get("/systems/{system_id}/energy-use-base-year", response_model=list[EnergyUseBaseYearRead])
def get_energy_use_base_year(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[EnergyUseBaseYearRead]:
    return service.list_energy_use_base_year(system_id)


@router.get("/systems/{system_id}/energy-use-base-year/pareto", response_model=list[ParetoItem])
def get_energy_use_base_year_pareto(
    system_id: int,
    year: int | None = Query(default=None, ge=1900),
    service: DataBackendService = Depends(get_data_backend_service),
) -> list[ParetoItem]:
    return service.pareto_energy_use_base_year(system_id, year=year)


@router.post("/systems/{system_id}/energy-use-base-year", response_model=EnergyUseBaseYearRead)
def post_energy_use_base_year(system_id: int, payload: EnergyUseBaseYearCreate, service: DataBackendService = Depends(get_data_backend_service)) -> EnergyUseBaseYearRead:
    return service.create_energy_use_base_year(system_id, payload)


@router.get("/systems/{system_id}/significant-energy-uses", response_model=list[SignificantEnergyUseRead])
def get_significant_energy_uses(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[SignificantEnergyUseRead]:
    return service.list_significant_energy_uses(system_id)


@router.get("/significant-energy-uses/{use_id}", response_model=SignificantEnergyUseRead)
def get_significant_energy_use(use_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> SignificantEnergyUseRead:
    record = service.get_significant_energy_use(use_id)
    if not record:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="USE no encontrado")
    return record


@router.post("/systems/{system_id}/significant-energy-uses", response_model=SignificantEnergyUseRead)
def post_significant_energy_use(system_id: int, payload: SignificantEnergyUseCreate, service: DataBackendService = Depends(get_data_backend_service)) -> SignificantEnergyUseRead:
    return service.create_significant_energy_use(system_id, payload)


@router.put("/significant-energy-uses/{use_id}", response_model=SignificantEnergyUseRead)
def put_significant_energy_use(use_id: int, payload: SignificantEnergyUseUpdate, service: DataBackendService = Depends(get_data_backend_service)) -> SignificantEnergyUseRead:
    return service.update_significant_energy_use(use_id, payload)


@router.get("/systems/{system_id}/baselines", response_model=list[BaselineModelReadV2])
def get_baselines(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[BaselineModelReadV2]:
    return service.list_baselines(system_id)


@router.get("/baselines/{baseline_id}", response_model=BaselineModelReadV2)
def get_baseline_route(baseline_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> BaselineModelReadV2:
    record = service.get_baseline(baseline_id)
    if not record:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Línea base no encontrada")
    return record


@router.post("/systems/{system_id}/baselines", response_model=BaselineModelReadV2)
def post_baseline(system_id: int, payload: BaselineModelBaseV2, service: DataBackendService = Depends(get_data_backend_service)) -> BaselineModelReadV2:
    return service.create_baseline_model(system_id, payload)


@router.put("/baselines/{baseline_id}", response_model=BaselineModelReadV2)
def put_baseline(baseline_id: int, payload: BaselineModelUpdateV2, service: DataBackendService = Depends(get_data_backend_service)) -> BaselineModelReadV2:
    return service.update_baseline_model(baseline_id, payload)


@router.get("/baselines/{baseline_id}/variables", response_model=list[BaselineVariableReadV2])
def get_baseline_variables(baseline_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[BaselineVariableReadV2]:
    return service.list_baseline_variables(baseline_id)


@router.post("/baselines/{baseline_id}/variables", response_model=BaselineVariableReadV2)
def post_baseline_variable(baseline_id: int, payload: BaselineVariableCreateV2, service: DataBackendService = Depends(get_data_backend_service)) -> BaselineVariableReadV2:
    return service.create_baseline_variable(baseline_id, payload)


@router.put("/baseline-variables/{variable_id}", response_model=BaselineVariableReadV2)
def put_baseline_variable(variable_id: int, payload: BaselineVariableUpdateV2, service: DataBackendService = Depends(get_data_backend_service)) -> BaselineVariableReadV2:
    return service.update_baseline_variable(variable_id, payload)


@router.get("/baselines/{baseline_id}/tracking", response_model=list[TrackingMonthlyRow])
def get_baseline_tracking_route(baseline_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[TrackingMonthlyRow]:
    return service.get_baseline_tracking(baseline_id)


@router.get("/systems/{system_id}/tracking", response_model=list[TrackingMonthlyRow])
def get_system_tracking_route(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[TrackingMonthlyRow]:
    return service.get_system_tracking(system_id)


@router.get("/systems/{system_id}/tracking/summary", response_model=TrackingSummary)
def get_system_tracking_summary_route(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> TrackingSummary:
    return service.get_tracking_summary(system_id)


@router.get("/significant-energy-uses/{use_id}/tracking", response_model=list[TrackingMonthlyRow])
def get_use_tracking_route(use_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[TrackingMonthlyRow]:
    return service.get_tracking_for_use(use_id)


@router.get("/systems/{system_id}/ides", response_model=list[IdeDefinitionReadV2])
def get_ides(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[IdeDefinitionReadV2]:
    return service.list_ides(system_id)


@router.get("/ides/{ide_id}", response_model=IdeDefinitionReadV2)
def get_ide_route(ide_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> IdeDefinitionReadV2:
    record = service.get_ide(ide_id)
    if not record:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="IDE no encontrado")
    return record


@router.post("/systems/{system_id}/ides", response_model=IdeDefinitionReadV2)
def post_ide(system_id: int, payload: IdeDefinitionCreateV2, service: DataBackendService = Depends(get_data_backend_service)) -> IdeDefinitionReadV2:
    return service.create_ide(system_id, payload)


@router.put("/ides/{ide_id}", response_model=IdeDefinitionReadV2)
def put_ide(ide_id: int, payload: IdeDefinitionUpdateV2, service: DataBackendService = Depends(get_data_backend_service)) -> IdeDefinitionReadV2:
    return service.update_ide(ide_id, payload)


@router.get("/systems/{system_id}/data-collection-plan", response_model=list[DataCollectionPlanItem])
def get_data_collection_plan(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[DataCollectionPlanItem]:
    return service.list_data_collection_plan(system_id)


@router.get("/baselines/{baseline_id}/data-collection-plan", response_model=list[DataCollectionPlanItem])
def get_baseline_data_collection_plan(baseline_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[DataCollectionPlanItem]:
    baseline = service.get_baseline(baseline_id)
    if not baseline:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Línea base no encontrada")
    variables = service.list_baseline_variables(baseline_id)
    use = service.get_significant_energy_use(int(baseline["significant_energy_use_id"])) if baseline.get("significant_energy_use_id") else None
    use_name = use.get("name") if use else baseline.get("name")
    return [
        {
            "variable_name": item["variable_name"],
            "variable_code": item["variable_code"],
            "use_name": use_name,
            "baseline_name": baseline.get("name"),
            "what_is_measured": item.get("measurement_reason"),
            "why_it_is_measured": item.get("measurement_reason"),
            "collection_method": item.get("collection_method"),
            "storage_location": item.get("storage_location"),
            "responsible_area": item.get("responsible_area"),
            "responsible_person": item.get("responsible_person"),
            "frequency": item.get("frequency"),
            "missing_data_procedure": item.get("missing_data_procedure"),
            "min_value": item.get("min_value"),
            "max_value": item.get("max_value"),
            "active": item.get("active", True),
        }
        for item in variables
    ]


@router.get("/systems/{system_id}/operational-controls", response_model=list[OperationalControlRead])
def get_operational_controls(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[OperationalControlRead]:
    return service.list_operational_controls(system_id)


@router.get("/significant-energy-uses/{use_id}/operational-controls", response_model=list[OperationalControlRead])
def get_use_operational_controls(use_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[OperationalControlRead]:
    return service.get_use_operational_controls(use_id)


@router.post("/significant-energy-uses/{use_id}/operational-controls", response_model=OperationalControlRead)
def post_use_operational_control(use_id: int, payload: OperationalControlCreate, service: DataBackendService = Depends(get_data_backend_service)) -> OperationalControlRead:
    use = service.get_significant_energy_use(use_id)
    if not use:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="USE no encontrado")
    return service.create_operational_control(int(use["energy_system_id"]), payload.model_copy(update={"significant_energy_use_id": use_id}))


@router.put("/operational-controls/{control_id}", response_model=OperationalControlRead)
def put_operational_control(control_id: int, payload: OperationalControlUpdate, service: DataBackendService = Depends(get_data_backend_service)) -> OperationalControlRead:
    return service.update_operational_control(control_id, payload)


@router.get("/systems/{system_id}/equipment-characterization", response_model=list[dict])
def get_equipment_characterization(system_id: int, service: DataBackendService = Depends(get_data_backend_service)) -> list[dict]:
    return service.list_equipment_characterization(system_id)
