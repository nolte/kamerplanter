import 'fake-indexeddb/auto';
import { AxiosError } from 'axios';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { setActiveTenantSlug } from '@/api/client';
import { ApiError } from '@/api/errors';
import { server } from '@/test/mocks/server';
import { ALICE_A, BOB_A, capture, completeWrite, emptyWriteQueue, noteWrite } from '@/test/writeQueueTestKit';
import { MAX_ATTEMPTS, listEntries, queueGeneration, removeEntry, updateEntry } from './queue';
import {
  SYNC_STALE_MS,
  classifySendError,
  createSyncScheduler,
  syncQueue,
  withSyncLock,
  type SyncResult,
} from './sync';
import type { ConflictCode, QueueEntry } from './queueTypes';

/**
 * REQ-053 WP 9.4 (#2744), UI-NFR-012 R-021…R-027, R-045 — the FIFO sync of the offline write buffer: order, the
 * stable `client_event_id` across retries (G-W9 f) with a replay `200` as success, the 1 → 60 s backoff, `failed`
 * after five attempts, the four WP 9.3 conflict codes, the owner scope, and the single-flight scheduler.
 */

const BASE = '/api/v1/t/:tenant';
const T0 = Date.UTC(2026, 10, 8, 8, 0, 0);

beforeAll(() => setActiveTenantSlug('testgarten'));

beforeEach(async () => {
  await emptyWriteQueue();
});

afterEach(() => {
  vi.useRealTimers();
});

function envelope(code: string, status: number) {
  return HttpResponse.json(
    { error_id: 'e1', error_code: code, message: 'refused', details: [], path: '/x', method: 'POST' },
    { status },
  );
}

/** The care-event route: records every body; `answer` decides the reply per call (default 201). */
function useCareEvents(answer: (call: number) => Response | Promise<Response> = () => HttpResponse.json({ key: 'ce_1', category: 'note' }, { status: 201 })) {
  const bodies: Record<string, unknown>[] = [];
  server.use(
    http.post(`${BASE}/care-events`, async ({ request }) => {
      bodies.push((await request.json()) as Record<string, unknown>);
      return answer(bodies.length);
    }),
  );
  return bodies;
}

function apiError(status: number, code: string): ApiError {
  return new ApiError({ error_id: 'e', error_code: code, message: 'x', details: [], path: '/', method: 'POST' } as never, status);
}

/** The text fields of a multipart body (jsdom's `File` does not survive undici's `formData()`). */
function formFields(body: string): Record<string, string> {
  const fields: Record<string, string> = {};
  for (const match of body.matchAll(/name="([^"]+)"\r\n\r\n([^\r]*)\r\n/g)) fields[match[1]] = match[2];
  return fields;
}

async function statusOf(entry: QueueEntry): Promise<QueueEntry | undefined> {
  return (await listEntries(ALICE_A)).find((row) => row.id === entry.id);
}

