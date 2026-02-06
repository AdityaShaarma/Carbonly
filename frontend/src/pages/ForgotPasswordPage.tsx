import { useState } from "react";
import { useMutation } from "react-query";
import { z } from "zod";
import toast from "react-hot-toast";
import { Link } from "react-router-dom";
import { forgotPassword } from "@/api/auth";
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

const schema = z.object({
  email: z.string().email("Invalid email"),
});

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");

  const mutation = useMutation(() => forgotPassword(email), {
    onSuccess: () => {
      toast.success("If the email exists, a reset link was sent.");
    },
    onError: () => {
      toast.error("Failed to request reset link");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const result = schema.safeParse({ email });
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
          <CardTitle className="text-2xl">Reset your password</CardTitle>
          <CardDescription>We will email you a reset link</CardDescription>
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
            <Button
              type="submit"
              className="w-full"
              isLoading={mutation.isLoading}
            >
              Send reset link
            </Button>
          </form>
          <div className="mt-3 text-center text-sm">
            <Link to="/login" className="text-primary hover:underline">
              Back to login
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
