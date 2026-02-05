import React from "react";
import { Button } from "@/components/ui/Button";

type ErrorBoundaryState = { hasError: boolean; error?: Error };

export class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error) {
    // eslint-disable-next-line no-console
    console.error("UI ErrorBoundary caught:", error);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
    window.location.href = "/";
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-muted/30 p-6">
          <div className="max-w-md rounded-lg border border-border bg-card p-6 text-center">
            <h1 className="text-xl font-semibold">Something went wrong</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Please refresh the page or return to the dashboard.
            </p>
            <div className="mt-4 flex justify-center gap-2">
              <Button
                onClick={() => window.location.reload()}
                variant="outline"
              >
                Refresh
              </Button>
              <Button onClick={this.handleReset}>Go home</Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
