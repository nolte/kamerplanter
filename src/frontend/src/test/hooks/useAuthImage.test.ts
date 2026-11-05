import { renderHook, act, cleanup } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { AxiosResponse } from 'axios';
import client from '@/api/client';
import { RENDITION_RETRY_DELAYS_MS, useAuthImage } from '@/hooks/useAuthImage';

const URI = '/api/v1/t/test-tenant/attachments/abc/thumbnails/512';

/** A pending rendition: `202 Accepted` with an empty body. */
function accepted(): AxiosResponse<ArrayBuffer> {
  return { status: 202, data: new ArrayBuffer(0), headers: {}, statusText: 'Accepted', config: {} as never };
}

function image(): AxiosResponse<ArrayBuffer> {
  return {
    status: 200,
    data: new Uint8Array([1, 2, 3]).buffer,
    headers: { 'content-type': 'image/jpeg' },
    statusText: 'OK',
    config: {} as never,
  };
}

/** Let the resolved axios promise and its `.then` run without advancing the clock. */
async function flush(): Promise<void> {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

async function advance(ms: number): Promise<void> {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

describe('useAuthImage — a rendition still being generated (202)', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('stays loading on 202 and loads once the retry answers 200', async () => {
    const get = vi.spyOn(client, 'get').mockResolvedValueOnce(accepted()).mockResolvedValueOnce(image());

    const { result } = renderHook(() => useAuthImage(URI));
    await flush();

    expect(get).toHaveBeenCalledTimes(1);
    expect(result.current.status).toBe('loading');
    expect(result.current.objectUrl).toBeNull();

    await advance(RENDITION_RETRY_DELAYS_MS[0]);

    expect(get).toHaveBeenCalledTimes(2);
    expect(result.current.status).toBe('loaded');
    expect(result.current.objectUrl).toMatch(/^blob:/);
  });

  it('ends in error when the rendition is still pending after the last retry', async () => {
    const get = vi.spyOn(client, 'get').mockResolvedValue(accepted());

    const { result } = renderHook(() => useAuthImage(URI));
    await flush();
    for (const delay of RENDITION_RETRY_DELAYS_MS) {
      expect(result.current.status).toBe('loading');
      await advance(delay);
    }

    expect(result.current.status).toBe('error');
    expect(result.current.objectUrl).toBeNull();
    // The first request plus one per retry delay, and nothing after the cap.
    expect(get).toHaveBeenCalledTimes(RENDITION_RETRY_DELAYS_MS.length + 1);
    await advance(60_000);
    expect(get).toHaveBeenCalledTimes(RENDITION_RETRY_DELAYS_MS.length + 1);
  });

  it('issues no request after unmount during a pending retry', async () => {
    const get = vi.spyOn(client, 'get').mockResolvedValue(accepted());

    const { unmount } = renderHook(() => useAuthImage(URI));
    await flush();
    expect(get).toHaveBeenCalledTimes(1);

    unmount();
    await advance(60_000);

    expect(get).toHaveBeenCalledTimes(1);
  });

  it('cancels the pending retry of the previous uri when the uri changes', async () => {
    const other = '/api/v1/t/test-tenant/attachments/def/thumbnails/512';
    const get = vi.spyOn(client, 'get').mockResolvedValueOnce(accepted()).mockResolvedValue(image());

    const { result, rerender } = renderHook(({ uri }) => useAuthImage(uri), { initialProps: { uri: URI } });
    await flush();
    rerender({ uri: other });
    await flush();
    expect(result.current.status).toBe('loaded');

    await advance(60_000);

    expect(get.mock.calls.map(([url]) => url)).toEqual([
      '/t/test-tenant/attachments/abc/thumbnails/512',
      '/t/test-tenant/attachments/def/thumbnails/512',
    ]);
  });
});
