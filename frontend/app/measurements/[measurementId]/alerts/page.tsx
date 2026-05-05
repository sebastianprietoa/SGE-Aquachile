import { MeasurementAlertsView } from "@/components/features/measurement-alerts-view";

export default async function MeasurementAlertsPage({ params }: { params: Promise<{ measurementId: string }> }) {
  const { measurementId } = await params;
  return <MeasurementAlertsView measurementId={Number(measurementId)} />;
}

