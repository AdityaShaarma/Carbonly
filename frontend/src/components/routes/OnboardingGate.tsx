import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useQuery } from "react-query";
import { fetchOnboarding } from "@/api/onboarding";
import { fetchIntegrations } from "@/api/integrations";
import { fetchDashboard } from "@/api/dashboard";
import { fetchReports } from "@/api/reports";
import { useYearSelector } from "@/hooks/useYearSelector";

export function OnboardingGate({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { year } = useYearSelector();
  // avoid trapping users; onboarding is a nudge, not a hard block.
  const ALWAYS_ALLOWED = [
    "/onboarding",
    "/reports",
    "/settings",
    "/manual",
    "/integrations",
  ];

  const { data: onboarding } = useQuery("onboarding", fetchOnboarding);
  const { data: integrations } = useQuery("integrations", fetchIntegrations);
  const { data: dashboard } = useQuery(["dashboard", year], () =>
    fetchDashboard(year)
  );
  const { data: reports } = useQuery(["reports", year], () =>
    fetchReports(year)
  );

  const hasIntegrations =
    integrations?.integrations?.some((i) => i.status !== "not_connected") ??
    false;
  const hasManual = (dashboard?.data_lineage?.manual_count ?? 0) > 0;
  const hasReports = (reports?.reports?.length ?? 0) > 0;

  const shouldOnboard =
    onboarding &&
    !onboarding.completed &&
    !hasIntegrations &&
    !hasManual &&
    !hasReports &&
    (location.pathname === "/dashboard" || location.pathname === "/");
  const isAllowedRoute = ALWAYS_ALLOWED.some(
    (path) =>
      location.pathname === path || location.pathname.startsWith(`${path}/`)
  );

  useEffect(() => {
    if (shouldOnboard && !isAllowedRoute) {
      navigate("/onboarding", { replace: true });
    }
  }, [shouldOnboard, isAllowedRoute, navigate]);

  return <>{children}</>;
}
