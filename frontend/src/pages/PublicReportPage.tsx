import { useParams } from "react-router-dom";
import { useQuery } from "react-query";
import { fetchPublicReport } from "@/api/reports";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Link } from "react-router-dom";
import { formatEmissions } from "@/utils/format";

export function PublicReportPage() {
  const { shareToken } = useParams<{ shareToken: string }>();

  const { data, isLoading, error } = useQuery(
    ["public-report", shareToken],
    () => fetchPublicReport(shareToken!),
    { enabled: !!shareToken }
  );

  if (error || !shareToken) {
    return (
      <div className="flex min-h-screen items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <p className="text-destructive">
              Report not found or link is invalid.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isLoading || !data) {
    return (
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-muted/30 p-4">
      <div className="mx-auto max-w-2xl space-y-6 py-8">
        <div className="flex justify-between items-center">
          <Link to="/login" className="text-sm text-primary hover:underline">
            Carbonly
          </Link>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>{data.company_name}</CardTitle>
            <p className="text-sm text-muted-foreground">
              Carbon Disclosure Report · {data.reporting_year}
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">
                Total emissions
              </p>
              <p className="text-2xl font-semibold">
                {formatEmissions(data.total_co2e)}
              </p>
            </div>
            {data.executive_summary && (
              <div className="prose prose-sm max-w-none">
                <p className="whitespace-pre-wrap">{data.executive_summary}</p>
              </div>
            )}
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">
                Scope breakdown
              </p>
              <ul className="space-y-1 text-sm">
                <li>
                  Scope 1: {formatEmissions(data.scope_breakdown.scope_1)}
                </li>
                <li>
                  Scope 2: {formatEmissions(data.scope_breakdown.scope_2)}
                </li>
                <li>
                  Scope 3: {formatEmissions(data.scope_breakdown.scope_3)}
                </li>
              </ul>
            </div>
            {data.scope_3_breakdown &&
              Object.keys(data.scope_3_breakdown).length > 0 && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">
                    Scope 3 by category
                  </p>
                  <ul className="space-y-1 text-sm">
                    {Object.entries(data.scope_3_breakdown).map(
                      ([cat, val]) => (
                        <li key={cat}>
                          {cat}: {formatEmissions(val)}
                        </li>
                      )
                    )}
                  </ul>
                </div>
              )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
