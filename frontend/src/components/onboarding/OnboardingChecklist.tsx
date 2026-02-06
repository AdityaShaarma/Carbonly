import { useMutation, useQuery } from "react-query";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { requestEmailVerification } from "@/api/auth";
import { fetchOnboarding, updateOnboarding } from "@/api/onboarding";
import { fetchReports } from "@/api/reports";
import { useYearSelector } from "@/hooks/useYearSelector";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/Button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";

function StepStatus({ done, label }: { done: boolean; label: string }) {
  return (
    <span
      className={
        done ? "text-sm text-primary" : "text-sm text-muted-foreground"
      }
    >
      {done ? "Done" : label}
    </span>
  );
}

export function OnboardingChecklist() {
  const { user, company } = useAuth();
  const navigate = useNavigate();
  const { year } = useYearSelector();
  const { data: reports, isLoading: reportsLoading } = useQuery(
    ["reports", year],
    () => fetchReports(year)
  );
  const { data: onboarding } = useQuery("onboarding", fetchOnboarding);

  const requestVerify = useMutation(
    () => requestEmailVerification(user?.email),
    {
      onSuccess: () => toast.success("Verification email sent"),
      onError: () => toast.error("Failed to send verification email"),
    }
  );

  const emailVerified = user?.is_email_verified ?? false;
  const profileComplete =
    Boolean(company?.name?.trim()) &&
    Boolean(company?.industry?.trim()) &&
    Boolean(company?.hq_location?.trim()) &&
    (company?.employee_count ?? 0) > 0;
  const orgConfirmed =
    profileComplete && Boolean(onboarding?.state?.confirm_company_details);
  const hasReport = (reports?.reports?.length ?? 0) > 0;
  const firstReport = reports?.reports?.[0];
  const pdfDownloaded =
    sessionStorage.getItem("carbonly_pdf_downloaded") === "true";
  const isPro = company?.plan === "pro";
  const coreComplete = emailVerified && orgConfirmed && hasReport;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Onboarding checklist</CardTitle>
        <CardDescription>
          Complete these steps to generate your first report
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">1) Verify your email</p>
            <p className="text-sm text-muted-foreground">
              Required to publish reports and enable notifications
            </p>
          </div>
          {emailVerified ? (
            <StepStatus done label="Pending" />
          ) : (
            <Button
              size="sm"
              variant="outline"
              onClick={() => requestVerify.mutate()}
              isLoading={requestVerify.isLoading}
              disabled={requestVerify.isLoading}
            >
              Send verification
            </Button>
          )}
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">2) Confirm company details</p>
            <p className="text-sm text-muted-foreground">
              Confirm your company profile for reporting
            </p>
          </div>
          {orgConfirmed ? (
            <StepStatus done label="Pending" />
          ) : profileComplete ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => updateOnboarding({ confirm_company_details: true })}
            >
              Confirm details
            </Button>
          ) : (
            <Link to="/settings">
              <Button size="sm" variant="outline">
                Update profile
              </Button>
            </Link>
          )}
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">3) Create your first report</p>
            <p className="text-sm text-muted-foreground">
              Generate a procurement-ready disclosure
            </p>
          </div>
          {hasReport ? (
            <StepStatus done label="Pending" />
          ) : (
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => navigate("/reports")}
            >
              Go to reports
            </Button>
          )}
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">4) Download your PDF report</p>
            <p className="text-sm text-muted-foreground">
              Share a customer-ready PDF with procurement teams
            </p>
          </div>
          {!isPro ? (
            <Button size="sm" variant="outline" onClick={() => navigate("/billing")}>
              Pro feature · Upgrade
            </Button>
          ) : hasReport && pdfDownloaded ? (
            <StepStatus done label="Pending" />
          ) : hasReport && firstReport ? (
            <Link to={`/reports/${firstReport.id}`}>
              <Button size="sm" variant="outline" disabled={reportsLoading}>
                Open report
              </Button>
            </Link>
          ) : (
            <StepStatus done={false} label="Pending" />
          )}
        </div>
        {coreComplete && (
          <div className="rounded-md border border-border bg-muted/50 px-3 py-2 text-sm text-muted-foreground">
            You&apos;re ready to publish your first carbon report
          </div>
        )}
      </CardContent>
    </Card>
  );
}
