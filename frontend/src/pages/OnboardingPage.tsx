import { useMutation, useQuery, useQueryClient } from "react-query";
import { fetchOnboarding, updateOnboarding } from "@/api/onboarding";
import { syncProvider } from "@/api/integrations";
import { Button } from "@/components/ui/Button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/Card";
import toast from "react-hot-toast";
import { Link } from "react-router-dom";

export function OnboardingPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery("onboarding", fetchOnboarding);

  const update = useMutation(
    (payload: { [key: string]: boolean }) => updateOnboarding(payload),
    {
      onSuccess: () => {
        queryClient.invalidateQueries("onboarding");
        toast.success("Onboarding updated");
      },
      onError: () => toast.error("Failed to update onboarding"),
    }
  );

  const simulateAws = useMutation(() => syncProvider("aws"), {
    onSuccess: async () => {
      await update.mutateAsync({ connect_aws: true });
      queryClient.invalidateQueries("integrations");
      toast.success("AWS simulated and connected");
    },
    onError: () => toast.error("AWS simulation failed"),
  });

  if (isLoading || !data) {
    return <div className="h-40 animate-pulse rounded-lg bg-muted" />;
  }

  const state = data.state;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Get started</h1>
      <Card>
        <CardHeader>
          <CardTitle>Onboarding checklist</CardTitle>
          <CardDescription>
            Complete these steps to generate your first report
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">1) Connect AWS</p>
              <p className="text-sm text-muted-foreground">
                Simulate connection to seed data
              </p>
            </div>
            {state.connect_aws ? (
              <span className="text-sm text-primary">Done</span>
            ) : (
              <Button
                size="sm"
                onClick={() => simulateAws.mutate()}
                isLoading={simulateAws.isLoading}
              >
                Simulate connection
              </Button>
            )}
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">2) Upload CSV</p>
              <p className="text-sm text-muted-foreground">
                Add manual data via CSV upload
              </p>
            </div>
            {state.upload_csv ? (
              <span className="text-sm text-primary">Done</span>
            ) : (
              <Button
                size="sm"
                variant="outline"
                onClick={() => update.mutate({ upload_csv: true })}
              >
                Mark complete
              </Button>
            )}
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">3) Add manual activity</p>
              <p className="text-sm text-muted-foreground">
                Enter a single activity record
              </p>
            </div>
            {state.add_manual_activity ? (
              <span className="text-sm text-primary">Done</span>
            ) : (
              <Link to="/manual">
                <Button size="sm" variant="outline">
                  Go to manual data
                </Button>
              </Link>
            )}
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">4) Create report</p>
              <p className="text-sm text-muted-foreground">
                Generate a procurement-ready report
              </p>
            </div>
            {state.create_report ? (
              <span className="text-sm text-primary">Done</span>
            ) : (
              <Link to="/reports">
                <Button size="sm" variant="outline">
                  Go to reports
                </Button>
              </Link>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
