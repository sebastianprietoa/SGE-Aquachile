"use client";

import { use, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { BaselineModelV2, BaselineVariableV2, TrackingMonthlyRow } from "@/types/api";
import { Badge } from "@/components/ui/badge";
import { LineComparisonChart } from "@/components/energy/charts";
import { BaselineVariableTable, TrackingMonthlyTable } from "@/components/energy/tables";
import { PageHeader, SectionCard } from "@/components/energy/shared";

export default function TrackingBaselinePage({ params }: { params: Promise<{ systemId: string; baselineId: string }> }) {
  const { systemId, baselineId } = use(params);
  const systemIdNumber = Number(systemId);
  const baselineIdNumber = Number(baselineId);
  const [baseline, setBaseline] = useState<BaselineModelV2 | null>(null);
  const [variables, setVariables] = useState<BaselineVariableV2[]>([]);
  const [tracking, setTracking] = useState<TrackingMonthlyRow[]>([]);

  useEffect(() => {
    let active = true;
    Promise.all([api.baseline(baselineIdNumber), api.baselineVariables(baselineIdNumber), api.baselineTracking(baselineIdNumber)])
      .then(([baselineResponse, variableResponse, trackingResponse]) => {
        if (!active) return;
        setBaseline(baselineResponse as BaselineModelV2);
        setVariables(variableResponse);
        setTracking(trackingResponse);
      })
      .catch(() => {
        if (!active) return;
        setBaseline(null);
        setVariables([]);
        setTracking([]);
      });
    return () => {
      active = false;
    };
  }, [baselineIdNumber]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Seguimiento por LBEn"
        title={baseline?.name ?? "Detalle de línea base"}
        description="Vista mensual de una línea base específica con sus variables requeridas, consumo real, consumo esperado e IDE."
      />

      {baseline ? (
        <div className="flex flex-wrap gap-3">
          <Badge variant="secondary">{baseline.model_type}</Badge>
          <Badge variant="success">Sistema {systemIdNumber}</Badge>
          <Badge variant={baseline.active ? "success" : "secondary"}>{baseline.active ? "Activa" : "Inactiva"}</Badge>
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
        <SectionCard title="Variables requeridas" description="Campos exactos del formulario mensual.">
          <BaselineVariableTable variables={variables} />
        </SectionCard>
        <SectionCard title="Consumo real vs esperado" description="Comparación mensual para la LBEn seleccionada.">
          <LineComparisonChart data={tracking} />
        </SectionCard>
      </div>

      <SectionCard title="Histórico mensual" description="Trazabilidad completa de la línea base.">
        <TrackingMonthlyTable rows={tracking} />
      </SectionCard>
    </div>
  );
}