describe('FIFO with one client_event_id per entry', () => {
  it('sends in capture order, each with its own id and its capture-time body, and deletes what was sent', async () => {
    const bodies = useCareEvents();
    const first = await capture(ALICE_A, noteWrite('first'));
    const second = await capture(ALICE_A, noteWrite('second'));
    const third = await capture(ALICE_A, noteWrite('third'));

    const progress: number[] = [];
    const result = await syncQueue({ scope: ALICE_A, now: () => T0, onProgress: (value) => progress.push(value.done) });

    expect(result).toMatchObject({ sent: 3, conflicts: 0, failed: 0, nextRetryAt: null });
    expect(bodies.map((body) => body.summary)).toEqual(['first', 'second', 'third']);
    expect(bodies.map((body) => body.client_event_id)).toEqual([first.id, second.id, third.id]);
    expect(bodies[0].performed_at).toBe('2026-11-08T07:00:00.000Z');
    expect(progress).toEqual([0, 1, 2, 3]);
    expect(await listEntries(ALICE_A)).toEqual([]);
  });

  it('treats a replay 200 (the first answer got lost) as success', async () => {
    useCareEvents(() => HttpResponse.json({ key: 'ce_stored', category: 'note' }, { status: 200 }));
    await capture(ALICE_A);
    expect(await syncQueue({ scope: ALICE_A, now: () => T0 })).toMatchObject({ sent: 1 });
    expect(await listEntries(ALICE_A)).toEqual([]);
  });

  it('resends exactly the same id after a lost answer — never a new one', async () => {
    const bodies = useCareEvents((call) =>
      call === 1 ? HttpResponse.error() : HttpResponse.json({ key: 'ce_1', category: 'note' }, { status: 200 }),
    );
    const entry = await capture(ALICE_A);
    const firstRun = await syncQueue({ scope: ALICE_A, now: () => T0 });
    expect(firstRun).toMatchObject({ sent: 0, nextRetryAt: T0 + 1000 });
    expect(await statusOf(entry)).toMatchObject({ status: 'pending', attempts: 1, lastErrorCode: 'network' });

    await syncQueue({ scope: ALICE_A, now: () => T0 + 1000 });
    expect(bodies).toHaveLength(2);
    expect(bodies[0].client_event_id).toBe(entry.id);
    expect(bodies[1].client_event_id).toBe(entry.id);
    expect(bodies[1]).toEqual(bodies[0]);
    expect(await listEntries(ALICE_A)).toEqual([]);
  });

  it('completes a task with the id in the body and a photo of the bed in two steps with the id as a form field', async () => {
    const seen: { path: string; id: unknown }[] = [];
    server.use(
      http.post(`${BASE}/tasks/:key/complete`, async ({ request, params }) => {
        seen.push({ path: `tasks/${String(params.key)}`, id: ((await request.json()) as Record<string, unknown>).client_event_id });
        return HttpResponse.json({ key: params.key, status: 'completed' });
      }),
      http.post(`${BASE}/attachments`, async ({ request }) => {
        const form = formFields(await request.text());
        seen.push({ path: `attachments:${form.category}`, id: form.client_event_id });
        return HttpResponse.json({ attachment_id: 'att_1' }, { status: 201 });
      }),
      http.post(`${BASE}/locations/:key/photos`, async ({ request, params }) => {
        seen.push({ path: `locations/${String(params.key)}/photos`, id: ((await request.json()) as Record<string, unknown>).attachment_id });
        return HttpResponse.json({ location_key: params.key, cover_photo_ref: 'att_1', photos: [], max_photos: 50 });
      }),
    );
    const done = await capture(ALICE_A, completeWrite('t_water'));
    const photo = await capture(ALICE_A, {
      kind: 'bedPhoto',
      locationKey: 'loc_a',
      photo: { bytes: new Uint8Array([1, 2, 3]).buffer, type: 'image/jpeg', name: 'bed.jpg' },
    });
    await syncQueue({ scope: ALICE_A, now: () => T0 });
    expect(seen).toEqual([
      { path: 'tasks/t_water', id: done.id },
      { path: 'attachments:location', id: photo.id },
      { path: 'locations/loc_a/photos', id: 'att_1' },
    ]);
  });
});

