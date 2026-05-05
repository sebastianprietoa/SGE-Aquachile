import { DynamicMeasurementForm } from "@/components/energy/measurement-form";

export function MeasurementWizard({
  mode,
  measurementId,
}: {
  mode: "create" | "edit";
  measurementId?: number;
}) {
  return <DynamicMeasurementForm measurementId={mode === "edit" ? measurementId : undefined} />;
}
