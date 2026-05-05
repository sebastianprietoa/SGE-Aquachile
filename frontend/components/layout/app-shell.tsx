"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import type { EnergySystem } from "@/types/api";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";

const navSections = [
  { label: "Dashboard", href: (systemId: number) => `/systems/${systemId}` },
  { label: "Usos energéticos", href: (systemId: number) => `/systems/${systemId}/energy-uses` },
  { label: "USE", href: (systemId: number) => `/systems/${systemId}/significant-energy-uses` },
  { label: "Líneas base", href: (systemId: number) => `/systems/${systemId}/baselines` },
  { label: "IDEs", href: (systemId: number) => `/systems/${systemId}/ides` },
  { label: "Seguimiento", href: (systemId: number) => `/systems/${systemId}/tracking` },
  { label: "Carga mensual", href: (systemId: number) => `/systems/${systemId}/measurements` },
  { label: "Plan de datos", href: (systemId: number) => `/systems/${systemId}/data-collection-plan` },
  { label: "Controles op.", href: (systemId: number) => `/systems/${systemId}/operational-controls` },
  { label: "Alertas", href: (systemId: number) => `/alerts` },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [systems, setSystems] = useState<EnergySystem[]>([]);

  useEffect(() => {
    api.systems().then(setSystems).catch(() => setSystems([]));
  }, []);

  const currentSystemId = useMemo(() => {
    const match = pathname.match(/\/systems\/(\d+)/);
    if (match) {
      return Number(match[1]);
    }
    return systems[0]?.id ?? 1;
  }, [pathname, systems]);

  const currentSystem = systems.find((item) => item.id === currentSystemId) ?? systems[0];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      <div className="grid min-h-screen lg:grid-cols-[250px_1fr]">
        <aside className="border-r border-white/10 bg-[#15343a] px-5 py-6 text-slate-100 shadow-[inset_-1px_0_0_rgba(255,255,255,0.03)]">
          <div className="mb-8">
            <p className="font-heading text-[1.9rem] font-semibold leading-none text-white">
              SGE<span className="text-emerald-300">AquaChile</span>
            </p>
            <p className="mt-2 text-xs uppercase tracking-[0.28em] text-emerald-100/70">ISO 50001 · Decreto 28</p>
          </div>
          <nav className="space-y-2">
            {navSections.map((item) => {
              const href = item.href(currentSystemId);
              const active = pathname === href || pathname.startsWith(`${href}/`);
              return (
                <Link
                  key={item.label}
                  href={href}
                  className={`flex items-center rounded-2xl px-4 py-3 text-[15px] transition-all ${
                    active
                      ? "bg-emerald-400/14 text-white ring-1 ring-emerald-300/20 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]"
                      : "text-slate-200/90 hover:bg-white/8 hover:text-white"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>
        <div className="flex min-h-screen flex-col">
          <header className="border-b border-slate-200/60 bg-slate-50/95 px-5 py-4 text-slate-900 backdrop-blur lg:px-8">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div>
                <p className="text-4xl font-semibold tracking-tight text-slate-800">
                  {currentSystem?.name ?? "SGE Aquachile"}
                </p>
                <p className="mt-1 max-w-4xl text-[15px] text-slate-500">
                  Monitoreo de desempeño energético, trazabilidad mensual, líneas base, USE, IDEs y controles operacionales.
                </p>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-900">
                  Sistema activo: {currentSystem?.code ?? "--"} · {currentSystem?.name ?? "Seleccionar sistema"}
                </div>
                <div className="min-w-[280px]">
                  <Select
                    value={currentSystemId ? String(currentSystemId) : ""}
                    onChange={(event) => router.push(`/systems/${event.target.value}`)}
                    className="bg-white text-slate-900"
                  >
                    {systems.map((system) => (
                      <option key={system.id} value={system.id}>
                        {system.code} - {system.name}
                      </option>
                    ))}
                  </Select>
                </div>
                <Button variant="secondary" onClick={() => router.push(`/systems/${currentSystemId}/measurements/new`)}>
                  Nuevo registro mensual
                </Button>
              </div>
            </div>
          </header>
          <main className="flex-1 bg-slate-100 px-5 py-6 lg:px-8">{children}</main>
        </div>
      </div>
    </div>
  );
}
