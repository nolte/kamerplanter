import { useEffect, useState } from 'react';
import { describe, it, expect } from 'vitest';
import { act, screen, within } from '@testing-library/react';
import { axe } from 'vitest-axe';
import { renderWithProviders } from '../../helpers';
import { deFull, enFull } from '../../i18nTestResources';
import DashboardReadonlyGrid from '@/components/dashboard/DashboardReadonlyGrid';
import { DashboardDataProvider } from '@/components/dashboard/DashboardDataContext';
import type { DashboardLayout } from '@/api/types';

/**
 * Issue #1337 item 1 — one loading announcement for the whole dashboard.
 *
 * The five aggregated widgets each rendered their loading placeholder as
 * `<div aria-busy="true" aria-label="Wird geladen...">`. A `<div>` maps to
 * `generic`, ARIA prohibits naming a generic element, so the name was dropped
 * and nothing was announced (axe `aria-prohibited-attr`, serious).
 *
 * The fix #1329 applied elsewhere — a `role="status"` live region per
 * placeholder — is wrong *here*, and that is the whole reason this was split
 * out: mid-load the dashboard stands with five placeholders at once, which
 * would be five concurrent polite live regions all saying "loading". So the
 * announcement moves up to the grid: exactly one region, one message, and the
 * placeholders keep `aria-busy` on an unnamed container.
 *
 * These tests hold the widgets in the loading state (the aggregated payload
 * never resolves) rather than waiting for a settled DOM — a settled scan cannot
 * see this defect at all.
 */

/**
 * The announcement as it is rendered here. The test i18n resolves to EN, so the
 * DOM assertions below use the English wording; the DE/EN pair itself is
 * asserted against the locale resources in its own test, so a missing
 * translation cannot hide behind `t()` echoing the key back.
 */
const LOADING_MESSAGE = 'Dashboard is loading...';

/** The five widgets the issue measured standing at once, in one grid. */
const WIDGET_KEYS = [
  'tasks_today',
  'care_reminders',
  'active_plants_summary',
  'daily_tip',
  'onboarding_progress',
] as const;

const LAYOUT: DashboardLayout = {
  schema_version: 2,
  widgets: WIDGET_KEYS.map((key) => ({ instance_id: key, widget_key: key, config: {} })),
  placements: {
    lg: WIDGET_KEYS.map((key, i) => ({ instance_id: key, x: (i % 3) * 4, y: Math.floor(i / 3), w: 4, h: 3 })),
  },
};

/** Resolved payload for a widget that has finished; shape mirrors the real slice. */
const SETTLED_PAYLOADS: Record<string, unknown> = Object.fromEntries(
  WIDGET_KEYS.map((key) => [key, { count: 3 }]),
);

interface Controls {
  setLoading: (v: boolean) => void;
  setPayloads: (p: Record<string, unknown>) => void;
}

const controls: Controls = { setLoading: () => {}, setPayloads: () => {} };

/**
 * Drives the same `DashboardDataContext` the widgets read, so loading is never
 * simulated at two different places — the grid and its widgets see one state.
 */
function Harness() {
  const [loading, setLoading] = useState(true);
  const [payloads, setPayloads] = useState<Record<string, unknown>>({});
  // Published from an effect, not during render: React's immutability lint rule
  // forbids writing to module scope in a render body (and a render write would
  // run twice under StrictMode).
  useEffect(() => {
    controls.setLoading = setLoading;
    controls.setPayloads = setPayloads;
  }, []);
  return (
    <DashboardDataProvider value={{ payloads, loading }}>
      <DashboardReadonlyGrid layout={LAYOUT} renderableKeys={() => true} />
    </DashboardDataProvider>
  );
}

/** Wait for all five lazily-imported widget bodies to have mounted. */
async function renderLoadingGrid() {
  const rendered = renderWithProviders(<Harness />);
  const placeholders = await screen.findAllByTestId(/^widget-.*-loading$/);
  expect(placeholders).toHaveLength(WIDGET_KEYS.length);
  return rendered;
}

/**
 * `aria-label` on an element that has no role of its own. `div`/`span` map to
 * `generic`, which ARIA prohibits naming, so the name is silently dropped —
 * this is the defect class, expressed directly on the DOM rather than only via
 * axe (axe sees it too, asserted separately below).
 */
