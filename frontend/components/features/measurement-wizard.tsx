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
import type { BaselineModel, BaselineVariable, EnergyArea, EnergySystem, EnergyUse, IdeDefinition, MonthlyMeasurement } from "@/types/api";

type WizardMode = "create" | "edit";

function calculatePreview(
  baseline: BaselineModel | null,
  ide: IdeDefinition | null,
  baselineVariables: BaselineVariable[],
  variableValues: Record<number, string>,
  realConsumption: string,
) {
  if (!baseline || !ide) {
    return null;
  }
  const numericValues: Record<string, number> = {};
  const missingRequired: string[] = [];
  baselineVariables.forEach((variable) => {
    const raw = variableValues[variable.id];
    if (raw === "" || raw === undefined) {
      if (variable.required) missingRequired.push(variable.variable_name);
      return;
    }
    numericValues[variable.variable_code] = Number(raw);
  });
  const consumption = Number(realConsumption || 0);
  const allRequiredPresent = missingRequired.length === 0;
  const coefficients = baseline.coefficients ?? {};
  const expected = allRequiredPresent
    ? Object.entries(coefficients).reduce((total, [code, coefficient]) => total + coefficient * (numericValues[code] ?? 0), baseline.intercept)
    : null;
  const denominator = ide.denominator ? numericValues[ide.denominator] : undefined;
  const ideReal = denominator ? consumption / denominator : null;
  const ideExpected = expected !== null && denominator ? expected / denominator : null;
  const difference = expected !== null ? consumption - expected : null;
  const percentageDifference = expected && difference !== null ? (difference / expected) * 100 : null;
  const status = !allRequiredPresent || expected === null || consumption <= 0 ? "incomplete" : Math.abs(percentageDifference ?? 0) <= 10 ? "compliant" : Math.abs(percentageDifference ?? 0) <= 20 ? "warning" : "non_compliant";
  const alerts: string[] = [];
  if (!allRequiredPresent) alerts.push("Datos incompletos");
  if (consumption <= 0) alerts.push("Consumo real cero o negativo");
  if (percentageDifference !== null && Math.abs(percentageDifference) > 20) alerts.push("Desviación crítica");
  if (percentageDifference !== null && Math.abs(percentageDifference) > 10 && Math.abs(percentageDifference) <= 20) alerts.push("Desviación moderada");
  if (ide.expected_range_min != null && ideReal !== null && ideReal < ide.expected_range_min) alerts.push("IDE bajo mínimo");
  if (ide.expected_range_max != null && ideReal !== null && ideReal > ide.expected_range_max) alerts.push("IDE sobre máximo");
  return { expected, ideReal, ideExpected, difference, percentageDifference, status, alerts, missingRequired };
}

