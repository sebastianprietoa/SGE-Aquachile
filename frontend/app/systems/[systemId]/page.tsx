import { DashboardView } from "@/components/features/dashboard-view";

export default async function SystemDashboardPage({ params }: { params: Promise<{ systemId: string }> }) {
  const { systemId } = await params;
  return <DashboardView systemId={Number(systemId)} />;
}
