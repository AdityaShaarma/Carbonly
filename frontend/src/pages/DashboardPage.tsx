import { useMemo } from "react";
import { useQuery } from "react-query";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { fetchDashboard, recomputeEmissions } from "@/api/dashboard";
import { useYearSelector } from "@/hooks/useYearSelector";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { Skeleton } from "@/components/ui/Skeleton";
import { useMutation, useQueryClient } from "react-query";
import toast from "react-hot-toast";
import { formatKgToTons, formatNumber, formatEmissions } from "@/utils/format";
import { Link } from "react-router-dom";
import { DEMO_MODE } from "@/config/env";

export function DashboardPage() {
  const { year, setYear, options } = useYearSelector();
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery(
    ["dashboard", year],
    () => fetchDashboard(year),
    { keepPreviousData: true }
  );

  const recompute = useMutation(() => recomputeEmissions(year), {
    onSuccess: () => {
      queryClient.invalidateQueries(["dashboard", year]);
      toast.success("Emissions recomputed");
    },
    onError: () => toast.error("Recompute failed"),
  });

  if (error) {
    return (
      <div className="space-y-4">
        <p className="text-destructive">Failed to load dashboard.</p>
      </div>
    );
  }

  const stats = data?.company_stats;
  const totals = data?.annual_totals;
  const quality = data?.data_quality;
  const lineage = data?.data_lineage;
  const trend = data?.monthly_trend ?? [];
  const trendMetrics = useMemo(() => {
    const monthsWithData = trend.filter(
      (m) => (m.total ?? 0) > 0 || (m.scope_1 ?? 0) > 0 || (m.scope_2 ?? 0) > 0 || (m.scope_3 ?? 0) > 0
    );
    const maxValue = trend.reduce((max, m) => {
      const candidates = [m.total ?? 0, m.scope_1 ?? 0, m.scope_2 ?? 0, m.scope_3 ?? 0];
      return Math.max(max, ...candidates);
    }, 0);
    return {
      monthsWithData: monthsWithData.length,
      maxValue,
      startMonth: monthsWithData[0]?.month,
    };
  }, [trend]);
  const insufficientTrendData =
    trendMetrics.monthsWithData < 2 || (totals?.total_co2e ?? 0) < 1;
  const showKgAxis = trendMetrics.maxValue < 1000;
  const yDomainMax = Math.max(1, trendMetrics.maxValue * 1.1);
  const showScope1 = trend.some((m) => (m.scope_1 ?? 0) > 0);
  const showScope2 = trend.some((m) => (m.scope_2 ?? 0) > 0);
  const showScope3 = trend.some((m) => (m.scope_3 ?? 0) > 0);
  const showTotal = trend.some((m) => (m.total ?? 0) > 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">
            Generate procurement-ready carbon disclosures.
          </h1>
          <p className="text-sm text-muted-foreground">
            Carbonly helps you respond to customer and regulatory carbon
            requests using measured data or defensible estimates.
          </p>
        </div>
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
          <Button
            variant="outline"
            size="sm"
            onClick={() => recompute.mutate()}
            isLoading={recompute.isLoading}
          >
            Recompute
          </Button>
        </div>
      </div>

      {DEMO_MODE && (
        <Card>
          <CardContent className="py-4 text-sm text-amber-700">
            Demo mode is enabled. Metrics shown are sample data for investor
            walkthroughs.
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i}>
                <CardHeader className="pb-2">
                  <Skeleton className="h-4 w-24" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-16" />
                </CardContent>
              </Card>
            ))}
          </div>
          <Card>
            <CardHeader>
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-4 w-64" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-64 w-full" />
            </CardContent>
          </Card>
        </div>
      ) : (
        <>
          {lineage &&
            lineage.measured_count === 0 &&
            lineage.estimated_count === 0 &&
            lineage.manual_count === 0 && (
              <Card>
                <CardContent className="flex flex-wrap items-center justify-between gap-4 py-6">
                  <div>
                    <p className="font-medium">Get started</p>
                    <p className="text-sm text-muted-foreground">
                      Connect a data source or add a manual entry to populate
                      your dashboard.
                    </p>
                    <div className="mt-3 space-y-1 text-sm text-muted-foreground">
                      <p>
                        <span className="font-medium text-foreground">
                          What is Scope 3?
                        </span>{" "}
                        It includes indirect emissions like cloud usage,
                        commuting, and travel.
                      </p>
                      <p>
                        <span className="font-medium text-foreground">
                          Why cloud emissions matter
                        </span>{" "}
                        Cloud workloads can be your largest Scope 3 category.
                      </p>
                    </div>
                  </div>
                  <Link to="/onboarding">
                    <Button>Start onboarding</Button>
                  </Link>
                </CardContent>
              </Card>
            )}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Employees</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.employees ?? 0}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Cloud providers</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.cloud_providers_count ?? 0}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Reporting year</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.reporting_year ?? year}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>CO₂e per employee (tCO₂e)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.employees
                    ? formatNumber(
                        (totals?.total_co2e ?? 0) / 1000 / stats.employees
                      )
                    : "—"}
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Total Carbon Footprint</CardTitle>
              <CardDescription>
                Annual total and scope breakdown ({year})
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Total</span>
                  <span className="font-medium">
                    {formatEmissions(totals?.total_co2e ?? 0)} / year
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span className="flex items-center gap-2">
                    Scope 1
                    <span
                      className="text-xs text-muted-foreground cursor-help"
                      title="Direct emissions from owned or controlled sources."
                    >
                      ⓘ
                    </span>
                  </span>
                  <span>
                    {formatEmissions(totals?.scope_1 ?? 0)}{" "}
                    <span className="text-xs text-muted-foreground">
                      (Measured/Estimated)
                    </span>
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span className="flex items-center gap-2">
                    Scope 2
                    <span
                      className="text-xs text-muted-foreground cursor-help"
                      title="Indirect emissions from purchased energy."
                    >
                      ⓘ
                    </span>
                  </span>
                  <span>{formatEmissions(totals?.scope_2 ?? 0)}</span>
                </div>
                <div className="flex items-center justify-between text-sm text-muted-foreground">
                  <span className="flex items-center gap-2">
                    Scope 3
                    <span
                      className="text-xs text-muted-foreground cursor-help"
                      title="Other indirect emissions in your value chain."
                    >
                      ⓘ
                    </span>
                  </span>
                  <span>{formatEmissions(totals?.scope_3 ?? 0)}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Data Quality</CardTitle>
              <CardDescription>
                Confidence{" "}
                {quality?.overall_confidence != null
                  ? `${quality.overall_confidence}%`
                  : "—"}{" "}
                · Connected: {quality?.connected_sources_count ?? 0} ·
                Estimated: {quality?.ai_estimated_sources_count ?? 0} · Manual:{" "}
                {quality?.manual_entries_count ?? 0}
              </CardDescription>
            </CardHeader>
          </Card>
          {lineage && (
            <Card>
              <CardHeader>
                <CardTitle>Source Breakdown</CardTitle>
                <CardDescription>
                  Measured vs estimated vs manual totals
                </CardDescription>
              </CardHeader>
              <CardContent className="text-sm space-y-2">
                <div className="flex justify-between">
                  <span>Measured</span>
                  <span>{formatEmissions(lineage.measured_kg_co2e)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Estimated</span>
                  <span>{formatEmissions(lineage.estimated_kg_co2e)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Manual</span>
                  <span>{formatEmissions(lineage.manual_kg_co2e)}</span>
                </div>
              </CardContent>
            </Card>
          )}

          {!insufficientTrendData ? (
            <Card>
              <CardHeader>
                <CardTitle>Emissions Trend</CardTitle>
                <CardDescription>
                  Monthly breakdown by scope
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="mb-3 text-xs text-muted-foreground">
                  Data coverage: {trendMetrics.startMonth ?? "Jan"} {year} – Present
                </p>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis
                      domain={[0, yDomainMax]}
                      tickFormatter={(v) =>
                        showKgAxis
                          ? `${formatNumber(v)} kg CO₂e`
                          : `${formatKgToTons(v, 0)} tCO₂e`
                      }
                    />
                    <Tooltip
                      formatter={(v: number) => [
                        showKgAxis ? `${formatNumber(v)} kg CO₂e` : formatEmissions(v),
                        "Emissions",
                      ]}
                    />
                    <Legend />
                    {showScope1 && (
                      <Line
                        type="monotone"
                        dataKey="scope_1"
                        name="Scope 1"
                        stroke="hsl(142 76% 22%)"
                      />
                    )}
                    {showScope2 && (
                      <Line
                        type="monotone"
                        dataKey="scope_2"
                        name="Scope 2"
                        stroke="hsl(200 80% 40%)"
                      />
                    )}
                    {showScope3 && (
                      <Line
                        type="monotone"
                        dataKey="scope_3"
                        name="Scope 3"
                        stroke="hsl(30 80% 45%)"
                      />
                    )}
                    {showTotal && (
                      <Line
                        type="monotone"
                        dataKey="total"
                        name="Total"
                        stroke="hsl(0 0% 30%)"
                        strokeWidth={2}
                      />
                    )}
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                <p className="text-muted-foreground mb-2 font-medium">
                  Not enough data to show trends yet
                </p>
                <p className="text-sm text-muted-foreground mb-4">
                  Add emissions data across multiple months to see trends over time.
                </p>
                <div className="flex flex-wrap items-center justify-center gap-2">
                  <Link to="/manual">
                    <Button variant="outline">Add manual data</Button>
                  </Link>
                  <Link to="/integrations">
                    <Button>Sync integrations</Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          )}

          {totals?.scope3_by_category &&
            totals.scope3_by_category.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Scope 3 breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-1 text-sm">
                    {totals.scope3_by_category.map(
                      ({ category, total_kg_co2e }) => (
                        <li key={category} className="flex justify-between">
                          <span className="capitalize">{category}</span>
                          <span>{formatEmissions(total_kg_co2e)}</span>
                        </li>
                      )
                    )}
                  </ul>
                </CardContent>
              </Card>
            )}
        </>
      )}
    </div>
  );
}
