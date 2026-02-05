import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useMutation } from "react-query";
import { z } from "zod";
import { login } from "@/api/auth";
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

  const mutation = useMutation(() => login(email, password), {
    onSuccess: async () => {
      await refetchMe();
      toast.success("Logged in");
      navigate(from, { replace: true });
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      toast.error(err.response?.data?.detail ?? "Login failed");
    },
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
          <p className="mt-4 text-center text-xs text-muted-foreground">
            Demo: test@carbonly.com / password123 (after seeding backend)
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
