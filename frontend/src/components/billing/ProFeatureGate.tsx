import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/Button";

export function ProFeatureGate({ children }: { children: React.ReactNode }) {
  const { company } = useAuth();
  const isPro = company?.plan === "pro";

  if (isPro) {
    return <>{children}</>;
  }

  return (
    <div className="relative">
      <div className="pointer-events-none blur-[1px] opacity-70">{children}</div>
      <div className="absolute inset-0 flex items-end justify-end p-3">
        <div className="pointer-events-auto flex flex-col items-end gap-2 rounded-md border border-border bg-background/90 px-3 py-2 text-xs text-muted-foreground shadow-sm">
          <div className="flex items-center gap-2">
            <span>Pro feature</span>
            <Link to="/billing">
              <Button size="md">Unlock Pro insights</Button>
            </Link>
          </div>
          <span className="text-xs text-muted-foreground">
            Get reduction recommendations and advanced analytics
          </span>
        </div>
      </div>
    </div>
  );
}
