import { Component, type ErrorInfo, type ReactNode } from 'react';
import Box from '@mui/material/Box';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Button from '@mui/material/Button';
import { captureHandledError } from '@/observability/errorTracking';

interface ErrorBoundaryProps {
  children: ReactNode;
  /** i18n-resolved title + hint + retry label (passed in so this stays i18n-agnostic). */
  title: string;
  hint: string;
  retryLabel: string;
  testId?: string;
  /** Names the failing subtree in the error report (e.g. the widget key). */
  boundaryName?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

/**
 * Generic error isolation boundary. Used per dashboard widget (REQ-045 §3.9 /
 * REQ-009 DoD) so a single failing widget shows an inline error + retry without
 * taking down the whole page. Retry remounts the subtree by bumping the key.
 */
export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private retryKey = 0;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  /**
   * Report the failure (#777). A boundary that renders a fallback has, from
   * every global handler's point of view, made the error disappear: the user
   * sees a tidy card and nobody is told the widget is broken. This is the
   * runtime complement of the swallowed-error no-go — no-op without a DSN.
   */
  componentDidCatch(error: Error, info: ErrorInfo): void {
    captureHandledError(error, {
      boundary: this.props.boundaryName ?? this.props.testId ?? 'unnamed',
      componentStack: info.componentStack,
    });
  }

  private handleRetry = () => {
    this.retryKey += 1;
    this.setState({ hasError: false });
  };

  render() {
    if (this.state.hasError) {
      return (
        <Box sx={{ p: 2 }} data-testid={this.props.testId ?? 'widget-error'}>
          <Alert
            severity="error"
            action={
              <Button
                color="inherit"
                size="small"
                onClick={this.handleRetry}
                sx={{ minHeight: 48 }}
              >
                {this.props.retryLabel}
              </Button>
            }
          >
            <AlertTitle>{this.props.title}</AlertTitle>
            {this.props.hint}
          </Alert>
        </Box>
      );
    }
    return <Box key={this.retryKey}>{this.props.children}</Box>;
  }
}
