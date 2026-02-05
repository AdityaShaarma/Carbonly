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
    !hasReports;

  useEffect(() => {
    if (shouldOnboard && location.pathname !== "/onboarding") {
      navigate("/onboarding", { replace: true });
    }
  }, [shouldOnboard, location.pathname, navigate]);

  return <>{children}</>;
}
