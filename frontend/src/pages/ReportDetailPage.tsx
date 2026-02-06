import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { fetchReport, publishReport, openReportPdf } from "@/api/reports";
import { fetchOnboarding } from "@/api/onboarding";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import toast from "react-hot-toast";
import { formatEmissions } from "@/utils/format";
import { DEMO_MODE } from "@/config/env";
import { useAuth } from "@/contexts/AuthContext";
import { Link } from "react-router-dom";
import { ProFeatureGate } from "@/components/billing/ProFeatureGate";

export function ReportDetailPage() {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, company } = useAuth();
  const [copied, setCopied] = useState(false);
  const [showPublishConfirm, setShowPublishConfirm] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  const {
    data: report,
    isLoading,
    error,
  } = useQuery(["report", reportId], () => fetchReport(reportId!), {
    enabled: !!reportId,
  });
  const { data: onboarding } = useQuery("onboarding", fetchOnboarding);

  const publish = useMutation(() => publishReport(reportId!), {
    onSuccess: () => {
      queryClient.invalidateQueries(["report", reportId]);
      queryClient.invalidateQueries("reports");
      toast.success("Report published");
    },
    onError: () => toast.error("Publish failed"),
  });

  function publicUrl(token: string) {
    const base = window.location.origin;
    return `${base}/r/${token}`;
  }

  const shareLink = report?.shareable_token
    ? publicUrl(report.shareable_token)
    : "";

  const handleCopyShare = () => {
    if (!shareLink) return;
    navigator.clipboard.writeText(shareLink);
    setCopied(true);
    toast.success("Link copied");
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOpenPdf = async () => {
    if (isDownloading) return;
    setIsDownloading(true);
    try {
      await openReportPdf(reportId!, report.reporting_year);
      sessionStorage.setItem("carbonly_pdf_downloaded", "true");
      toast.success("PDF downloaded");
    } catch (err) {
      toast.error("Failed to download PDF");
    } finally {
      setIsDownloading(false);
    }
  };

  if (error || !reportId) {
    return (
      <div>
        <p className="text-destructive">Report not found.</p>
        <Button
          variant="outline"
          className="mt-2"
          onClick={() => navigate("/reports")}
        >
          Back to reports
        </Button>
      </div>
    );
  }

  if (isLoading || !report) {
    return <div className="animate-pulse space-y-4 rounded-lg bg-muted h-64" />;
  }

  const content = report.content_snapshot as Record<string, unknown> | null;
  const executiveSummary = content?.executive_summary as string | undefined;
  const requiresVerification = user ? !user.is_email_verified : false;
  const isPro = company?.plan === "pro";
  const profileComplete =
    Boolean(company?.name?.trim()) &&
    Boolean(company?.industry?.trim()) &&
    Boolean(company?.hq_location?.trim()) &&
    (company?.employee_count ?? 0) > 0;
  const companyConfirmed =
    profileComplete && Boolean(onboarding?.state?.confirm_company_details);
  const requiresCompanyConfirm = !companyConfirmed;

  const statusBadge = (status: string) => {
    const base = "inline-flex items-center rounded-full px-2 py-0.5 text-xs";
    if (status === "published") {
      return `${base} bg-emerald-100 text-emerald-700`;
    }
    return `${base} bg-muted text-muted-foreground`;
  };

  return (
    <div className="space-y-6">
      {showPublishConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
          <div className="w-full max-w-md rounded-lg bg-card p-6 shadow-lg">
            <h2 className="text-lg font-semibold">Publish report?</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Publishing will generate a public share link. You can’t unpublish
              from the public view.
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowPublishConfirm(false)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={() => {
                  setShowPublishConfirm(false);
                  publish.mutate();
                }}
                isLoading={publish.isLoading}
              >
                Publish
              </Button>
            </div>
          </div>
        </div>
      )}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">{report.title}</h1>
        <div className="flex flex-col items-end gap-2">
          {requiresVerification && (
            <span className="text-xs text-muted-foreground">
              Verify your email to publish or download PDFs.
            </span>
          )}
          {requiresCompanyConfirm && (
            <span className="text-xs text-muted-foreground">
              Please confirm your company details before publishing.{" "}
              <Link to="/settings" className="text-primary hover:underline">
                Go to settings
              </Link>
            </span>
          )}
          {!isPro && (
            <span className="text-xs text-muted-foreground">
              Pro feature{" "}
              <Link to="/billing" className="text-primary hover:underline">
                Upgrade to Pro
              </Link>
            </span>
          )}
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleOpenPdf}
              disabled={
                isDownloading || requiresVerification || !isPro
              }
              title={
                requiresVerification
                  ? "Email verification required to download PDFs"
                  : !isPro
                  ? "Pro plan required to download PDFs"
                  : undefined
              }
            >
              {isDownloading ? (
                <span className="inline-flex items-center gap-2">
                  <span className="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Downloading
                </span>
              ) : (
                "Download PDF"
              )}
            </Button>
            {report.status === "draft" && !DEMO_MODE && (
              <Button
                size="sm"
                onClick={() => setShowPublishConfirm(true)}
                isLoading={publish.isLoading}
                disabled={requiresVerification || !isPro || requiresCompanyConfirm}
                title={
                  requiresVerification
                    ? "Email verification required to publish reports"
                    : !isPro
                    ? "Pro plan required to publish reports"
                    : requiresCompanyConfirm
                    ? "Confirm your company details to publish reports"
                    : undefined
                }
              >
                Publish
              </Button>
            )}
          </div>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
          <CardDescription>
            {report.company_name_snapshot} · {report.reporting_year} ·{" "}
            {formatEmissions(report.total_kg_co2e)}
          </CardDescription>
        </CardHeader>
        <CardContent className="prose prose-sm max-w-none">
          <div className="mb-3">
            <span className={statusBadge(report.status)}>{report.status}</span>
          </div>
          {executiveSummary && (
            <p className="whitespace-pre-wrap">{executiveSummary}</p>
          )}
        </CardContent>
      </Card>

      {shareLink && (
        <ProFeatureGate>
          <Card>
            <CardHeader>
              <CardTitle>Share link</CardTitle>
              <CardDescription>
                Anyone with this link can view the report (read-only)
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center gap-2">
              <input
                readOnly
                value={shareLink}
                className="flex-1 min-w-[200px] rounded-md border border-input bg-muted px-3 py-2 text-sm"
              />
              <Button variant="outline" size="sm" onClick={handleCopyShare}>
                {copied ? "Copied" : "Copy"}
              </Button>
            </CardContent>
          </Card>
        </ProFeatureGate>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Methodology</CardTitle>
          <CardDescription>
            Learn how emissions are calculated and scoped.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate("/about/methodology")}
          >
            View methodology
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
