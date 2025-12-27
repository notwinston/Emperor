import { Component, ErrorInfo, ReactNode } from "react";
import { Button } from "@/components/ui/button";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);
    this.setState({ errorInfo });
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-background p-6">
          <div className="max-w-md w-full text-center">
            <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mb-6 mx-auto">
              <span className="text-3xl">⚠️</span>
            </div>

            <h1 className="text-2xl font-bold text-foreground mb-2">
              Something went wrong
            </h1>
            <p className="text-muted-foreground mb-6">
              An unexpected error occurred. Don't worry, your data is safe.
            </p>

            {this.state.error && (
              <div className="bg-zinc-900 rounded-lg p-4 mb-6 text-left">
                <p className="text-sm font-mono text-red-400 break-all">
                  {this.state.error.message}
                </p>
              </div>
            )}

            <div className="flex gap-3 justify-center">
              <Button variant="ghost" onClick={this.handleRetry}>
                Try Again
              </Button>
              <Button
                onClick={this.handleReload}
                className="bg-amber-500 hover:bg-amber-600 text-black"
              >
                Reload App
              </Button>
            </div>

            <p className="text-xs text-muted-foreground mt-8">
              If this keeps happening,{" "}
              <a
                href="https://github.com/anthropics/claude-code/issues"
                target="_blank"
                rel="noopener noreferrer"
                className="text-amber-500 hover:underline"
              >
                report an issue
              </a>
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Smaller error boundary for individual components
export function ComponentErrorFallback({
  error,
  onRetry,
}: {
  error: Error;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-6 bg-zinc-900/50 rounded-lg border border-zinc-800">
      <span className="text-2xl mb-2">😵</span>
      <p className="text-sm text-muted-foreground mb-3">
        This component failed to load
      </p>
      {onRetry && (
        <Button size="sm" variant="ghost" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}
