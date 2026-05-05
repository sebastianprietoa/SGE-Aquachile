"use client";

import { use, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { BaselineModelV2, EnergyArea, EnergySystem, IdeDefinitionV2, TrackingMonthlyRow } from "@/types/api";
import { Badge } from "@/components/ui/badge";
import { IdeComparisonChart } from "@/components/energy/charts";
import { DataTable, PageHeader, SectionCard } from "@/components/energy/shared";

export default function IdesPage({ params }: { params: Promise<{ systemId: string }> }) {
  const { systemId } = use(params);
  const systemIdNumber = Number(systemId);
  const [system, setSystem] = useState<EnergySystem | null>(null);
  const [areas, setAreas] = useState<EnergyArea[]>([]);
  const [ides, setIdes] = useState<IdeDefinitionV2[]>([]);
  const [baselines, setBaselines] = useState<BaselineModelV2[]>([]);
  const [trend, setTrend] = useState<TrackingMonthlyRow[]>([]);

  useEffect(() => {
    let active = true;
    Promise.all([api.system(systemIdNumber), api.areas(systemIdNumber), api.ides(systemIdNumber), api.baselines(systemIdNumber), api.systemTracking(systemIdNumber)])
      .then(([systemResponse, areaResponse, ideResponse, baselineResponse, trackingResponse]) => {
        if (!active) return;
        setSystem(systemResponse);
        setAreas(areaResponse);
        setIdes(ideResponse);
        setBaselines(baselineResponse);
        setTrend(trackingResponse);
      })
      .catch(() => {
        if (!active) return;
        setSystem(null);
        setAreas([]);
        setIdes([]);
        setBaselines([]);
        setTrend([]);
      });
    return () => {
      active = false;
    };
  }, [systemIdNumber]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="IDE"
        title={`Indicadores de desempeño energético · ${system?.name ?? "Sistema"}`}
        description="Cada IDE mantiene trazabilidad mensual, rango esperado, fórmula y conexión directa con la LBEn asociada."
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <SectionCard title="IDEs definidos" description="Catálogo activo del sistema.">
          <p className="font-heading text-3xl text-slate-900">{ides.length}</p>
        </SectionCard>
        <SectionCard title="Frecuencia mensual" description="Seguimiento operativo.">
          <p className="font-heading text-3xl text-slate-900">{ides.filter((ide) => ide.frequency === "Mensual" || ide.frequency === "Mensual").length || ides.length || "--"}</p>
        </SectionCard>
        <SectionCard title="LBEn asociadas" description="Relación indicador / modelo.">
          <p className="font-heading text-3xl text-slate-900">{baselines.length}</p>
        </SectionCard>
        <SectionCard title="Trazabilidad" description="Fórmula, protocolo y umbral.">
          <p className="font-heading text-3xl text-slate-900">{ides.some((ide) => ide.protocol_description) ? "Completa" : "--"}</p>
        </SectionCard>
      </div>

      <SectionCard title="Catálogo de IDEs" description="Fórmula, rango esperado y conexión con la LBEn.">
        <DataTable
          headers={["Código", "IDE", "Fórmula", "Área", "LBEn", "Unidad", "Rango", "Umbral"]}
          rows={ides.map((ide) => [
            ide.ide_code,
            ide.ide_name,
            ide.formula_text ?? `${ide.numerator ?? ""}/${ide.denominator ?? ""}`,
            areas.find((area) => area.id === ide.area_id)?.name ?? ide.area_id,
            baselines.find((baseline) => baseline.id === ide.baseline_model_id)?.name ?? ide.baseline_model_id,
            ide.unit ?? "-",
            `${ide.expected_range_min ?? "-"} a ${ide.expected_range_max ?? "-"}`,
            `${ide.warning_threshold_percentage ?? ide.critical_threshold_percentage ?? "-"}%`,
          ])}
          emptyMessage="No hay IDEs configurados para este sistema."
        />
      </SectionCard>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <SectionCard title="Resumen de protocolos" description="Señala el soporte documental y rango de desviación.">
          <div className="space-y-3">
            {ides.map((ide) => (
              <div key={ide.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <strong className="text-slate-900">{ide.ide_name}</strong>
                  <Badge variant={ide.active ? "success" : "secondary"}>{ide.active ? "Activo" : "Inactivo"}</Badge>
                </div>
                <p className="mt-2 text-sm text-slate-600">{ide.protocol_description ?? "Sin protocolo documentado"}</p>
              </div>
            ))}
          </div>
        </SectionCard>
        <SectionCard title="IDE real vs esperado" description="Tendencia histórica por mes.">
          <IdeComparisonChart data={trend} />
        </SectionCard>
      </div>
    </div>
  );
}
