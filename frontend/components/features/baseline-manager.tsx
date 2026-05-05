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
import type { BaselineModel, BaselineVariable, EnergyArea, EnergySystem, EnergyUse, IdeDefinition } from "@/types/api";

const variableTypeOptions = [
  "production",
  "ambient_temperature",
  "operating_hours",
  "generated_energy",
  "flow",
  "ph",
  "biomass",
  "tons_processed",
  "other",
];

export function BaselineManager() {
  const [systems, setSystems] = useState<EnergySystem[]>([]);
  const [areas, setAreas] = useState<EnergyArea[]>([]);
  const [uses, setUses] = useState<EnergyUse[]>([]);
  const [baselines, setBaselines] = useState<BaselineModel[]>([]);
  const [baselineId, setBaselineId] = useState<number | null>(null);
  const [baselineVariables, setBaselineVariables] = useState<BaselineVariable[]>([]);
  const [selectedVariableId, setSelectedVariableId] = useState<number | null>(null);
  const [ides, setIdes] = useState<IdeDefinition[]>([]);
  const [systemId, setSystemId] = useState<number | null>(null);
  const [baselineForm, setBaselineForm] = useState({
    area_id: "",
    energy_use_id: "",
    name: "",
    dependent_variable: "",
    dependent_variable_unit: "kWh",
    formula_text: "",
    model_type: "linear",
    intercept: "0",
    coefficients: "{}",
    active: true,
  });
  const [variableForm, setVariableForm] = useState({
    variable_name: "",
    variable_code: "",
    variable_type: "other",
    unit: "",
    required: true,
    min_value: "",
    max_value: "",
    description: "",
    display_order: "1",
    active: true,
  });
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    api.systems().then((items) => {
      setSystems(items);
      if (items[0]) setSystemId(items[0].id);
    });
  }, []);

  useEffect(() => {
    if (!systemId) return;
    Promise.all([api.areas(systemId), api.energyUses(systemId), api.baselines(systemId), api.ides(systemId)]).then(([areaItems, useItems, baselineItems, ideItems]) => {
      setAreas(areaItems);
      setUses(useItems);
      setBaselines(baselineItems);
      setIdes(ideItems);
      if (baselineItems[0]) setBaselineId(baselineItems[0].id);
    });
  }, [systemId]);

  useEffect(() => {
    if (!baselineId) return;
    api.baselineVariables(baselineId).then(setBaselineVariables);
  }, [baselineId]);

  useEffect(() => {
    if (!baselineId) {
      setBaselineForm({
        area_id: "",
        energy_use_id: "",
        name: "",
        dependent_variable: "",
        dependent_variable_unit: "kWh",
        formula_text: "",
        model_type: "linear",
        intercept: "0",
        coefficients: "{}",
        active: true,
      });
      return;
    }
    const baseline = baselines.find((item) => item.id === baselineId);
    if (!baseline) return;
    setBaselineForm({
      area_id: String(baseline.area_id),
      energy_use_id: String(baseline.energy_use_id),
      name: baseline.name,
      dependent_variable: baseline.dependent_variable,
      dependent_variable_unit: baseline.dependent_variable_unit,
      formula_text: baseline.formula_text ?? "",
      model_type: baseline.model_type,
      intercept: String(baseline.intercept),
      coefficients: JSON.stringify(baseline.coefficients ?? {}, null, 2),
      active: baseline.active,
    });
  }, [baselineId, baselines]);

  const selectedBaseline = useMemo(() => baselines.find((item) => item.id === baselineId) ?? null, [baselineId, baselines]);

  async function saveBaseline() {
    if (!systemId) return;
    const payload = {
      area_id: Number(baselineForm.area_id),
      energy_use_id: Number(baselineForm.energy_use_id),
      name: baselineForm.name,
      dependent_variable: baselineForm.dependent_variable,
      dependent_variable_unit: baselineForm.dependent_variable_unit,
      formula_text: baselineForm.formula_text,
      model_type: baselineForm.model_type,
      coefficients: JSON.parse(baselineForm.coefficients || "{}"),
      intercept: Number(baselineForm.intercept),
      active: baselineForm.active,
    };

    try {
      const url = baselineId
        ? `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/baselines/${baselineId}`
        : `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/systems/${systemId}/baselines`;
      const response = await fetch(url, {
        method: baselineId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? "No fue posible guardar la línea base");
      }
      if (baselineId) {
        setMessage("Línea base actualizada");
      } else {
        setMessage("Línea base creada");
      }
      const refreshed = await api.baselines(systemId);
      setBaselines(refreshed);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No fue posible guardar la línea base");
    }
  }

  async function saveVariable() {
    if (!baselineId) return;
    try {
      const endpoint = selectedVariableId
        ? `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/baseline-variables/${selectedVariableId}`
        : `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/baselines/${baselineId}/variables`;
      const response = await fetch(endpoint, {
        method: selectedVariableId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          variable_name: variableForm.variable_name,
          variable_code: variableForm.variable_code,
          variable_type: variableForm.variable_type,
          unit: variableForm.unit,
          required: variableForm.required,
          min_value: variableForm.min_value === "" ? null : Number(variableForm.min_value),
          max_value: variableForm.max_value === "" ? null : Number(variableForm.max_value),
          description: variableForm.description,
          display_order: Number(variableForm.display_order),
          active: variableForm.active,
        }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ?? "No fue posible guardar la variable");
      }
      setBaselineVariables(await api.baselineVariables(baselineId));
      setSelectedVariableId(null);
      setMessage(selectedVariableId ? "Variable actualizada" : "Variable agregada");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No fue posible guardar la variable");
    }
  }

  function editVariable(variable: BaselineVariable) {
    setSelectedVariableId(variable.id);
    setVariableForm({
      variable_name: variable.variable_name,
      variable_code: variable.variable_code,
      variable_type: variable.variable_type,
      unit: variable.unit ?? "",
      required: variable.required,
      min_value: variable.min_value === null || variable.min_value === undefined ? "" : String(variable.min_value),
      max_value: variable.max_value === null || variable.max_value === undefined ? "" : String(variable.max_value),
      description: variable.description ?? "",
      display_order: String(variable.display_order),
      active: variable.active,
    });
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Configuración de líneas base</CardTitle>
          <CardDescription>Crear, editar y asociar variables e IDEs por sistema energético.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <Select
            value={systemId ? String(systemId) : ""}
            onChange={(event) => {
              setSystemId(Number(event.target.value));
              setBaselineId(null);
              setBaselineVariables([]);
              setSelectedVariableId(null);
            }}
          >
            {systems.map((system) => (
              <option key={system.id} value={system.id}>
                {system.code}
              </option>
            ))}
          </Select>
          <Select value={baselineId ? String(baselineId) : ""} onChange={(event) => setBaselineId(event.target.value ? Number(event.target.value) : null)}>
            <option value="">Nueva línea base</option>
            {baselines.map((baseline) => (
              <option key={baseline.id} value={baseline.id}>
                {baseline.name}
              </option>
            ))}
          </Select>
          <Button variant="secondary" onClick={() => setBaselineId(null)}>
            Limpiar formulario
          </Button>
          {selectedBaseline ? <Badge variant="secondary">Modelo {selectedBaseline.model_type}</Badge> : null}
          {message ? <p className="text-sm text-slate-300">{message}</p> : null}
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{baselineId ? "Editar línea base" : "Crear línea base"}</CardTitle>
            <CardDescription>Define coeficientes e intercepto para el cálculo de consumo esperado.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Select value={baselineForm.area_id} onChange={(event) => setBaselineForm((current) => ({ ...current, area_id: event.target.value }))}>
              <option value="">Área</option>
              {areas.map((area) => (
                <option key={area.id} value={area.id}>
                  {area.name}
                </option>
              ))}
            </Select>
            <Select value={baselineForm.energy_use_id} onChange={(event) => setBaselineForm((current) => ({ ...current, energy_use_id: event.target.value }))}>
              <option value="">Uso energético</option>
              {uses.map((energyUse) => (
                <option key={energyUse.id} value={energyUse.id}>
                  {energyUse.name}
                </option>
              ))}
            </Select>
            <Input placeholder="Nombre" value={baselineForm.name} onChange={(event) => setBaselineForm((current) => ({ ...current, name: event.target.value }))} />
            <Input placeholder="Variable dependiente" value={baselineForm.dependent_variable} onChange={(event) => setBaselineForm((current) => ({ ...current, dependent_variable: event.target.value }))} />
            <Input placeholder="Unidad variable dependiente" value={baselineForm.dependent_variable_unit} onChange={(event) => setBaselineForm((current) => ({ ...current, dependent_variable_unit: event.target.value }))} />
            <Textarea placeholder="Fórmula textual" value={baselineForm.formula_text} onChange={(event) => setBaselineForm((current) => ({ ...current, formula_text: event.target.value }))} />
            <Input placeholder="Intercepto" value={baselineForm.intercept} onChange={(event) => setBaselineForm((current) => ({ ...current, intercept: event.target.value }))} />
            <Textarea placeholder='Coeficientes JSON, por ejemplo {"production_monthly":0.42}' value={baselineForm.coefficients} onChange={(event) => setBaselineForm((current) => ({ ...current, coefficients: event.target.value }))} />
            <Button onClick={saveBaseline}>Guardar línea base</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Variables de línea base</CardTitle>
            <CardDescription>Las variables cargables se restringen a lo definido en la línea base.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-3 md:grid-cols-2">
              <Input placeholder="Nombre variable" value={variableForm.variable_name} onChange={(event) => setVariableForm((current) => ({ ...current, variable_name: event.target.value }))} />
              <Input placeholder="Código" value={variableForm.variable_code} onChange={(event) => setVariableForm((current) => ({ ...current, variable_code: event.target.value }))} />
              <Select value={variableForm.variable_type} onChange={(event) => setVariableForm((current) => ({ ...current, variable_type: event.target.value }))}>
                {variableTypeOptions.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </Select>
              <Input placeholder="Unidad" value={variableForm.unit} onChange={(event) => setVariableForm((current) => ({ ...current, unit: event.target.value }))} />
              <Input placeholder="Mínimo" value={variableForm.min_value} onChange={(event) => setVariableForm((current) => ({ ...current, min_value: event.target.value }))} />
              <Input placeholder="Máximo" value={variableForm.max_value} onChange={(event) => setVariableForm((current) => ({ ...current, max_value: event.target.value }))} />
              <Input placeholder="Orden" value={variableForm.display_order} onChange={(event) => setVariableForm((current) => ({ ...current, display_order: event.target.value }))} />
              <Input placeholder="Descripción" value={variableForm.description} onChange={(event) => setVariableForm((current) => ({ ...current, description: event.target.value }))} />
            </div>
            <Button onClick={saveVariable} disabled={!baselineId}>
              {selectedVariableId ? "Actualizar variable" : "Agregar variable"}
            </Button>
            <div className="space-y-2 pt-2">
              {baselineVariables.map((variable) => (
                <div key={variable.id} className="rounded-2xl border border-white/10 bg-slate-900/70 p-3 text-sm text-slate-200">
                  <div className="flex items-center justify-between gap-3">
                    <strong>{variable.variable_name}</strong>
                    <div className="flex items-center gap-2">
                      <Badge variant={variable.required ? "success" : "secondary"}>{variable.variable_code}</Badge>
                      <Button size="sm" variant="ghost" onClick={() => editVariable(variable)}>
                        Editar
                      </Button>
                    </div>
                  </div>
                  <p className="text-slate-400">
                    {variable.unit ?? "-"} | rango {variable.min_value ?? "sin mínimo"} a {variable.max_value ?? "sin máximo"}
                  </p>
                </div>
              ))}
            </div>
            <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-4 text-sm text-cyan-100">
              IDEs asociados: {ides.length}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
