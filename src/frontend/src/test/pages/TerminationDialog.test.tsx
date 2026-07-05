import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import { SnackbarProvider } from 'notistack';
import TerminationDialog from '@/pages/pflanzen/TerminationDialog';
import '@/i18n';

function renderDialog(props: Partial<Parameters<typeof TerminationDialog>[0]> = {}) {
  const merged = {
    open: true,
    plantName: 'TOMATO-1',
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
    ...props,
  };
  return {
    ...merged,
    ...render(
      <ThemeContextProvider>
        <SnackbarProvider>
          <TerminationDialog {...merged} />
        </SnackbarProvider>
      </ThemeContextProvider>,
    ),
  };
}

async function openTypeAndSelect(user: ReturnType<typeof userEvent.setup>, value: string) {
  const select = within(screen.getByTestId('termination-type-select')).getByRole('combobox');
  await user.click(select);
  await user.click(await screen.findByTestId(`termination-type-${value}`));
}

describe('TerminationDialog', () => {
  it('shows no cause select until "died" is chosen', () => {
    renderDialog();
    expect(screen.getByTestId('termination-type-select')).toBeTruthy();
    expect(screen.queryByTestId('termination-cause-block')).toBeNull();
  });

  it('plain confirm without a type performs a backward-compatible removal', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    renderDialog({ onConfirm });
    await user.click(screen.getByTestId('termination-confirm'));
    expect(onConfirm).toHaveBeenCalledWith({});
  });

  it('a planned end submits only the termination_type', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    renderDialog({ onConfirm });
    await openTypeAndSelect(user, 'harvested');
    expect(screen.queryByTestId('termination-cause-block')).toBeNull();
    await user.click(screen.getByTestId('termination-confirm'));
    expect(onConfirm).toHaveBeenCalledWith({ termination_type: 'harvested' });
  });

  it('requires a cause for "died" and submits type + cause', async () => {
    const user = userEvent.setup();
    const onConfirm = vi.fn();
    renderDialog({ onConfirm });
    await openTypeAndSelect(user, 'died');

    // Cause block appears and confirm is blocked until a cause is picked.
    expect(screen.getByTestId('termination-cause-block')).toBeTruthy();
    expect(screen.getByTestId('termination-confirm')).toBeDisabled();

    const causeSelect = within(screen.getByTestId('termination-cause-select')).getByRole('combobox');
    await user.click(causeSelect);
    await user.click(await screen.findByTestId('termination-cause-pest'));

    const confirm = screen.getByTestId('termination-confirm');
    expect(confirm).not.toBeDisabled();
    await user.click(confirm);
    expect(onConfirm).toHaveBeenCalledWith({ termination_type: 'died', termination_cause: 'pest' });
  });

  it('calls onCancel when cancelled', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    renderDialog({ onCancel });
    await user.click(screen.getByTestId('termination-cancel'));
    expect(onCancel).toHaveBeenCalledOnce();
  });
});
