"use client";

import { use } from "react";

import { DynamicMeasurementForm } from "@/components/energy/measurement-form";
import { PageHeader } from "@/components/energy/shared";

export default function NewSystemMeasurementPage({ params }: { params: Promise<{ systemId: string }> }) {
  const { systemId } = use(params);
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Carga mensual"
        title="Nuevo registro mensual"
        description="El formulario se genera dinámicamente desde la LBEn seleccionada y no permite variables fuera de catálogo."
      />
      <DynamicMeasurementForm systemId={Number(systemId)} />
    </div>
  );
}
