import { useQuery, useMutation, useQueryClient } from "react-query";
import {
  fetchIntegrations,
  syncProvider,
  estimateProvider,
} from "@/api/integrations";
import { updateOnboarding } from "@/api/onboarding";
import { useYearSelector } from "@/hooks/useYearSelector";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import toast from "react-hot-toast";

const PROVIDERS = ["aws", "gcp", "azure"];

export function IntegrationsPage() {
  const queryClient = useQueryClient();
  const { year } = useYearSelector();

  const { data, isLoading, error } = useQuery(
    "integrations",
    fetchIntegrations
  );

  const sync = useMutation((provider: string) => syncProvider(provider), {
    onSuccess: async (_, provider) => {
      queryClient.invalidateQueries("integrations");
      queryClient.invalidateQueries(["dashboard", year]);
      if (provider === "aws") {
        await updateOnboarding({ connect_aws: true });
        queryClient.invalidateQueries("onboarding");
      }
      toast.success(`${provider} synced`);
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail ?? "Sync failed");
    },
  });

  const estimate = useMutation(
    (provider: string) => estimateProvider(provider),
    {
      onSuccess: async (_, provider) => {
        queryClient.invalidateQueries("integrations");
        queryClient.invalidateQueries(["dashboard", year]);
        if (provider === "aws") {
          await updateOnboarding({ connect_aws: true });
          queryClient.invalidateQueries("onboarding");
        }
        toast.success(`${provider} set to AI estimated`);
      },
      onError: () => toast.error("Estimate failed"),
    }
  );

  if (error)
    return <p className="text-destructive">Failed to load integrations.</p>;

  const list = data?.integrations ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Integrations</h1>

      <Card>
        <CardHeader>
          <CardTitle>Data quality</CardTitle>
          <CardDescription>
            <strong>Measured</strong> = connected source.{" "}
            <strong>Estimated</strong> = AI-estimated from benchmarks.{" "}
            <strong>Manual</strong> = entered by you. Higher data quality
            improves report credibility.
          </CardDescription>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Cloud providers</CardTitle>
          <CardDescription>Connect, sync, or use AI estimates</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <div className="space-y-2">
              {PROVIDERS.map((p) => (
                <div key={p} className="h-14 animate-pulse rounded bg-muted" />
              ))}
            </div>
          ) : list.length === 0 ? (
            <div className="rounded-lg border border-border p-6 text-center text-muted-foreground">
              No integrations found. Connect AWS, GCP, or Azure to start
              tracking emissions.
            </div>
          ) : (
            PROVIDERS.map((provider) => {
              const conn = list.find((c) => c.source_type === provider);
              const displayName = conn?.display_name ?? provider.toUpperCase();
              const status = conn?.status ?? "not_connected";
              const lastSync = conn?.last_synced_at
                ? new Date(conn.last_synced_at).toLocaleString()
                : "Never";

              return (
                <div
                  key={provider}
                  className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-border p-4"
                >
                  <div>
                    <p className="font-medium">{displayName}</p>
                    <p className="text-sm text-muted-foreground">
                      Status:{" "}
                      <span className="capitalize">
                        {status.replace("_", " ")}
                      </span>
                      {lastSync !== "Never" && ` · Last sync: ${lastSync}`}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => sync.mutate(provider)}
                      disabled={sync.isLoading}
                    >
                      Sync
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => estimate.mutate(provider)}
                      disabled={estimate.isLoading}
                    >
                      Use AI estimate
                    </Button>
                  </div>
                </div>
              );
            })
          )}
        </CardContent>
      </Card>
    </div>
  );
}
