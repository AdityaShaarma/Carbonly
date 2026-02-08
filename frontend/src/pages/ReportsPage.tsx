import { useEffect, useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { Link } from "react-router-dom";
import { fetchReports, createReport, deleteReport } from "@/api/reports";
import { fetchDashboard } from "@/api/dashboard";
import { getReportYears } from "@/utils/years";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Select } from "@/components/ui/Select";
import toast from "react-hot-toast";
import { formatEmissions } from "@/utils/format";
import { updateOnboarding } from "@/api/onboarding";

export function ReportsPage() {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const currentYear = new Date().getFullYear();
  const [createYear, setCreateYear] = useState(currentYear);
  const [deleteError, setDeleteError] = useState("");
  const [createError, setCreateError] = useState("");
  const createYearOptions = getReportYears(currentYear, 9);
  const isFutureYear = createYear > currentYear;
  const [sortOrder, setSortOrder] = useState<"newest" | "oldest" | "year_desc">(
    "newest"
  );

  useEffect(() => {
    if (!createYearOptions.includes(createYear)) {
      setCreateYear(currentYear);
    }
  }, [createYearOptions, createYear, currentYear]);

  const { data: dashboard } = useQuery(["dashboard", createYear], () =>
    fetchDashboard(createYear)
  );

  const create = useMutation(
    () => createReport(title || `Carbon Report ${createYear}`, createYear),
    {
      onSuccess: async () => {
        queryClient.invalidateQueries(["reports"]);
        await updateOnboarding({ create_report: true });
        queryClient.invalidateQueries("onboarding");
        toast.success("Report created");
        setTitle("");
        setCreateError("");
      },
      onError: (err: { response?: { status?: number; data?: { detail?: string } } }) => {
        const status = err.response?.status;
        const detail = err.response?.data?.detail ?? "";
        if (status === 400 && detail === "Cannot create a disclosure report for a future year.") {
          setCreateError(detail);
          return;
        }
        toast.error("We couldn’t create a report yet. Add data and try again.");
      },
    }
  );
  const remove = useMutation((reportId: string) => deleteReport(reportId), {
    onSuccess: () => {
      setDeleteError("");
      queryClient.invalidateQueries(["reports"]);
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      setDeleteError(
        err.response?.data?.detail ?? "We couldn’t delete that report. Try again."
      );
    },
  });

  const hasData =
    (dashboard?.data_lineage?.manual_count ?? 0) +
      (dashboard?.data_lineage?.estimated_count ?? 0) +
      (dashboard?.data_lineage?.measured_count ?? 0) >
      0 ||
    (dashboard?.annual_totals?.total_co2e ?? 0) > 0;
  const { data, isLoading, error } = useQuery(["reports"], () => fetchReports(), {
    keepPreviousData: true,
  });
  const reports = data?.reports ?? [];
  const sortedReports = useMemo(() => {
    const copy = [...reports];
    if (sortOrder === "oldest") {
      return copy.sort(
        (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      );
    }
    if (sortOrder === "year_desc") {
      return copy.sort((a, b) => b.reporting_year - a.reporting_year);
    }
    return copy.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  }, [reports, sortOrder]);
  const errorStatus = (error as { response?: { status?: number } } | null)?.response?.status;
  const showError = Boolean(error) && (!errorStatus || errorStatus >= 500);

  const statusBadge = (status: string) => {
    const base = "inline-flex items-center rounded-full px-2 py-0.5 text-xs";
    if (status === "published") {
      return `${base} bg-emerald-100 text-emerald-700`;
    }
    return `${base} bg-muted text-muted-foreground`;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">Reports</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Why this report matters</CardTitle>
          <CardDescription>
            These reports are commonly requested in enterprise procurement, ESG
            questionnaires, and regulatory reporting.
          </CardDescription>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Create report</CardTitle>
          <CardDescription>
            Generate a new carbon disclosure report (draft)
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap items-end gap-4">
          <div className="space-y-2">
            <Label>Title</Label>
            <Input
              placeholder="e.g. Annual Carbon Report 2025"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-64"
            />
          </div>
          <div className="space-y-2">
            <Label>Year</Label>
            <Select
              value={createYear}
              onChange={(e) => setCreateYear(Number(e.target.value))}
              className="w-28"
            >
              {createYearOptions.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </Select>
          </div>
          <Button
            onClick={() => {
              create.mutate();
            }}
            disabled={!title.trim() || create.isLoading || !hasData || isFutureYear}
            isLoading={create.isLoading}
          >
            Create report
          </Button>
          {!hasData && (
            <span className="text-sm text-muted-foreground">
              Add data to enable
            </span>
          )}
          {isFutureYear && (
            <span className="text-sm text-muted-foreground">
              Reports can’t be created for future years.
            </span>
          )}
          {createError && (
            <span className="text-sm text-destructive">{createError}</span>
          )}
        </CardContent>
      </Card>

      {showError && (
        <p className="text-destructive">
          We couldn’t load reports. Try again in a moment.
        </p>
      )}

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : sortedReports.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            {!hasData ? (
              <div className="space-y-2">
                <p className="text-lg font-medium text-foreground">
                  No reports yet
                </p>
                <p>
                  Reports are generated from your emissions data. Add data first
                  to create your first report.
                </p>
                <Link to="/manual">
                  <Button className="mt-2" size="sm">
                    Add data
                  </Button>
                </Link>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Create your first report
              </p>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <CardTitle>Reports</CardTitle>
                <CardDescription>
                  Preview, publish, download PDF, or share
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-sm text-muted-foreground">Sort</label>
                <Select
                  value={sortOrder}
                  onChange={(e) =>
                    setSortOrder(e.target.value as "newest" | "oldest" | "year_desc")
                  }
                  className="w-40"
                >
                  <option value="newest">Newest</option>
                  <option value="oldest">Oldest</option>
                  <option value="year_desc">Reporting year (desc)</option>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {deleteError && (
              <p className="mb-3 text-sm text-destructive">{deleteError}</p>
            )}
            <ul className="divide-y divide-border">
              {sortedReports.map((r) => (
                <li
                  key={r.id}
                  className="flex flex-wrap items-center justify-between gap-4 py-3 first:pt-0"
                >
                  <div>
                    <Link
                      to={`/reports/${r.id}`}
                      className="font-medium hover:underline"
                    >
                      {r.title}
                    </Link>
                    <p className="text-sm text-muted-foreground">
                      {r.company_name_snapshot ?? ""} ·{" "}
                      {formatEmissions(r.total_kg_co2e)} · Created{" "}
                      {new Date(r.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="inline-flex items-center rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground">
                      Year: {r.reporting_year}
                    </span>
                    <span className={statusBadge(r.status)}>{r.status}</span>
                    {r.status === "draft" && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-destructive border-destructive/30 hover:text-destructive"
                        onClick={() => {
                          if (!window.confirm("Delete this draft report?")) {
                            return;
                          }
                          remove.mutate(r.id);
                        }}
                        disabled={remove.isLoading}
                      >
                        Delete
                      </Button>
                    )}
                    <Link to={`/reports/${r.id}`}>
                      <Button variant="outline" size="sm">
                        View
                      </Button>
                    </Link>
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
