"use client";

import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type {
  BaselineModelV2,
  BaselineVariableV2,
  EnergyArea,
  EnergySystem,
  EnergyUse,
  IdeDefinitionV2,
  MonthlyMeasurementV2,
  SignificantEnergyUse,
} from "@/types/api";

type WizardStep = 1 | 2 | 3 | 4 | 5;

function calculatePreview(
  baseline: BaselineModelV2 | null,
  ide: IdeDefinitionV2 | null,
  variables: BaselineVariableV2[],
  values: Record<number, string>,
  realConsumption: string,
) {
  if (!baseline || !ide) {
    return null;
  }

  const numericValues: Record<string, number> = {};
  const missingRequired: string[] = [];

  for (const variable of variables) {
    const raw = values[variable.id];
    if (raw === "" || raw === undefined) {
      if (variable.required) missingRequired.push(variable.variable_name);
      continue;
    }
    numericValues[variable.variable_code] = Number(raw);
  }

  const consumption = Number(realConsumption || 0);
  const coefficients = baseline.coefficients ?? {};
  const allRequiredPresent = missingRequired.length === 0;
  const expected =
    allRequiredPresent && Object.keys(coefficients).every((code) => numericValues[code] !== undefined)
      ? Object.entries(coefficients).reduce((total, [code, coefficient]) => total + Number(coefficient) * Number(numericValues[code] ?? 0), Number(baseline.intercept ?? 0))
      : null;
  const denominator = ide.denominator ? numericValues[ide.denominator] : undefined;
  const ideReal = denominator ? consumption / denominator : null;
  const ideExpected = expected !== null && denominator ? expected / denominator : null;
  const difference = expected !== null ? consumption - expected : null;
  const percentageDifference = expected && difference !== null ? (difference / expected) * 100 : null;
  const absoluteDifference = Math.abs(percentageDifference ?? 0);
  const status =
    !allRequiredPresent || expected === null || consumption <= 0
      ? "incomplete"
      : absoluteDifference <= 10
        ? "compliant"
        : absoluteDifference <= 20
          ? "warning"
          : "non_compliant";

  const alerts: string[] = [];
  if (!allRequiredPresent) alerts.push("Datos incompletos");
  if (consumption <= 0) alerts.push("Consumo real cero o negativo");
  if (percentageDifference !== null && absoluteDifference > 20) alerts.push("Desviación crítica");
  if (percentageDifference !== null && absoluteDifference > 10 && absoluteDifference <= 20) alerts.push("Desviación moderada");
  if (ide.expected_range_min != null && ideReal !== null && ideReal < ide.expected_range_min) alerts.push("IDE bajo mínimo");
  if (ide.expected_range_max != null && ideReal !== null && ideReal > ide.expected_range_max) alerts.push("IDE sobre máximo");

  return { expected, ideReal, ideExpected, difference, percentageDifference, status, alerts, missingRequired };
}

