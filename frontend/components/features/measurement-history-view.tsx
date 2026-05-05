"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { MeasurementAuditLog } from "@/types/api";

export function MeasurementHistoryView({ measurementId }: { measurementId: number }) {
  const [logs, setLogs] = useState<MeasurementAuditLog[]>([]);

  useEffect(() => {
    api.measurementAuditLog(measurementId).then(setLogs);
  }, [measurementId]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Historial de modificaciones</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Acción</TableHead>
              <TableHead>Campo</TableHead>
              <TableHead>Anterior</TableHead>
              <TableHead>Nuevo</TableHead>
              <TableHead>Comentario</TableHead>
              <TableHead>Fecha</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {logs.map((log) => (
              <TableRow key={log.id}>
                <TableCell>{log.action}</TableCell>
                <TableCell>{log.field_name ?? "--"}</TableCell>
                <TableCell>{log.old_value ?? "--"}</TableCell>
                <TableCell>{log.new_value ?? "--"}</TableCell>
                <TableCell>{log.comment ?? "--"}</TableCell>
                <TableCell>{new Date(log.created_at).toLocaleString("es-CL")}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

