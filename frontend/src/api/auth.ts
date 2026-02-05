import type { MeResponse, TokenResponse } from "@/types/api";
import { api, clearStoredToken, setStoredToken } from "./client";

export async function login(email: string, password: string): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/api/auth/login", { email, password });
  setStoredToken(data.access_token);
  return data;
}

export async function fetchMe(): Promise<MeResponse> {
  const { data } = await api.get<MeResponse>("/api/auth/me");
  return data;
}

export function logout(): void {
  clearStoredToken();
}

export async function devSeed(): Promise<{ ok: boolean; email?: string; password?: string }> {
  const { data } = await api.post("/api/auth/dev-seed");
  return data as { ok: boolean; email?: string; password?: string };
}
