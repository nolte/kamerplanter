import { act, renderHook, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { smallPlan } from '@/test/gardenPlanFixtures';
import { server } from '@/test/mocks/server';
import type { PlanModel } from '../model/planModel';
import type { PlanUnderlay } from '../model/types';
import { useUnderlay } from './useUnderlay';

/** The underlay hook (REQ-053 GP-FR-033, WP 7.15): the picture follows the layer switch and leaks no object URL. */
const UNDERLAY: PlanUnderlay = {
  attachment_key: 'att_1',
  calibration: { p1_px: [0, 0], p2_px: [400, 0], distance_m: 4 },
  origin: [0, 5],
  rotation_deg: 0,
  opacity: 0.5,
};

function planWith(underlay: PlanUnderlay | null): PlanModel {
  const plan = smallPlan({ locations: [], garden_objects: [], slots: [], plants: [] });
  return { ...plan, settings: { ...(plan.settings as NonNullable<PlanModel['settings']>), underlay } };
}

let created: string[] = [];
let revoked: string[] = [];

beforeEach(() => {
  created = [];
  revoked = [];
  vi.spyOn(URL, 'createObjectURL').mockImplementation(() => {
    const url = `blob:test/${created.length}`;
    created.push(url);
    return url;
  });
  vi.spyOn(URL, 'revokeObjectURL').mockImplementation((url) => {
    revoked.push(url);
  });
  // jsdom never decodes an image: report a size the way the browser's `load` would.
  vi.stubGlobal(
    'Image',
    class {
      naturalWidth = 800;
      naturalHeight = 400;
      onload: (() => void) | null = null;
      onerror: (() => void) | null = null;
      set src(_value: string) {
        queueMicrotask(() => this.onload?.());
      }
    },
  );
  server.use(
    http.get('/api/v1/t/:tenant/attachments/att_1', () => new HttpResponse(new Blob(['x']), { status: 200 })),
  );
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe('useUnderlay', () => {
  it('loads nothing while the layer is hidden', async () => {
    const { result } = renderHook(() => useUnderlay(planWith(UNDERLAY), false));
    expect(result.current.underlay).toEqual(UNDERLAY);
    expect(result.current.entry).toBeUndefined();
    expect(created).toEqual([]);
  });

  it('draws a fresh picture after hide and show, never the revoked URL', async () => {
    const plan = planWith(UNDERLAY);
    const { result, rerender } = renderHook(({ visible }) => useUnderlay(plan, visible), {
      initialProps: { visible: true },
    });
    await waitFor(() => expect(result.current.entry?.href).toBe('blob:test/0'));

    rerender({ visible: false });
    expect(result.current.entry).toBeUndefined();
    expect(revoked).toContain('blob:test/0');

    rerender({ visible: true });
    await waitFor(() => expect(result.current.entry?.href).toBe('blob:test/1'));
  });

  it('creates no URL for a request that was given up before its answer', async () => {
    const plan = planWith(UNDERLAY);
    const { rerender } = renderHook(({ visible }) => useUnderlay(plan, visible), {
      initialProps: { visible: true },
    });
    rerender({ visible: false });
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
    });

    expect(created.length).toBe(revoked.length);
  });

  it('gives the URL of a picture that cannot be decoded back at once, while the layer stays on', async () => {
    vi.stubGlobal(
      'Image',
      class {
        onload: (() => void) | null = null;
        onerror: (() => void) | null = null;
        set src(_value: string) {
          queueMicrotask(() => this.onerror?.());
        }
      },
    );
    const plan = planWith(UNDERLAY);
    const { result } = renderHook(() => useUnderlay(plan, true));

    // No hide, no other picture: the effect cleanup does not run, so only the failure path can revoke it.
    await waitFor(() => expect(created).toEqual(['blob:test/0']));
    await waitFor(() => expect(revoked).toEqual(['blob:test/0']));
    expect(result.current.entry).toBeUndefined();
  });

  it('revokes a failed picture once, also when the layer is hidden afterwards', async () => {
    vi.stubGlobal(
      'Image',
      class {
        onload: (() => void) | null = null;
        onerror: (() => void) | null = null;
        set src(_value: string) {
          queueMicrotask(() => this.onerror?.());
        }
      },
    );
    const plan = planWith(UNDERLAY);
    const { rerender } = renderHook(({ visible }) => useUnderlay(plan, visible), {
      initialProps: { visible: true },
    });
    await waitFor(() => expect(revoked).toEqual(['blob:test/0']));
    rerender({ visible: false });

    expect(revoked).toEqual(['blob:test/0']);
  });

  it('takes a saved or removed underlay over the stored one until the plan reloads', () => {
    const { result } = renderHook(() => useUnderlay(planWith(UNDERLAY), false));
    act(() => result.current.set(null));
    expect(result.current.underlay).toBeNull();
  });
});
