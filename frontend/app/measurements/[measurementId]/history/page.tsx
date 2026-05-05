import { MeasurementHistoryView } from "@/components/features/measurement-history-view";

export default async function MeasurementHistoryPage({ params }: { params: Promise<{ measurementId: string }> }) {
  const { measurementId } = await params;
  return <MeasurementHistoryView measurementId={Number(measurementId)} />;
}

