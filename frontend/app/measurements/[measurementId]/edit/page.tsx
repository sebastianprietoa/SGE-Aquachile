import { MeasurementWizard } from "@/components/features/measurement-wizard";

export default async function EditMeasurementPage({ params }: { params: Promise<{ measurementId: string }> }) {
  const { measurementId } = await params;
  return <MeasurementWizard mode="edit" measurementId={Number(measurementId)} />;
}
