import { useEffect, useState } from "react";
import { useSearchParams, Link, useNavigate } from "react-router-dom";
import { verifyEmailToken } from "@/api/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

export function VerifyEmailPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading"
  );

  useEffect(() => {
    const token = params.get("token");
    if (!token) {
      setStatus("error");
      return;
    }
    verifyEmailToken(token)
      .then(() => {
        setStatus("success");
        navigate("/onboarding", { replace: true });
      })
      .catch(() => setStatus("error"));
  }, [params, navigate]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Email verification</CardTitle>
        </CardHeader>
        <CardContent>
          {status === "loading" && <p>Verifying your email…</p>}
          {status === "success" && (
            <div className="space-y-2">
              <p>Your email is verified. You can continue to Carbonly.</p>
              <Link to="/login" className="text-primary hover:underline">
                Go to login
              </Link>
            </div>
          )}
          {status === "error" && (
            <div className="space-y-2">
              <p>Verification link is invalid or expired.</p>
              <Link to="/login" className="text-primary hover:underline">
                Back to login
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
