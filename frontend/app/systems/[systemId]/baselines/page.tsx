"use client";

import { use, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import type { BaselineModelV2, BaselineVariableV2, EnergySystem, TrackingMonthlyRow } from "@/types/api";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { LineComparisonChart } from "@/components/energy/charts";
import { BaselineVariableTable, TrackingMonthlyTable } from "@/components/energy/tables";
import { PageHeader, SectionCard } from "@/components/energy/shared";

export default function BaselinesPage({ params }: { params: Promise<{ systemId: string }> }) {
  const { systemId } = use(params);
  const systemIdNumber = Number(systemId);
  const [system, setSystem] = useState<EnergySystem | null>(null);
  const [baselines, setBaselines] = useState<BaselineModelV2[]>([]);
  const [selectedBaselineId, setSelectedBaselineId] = useState<number | null>(null);
  const [variables, setVariables] = useState<BaselineVariableV2[]>([]);
  const [tracking, setTracking] = useState<TrackingMonthlyRow[]>([]);

  useEffect(() => {
    let active = true;
    Promise.all([api.system(systemIdNumber), api.baselines(systemIdNumber)])
      .then(([systemResponse, baselineResponse]) => {
        if (!active) return;
        setSystem(systemResponse);
        setBaselines(baselineResponse);
        setSelectedBaselineId((current) => current ?? baselineResponse[0]?.id ?? null);
      })
      .catch(() => {
        if (!active) return;
        setSystem(null);
        setBaselines([]);
      });
    return () => {
      active = false;
    };
  }, [systemIdNumber]);

  useEffect(() => {
    if (!selectedBaselineId) return;
    let active = true;
    Promise.all([api.baselineVariables(selectedBaselineId), api.baselineTracking(selectedBaselineId)])
      .then(([variableResponse, trackingResponse]) => {
        if (!active) return;
        setVariables(variableResponse);
        setTracking(trackingResponse);
      })
      .catch(() => {
        if (!active) return;
        setVariables([]);
        setTracking([]);
      });
    return () => {
      active = false;
    };
  }, [selectedBaselineId]);

  const selectedBaseline = useMemo(() => baselines.find((item) => item.id === selectedBaselineId) ?? null, [baselines, selectedBaselineId]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="LBEn"
        title={`Líneas base energéticas · ${system?.name ?? "Sistema"}`}
        description="La LBEn define la variable dependiente, las variables independientes requeridas, el método/regresión y el consumo esperado mensual."
        actions={
          <Select
            value={selectedBaselineId ? String(selectedBaselineId) : ""}
            onChange={(event) => setSelectedBaselineId(Number(event.target.value))}
            className="min-w-[280px] bg-white"
          >
            {baselines.map((baseline) => (
              <option key={baseline.id} value={baseline.id}>
                {baseline.name}
              </option>
            ))}
          </Select>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <SectionCard title="LBEn activas" description="Modelos vigentes del sistema.">
          <p className="font-heading text-3xl text-slate-900">{baselines.filter((baseline) => baseline.active).length}</p>
        </SectionCard>
        <SectionCard title="Variables vinculadas" description="Variables requeridas por el formulario mensual.">
          <p className="font-heading text-3xl text-slate-900">{variables.length}</p>
        </SectionCard>
        <SectionCard title="Control mensual" description="Base para seguimiento y comparación.">
          <p className="font-heading text-3xl text-slate-900">{tracking.length} meses</p>
        </SectionCard>
        <SectionCard title="R² documentado" description="Calidad de regresión del modelo.">
          <p className="font-heading text-3xl text-slate-900">{selectedBaseline?.r_squared?.toFixed(2) ?? "--"}</p>
        </SectionCard>
      </div>

      {selectedBaseline ? (
        <SectionCard
          title={selectedBaseline.name}
          description={selectedBaseline.formula_text ?? "Modelo documentado con coeficientes e intercepto."}
        >
          <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
            <div className="space-y-3 rounded-3xl border border-slate-200 bg-slate-50 p-4">
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary">{selectedBaseline.model_type}</Badge>
                <Badge variant={selectedBaseline.active ? "success" : "secondary"}>{selectedBaseline.active ? "Activa" : "Inactiva"}</Badge>
                {selectedBaseline.significant_energy_use_id ? <Badge variant="warning">Con USE asociado</Badge> : null}
              </div>
              <p className="text-sm text-slate-600">
                Variable dependiente: <strong className="text-slate-900">{selectedBaseline.dependent_variable}</strong> ({selectedBaseline.dependent_variable_unit})
              </p>
              <p className="text-sm text-slate-600">
                Periodo de referencia: {selectedBaseline.reference_period_start ?? "-"} a {selectedBaseline.reference_period_end ?? "-"}
              </p>
              <p className="text-sm text-slate-600">Factores estáticos: {selectedBaseline.static_factors ? JSON.stringify(selectedBaseline.static_factors) : "-"}</p>
              <p className="text-sm text-slate-600">Ajustes rutinarios: {selectedBaseline.routine_adjustments ? JSON.stringify(selectedBaseline.routine_adjustments) : "-"}</p>
              <p className="text-sm text-slate-600">Ajustes no rutinarios: {selectedBaseline.non_routine_adjustments ? JSON.stringify(selectedBaseline.non_routine_adjustments) : "-"}</p>
            </div>
            <div>
              <LineComparisonChart data={tracking} />
            </div>
          </div>
        </SectionCard>
      ) : null}

      <SectionCard title="Variables requeridas" description="Exactamente estas variables aparecen en el formulario mensual.">
        <BaselineVariableTable variables={variables} />
      </SectionCard>

      <SectionCard title="Control mensual de la LBEn" description="Comparación real vs esperado y trazabilidad de cumplimiento.">
        <TrackingMonthlyTable rows={tracking} />
      </SectionCard>
    </div>
  );
}
