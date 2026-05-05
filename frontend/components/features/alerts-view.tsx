"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { AlertEvent, EnergySystem } from "@/types/api";

const severityVariant: Record<string, "default" | "success" | "warning" | "destructive" | "secondary"> = {
  critical: "destructive",
  high: "destructive",
  medium: "warning",
  low: "secondary",
};

export function AlertsView() {
  const [systems, setSystems] = useState<EnergySystem[]>([]);
  const [systemId, setSystemId] = useState<number | null>(null);
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);

  useEffect(() => {
    api.systems().then((items) => {
      setSystems(items);
      if (items[0]) setSystemId(items[0].id);
    });
  }, []);

  useEffect(() => {
    if (!systemId) return;
    api.systemAlerts(systemId).then(setAlerts);
  }, [systemId]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Alertas</CardTitle>
          <CardDescription>Listado de alertas generadas por el sistema de monitoreo energético.</CardDescription>
        </CardHeader>
        <CardContent>
          <Select value={systemId ? String(systemId) : ""} onChange={(event) => setSystemId(Number(event.target.value))}>
            {systems.map((system) => (
              <option key={system.id} value={system.id}>
                {system.code}
              </option>
            ))}
          </Select>
        </CardContent>
      </Card>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Severidad</TableHead>
            <TableHead>Estado</TableHead>
            <TableHead>Medición</TableHead>
            <TableHead>Mensaje</TableHead>
            <TableHead>Fecha</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {alerts.map((alert) => (
            <TableRow key={alert.id}>
              <TableCell>
                <Badge variant={severityVariant[alert.severity] ?? "secondary"}>{alert.severity}</Badge>
              </TableCell>
              <TableCell>{alert.status}</TableCell>
              <TableCell>{alert.monthly_measurement_id}</TableCell>
              <TableCell>{alert.message}</TableCell>
              <TableCell>{new Date(alert.created_at).toLocaleString("es-CL")}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

