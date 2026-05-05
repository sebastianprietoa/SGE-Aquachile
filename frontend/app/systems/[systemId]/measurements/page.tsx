"use client";

import Link from "next/link";
import { use, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import type { AlertEvent, EnergyArea, EnergySystem, EnergyUse, MonthlyMeasurement } from "@/types/api";
import { AlertBadge, PageHeader, SectionCard, StatusBadge } from "@/components/energy/shared";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { DataTable } from "@/components/energy/shared";

export default function MeasurementsPage({ params }: { params: Promise<{ systemId: string }> }) {
  const { systemId } = use(params);
  const systemIdNumber = Number(systemId);
  const [system, setSystem] = useState<EnergySystem | null>(null);
  const [areas, setAreas] = useState<EnergyArea[]>([]);
  const [uses, setUses] = useState<EnergyUse[]>([]);
  const [measurements, setMeasurements] = useState<MonthlyMeasurement[]>([]);
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [filters, setFilters] = useState({ year: "", month: "", areaId: "", useId: "", status: "", severity: "" });

  useEffect(() => {
    let active = true;
    Promise.all([api.system(systemIdNumber), api.areas(systemIdNumber), api.energyUses(systemIdNumber), api.measurements(systemIdNumber), api.systemAlerts(systemIdNumber)])
      .then(([systemResponse, areaResponse, useResponse, measurementResponse, alertResponse]) => {
        if (!active) return;
        setSystem(systemResponse);
        setAreas(areaResponse);
        setUses(useResponse);
        setMeasurements(measurementResponse);
        setAlerts(alertResponse);
      })
      .catch(() => {
        if (!active) return;
        setSystem(null);
        setAreas([]);
        setUses([]);
        setMeasurements([]);
        setAlerts([]);
      });
    return () => {
      active = false;
    };
  }, [systemIdNumber]);

  const filtered = useMemo(
    () =>
      measurements.filter((item) => {
        const matchesYear = !filters.year || item.year === Number(filters.year);
        const matchesMonth = !filters.month || item.month === Number(filters.month);
        const matchesArea = !filters.areaId || item.area_id === Number(filters.areaId);
        const matchesUse = !filters.useId || item.energy_use_id === Number(filters.useId);
        const matchesStatus = !filters.status || item.status === filters.status;
        const severityMatches =
          !filters.severity ||
          alerts.some((alert) => alert.monthly_measurement_id === item.id && alert.severity === filters.severity);
        return matchesYear && matchesMonth && matchesArea && matchesUse && matchesStatus && severityMatches;
      }),
    [alerts, filters, measurements],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Carga mensual"
        title={`Registros mensuales · ${system?.name ?? "Sistema"}`}
        description="La tabla se filtra por año, mes, área, uso, estado y severidad de alerta, manteniendo trazabilidad completa."
        actions={
          <Button asChild>
            <Link href={`/systems/${systemIdNumber}/measurements/new`}>Nuevo registro mensual</Link>
          </Button>
        }
      />

      <SectionCard title="Filtros" description="Búsqueda de registros y alertas vinculadas.">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
          <Input placeholder="Año" value={filters.year} onChange={(event) => setFilters((current) => ({ ...current, year: event.target.value }))} />
          <Input placeholder="Mes" value={filters.month} onChange={(event) => setFilters((current) => ({ ...current, month: event.target.value }))} />
          <Select value={filters.areaId} onChange={(event) => setFilters((current) => ({ ...current, areaId: event.target.value }))}>
            <option value="">Área</option>
            {areas.map((area) => (
              <option key={area.id} value={area.id}>
                {area.name}
              </option>
            ))}
          </Select>
          <Select value={filters.useId} onChange={(event) => setFilters((current) => ({ ...current, useId: event.target.value }))}>
            <option value="">Uso</option>
            {uses.map((energyUse) => (
              <option key={energyUse.id} value={energyUse.id}>
                {energyUse.name}
              </option>
            ))}
          </Select>
          <Select value={filters.status} onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}>
            <option value="">Estado</option>
            <option value="draft">draft</option>
            <option value="submitted">submitted</option>
            <option value="reviewed">reviewed</option>
            <option value="approved">approved</option>
            <option value="rejected">rejected</option>
          </Select>
          <Select value={filters.severity} onChange={(event) => setFilters((current) => ({ ...current, severity: event.target.value }))}>
            <option value="">Severidad</option>
            <option value="critical">critical</option>
            <option value="high">high</option>
            <option value="medium">medium</option>
            <option value="low">low</option>
          </Select>
        </div>
      </SectionCard>

      <SectionCard title="Registros mensuales" description="Editar, revisar historial y ver alertas asociadas.">
        <DataTable
          headers={["Periodo", "Área", "Uso", "Real", "Esperado", "Desviación", "Estado", "Acciones"]}
          rows={filtered.map((measurement) => [
            `${String(measurement.month).padStart(2, "0")}/${measurement.year}`,
            areas.find((item) => item.id === measurement.area_id)?.name ?? measurement.area_id,
            uses.find((item) => item.id === measurement.energy_use_id)?.name ?? measurement.energy_use_id,
            measurement.real_consumption.toLocaleString("es-CL"),
            measurement.expected_consumption?.toLocaleString("es-CL") ?? "-",
            `${measurement.percentage_difference?.toFixed(2) ?? "-"}%`,
            <StatusBadge key={`${measurement.id}-status`} value={measurement.compliance_status} />,
            <div key={`${measurement.id}-actions`} className="flex flex-wrap gap-2">
              <Button asChild size="sm" variant="secondary">
                <Link href={`/measurements/${measurement.id}/edit`}>Editar</Link>
              </Button>
              <Button asChild size="sm" variant="ghost">
                <Link href={`/measurements/${measurement.id}/history`}>Historial</Link>
              </Button>
              <Button asChild size="sm" variant="ghost">
                <Link href={`/measurements/${measurement.id}/alerts`}>Alertas</Link>
              </Button>
            </div>,
          ])}
          emptyMessage="No existen registros para el filtro actual."
        />
      </SectionCard>

      <div className="grid gap-6 xl:grid-cols-[1fr_0.8fr]">
        <SectionCard title="Alertas recientes" description="Severidad y estado de eventos asociados al sistema.">
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
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
