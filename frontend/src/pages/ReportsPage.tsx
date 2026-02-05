import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { Link } from "react-router-dom";
import { fetchReports, createReport } from "@/api/reports";
import { useYearSelector } from "@/hooks/useYearSelector";
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
import { formatKgToTons } from "@/utils/format";
import { updateOnboarding } from "@/api/onboarding";

export function ReportsPage() {
  const queryClient = useQueryClient();
  const { year, setYear, options } = useYearSelector();
  const [title, setTitle] = useState("");
  const [createYear, setCreateYear] = useState(year);

  const { data, isLoading, error } = useQuery(
    ["reports", year],
    () => fetchReports(year),
    { keepPreviousData: true }
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
      },
      onError: () => toast.error("Failed to create report"),
    }
  );

  const reports = data?.reports ?? [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold">Reports</h1>
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
              {options.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </Select>
          </div>
          <Button
            onClick={() => create.mutate()}
            disabled={!title.trim() || create.isLoading}
            isLoading={create.isLoading}
          >
            Create report
          </Button>
        </CardContent>
      </Card>

      {error && <p className="text-destructive">Failed to load reports.</p>}

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : reports.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No reports yet. Create one above.
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Reports</CardTitle>
            <CardDescription>
              Preview, publish, download PDF, or share
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="divide-y divide-border">
              {reports.map((r) => (
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
                      {formatKgToTons(r.total_kg_co2e)} tCO₂e ·{" "}
                      {new Date(r.created_at).toLocaleDateString()} · {r.status}
                    </p>
                  </div>
                  <Link to={`/reports/${r.id}`}>
                    <Button variant="outline" size="sm">
                      View
                    </Button>
                  </Link>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
