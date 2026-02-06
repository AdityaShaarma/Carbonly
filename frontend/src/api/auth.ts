import type { MeResponse, TokenResponse, User } from "@/types/api";
import { api, clearStoredToken, setStoredToken } from "./client";

export async function login(email: string, password: string): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/api/auth/login", { email, password });
  setStoredToken(data.access_token);
  return data;
}

export async function signup(email: string, password: string, full_name?: string): Promise<{ user: User }> {
  const { data } = await api.post<{ access_token: string; token_type: string; user: User }>(
    "/api/auth/signup",
    { email, password, full_name }
  );
  setStoredToken(data.access_token);
  return { user: data.user };
}

export async function requestEmailVerification(email?: string): Promise<{ ok: boolean }> {
  const { data } = await api.post<{ ok: boolean }>("/api/auth/verify/request", { email });
  return data;
}

export async function verifyEmailToken(token: string): Promise<{ ok: boolean }> {
  const { data } = await api.get<{ ok: boolean }>("/api/auth/verify", {
    params: { token },
  });
  return data;
}

export async function forgotPassword(email: string): Promise<{ ok: boolean }> {
  const { data } = await api.post<{ ok: boolean }>("/api/auth/password/forgot", { email });
  return data;
}

export async function resetPassword(token: string, new_password: string): Promise<{ ok: boolean }> {
  const { data } = await api.post<{ ok: boolean }>("/api/auth/password/reset", {
    token,
    new_password,
  });
  return data;
}

export async function demoLogin(): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/api/auth/demo");
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
