"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { AlertEvent, EnergyArea, EnergySystem, EnergyUse, MonthlyMeasurement } from "@/types/api";

const severityVariant: Record<string, "default" | "success" | "warning" | "destructive" | "secondary"> = {
  critical: "destructive",
  high: "destructive",
  medium: "warning",
  low: "secondary",
};

export function MeasurementTable() {
  const [systems, setSystems] = useState<EnergySystem[]>([]);
  const [areas, setAreas] = useState<EnergyArea[]>([]);
  const [uses, setUses] = useState<EnergyUse[]>([]);
  const [measurements, setMeasurements] = useState<MonthlyMeasurement[]>([]);
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [systemId, setSystemId] = useState<number | null>(null);
  const [filters, setFilters] = useState({ year: "", month: "", areaId: "", useId: "", status: "", severity: "" });

  useEffect(() => {
    api.systems().then((items) => {
      setSystems(items);
      if (items[0]) {
        setSystemId(items[0].id);
      }
    });
  }, []);

  useEffect(() => {
    if (!systemId) return;
    Promise.all([api.areas(systemId), api.energyUses(systemId), api.measurements(systemId), api.systemAlerts(systemId)]).then(([areaItems, useItems, measurementItems, alertItems]) => {
      setAreas(areaItems);
      setUses(useItems);
      setMeasurements(measurementItems);
      setAlerts(alertItems);
    });
  }, [systemId]);

  const alertMeasurementIds = useMemo(() => {
    if (!filters.severity) return new Set<number>();
    return new Set(alerts.filter((item) => item.severity === filters.severity).map((item) => item.monthly_measurement_id));
  }, [alerts, filters.severity]);

  const filteredMeasurements = measurements.filter((item) => {
    const matchesYear = !filters.year || item.year === Number(filters.year);
    const matchesMonth = !filters.month || item.month === Number(filters.month);
    const matchesArea = !filters.areaId || item.area_id === Number(filters.areaId);
    const matchesUse = !filters.useId || item.energy_use_id === Number(filters.useId);
    const matchesStatus = !filters.status || item.status === filters.status;
    const matchesSeverity = !filters.severity || alertMeasurementIds.has(item.id);
    return matchesYear && matchesMonth && matchesArea && matchesUse && matchesStatus && matchesSeverity;
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Carga de información energética</CardTitle>
          <CardDescription>Tabla de registros mensuales, edición, historial y alertas.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-7">
          <Select value={systemId ? String(systemId) : ""} onChange={(event) => setSystemId(Number(event.target.value))}>
            {systems.map((system) => (
              <option key={system.id} value={system.id}>
                {system.code}
              </option>
            ))}
          </Select>
          <Input placeholder="Año" value={filters.year} onChange={(event) => setFilters((current) => ({ ...current, year: event.target.value }))} />
          <Input placeholder="Mes" value={filters.month} onChange={(event) => setFilters((current) => ({ ...current, month: event.target.value }))} />
          <Select value={filters.areaId} onChange={(event) => setFilters((current) => ({ ...current, areaId: event.target.value }))}>
            <option value="">Todas las áreas</option>
            {areas.map((area) => (
              <option key={area.id} value={area.id}>
                {area.name}
              </option>
            ))}
          </Select>
          <Select value={filters.useId} onChange={(event) => setFilters((current) => ({ ...current, useId: event.target.value }))}>
            <option value="">Todos los usos</option>
            {uses.map((energyUse) => (
              <option key={energyUse.id} value={energyUse.id}>
                {energyUse.name}
              </option>
            ))}
          </Select>
          <Select value={filters.status} onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}>
            <option value="">Todos los estados</option>
            <option value="draft">draft</option>
            <option value="submitted">submitted</option>
            <option value="reviewed">reviewed</option>
            <option value="approved">approved</option>
            <option value="rejected">rejected</option>
          </Select>
          <Select value={filters.severity} onChange={(event) => setFilters((current) => ({ ...current, severity: event.target.value }))}>
            <option value="">Todas las severidades</option>
            <option value="critical">critical</option>
            <option value="high">high</option>
            <option value="medium">medium</option>
            <option value="low">low</option>
          </Select>
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
        <div className="text-sm text-slate-300">{filteredMeasurements.length} registros encontrados</div>
        <Button asChild>
          <Link href="/measurements/new">Nuevo registro mensual</Link>
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Periodo</TableHead>
            <TableHead>Área</TableHead>
            <TableHead>Uso</TableHead>
            <TableHead>Real</TableHead>
            <TableHead>Esperado</TableHead>
            <TableHead>Desviación</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead>Acciones</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {filteredMeasurements.map((measurement) => (
            <TableRow key={measurement.id}>
              <TableCell>
                {measurement.month}/{measurement.year}
              </TableCell>
              <TableCell>{areas.find((item) => item.id === measurement.area_id)?.name ?? measurement.area_id}</TableCell>
              <TableCell>{uses.find((item) => item.id === measurement.energy_use_id)?.name ?? measurement.energy_use_id}</TableCell>
              <TableCell>{measurement.real_consumption.toLocaleString("es-CL")}</TableCell>
              <TableCell>{measurement.expected_consumption?.toLocaleString("es-CL") ?? "--"}</TableCell>
              <TableCell>{measurement.percentage_difference?.toFixed(2) ?? "--"}%</TableCell>
              <TableCell>
                <Badge variant={measurement.compliance_status === "compliant" ? "success" : measurement.compliance_status === "warning" ? "warning" : measurement.compliance_status === "non_compliant" ? "destructive" : "secondary"}>
                  {measurement.status}
                </Badge>
              </TableCell>
              <TableCell>
                <div className="flex flex-wrap gap-2">
                  <Button asChild size="sm" variant="secondary">
                    <Link href={`/measurements/${measurement.id}/edit`}>Editar</Link>
                  </Button>
                  <Button asChild size="sm" variant="ghost">
                    <Link href={`/measurements/${measurement.id}/history`}>Ver historial</Link>
                  </Button>
                  <Button asChild size="sm" variant="ghost">
                    <Link href={`/measurements/${measurement.id}/alerts`}>Ver alertas</Link>
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {!filteredMeasurements.length ? <p className="text-sm text-slate-400">No existen registros para el filtro actual.</p> : null}

      <Card>
        <CardHeader>
          <CardTitle>Alertas de sistema</CardTitle>
          <CardDescription>Severidad y estado de las alertas asociadas al sistema seleccionado.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {alerts.slice(0, 5).map((alert) => (
            <div key={alert.id} className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
              <div className="flex items-center justify-between gap-3">
                <Badge variant={severityVariant[alert.severity] ?? "secondary"}>{alert.severity}</Badge>
                <span className="text-xs text-slate-400">{new Date(alert.created_at).toLocaleString("es-CL")}</span>
              </div>
              <p className="mt-2 text-sm text-slate-200">{alert.message}</p>
            </div>
          ))}
          {!alerts.length ? <p className="text-sm text-slate-400">Sin alertas.</p> : null}
        </CardContent>
      </Card>
    </div>
  );
}
