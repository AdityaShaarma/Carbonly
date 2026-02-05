import { Outlet } from "react-router-dom";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { logout } from "@/api/auth";
import { useQueryClient } from "react-query";
import {
  LayoutDashboard,
  Plug,
  FileEdit,
  FileText,
  Settings,
  Lightbulb,
  LogOut,
  CreditCard,
  HeartPulse,
} from "lucide-react";
import { cn } from "@/utils/cn";
import { OnboardingGate } from "@/components/routes/OnboardingGate";

const nav = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/integrations", label: "Integrations", icon: Plug },
  { to: "/manual", label: "Manual Data", icon: FileEdit },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/insights", label: "Insights", icon: Lightbulb },
  { to: "/settings", label: "Settings", icon: Settings },
  { to: "/billing", label: "Billing", icon: CreditCard },
  { to: "/health", label: "Health", icon: HeartPulse },
];

export function Layout() {
  const location = useLocation();
  const { company, user, clearAuth } = useAuth();
  const queryClient = useQueryClient();

  const handleLogout = () => {
    logout();
    queryClient.clear();
    clearAuth();
    window.location.href = "/login";
  };

  return (
    <div className="flex min-h-screen bg-muted/30">
      <aside className="w-56 border-r border-border bg-card flex flex-col">
        <div className="p-4 border-b border-border">
          <Link to="/dashboard" className="font-semibold text-primary text-lg">
            Carbonly
          </Link>
        </div>
        <nav className="flex-1 p-2 space-y-0.5">
          {nav.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                location.pathname === to ||
                  (to !== "/dashboard" && location.pathname.startsWith(to))
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>
      </aside>
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-border bg-card flex items-center justify-between px-6">
          <span className="text-sm text-muted-foreground truncate">
            {company?.name}
          </span>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground truncate max-w-[200px]">
              {user?.email}
            </span>
            <button
              type="button"
              onClick={handleLogout}
              className="p-2 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground"
              title="Log out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </header>
        <main className="flex-1 p-6 overflow-auto">
          <OnboardingGate>
            <Outlet />
          </OnboardingGate>
        </main>
      </div>
    </div>
  );
}
