import { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import {
  fetchIntegrations,
  syncProvider,
  estimateProvider,
  disconnectProvider,
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
  const [showHowItWorks, setShowHowItWorks] = useState(false);
  const [busyProviders, setBusyProviders] = useState<Record<string, boolean>>({});
  const [errorProviders, setErrorProviders] = useState<Record<string, string>>({});

  const { data, isLoading, error } = useQuery(
    "integrations",
    fetchIntegrations
  );

  const sync = useMutation((provider: string) => syncProvider(provider), {
    onMutate: (provider) => {
      setBusyProviders((prev) => ({ ...prev, [provider]: true }));
      setErrorProviders((prev) => {
        const next = { ...prev };
        delete next[provider];
        return next;
      });
    },
    onSuccess: async (_, provider) => {
      queryClient.invalidateQueries("integrations");
      queryClient.invalidateQueries(["dashboard", year]);
      if (provider === "aws") {
        await updateOnboarding({ connect_aws: true });
        queryClient.invalidateQueries("onboarding");
      }
      toast.success(`${provider} synced`);
    },
    onError: (err: { response?: { status?: number; data?: { detail?: string } } }, provider) => {
      const status = err.response?.status;
      const detail = err.response?.data?.detail ?? "";
      const hasData = ["connected", "ai_estimated"].includes(
        list.find((c) => c.source_type === provider)?.status ?? ""
      );
      let message = detail || "Sync failed";
      if (status === 429) {
        message = "Rate limited. Please wait and try again.";
      } else if (status === 401) {
        message = "Authentication expired — please log in again.";
      } else if (hasData) {
        message = "Sync failed — previous data is still in use";
      }
      setErrorProviders((prev) => ({ ...prev, [provider]: message }));
      toast.error(message);
    },
    onSettled: (_, __, provider) => {
      setBusyProviders((prev) => ({ ...prev, [provider]: false }));
    },
  });

  const estimate = useMutation((provider: string) => estimateProvider(provider), {
    onMutate: (provider) => {
      setBusyProviders((prev) => ({ ...prev, [provider]: true }));
      setErrorProviders((prev) => {
        const next = { ...prev };
        delete next[provider];
        return next;
      });
    },
    onSuccess: async (_, provider) => {
      queryClient.invalidateQueries("integrations");
      queryClient.invalidateQueries(["dashboard", year]);
      if (provider === "aws") {
        await updateOnboarding({ connect_aws: true });
        queryClient.invalidateQueries("onboarding");
      }
      toast.success(`${provider} set to benchmark estimate`);
    },
    onError: (err: { response?: { status?: number; data?: { detail?: string } } }, provider) => {
      const status = err.response?.status;
      const detail = err.response?.data?.detail ?? "";
      const hasData = ["connected", "ai_estimated"].includes(
        list.find((c) => c.source_type === provider)?.status ?? ""
      );
      let message = detail || "Estimate failed";
      if (status === 429) {
        message = "Rate limited. Please wait and try again.";
      } else if (status === 401) {
        message = "Authentication expired — please log in again.";
      } else if (hasData) {
        message = "Estimate failed — previous data is still in use";
      }
      setErrorProviders((prev) => ({ ...prev, [provider]: message }));
      toast.error(message);
    },
    onSettled: (_, __, provider) => {
      setBusyProviders((prev) => ({ ...prev, [provider]: false }));
    },
  });

  const disconnect = useMutation((provider: string) => disconnectProvider(provider), {
    onMutate: (provider) => {
      setBusyProviders((prev) => ({ ...prev, [provider]: true }));
      setErrorProviders((prev) => {
        const next = { ...prev };
        delete next[provider];
        return next;
      });
    },
    onSuccess: async (_, provider) => {
      queryClient.invalidateQueries("integrations");
      queryClient.invalidateQueries(["dashboard", year]);
      queryClient.invalidateQueries(["reports", year]);
      toast.success(`${provider} disconnected`);
    },
    onError: (err: { response?: { status?: number; data?: { detail?: string } } }, provider) => {
      const status = err.response?.status;
      const detail = err.response?.data?.detail ?? "";
      let message = detail || "Disconnect failed";
      if (status === 429) {
        message = "Rate limited. Please wait and try again.";
      } else if (status === 401) {
        message = "Authentication expired — please log in again.";
      }
      setErrorProviders((prev) => ({ ...prev, [provider]: message }));
      toast.error(message);
    },
    onSettled: (_, __, provider) => {
      setBusyProviders((prev) => ({ ...prev, [provider]: false }));
    },
  });

  if (error)
    return <p className="text-destructive">Failed to load integrations.</p>;

  const list = data?.integrations ?? [];
  const reportSources = useMemo(() => {
    const active = list.filter(
      (c) => c.status === "connected" || c.status === "ai_estimated"
    );
    if (active.length === 0) return "None yet";
    return active
      .map(
        (c) =>
          `${c.display_name} (${
            c.status === "connected" ? "Measured" : "Estimated"
          })`
      )
      .join(", ");
  }, [list]);

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold">Integrations</h1>
        <p className="text-sm text-muted-foreground">
          This page controls where your emissions data comes from. Sync pulls
          real usage data from your cloud providers (Measured). Benchmark-based
          estimates are an acceptable starting point when sync isn’t possible.
          You can also add Manual data separately, and you can still generate
          reports without syncing.
        </p>
        <p className="text-sm text-muted-foreground">
          Reports currently use: <span className="font-medium">{reportSources}</span>
        </p>
        <button
          type="button"
          onClick={() => setShowHowItWorks(true)}
          className="text-sm text-primary hover:underline"
        >
          How this works
        </button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Data quality</CardTitle>
          <CardDescription>
            <strong>Measured</strong> = connected source.{" "}
            <strong>Estimated</strong> = benchmark-based estimate.{" "}
            <strong>Manual</strong> = entered by you. Higher data quality
            improves report credibility.
          </CardDescription>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Cloud providers</CardTitle>
          <CardDescription>
            Connect, sync, or use benchmark-based estimates
          </CardDescription>
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
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{displayName}</p>
                      <span className="rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground">
                        {busyProviders[provider]
                          ? "Syncing"
                          : errorProviders[provider]
                          ? "Error"
                          : status === "connected"
                          ? "Measured"
                          : status === "ai_estimated"
                          ? "Estimated"
                          : "Not connected"}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Status:{" "}
                      <span className="capitalize">
                        {status.replace("_", " ")}
                      </span>
                      {lastSync !== "Never" && ` · Last sync: ${lastSync}`}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Sync pulls usage data from {displayName} to generate
                      measured emissions.
                    </p>
                    {errorProviders[provider] && (
                      <p className="text-xs text-muted-foreground">
                        {errorProviders[provider]}
                      </p>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {status === "not_connected" && (
                      <>
                        <Button
                          size="sm"
                          onClick={() => sync.mutate(provider)}
                          disabled={busyProviders[provider]}
                        >
                          Sync
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => estimate.mutate(provider)}
                          disabled={busyProviders[provider]}
                        >
                          Use benchmark estimate
                        </Button>
                      </>
                    )}
                    {status === "connected" && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => sync.mutate(provider)}
                          disabled={busyProviders[provider]}
                        >
                          Resync
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => estimate.mutate(provider)}
                          disabled={busyProviders[provider]}
                        >
                          Replace with benchmark estimate
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => disconnect.mutate(provider)}
                          disabled={busyProviders[provider]}
                        >
                          Disconnect
                        </Button>
                      </>
                    )}
                    {status === "ai_estimated" && (
                      <>
                        <Button
                          size="sm"
                          onClick={() => sync.mutate(provider)}
                          disabled={busyProviders[provider]}
                        >
                          Replace with measured data
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => disconnect.mutate(provider)}
                          disabled={busyProviders[provider]}
                        >
                          Remove estimate
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </CardContent>
      </Card>

      {showHowItWorks && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-lg bg-background p-6 shadow-lg">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold">How estimates work</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  Benchmark-based estimates create an estimated activity record
                  for your cloud usage. No external AI model is called.
                  Carbonly then applies standard emission factors to compute
                  estimated CO₂e. Use Sync for measured data when you can
                  connect the provider.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowHowItWorks(false)}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
