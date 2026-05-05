"use client";

import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import type { AlertEvent, EnergySystem, ParetoItem, TrackingSummary, TrendPoint } from "@/types/api";
import { AlertBadge, ComplianceStrip, DataTable, KpiCard, PageHeader, SectionCard } from "@/components/energy/shared";
import { IdeComparisonChart, LineComparisonChart, ParetoChart } from "@/components/energy/charts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";

const severityVariant: Record<string, "default" | "success" | "warning" | "destructive" | "secondary"> = {
  critical: "destructive",
  high: "destructive",
  medium: "warning",
  low: "secondary",
};

const tcalFormatter = new Intl.NumberFormat("es-CL", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const percentageFormatter = new Intl.NumberFormat("es-CL", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

function formatTcal(value: number): string {
  return `${tcalFormatter.format(value)} tCal`;
}

function formatPercent(value: number | null | undefined): string {
  const numeric = Number(value ?? 0);
  const normalized = Math.abs(numeric) <= 1 ? numeric * 100 : numeric;
  return `${percentageFormatter.format(normalized)}%`;
}

export function DashboardView({ systemId: forcedSystemId }: { systemId?: number } = {}) {
  const [systems, setSystems] = useState<EnergySystem[]>([]);
  const [systemId, setSystemId] = useState<number | null>(forcedSystemId ?? null);
  const [summary, setSummary] = useState<TrackingSummary | null>(null);
  const [kpis, setKpis] = useState<{
    real_consumption: number;
    expected_consumption: number;
    percentage_difference: number;
    open_alerts: number;
  } | null>(null);
  const [realVsExpected, setRealVsExpected] = useState<TrendPoint[]>([]);
  const [ideTrend, setIdeTrend] = useState<TrendPoint[]>([]);
  const [pareto, setPareto] = useState<ParetoItem[]>([]);
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [paretoYear, setParetoYear] = useState<number | null>(null);

  useEffect(() => {
    api.systems().then((items) => {
      setSystems(items);
      if (!forcedSystemId && !systemId) {
        setSystemId(items[0]?.id ?? null);
      }
    });
  }, [forcedSystemId, systemId]);

  useEffect(() => {
    if (!systemId) return;
    let active = true;
    Promise.all([
      api.dashboard(systemId),
      api.systemTrackingSummary(systemId),
      api.energyUseBaseYearPareto(systemId),
      api.systemAlerts(systemId),
    ])
      .then(([dashboardResponse, summaryResponse, paretoResponse, alertsResponse]) => {
        if (!active) return;
        setKpis(dashboardResponse.kpis);
        setRealVsExpected(dashboardResponse.real_vs_expected);
        setIdeTrend(dashboardResponse.ide_trend);
        setSummary(summaryResponse);
        setPareto(paretoResponse);
        setAlerts(alertsResponse);
      })
      .catch(() => {
        if (!active) return;
        setKpis(null);
        setSummary(null);
        setPareto([]);
        setAlerts([]);
      });
    return () => {
      active = false;
    };
  }, [systemId]);

  useEffect(() => {
    if (!pareto.length) {
      setParetoYear(null);
      return;
    }
    const years = [...new Set(pareto.map((item) => item.year))].sort((a, b) => a - b);
    setParetoYear((current) => {
      if (current !== null && years.includes(current)) {
        return current;
      }
      return years.includes(2022) ? 2022 : years[years.length - 1] ?? null;
    });
  }, [pareto]);

  const selectedSystem = useMemo(() => systems.find((item) => item.id === systemId) ?? systems[0] ?? null, [systemId, systems]);
  const paretoYears = useMemo(() => [...new Set(pareto.map((item) => item.year))].sort((a, b) => a - b), [pareto]);
  const selectedParetoData = useMemo(() => pareto.filter((item) => item.year === paretoYear), [pareto, paretoYear]);
  const selectedParetoTotal = useMemo(() => selectedParetoData.reduce((sum, item) => sum + item.value, 0), [selectedParetoData]);

  if (!selectedSystem) {
    return <div className="rounded-3xl border border-slate-200 bg-white p-8 text-slate-600 shadow-sm">Cargando sistema energético...</div>;
  }

  const art21State = summary && summary.incomplete === 0 ? "Cumple base de seguimiento" : "Requiere completar datos";
  const art22State = summary && summary.total_measurements > 0 ? "Plan de recopilación activo" : "Sin registros suficientes";
  const art23State = alerts.length > 0 ? "Con controles y alertas activas" : "Sin alertas abiertas";

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Panel ejecutivo"
        title={selectedSystem.name}
        description="Seguimiento mensual, líneas base, USE, IDEs, alertas y trazabilidad documental en una sola consola operativa."
        actions={
          <div className="flex flex-wrap items-center gap-3">
            {!forcedSystemId ? (
              <Select
                value={systemId ? String(systemId) : ""}
                onChange={(event) => setSystemId(Number(event.target.value))}
                className="min-w-[260px] bg-white"
              >
                {systems.map((system) => (
                  <option key={system.id} value={system.id}>
                    {system.code} - {system.name}
                  </option>
                ))}
              </Select>
            ) : (
              <Badge variant="secondary" className="rounded-full px-4 py-2">
                {selectedSystem.code}
              </Badge>
            )}
            <Button asChild variant="secondary">
              <a href={`/systems/${selectedSystem.id}/measurements`}>Ver registros</a>
            </Button>
            <Button asChild>
              <a href={`/systems/${selectedSystem.id}/measurements/new`}>Nuevo registro mensual</a>
            </Button>
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Consumo real mensual"
          value={`${kpis?.real_consumption?.toLocaleString("es-CL") ?? "--"} ${kpis ? "L" : ""}`}
          helper="Sumatoria mensual del sistema"
        />
        <KpiCard
          label="Consumo esperado"
          value={`${kpis?.expected_consumption?.toLocaleString("es-CL") ?? "--"} ${kpis ? "L" : ""}`}
          helper="Calculado desde la LBEn"
        />
        <KpiCard
          label="Desviación porcentual"
          value={kpis ? `${kpis.percentage_difference.toFixed(2)}%` : "--"}
          helper="Comparación real vs esperado"
          trend={kpis && kpis.percentage_difference <= 10 ? "Dentro del umbral" : "Revisar desviación"}
        />
        <KpiCard
          label="Alertas abiertas"
          value={kpis ? String(kpis.open_alerts) : "--"}
          helper="Eventos de seguimiento"
          trend={summary ? `${summary.compliant} registros conformes` : undefined}
        />
      </div>

      <ComplianceStrip
        items={[
          { label: "Art. 21", value: art21State, variant: "success" },
          { label: "Art. 22", value: art22State, variant: "warning" },
          { label: "Art. 23", value: art23State, variant: "secondary" },
          { label: "Cumplimiento", value: summary ? `${((summary.compliant / Math.max(summary.total_measurements, 1)) * 100).toFixed(1)}%` : "--", variant: "success" },
        ]}
      />

      <div className="grid gap-6 xl:grid-cols-2">
        <SectionCard title="Consumo real vs esperado" description="Comparación mensual del sistema seleccionado.">
          <LineComparisonChart data={realVsExpected} />
        </SectionCard>
        <SectionCard title="IDE real vs esperado" description="Seguimiento del indicador de desempeño energético.">
          <IdeComparisonChart data={ideTrend} />
        </SectionCard>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <SectionCard
          title="Pareto de consumo energético"
          description={`Base para identificación de USE y priorización Art. 21. Año ${paretoYear ?? "--"} · Total ${formatTcal(selectedParetoTotal)}`}
          actions={
            <div className="flex flex-wrap items-center gap-3">
              <Select value={paretoYear ? String(paretoYear) : ""} onChange={(event) => setParetoYear(Number(event.target.value))} className="min-w-[140px] bg-white">
                {paretoYears.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </Select>
              <Badge variant="secondary" className="rounded-full px-4 py-2">
                {formatTcal(selectedParetoTotal)}
              </Badge>
            </div>
          }
        >
          <div className="space-y-5">
            <ParetoChart data={selectedParetoData} />
            <DataTable
              headers={["Área / instalación", "tCal", "% participación", "% acumulado", "Fuente"]}
              rows={selectedParetoData.map((item) => [
                item.label,
                formatTcal(item.value),
                formatPercent(item.percentage),
                formatPercent(item.accumulated_percentage),
                <span key={`${item.year}-${item.label}`} className="text-slate-500">
                  {item.year === 2022 ? "BNE 2022" : `BNE ${item.year}`}
                </span>,
              ])}
              emptyMessage="Sin datos para el año seleccionado."
            />
          </div>
        </SectionCard>
        <SectionCard title="Alertas recientes" description="Alertas generadas por desviación, datos incompletos o IDE fuera de rango.">
          <div className="space-y-3">
            {alerts.slice(0, 6).map((alert) => (
              <div key={alert.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center justify-between gap-3">
                  <AlertBadge severity={alert.severity} />
                  <span className="text-xs text-slate-500">{new Date(alert.created_at).toLocaleString("es-CL")}</span>
                </div>
                <p className="mt-2 text-sm text-slate-700">{alert.message}</p>
              </div>
            ))}
            {!alerts.length ? <p className="text-sm text-slate-500">Sin alertas recientes.</p> : null}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
