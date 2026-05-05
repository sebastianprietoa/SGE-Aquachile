"use client";

import { useEffect, useState } from "react";
import { Area, AreaChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { api } from "@/lib/api";
import type { DashboardResponse, EnergySystem, PerformanceSummaryResponse } from "@/types/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";

const severityToVariant: Record<string, "default" | "success" | "warning" | "destructive" | "secondary"> = {
  critical: "destructive",
  high: "destructive",
  medium: "warning",
  low: "secondary",
};

export function DashboardView() {
  const [systems, setSystems] = useState<EnergySystem[]>([]);
  const [systemId, setSystemId] = useState<number | null>(null);
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [summary, setSummary] = useState<PerformanceSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        setLoading(true);
        const items = await api.systems();
        if (!active) return;
        setSystems(items);
        const first = items[0];
        if (first) {
          setSystemId(first.id);
        }
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "No fue posible cargar los sistemas");
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const currentSystemId = systemId;
    if (!currentSystemId) return;
    const systemToLoad = currentSystemId;
    let active = true;
    async function loadDetails() {
      try {
        const [dashboardResponse, summaryResponse] = await Promise.all([api.dashboard(systemToLoad), api.performanceSummary(systemToLoad)]);
        if (!active) return;
        setDashboard(dashboardResponse);
        setSummary(summaryResponse);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "No fue posible cargar el dashboard");
      }
    }
    loadDetails();
    return () => {
      active = false;
    };
  }, [systemId]);

  if (loading && !dashboard) {
    return <div className="rounded-3xl border border-white/10 bg-white/5 p-8 text-slate-200">Cargando sistema energético...</div>;
  }

  if (!systems.length) {
    return <div className="rounded-3xl border border-white/10 bg-white/5 p-8 text-slate-200">No hay sistemas cargados.</div>;
  }

  const kpis = dashboard?.kpis;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <CardTitle>Dashboard principal</CardTitle>
            <CardDescription>Seguimiento energético mensual, desempeño e ինտensidad energética.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {[
                { label: "Consumo real", value: kpis ? `${kpis.real_consumption.toLocaleString("es-CL")} kWh` : "--" },
                { label: "Consumo esperado", value: kpis ? `${kpis.expected_consumption.toLocaleString("es-CL")} kWh` : "--" },
                { label: "Desviación", value: kpis ? `${kpis.percentage_difference.toFixed(2)}%` : "--" },
                { label: "Alertas abiertas", value: kpis ? `${kpis.open_alerts}` : "--" },
              ].map((item) => (
                <div key={item.label} className="rounded-2xl border border-white/10 bg-slate-900/60 p-4">
                  <p className="text-xs uppercase tracking-[0.22em] text-slate-400">{item.label}</p>
                  <p className="mt-2 font-heading text-2xl font-semibold text-white">{item.value}</p>
                </div>
              ))}
            </div>
            {summary ? (
              <div className="mt-4 flex flex-wrap gap-3 text-sm text-slate-300">
                <Badge variant="success">Cumplimiento {summary.compliance_rate.toFixed(1)}%</Badge>
                <Badge variant="secondary">Total mediciones {summary.total_measurements}</Badge>
                <Badge variant="warning">Warnings {summary.warning}</Badge>
                <Badge variant="destructive">No conformes {summary.non_compliant}</Badge>
              </div>
            ) : null}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Selector de sistema</CardTitle>
            <CardDescription>ELF y AquaChile operan como contextos energéticos separados.</CardDescription>
          </CardHeader>
          <CardContent>
            <Select value={systemId ? String(systemId) : ""} onChange={(event) => setSystemId(Number(event.target.value))}>
              {systems.map((system) => (
                <option key={system.id} value={system.id}>
                  {system.code} - {system.name}
                </option>
              ))}
            </Select>
            {error ? <p className="mt-3 text-sm text-rose-200">{error}</p> : null}
            <div className="mt-4 rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-4 text-sm text-cyan-100">
              La lógica central del sistema es línea base, variables requeridas, medición mensual, cálculo de desempeño y alertas.
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Consumo real vs esperado</CardTitle>
            <CardDescription>Comparación mensual del sistema seleccionado.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={dashboard?.real_vs_expected ?? []}>
                  <defs>
                    <linearGradient id="realFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#67e8f9" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#67e8f9" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="expectedFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#34d399" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#34d399" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(255,255,255,0.08)" strokeDasharray="3 3" />
                  <XAxis dataKey="month" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip contentStyle={{ background: "#020617", border: "1px solid rgba(255,255,255,0.1)" }} />
                  <Area type="monotone" dataKey="real_consumption" stroke="#67e8f9" fill="url(#realFill)" name="Real" />
                  <Area type="monotone" dataKey="expected_consumption" stroke="#34d399" fill="url(#expectedFill)" name="Esperado" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>IDE real vs esperado</CardTitle>
            <CardDescription>Seguimiento del indicador de desempeño energético.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={dashboard?.ide_trend ?? []}>
                  <CartesianGrid stroke="rgba(255,255,255,0.08)" strokeDasharray="3 3" />
                  <XAxis dataKey="month" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip contentStyle={{ background: "#020617", border: "1px solid rgba(255,255,255,0.1)" }} />
                  <Line type="monotone" dataKey="ide_real" stroke="#f59e0b" strokeWidth={2} dot={false} name="IDE real" />
                  <Line type="monotone" dataKey="ide_expected" stroke="#22c55e" strokeWidth={2} dot={false} name="IDE esperado" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <CardTitle>Tendencia mensual</CardTitle>
            <CardDescription>Resumen de consumo por mes.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={dashboard?.real_vs_expected ?? []}>
                  <CartesianGrid stroke="rgba(255,255,255,0.08)" strokeDasharray="3 3" />
                  <XAxis dataKey="month" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip contentStyle={{ background: "#020617", border: "1px solid rgba(255,255,255,0.1)" }} />
                  <Line type="monotone" dataKey="real_consumption" stroke="#67e8f9" strokeWidth={2} dot={false} name="Real" />
                  <Line type="monotone" dataKey="expected_consumption" stroke="#34d399" strokeWidth={2} dot={false} name="Esperado" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Alertas recientes</CardTitle>
            <CardDescription>Eventos generados por desviaciones, rangos y datos incompletos.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(dashboard?.recent_alerts ?? []).map((alert) => (
              <div key={alert.id} className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
                <div className="flex items-center justify-between gap-3">
                  <Badge variant={severityToVariant[alert.severity] ?? "secondary"}>{alert.severity}</Badge>
                  <span className="text-xs text-slate-400">{new Date(alert.created_at).toLocaleString("es-CL")}</span>
                </div>
                <p className="mt-2 text-sm text-slate-100">{alert.message}</p>
              </div>
            ))}
            {!dashboard?.recent_alerts?.length ? <p className="text-sm text-slate-400">Sin alertas recientes.</p> : null}
            <div className="pt-2">
              <Button variant="secondary">Ver detalle operativo</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
