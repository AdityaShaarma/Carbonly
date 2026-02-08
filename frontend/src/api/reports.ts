import type { ReportDetail, ReportListItem } from "@/types/api";
import { api } from "./client";

export async function fetchReports(year?: number): Promise<{ reports: ReportListItem[] }> {
  const { data } = await api.get<{ reports: ReportListItem[] }>("/api/reports", {
    params: year != null ? { year } : undefined,
  });
  return data;
}

export async function createReport(title: string, reporting_year: number): Promise<ReportDetail> {
  const { data } = await api.post<ReportDetail>("/api/reports", { title, reporting_year });
  return data;
}

export async function fetchReport(reportId: string): Promise<ReportDetail> {
  const { data } = await api.get<ReportDetail>(`/api/reports/${reportId}`);
  return data;
}

export async function publishReport(reportId: string): Promise<{ status: string; shareable_token: string }> {
  const { data } = await api.post<{ status: string; shareable_token: string }>(
    `/api/reports/${reportId}/publish`
  );
  return data;
}

export async function deleteReport(reportId: string): Promise<{ status: string }> {
  const { data } = await api.delete<{ status: string }>(`/api/reports/${reportId}`);
  return data;
}

export async function openReportPdf(
  reportId: string,
  reportingYear: number,
  reportTitle?: string
): Promise<void> {
  const { data } = await api.get<Blob>(`/api/reports/${reportId}/pdf`, {
    responseType: "blob",
  });
  const blob = data;
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  const safeTitle = reportTitle
    ? reportTitle.replace(/[^\w\- ]+/g, "").trim().replace(/\s+/g, "-")
    : `carbonly-report-${reportingYear}`;
  link.download = `${safeTitle}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export async function fetchPublicReport(shareToken: string): Promise<{
  company_name: string;
  reporting_year: number;
  total_co2e: number;
  executive_summary: string;
  scope_breakdown: { scope_1: number; scope_2: number; scope_3: number };
  scope_3_breakdown: Record<string, number>;
}> {
  const base = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
  const res = await fetch(`${base}/api/reports/r/${shareToken}`);
  if (!res.ok) throw new Error("Report not found");
  return res.json();
}
