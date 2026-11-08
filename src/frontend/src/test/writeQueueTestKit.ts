/**
 * Test kit for the offline write buffer (REQ-053 WP 9.4): an empty buffer for every test, as after a page load,
 * and entries as the field sheet captures them. Import `fake-indexeddb/auto` in the test file before this runs.
 */
import { enqueue, newClientEventId, resetWriteQueueForTests } from '@/features/gardenPlanner/offline/queue';
import { writeQueueDatabase } from '@/features/gardenPlanner/offline/queueDb';
import type { CacheScope } from '@/features/gardenPlanner/offline/planCache';
import type { QueueEntry, QueueStatus, QueuedWrite } from '@/features/gardenPlanner/offline/queueTypes';

export const ALICE_A: CacheScope = { userKey: 'alice', tenantKey: 'tenant_a' };
export const ALICE_B: CacheScope = { userKey: 'alice', tenantKey: 'tenant_b' };
export const BOB_A: CacheScope = { userKey: 'bob', tenantKey: 'tenant_a' };

export function testWriteQueueDatabase() {
  return writeQueueDatabase(() => undefined);
}

export async function emptyWriteQueue(): Promise<void> {
  resetWriteQueueForTests();
  await testWriteQueueDatabase().entries.clear();
}

export function noteWrite(summary = 'Aphids on the beans', locationKey = 'loc_a'): QueuedWrite {
  return {
    kind: 'note',
    body: { location_key: locationKey, category: 'note', summary, performed_at: '2026-11-08T07:00:00.000Z' },
  };
}

export function completeWrite(taskKey = 't_water'): QueuedWrite {
  return {
    kind: 'complete',
    taskKey,
    taskName: 'Water the bed',
    payload: { performed_at: '2026-11-08T07:00:00.000Z' },
  };
}

/** Buffer `write` for `scope` at the bed `loc_a`. */
export function capture(scope: CacheScope, write: QueuedWrite = noteWrite(), now = Date.now()) {
  return enqueue({ scope, bedKey: 'loc_a', bedName: 'Raised bed 1', write }, now);
}

/**
 * A row written straight into the table, past `enqueue` — for states a capture cannot produce today (an entry
 * captured a year ago, a note dated back, a failed one). Returns the stored row.
 */
export async function storeRow(
  scope: CacheScope,
  { capturedAt, performedAt, status = 'pending' }: { capturedAt: number; performedAt?: number; status?: QueueStatus },
): Promise<QueueEntry> {
  const row: QueueEntry = {
    id: newClientEventId(),
    userKey: scope.userKey,
    tenantKey: scope.tenantKey,
    capturedAt,
    status,
    attempts: 0,
    nextAttemptAt: 0,
    syncingSince: null,
    lastErrorCode: null,
    conflictCode: status === 'conflict' ? 'task.already_closed' : null,
    kept: false,
    bedKey: 'loc_a',
    bedName: 'Raised bed 1',
    write: {
      kind: 'note',
      body: { location_key: 'loc_a', category: 'note', summary: 'row', performed_at: new Date(performedAt ?? capturedAt).toISOString() },
    },
  };
  row.seq = await testWriteQueueDatabase().entries.add(row);
  return row;
}

/** Another tab ends `userKey`'s session (the `kp-offline` broadcast): this tab's buffer retires. */
export async function retireFromOtherTab(userKey: string): Promise<void> {
  const { OFFLINE_CLEAR_CHANNEL, postNamespace } = await import('@/pwa/offlineData');
  await postNamespace(userKey, 'tenant_a');
  const channel = new BroadcastChannel(OFFLINE_CLEAR_CHANNEL);
  channel.postMessage({ type: 'offline-data-cleared', userKey });
  channel.close();
  await new Promise((resolve) => setTimeout(resolve, 30));
}
