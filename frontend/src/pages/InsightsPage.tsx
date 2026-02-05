import { useQuery } from "react-query";
import { fetchInsights } from "@/api/insights";
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

export function InsightsPage() {
  const { year, setYear, options } = useYearSelector();

  const { data, isLoading, error } = useQuery(
    ["insights", year],
    () => fetchInsights(year),
    { keepPreviousData: true }
  );

  const insights = data?.insights ?? [];

  if (error)
    return <p className="text-destructive">Failed to load insights.</p>;

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

      <Card>
        <CardHeader>
          <CardTitle>Reduction recommendations</CardTitle>
          <CardDescription>
            Actions to lower your carbon footprint
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
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
    </div>
  );
}
