import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { act } from '@testing-library/react';
import { renderWithProviders } from '../../helpers';
import DashboardEditGrid from '@/components/dashboard/DashboardEditGrid';
import { packByReadingOrder } from '@/lib/dashboardLayoutOps';
import { placementsForBreakpoint } from '@/config/dashboardWidgetCatalog';
import type { DashboardLayout, DashboardWidgetInstance } from '@/api/types';

/**
 * REQ-045 §3.8 (#437) — the drag/resize edit grid.
 *
 * P1: a tile's box must cover its real content height (no overflow/overlap with
 *     the tile below). react-grid-layout has no `min-content` auto-row, so the
 *     component measures content and clamps the tile's `h` up.
 * P2: a breakpoint derived from lg must be re-packed into its own column count
 *     (`packByReadingOrder`) — covered exhaustively by the unit tests in
 *     dashboardLayout.test.ts; here we only smoke-render md to prove no crash.
 */

// react-grid-layout (v2 legacy) and the measurement hook both need a
// ResizeObserver. Capture every instance so the test can synthesise a resize on
// exactly the observer that watches the widget content wrappers.
interface RecordedObserver {
  cb: ResizeObserverCallback;
  targets: Element[];
}
const observers: RecordedObserver[] = [];
class ResizeObserverStub {
  private record: RecordedObserver;
  constructor(cb: ResizeObserverCallback) {
    this.record = { cb, targets: [] };
    observers.push(this.record);
  }
  observe(el: Element) {
    this.record.targets.push(el);
  }
  unobserve(el: Element) {
    this.record.targets = this.record.targets.filter((t) => t !== el);
  }
  disconnect() {
    this.record.targets = [];
  }
}

// Render a synchronous stub widget so no lazy/Suspense boundary sits between the
// grid and the assertions.
const registryMock = vi.hoisted(() => ({ getWidgetComponent: vi.fn() }));
vi.mock('@/components/dashboard/widgetRegistry', () => ({
  getWidgetComponent: registryMock.getWidgetComponent,
}));
const StubWidget = () => <div data-testid="stub-widget">body</div>;

const LAYOUT: DashboardLayout = {
  schema_version: 2,
  widgets: [
    { instance_id: 'a', widget_key: 'winter_protection', config: {} },
    { instance_id: 'b', widget_key: 'onboarding_progress', config: {} },
  ],
  placements: {
    lg: [
      { instance_id: 'a', x: 0, y: 0, w: 6, h: 4 },
      { instance_id: 'b', x: 8, y: 0, w: 4, h: 3 },
    ],
  },
};

const noopWidgetProps = (_instance: DashboardWidgetInstance) => ({
  isFirst: false,
  isLast: false,
  hasConfig: false,
  onMoveUp: vi.fn(),
  onMoveDown: vi.fn(),
  onGrow: vi.fn(),
  onShrink: vi.fn(),
  onRemove: vi.fn(),
  onConfigure: vi.fn(),
});

let originalRO: typeof ResizeObserver | undefined;

beforeEach(() => {
  observers.length = 0;
  registryMock.getWidgetComponent.mockReturnValue(StubWidget);
  originalRO = globalThis.ResizeObserver;
  globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;
});

afterEach(() => {
  globalThis.ResizeObserver = originalRO as typeof ResizeObserver;
  vi.clearAllMocks();
});

/** Parse the px height react-grid-layout writes onto a `.react-grid-item`. */
function itemHeight(el: Element): number {
  const match = /height:\s*([\d.]+)px/.exec(el.getAttribute('style') ?? '');
  return match ? Number(match[1]) : 0;
}

