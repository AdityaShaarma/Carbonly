/** API types aligned with backend responses */

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  company_id: string;
}

export interface Company {
  id: string;
  name: string;
  industry: string | null;
  employee_count: number | null;
  hq_location: string | null;
  reporting_year: number;
  email_notifications: boolean;
  monthly_summary_reports: boolean;
  unit_system: string;
}

export interface MeResponse {
  user: User;
  company: Company;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface ScopeTotal {
  scope: number;
  scope_3_category: string | null;
  total_kg_co2e: number;
  measured_kg_co2e: number;
  estimated_kg_co2e: number;
  manual_kg_co2e: number;
  confidence_score_avg: number | null;
}

export interface MonthlyTrendPoint {
  month: string;
  scope_1: number;
  scope_2: number;
  scope_3: number;
  total: number;
}

export interface DataQualityStats {
  overall_confidence: number | null;
  connected_sources_count: number;
  ai_estimated_sources_count: number;
  manual_entries_count: number;
}

export interface DashboardResponse {
  company_stats: {
    employees: number;
    cloud_providers_count: number;
    reporting_year: number;
  };
  annual_totals: {
    total_co2e: number;
    scope_1: number;
    scope_2: number;
    scope_3: number;
    scope_totals: ScopeTotal[];
    scope3_by_category: { category: string; total_kg_co2e: number }[];
  };
  data_quality: DataQualityStats;
  monthly_trend: MonthlyTrendPoint[];
  data_lineage?: {
    measured_kg_co2e: number;
    estimated_kg_co2e: number;
    manual_kg_co2e: number;
    measured_count: number;
    estimated_count: number;
    manual_count: number;
  };
}

export interface Integration {
  id: string;
  source_type: string;
  display_name: string;
  status: string;
  last_synced_at: string | null;
}

export interface IntegrationsListResponse {
  integrations: Integration[];
}

export interface ReportListItem {
  id: string;
  title: string;
  company_name_snapshot: string | null;
  reporting_year: number;
  total_kg_co2e: number;
  status: string;
  created_at: string;
  shareable_token: string | null;
}

export interface ReportDetail {
  id: string;
  title: string;
  company_name_snapshot: string | null;
  reporting_year: number;
  total_kg_co2e: number;
  status: string;
  shareable_token: string | null;
  content_snapshot: Record<string, unknown> | null;
  created_at: string;
  generated_at: string | null;
  published_at: string | null;
}

export interface Insight {
  id: string;
  title: string;
  description: string;
  impact_level: string;
  estimated_reduction_percent: number | null;
  category: string | null;
}

export interface OnboardingState {
  connect_aws: boolean;
  upload_csv: boolean;
  add_manual_activity: boolean;
  create_report: boolean;
}

export interface OnboardingResponse {
  completed: boolean;
  state: OnboardingState;
}

export interface MethodologyResponse {
  factors_source: string;
  supported_scopes: string[];
  confidence_calculation: string;
  measured_vs_estimated: string;
}

export interface CsvUploadResponse {
  inserted: number;
  errors: { row: number; error: string }[];
}
