import { Link } from "react-router-dom";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export function BillingCancelPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Billing</h1>
      <Card>
        <CardHeader>
          <CardTitle>Checkout canceled</CardTitle>
          <CardDescription>Your subscription was not changed.</CardDescription>
        </CardHeader>
        <CardContent>
          <Link to="/billing">
            <Button>Back to billing</Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
