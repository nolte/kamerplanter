/**
 * Test kit for the offline write buffer (REQ-053 WP 9.4): an empty buffer for every test, as after a page load,
 * and entries as the field sheet captures them. Import `fake-indexeddb/auto` in the test file before this runs.
 */
import { enqueue, resetWriteQueueForTests } from '@/features/gardenPlanner/offline/queue';
import { writeQueueDatabase } from '@/features/gardenPlanner/offline/queueDb';
import type { CacheScope } from '@/features/gardenPlanner/offline/planCache';
import type { QueuedWrite } from '@/features/gardenPlanner/offline/queueTypes';

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
