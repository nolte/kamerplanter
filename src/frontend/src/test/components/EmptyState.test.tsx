import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { SnackbarProvider } from 'notistack';
import { ThemeContextProvider } from '@/theme';
import EmptyState from '@/components/common/EmptyState';
import '@/i18n';

function renderComponent(props: Parameters<typeof EmptyState>[0] = {}) {
  return render(
    <ThemeContextProvider>
      <SnackbarProvider>
        <EmptyState {...props} />
      </SnackbarProvider>
    </ThemeContextProvider>,
  );
}

describe('EmptyState', () => {
  it('renders default message from i18n', () => {
    renderComponent();
    expect(screen.getByText(/keine daten|no data/i)).toBeTruthy();
  });

  it('renders custom message', () => {
    renderComponent({ message: 'Nothing here' });
    expect(screen.getByText('Nothing here')).toBeTruthy();
  });

  it('renders action button when label and handler provided', () => {
    const onAction = vi.fn();
    renderComponent({ actionLabel: 'Add Item', onAction });
    expect(screen.getByRole('button', { name: 'Add Item' })).toBeTruthy();
  });

  it('calls onAction when button clicked', async () => {
    const user = userEvent.setup();
    const onAction = vi.fn();
    renderComponent({ actionLabel: 'Add', onAction });
    await user.click(screen.getByRole('button', { name: 'Add' }));
    expect(onAction).toHaveBeenCalledOnce();
  });

  it('hides action button when no handler', () => {
    renderComponent({ actionLabel: 'Add' });
    expect(screen.queryByRole('button')).toBeNull();
  });

  it('has aria-hidden icon', () => {
    renderComponent();
    const icon = document.querySelector('[aria-hidden="true"]');
    expect(icon).toBeTruthy();
  });
});
