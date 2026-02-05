import type { OnboardingResponse, OnboardingState } from "@/types/api";
import { api } from "./client";

export async function fetchOnboarding(): Promise<OnboardingResponse> {
  const { data } = await api.get<OnboardingResponse>("/api/onboarding");
  return data;
}

export async function updateOnboarding(
  payload: Partial<OnboardingState>
): Promise<OnboardingResponse> {
  const { data } = await api.put<OnboardingResponse>("/api/onboarding", payload);
  return data;
}
