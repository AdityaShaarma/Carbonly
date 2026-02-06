import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/contexts/AuthContext";
import { useMutation } from "react-query";
import { createCheckoutSession, createPortalSession } from "@/api/billing";
import toast from "react-hot-toast";

export function BillingPage() {
  const { company, user } = useAuth();
  const checkout = useMutation(
    (plan: "starter" | "pro") => createCheckoutSession(plan),
    {
      onSuccess: (data) => {
        window.location.href = data.url;
      },
      onError: (err: {
        response?: { status?: number; data?: { detail?: string } };
      }) => {
        const message =
          err.response?.data?.detail ?? "Unable to start checkout";
        if (import.meta.env.DEV) {
          // eslint-disable-next-line no-console
          console.error("Checkout error", {
            status: err.response?.status,
            data: err.response?.data,
          });
        }
        toast.error(message);
      },
    }
  );
  const portal = useMutation(() => createPortalSession(), {
    onSuccess: (data) => {
      window.location.href = data.url;
    },
    onError: (err: {
      response?: { status?: number; data?: { detail?: string } };
    }) => {
      const message =
        err.response?.data?.detail ?? "Unable to open billing portal";
      if (import.meta.env.DEV) {
        // eslint-disable-next-line no-console
        console.error("Portal error", {
          status: err.response?.status,
          data: err.response?.data,
        });
      }
      toast.error(message);
    },
  });

  const periodEnd = company?.current_period_end
    ? new Date(company.current_period_end).toLocaleDateString()
    : null;
  const isDemo = user?.is_demo ?? false;
  const isActive = company?.billing_status === "active";
  const currentPlan = company?.plan ?? "demo";

  const getPlanCTA = (plan: "starter" | "pro") => {
    if (!isActive || currentPlan === "demo" || currentPlan === "inactive") {
      return {
        label: plan === "starter" ? "Upgrade to Starter" : "Upgrade to Pro",
        disabled: isDemo || checkout.isLoading,
        variant: "default" as const,
        onClick: () => checkout.mutate(plan),
        isLoading: checkout.isLoading,
      };
    }
    if (currentPlan === plan) {
      return {
        label: "Current plan",
        disabled: true,
        variant: "outline" as const,
        isLoading: false,
      };
    }
    if (plan === "pro" && currentPlan === "starter") {
      return {
        label: "Upgrade to Pro",
        disabled: isDemo || checkout.isLoading,
        variant: "default" as const,
        onClick: () => checkout.mutate("pro"),
        isLoading: checkout.isLoading,
      };
    }
    if (plan === "starter" && currentPlan === "pro") {
      return {
        label: "Downgrade to Starter (effective next billing cycle)",
        disabled: isDemo || portal.isLoading,
        variant: "outline" as const,
        onClick: () => portal.mutate(),
        isLoading: portal.isLoading,
      };
    }
    return {
      label: "Upgrade",
      disabled: isDemo || checkout.isLoading,
      variant: "default" as const,
      onClick: () => checkout.mutate(plan),
      isLoading: checkout.isLoading,
    };
  };

  const starterCTA = getPlanCTA("starter");
  const proCTA = getPlanCTA("pro");

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Billing</h1>
      <Card>
        <CardHeader>
          <CardTitle>Current plan</CardTitle>
          <CardDescription>Manage your Carbonly subscription</CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-medium text-foreground">
              {company?.plan ?? "demo"}
            </span>
            <span className="rounded-full bg-muted px-2 py-0.5 text-xs">
              {company?.billing_status ?? "inactive"}
            </span>
            {periodEnd && (
              <span className="text-xs">Renews on {periodEnd}</span>
            )}
          </div>
          {isActive && (
            <Button
              className="mt-3"
              variant="outline"
              onClick={() => portal.mutate()}
              isLoading={portal.isLoading}
            >
              Manage billing
            </Button>
          )}
          {isDemo && (
            <p className="mt-2 text-xs text-muted-foreground">
              Demo accounts cannot subscribe to paid plans.
            </p>
          )}
        </CardContent>
      </Card>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Plans</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Starter</CardTitle>
                {currentPlan === "starter" && isActive && (
                  <span className="rounded-full bg-muted px-2 py-0.5 text-xs">
                    Current
                  </span>
                )}
              </div>
              <CardDescription>
                Essential reporting for smaller teams
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={starterCTA.onClick}
                disabled={starterCTA.disabled}
                isLoading={starterCTA.isLoading}
                variant={starterCTA.variant}
              >
                {starterCTA.label}
              </Button>
              {currentPlan === "pro" && isActive && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Downgrades take effect at the end of your current billing
                  period.
                </p>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Pro</CardTitle>
                {currentPlan === "pro" && isActive && (
                  <span className="rounded-full bg-muted px-2 py-0.5 text-xs">
                    Current
                  </span>
                )}
              </div>
              <CardDescription>
                Advanced reporting and procurement readiness
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={proCTA.onClick}
                disabled={proCTA.disabled}
                isLoading={proCTA.isLoading}
                variant={proCTA.variant}
              >
                {proCTA.label}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
