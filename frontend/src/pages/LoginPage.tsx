import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useMutation } from "react-query";
import { z } from "zod";
import { demoLogin, login } from "@/api/auth";
import { useAuth } from "@/contexts/AuthContext";
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

  useEffect(() => {
    const message = sessionStorage.getItem("auth_message");
    if (message) {
      toast.error(message);
      sessionStorage.removeItem("auth_message");
    }
  }, []);

  const mutation = useMutation(() => login(email, password), {
    onSuccess: async () => {
      await refetchMe();
      toast.success("Logged in");
      navigate(from, { replace: true });
    },
    onError: (err: { response?: { status?: number; data?: { detail?: string } } }) => {
      const detail = err.response?.data?.detail ?? "";
      if (detail.toLowerCase().includes("expired")) {
        toast.error("Session expired — please log in again");
        return;
      }
      if (err.response?.status === 404) {
        toast.error("Account not found");
        return;
      }
      toast.error("Invalid email or password");
    },
  });

  const demo = useMutation(() => demoLogin(), {
    onSuccess: async () => {
      await refetchMe();
      toast.success("Demo mode enabled");
      navigate(from, { replace: true });
    },
    onError: () => toast.error("Demo login failed"),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const result = schema.safeParse({ email, password });
    if (!result.success) {
      toast.error(result.error.errors[0].message);
      return;
    }
    mutation.mutate();
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">Carbonly</CardTitle>
          <CardDescription>Sign in to your account</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
            </div>
            <Button
              type="submit"
              className="w-full"
              isLoading={mutation.isLoading}
            >
              Sign in
            </Button>
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
              onClick={() => demo.mutate()}
              isLoading={demo.isLoading}
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