function droppedNames(root: HTMLElement): string[] {
  return Array.from(root.querySelectorAll('[aria-label]:not([role])'))
    .filter((el) => el.tagName === 'DIV' || el.tagName === 'SPAN')
    .map((el) => el.outerHTML.slice(0, 200));
}

describe('dashboard loading announcement (#1337 item 1)', () => {
  it('announces once from the grid while five widgets load, not once per widget', async () => {
    const { container } = await renderLoadingGrid();

    const regions = within(container).getAllByRole('status');
    expect(
      regions.map((r) => r.outerHTML.slice(0, 160)),
      'mid-load the dashboard must expose exactly one polite live region for ' +
        'the whole grid — one per loading widget would announce five times',
    ).toHaveLength(1);
    expect(regions[0]).toHaveTextContent(LOADING_MESSAGE);
  });

  it('keeps aria-busy on the widget placeholders but strips their dropped name', async () => {
    const { container } = await renderLoadingGrid();

    for (const key of WIDGET_KEYS) {
      const placeholder = screen.getByTestId(`widget-${key}-loading`);
      expect(placeholder).toHaveAttribute('aria-busy', 'true');
      expect(placeholder).not.toHaveAttribute('aria-label');
    }
    expect(droppedNames(container)).toEqual([]);
  });

  it('reports no aria-prohibited-attr from axe while the placeholders stand', async () => {
    const { container } = await renderLoadingGrid();

    const results = await axe(container);
    const prohibited = (results.violations as { id: string; nodes: { html: string }[] }[]).filter(
      (v) => v.id === 'aria-prohibited-attr',
    );
    expect(
      prohibited.flatMap((v) => v.nodes.map((n) => n.html)),
      'a name on a role-less element is dropped, so the placeholder announces nothing',
    ).toEqual([]);
  });

  it('empties the region once every widget has settled', async () => {
    const { container } = await renderLoadingGrid();

    act(() => {
      controls.setPayloads(SETTLED_PAYLOADS);
      controls.setLoading(false);
    });

    // The region stays mounted and goes empty. Unmounting it would remove the
    // live region a screen reader is watching, and a region inserted *with*
    // content is not reliably announced when the next load starts.
    const region = within(container).getByRole('status');
    expect(region).toHaveTextContent('');
    expect(screen.queryAllByTestId(/^widget-.*-loading$/)).toHaveLength(0);
  });

  it('does not touch the region when a single widget settles early', async () => {
    const { container } = await renderLoadingGrid();
    const region = within(container).getByRole('status');

    const observer = new MutationObserver(() => {});
    observer.observe(region, { childList: true, characterData: true, subtree: true });

    // One widget's slice arrives while the rest are still in flight.
    act(() => {
      controls.setPayloads({ tasks_today: { count: 3 } });
    });

    const mutations = observer.takeRecords();
    observer.disconnect();
    expect(
      mutations.map((m) => m.type),
      'an early-finished widget must not rewrite the region — a re-written live ' +
        'region is re-announced, which is exactly the chatter this shape avoids',
    ).toEqual([]);
    expect(region).toHaveTextContent(LOADING_MESSAGE);
  });

  it('carries the announcement in DE and EN', () => {
    const path = ['dashboard', 'loading', 'announcement'];
    const read = (locale: unknown) =>
      path.reduce<unknown>((node, key) => (node as Record<string, unknown> | undefined)?.[key], locale);
    expect(read(deFull)).toBe('Dashboard wird geladen...');
    expect(read(enFull)).toBe(LOADING_MESSAGE);
  });

  it('announces again when loading restarts after a refresh', async () => {
    const { container } = await renderLoadingGrid();
    const region = within(container).getByRole('status');

    act(() => {
      controls.setPayloads(SETTLED_PAYLOADS);
      controls.setLoading(false);
    });
    expect(region).toHaveTextContent('');

    act(() => {
      controls.setLoading(true);
    });
    // Empty → message is a content change on a live region, so the refresh is
    // announced a second time.
    expect(region).toHaveTextContent(LOADING_MESSAGE);
  });
});