describe('backoff and failed (R-026/R-027)', () => {
  it('waits 1 s, 2 s, 4 s, 8 s between attempts and marks the entry failed after the fifth', async () => {
    const send = vi.fn(async () => {
      throw new AxiosError('Network Error', 'ERR_NETWORK');
    });
    const entry = await capture(ALICE_A);
    let now = T0;
    const waits: number[] = [];
    for (let attempt = 1; attempt < MAX_ATTEMPTS; attempt += 1) {
      const result = await syncQueue({ scope: ALICE_A, now: () => now, send });
      waits.push((result.nextRetryAt ?? now) - now);
      // Too early: the head waits, nothing is sent.
      await syncQueue({ scope: ALICE_A, now: () => now + 1, send });
      now = result.nextRetryAt ?? now;
    }
    expect(waits).toEqual([1000, 2000, 4000, 8000]);
    expect(send).toHaveBeenCalledTimes(MAX_ATTEMPTS - 1);
    const last = await syncQueue({ scope: ALICE_A, now: () => now, send });
    expect(last).toMatchObject({ failed: 1, nextRetryAt: null });
    expect(await statusOf(entry)).toMatchObject({ status: 'failed', attempts: MAX_ATTEMPTS, lastErrorCode: 'network' });
    expect(send).toHaveBeenCalledTimes(MAX_ATTEMPTS);
  });

  it('holds back every later entry while the head waits (FIFO), and moves on past a failed one', async () => {
    const order: string[] = [];
    let failHead = true;
    const send = vi.fn(async (entry: QueueEntry) => {
      const summary = entry.write.kind === 'note' ? entry.write.body.summary : '';
      order.push(summary);
      if (summary === 'head' && failHead) throw new AxiosError('Network Error', 'ERR_NETWORK');
    });
    await capture(ALICE_A, noteWrite('head'));
    await capture(ALICE_A, noteWrite('tail'));
    await syncQueue({ scope: ALICE_A, now: () => T0, send });
    expect(order).toEqual(['head']);
    await syncQueue({ scope: ALICE_A, now: () => T0 + 500, send });
    expect(order).toEqual(['head']);
    failHead = false;
    await syncQueue({ scope: ALICE_A, now: () => T0 + 1000, send });
    expect(order).toEqual(['head', 'head', 'tail']);

    // A failed head no longer blocks: the run goes on to the next entry.
    order.length = 0;
    const blocked = await capture(ALICE_A, noteWrite('head'));
    await updateEntry(ALICE_A, blocked.seq!, { status: 'failed', attempts: MAX_ATTEMPTS });
    await capture(ALICE_A, noteWrite('after'));
    await syncQueue({ scope: ALICE_A, now: () => T0, send });
    expect(order).toEqual(['after']);
  });

  it.each([
    [500, 'INTERNAL_ERROR'],
    [503, 'SERVICE_UNAVAILABLE'],
    [429, 'RATE_LIMITED'],
    [409, 'WRITE_CONFLICT'],
  ])('retries a %i %s after the backoff', async (status, code) => {
    useCareEvents(() => envelope(code, status));
    const entry = await capture(ALICE_A);
    await syncQueue({ scope: ALICE_A, now: () => T0 });
    expect(await statusOf(entry)).toMatchObject({ status: 'pending', attempts: 1, nextAttemptAt: T0 + 1000 });
  });

  it('marks a refusal that resending cannot change (422) failed at once, with the error code only', async () => {
    useCareEvents(() => envelope('VALIDATION_ERROR', 422));
    const entry = await capture(ALICE_A);
    expect(await syncQueue({ scope: ALICE_A, now: () => T0 })).toMatchObject({ failed: 1 });
    expect(await statusOf(entry)).toMatchObject({ status: 'failed', attempts: 0, lastErrorCode: 'VALIDATION_ERROR' });
  });

  it('stops on a 401 without counting an attempt', async () => {
    const send = vi.fn(async () => {
      throw apiError(401, 'UNAUTHORIZED');
    });
    const entry = await capture(ALICE_A);
    await capture(ALICE_A, noteWrite('later'));
    await syncQueue({ scope: ALICE_A, now: () => T0, send });
    expect(send).toHaveBeenCalledTimes(1);
    expect(await statusOf(entry)).toMatchObject({ status: 'pending', attempts: 0 });
  });
});

describe('conflicts (R-028, WP 9.3)', () => {
  const CASES: [ConflictCode, number][] = [
    ['client_event.payload_mismatch', 409],
    ['task.already_closed', 409],
    ['task.missing', 404],
    ['client_event.deleted', 404],
  ];

  it.each(CASES)('marks %s (%i) a conflict and goes on with the next entry', async (code, status) => {
    const bodies = useCareEvents((call) =>
      call === 1 ? envelope(code, status) : HttpResponse.json({ key: 'ce_2', category: 'note' }, { status: 201 }),
    );
    const entry = await capture(ALICE_A);
    await capture(ALICE_A, noteWrite('next'));
    const result = await syncQueue({ scope: ALICE_A, now: () => T0 });
    expect(result).toMatchObject({ sent: 1, conflicts: 1 });
    expect(bodies).toHaveLength(2);
    const rows = await listEntries(ALICE_A);
    expect(rows).toHaveLength(1);
    expect(rows[0]).toMatchObject({ id: entry.id, status: 'conflict', conflictCode: code, kept: false });
    // A conflict is never resent.
    await syncQueue({ scope: ALICE_A, now: () => T0 + 60_000 });
    expect(bodies).toHaveLength(2);
  });
});

