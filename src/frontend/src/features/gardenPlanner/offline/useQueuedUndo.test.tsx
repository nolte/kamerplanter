import 'fake-indexeddb/auto';
import { cleanup, screen, waitFor } from '@testing-library/react';
import { useEffect } from 'react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { renderWithProviders } from '@/test/helpers';
import { ALICE_A, capture, emptyWriteQueue } from '@/test/writeQueueTestKit';
import { discardEntry, removeEntry, updateEntry } from './queue';
import type { QueueEntry } from './queueTypes';
import { useQueuedUndo } from './useQueuedUndo';

/**
 * #2814 — the "Undo" toast of a buffered entry, with the real snackbar provider and a real IndexedDB: it closes when
 * the entry is sent, discarded or ran into a conflict, and stays while the entry still waits.
 */

type Offer = (entry: QueueEntry, message: string) => void;
let offer: Offer | null = null;

function Offerer({ onReady }: { onReady: (value: Offer) => void }) {
  const { offerQueuedUndo } = useQueuedUndo(ALICE_A);
  useEffect(() => onReady(offerQueuedUndo), [offerQueuedUndo, onReady]);
  return null;
}

async function offered(): Promise<QueueEntry> {
  const entry = await capture(ALICE_A);
  renderWithProviders(
    <Offerer
      onReady={(value) => {
        offer = value;
      }}
    />,
  );
  await waitFor(() => expect(offer).not.toBeNull());
  offer!(entry, 'Notiz auf dem Gerät gespeichert');
  await screen.findByTestId('care-undo');
  return entry;
}

beforeEach(async () => {
  offer = null;
  await emptyWriteQueue();
});

afterEach(() => cleanup());

describe('useQueuedUndo (#2814)', () => {
  it('closes the toast once a sync sent the entry', async () => {
    const entry = await offered();

    await removeEntry(ALICE_A, entry.seq!);

    await waitFor(() => expect(screen.queryByTestId('care-undo')).toBeNull());
  });

  it('closes the toast once the entry was discarded elsewhere (the conflict dialog)', async () => {
    const entry = await offered();

    await discardEntry(ALICE_A, entry.id);

    await waitFor(() => expect(screen.queryByTestId('care-undo')).toBeNull());
  });

  it('closes the toast when the entry runs into a conflict, so it cannot cover the conflict dialog', async () => {
    const entry = await offered();

    await updateEntry(ALICE_A, entry.seq!, { status: 'conflict', conflictCode: 'task.already_closed' });

    await waitFor(() => expect(screen.queryByTestId('care-undo')).toBeNull());
  });

  it('keeps the toast while the entry still waits, e.g. when another entry is captured', async () => {
    await offered();

    await capture(ALICE_A);
    await new Promise((resolve) => setTimeout(resolve, 50));

    expect(screen.getByTestId('care-undo')).toBeInTheDocument();
  });
});
