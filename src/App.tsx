import { lazy, Suspense, useCallback } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Sidebar } from "@/components/Sidebar";
import { StatusBar } from "@/components/StatusBar";
import { ChatPanel } from "@/components/ChatPanel";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Onboarding } from "@/components/Onboarding";
import { ToastContainer } from "@/components/Toast";
import { useOnboardingStore } from "@/stores/onboardingStore";
import { useKeyboardShortcuts, APP_SHORTCUTS } from "@/hooks/useKeyboardShortcuts";
import { toast } from "@/stores/toastStore";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

// Loading fallback for lazy components
function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="animate-pulse text-muted-foreground">Loading...</div>
    </div>
  );
}

function AppContent() {
  const { isComplete } = useOnboardingStore();

  // Global keyboard shortcuts
  useKeyboardShortcuts({
    shortcuts: [
      {
        ...APP_SHORTCUTS.OPEN_SETTINGS,
        action: () => toast.info("Settings", "Settings panel coming soon"),
        description: "Open settings",
      },
      {
        ...APP_SHORTCUTS.NEW_CONVERSATION,
        action: () => toast.info("New Chat", "Starting new conversation"),
        description: "New conversation",
      },
      {
        ...APP_SHORTCUTS.COMMAND_PALETTE,
        action: () => toast.info("Commands", "Command palette coming soon"),
        description: "Open command palette",
      },
    ],
  });

  // Show onboarding if not complete
  if (!isComplete) {
    return <Onboarding />;
  }

  return (
    <div className="flex h-full bg-background">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content area */}
      <div className="flex flex-1 flex-col">
        {/* Status bar */}
        <StatusBar />

        {/* Chat panel */}
        <Suspense fallback={<LoadingFallback />}>
          <ChatPanel />
        </Suspense>
      </div>

      {/* Toast notifications */}
      <ToastContainer />
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AppContent />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
