"use client";

import { use, useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { DataCollectionPlanItem, EnergySystem } from "@/types/api";
import { PageHeader, SectionCard } from "@/components/energy/shared";
import { DataTable } from "@/components/energy/shared";

export default function DataCollectionPlanPage({ params }: { params: Promise<{ systemId: string }> }) {
  const { systemId } = use(params);
  const systemIdNumber = Number(systemId);
  const [system, setSystem] = useState<EnergySystem | null>(null);
  const [plan, setPlan] = useState<DataCollectionPlanItem[]>([]);

  useEffect(() => {
    let active = true;
    Promise.all([api.system(systemIdNumber), api.dataCollectionPlan(systemIdNumber)])
      .then(([systemResponse, planResponse]) => {
        if (!active) return;
        setSystem(systemResponse);
        setPlan(planResponse);
      })
      .catch(() => {
        if (!active) return;
        setSystem(null);
        setPlan([]);
      });
    return () => {
      active = false;
    };
  }, [systemIdNumber]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Art. 22"
        title={`Plan de recopilación de datos · ${system?.name ?? "Sistema"}`}
        description="Documenta qué se mide, por qué, cómo se recopila, dónde se almacena, quién es responsable y qué ocurre ante datos faltantes."
      />

      <SectionCard title="Plan de recopilación" description="Variables pertinentes por USE y LBEn.">
        <DataTable
          headers={["Variable", "USE", "LBEn", "Qué se mide", "Por qué", "Método", "Almacenamiento", "Responsable", "Frecuencia", "Dato faltante", "Rango"]}
          rows={plan.map((item) => [
            item.variable_name,
            item.use_name,
            item.baseline_name,
            item.what_is_measured ?? "-",
            item.why_it_is_measured ?? "-",
            item.collection_method ?? "-",
            item.storage_location ?? "-",
            `${item.responsible_area ?? "-"} / ${item.responsible_person ?? "-"}`,
            item.frequency ?? "-",
            item.missing_data_procedure ?? "-",
            `${item.min_value ?? "-"} a ${item.max_value ?? "-"}`,
          ])}
          emptyMessage="Sin variables documentadas para este sistema."
        />
      </SectionCard>
    </div>
  );
}
