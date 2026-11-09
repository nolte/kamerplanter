import 'fake-indexeddb/auto';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ALICE_A, capture, emptyWriteQueue } from '@/test/writeQueueTestKit';
import { discardEntry, removeEntry, updateEntry } from './queue';
import { watchSettled } from './watchSettled';

/**
 * #2814 — the "Undo" toast of a buffered entry follows the entry: it goes once the entry was sent, discarded, is on
 * its way or ran into a conflict, and only then.
 */

beforeEach(async () => {
  await emptyWriteQueue();
});

describe('watchSettled (#2814)', () => {
  it('fires when the entry is discarded', async () => {
    const entry = await capture(ALICE_A);
    const settled = vi.fn();
    watchSettled(ALICE_A, entry.id, settled);

    await discardEntry(ALICE_A, entry.id);

    await vi.waitFor(() => expect(settled).toHaveBeenCalledTimes(1));
  });

  it('fires when a sync sent the entry (it leaves the buffer)', async () => {
    const entry = await capture(ALICE_A);
    const settled = vi.fn();
    watchSettled(ALICE_A, entry.id, settled);

    await removeEntry(ALICE_A, entry.seq!);

    await vi.waitFor(() => expect(settled).toHaveBeenCalledTimes(1));
  });

  it('fires when the entry is on its way or in conflict, and only once', async () => {
    const entry = await capture(ALICE_A);
    const settled = vi.fn();
    watchSettled(ALICE_A, entry.id, settled);

    await updateEntry(ALICE_A, entry.seq!, { status: 'syncing', syncingSince: Date.now() });
    await vi.waitFor(() => expect(settled).toHaveBeenCalledTimes(1));
    await updateEntry(ALICE_A, entry.seq!, { status: 'conflict', conflictCode: 'task.already_closed' });

    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(settled).toHaveBeenCalledTimes(1);
  });

  it('stays quiet while the entry still waits, e.g. when another entry is captured', async () => {
    const entry = await capture(ALICE_A);
    const settled = vi.fn();
    const stop = watchSettled(ALICE_A, entry.id, settled);

    await capture(ALICE_A);
    await new Promise((resolve) => setTimeout(resolve, 20));

    expect(settled).not.toHaveBeenCalled();
    stop();
    await discardEntry(ALICE_A, entry.id);
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(settled).not.toHaveBeenCalled();
  });
});
