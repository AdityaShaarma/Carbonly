import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "react-query";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { AuthProvider } from "@/contexts/AuthContext";
import { ErrorBoundary } from "@/components/routes/ErrorBoundary";
import App from "./App";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 0, refetchOnWindowFocus: false },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <ErrorBoundary>
            <App />
            <Toaster position="top-right" />
          </ErrorBoundary>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);
