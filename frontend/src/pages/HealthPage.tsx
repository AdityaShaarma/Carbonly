import { useQuery } from "react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

async function fetchHealthDetails() {
  const res = await fetch(
    `${import.meta.env.VITE_API_BASE_URL}/health/details`
  );
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export function HealthPage() {
  const { data, isLoading, error } = useQuery(
    "health-details",
    fetchHealthDetails
  );

  if (error)
    return <p className="text-destructive">Failed to load health status.</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">System Health</h1>
      <Card>
        <CardHeader>
          <CardTitle>Backend status</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          {isLoading ? (
            <div className="h-20 animate-pulse rounded bg-muted" />
          ) : (
            <div className="space-y-2">
              <div>Status: {data.status}</div>
              <div>Database: {data.database}</div>
              <div>Service: {data.service}</div>
              <div>Environment: {data.environment}</div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
