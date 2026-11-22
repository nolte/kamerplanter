/**
 * The live preview (REQ-053 GP-FR-063): the port answers at once, the server's answer replaces it after a
 * debounce and wins where it differs. The debounce is pinned on fake timers - no retry loop, no real wait.
 */
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { EntryLayout } from '../model/layout';
import * as api from './plantingApi';
import { BED_GEOMETRY } from './plantingTestKit';
import type { PreviewResponse } from './plantingTypes';
import { PREVIEW_DEBOUNCE_MS, useEntryPreviews, type PreviewRequest } from './useEntryPreviews';

vi.mock('./plantingApi');

const ROWS: EntryLayout = { layout_strategy: 'rows', spacing_cm: 30, row_spacing_cm: 40 };

function serverAnswer(count: number): PreviewResponse {
  return {
    slots: Array.from({ length: count }, (_, index) => ({
      slot_role: 'position' as const,
      geometry: { kind: 'point' as const, origin: [0.1 * (index + 1), 0.1] as [number, number] },
      row_index: 0,
      sequence: index + 1,
      capacity_plants: 1,
    })),
    count,
    capacity_max: count + 5,
    warnings: [],
  };
}

function render(initial: PreviewRequest[]) {
  return renderHook(({ requests }) => useEntryPreviews('loc_b03', BED_GEOMETRY, requests), {
    initialProps: { requests: initial },
  });
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.mocked(api.previewLayout).mockReset();
});

afterEach(() => {
  vi.useRealTimers();
});

describe('useEntryPreviews', () => {
  it('shows the port at once and asks the server only after the debounce', async () => {
    vi.mocked(api.previewLayout).mockResolvedValue(serverAnswer(3));
    const { result } = render([{ id: 'e1', layout: ROWS, maxCount: null }]);

    expect(result.current.e1.source).toBe('local');
    expect(result.current.e1.pending).toBe(true);
    expect(result.current.e1.count).toBeGreaterThan(0);
    expect(api.previewLayout).not.toHaveBeenCalled();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(PREVIEW_DEBOUNCE_MS - 1);
    });
    expect(api.previewLayout).not.toHaveBeenCalled();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(api.previewLayout).toHaveBeenCalledTimes(1);
  });

  it('lets the server win where it differs from the port (GP-FR-063)', async () => {
    vi.mocked(api.previewLayout).mockResolvedValue(serverAnswer(3));
    const { result } = render([{ id: 'e1', layout: ROWS, maxCount: null }]);
    const localCount = result.current.e1.count;
    expect(localCount).not.toBe(3);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(PREVIEW_DEBOUNCE_MS);
    });

    expect(result.current.e1).toMatchObject({ source: 'server', pending: false, count: 3, capacityMax: 8 });
  });

  it('restarts the debounce while the input keeps changing: one request for the last value', async () => {
    vi.mocked(api.previewLayout).mockResolvedValue(serverAnswer(2));
    const { result, rerender } = render([{ id: 'e1', layout: { ...ROWS, spacing_cm: 30 }, maxCount: null }]);

    for (const spacing of [31, 32, 33]) {
      await act(async () => {
        await vi.advanceTimersByTimeAsync(PREVIEW_DEBOUNCE_MS - 50);
      });
      rerender({ requests: [{ id: 'e1', layout: { ...ROWS, spacing_cm: spacing }, maxCount: null }] });
    }
    expect(api.previewLayout).not.toHaveBeenCalled();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(PREVIEW_DEBOUNCE_MS);
    });
    expect(api.previewLayout).toHaveBeenCalledTimes(1);
    expect(vi.mocked(api.previewLayout).mock.calls[0][1]).toMatchObject({ spacing_cm: 33 });
    expect(result.current.e1.source).toBe('server');
  });

  it('shows the port again for a changed input until the server has answered that one', async () => {
    vi.mocked(api.previewLayout).mockResolvedValue(serverAnswer(3));
    const { result, rerender } = render([{ id: 'e1', layout: ROWS, maxCount: null }]);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(PREVIEW_DEBOUNCE_MS);
    });
    expect(result.current.e1.source).toBe('server');

    rerender({ requests: [{ id: 'e1', layout: { ...ROWS, spacing_cm: 20 }, maxCount: null }] });

    expect(result.current.e1).toMatchObject({ source: 'local', pending: true });
  });

  it('does not ask again for a rerender with the same content', async () => {
    vi.mocked(api.previewLayout).mockResolvedValue(serverAnswer(3));
    const { rerender } = render([{ id: 'e1', layout: ROWS, maxCount: null }]);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(PREVIEW_DEBOUNCE_MS);
    });
    rerender({ requests: [{ id: 'e1', layout: { ...ROWS }, maxCount: null }] });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(PREVIEW_DEBOUNCE_MS * 3);
    });
    expect(api.previewLayout).toHaveBeenCalledTimes(1);
  });

  it('asks again only for the entry that changed, not for the ones that rest', async () => {
    vi.mocked(api.previewLayout).mockResolvedValue(serverAnswer(2));
    const second: EntryLayout = { layout_strategy: 'grid', spacing_cm: 40 };
    const { rerender } = render([
      { id: 'e1', layout: ROWS, maxCount: null },
      { id: 'e2', layout: second, maxCount: null },
    ]);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(PREVIEW_DEBOUNCE_MS);
    });
    expect(api.previewLayout).toHaveBeenCalledTimes(2);

    rerender({
      requests: [
        { id: 'e1', layout: { ...ROWS, spacing_cm: 35 }, maxCount: null },
        { id: 'e2', layout: { ...second }, maxCount: null },
      ],
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(PREVIEW_DEBOUNCE_MS);
    });

    expect(api.previewLayout).toHaveBeenCalledTimes(3);
    expect(vi.mocked(api.previewLayout).mock.calls[2][1]).toMatchObject({ spacing_cm: 35 });
  });

  it('reports a refusal of the port as a result and never calls the server for it', async () => {
    const outOfRange: EntryLayout = { layout_strategy: 'grid', spacing_cm: 2 };
    const { result } = render([{ id: 'e1', layout: outOfRange, maxCount: null }]);

    expect(result.current.e1.error).toMatchObject({ code: 'layout.spacing_out_of_range' });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(PREVIEW_DEBOUNCE_MS * 2);
    });
    expect(api.previewLayout).not.toHaveBeenCalled();
  });

  it('keeps the port result and says so when the server cannot be reached', async () => {
    vi.mocked(api.previewLayout).mockRejectedValue(new Error('offline'));
    const { result } = render([{ id: 'e1', layout: ROWS, maxCount: null }]);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(PREVIEW_DEBOUNCE_MS);
    });
    expect(result.current.e1.error?.message).toBeTruthy();
    expect(result.current.e1.count).toBeGreaterThan(0);
    expect(result.current.e1.pending).toBe(false);
  });

  it('computes nothing for an entry without a layout (free positions, spacing missing)', () => {
    const { result } = render([{ id: 'e1', layout: null, maxCount: null }]);
    expect(result.current.e1).toMatchObject({ count: 0, positions: [], pending: false, error: null });
    expect(api.previewLayout).not.toHaveBeenCalled();
  });
});
