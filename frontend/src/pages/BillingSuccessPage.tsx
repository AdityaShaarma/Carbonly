import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useEffect } from "react";
import toast from "react-hot-toast";
import { confirmCheckout } from "@/api/billing";
import { useAuth } from "@/contexts/AuthContext";

export function BillingSuccessPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { refetchMe } = useAuth();

  useEffect(() => {
    const sessionId = params.get("session_id");
    if (!sessionId) {
      toast.error("Missing checkout session id");
      return;
    }
    confirmCheckout(sessionId)
      .then(async () => {
        await refetchMe();
        navigate("/billing", { replace: true });
      })
      .catch(() => {
        toast.error("Unable to confirm subscription");
      });
  }, [params, navigate, refetchMe]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Billing</h1>
      <Card>
        <CardHeader>
          <CardTitle>Subscription active</CardTitle>
          <CardDescription>Your plan is now active.</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-2">
          <Link to="/reports">
            <Button>Go to reports</Button>
          </Link>
          <Link to="/billing">
            <Button variant="outline">Back to billing</Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
