import type { ReactNode } from "react";
import Link from "next/link";

import { Button } from "@/components/ui/button";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/measurements", label: "Carga energética" },
  { href: "/baselines", label: "Líneas base" },
  { href: "/alerts", label: "Alertas" },
  { href: "/login", label: "Acceso" },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-white/10 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 lg:px-8">
          <div>
            <p className="font-heading text-lg font-semibold text-white">SGE Aquachile</p>
            <p className="text-xs uppercase tracking-[0.24em] text-cyan-200/80">ISO 50001 / Decreto 28</p>
          </div>
          <nav className="hidden items-center gap-2 lg:flex">
            {navItems.map((item) => (
              <Link key={item.href} href={item.href} className="rounded-xl px-3 py-2 text-sm text-slate-200 transition-colors hover:bg-white/10">
                {item.label}
              </Link>
            ))}
          </nav>
          <Button variant="secondary" size="sm">
            Monitoreo en vivo
          </Button>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8 lg:px-8">{children}</main>
    </div>
  );
}