describe('owner scope and stale claims (G-W9 a)', () => {
  it('sends only the entries of its own scope', async () => {
    const bodies = useCareEvents();
    await capture(BOB_A, noteWrite('bob'));
    await capture(ALICE_A, noteWrite('alice'));
    await syncQueue({ scope: ALICE_A, now: () => T0 });
    expect(bodies.map((body) => body.summary)).toEqual(['alice']);
    expect(await listEntries(BOB_A)).toHaveLength(1);
  });

  it('stops as soon as the active user or tenant is another one', async () => {
    let scope: typeof ALICE_A | null = ALICE_A;
    const send = vi.fn(async () => {
      scope = null; // signed out while the first request was on its way
    });
    await capture(ALICE_A, noteWrite('one'));
    await capture(ALICE_A, noteWrite('two'));
    await syncQueue({ scope: ALICE_A, currentScope: () => scope, now: () => T0, send });
    expect(send).toHaveBeenCalledTimes(1);
  });

  it('sends nothing while the browser is offline', async () => {
    const send = vi.fn(async () => undefined);
    await capture(ALICE_A);
    expect(await syncQueue({ scope: ALICE_A, online: () => false, send })).toMatchObject({ skipped: true });
    expect(send).not.toHaveBeenCalled();
  });

  it('takes back a syncing claim of a run that died, and resends it with the same id', async () => {
    const send = vi.fn(async (_entry: QueueEntry) => undefined);
    const entry = await capture(ALICE_A);
    await updateEntry(ALICE_A, entry.seq!, { status: 'syncing', syncingSince: T0 });
    await syncQueue({ scope: ALICE_A, now: () => T0 + 1000, send });
    expect(send).not.toHaveBeenCalled(); // a fresh claim: another tab may be sending it
    await syncQueue({ scope: ALICE_A, now: () => T0 + SYNC_STALE_MS + 1, send });
    expect(send).toHaveBeenCalledTimes(1);
    expect(send.mock.calls[0][0].id).toBe(entry.id);
  });
});

describe('classifySendError', () => {
  it('reads codes and statuses', () => {
    expect(classifySendError(apiError(409, 'task.already_closed'))).toEqual({ kind: 'conflict', code: 'task.already_closed' });
    expect(classifySendError(apiError(404, 'ENTITY_NOT_FOUND'))).toEqual({ kind: 'refused', code: 'ENTITY_NOT_FOUND' });
    expect(classifySendError(apiError(403, 'FORBIDDEN'))).toEqual({ kind: 'refused', code: 'FORBIDDEN' });
    expect(classifySendError(apiError(502, 'BAD_GATEWAY'))).toEqual({ kind: 'retry', code: 'BAD_GATEWAY' });
    expect(classifySendError(new AxiosError('Network Error', 'ERR_NETWORK'))).toEqual({ kind: 'retry', code: 'network' });
    expect(classifySendError(new AxiosError('canceled', 'ERR_CANCELED'))).toEqual({ kind: 'stop' });
    expect(classifySendError(new Error('boom'))).toEqual({ kind: 'refused', code: 'client' });
  });
});

describe('createSyncScheduler', () => {
  const RESULT: SyncResult = { sent: 0, conflicts: 0, failed: 0, nextRetryAt: null, skipped: false };

  it('runs once more when asked during a run, and never two runs at a time', async () => {
    let release: () => void = () => undefined;
    let active = 0;
    let maxActive = 0;
    const run = vi.fn(async () => {
      active += 1;
      maxActive = Math.max(maxActive, active);
      await new Promise<void>((resolve) => {
        release = resolve;
      });
      active -= 1;
      return RESULT;
    });
    const scheduler = createSyncScheduler({ getScope: () => ALICE_A, run });
    const first = scheduler.request();
    void scheduler.request();
    void scheduler.request();
    await vi.waitFor(() => expect(run).toHaveBeenCalledTimes(1));
    release();
    await vi.waitFor(() => expect(run).toHaveBeenCalledTimes(2));
    release();
    await first;
    expect(maxActive).toBe(1);
    scheduler.dispose();
  });

  it('comes back for the head of the queue when its backoff is over', async () => {
    vi.useFakeTimers();
    vi.setSystemTime(T0);
    const run = vi
      .fn<() => Promise<SyncResult>>()
      .mockResolvedValueOnce({ ...RESULT, nextRetryAt: T0 + 4000 })
      .mockResolvedValue(RESULT);
    const scheduler = createSyncScheduler({ getScope: () => ALICE_A, run });
    await scheduler.request();
    expect(run).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(3999);
    expect(run).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(1);
    expect(run).toHaveBeenCalledTimes(2);
    scheduler.dispose();
  });

  it('does nothing without a scope', async () => {
    const run = vi.fn(async () => RESULT);
    const scheduler = createSyncScheduler({ getScope: () => null, run });
    await scheduler.request();
    expect(run).not.toHaveBeenCalled();
  });
});

