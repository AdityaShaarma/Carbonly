import type { Company } from "@/types/api";
import { api } from "./client";

export async function fetchCompany(): Promise<Company> {
  const { data } = await api.get<Company>("/api/company");
  return data;
}

export async function updateCompany(payload: Partial<Company>): Promise<Company> {
  const { data } = await api.put<Company>("/api/company", payload);
  return data;
}

export async function updatePreferences(payload: {
  email_notifications?: boolean;
  monthly_summary_reports?: boolean;
  unit_system?: string;
}): Promise<Company> {
  const { data } = await api.put<Company>("/api/company/preferences", payload);
  return data;
}

export async function deleteCompanyData(confirm: boolean): Promise<{ status: string }> {
  const { data } = await api.delete("/api/company/data", { data: { confirm } });
  return data as { status: string };
}
