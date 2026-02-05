import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { fetchReport, publishReport, openReportPdf } from "@/api/reports";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import toast from "react-hot-toast";
import { formatKgToTons } from "@/utils/format";

export function ReportDetailPage() {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [copied, setCopied] = useState(false);

  const {
    data: report,
    isLoading,
    error,
  } = useQuery(["report", reportId], () => fetchReport(reportId!), {
    enabled: !!reportId,
  });

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

  const handleOpenPdf = () => {
    openReportPdf(reportId!)
      .then(() => toast.success("PDF opened"))
      .catch(() => toast.error("Failed to open PDF"));
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

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">{report.title}</h1>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleOpenPdf}>
            Download PDF
          </Button>
          {report.status === "draft" && (
            <Button
              size="sm"
              onClick={() => publish.mutate()}
              isLoading={publish.isLoading}
            >
              Publish
            </Button>
          )}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
          <CardDescription>
            {report.company_name_snapshot} · {report.reporting_year} ·{" "}
            {formatKgToTons(report.total_kg_co2e)} tCO₂e
          </CardDescription>
        </CardHeader>
        <CardContent className="prose prose-sm max-w-none">
          {executiveSummary && (
            <p className="whitespace-pre-wrap">{executiveSummary}</p>
          )}
        </CardContent>
      </Card>

      {shareLink && (
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
      )}
    </div>
  );
}
