import 'fake-indexeddb/auto';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ALICE_A, emptyWriteQueue, noteWrite } from '@/test/writeQueueTestKit';

/**
 * #2755: the first offline capture of a device that never buffered anything. Offline, a lazy chunk that was never
 * loaded cannot be fetched — modelled here by a `./queueDb` import that rejects. Loaded ahead (`preloadWriteQueue`
 * through `preloadOfflineCapture`), the capture works anyway; without the preload it fails as "buffer unavailable".
 */

afterEach(() => {
  vi.doUnmock('./queueDb');
  vi.resetModules();
});

/** A fresh `queue` module (nothing loaded yet) and, after `preload`, a `./queueDb` that can no longer be fetched. */
async function captureWithChunkGone(preload: boolean) {
  await emptyWriteQueue();
  vi.resetModules();
  const queue = await import('./queue');
  if (preload) {
    const { preloadOfflineCapture } = await import('./preloadOfflineCapture');
    expect(await preloadOfflineCapture()).toBe(true);
  }
  vi.doMock('./queueDb', () => {
    throw new Error('Failed to fetch dynamically imported module (offline)');
  });
  return queue.enqueue({ scope: ALICE_A, bedKey: 'loc_a', bedName: 'Raised bed 1', write: noteWrite() });
}

describe('preloadOfflineCapture', () => {
  it('lets the first offline capture work although the chunk can no longer be fetched', async () => {
    const entry = await captureWithChunkGone(true);
    expect(entry.status).toBe('pending');
    expect(entry.write.kind).toBe('note');
  });

  it('the same capture without the preload fails: the model of the defect holds', async () => {
    await expect(captureWithChunkGone(false)).rejects.toThrow('offline_queue.unavailable');
  });

  it('loads nothing and reports false with PWA_CACHING_ENABLED=false', async () => {
    vi.resetModules();
    (window as { __RUNTIME_CONFIG__?: unknown }).__RUNTIME_CONFIG__ = { PWA_CACHING_ENABLED: 'false' };
    try {
      const { preloadOfflineCapture } = await import('./preloadOfflineCapture');
      expect(await preloadOfflineCapture()).toBe(false);
    } finally {
      delete (window as { __RUNTIME_CONFIG__?: unknown }).__RUNTIME_CONFIG__;
    }
  });
});
