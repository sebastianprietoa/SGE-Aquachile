"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ParetoItem, TrackingMonthlyRow, TrendPoint } from "@/types/api";

const tooltipStyle = {
  background: "#f8fafc",
  border: "1px solid rgba(148,163,184,0.35)",
  borderRadius: 16,
  boxShadow: "0 16px 40px rgba(15,23,42,0.12)",
};

const tcalFormatter = new Intl.NumberFormat("es-CL", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const percentageFormatter = new Intl.NumberFormat("es-CL", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

function normalizePercent(value: number | string | undefined | null): number {
  if (value === undefined || value === null || value === "") {
    return 0;
  }
  const numeric = typeof value === "string" ? Number(value.replace(",", ".")) : Number(value);
  if (Number.isNaN(numeric)) {
    return 0;
  }
  return Math.abs(numeric) <= 1 ? numeric * 100 : numeric;
}

function formatTcal(value: number | string | undefined | null): string {
  const numeric = typeof value === "string" ? Number(value.replace(",", ".")) : Number(value ?? 0);
  return `${tcalFormatter.format(Number.isFinite(numeric) ? numeric : 0)} tCal`;
}

function formatPercentage(value: number | string | undefined | null): string {
  return `${percentageFormatter.format(normalizePercent(value))}%`;
}

export function ParetoChart({ data }: { data: ParetoItem[] }) {
  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data}>
          <CartesianGrid stroke="rgba(148,163,184,0.22)" strokeDasharray="3 3" />
          <XAxis dataKey="label" tick={{ fill: "#64748b", fontSize: 12 }} interval={0} angle={-12} textAnchor="end" height={70} />
          <YAxis yAxisId="left" tick={{ fill: "#64748b", fontSize: 12 }} tickFormatter={(value) => tcalFormatter.format(Number(value))} />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fill: "#64748b", fontSize: 12 }}
            domain={[0, 100]}
            tickFormatter={(value) => percentageFormatter.format(Number(value))}
          />
          <Tooltip
            contentStyle={tooltipStyle}
            formatter={(value, name) => {
              if (name === "Consumo") {
                return [formatTcal(value as number | string), name];
              }
              if (name === "% acumulado") {
                return [formatPercentage(value as number | string), name];
              }
              return [String(value), String(name)];
            }}
            labelFormatter={(label, payload) => {
              const year = payload?.[0]?.payload?.year;
              return `${label}${year ? ` · ${year}` : ""}`;
            }}
          />
          <Legend />
          <Bar yAxisId="left" dataKey="value" fill="#0f766e" radius={[8, 8, 0, 0]} name="Consumo" />
          <Line yAxisId="right" type="monotone" dataKey="accumulated_percentage" stroke="#16a34a" strokeWidth={2.5} dot={false} name="% acumulado" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export function LineComparisonChart({ data }: { data: Array<TrendPoint | TrackingMonthlyRow> }) {
  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid stroke="rgba(148,163,184,0.22)" strokeDasharray="3 3" />
          <XAxis dataKey="month" tick={{ fill: "#64748b", fontSize: 12 }} />
          <YAxis tick={{ fill: "#64748b", fontSize: 12 }} />
          <Tooltip contentStyle={tooltipStyle} />
          <Legend />
          <Line type="monotone" dataKey="real_consumption" stroke="#0f766e" strokeWidth={3} dot={{ r: 3 }} name="Real" />
          <Line type="monotone" dataKey="expected_consumption" stroke="#16a34a" strokeWidth={3} dot={{ r: 3 }} name="Esperado" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function DeviationChart({ data }: { data: Array<TrackingMonthlyRow | TrendPoint> }) {
  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid stroke="rgba(148,163,184,0.22)" strokeDasharray="3 3" />
          <XAxis dataKey="month" tick={{ fill: "#64748b", fontSize: 12 }} />
          <YAxis tick={{ fill: "#64748b", fontSize: 12 }} />
          <Tooltip contentStyle={tooltipStyle} />
          <Legend />
          <Line type="monotone" dataKey="percentage_difference" stroke="#b45309" strokeWidth={3} dot={false} name="% desviación" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function IdeComparisonChart({ data }: { data: Array<TrackingMonthlyRow | TrendPoint> }) {
  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid stroke="rgba(148,163,184,0.22)" strokeDasharray="3 3" />
          <XAxis dataKey="month" tick={{ fill: "#64748b", fontSize: 12 }} />
          <YAxis tick={{ fill: "#64748b", fontSize: 12 }} />
          <Tooltip contentStyle={tooltipStyle} />
          <Legend />
          <Line type="monotone" dataKey="ide_real" stroke="#7c3aed" strokeWidth={3} dot={false} name="IDE real" />
          <Line type="monotone" dataKey="ide_expected" stroke="#0f766e" strokeWidth={3} dot={false} name="IDE esperado" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
