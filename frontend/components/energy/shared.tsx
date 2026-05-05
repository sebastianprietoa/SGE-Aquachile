"use client";

import type { ReactNode } from "react";

import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type BadgeVariant = "default" | "secondary" | "success" | "warning" | "destructive";

export function PageHeader({
  title,
  description,
  eyebrow,
  actions,
}: {
  title: string;
  description: string;
  eyebrow?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div className="space-y-2">
        {eyebrow ? <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">{eyebrow}</p> : null}
        <h1 className="font-heading text-4xl font-semibold tracking-tight text-slate-900">{title}</h1>
        <p className="max-w-4xl text-[15px] leading-6 text-slate-600">{description}</p>
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
    </div>
  );
}

export function KpiCard({
  label,
  value,
  helper,
  trend,
}: {
  label: string;
  value: string;
  helper?: string;
  trend?: string;
}) {
  return (
    <Card className="border-slate-200/80 bg-white shadow-sm">
      <CardContent className="space-y-2 p-5">
        <p className="text-[11px] font-semibold uppercase tracking-[0.26em] text-slate-500">{label}</p>
        <p className="font-heading text-3xl font-semibold text-slate-900">{value}</p>
        {helper ? <p className="text-sm text-slate-500">{helper}</p> : null}
        {trend ? <p className="text-xs font-medium text-emerald-700">{trend}</p> : null}
      </CardContent>
    </Card>
  );
}

const statusVariantMap: Record<string, BadgeVariant> = {
  compliant: "success",
  warning: "warning",
  non_compliant: "destructive",
  incomplete: "secondary",
  draft: "secondary",
  submitted: "warning",
  reviewed: "secondary",
  approved: "success",
  rejected: "destructive",
  critical: "destructive",
  high: "destructive",
  medium: "warning",
  low: "secondary",
  open: "warning",
  closed: "success",
};

export function StatusBadge({ value, className }: { value: string; className?: string }) {
  return <Badge variant={statusVariantMap[value] ?? "secondary"} className={className}>{value}</Badge>;
}

export function AlertBadge({ severity }: { severity: string }) {
  return <Badge variant={statusVariantMap[severity] ?? "secondary"}>{severity}</Badge>;
}

export function ComplianceStrip({
  items,
}: {
  items: Array<{ label: string; value: string; variant?: BadgeVariant }>;
}) {
  return (
    <div className="flex flex-wrap gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-3 rounded-2xl bg-slate-50 px-4 py-3">
          <span className="text-sm text-slate-600">{item.label}</span>
          <Badge variant={item.variant ?? "secondary"}>{item.value}</Badge>
        </div>
      ))}
    </div>
  );
}

export function DataTable({
  headers,
  rows,
  emptyMessage = "Sin registros.",
  className,
}: {
  headers: string[];
  rows: ReactNode[][];
  emptyMessage?: string;
  className?: string;
}) {
  return (
    <div className={cn("overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm", className)}>
      <Table>
        <TableHeader className="bg-[#183f44]">
          <TableRow className="hover:bg-[#183f44]">
            {headers.map((header) => (
              <TableHead key={header} className="h-12 text-[11px] uppercase tracking-[0.22em] text-white">
                {header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.length ? (
            rows.map((row, rowIndex) => (
              <TableRow key={rowIndex} className="border-slate-200">
                {row.map((cell, cellIndex) => (
                  <TableCell key={`${rowIndex}-${cellIndex}`} className="align-top text-[13px] text-slate-700">
                    {cell}
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={headers.length} className="py-10 text-center text-sm text-slate-500">
                {emptyMessage}
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );
}

export function SectionCard({
  title,
  description,
  children,
  actions,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <Card className="border-slate-200/80 bg-white shadow-sm">
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div className="space-y-1">
          <CardTitle className="font-heading text-2xl text-slate-900">{title}</CardTitle>
          {description ? <CardDescription className="text-slate-600">{description}</CardDescription> : null}
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}
