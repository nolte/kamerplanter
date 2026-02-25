import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import { SnackbarProvider } from 'notistack';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import '@/i18n';

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
    expect(screen.getByRole('alert')).toBeTruthy();
    expect(screen.getByText('Something went wrong')).toBeTruthy();
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
