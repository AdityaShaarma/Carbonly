import type { MethodologyResponse } from "@/types/api";
import { api } from "./client";

export async function fetchMethodology(): Promise<MethodologyResponse> {
  const { data } = await api.get<MethodologyResponse>("/api/methodology");
  return data;
}
