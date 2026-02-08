import { useEffect, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useMutation } from "react-query";
import { z } from "zod";
import { login } from "@/api/auth";
import { useAuth } from "@/contexts/AuthContext";
import { getStoredToken } from "@/api/client";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import toast from "react-hot-toast";
import { Link } from "react-router-dom";
import { DEMO_MODE } from "@/config/env";

const schema = z.object({
  email: z.string().email("Invalid email"),
  password: z.string().min(1, "Password required"),
});

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { refetchMe } = useAuth();
  const from =
    (location.state as { from?: { pathname: string } })?.from?.pathname ??
    "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [cooldownUntil, setCooldownUntil] = useState<number | null>(null);
  const [nowMs, setNowMs] = useState(() => Date.now());
  const requestIdRef = useRef(0);
  const DEMO_EMAIL = "test@carbonly.com";
  const DEMO_PASSWORD = "password123";

  useEffect(() => {
    const message = sessionStorage.getItem("auth_message");
    if (message) {
      toast.error(message);
      sessionStorage.removeItem("auth_message");
    }
  }, []);
  useEffect(() => {
    if (!cooldownUntil) return;
    const interval = window.setInterval(() => {
      setNowMs(Date.now());
    }, 1000);
    return () => window.clearInterval(interval);
  }, [cooldownUntil]);

  const mutation = useMutation((vars: { email: string; password: string }) =>
    login(vars.email, vars.password)
  );

  const isDev = Boolean((import.meta as { env?: { DEV?: boolean } }).env?.DEV);
  const runLogin = async (loginEmail: string, loginPassword: string) => {
    if (isSubmitting) return;
    if (cooldownUntil && Date.now() < cooldownUntil) return;
    setErrorMessage(null);
    const result = schema.safeParse({
      email: loginEmail,
      password: loginPassword,
    });
    if (!result.success) {
      const message = result.error.errors[0].message;
      setErrorMessage(message);
      toast.error(message);
      return;
    }
    const requestId = ++requestIdRef.current;
    setIsSubmitting(true);
    try {
      await mutation.mutateAsync({
        email: loginEmail,
        password: loginPassword,
      });
      if (requestId !== requestIdRef.current) return;
      if (isDev) {
        const token = getStoredToken();
        console.debug("[auth] login success token saved", {
          hasToken: Boolean(token),
          tokenLength: token?.length ?? 0,
        });
      }
      if (isDev) {
        console.debug("[auth] before /me", {
          hasAuthHeader: Boolean(getStoredToken()),
        });
      }
      await refetchMe();
      toast.success("Logged in");
      navigate(from, { replace: true });
    } catch (err) {
      if (requestId !== requestIdRef.current) return;
      const status = (err as { response?: { status?: number } })?.response
        ?.status;
      if (status === 401) {
        const message = "Invalid email or password.";
        setErrorMessage(message);
        toast.error(message);
      } else if (status === 429) {
        const message =
          "Too many attempts. Please wait 30 seconds and try again.";
        setErrorMessage(message);
        toast.error(message);
        setCooldownUntil(Date.now() + 30_000);
      } else if (status === 404) {
        const message = "Account not found";
        setErrorMessage(message);
        toast.error(message);
      } else {
        const message = "We couldn't log you in. Try again.";
        setErrorMessage(message);
        toast.error(message);
      }
    } finally {
      if (requestId === requestIdRef.current) {
        setIsSubmitting(false);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation();
    await runLogin(email, password);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">Carbonly</CardTitle>
          <CardDescription>Sign in to your account</CardDescription>
        </CardHeader>
        <CardContent>
          <form
            id="login-form"
            onSubmit={handleSubmit}
            className="space-y-4"
            noValidate
          >
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (errorMessage) setErrorMessage(null);
                }}
                autoComplete="email"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (errorMessage) setErrorMessage(null);
                }}
                autoComplete="current-password"
              />
            </div>
            <Button
              type="submit"
              form="login-form"
              className="w-full"
              isLoading={isSubmitting}
              disabled={
                isSubmitting || (cooldownUntil ? nowMs < cooldownUntil : false)
              }
            >
              Sign in
            </Button>
            {cooldownUntil && nowMs < cooldownUntil && (
              <p className="text-xs text-muted-foreground">
                Try again in {Math.ceil((cooldownUntil - nowMs) / 1000)}s
              </p>
            )}
            {errorMessage && (
              <p className="text-sm text-destructive">{errorMessage}</p>
            )}
          </form>
          <div className="mt-3 flex items-center justify-between text-sm">
            <Link
              to="/forgot-password"
              className="text-primary hover:underline"
            >
              Forgot password?
            </Link>
            <Link to="/signup" className="text-primary hover:underline">
              Create account
            </Link>
          </div>
          {DEMO_MODE && (
            <Button
              className="mt-4 w-full"
              variant="outline"
              onClick={async () => {
                setEmail(DEMO_EMAIL);
                setPassword(DEMO_PASSWORD);
                await runLogin(DEMO_EMAIL, DEMO_PASSWORD);
              }}
              isLoading={isSubmitting}
            >
              Try Demo
            </Button>
          )}
          <p className="mt-4 text-center text-xs text-muted-foreground">
            Demo: test@carbonly.com / password123 (after seeding backend)
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