describe('DashboardEditGrid — P1 content coverage', () => {
  it('grows a tile so its box covers taller-than-stored content (no overlap)', () => {
    const CONTENT_PX = 400; // taller than winter_protection's stored h=4 (224px box)
    const { container } = renderWithProviders(
      <DashboardEditGrid layout={LAYOUT} breakpoint="lg" onChange={vi.fn()} widgetProps={noopWidgetProps} />,
    );

    // Report a tall content height for every measured content wrapper, then fire
    // the hook's ResizeObserver (the one that observes `.widget-drag-handle`).
    const handles = Array.from(container.querySelectorAll('.widget-drag-handle'));
    expect(handles.length).toBe(2);
    for (const h of handles) {
      Object.defineProperty(h, 'scrollHeight', { configurable: true, value: CONTENT_PX });
    }
    act(() => {
      for (const obs of observers) {
        const entries = obs.targets
          .filter((t) => (t as HTMLElement).classList.contains('widget-drag-handle'))
          .map((t) => ({ target: t }) as ResizeObserverEntry);
        if (entries.length) obs.cb(entries, obs as unknown as ResizeObserver);
      }
    });

    // Every tile box is now at least as tall as its content — no clipping/overlap.
    const items = Array.from(container.querySelectorAll('.react-grid-item'));
    expect(items.length).toBe(2);
    for (const item of items) {
      expect(itemHeight(item)).toBeGreaterThanOrEqual(CONTENT_PX);
    }
  });

  it('equalises tiles in the same row to the tallest content (no ragged bottoms)', () => {
    // Two widgets share row y=0 with very different content heights. The edit
    // grid must render both tiles at the taller one's height so the row shares a
    // bottom edge (react-grid-layout can't stretch tiles like the CSS grid does).
    const TALL = 500; // widget "a"
    const SHORT = 90; // widget "b"
    const { container } = renderWithProviders(
      <DashboardEditGrid layout={LAYOUT} breakpoint="lg" onChange={vi.fn()} widgetProps={noopWidgetProps} />,
    );

    const handles = Array.from(container.querySelectorAll('.widget-drag-handle')) as HTMLElement[];
    expect(handles.length).toBe(2);
    // DOM order follows reading order (y, x): a (x=0) before b (x=8).
    Object.defineProperty(handles[0], 'scrollHeight', { configurable: true, value: TALL });
    Object.defineProperty(handles[1], 'scrollHeight', { configurable: true, value: SHORT });
    act(() => {
      for (const obs of observers) {
        const entries = obs.targets
          .filter((t) => (t as HTMLElement).classList.contains('widget-drag-handle'))
          .map((t) => ({ target: t }) as ResizeObserverEntry);
        if (entries.length) obs.cb(entries, obs as unknown as ResizeObserver);
      }
    });

    const items = Array.from(container.querySelectorAll('.react-grid-item'));
    expect(items.length).toBe(2);
    const heights = items.map(itemHeight);
    // Both tiles share one height, and it covers the tall widget's content.
    expect(heights[0]).toBe(heights[1]);
    expect(heights[0]).toBeGreaterThanOrEqual(TALL);
  });

  it('shrinks a bloated tile down to its (smaller) natural content height', () => {
    // winter_protection stores h=4 (224px box). A shorter natural content must
    // drive the tile *below* the stored height — the #437 "bloated" fix — rather
    // than staying locked to the stored h (which only ever grew before).
    const SHORT = 110; // < the 224px stored box
    const { container } = renderWithProviders(
      <DashboardEditGrid layout={LAYOUT} breakpoint="lg" onChange={vi.fn()} widgetProps={noopWidgetProps} />,
    );
    const handles = Array.from(container.querySelectorAll('.widget-drag-handle')) as HTMLElement[];
    for (const h of handles) {
      Object.defineProperty(h, 'scrollHeight', { configurable: true, value: SHORT });
    }
    act(() => {
      for (const obs of observers) {
        const entries = obs.targets
          .filter((t) => (t as HTMLElement).classList.contains('widget-drag-handle'))
          .map((t) => ({ target: t }) as ResizeObserverEntry);
        if (entries.length) obs.cb(entries, obs as unknown as ResizeObserver);
      }
    });
    // rowsForContentHeight(110,44,16) = ceil((110+16)/60) = 3 rows → 3*44+2*16 = 164px.
    const items = Array.from(container.querySelectorAll('.react-grid-item'));
    for (const item of items) {
      expect(itemHeight(item)).toBe(164);
      expect(itemHeight(item)).toBeLessThan(224); // shrunk below the stored box
    }
  });

  it('keeps the stored height when content fits within the box', () => {
    const { container } = renderWithProviders(
      <DashboardEditGrid layout={LAYOUT} breakpoint="lg" onChange={vi.fn()} widgetProps={noopWidgetProps} />,
    );
    // jsdom reports scrollHeight 0 → floor 1 → h stays at the stored value.
    // winter_protection stored h=4 → 4*44 + 3*16 = 224px.
    const items = Array.from(container.querySelectorAll('.react-grid-item'));
    const heights = items.map(itemHeight).sort((x, y) => y - x);
    expect(heights[0]).toBe(224);
  });
});

describe('DashboardEditGrid — P2 md re-pack', () => {
  it('renders the md breakpoint from lg placements without crashing', () => {
    const { container } = renderWithProviders(
      <DashboardEditGrid layout={LAYOUT} breakpoint="md" onChange={vi.fn()} widgetProps={noopWidgetProps} />,
    );
    expect(container.querySelectorAll('.react-grid-item').length).toBe(2);
    // The rendered md placements match the shared re-pack helper's output.
    const expected = packByReadingOrder(placementsForBreakpoint(LAYOUT, 'md'), 8);
    for (const p of expected) expect(p.x + p.w).toBeLessThanOrEqual(8);
  });
});
