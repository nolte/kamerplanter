import { Component, createRef, type ErrorInfo, type ReactNode } from 'react';
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
  /**
   * 'inline' (default) — the widget-tile fallback (REQ-045/REQ-009 DoD): a
   * compact `Alert` inside its own panel. 'page' — the app-root fallback
   * (#777): the boundary renders with nothing above it in the tree (no
   * layout, no navigation), so it fills the viewport and centers itself
   * instead of sitting as a stray strip in the top-left corner.
   */
  variant?: 'inline' | 'page';
  /**
   * Only used by variant="page". Retry alone re-mounts the subtree with the
   * same app state — if the error came from something other than transient
   * render timing (e.g. a corrupt persisted store), it fails again
   * immediately. This renders a second, explicit "reload the page" action
   * (a real `window.location.reload()`) alongside Retry.
   */
  reloadLabel?: string;
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
  // variant="page" only: the fallback replaces the entire (otherwise blank)
  // page, so nothing else on screen tells assistive tech something happened.
  // Alert's default role="alert" makes it an ARIA live region, but that only
  // announces — a sighted keyboard user's focus stays wherever it was before
  // the crash (often nowhere, on first paint). Move focus onto the alert
  // itself so both audiences land on the same element.
  private pageAlertRef = createRef<HTMLDivElement>();

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

  componentDidMount(): void {
    // A synchronous render error on the very first mount never produces a
    // committed "not-yet-failed" render — React resolves getDerivedStateFromError
    // before the initial commit, so this instance mounts directly into the
    // error state and componentDidUpdate (below) never fires for it.
    if (this.props.variant === 'page' && this.state.hasError) {
      this.pageAlertRef.current?.focus();
    }
  }

  componentDidUpdate(_prevProps: ErrorBoundaryProps, prevState: ErrorBoundaryState): void {
    if (this.props.variant === 'page' && !prevState.hasError && this.state.hasError) {
      this.pageAlertRef.current?.focus();
    }
  }

  private handleRetry = () => {
    this.retryKey += 1;
    this.setState({ hasError: false });
  };

  private handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.variant === 'page') {
        return (
          <Box
            data-testid={this.props.testId ?? 'widget-error'}
            sx={{
              minHeight: '100dvh',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              p: 2,
            }}
          >
            {/* tabIndex=-1: programmatically focusable without joining the
                (non-existent, on this page) tab order. */}
            <Alert
              ref={this.pageAlertRef}
              tabIndex={-1}
              severity="error"
              sx={{ maxWidth: 480, width: '100%' }}
            >
              <AlertTitle>{this.props.title}</AlertTitle>
              {this.props.hint}
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 2 }}>
                <Button
                  variant="contained"
                  color="error"
                  size="small"
                  onClick={this.handleRetry}
                  sx={{ minHeight: 48 }}
                >
                  {this.props.retryLabel}
                </Button>
                {this.props.reloadLabel && (
                  <Button
                    variant="outlined"
                    color="inherit"
                    size="small"
                    onClick={this.handleReload}
                    sx={{ minHeight: 48 }}
                  >
                    {this.props.reloadLabel}
                  </Button>
                )}
              </Box>
            </Alert>
          </Box>
        );
      }
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
