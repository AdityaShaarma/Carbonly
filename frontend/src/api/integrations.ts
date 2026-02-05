import type { CsvUploadResponse, IntegrationsListResponse } from "@/types/api";
import { api } from "./client";

export async function fetchIntegrations(): Promise<IntegrationsListResponse> {
  const { data } = await api.get<IntegrationsListResponse>("/api/integrations");
  return data;
}

export async function syncProvider(provider: string): Promise<{ status: string; activities_created?: number }> {
  const { data } = await api.post(`/api/integrations/${provider}/sync`);
  return data as { status: string; activities_created?: number };
}

export async function estimateProvider(provider: string): Promise<{ status: string; activity_created?: boolean }> {
  const { data } = await api.post(`/api/integrations/${provider}/estimate`);
  return data as { status: string; activity_created?: boolean };
}

export interface ManualActivityPayload {
  scope: number;
  scope_3_category?: string | null;
  activity_type: string;
  quantity: number;
  unit: string;
  period_start: string;
  period_end: string;
  data_quality?: string;
  assumptions?: string | null;
  confidence_score?: number | null;
}

export async function createManualActivity(payload: ManualActivityPayload): Promise<{ id: string; status: string }> {
  const { data } = await api.post("/api/integrations/manual/activity", payload);
  return data as { id: string; status: string };
}

export async function uploadCsv(file: File): Promise<CsvUploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<CsvUploadResponse>("/api/integrations/manual/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
