import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import { SnackbarProvider } from 'notistack';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import i18n from '@/i18n/i18n';

function renderComponent(props: { error: string; onRetry?: () => void }) {
  return render(
    <ThemeContextProvider>
      <SnackbarProvider>
        <ErrorDisplay {...props} />
      </SnackbarProvider>
    </ThemeContextProvider>,
  );
}

describe('ErrorDisplay', () => {
  it('renders error message in alert', () => {
    renderComponent({ error: 'Something went wrong' });
    expect(screen.getByTestId('error-display')).toBeTruthy();
    expect(screen.getByText('Something went wrong')).toBeTruthy();
  });

  it('resolves an errors.* i18n key to localized text (FE-L5)', () => {
    renderComponent({ error: 'errors.loadFailed' });
    // Resolved against the active locale — the raw key must never reach the DOM.
    expect(screen.getByText(i18n.t('errors.loadFailed'))).toBeTruthy();
    expect(screen.queryByText('errors.loadFailed')).toBeNull();
  });

  it('maps a raw "not found" backend message via the pattern fallback', () => {
    renderComponent({ error: 'Species not found' });
    expect(screen.getByText(i18n.t('errors.notFound'))).toBeTruthy();
  });

  it('renders an unknown raw message unchanged', () => {
    renderComponent({ error: 'Something unexpected' });
    expect(screen.getByText('Something unexpected')).toBeTruthy();
  });

  it('renders retry button when onRetry provided', () => {
    renderComponent({ error: 'Fail', onRetry: vi.fn() });
    expect(screen.getByRole('button')).toBeTruthy();
  });

  it('calls onRetry when button clicked', async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    renderComponent({ error: 'Fail', onRetry });
    await user.click(screen.getByRole('button'));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it('hides retry button when no onRetry', () => {
    renderComponent({ error: 'Fail' });
    expect(screen.queryByRole('button')).toBeNull();
  });
});
