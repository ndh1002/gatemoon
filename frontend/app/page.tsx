import { fetchLatest } from "@/lib/api";
import { Dashboard } from "@/components/Dashboard";

export const dynamic = "force-dynamic";

export default async function Page() {
  let initial = null;
  try {
    initial = await fetchLatest();
  } catch {
    initial = { type: "empty", rows: [], generated_at: null };
  }
  return <Dashboard initial={initial} />;
}
