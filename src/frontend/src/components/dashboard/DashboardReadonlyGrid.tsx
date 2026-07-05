import { useMemo } from 'react';
import Box from '@mui/material/Box';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import WidgetFrame from '@/components/dashboard/WidgetFrame';
import {
  GRID_COLS_BY_BREAKPOINT,
  dashboardWidgetCatalog,
  placementsForBreakpoint,
  type WidgetKey,
} from '@/config/dashboardWidgetCatalog';
import { sortByReadingOrder } from '@/lib/dashboardLayoutOps';
import type { DashboardLayout, DashboardWidgetInstance } from '@/api/types';

const ROW_HEIGHT = 44; // px per grid row unit

/**
 * REQ-045 §3.9 (K-001) — read-only rendering via a plain CSS grid, **without**
 * react-grid-layout, so the heavy DnD library is not loaded on the most-visited
 * page. DOM order follows (y, x) of the active breakpoint (UI-NFR-002 U-002 /
 * WCAG 1.3.2). Below 600px it stacks into a single column in reading order.
 */
export default function DashboardReadonlyGrid({
  layout,
  renderableKeys,
}: {
  layout: DashboardLayout;
  renderableKeys: (key: string) => boolean;
}) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'lg'));
  const breakpoint: 'lg' | 'md' | 'sm' = isMobile ? 'sm' : isTablet ? 'md' : 'lg';
  const cols = GRID_COLS_BY_BREAKPOINT[breakpoint];

  const ordered = useMemo(() => {
    const placements = placementsForBreakpoint(layout, breakpoint);
    const byId = new Map<string, DashboardWidgetInstance>(layout.widgets.map((w) => [w.instance_id, w]));
    return sortByReadingOrder(placements)
      .map((p) => ({ placement: p, widget: byId.get(p.instance_id) }))
      .filter((x): x is { placement: typeof x.placement; widget: DashboardWidgetInstance } => Boolean(x.widget))
      .filter((x) => renderableKeys(x.widget.widget_key));
  }, [layout, breakpoint, renderableKeys]);

  return (
    <Box
      data-testid="dashboard-readonly-grid"
      sx={{
        display: 'grid',
        gap: 2,
        gridTemplateColumns: isMobile ? '1fr' : `repeat(${cols}, 1fr)`,
        gridAutoRows: isMobile ? 'auto' : `${ROW_HEIGHT}px`,
      }}
    >
      {ordered.map(({ placement, widget }) => (
        <Box
          key={widget.instance_id}
          sx={
            isMobile
              ? undefined
              : {
                  gridColumn: `${placement.x + 1} / span ${Math.min(placement.w, cols)}`,
                  gridRow: `${placement.y + 1} / span ${placement.h}`,
                  minWidth: 0,
                }
          }
        >
          <WidgetFrame
            instance={widget}
            editMode={false}
            hasConfig={dashboardWidgetCatalog[widget.widget_key as WidgetKey]?.hasConfig ?? false}
            isFirst
            isLast
            onMoveUp={() => {}}
            onMoveDown={() => {}}
            onGrow={() => {}}
            onShrink={() => {}}
            onRemove={() => {}}
            onConfigure={() => {}}
          />
        </Box>
      ))}
    </Box>
  );
}
