import type { DashboardResponse } from "@/types/api";
import { api } from "./client";

export async function fetchDashboard(year: number): Promise<DashboardResponse> {
  const { data } = await api.get<DashboardResponse>("/api/dashboard", { params: { year } });
  return data;
}

export async function recomputeEmissions(year: number): Promise<{ estimates_created: number; summaries_refreshed: number }> {
  const { data } = await api.post("/api/dashboard/recompute", null, { params: { year } });
  return data as { estimates_created: number; summaries_refreshed: number };
}
