import { api } from "./client";

export async function createCheckoutSession(plan: "starter" | "pro"): Promise<{ url: string }> {
  const { data } = await api.post<{ url: string }>("/api/billing/checkout-session", { plan });
  return data;
}

export async function createPortalSession(): Promise<{ url: string }> {
  const { data } = await api.post<{ url: string }>("/api/billing/portal-session");
  return data;
}

export async function confirmCheckout(session_id: string): Promise<{
  plan: string;
  billing_status: string;
  current_period_end: string | null;
}> {
  const { data } = await api.post<{
    plan: string;
    billing_status: string;
    current_period_end: string | null;
  }>("/api/billing/checkout-success", { session_id });
  return data;
}
