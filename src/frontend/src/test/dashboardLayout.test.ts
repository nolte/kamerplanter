import { describe, it, expect } from 'vitest';
import {
  resolveDefaultLayout,
  migrateLayout,
  placementsForBreakpoint,
  DEFAULT_WIDGETS_BY_LEVEL,
} from '@/config/dashboardWidgetCatalog';
import {
  moveWidget,
  toggleWidget,
  resizeWidget,
  sortByReadingOrder,
  copyPlacementsToAllBreakpoints,
  packByReadingOrder,
} from '@/lib/dashboardLayoutOps';
import type { DashboardLayout } from '@/api/types';

describe('resolveDefaultLayout (REQ-021 defaults)', () => {
  it('produces a widget per default key with lg placements', () => {
    const layout = resolveDefaultLayout('beginner');
    expect(layout.schema_version).toBe(2);
    expect(layout.widgets.map((w) => w.widget_key)).toEqual(DEFAULT_WIDGETS_BY_LEVEL.beginner);
    expect(layout.placements.lg).toHaveLength(DEFAULT_WIDGETS_BY_LEVEL.beginner.length);
  });

  it('is additive across levels', () => {
    const beginner = resolveDefaultLayout('beginner').widgets.length;
    const expert = resolveDefaultLayout('expert').widgets.length;
    expect(expert).toBeGreaterThan(beginner);
  });

  it('filters out unavailable widgets', () => {
    const available = new Set(DEFAULT_WIDGETS_BY_LEVEL.beginner.filter((k) => k !== 'daily_tip'));
    const layout = resolveDefaultLayout('beginner', available);
    expect(layout.widgets.map((w) => w.widget_key)).not.toContain('daily_tip');
  });
});

describe('migrateLayout (Szenario 11: v1 → v2)', () => {
  it('reads v1 positions as lg placements and strips them from widgets', () => {
    const v1 = {
      schema_version: 1,
      columns: 12,
      widgets: [
        { instance_id: 'a', widget_key: 'tasks_today', x: 0, y: 0, w: 4, h: 4 },
        { instance_id: 'b', widget_key: 'care_reminders', x: 4, y: 0, w: 4, h: 4 },
      ],
    };
    const migrated = migrateLayout(v1)!;
    expect(migrated.schema_version).toBe(2);
    expect(migrated.placements.lg).toHaveLength(2);
    expect(migrated.widgets[0]).not.toHaveProperty('x');
  });

  it('passes an already-v2 layout through unchanged in shape', () => {
    const v2: DashboardLayout = {
      schema_version: 2,
      widgets: [{ instance_id: 'a', widget_key: 'tasks_today', config: {} }],
      placements: { lg: [{ instance_id: 'a', x: 0, y: 0, w: 4, h: 4 }] },
    };
    const migrated = migrateLayout(v2)!;
    expect(migrated.placements.lg).toHaveLength(1);
  });
});

describe('placementsForBreakpoint', () => {
  const layout: DashboardLayout = {
    schema_version: 2,
    widgets: [
      { instance_id: 'a', widget_key: 'tasks_today', config: {} },
      { instance_id: 'b', widget_key: 'care_reminders', config: {} },
    ],
    placements: { lg: [{ instance_id: 'a', x: 0, y: 0, w: 4, h: 4 }, { instance_id: 'b', x: 4, y: 0, w: 4, h: 4 }] },
  };

  it('derives sm from lg when absent (Szenario 10)', () => {
    const sm = placementsForBreakpoint(layout, 'sm');
    expect(sm).toHaveLength(2);
  });

  it('appends widgets missing a placement so none are dropped', () => {
    const partial: DashboardLayout = {
      ...layout,
      placements: { lg: [{ instance_id: 'a', x: 0, y: 0, w: 4, h: 4 }] },
    };
    const lg = placementsForBreakpoint(partial, 'lg');
    expect(lg.map((p) => p.instance_id).sort()).toEqual(['a', 'b']);
  });
});

describe('dashboardLayoutOps', () => {
  const base: DashboardLayout = {
    schema_version: 2,
    widgets: [
      { instance_id: 'a', widget_key: 'tasks_today', config: {} },
      { instance_id: 'b', widget_key: 'care_reminders', config: {} },
    ],
    placements: { lg: [{ instance_id: 'a', x: 0, y: 0, w: 4, h: 4 }, { instance_id: 'b', x: 0, y: 4, w: 4, h: 4 }] },
  };

  it('moveWidget down reorders reading order (Szenario 7)', () => {
    const moved = moveWidget(base, 'lg', 'a', 'down');
    const order = sortByReadingOrder(moved.placements.lg!).map((p) => p.instance_id);
    expect(order).toEqual(['b', 'a']);
  });

  it('toggleWidget removes an active widget and adds an inactive one', () => {
    const removed = toggleWidget(base, 'tasks_today');
    expect(removed.widgets.map((w) => w.widget_key)).toEqual(['care_reminders']);
    const added = toggleWidget(removed, 'tasks_today');
    expect(added.widgets.map((w) => w.widget_key)).toContain('tasks_today');
  });

  it('resizeWidget clamps to catalog min size', () => {
    // tasks_today minSize.w = 2, minSize.h = 3
    const shrunk = resizeWidget(base, 'lg', 'a', -10, -10);
    const p = shrunk.placements.lg!.find((x) => x.instance_id === 'a')!;
    expect(p.w).toBe(2);
    expect(p.h).toBe(3);
  });

  it('copyPlacementsToAllBreakpoints fills md and sm', () => {
    const all = copyPlacementsToAllBreakpoints(base, 'lg');
    expect(all.placements.md).toBeDefined();
    expect(all.placements.sm).toBeDefined();
  });

  it('packByReadingOrder re-flows 12-col placements into a narrower grid (no overflow)', () => {
    // lg placement at x=8,w=4 would overflow an 8-column grid (gridColumn 9).
    const lg = [
      { instance_id: 'a', x: 0, y: 0, w: 8, h: 4 },
      { instance_id: 'b', x: 8, y: 0, w: 4, h: 4 },
    ];
    const packed = packByReadingOrder(lg, 8);
    // Every packed placement must fit within the 8 columns.
    for (const p of packed) {
      expect(p.x + p.w).toBeLessThanOrEqual(8);
    }
    // Reading order is preserved: a before b.
    expect(packed.map((p) => p.instance_id)).toEqual(['a', 'b']);
    // b wraps to the next row since 8+4 > 8.
    expect(packed[1].y).toBeGreaterThan(0);
  });
});
