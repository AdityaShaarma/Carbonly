import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";

export function BillingPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Billing</h1>
      <Card>
        <CardHeader>
          <CardTitle>Billing locked</CardTitle>
          <CardDescription>
            This area is managed by your account administrator.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Billing is available after onboarding. If you need access, contact
          support.
        </CardContent>
      </Card>
    </div>
  );
}
