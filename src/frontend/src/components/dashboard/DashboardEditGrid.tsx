import { useMemo } from 'react';
import Box from '@mui/material/Box';
import GlobalStyles from '@mui/material/GlobalStyles';
import useMediaQuery from '@mui/material/useMediaQuery';
// react-grid-layout v2 dropped WidthProvider and the old flat `Layout` item type
// from the main entry; the `/legacy` subpath keeps the v1-compatible HOC API and
// re-exports Layout (now `readonly LayoutItem[]`) that this component relies on.
import GridLayout, { WidthProvider, type Layout } from 'react-grid-layout/legacy';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import WidgetFrame from '@/components/dashboard/WidgetFrame';
import {
  GRID_COLS_BY_BREAKPOINT,
  dashboardWidgetCatalog,
  type WidgetKey,
} from '@/config/dashboardWidgetCatalog';
import { deriveBreakpointPlacements, sortByReadingOrder } from '@/lib/dashboardLayoutOps';
import { useContentRowFloors } from '@/hooks/useContentRowFloors';
import type { DashboardLayout, DashboardWidgetInstance, WidgetPlacement } from '@/api/types';

const ResponsiveGrid = WidthProvider(GridLayout);
const ROW_HEIGHT = 44;
const GRID_MARGIN = 16;

/**
 * REQ-045 §3.8 — the drag-and-drop / resize surface. Lazy-loaded (this module
 * is the only static importer of react-grid-layout, UI-NFR-003 K-001) and
 * mounted only when the user enters edit mode. Drag/resize handles are not
 * focusable (draggableCancel + tabIndex handling); keyboard parity lives in the
 * WidgetFrame kebab menu (UI-NFR-002 U-001). Motion is disabled under
 * prefers-reduced-motion (O-003).
 *
 * Two layout concerns are handled here that the read-only grid gets "for free"
 * from CSS:
 *
 *  - **Content coverage (no overlap).** react-grid-layout boxes each tile to a
 *    fixed `h × ROW_HEIGHT` geometry, so content taller than the box overflows
 *    into the tile below. We measure each tile's real content height
 *    (`useContentRowFloors`) and clamp its rendered `h` up to the number of rows
 *    that covers it — keeping the fixed-row geometry DnD/resize needs.
 *  - **md/sm re-pack.** A breakpoint without its own placements is derived from
 *    the 12-column `lg` layout; its `x/w` are re-packed into the active column
 *    count (`deriveBreakpointPlacements`) instead of leaving scattered gaps and
 *    overflows. `compactType="vertical"` then keeps rows gap-free.
 */
export default function DashboardEditGrid({
  layout,
  breakpoint,
  onChange,
  widgetProps,
}: {
  layout: DashboardLayout;
  breakpoint: 'lg' | 'md' | 'sm';
  onChange: (placements: WidgetPlacement[]) => void;
  widgetProps: (instance: DashboardWidgetInstance) => {
    isFirst: boolean;
    isLast: boolean;
    hasConfig: boolean;
    onMoveUp: () => void;
    onMoveDown: () => void;
    onGrow: () => void;
    onShrink: () => void;
    onRemove: () => void;
    onConfigure: () => void;
  };
}) {
  const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');
  const cols = GRID_COLS_BY_BREAKPOINT[breakpoint];
  const draggable = breakpoint !== 'sm'; // Mobile: no DnD (UI-NFR-001)

  const { floors, getContentRef } = useContentRowFloors(ROW_HEIGHT, GRID_MARGIN);

  // Own placements win; a breakpoint derived from lg is re-packed into `cols`
  // (P2) so md/sm never inherit 12-column x-coordinates.
  const placements = useMemo(
    () => deriveBreakpointPlacements(layout, breakpoint, cols),
    [layout, breakpoint, cols],
  );

  const byId = useMemo(
    () => new Map<string, DashboardWidgetInstance>(layout.widgets.map((w) => [w.instance_id, w])),
    [layout.widgets],
  );

  const gridLayout: Layout = useMemo(
    () =>
      placements.map((p) => {
        const widget = byId.get(p.instance_id);
        const def = widget ? dashboardWidgetCatalog[widget.widget_key as WidgetKey] : undefined;
        const minH = def?.minSize.h ?? 2;
        // Clamp `h` up to whatever covers the measured content (P1). Content
        // coverage overrides maxSize.h — a tile must never clip/overlap — so the
        // resize ceiling is widened to the effective height when needed.
        const contentFloor = floors[p.instance_id] ?? 0;
        const h = Math.max(p.h, minH, contentFloor);
        return {
          i: p.instance_id,
          x: p.x,
          y: p.y,
          w: Math.min(p.w, cols),
          h,
          minW: def?.minSize.w ?? 2,
          minH,
          maxW: Math.min(def?.maxSize.w ?? cols, cols),
          maxH: Math.max(def?.maxSize.h ?? 12, h),
        };
      }),
    [placements, byId, cols, floors],
  );

  // DOM order follows reading order (y, x) for screenreaders (UI-NFR-002 U-002).
  // Derived from the same (packed) placements the grid renders, so DOM and
  // visual order stay in sync across breakpoints.
  const orderedInstances = useMemo(
    () =>
      sortByReadingOrder(placements)
        .map((p) => byId.get(p.instance_id))
        .filter((w): w is DashboardWidgetInstance => Boolean(w)),
    [placements, byId],
  );

  const handleChange = (next: Layout) => {
    onChange(next.map((l) => ({ instance_id: l.i, x: l.x, y: l.y, w: l.w, h: l.h })));
  };

  return (
    <Box data-testid="dashboard-edit-grid">
      <GlobalStyles
        styles={{
          // U-006 — enlarge the resize-handle touch target to ≥48px while
          // keeping the visible icon small (padded hit-area, like MUI IconButton).
          '.react-resizable-handle': {
            width: '48px',
            height: '48px',
            padding: '0 14px 14px 0',
          },
          // O-003 — respect reduced motion by dropping the grid transition.
          '@media (prefers-reduced-motion: reduce)': {
            '.react-grid-item.cssTransforms': { transition: 'none !important' },
            '.react-grid-item': { transition: 'none !important' },
          },
        }}
      />
      <ResponsiveGrid
        className="layout"
        layout={gridLayout}
        cols={cols}
        rowHeight={ROW_HEIGHT}
        compactType="vertical"
        isDraggable={draggable}
        isResizable={draggable}
        draggableHandle=".widget-drag-handle"
        transformScale={1}
        useCSSTransforms={!prefersReducedMotion}
        onDragStop={handleChange}
        onResizeStop={handleChange}
        margin={[GRID_MARGIN, GRID_MARGIN]}
      >
        {orderedInstances.map((widget) => (
          <div key={widget.instance_id}>
            <Box
              ref={getContentRef(widget.instance_id)}
              className="widget-drag-handle"
              sx={{ cursor: draggable ? 'move' : 'default', height: '100%' }}
              tabIndex={-1}
            >
              <WidgetFrame instance={widget} editMode {...widgetProps(widget)} />
            </Box>
          </div>
        ))}
      </ResponsiveGrid>
    </Box>
  );
}
