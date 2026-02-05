import type { Insight } from "@/types/api";
import { api } from "./client";

export async function fetchInsights(year: number): Promise<{ insights: Insight[] }> {
  const { data } = await api.get<{ insights: Insight[] }>("/api/insights", { params: { year } });
  return data;
}
