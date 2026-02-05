import { Navigate, RouteObject } from "react-router-dom";
import { Layout } from "@/components/layout/Layout";
import { ProtectedRoute } from "@/components/routes/ProtectedRoute";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { IntegrationsPage } from "@/pages/IntegrationsPage";
import { ManualDataPage } from "@/pages/ManualDataPage";
import { ReportsPage } from "@/pages/ReportsPage";
import { ReportDetailPage } from "@/pages/ReportDetailPage";
import { PublicReportPage } from "@/pages/PublicReportPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { InsightsPage } from "@/pages/InsightsPage";
import { OnboardingPage } from "@/pages/OnboardingPage";
import { MethodologyPage } from "@/pages/MethodologyPage";
import { HealthPage } from "@/pages/HealthPage";
import { BillingPage } from "@/pages/BillingPage";

export const routes: RouteObject[] = [
  { path: "/login", element: <LoginPage /> },
  { path: "/r/:shareToken", element: <PublicReportPage /> },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "onboarding", element: <OnboardingPage /> },
      { path: "integrations", element: <IntegrationsPage /> },
      { path: "manual", element: <ManualDataPage /> },
      { path: "reports", element: <ReportsPage /> },
      { path: "reports/:reportId", element: <ReportDetailPage /> },
      { path: "methodology", element: <MethodologyPage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "insights", element: <InsightsPage /> },
      { path: "billing", element: <BillingPage /> },
      { path: "health", element: <HealthPage /> },
    ],
  },
  { path: "*", element: <Navigate to="/dashboard" replace /> },
];