export function MeasurementWizard({
  mode,
  measurementId,
}: {
  mode: WizardMode;
  measurementId?: number;
}) {
  const [systems, setSystems] = useState<EnergySystem[]>([]);
  const [areas, setAreas] = useState<EnergyArea[]>([]);
  const [uses, setUses] = useState<EnergyUse[]>([]);
  const [baselines, setBaselines] = useState<BaselineModel[]>([]);
  const [ides, setIdes] = useState<IdeDefinition[]>([]);
  const [baselineVariables, setBaselineVariables] = useState<BaselineVariable[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [step, setStep] = useState(1);
  const [selectedSystemId, setSelectedSystemId] = useState<number | null>(null);
  const [selectedAreaId, setSelectedAreaId] = useState<number | null>(null);
  const [selectedUseId, setSelectedUseId] = useState<number | null>(null);
  const [selectedBaselineId, setSelectedBaselineId] = useState<number | null>(null);
  const [selectedIdeId, setSelectedIdeId] = useState<number | null>(null);
  const [selectedYear, setSelectedYear] = useState("2025");
  const [selectedMonth, setSelectedMonth] = useState("1");
  const [realConsumption, setRealConsumption] = useState("0");
  const [consumptionUnit, setConsumptionUnit] = useState("kWh");
  const [comments, setComments] = useState("");
  const [status, setStatus] = useState<"draft" | "submitted" | "reviewed" | "approved" | "rejected">("draft");
  const [variableValues, setVariableValues] = useState<Record<number, string>>({});
  const [editMeasurement, setEditMeasurement] = useState<MonthlyMeasurement | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const systemItems = await api.systems();
        setSystems(systemItems);
        const system = systemItems[0] ?? null;
        if (system) {
          setSelectedSystemId(system.id);
        }
        if (measurementId) {
          const measurement = await api.measurement(measurementId);
          setEditMeasurement(measurement);
          setSelectedSystemId(measurement.energy_system_id);
          setSelectedAreaId(measurement.area_id);
          setSelectedUseId(measurement.energy_use_id);
          setSelectedBaselineId(measurement.baseline_model_id);
          setSelectedIdeId(measurement.ide_id);
          setSelectedYear(String(measurement.year));
          setSelectedMonth(String(measurement.month));
          setRealConsumption(String(measurement.real_consumption));
          setConsumptionUnit(measurement.consumption_unit);
          setComments(measurement.comments ?? "");
          setStatus(measurement.status as typeof status);
        }
      } catch (error) {
        setMessage(error instanceof Error ? error.message : "No fue posible cargar el formulario");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [measurementId]);

  useEffect(() => {
    if (!selectedSystemId) return;
    Promise.all([api.areas(selectedSystemId), api.energyUses(selectedSystemId), api.baselines(selectedSystemId), api.ides(selectedSystemId)]).then(([areaItems, useItems, baselineItems, ideItems]) => {
      setAreas(areaItems);
      setUses(useItems);
      setBaselines(baselineItems);
      setIdes(ideItems);
      if (!selectedAreaId && areaItems[0]) setSelectedAreaId(areaItems[0].id);
      if (!selectedUseId && useItems[0]) setSelectedUseId(useItems[0].id);
      if (!selectedBaselineId && baselineItems[0]) setSelectedBaselineId(baselineItems[0].id);
      if (!selectedIdeId && ideItems[0]) setSelectedIdeId(ideItems[0].id);
    });
  }, [selectedSystemId, selectedAreaId, selectedBaselineId, selectedIdeId, selectedUseId]);

  useEffect(() => {
    if (!selectedBaselineId) {
      setBaselineVariables([]);
      return;
    }
    api.baselineVariables(selectedBaselineId).then((items) => {
      setBaselineVariables(items);
      if (editMeasurement) {
        const existingValues: Record<number, string> = {};
        editMeasurement.variables.forEach((variable) => {
          existingValues[variable.baseline_variable_id] = String(variable.value);
        });
        setVariableValues(existingValues);
      }
    });
  }, [selectedBaselineId, editMeasurement]);

  useEffect(() => {
    if (mode !== "edit" || !editMeasurement) return;
    setVariableValues((current) => {
      const next = { ...current };
      editMeasurement.variables.forEach((variable) => {
        next[variable.baseline_variable_id] = String(variable.value);
      });
      return next;
    });
  }, [editMeasurement, mode]);

  const selectedBaseline = useMemo(() => baselines.find((item) => item.id === selectedBaselineId) ?? null, [baselines, selectedBaselineId]);
  const selectedIde = useMemo(() => ides.find((item) => item.id === selectedIdeId) ?? null, [ides, selectedIdeId]);
  const preview = useMemo(
    () => calculatePreview(selectedBaseline, selectedIde, baselineVariables, variableValues, realConsumption),
    [baselineVariables, realConsumption, selectedBaseline, selectedIde, variableValues],
  );

  async function submitMeasurement(nextStatus: typeof status) {
    if (!selectedSystemId || !selectedBaseline || !selectedIde) return;
    const payload = {
      area_id: selectedAreaId ?? 0,
      energy_use_id: selectedUseId ?? 0,
      baseline_model_id: selectedBaselineId ?? 0,
      ide_id: selectedIdeId ?? 0,
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
      if (mode === "edit" && measurementId) {
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
    return <Card><CardContent>Cargando formulario...</CardContent></Card>;
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{mode === "edit" ? "Editar registro mensual" : "Nuevo registro mensual"}</CardTitle>
          <CardDescription>Flujo: contexto, consumo, variables, resultado preliminar y guardado.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex flex-wrap gap-2">
            {[1, 2, 3, 4, 5].map((item) => (
              <Badge key={item} variant={step === item ? "default" : "secondary"}>
                Paso {item}
              </Badge>
            ))}
          </div>

          {step === 1 ? (
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              <Select
                value={selectedSystemId ? String(selectedSystemId) : ""}
                onChange={(event) => {
                  const nextSystemId = Number(event.target.value);
                  setSelectedSystemId(nextSystemId);
                  setSelectedAreaId(null);
                  setSelectedUseId(null);
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
              <div>
                <Label htmlFor="real_consumption">Consumo real</Label>
                <Input id="real_consumption" value={realConsumption} onChange={(event) => setRealConsumption(event.target.value)} />
              </div>
              <div>
                <Label htmlFor="consumption_unit">Unidad</Label>
                <Input id="consumption_unit" value={consumptionUnit} onChange={(event) => setConsumptionUnit(event.target.value)} />
              </div>
            </div>
          ) : null}

          {step === 3 ? (
            <div className="grid gap-4">
              {baselineVariables.map((variable) => {
                const currentValue = variableValues[variable.id] ?? "";
                return (
                  <div key={variable.id} className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="font-medium text-white">
                          {variable.variable_name} {variable.required ? "*" : ""}
                        </p>
                        <p className="text-sm text-slate-400">
                          {variable.description ?? "Sin descripción"} | {variable.unit ?? "sin unidad"}
                        </p>
                      </div>
                      <Badge variant={variable.required ? "destructive" : "secondary"}>{variable.variable_code}</Badge>
                    </div>
                    <div className="mt-3 grid gap-3 md:grid-cols-[1fr_180px]">
                      <Input
                        value={currentValue}
                        onChange={(event) => setVariableValues((state) => ({ ...state, [variable.id]: event.target.value }))}
                        placeholder={`Valor para ${variable.variable_name}`}
                      />
                      <div className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300">
                        Rango: {variable.min_value ?? "sin mínimo"} - {variable.max_value ?? "sin máximo"}
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
                <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
                  <p className="text-sm text-slate-400">Consumo esperado</p>
                  <p className="font-heading text-2xl text-white">{preview?.expected !== null && preview?.expected !== undefined ? preview.expected.toFixed(2) : "--"}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
                  <p className="text-sm text-slate-400">IDE real / esperado</p>
                  <p className="font-heading text-2xl text-white">
                    {preview?.ideReal?.toFixed(2) ?? "--"} / {preview?.ideExpected?.toFixed(2) ?? "--"}
                  </p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
                  <p className="text-sm text-slate-400">Desviación</p>
                  <p className="font-heading text-2xl text-white">
                    {preview?.difference?.toFixed(2) ?? "--"} ({preview?.percentageDifference?.toFixed(2) ?? "--"}%)
                  </p>
                </div>
              </div>
              <div className="space-y-3">
                <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
                  <p className="text-sm text-slate-400">Estado de cumplimiento</p>
                  <Badge variant={preview?.status === "compliant" ? "success" : preview?.status === "warning" ? "warning" : preview?.status === "non_compliant" ? "destructive" : "secondary"}>
                    {preview?.status ?? "incomplete"}
                  </Badge>
                </div>
                <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
                  <p className="text-sm text-slate-400">Alertas preliminares</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {preview?.alerts.map((alert) => (
                      <Badge key={alert} variant="destructive">
                        {alert}
                      </Badge>
                    )) ?? <Badge variant="secondary">Sin alertas</Badge>}
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          {step === 5 ? (
            <div className="space-y-4">
              <Textarea value={comments} onChange={(event) => setComments(event.target.value)} placeholder="Comentarios o antecedentes" />
              <div className="flex flex-wrap gap-3">
                <Button variant="secondary" onClick={() => submitMeasurement("draft")}>Guardar borrador</Button>
                <Button onClick={() => submitMeasurement("submitted")}>Enviar a revisión</Button>
              </div>
            </div>
          ) : null}

          <div className="flex flex-wrap gap-3 pt-2">
            <Button variant="secondary" disabled={step === 1} onClick={() => setStep((current) => Math.max(1, current - 1))}>
              Anterior
            </Button>
            <Button variant="secondary" disabled={step === 5} onClick={() => setStep((current) => Math.min(5, current + 1))}>
              Siguiente
            </Button>
          </div>

          {message ? <p className="text-sm text-slate-300">{message}</p> : null}
        </CardContent>
      </Card>
    </div>
  );
}