describe('one sender (review 1-3, 8)', () => {
  const RESULT: SyncResult = { sent: 0, conflicts: 0, failed: 0, nextRetryAt: null, skipped: false };

  it("the logout dialog's sync waits for the app bar's run and never resends what that run is sending", async () => {
    let release: () => void = () => undefined;
    let held = false;
    // The host's first request hangs (a slow upload); every later one answers at once.
    const hostSend = vi.fn(() => {
      if (held) return Promise.resolve();
      held = true;
      return new Promise<void>((resolve) => {
        release = resolve;
      });
    });
    const dialogSend = vi.fn(async () => undefined);
    const entry = await capture(ALICE_A);
    const second = await capture(ALICE_A, noteWrite('second'));
    // Long after the claim: a run that did not know about the live one would take it back as stale.
    const late = () => Date.now() + SYNC_STALE_MS * 2;
    const scheduler = createSyncScheduler({ getScope: () => ALICE_A, run: (options) => syncQueue({ ...options, send: hostSend }) });
    const hostRun = scheduler.request();
    await vi.waitFor(() => expect(hostSend).toHaveBeenCalledTimes(1));
    const { syncThenCount } = await import('./sessionChange');
    const dialogRun = syncThenCount('alice', ALICE_A, undefined, { now: late, send: dialogSend });
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(dialogSend).not.toHaveBeenCalled();
    release();
    await hostRun;
    await dialogRun;
    expect(dialogSend).not.toHaveBeenCalled(); // the host's run sent both; nothing was left
    expect(hostSend).toHaveBeenCalledTimes(2);
    expect(await statusOf(entry)).toBeUndefined();
    expect(await statusOf(second)).toBeUndefined();
    scheduler.dispose();
  });

  it('a stale-claim reset never takes back an entry a live run of this tab is sending', async () => {
    let release: () => void = () => undefined;
    const first = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          release = resolve;
        }),
    );
    const second = vi.fn(async () => undefined);
    await capture(ALICE_A);
    const running = syncQueue({ scope: ALICE_A, send: first });
    await vi.waitFor(() => expect(first).toHaveBeenCalledTimes(1));
    // Bypassing the run queue on purpose, holding "the lock": every syncing claim would count as stale.
    await syncQueue({ scope: ALICE_A, send: second, ownsLock: true });
    expect(second).not.toHaveBeenCalled();
    release();
    await running;
  });

  it('withSyncLock never reruns a task that failed inside the lock; it runs unlocked only when the lock API refuses', async () => {
    const task = vi.fn(async () => {
      throw new Error('task failed');
    });
    vi.stubGlobal('navigator', Object.assign(Object.create(navigator), {
      locks: { request: (_name: string, _options: unknown, callback: (lock: unknown) => Promise<SyncResult>) => callback({}) },
    }));
    await expect(withSyncLock(task)).rejects.toThrow('task failed');
    expect(task).toHaveBeenCalledTimes(1);

    const plain = vi.fn(async () => RESULT);
    vi.stubGlobal('navigator', Object.assign(Object.create(navigator), {
      locks: {
        request: () => {
          throw new DOMException('denied', 'SecurityError');
        },
      },
    }));
    await expect(withSyncLock(plain)).resolves.toBe(RESULT);
    expect(plain).toHaveBeenCalledWith(false);
    vi.unstubAllGlobals();
  });

  it('a scheduler disposed mid-run reports onDispose once and drops every later progress', async () => {
    let release: () => void = () => undefined;
    const onProgress = vi.fn();
    const onFinish = vi.fn();
    const onDispose = vi.fn();
    const run = vi.fn(async (options: { onProgress?: (value: { done: number; total: number }) => void }) => {
      options.onProgress?.({ done: 0, total: 3 });
      await new Promise<void>((resolve) => {
        release = resolve;
      });
      options.onProgress?.({ done: 1, total: 3 });
      return RESULT;
    });
    const scheduler = createSyncScheduler({ getScope: () => ALICE_A, run, onProgress, onFinish, onDispose });
    const pending = scheduler.request();
    await vi.waitFor(() => expect(onProgress).toHaveBeenCalledTimes(1));
    scheduler.dispose();
    scheduler.dispose();
    release();
    await pending;
    expect(onDispose).toHaveBeenCalledTimes(1);
    expect(onProgress).toHaveBeenCalledTimes(1);
    expect(onFinish).not.toHaveBeenCalled();
  });

  it('removeEntry writes nothing once a clearing started since its generation', async () => {
    const entry = await capture(ALICE_A);
    const stale = (queueGeneration() ?? 0) - 1;
    expect(await removeEntry(ALICE_A, entry.seq!, { generation: stale })).toBe(false);
    expect(await statusOf(entry)).toBeDefined();
  });
});

