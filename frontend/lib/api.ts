import { getStoredToken } from "@/lib/auth";
import type {
  AlertEvent,
  AlertRule,
  BaselineModel,
  BaselineVariable,
  DashboardResponse,
  EnergyArea,
  EnergySystem,
  EnergyUse,
  IdeDefinition,
  MonthlyMeasurement,
  MonthlyMeasurementCreatePayload,
  MonthlyMeasurementUpdatePayload,
  PerformanceSummaryResponse,
  TrendPoint,
  LoginResponse,
  LoginRequest,
  MeasurementAuditLog,
  MonthlyMeasurementVariableInput,
} from "@/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  const token = getStoredToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const message = payload?.detail ?? payload?.message ?? `Request failed: ${response.status}`;
    throw new Error(Array.isArray(message) ? message.join(", ") : message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  login: (payload: LoginRequest) => request<LoginResponse>("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  systems: () => request<EnergySystem[]>("/systems"),
  system: (id: number) => request<EnergySystem>(`/systems/${id}`),
  dashboard: (id: number) => request<DashboardResponse>(`/systems/${id}/dashboard`),
  performanceSummary: (id: number) => request<PerformanceSummaryResponse>(`/systems/${id}/performance-summary`),
  monthlyTrends: (id: number) => request<TrendPoint[]>(`/systems/${id}/monthly-trends`),
  areas: (id: number) => request<EnergyArea[]>(`/systems/${id}/areas`),
  energyUses: (id: number) => request<EnergyUse[]>(`/systems/${id}/energy-uses`),
  baselines: (id: number) => request<BaselineModel[]>(`/systems/${id}/baselines`),
  baseline: (id: number) => request<BaselineModel>(`/baselines/${id}`),
  baselineVariables: (id: number) => request<BaselineVariable[]>(`/baselines/${id}/variables`),
  ides: (id: number) => request<IdeDefinition[]>(`/systems/${id}/ides`),
  measurements: (systemId: number, query?: Record<string, string | number | undefined>) => {
    const params = new URLSearchParams();
    Object.entries(query ?? {}).forEach(([key, value]) => {
      if (value !== undefined && value !== "") {
        params.set(key, String(value));
      }
    });
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return request<MonthlyMeasurement[]>(`/systems/${systemId}/measurements${suffix}`);
  },
  measurement: (id: number) => request<MonthlyMeasurement>(`/measurements/${id}`),
  createMeasurement: (systemId: number, payload: MonthlyMeasurementCreatePayload) =>
    request<MonthlyMeasurement>(`/systems/${systemId}/measurements`, { method: "POST", body: JSON.stringify(payload) }),
  updateMeasurement: (id: number, payload: MonthlyMeasurementUpdatePayload) =>
    request<MonthlyMeasurement>(`/measurements/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  submitMeasurement: (id: number) => request<MonthlyMeasurement>(`/measurements/${id}/submit`, { method: "POST" }),
  approveMeasurement: (id: number) => request<MonthlyMeasurement>(`/measurements/${id}/approve`, { method: "POST" }),
  rejectMeasurement: (id: number) => request<MonthlyMeasurement>(`/measurements/${id}/reject`, { method: "POST" }),
  measurementAuditLog: (id: number) => request<MeasurementAuditLog[]>(`/measurements/${id}/audit-log`),
  measurementAlerts: (id: number) => request<AlertEvent[]>(`/measurements/${id}/alerts`),
  systemAlerts: (id: number) => request<AlertEvent[]>(`/systems/${id}/alerts`),
  alertRules: (payload: AlertRule) => request<AlertRule>("/alert-rules", { method: "POST", body: JSON.stringify(payload) }),
  updateAlertRule: (id: number, payload: Partial<AlertRule>) => request<AlertRule>(`/alert-rules/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
};

