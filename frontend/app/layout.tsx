import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";

import { AppShell } from "@/components/layout/app-shell";
import "./globals.css";

const bodyFont = Inter({ subsets: ["latin"], variable: "--font-body" });
const headingFont = Space_Grotesk({ subsets: ["latin"], variable: "--font-heading" });
const monoFont = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "SGE Aquachile",
  description: "Monitoreo de sistemas de gestión de energía y trazabilidad mensual.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body className={`${bodyFont.variable} ${headingFont.variable} ${monoFont.variable} bg-slate-950 text-slate-50`}>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}

