import { useMemo } from 'react';
import Box from '@mui/material/Box';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DashboardLoadingRegion from '@/components/dashboard/DashboardLoadingRegion';
import WidgetFrame from '@/components/dashboard/WidgetFrame';
import {
  GRID_COLS_BY_BREAKPOINT,
  dashboardWidgetCatalog,
  type WidgetKey,
} from '@/config/dashboardWidgetCatalog';
import { sortByReadingOrder, deriveBreakpointPlacements } from '@/lib/dashboardLayoutOps';
import type { DashboardLayout, DashboardWidgetInstance } from '@/api/types';

const MIN_ROW_HEIGHT = 44; // px — floor per implicit grid row; content may grow past it

/**
 * REQ-045 §3.9 (K-001) — read-only rendering via a plain CSS grid, **without**
 * react-grid-layout, so the heavy DnD library is not loaded on the most-visited
 * page. DOM order follows (y, x) of the active breakpoint (UI-NFR-002 U-002 /
 * WCAG 1.3.2). Below 600px it stacks into a single column in reading order.
 *
 * Layout note: widgets keep their saved **column** placement (`x` / `w`) but
 * flow to their **natural content height** instead of being locked to a fixed
 * `h × ROW_HEIGHT` box. The old fixed-height rows left large vertical gaps
 * whenever a widget's content was shorter than its stored `h`, and clipped
 * widgets (e.g. quick-actions) whose content was taller. Implicit rows now use
 * `min-content` with a small floor, so the grid packs tightly with no gaps.
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
    // A breakpoint without its own placements is derived from lg, whose x/w
    // assume 12 columns. Re-pack into the active breakpoint's column count so a
    // widget at lg-x=8 doesn't overflow the 8-column tablet grid (the read-only
    // grid has no react-grid-layout re-compaction). Shared with the edit grid.
    const placements = deriveBreakpointPlacements(layout, breakpoint, cols);
    const byId = new Map<string, DashboardWidgetInstance>(layout.widgets.map((w) => [w.instance_id, w]));
    return sortByReadingOrder(placements)
      .map((p) => ({ placement: p, widget: byId.get(p.instance_id) }))
      .filter((x): x is { placement: typeof x.placement; widget: DashboardWidgetInstance } => Boolean(x.widget))
      .filter((x) => renderableKeys(x.widget.widget_key));
  }, [layout, breakpoint, cols, renderableKeys]);

  return (
    <>
      {/* The dashboard's single loading announcement (#1337). It lives on the
          grid, not on a widget: mid-load five widget placeholders stand at once,
          and a live region per placeholder would announce "loading" five times.
          Rendered outside the grid Box so it never becomes a grid item. */}
      <DashboardLoadingRegion />
      <Box
        data-testid="dashboard-readonly-grid"
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: isMobile ? '1fr' : `repeat(${cols}, 1fr)`,
          // Content-driven rows with a small floor. Widgets flow to their natural
          // height (no fixed h×ROW_HEIGHT box), so short widgets no longer leave
          // gaps and tall ones are no longer clipped.
          gridAutoRows: isMobile ? 'auto' : `minmax(${MIN_ROW_HEIGHT}px, min-content)`,
        }}
      >
        {ordered.map(({ placement, widget }) => (
          <Box
            key={widget.instance_id}
            sx={{
              // Keep the saved column placement; let the row auto-flow so the
              // widget takes its content height instead of spanning `h` rows.
              ...(isMobile ? {} : { gridColumn: `${placement.x + 1} / span ${Math.min(placement.w, cols)}` }),
              // minWidth: 0 is required on every breakpoint (not just desktop): a
              // `1fr` track's implicit min-width is `auto` (= the item's
              // min-content size), so a widget with intrinsically wide content
              // (e.g. a chart or long unbreakable label) would otherwise force
              // the single mobile column past the viewport width and cause
              // horizontal page scroll.
              minWidth: 0,
            }}
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
    </>
  );
}
