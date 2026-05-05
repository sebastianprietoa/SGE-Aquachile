"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { AlertEvent, EnergySystem, TrackingMonthlyRow, TrackingSummary } from "@/types/api";
import { AlertBadge, KpiCard, PageHeader, SectionCard, StatusBadge } from "@/components/energy/shared";
import { DeviationChart, LineComparisonChart } from "@/components/energy/charts";
import { TrackingMonthlyTable } from "@/components/energy/tables";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function TrackingPage({ params }: { params: Promise<{ systemId: string }> }) {
  const { systemId } = use(params);
  const systemIdNumber = Number(systemId);
  const [system, setSystem] = useState<EnergySystem | null>(null);
  const [summary, setSummary] = useState<TrackingSummary | null>(null);
  const [tracking, setTracking] = useState<TrackingMonthlyRow[]>([]);
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);

  useEffect(() => {
    let active = true;
    Promise.all([api.system(systemIdNumber), api.systemTrackingSummary(systemIdNumber), api.systemTracking(systemIdNumber), api.systemAlerts(systemIdNumber)])
      .then(([systemResponse, summaryResponse, trackingResponse, alertsResponse]) => {
        if (!active) return;
        setSystem(systemResponse);
        setSummary(summaryResponse);
        setTracking(trackingResponse);
        setAlerts(alertsResponse);
      })
      .catch(() => {
        if (!active) return;
        setSystem(null);
        setSummary(null);
        setTracking([]);
        setAlerts([]);
      });
    return () => {
      active = false;
    };
  }, [systemIdNumber]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Seguimiento"
        title={`Seguimiento mensual · ${system?.name ?? "Sistema"}`}
        description="El seguimiento conecta consumo real, consumo esperado, IDE real, desviación, estado y alertas para cada LBEn."
        actions={
          <Button asChild variant="secondary">
              <Link href={`/systems/${systemIdNumber}/measurements/new`}>Nuevo registro mensual</Link>
          </Button>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Mediciones" value={summary ? String(summary.total_measurements) : "--"} helper="Registros del sistema" />
        <KpiCard label="Conformes" value={summary ? String(summary.compliant) : "--"} helper="Estado compliant" />
        <KpiCard label="Advertencia" value={summary ? String(summary.warning) : "--"} helper="Desviación moderada" />
        <KpiCard label="No conformes" value={summary ? String(summary.non_compliant) : "--"} helper="Desviación crítica" />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard title="Consumo real vs esperado" description="Serie mensual del sistema.">
          <LineComparisonChart data={tracking} />
        </SectionCard>
        <SectionCard title="Desviación porcentual" description="Tendencia anual del cumplimiento.">
          <DeviationChart data={tracking} />
        </SectionCard>
      </div>

      <SectionCard title="Tabla mensual" description="Variables reales, cálculo LBEn, IDE y estado de cumplimiento.">
        <TrackingMonthlyTable rows={tracking} />
      </SectionCard>

      <div className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
        <SectionCard title="Acciones requeridas" description="Comentarios y eventos que requieren revisión.">
          <div className="space-y-3">
            {tracking.slice(0, 6).map((row) => (
              <div key={row.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center justify-between gap-3">
                  <strong className="text-slate-900">{String(row.month).padStart(2, "0")}/{row.year}</strong>
                  <StatusBadge value={row.compliance_status} />
                </div>
                <p className="mt-2 text-sm text-slate-600">{row.comments ?? "Sin comentario asociado."}</p>
              </div>
            ))}
          </div>
        </SectionCard>
        <SectionCard title="Alertas recientes" description="Eventos abiertos y severidad.">
          <div className="space-y-3">
            {alerts.slice(0, 6).map((alert) => (
              <div key={alert.id} className="rounded-2xl border border-slate-200 bg-white p-4">
                <div className="flex items-center justify-between gap-3">
                  <AlertBadge severity={alert.severity} />
                  <Badge variant={alert.status === "open" ? "warning" : "success"}>{alert.status}</Badge>
                </div>
                <p className="mt-2 text-sm text-slate-700">{alert.message}</p>
              </div>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