describe('the logout wait is bounded (review 2)', () => {
  it('gives up waiting for the lock when the signal ends — nothing is sent', async () => {
    const task = vi.fn(async () => ({ sent: 1, conflicts: 0, failed: 0, nextRetryAt: null, skipped: false }));
    vi.stubGlobal('navigator', Object.assign(Object.create(navigator), {
      locks: {
        // Another tab holds the lock: the request waits until its signal aborts.
        request: (_name: string, options: { signal?: AbortSignal }) =>
          new Promise((_resolve, reject) => {
            options.signal?.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')));
          }),
      },
    }));
    const controller = new AbortController();
    const waiting = withSyncLock(task, true, controller.signal);
    controller.abort();
    await expect(waiting).resolves.toMatchObject({ skipped: true });
    expect(task).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it.each(['the wait limit', 'a cancel'])('the dialog only counts once %s ends the wait for a hanging app-bar run', async (how) => {
    const { syncThenCount, LOGOUT_SYNC_WAIT_MS } = await import('./sessionChange');
    expect(LOGOUT_SYNC_WAIT_MS).toBe(30_000);
    let release: () => void = () => undefined;
    const hang = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          release = resolve;
        }),
    );
    await capture(ALICE_A);
    const scheduler = createSyncScheduler({ getScope: () => ALICE_A, run: (options) => syncQueue({ ...options, send: hang }) });
    void scheduler.request();
    await vi.waitFor(() => expect(hang).toHaveBeenCalledTimes(1));
    const controller = new AbortController();
    const counted = syncThenCount('alice', ALICE_A, undefined, { waitMs: how === 'a cancel' ? 60_000 : 50 }, controller.signal);
    if (how === 'a cancel') controller.abort();
    await expect(counted).resolves.toBe(1); // counted, nothing discarded, the buttons are free
    release();
    scheduler.dispose();
  });

  it('sends with a per-request timeout: 30 s for JSON, 120 s for a photo', async () => {
    const { tenantClient } = await import('@/api/client');
    const { SEND_TIMEOUT_MS, PHOTO_SEND_TIMEOUT_MS, sendEntry } = await import('./sync');
    const post = vi.spyOn(tenantClient, 'post').mockResolvedValue({ data: { attachment_id: 'a' } });
    try {
      const note = await capture(ALICE_A);
      await sendEntry(note);
      expect(post.mock.calls[0][2]).toMatchObject({ timeout: SEND_TIMEOUT_MS });
      const photo = await capture(ALICE_A, {
        kind: 'plantPhoto',
        plantKey: 'pl_1',
        plantName: 'PL',
        photo: { bytes: new Uint8Array([1]).buffer, type: 'image/jpeg', name: 'photo.jpg' },
      });
      await sendEntry(photo);
      expect(post.mock.calls[1][2]).toMatchObject({ timeout: PHOTO_SEND_TIMEOUT_MS });
      expect([SEND_TIMEOUT_MS, PHOTO_SEND_TIMEOUT_MS]).toEqual([30_000, 120_000]);
    } finally {
      post.mockRestore();
    }
  });
});
