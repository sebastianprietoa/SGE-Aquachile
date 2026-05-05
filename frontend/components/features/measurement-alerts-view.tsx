"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { AlertEvent } from "@/types/api";

const severityVariant: Record<string, "default" | "success" | "warning" | "destructive" | "secondary"> = {
  critical: "destructive",
  high: "destructive",
  medium: "warning",
  low: "secondary",
};

export function MeasurementAlertsView({ measurementId }: { measurementId: number }) {
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);

  useEffect(() => {
    api.measurementAlerts(measurementId).then(setAlerts);
  }, [measurementId]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Alertas asociadas a la medición</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Severidad</TableHead>
              <TableHead>Estado</TableHead>
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
                <TableCell>{alert.message}</TableCell>
                <TableCell>{new Date(alert.created_at).toLocaleString("es-CL")}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

