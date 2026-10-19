/**
 * The undo snackbar (REQ-053 GP-FR-149): eight seconds on screen, one "Undo" action that runs the
 * supplied call and then the follow-up. The duration is read from what the hook hands to notistack.
 */
import { act, cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { SnackbarKey } from 'notistack';
import { renderWithProviders } from '@/test/helpers';
import { UNDO_SNACKBAR_MS, useUndoSnackbar } from './useUndoSnackbar';

const enqueue = vi.fn();
const close = vi.fn();
vi.mock('notistack', async (importOriginal) => ({
  ...(await importOriginal<typeof import('notistack')>()),
  useSnackbar: () => ({ enqueueSnackbar: enqueue, closeSnackbar: close }),
}));

function Probe({ undo, onUndone }: { undo: () => Promise<void>; onUndone: () => void }) {
  const { offerUndo } = useUndoSnackbar();
  return (
    <button type="button" onClick={() => offerUndo({ message: 'Done: Weed', undo, onUndone })}>
      offer
    </button>
  );
}

afterEach(() => {
  cleanup();
  enqueue.mockReset();
  close.mockReset();
});

describe('useUndoSnackbar', () => {
  it('keeps the snackbar for eight seconds', () => {
    expect(UNDO_SNACKBAR_MS).toBe(8000);
  });

  it('enqueues the message for that long with an Undo action that runs the call, then the follow-up', async () => {
    const undo = vi.fn().mockResolvedValue(undefined);
    const onUndone = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<Probe undo={undo} onUndone={onUndone} />);
    await user.click(screen.getByText('offer'));

    expect(enqueue).toHaveBeenCalledTimes(1);
    const [message, options] = enqueue.mock.calls[0] as [string, { autoHideDuration: number; action: (id: SnackbarKey) => React.ReactNode }];
    expect(message).toBe('Done: Weed');
    expect(options.autoHideDuration).toBe(8000);

    render(<>{options.action('snack-1')}</>);
    await user.click(screen.getByTestId('care-undo'));
    expect(close).toHaveBeenCalledWith('snack-1');
    expect(undo).toHaveBeenCalledTimes(1);
    await act(async () => undefined);
    expect(onUndone).toHaveBeenCalledTimes(1);
  });

  it('does not run the follow-up when the server refuses the undo', async () => {
    const undo = vi.fn().mockRejectedValue(new Error('403'));
    const onUndone = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(<Probe undo={undo} onUndone={onUndone} />);
    await user.click(screen.getByText('offer'));
    const [, options] = enqueue.mock.calls[0] as [string, { action: (id: SnackbarKey) => React.ReactNode }];
    render(<>{options.action('snack-2')}</>);
    await user.click(screen.getByTestId('care-undo'));
    await act(async () => undefined);
    expect(onUndone).not.toHaveBeenCalled();
  });
});
