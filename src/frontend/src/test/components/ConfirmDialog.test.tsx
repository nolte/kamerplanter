import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import { SnackbarProvider } from 'notistack';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import '@/i18n';

function renderDialog(props: Partial<Parameters<typeof ConfirmDialog>[0]> = {}) {
  const defaults = {
    open: true,
    title: 'Delete Item',
    message: 'Are you sure?',
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
  };
  const merged = { ...defaults, ...props };
  return { ...merged, ...render(
    <ThemeContextProvider>
      <SnackbarProvider>
        <ConfirmDialog {...merged} />
      </SnackbarProvider>
    </ThemeContextProvider>,
  )};
}

describe('ConfirmDialog', () => {
  it('renders title and message', () => {
    renderDialog();
    expect(screen.getByText('Delete Item')).toBeTruthy();
    expect(screen.getByText('Are you sure?')).toBeTruthy();
  });

  it('has alertdialog role', () => {
    renderDialog();
    expect(screen.getByRole('alertdialog')).toBeTruthy();
  });

  it('calls onCancel when cancel clicked', async () => {
    const user = userEvent.setup();
    const { onCancel } = renderDialog();
    await user.click(screen.getByRole('button', { name: /abbrechen|cancel/i }));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it('calls onConfirm when confirm clicked', async () => {
    const user = userEvent.setup();
    const { onConfirm } = renderDialog();
    await user.click(screen.getByRole('button', { name: /bestätigen|confirm/i }));
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it('uses custom confirm label', () => {
    renderDialog({ confirmLabel: 'Yes, delete' });
    expect(screen.getByRole('button', { name: 'Yes, delete' })).toBeTruthy();
  });

  it('renders contained button for confirm action', () => {
    renderDialog({ destructive: true });
    const confirmBtn = screen.getByRole('button', { name: /bestätigen|confirm/i });
    expect(confirmBtn.classList.toString()).toContain('contained');
  });

  it('disables buttons when loading', () => {
    renderDialog({ loading: true });
    const buttons = screen.getAllByRole('button');
    buttons.forEach((btn) => expect(btn).toBeDisabled());
  });

  it('is not visible when closed', () => {
    renderDialog({ open: false });
    expect(screen.queryByText('Delete Item')).toBeNull();
  });
});
