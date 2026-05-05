"use client";

import { use, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { EnergySystem, OperationalControl } from "@/types/api";
import { PageHeader, SectionCard } from "@/components/energy/shared";
import { OperationalControlPanel } from "@/components/energy/tables";

export default function OperationalControlsPage({ params }: { params: Promise<{ systemId: string }> }) {
  const { systemId } = use(params);
  const systemIdNumber = Number(systemId);
  const [system, setSystem] = useState<EnergySystem | null>(null);
  const [controls, setControls] = useState<OperationalControl[]>([]);

  useEffect(() => {
    let active = true;
    Promise.all([api.system(systemIdNumber), api.operationalControls(systemIdNumber)])
      .then(([systemResponse, controlResponse]) => {
        if (!active) return;
        setSystem(systemResponse);
        setControls(controlResponse);
      })
      .catch(() => {
        if (!active) return;
        setSystem(null);
        setControls([]);
      });
    return () => {
      active = false;
    };
  }, [systemIdNumber]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Art. 23"
        title={`Controles operacionales · ${system?.name ?? "Sistema"}`}
        description="Criterios técnicos, administrativos y de mantención asociados a los USE, junto con capacitación y evaluación de eficacia."
      />

      <SectionCard title="Controles operacionales" description="Registros y criterios de operación para los USE.">
        <OperationalControlPanel controls={controls} />
      </SectionCard>
    </div>
  );
}