export function DynamicMeasurementForm({
  systemId: forcedSystemId,
  measurementId,
}: {
  systemId?: number;
  measurementId?: number;
}) {
  const [systems, setSystems] = useState<EnergySystem[]>([]);
  const [areas, setAreas] = useState<EnergyArea[]>([]);
  const [uses, setUses] = useState<EnergyUse[]>([]);
  const [significantUses, setSignificantUses] = useState<SignificantEnergyUse[]>([]);
  const [baselines, setBaselines] = useState<BaselineModelV2[]>([]);
  const [ides, setIdes] = useState<IdeDefinitionV2[]>([]);
  const [baselineVariables, setBaselineVariables] = useState<BaselineVariableV2[]>([]);
  const [measurement, setMeasurement] = useState<MonthlyMeasurementV2 | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [step, setStep] = useState<WizardStep>(1);
  const [selectedSystemId, setSelectedSystemId] = useState<number | null>(forcedSystemId ?? null);
  const [selectedAreaId, setSelectedAreaId] = useState<number | null>(null);
  const [selectedUseId, setSelectedUseId] = useState<number | null>(null);
  const [selectedSignificantUseId, setSelectedSignificantUseId] = useState<number | null>(null);
  const [selectedBaselineId, setSelectedBaselineId] = useState<number | null>(null);
  const [selectedIdeId, setSelectedIdeId] = useState<number | null>(null);
  const [selectedYear, setSelectedYear] = useState("2025");
  const [selectedMonth, setSelectedMonth] = useState("1");
  const [realConsumption, setRealConsumption] = useState("0");
  const [consumptionUnit, setConsumptionUnit] = useState("kWh");
  const [comments, setComments] = useState("");
  const [status, setStatus] = useState<"draft" | "submitted" | "reviewed" | "approved" | "rejected">("draft");
  const [variableValues, setVariableValues] = useState<Record<number, string>>({});

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const systemItems = await api.systems();
        if (!active) return;
        setSystems(systemItems);
        setSelectedSystemId((current) => current ?? forcedSystemId ?? systemItems[0]?.id ?? null);
        if (measurementId) {
          const current = await api.measurement(measurementId);
          if (!active) return;
          setMeasurement(current as MonthlyMeasurementV2);
          setSelectedSystemId(current.energy_system_id);
          setSelectedAreaId(current.area_id);
          setSelectedUseId(current.energy_use_id);
          setSelectedSignificantUseId(current.significant_energy_use_id ?? null);
          setSelectedBaselineId(current.baseline_model_id);
          setSelectedIdeId(current.ide_id);
          setSelectedYear(String(current.year));
          setSelectedMonth(String(current.month));
          setRealConsumption(String(current.real_consumption));
          setConsumptionUnit(current.consumption_unit);
          setComments(current.comments ?? "");
          setStatus(current.status as typeof status);
        }
      } catch (error) {
        setMessage(error instanceof Error ? error.message : "No fue posible cargar el formulario");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [forcedSystemId, measurementId]);

  useEffect(() => {
    if (!selectedSystemId) return;
    let active = true;
    Promise.all([api.areas(selectedSystemId), api.energyUses(selectedSystemId), api.significantEnergyUses(selectedSystemId), api.baselines(selectedSystemId), api.ides(selectedSystemId)])
      .then(([areaItems, useItems, significantUseItems, baselineItems, ideItems]) => {
        if (!active) return;
        setAreas(areaItems);
        setUses(useItems);
        setSignificantUses(significantUseItems);
        setBaselines(baselineItems);
        setIdes(ideItems);
        if (!selectedAreaId) setSelectedAreaId(areaItems[0]?.id ?? null);
        if (!selectedUseId) setSelectedUseId(useItems[0]?.id ?? null);
        if (!selectedSignificantUseId) setSelectedSignificantUseId(significantUseItems[0]?.id ?? null);
        if (!selectedBaselineId) setSelectedBaselineId(baselineItems[0]?.id ?? null);
        if (!selectedIdeId) setSelectedIdeId(ideItems[0]?.id ?? null);
      })
      .catch((error) => setMessage(error instanceof Error ? error.message : "No fue posible cargar el contexto"));
    return () => {
      active = false;
    };
  }, [selectedSystemId]);

  useEffect(() => {
    if (!selectedBaselineId) {
      setBaselineVariables([]);
      return;
    }
    api.baselineVariables(selectedBaselineId)
      .then((items) => {
        setBaselineVariables(items);
        if (measurement) {
          const values: Record<number, string> = {};
          measurement.variables.forEach((variable) => {
            values[variable.baseline_variable_id] = String(variable.value);
          });
          setVariableValues(values);
        } else {
          setVariableValues({});
        }
      })
      .catch((error) => setMessage(error instanceof Error ? error.message : "No fue posible cargar las variables"));
  }, [measurement, selectedBaselineId]);

  const selectedSystem = useMemo(() => systems.find((item) => item.id === selectedSystemId) ?? null, [selectedSystemId, systems]);
  const selectedBaseline = useMemo(() => baselines.find((item) => item.id === selectedBaselineId) ?? null, [baselines, selectedBaselineId]);
  const selectedIde = useMemo(() => ides.find((item) => item.id === selectedIdeId) ?? null, [ides, selectedIdeId]);
  const preview = useMemo(
    () => calculatePreview(selectedBaseline, selectedIde, baselineVariables, variableValues, realConsumption),
    [baselineVariables, realConsumption, selectedBaseline, selectedIde, variableValues],
  );

  async function save(nextStatus: typeof status) {
    if (!selectedSystemId || !selectedAreaId || !selectedUseId || !selectedSignificantUseId || !selectedBaseline || !selectedIde) {
      setMessage("Faltan datos de contexto para guardar");
      return;
    }

    const payload = {
      significant_energy_use_id: selectedSignificantUseId,
      area_id: selectedAreaId,
      energy_use_id: selectedUseId,
      baseline_model_id: selectedBaseline.id,
      ide_id: selectedIde.id,
      year: Number(selectedYear),
      month: Number(selectedMonth),
      real_consumption: Number(realConsumption),
      consumption_unit: consumptionUnit,
      comments,
      status: nextStatus,
      variables: baselineVariables.map((variable) => ({
        baseline_variable_id: variable.id,
        variable_code: variable.variable_code,
        value: Number(variableValues[variable.id] ?? 0),
      })),
    };

    try {
      if (measurementId) {
        await api.updateMeasurement(measurementId, payload);
        setMessage("Medición actualizada");
      } else {
        await api.createMeasurement(selectedSystemId, payload);
        setMessage("Medición creada");
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No fue posible guardar la medición");
    }
  }

  if (loading) {
    return (
      <Card className="border-slate-200 bg-white shadow-sm">
        <CardContent className="p-6 text-slate-600">Cargando formulario...</CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card className="border-slate-200 bg-white shadow-sm">
        <CardHeader>
          <CardTitle className="font-heading text-2xl text-slate-900">
            {measurementId ? "Editar registro mensual" : "Nuevo registro mensual"}
          </CardTitle>
          <CardDescription className="text-slate-600">
            El formulario se arma desde la línea base seleccionada y solo permite variables definidas por su modelo.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex flex-wrap gap-2">
            {[1, 2, 3, 4, 5].map((item) => (
              <Badge key={item} variant={step === item ? "default" : "secondary"}>
                Paso {item}
              </Badge>
            ))}
          </div>

          {step === 1 ? (
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {!forcedSystemId ? (
                <Select
                  value={selectedSystemId ? String(selectedSystemId) : ""}
                  onChange={(event) => {
                    const nextSystemId = Number(event.target.value);
                    setSelectedSystemId(nextSystemId);
                    setSelectedAreaId(null);
                    setSelectedUseId(null);
                    setSelectedSignificantUseId(null);
                    setSelectedBaselineId(null);
                    setSelectedIdeId(null);
                    setBaselineVariables([]);
                    setVariableValues({});
                  }}
                >
                  {systems.map((system) => (
                    <option key={system.id} value={system.id}>
                      {system.code} - {system.name}
                    </option>
                  ))}
                </Select>
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                  {selectedSystem?.code ?? "--"} - {selectedSystem?.name ?? "--"}
                </div>
              )}
              <Select value={selectedAreaId ? String(selectedAreaId) : ""} onChange={(event) => setSelectedAreaId(Number(event.target.value))}>
                <option value="">Área</option>
                {areas.map((area) => (
                  <option key={area.id} value={area.id}>
                    {area.name}
                  </option>
                ))}
              </Select>
              <Select value={selectedUseId ? String(selectedUseId) : ""} onChange={(event) => setSelectedUseId(Number(event.target.value))}>
                <option value="">Uso energético</option>
                {uses.map((energyUse) => (
                  <option key={energyUse.id} value={energyUse.id}>
                    {energyUse.name}
                  </option>
                ))}
              </Select>
              <Select value={selectedSignificantUseId ? String(selectedSignificantUseId) : ""} onChange={(event) => setSelectedSignificantUseId(Number(event.target.value))}>
                <option value="">USE</option>
                {significantUses.map((use) => (
                  <option key={use.id} value={use.id}>
                    {use.name}
                  </option>
                ))}
              </Select>
              <Select value={selectedBaselineId ? String(selectedBaselineId) : ""} onChange={(event) => setSelectedBaselineId(Number(event.target.value))}>
                <option value="">Línea base</option>
                {baselines.map((baseline) => (
                  <option key={baseline.id} value={baseline.id}>
                    {baseline.name}
                  </option>
                ))}
              </Select>
              <Select value={selectedIdeId ? String(selectedIdeId) : ""} onChange={(event) => setSelectedIdeId(Number(event.target.value))}>
                <option value="">IDE</option>
                {ides.map((ide) => (
                  <option key={ide.id} value={ide.id}>
                    {ide.ide_name}
                  </option>
                ))}
              </Select>
              <Input value={selectedYear} onChange={(event) => setSelectedYear(event.target.value)} placeholder="Año" />
              <Input value={selectedMonth} onChange={(event) => setSelectedMonth(event.target.value)} placeholder="Mes" />
            </div>
          ) : null}

          {step === 2 ? (
            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="real_consumption">Consumo real</Label>
                <Input id="real_consumption" value={realConsumption} onChange={(event) => setRealConsumption(event.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="consumption_unit">Unidad</Label>
                <Input id="consumption_unit" value={consumptionUnit} onChange={(event) => setConsumptionUnit(event.target.value)} />
              </div>
            </div>
          ) : null}

          {step === 3 ? (
            <div className="grid gap-4">
              {baselineVariables.map((variable) => {
                const currentValue = variableValues[variable.id] ?? "";
                const outOfRange =
                  currentValue !== "" &&
                  ((variable.min_value !== null && variable.min_value !== undefined && Number(currentValue) < variable.min_value) ||
                    (variable.max_value !== null && variable.max_value !== undefined && Number(currentValue) > variable.max_value));
                return (
                  <div key={variable.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="font-medium text-slate-900">
                          {variable.variable_name} {variable.required ? "*" : ""}
                        </p>
                        <p className="text-sm text-slate-500">
                          {variable.description ?? "Sin descripción"} {variable.unit ? `· ${variable.unit}` : ""}
                        </p>
                      </div>
                      <Badge variant={variable.required ? "destructive" : "secondary"}>{variable.variable_code}</Badge>
                    </div>
                    <div className="mt-3 grid gap-3 md:grid-cols-[1fr_220px]">
                      <Input
                        value={currentValue}
                        onChange={(event) => setVariableValues((state) => ({ ...state, [variable.id]: event.target.value }))}
                        placeholder={`Valor para ${variable.variable_name}`}
                      />
                      <div className={`rounded-xl border px-3 py-2 text-sm ${outOfRange ? "border-amber-300 bg-amber-50 text-amber-900" : "border-slate-200 bg-white text-slate-600"}`}>
                        Rango: {variable.min_value ?? "sin mínimo"} - {variable.max_value ?? "sin máximo"}
                        <div className="mt-1 text-xs text-slate-500">{variable.missing_data_procedure ?? "Dato faltante: revisar plan de recopilación."}</div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : null}

          {step === 4 ? (
            <div className="grid gap-4 xl:grid-cols-2">
              <div className="space-y-3">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">Consumo esperado</p>
                  <p className="font-heading text-2xl text-slate-900">{preview?.expected !== null && preview?.expected !== undefined ? preview.expected.toFixed(2) : "--"}</p>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">IDE real / esperado</p>
                  <p className="font-heading text-2xl text-slate-900">
                    {preview?.ideReal?.toFixed(2) ?? "--"} / {preview?.ideExpected?.toFixed(2) ?? "--"}
                  </p>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">Desviación</p>
                  <p className="font-heading text-2xl text-slate-900">
                    {preview?.difference?.toFixed(2) ?? "--"} ({preview?.percentageDifference?.toFixed(2) ?? "--"}%)
                  </p>
                </div>
              </div>
              <div className="space-y-3">
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">Estado de cumplimiento</p>
                  <Badge variant={preview?.status === "compliant" ? "success" : preview?.status === "warning" ? "warning" : preview?.status === "non_compliant" ? "destructive" : "secondary"}>
                    {preview?.status ?? "incomplete"}
                  </Badge>
                </div>
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">Alertas preliminares</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {preview?.alerts.length ? preview.alerts.map((alert) => <Badge key={alert} variant="destructive">{alert}</Badge>) : <Badge variant="secondary">Sin alertas</Badge>}
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          {step === 5 ? (
            <div className="space-y-4">
              <Textarea value={comments} onChange={(event) => setComments(event.target.value)} placeholder="Comentarios o antecedentes" />
              <div className="flex flex-wrap gap-3">
                <Button variant="secondary" onClick={() => save("draft")}>Guardar borrador</Button>
                <Button onClick={() => save("submitted")}>Enviar a revisión</Button>
              </div>
            </div>
          ) : null}

          <div className="flex flex-wrap gap-3 pt-2">
            <Button variant="secondary" disabled={step === 1} onClick={() => setStep((current) => Math.max(1, current - 1) as WizardStep)}>
              Anterior
            </Button>
            <Button variant="secondary" disabled={step === 5} onClick={() => setStep((current) => Math.min(5, current + 1) as WizardStep)}>
              Siguiente
            </Button>
          </div>

          {message ? <p className="text-sm text-slate-600">{message}</p> : null}
        </CardContent>
      </Card>
    </div>
  );
}
