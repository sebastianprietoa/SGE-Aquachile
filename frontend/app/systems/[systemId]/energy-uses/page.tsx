"use client";

import { use, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import type { EnergySystem, EnergyUseBaseYear, ParetoItem } from "@/types/api";
import { ComplianceStrip, PageHeader, SectionCard } from "@/components/energy/shared";
import { ParetoChart } from "@/components/energy/charts";
import { Badge } from "@/components/ui/badge";
import { DataTable } from "@/components/energy/shared";

export default function EnergyUsesPage({ params }: { params: Promise<{ systemId: string }> }) {
  const { systemId } = use(params);
  const systemIdNumber = Number(systemId);
  const [system, setSystem] = useState<EnergySystem | null>(null);
  const [items, setItems] = useState<EnergyUseBaseYear[]>([]);
  const [pareto, setPareto] = useState<ParetoItem[]>([]);

  useEffect(() => {
    let active = true;
    Promise.all([api.system(systemIdNumber), api.energyUseBaseYear(systemIdNumber), api.energyUseBaseYearPareto(systemIdNumber)])
      .then(([systemResponse, baseYearResponse, paretoResponse]) => {
        if (!active) return;
        setSystem(systemResponse);
        setItems(baseYearResponse);
        setPareto(paretoResponse);
      })
      .catch(() => {
        if (!active) return;
        setSystem(null);
        setItems([]);
        setPareto([]);
      });
    return () => {
      active = false;
    };
  }, [systemIdNumber]);

  const totalConsumption = useMemo(() => items.reduce((total, item) => total + Number(item.consumption_tcal ?? item.consumption_value ?? 0), 0), [items]);
  const significantCount = useMemo(() => items.filter((item) => item.is_significant_use).length, [items]);
  const candidateCount = useMemo(() => items.filter((item) => item.is_candidate_use).length, [items]);
  const principal = items[0];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Art. 21"
        title={`Usos energéticos · ${system?.name ?? "Sistema"}`}
        description="La base BD 2022 prioriza consumos para identificar USE, documentar tendencias y sostener el análisis de revisión energética."
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <SectionCard title="Consumo total BD 2022" description="Base para priorización y Pareto.">
          <p className="font-heading text-3xl text-slate-900">{totalConsumption.toLocaleString("es-CL")} Tcal</p>
        </SectionCard>
        <SectionCard title="Cobertura del SGE" description="Participación de consumos identificados.">
          <p className="font-heading text-3xl text-slate-900">{items.length ? `${Math.round((significantCount / items.length) * 100)}%` : "--"}</p>
        </SectionCard>
        <SectionCard title="Principal área consumidora" description="Área o instalación de mayor peso.">
          <p className="font-heading text-3xl text-slate-900">{principal?.area_name ?? principal?.installation_name ?? "--"}</p>
        </SectionCard>
        <SectionCard title="Actualización anual" description="Base de referencia y priorización.">
          <p className="font-heading text-3xl text-slate-900">{candidateCount ? `${candidateCount} candidatos` : "--"}</p>
        </SectionCard>
      </div>

      <ComplianceStrip
        items={[
          { label: "Art. 21", value: items.length ? "Estructura documentada" : "Sin datos", variant: "success" },
          { label: "USE", value: `${significantCount}`, variant: "warning" },
          { label: "Candidatos", value: `${candidateCount}`, variant: "secondary" },
        ]}
      />

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <SectionCard title="Pareto de consumo energético" description="Ordena la base 2022 para visualizar la concentración de consumo.">
          <ParetoChart data={pareto} />
        </SectionCard>
        <SectionCard title="Estado de requisitos Art. 21" description="Cumplimiento de revisión energética y priorización.">
          <div className="space-y-3">
            {[
              ["Análisis por instalación", "OK"],
              ["Identificación de USE", items.length ? "OK" : "Pendiente"],
              ["Variables pertinentes", significantCount ? "OK" : "Pendiente"],
              ["IDE medibles", significantCount ? "OK" : "Pendiente"],
              ["Rangos de desviación", "OK"],
              ["Relación matemática", "OK"],
            ].map(([label, value]) => (
              <div key={label} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                <span className="text-sm text-slate-700">{label}</span>
                <Badge variant={value === "OK" ? "success" : "warning"}>{value}</Badge>
              </div>
            ))}
          </div>
        </SectionCard>
      </div>

      <SectionCard title="Priorización por área/faena" description="Tabla base para identificar los USE.">
        <DataTable
          headers={["Área", "Instalación", "Fuente", "Uso", "Consumo", "%", "% acum.", "Base", "Estado"]}
          rows={items.map((item) => [
            item.area_name,
            item.installation_name,
            item.energy_source,
            item.use_category,
            `${Number(item.consumption_tcal ?? item.consumption_value).toLocaleString("es-CL")} ${item.consumption_unit}`,
            `${Number(item.percentage ?? 0).toFixed(1)}%`,
            `${Number(item.accumulated_percentage ?? 0).toFixed(1)}%`,
            item.source,
            <Badge key={`${item.id}-badge`} variant={item.is_significant_use ? "success" : item.is_candidate_use ? "warning" : "secondary"}>
              {item.is_significant_use ? "USE" : item.is_candidate_use ? "Candidato" : "Soporte"}
            </Badge>,
          ])}
          emptyMessage="No hay datos BD 2022 para este sistema."
        />
      </SectionCard>
    </div>
  );
}
