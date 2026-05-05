"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { BaselineVariableV2, OperationalControl, TrackingMonthlyRow } from "@/types/api";
import { StatusBadge } from "@/components/energy/shared";

export function BaselineVariableTable({ variables }: { variables: BaselineVariableV2[] }) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <Table>
        <TableHeader className="bg-[#183f44]">
          <TableRow className="hover:bg-[#183f44]">
            <TableHead className="text-white">Variable</TableHead>
            <TableHead className="text-white">Tipo</TableHead>
            <TableHead className="text-white">Unidad</TableHead>
            <TableHead className="text-white">Requerida</TableHead>
            <TableHead className="text-white">Rango</TableHead>
            <TableHead className="text-white">Frecuencia</TableHead>
            <TableHead className="text-white">Procedimiento</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {variables.map((variable) => (
            <TableRow key={variable.id}>
              <TableCell className="font-medium text-slate-900">{variable.variable_name}</TableCell>
              <TableCell>{variable.variable_type}</TableCell>
              <TableCell>{variable.unit ?? "-"}</TableCell>
              <TableCell>
                <Badge variant={variable.required ? "destructive" : "secondary"}>{variable.required ? "Sí" : "No"}</Badge>
              </TableCell>
              <TableCell>
                {variable.min_value ?? "-"} a {variable.max_value ?? "-"}
              </TableCell>
              <TableCell>{variable.frequency ?? "-"}</TableCell>
              <TableCell className="max-w-[300px] text-sm text-slate-600">{variable.missing_data_procedure ?? variable.measurement_reason ?? "-"}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export function TrackingMonthlyTable({ rows }: { rows: TrackingMonthlyRow[] }) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <Table>
        <TableHeader className="bg-[#183f44]">
          <TableRow className="hover:bg-[#183f44]">
            <TableHead className="text-white">Periodo</TableHead>
            <TableHead className="text-white">Real</TableHead>
            <TableHead className="text-white">Esperado</TableHead>
            <TableHead className="text-white">IDE real</TableHead>
            <TableHead className="text-white">IDE esperado</TableHead>
            <TableHead className="text-white">Desviación</TableHead>
            <TableHead className="text-white">Estado</TableHead>
            <TableHead className="text-white">Comentarios</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row) => (
            <TableRow key={row.id}>
              <TableCell className="font-medium text-slate-900">
                {String(row.month).padStart(2, "0")}/{row.year}
              </TableCell>
              <TableCell>{row.real_consumption.toLocaleString("es-CL")}</TableCell>
              <TableCell>{row.expected_consumption?.toLocaleString("es-CL") ?? "-"}</TableCell>
              <TableCell>{row.ide_real?.toFixed(2) ?? "-"}</TableCell>
              <TableCell>{row.ide_expected?.toFixed(2) ?? "-"}</TableCell>
              <TableCell>{row.percentage_difference?.toFixed(2) ?? "-"}%</TableCell>
              <TableCell><StatusBadge value={row.compliance_status} /></TableCell>
              <TableCell className="max-w-[220px] text-sm text-slate-600">{row.comments ?? "-"}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

export function OperationalControlPanel({ controls }: { controls: OperationalControl[] }) {
  return (
    <div className="grid gap-4 xl:grid-cols-2">
      {controls.map((control) => (
        <Card key={control.id} className="border-slate-200 bg-white shadow-sm">
          <CardHeader>
            <CardTitle className="font-heading text-xl text-slate-900">{control.name}</CardTitle>
            <CardDescription>
              {control.responsible_area ?? "-"} · {control.responsible_person ?? "-"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-slate-600">
            <p><strong className="text-slate-800">Técnico:</strong> {control.technical_criteria ?? "-"}</p>
            <p><strong className="text-slate-800">Administrativo:</strong> {control.administrative_criteria ?? "-"}</p>
            <p><strong className="text-slate-800">Mantención:</strong> {control.maintenance_criteria ?? "-"}</p>
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary">{control.record_frequency ?? "Mensual"}</Badge>
              <Badge variant={control.training_required ? "warning" : "secondary"}>{control.training_required ? "Capacitación requerida" : "Sin capacitación"}</Badge>
              <Badge variant="secondary">{control.record_type ?? "Registro"}</Badge>
            </div>
            {control.effectiveness_evaluation_method ? (
              <p><strong className="text-slate-800">Eficacia:</strong> {control.effectiveness_evaluation_method}</p>
            ) : null}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
