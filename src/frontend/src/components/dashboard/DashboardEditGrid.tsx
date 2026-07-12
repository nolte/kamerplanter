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
import {
  EDIT_GRID_MARGIN as GRID_MARGIN,
  EDIT_GRID_ROW_HEIGHT as ROW_HEIGHT,
  RESIZE_HANDLE_MARGIN_TOP,
  RESIZE_HANDLE_SIZE,
} from '@/lib/dashboardEditGridGeometry';
import { useContentRowFloors } from '@/hooks/useContentRowFloors';
import type { DashboardLayout, DashboardWidgetInstance, WidgetPlacement } from '@/api/types';

const ResponsiveGrid = WidthProvider(GridLayout);

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
 *  - **Content coverage + equal rows (no overlap, no ragged bottoms).**
 *    react-grid-layout boxes each tile to a fixed `h × ROW_HEIGHT` geometry, so
 *    content taller than the box overflows into the tile below and mixed-height
 *    content in a row leaves ragged bottoms. We measure each tile's real content
 *    height (`useContentRowFloors`), drive its `h` from that, and then equalise
 *    every tile in a row (same `y`) to the row's tallest content — the CSS
 *    `align-items: stretch` the read-only grid gets for free — while keeping the
 *    fixed-row geometry DnD/resize needs.
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

  const gridLayout: Layout = useMemo(() => {
    // 1. Per-tile *content* height (rows). react-grid-layout boxes each tile to a
    //    fixed `h × ROW_HEIGHT`, so a stored `h` larger than the content left dead
    //    space ("bloated") and one smaller clipped/overlapped. `contentFloor` is a
    //    natural measurement (the height:auto drag-handle below), so it shrinks as
    //    well as grows; never below the catalog `minH`. Before the first
    //    measurement lands, fall back to the stored `h` (avoids a paint flash).
    const items = placements.map((p) => {
      const widget = byId.get(p.instance_id);
      const def = widget ? dashboardWidgetCatalog[widget.widget_key as WidgetKey] : undefined;
      const minH = def?.minSize.h ?? 2;
      const contentFloor = floors[p.instance_id] ?? 0;
      const ownH = contentFloor > 0 ? Math.max(minH, contentFloor) : Math.max(minH, p.h);
      return { p, def, ownH };
    });

    // 2. Equalise every tile in a visual row (same start-`y`) to the row's tallest
    //    content. Unlike the read-only CSS grid (`align-items: stretch` gives a row
    //    a shared height for free), react-grid-layout renders each tile at its own
    //    `h` — so mixed-height content in one row produced ragged bottoms and a
    //    zig-zag next row. Rows share `y` because both derived placements
    //    (`packByReadingOrder`) and persisted drag results are vertically
    //    compacted, so grouping by `y` matches the rendered rows. `compactType`
    //    then keeps the equalised rows gap-free; the tallest tile fills exactly and
    //    the row below always starts on one line.
    const rowMaxH = new Map<number, number>();
    for (const it of items) {
      rowMaxH.set(it.p.y, Math.max(rowMaxH.get(it.p.y) ?? 0, it.ownH));
    }

    return items.map(({ p, def, ownH }) => {
      const h = rowMaxH.get(p.y) ?? ownH;
      return {
        i: p.instance_id,
        x: p.x,
        y: p.y,
        w: Math.min(p.w, cols),
        h,
        minW: def?.minSize.w ?? 2,
        minH: 1, // height is content-driven; don't let RGL inflate the tile
        maxW: Math.min(def?.maxSize.w ?? cols, cols),
        maxH: Math.max(def?.maxSize.h ?? 12, h),
      };
    });
  }, [placements, byId, cols, floors]);

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
    // Persist the *stored* `h`, not the rendered one. The rendered `h` is
    // content-driven and row-equalised (see gridLayout above), so writing it back
    // would let a short tile inherit a tall neighbour's height and creep upward on
    // every drag. Vertical resize is disabled (`resizeHandles={['e']}`), so the
    // user never changes `h` directly — the stored value is always the intent.
    const storedH = new Map(placements.map((p) => [p.instance_id, p.h]));
    onChange(next.map((l) => ({ instance_id: l.i, x: l.x, y: l.y, w: l.w, h: storedH.get(l.i) ?? l.h })));
  };

  return (
    <Box data-testid="dashboard-edit-grid">
      <GlobalStyles
        styles={{
          // U-006 — enlarge the resize-handle touch target to ≥48px while
          // keeping the visible icon small (padded hit-area, like MUI IconButton).
          '.react-resizable-handle': {
            width: `${RESIZE_HANDLE_SIZE}px`,
            height: `${RESIZE_HANDLE_SIZE}px`,
            padding: '0 14px 14px 0',
          },
          // DASH-1 (#487) — react-resizable positions the east handle at
          // `top: 50%; margin-top: -10px`; that -10px is calibrated for its
          // original 20px handle. The U-006 enlargement above grows the handle
          // to 48px but leaves the -10px, so on a minimum-height (h=2 → 104px)
          // tile the hit area reached up to `H/2 - 10 = 42px` — into the kebab's
          // 4…52px band (~10px overlap), letting a corner tap start a
          // width-resize instead of opening the widget menu. Re-centre the
          // enlarged handle on the tile's vertical middle (`margin-top: 0` → top
          // edge at `H/2` = 52px on an h=2 tile, level with the kebab's 52px
          // bottom edge) so the two hit areas never overlap on any tile ≥ h=2,
          // while keeping the full 48px ew-resize target and the #480
          // row-equalisation untouched. The selector mirrors react-grid-layout's
          // own `.react-grid-item > … .react-resizable-handle-e` specificity so
          // this override wins deterministically over the library rule.
          '.react-grid-item > .react-resizable-handle.react-resizable-handle-e': {
            marginTop: `${RESIZE_HANDLE_MARGIN_TOP}px`,
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
        // Height follows content (see gridLayout above), so only the east edge
        // resizes width/columns — a vertical resize would just snap back.
        resizeHandles={['e']}
        draggableHandle=".widget-drag-handle"
        transformScale={1}
        useCSSTransforms={!prefersReducedMotion}
        onDragStop={handleChange}
        onResizeStop={handleChange}
        margin={[GRID_MARGIN, GRID_MARGIN]}
      >
        {orderedInstances.map((widget) => (
          // `overflow: hidden` on the grid item is the hard no-overlap guarantee.
          // react-grid-layout already keeps the tile *boxes* from overlapping
          // (collision resolution), so the only way one widget can visually cover
          // another is content overflowing its fixed `h × ROW_HEIGHT` box. Clipping
          // at the tile edge makes that impossible regardless of whether the
          // content-height measurement below has caught up yet. When the
          // measurement has grown `h` to fit (the normal case) nothing is clipped;
          // this only bites during the first paint / a mis-measure, and then it
          // clips rather than overlaps.
          <div key={widget.instance_id} style={{ overflow: 'hidden' }}>
            <Box
              ref={getContentRef(widget.instance_id)}
              className="widget-drag-handle"
              // `height: 'auto'` (natural height) is load-bearing for the
              // content measurement above. A widget card that locks itself to
              // `height:100%` and clips (MUI `Card`'s default `overflow:hidden`)
              // resolves its percentage height against this auto-height box down
              // to its own content, so `scrollHeight` reports the *natural*
              // content height — independent of the current tile box. That lets
              // `useContentRowFloors` size the tile down to its content as well
              // as up (a `minHeight:100%` box instead fills to the tile and can
              // only ever grow, which left short tiles bloated with dead space).
              sx={{ cursor: draggable ? 'move' : 'default', height: 'auto' }}
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
