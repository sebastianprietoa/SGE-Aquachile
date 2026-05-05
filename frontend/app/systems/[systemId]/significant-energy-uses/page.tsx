"use client";

import { use, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import type { BaselineModelV2, BaselineVariableV2, EnergyArea, EnergySystem, SignificantEnergyUse } from "@/types/api";
import { Badge } from "@/components/ui/badge";
import { PageHeader, SectionCard } from "@/components/energy/shared";
import { DataTable } from "@/components/energy/shared";

export default function SignificantEnergyUsesPage({ params }: { params: Promise<{ systemId: string }> }) {
  const { systemId } = use(params);
  const systemIdNumber = Number(systemId);
  const [system, setSystem] = useState<EnergySystem | null>(null);
  const [areas, setAreas] = useState<EnergyArea[]>([]);
  const [uses, setUses] = useState<SignificantEnergyUse[]>([]);
  const [baselines, setBaselines] = useState<BaselineModelV2[]>([]);
  const [variablesByBaseline, setVariablesByBaseline] = useState<Record<number, BaselineVariableV2[]>>({});

  useEffect(() => {
    let active = true;
    Promise.all([api.system(systemIdNumber), api.areas(systemIdNumber), api.significantEnergyUses(systemIdNumber), api.baselines(systemIdNumber)])
      .then(async ([systemResponse, areaResponse, useResponse, baselineResponse]) => {
        if (!active) return;
        setSystem(systemResponse);
        setAreas(areaResponse);
        setUses(useResponse);
        setBaselines(baselineResponse);
        const entries = await Promise.all(
          baselineResponse.map(async (baseline) => [baseline.id, await api.baselineVariables(baseline.id)] as const),
        );
        if (!active) return;
        setVariablesByBaseline(Object.fromEntries(entries));
      })
      .catch(() => {
        if (!active) return;
        setSystem(null);
        setAreas([]);
        setUses([]);
        setBaselines([]);
        setVariablesByBaseline({});
      });
    return () => {
      active = false;
    };
  }, [systemIdNumber]);

  const rows = useMemo(
    () =>
      uses.map((use) => {
        const linkedBaselines = baselines.filter((baseline) => baseline.significant_energy_use_id === use.id);
        const variableCount = linkedBaselines.reduce((total, baseline) => total + (variablesByBaseline[baseline.id]?.length ?? 0), 0);
        return [
          areas.find((area) => area.id === use.area_id)?.name ?? use.area_id ?? "-",
          use.name,
          use.energy_source,
          `${Number(use.consumption_value ?? 0).toLocaleString("es-CL")} ${use.consumption_unit ?? ""}`,
          <Badge key={`${use.id}-active`} variant={use.active ? "success" : "secondary"}>{use.active ? "Activo" : "Inactivo"}</Badge>,
          variableCount ? `${variableCount}` : "-",
          use.current_energy_performance != null
            ? `${use.current_energy_performance.toLocaleString("es-CL")} ${use.current_energy_performance_unit ?? ""}`
            : "-",
          use.relevant_personnel ?? "-",
          use.operational_control_required ?? "-",
          use.improvement_opportunities ?? "-",
        ];
      }),
    [areas, baselines, uses, variablesByBaseline],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="USE"
        title={`Matriz de USE · ${system?.name ?? "Sistema"}`}
        description="Cada USE se conecta con sus variables pertinentes, desempeño actual, personal influyente, controles operacionales y oportunidades de mejora."
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <SectionCard title="USE activos" description="Usos energéticos significativos del sistema.">
          <p className="font-heading text-3xl text-slate-900">{uses.filter((item) => item.active).length}</p>
        </SectionCard>
        <SectionCard title="Líneas base asociadas" description="Relación USE → LBEn.">
          <p className="font-heading text-3xl text-slate-900">{baselines.length}</p>
        </SectionCard>
        <SectionCard title="Variables pertinentes" description="Variables amarradas a las líneas base.">
          <p className="font-heading text-3xl text-slate-900">{Object.values(variablesByBaseline).flat().length}</p>
        </SectionCard>
        <SectionCard title="Controles operacionales" description="Criterios de operación y mantenimiento.">
          <p className="font-heading text-3xl text-slate-900">{uses.length ? "Activos" : "--"}</p>
        </SectionCard>
      </div>

      <SectionCard title="Matriz de USE" description="Relación de uso, consumo, desempeño, personal y controles.">
        <DataTable
          headers={["Área", "USE", "Energético", "Consumo", "Estado", "Variables", "Desempeño", "Personal", "Controles", "Mejoras"]}
          rows={rows}
          emptyMessage="No hay USE disponibles para este sistema."
        />
      </SectionCard>
    </div>
  );
}
