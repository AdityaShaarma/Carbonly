import { useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { useAuth } from "@/contexts/AuthContext";
import { fetchReports } from "@/api/reports";
import { fetchOnboarding, updateOnboarding } from "@/api/onboarding";
import { requestEmailVerification } from "@/api/auth";
import { syncProvider } from "@/api/integrations";
import { useYearSelector } from "@/hooks/useYearSelector";
import toast from "react-hot-toast";

export function OnboardingPage() {
  const queryClient = useQueryClient();
  const { user, company, refetchMe } = useAuth();
  const { year } = useYearSelector();
  const { data: reports } = useQuery(["reports", year], () => fetchReports(year));
  const { data: onboarding } = useQuery("onboarding", fetchOnboarding);
  useEffect(() => {
    refetchMe();
  }, [refetchMe]);

  const verifyEmail = useMutation(() => requestEmailVerification(user?.email), {
    onSuccess: () => {
      toast.success("Verification email sent");
      queryClient.invalidateQueries("onboarding");
      queryClient.invalidateQueries(["dashboard", year]);
    },
    onError: () => toast.error("Couldn’t send verification email"),
  });
  const confirmCompany = useMutation(
    () => updateOnboarding({ confirm_company_details: true }),
    {
      onSuccess: () => {
        queryClient.setQueryData("onboarding", (prev: any) => ({
          ...prev,
          state: { ...(prev?.state ?? {}), confirm_company_details: true },
        }));
        queryClient.invalidateQueries("onboarding");
        queryClient.invalidateQueries(["dashboard", year]);
        refetchMe();
        toast.success("Company details confirmed");
      },
      onError: () => toast.error("Couldn’t confirm company details"),
    }
  );
  const loadSample = useMutation(() => syncProvider("aws"), {
    onSuccess: () => {
      queryClient.invalidateQueries("integrations");
      queryClient.invalidateQueries(["dashboard", year]);
      queryClient.invalidateQueries(["reports", year]);
      toast.success("Sample data loaded");
    },
    onError: () => toast.error("Sample data couldn’t load"),
  });

  const hasReport = (reports?.reports?.length ?? 0) > 0;
  const firstReport = reports?.reports?.[0];
  const pdfDownloaded =
    sessionStorage.getItem("carbonly_pdf_downloaded") === "true";
  const isPro = company?.plan === "pro";
  const isDemo = user?.is_demo ?? false;

  const profileComplete =
    Boolean(company?.name?.trim()) &&
    Boolean(company?.industry?.trim()) &&
    Boolean(company?.hq_location?.trim()) &&
    (company?.employee_count ?? 0) > 0;
  const companyConfirmed =
    profileComplete && Boolean(onboarding?.state?.confirm_company_details);

  const steps = [
    {
      key: "verify_email",
      title: "Verify your email",
      description: "Required to publish your report",
      complete: user?.is_email_verified ?? false,
      action: (
        <Button
          size="sm"
          variant="outline"
          onClick={() => verifyEmail.mutate()}
          isLoading={verifyEmail.isLoading}
          disabled={verifyEmail.isLoading}
        >
          Send verification
        </Button>
      ),
    },
    {
      key: "confirm_company",
      title: "Confirm company details",
      description: "Ensure your report uses accurate company information",
      complete: companyConfirmed,
      action: profileComplete ? (
        <Button
          size="sm"
          variant="outline"
          onClick={() => confirmCompany.mutate()}
          isLoading={confirmCompany.isLoading}
          disabled={confirmCompany.isLoading || companyConfirmed}
        >
          Confirm details
        </Button>
      ) : (
        <Link to="/settings">
          <Button size="sm" variant="outline">
            Update profile
          </Button>
        </Link>
      ),
    },
    {
      key: "create_report",
      title: "Create your first report",
      description: "Generate a customer-ready carbon report",
      complete: hasReport,
      action: (
        <Link to="/reports">
          <Button size="sm" variant="outline">
            Go to reports
          </Button>
        </Link>
      ),
    },
    {
      key: "finish_share",
      title: "Finish & share your report",
      description: "Export a customer-ready PDF (Pro)",
      complete: isPro && pdfDownloaded,
      action: !isPro ? (
        <Link to="/billing">
          <Button size="sm" variant="outline">
            Upgrade to Pro
          </Button>
        </Link>
      ) : hasReport && firstReport ? (
        <Link to={`/reports/${firstReport.id}`}>
          <Button size="sm" variant="outline">
            Open report
          </Button>
        </Link>
      ) : (
        <Button size="sm" variant="outline" disabled>
          Create a report first
        </Button>
      ),
    },
  ];

  const completedCount = steps.filter((s) => s.complete).length;
  const nextStep = steps.find((s) => !s.complete) ?? steps[steps.length - 1];

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <h1 className="text-2xl font-semibold">
          Create your first carbon report in minutes
        </h1>
        <p className="text-sm text-muted-foreground">
          Customers and regulators increasingly ask for carbon disclosures.
          Carbonly helps you produce procurement-ready carbon disclosures in
          minutes, using measured data or defensible estimates—no consultants
          required.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <Link to="/integrations">
            <Button size="lg">Add your first data</Button>
          </Link>
          {isDemo && (
            <Button
              variant="outline"
              size="lg"
              onClick={() => loadSample.mutate()}
              isLoading={loadSample.isLoading}
            >
              Load sample data
            </Button>
          )}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Progress</CardTitle>
          <CardDescription>
            {completedCount} of {steps.length} completed
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-md border border-border bg-muted/40 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="font-medium">{nextStep.title}</p>
                <p className="text-sm text-muted-foreground">
                  {nextStep.description}
                </p>
              </div>
              <div>{nextStep.action}</div>
            </div>
          </div>

          {steps.filter((s) => s.complete).length > 0 && (
            <div className="space-y-2 text-sm text-muted-foreground">
              {steps
                .filter((s) => s.complete)
                .map((s) => (
                  <div key={s.key} className="flex items-center gap-2 opacity-70">
                    <span className="h-1.5 w-1.5 rounded-full bg-primary/60" />
                    <span>{s.title}</span>
                  </div>
                ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
