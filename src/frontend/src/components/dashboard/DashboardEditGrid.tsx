import { useMemo } from 'react';
import Box from '@mui/material/Box';
import GlobalStyles from '@mui/material/GlobalStyles';
import useMediaQuery from '@mui/material/useMediaQuery';
import GridLayout, { WidthProvider, type Layout } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import WidgetFrame from '@/components/dashboard/WidgetFrame';
import {
  GRID_COLS_BY_BREAKPOINT,
  dashboardWidgetCatalog,
  placementsForBreakpoint,
  type WidgetKey,
} from '@/config/dashboardWidgetCatalog';
import { sortByReadingOrder } from '@/lib/dashboardLayoutOps';
import type { DashboardLayout, DashboardWidgetInstance, WidgetPlacement } from '@/api/types';

const ResponsiveGrid = WidthProvider(GridLayout);
const ROW_HEIGHT = 44;

/**
 * REQ-045 §3.8 — the drag-and-drop / resize surface. Lazy-loaded (this module
 * is the only static importer of react-grid-layout, UI-NFR-003 K-001) and
 * mounted only when the user enters edit mode. Drag/resize handles are not
 * focusable (draggableCancel + tabIndex handling); keyboard parity lives in the
 * WidgetFrame kebab menu (UI-NFR-002 U-001). Motion is disabled under
 * prefers-reduced-motion (O-003).
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

  const placements = placementsForBreakpoint(layout, breakpoint);
  const byId = new Map<string, DashboardWidgetInstance>(layout.widgets.map((w) => [w.instance_id, w]));

  const gridLayout: Layout[] = useMemo(
    () =>
      placements.map((p) => {
        const widget = byId.get(p.instance_id);
        const def = widget ? dashboardWidgetCatalog[widget.widget_key as WidgetKey] : undefined;
        return {
          i: p.instance_id,
          x: p.x,
          y: p.y,
          w: Math.min(p.w, cols),
          h: p.h,
          minW: def?.minSize.w ?? 2,
          minH: def?.minSize.h ?? 2,
          maxW: Math.min(def?.maxSize.w ?? cols, cols),
          maxH: def?.maxSize.h ?? 12,
        };
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [layout, breakpoint, cols],
  );

  // DOM order follows reading order (y, x) for screenreaders (UI-NFR-002 U-002).
  const orderedInstances = sortByReadingOrder(placements)
    .map((p) => byId.get(p.instance_id))
    .filter((w): w is DashboardWidgetInstance => Boolean(w));

  const handleChange = (next: Layout[]) => {
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
        isDraggable={draggable}
        isResizable={draggable}
        draggableHandle=".widget-drag-handle"
        transformScale={1}
        useCSSTransforms={!prefersReducedMotion}
        onDragStop={handleChange}
        onResizeStop={handleChange}
        margin={[16, 16]}
      >
        {orderedInstances.map((widget) => (
          <div key={widget.instance_id}>
            <Box
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
