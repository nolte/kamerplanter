import type { DashboardLayout, WidgetPlacement } from '@/api/types';
import {
  dashboardWidgetCatalog,
  newInstanceId,
  placementsForBreakpoint,
  GRID_COLS_BY_BREAKPOINT,
  type WidgetKey,
} from '@/config/dashboardWidgetCatalog';

type Breakpoint = 'lg' | 'md' | 'sm';

/** Sort placements into reading order (y then x) — the DOM/screenreader order
 *  (UI-NFR-002 R-026 / WCAG 1.3.2). */
export function sortByReadingOrder(placements: WidgetPlacement[]): WidgetPlacement[] {
  return [...placements].sort((a, b) => a.y - b.y || a.x - b.x);
}

/**
 * Re-pack placements row-by-row into a grid of `cols` columns, preserving
 * reading order. Used by the read-only grid when a narrower breakpoint (md/sm)
 * is derived from the wider `lg` placements: the lg coordinates assume 12
 * columns, so rendering them verbatim into an 8-column grid overflows. Each
 * width is clamped to `cols`; heights are preserved.
 */
export function packByReadingOrder(placements: WidgetPlacement[], cols: number): WidgetPlacement[] {
  const ordered = sortByReadingOrder(placements);
  const packed: WidgetPlacement[] = [];
  let x = 0;
  let y = 0;
  let rowHeight = 0;
  for (const p of ordered) {
    const w = Math.min(p.w, cols);
    if (x + w > cols) {
      x = 0;
      y += rowHeight;
      rowHeight = 0;
    }
    packed.push({ instance_id: p.instance_id, x, y, w, h: p.h });
    x += w;
    rowHeight = Math.max(rowHeight, p.h);
  }
  return packed;
}

function withPlacements(layout: DashboardLayout, breakpoint: Breakpoint, placements: WidgetPlacement[]): DashboardLayout {
  return { ...layout, placements: { ...layout.placements, [breakpoint]: placements } };
}

/** Append a widget from the catalog to the layout, placing it in a new bottom row of every existing breakpoint. */
export function addWidget(layout: DashboardLayout, widgetKey: WidgetKey): DashboardLayout {
  const def = dashboardWidgetCatalog[widgetKey];
  const instanceId = newInstanceId();
  const widgets = [...layout.widgets, { instance_id: instanceId, widget_key: widgetKey, config: {} }];

  const placements = { ...layout.placements };
  const breakpoints: Breakpoint[] = ['lg', 'md', 'sm'];
  for (const bp of breakpoints) {
    const existing = placements[bp];
    if (!existing) continue; // derived from lg — leave it derived
    const cols = GRID_COLS_BY_BREAKPOINT[bp];
    const maxY = existing.reduce((m, p) => Math.max(m, p.y + p.h), 0);
    placements[bp] = [
      ...existing,
      { instance_id: instanceId, x: 0, y: maxY, w: Math.min(def.defaultSize.w, cols), h: def.defaultSize.h },
    ];
  }
  // Always ensure lg has the placement (lg is the canonical breakpoint).
  if (!placements.lg) {
    placements.lg = [
      { instance_id: instanceId, x: 0, y: 0, w: Math.min(def.defaultSize.w, GRID_COLS_BY_BREAKPOINT.lg), h: def.defaultSize.h },
    ];
  }
  return { ...layout, widgets, placements };
}

/** Remove a widget instance and prune its placements from every breakpoint. */
export function removeWidget(layout: DashboardLayout, instanceId: string): DashboardLayout {
  const widgets = layout.widgets.filter((w) => w.instance_id !== instanceId);
  const placements: DashboardLayout['placements'] = {};
  for (const [bp, list] of Object.entries(layout.placements)) {
    placements[bp as Breakpoint] = (list ?? []).filter((p) => p.instance_id !== instanceId);
  }
  return { ...layout, widgets, placements };
}

/** Toggle a widget by key: remove all its instances if present, else add one. */
export function toggleWidget(layout: DashboardLayout, widgetKey: WidgetKey): DashboardLayout {
  const instance = layout.widgets.find((w) => w.widget_key === widgetKey);
  if (instance) return removeWidget(layout, instance.instance_id);
  return addWidget(layout, widgetKey);
}

/**
 * Keyboard/button reorder (UI-NFR-002 alternative to drag). Operates on the
 * given breakpoint's reading order, swaps the target with its neighbour, and
 * re-stacks the whole breakpoint into a single clean column so the change is
 * deterministic and screenreader order follows it.
 */
export function moveWidget(
  layout: DashboardLayout,
  breakpoint: Breakpoint,
  instanceId: string,
  direction: 'up' | 'down',
): DashboardLayout {
  const ordered = sortByReadingOrder(placementsForBreakpoint(layout, breakpoint));
  const idx = ordered.findIndex((p) => p.instance_id === instanceId);
  if (idx < 0) return layout;
  const swapWith = direction === 'up' ? idx - 1 : idx + 1;
  if (swapWith < 0 || swapWith >= ordered.length) return layout;
  [ordered[idx], ordered[swapWith]] = [ordered[swapWith], ordered[idx]];
  // Re-stack vertically into a single column (x=0), preserving each height.
  let y = 0;
  const restacked = ordered.map((p) => {
    const placed = { ...p, x: 0, y };
    y += p.h;
    return placed;
  });
  return withPlacements(layout, breakpoint, restacked);
}

/** Resize a widget in the given breakpoint, clamped to catalog min/max and column count. */
export function resizeWidget(
  layout: DashboardLayout,
  breakpoint: Breakpoint,
  instanceId: string,
  deltaW: number,
  deltaH: number,
): DashboardLayout {
  const widget = layout.widgets.find((w) => w.instance_id === instanceId);
  if (!widget) return layout;
  const def = dashboardWidgetCatalog[widget.widget_key as WidgetKey];
  if (!def) return layout;
  const cols = GRID_COLS_BY_BREAKPOINT[breakpoint];
  const current = placementsForBreakpoint(layout, breakpoint);
  const next = current.map((p) => {
    if (p.instance_id !== instanceId) return p;
    const w = Math.min(Math.max(p.w + deltaW, def.minSize.w), Math.min(def.maxSize.w, cols));
    const h = Math.min(Math.max(p.h + deltaH, def.minSize.h), def.maxSize.h);
    return { ...p, w, h };
  });
  return withPlacements(layout, breakpoint, next);
}

/** Replace a breakpoint's placements wholesale (used by react-grid-layout onLayoutChange). */
export function setBreakpointPlacements(
  layout: DashboardLayout,
  breakpoint: Breakpoint,
  placements: WidgetPlacement[],
): DashboardLayout {
  return withPlacements(layout, breakpoint, placements);
}

/** Copy one breakpoint's placements into the other two ("apply to all breakpoints"). */
export function copyPlacementsToAllBreakpoints(layout: DashboardLayout, from: Breakpoint): DashboardLayout {
  const source = placementsForBreakpoint(layout, from);
  return {
    ...layout,
    placements: { lg: source, md: source, sm: source },
  };
}

/** Update a widget instance's config object. */
export function setWidgetConfig(
  layout: DashboardLayout,
  instanceId: string,
  config: Record<string, unknown>,
): DashboardLayout {
  return {
    ...layout,
    widgets: layout.widgets.map((w) => (w.instance_id === instanceId ? { ...w, config } : w)),
  };
}
