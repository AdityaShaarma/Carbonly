import { useQuery } from "react-query";
import { fetchInsights } from "@/api/insights";
import { fetchDashboard } from "@/api/dashboard";
import { useYearSelector } from "@/hooks/useYearSelector";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Select } from "@/components/ui/Select";
import { cn } from "@/utils/cn";
import { ProFeatureGate } from "@/components/billing/ProFeatureGate";
import { Link } from "react-router-dom";

export function InsightsPage() {
  const { year, setYear, options } = useYearSelector();

  const { data: dashboard } = useQuery(["dashboard", year], () =>
    fetchDashboard(year)
  );

  const hasData =
    (dashboard?.data_lineage?.manual_count ?? 0) +
      (dashboard?.data_lineage?.estimated_count ?? 0) +
      (dashboard?.data_lineage?.measured_count ?? 0) >
      0 ||
    (dashboard?.annual_totals?.total_co2e ?? 0) > 0;
  const { data, isLoading, error } = useQuery(
    ["insights", year],
    () => fetchInsights(year),
    { keepPreviousData: true, enabled: hasData }
  );

  const insights = data?.insights ?? [];
  const errorStatus = (error as { response?: { status?: number } } | null)?.response?.status;
  const showError = Boolean(error) && (!errorStatus || errorStatus >= 500);

  if (showError) {
    return (
      <p className="text-destructive">
        We couldn’t load insights. Try again in a moment.
      </p>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">Insights</h1>
        <div className="flex items-center gap-2">
          <label className="text-sm text-muted-foreground">Year</label>
          <Select
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="w-28"
          >
            {options.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <ProFeatureGate>
        <Card>
          <CardHeader>
            <CardTitle>Reduction recommendations</CardTitle>
            <CardDescription>
              Actions to lower your carbon footprint
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!hasData ? (
              <div className="space-y-2 text-sm text-muted-foreground">
                <p>No emissions data yet</p>
                <p>Add data to see insights about your carbon footprint</p>
                <Link to="/manual" className="text-primary hover:underline">
                  Add data
                </Link>
              </div>
            ) : isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-20 animate-pulse rounded bg-muted" />
                ))}
              </div>
            ) : insights.length === 0 ? (
              <p className="text-muted-foreground">No insights for this year.</p>
            ) : (
              <ul className="space-y-4">
                {insights.map((insight) => (
                  <li
                    key={insight.id}
                    className="rounded-lg border border-border p-4"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <p className="font-medium">{insight.title}</p>
                        <p className="text-sm text-muted-foreground mt-1">
                          {insight.description}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            "rounded-full px-2 py-0.5 text-xs font-medium capitalize",
                            insight.impact_level === "High" &&
                              "bg-primary/10 text-primary",
                            insight.impact_level === "Medium" &&
                              "bg-amber-100 text-amber-800",
                            insight.impact_level === "Low" &&
                              "bg-muted text-muted-foreground"
                          )}
                        >
                          {insight.impact_level}
                        </span>
                        {insight.estimated_reduction_percent != null && (
                          <span className="text-sm text-muted-foreground">
                            ~{insight.estimated_reduction_percent}% reduction
                          </span>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </ProFeatureGate>
    </div>
  );
}
