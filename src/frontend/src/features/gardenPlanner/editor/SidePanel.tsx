/**
 * The side panel of the plan editor (REQ-053 §17.3, GP-UX-068/069, AC-5/AC-17, WP 10.5): the tabs Eigenschaften
 * (properties), Ansicht (view), Ebenen (layers) and Zonen (zones) in one panel that the user can collapse.
 *
 * Its form follows the width alone (GP-UX-069), from this one component:
 * - `docked` (≥ lg): beside the canvas, as high as the canvas area. Collapsed it is not rendered at all, so it
 *   reserves no width (AC-5).
 * - `drawer` (md): a persistent MUI `Drawer` over the right edge of the canvas. It is not modal (the persistent
 *   variant has no backdrop, no focus trap and no `role="dialog"`), so the plan stays usable beside it.
 * - `sheet` (below md): a bottom sheet in the dock above the tool bars, half or full height of what is visible
 *   above the on-screen keyboard (`visualViewport`, GP-UX-052); not modal, closed by its button.
 *
 * The tabs follow the WAI-ARIA "Tabs" pattern: a `tablist` of `tab`s with `aria-selected` and `aria-controls` on
 * their `tabpanel` (which names itself by `aria-labelledby`), a roving tabindex - only the active tab is a tab stop -
 * and arrow left/right, Home and End move between them; the selection follows the focus. All four tab panels exist,
 * the inactive ones hidden and empty: only the active tab's content is mounted.
 */
import type { KeyboardEvent as ReactKeyboardEvent, ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import Tab from '@mui/material/Tab';
import Tabs from '@mui/material/Tabs';
import Tooltip from '@mui/material/Tooltip';
import CloseIcon from '@mui/icons-material/Close';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { EDITOR_ANCHORS } from './anchors';
import { PANEL_WIDTH_PX } from './layout';
import { SIDE_PANEL_TABS, type SidePanelTab } from './sidePanelState';

const PREFIX = 'pages.gardenPlan.editor.sidePanel';
const TARGET_PX = 48;

/** The form of the panel, chosen by the width (GP-UX-069). */
export type SidePanelVariant = 'docked' | 'drawer' | 'sheet';
/** The height of the bottom sheet. */
export type SheetSize = 'half' | 'full';

/** Share of the visible height the sheet takes at most (half) or exactly (full). */
const SHEET_SHARE: Record<SheetSize, number> = { half: 0.45, full: 0.9 };

export const sidePanelTabId = (tab: SidePanelTab): string => `garden-plan-side-panel-tab-${tab}`;
export const sidePanelTabPanelId = (tab: SidePanelTab): string =>
  `garden-plan-side-panel-tabpanel-${tab}`;

/** The keys the tab list keeps for itself: they must not reach the plan (arrow-key move, single-key shortcuts). */
const TAB_KEYS = new Set(['ArrowLeft', 'ArrowRight', 'Home', 'End']);

export interface SidePanelProps {
  variant: SidePanelVariant;
  open: boolean;
  tab: SidePanelTab;
  onTab: (tab: SidePanelTab) => void;
  onClose: () => void;
  /** The content of the active tab; only that one is mounted. */
  children: ReactNode;
  /** Docked: the height of the canvas area beside it (absent where nothing is laid out). */
  heightPx?: number;
  /** Sheet: the height visible above the on-screen keyboard (`visualViewport`). */
  visibleHeight: number;
  sheetSize: SheetSize;
  onSheetSize: (size: SheetSize) => void;
}

function PanelFrame({
  variant,
  tab,
  onTab,
  onClose,
  children,
  sheetSize,
  onSheetSize,
}: Omit<SidePanelProps, 'open' | 'heightPx' | 'visibleHeight'>) {
  const { t } = useTranslation();
  const keepKeys = (event: ReactKeyboardEvent<HTMLElement>) => {
    if (TAB_KEYS.has(event.key)) event.stopPropagation();
  };
  const sizeLabel = t(`${PREFIX}.${sheetSize === 'half' ? 'expand' : 'shrink'}`);
  return (
    <Paper
      component="section"
      variant={variant === 'drawer' ? 'elevation' : 'outlined'}
      elevation={0}
      id={EDITOR_ANCHORS.panel}
      // The skip link "To the properties panel" focuses the panel itself (GP-NFR-070).
      tabIndex={-1}
      aria-label={t(`${PREFIX}.region`)}
      data-testid="garden-plan-side-panel"
      data-variant={variant}
      data-tab={tab}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        flex: '1 1 auto',
        minHeight: 0,
        minWidth: 0,
        outline: 'none',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          borderBottom: 1,
          borderColor: 'divider',
          minWidth: 0,
        }}
      >
        {variant === 'sheet' && (
          <Tooltip title={sizeLabel}>
            <IconButton
              aria-label={sizeLabel}
              onClick={() => onSheetSize(sheetSize === 'half' ? 'full' : 'half')}
              data-testid="garden-plan-sheet-size"
              data-size={sheetSize}
              sx={{ width: TARGET_PX, height: TARGET_PX, flex: 'none' }}
            >
              {sheetSize === 'half' ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Tooltip>
        )}
        <Box onKeyDown={keepKeys} sx={{ flex: '1 1 auto', minWidth: 0 }}>
          <Tabs
            value={tab}
            onChange={(_event, next: SidePanelTab) => onTab(next)}
            aria-label={t(`${PREFIX}.tabs`)}
            selectionFollowsFocus
            // Content-sized tabs; on a panel too narrow for the labels the list scrolls inside, the page never does.
            variant="scrollable"
            scrollButtons={false}
            data-testid="garden-plan-side-panel-tabs"
            sx={{ minHeight: TARGET_PX }}
          >
            {SIDE_PANEL_TABS.map((value) => (
              <Tab
                key={value}
                value={value}
                label={t(`${PREFIX}.tab.${value}`)}
                id={sidePanelTabId(value)}
                aria-controls={sidePanelTabPanelId(value)}
                data-testid={sidePanelTabId(value)}
                sx={{
                  minHeight: TARGET_PX,
                  minWidth: 0,
                  px: 1,
                  // The four labels fit beside the close button on the 344 px panel, also in German.
                  fontSize: '0.8125rem',
                  textTransform: 'none',
                  letterSpacing: 0,
                }}
              />
            ))}
          </Tabs>
        </Box>
        <Tooltip title={t(`${PREFIX}.close`)}>
          <IconButton
            aria-label={t(`${PREFIX}.close`)}
            onClick={onClose}
            data-testid="garden-plan-panel-close"
            sx={{ width: TARGET_PX, height: TARGET_PX, flex: 'none' }}
          >
            <CloseIcon />
          </IconButton>
        </Tooltip>
      </Box>
      {SIDE_PANEL_TABS.map((value) => (
        <Box
          key={value}
          role="tabpanel"
          id={sidePanelTabPanelId(value)}
          aria-labelledby={sidePanelTabId(value)}
          data-testid={sidePanelTabPanelId(value)}
          hidden={value !== tab}
          sx={
            value === tab
              ? { flex: '1 1 auto', minHeight: 0, overflowY: 'auto', p: 1.5 }
              : undefined
          }
        >
          {value === tab ? children : null}
        </Box>
      ))}
    </Paper>
  );
}

export function SidePanel({ open, heightPx, visibleHeight, ...frame }: SidePanelProps) {
  const { variant, sheetSize } = frame;
  if (variant === 'drawer') {
    return (
      <Drawer
        variant="persistent"
        anchor="right"
        open={open}
        data-testid="garden-plan-side-panel-drawer"
        slotProps={{
          // Over the canvas row (positioned), not the window: the drawer lies on the right edge of the plan.
          paper: {
            sx: {
              position: 'absolute',
              top: 0,
              right: 0,
              height: '100%',
              width: PANEL_WIDTH_PX,
              maxWidth: '100%',
              zIndex: 3,
              boxShadow: 6,
              display: 'flex',
              flexDirection: 'column',
            },
          },
          transition: { unmountOnExit: true },
        }}
      >
        <PanelFrame {...frame} />
      </Drawer>
    );
  }
  if (!open) return null;
  if (variant === 'sheet') {
    const sheetPx = Math.round(visibleHeight * SHEET_SHARE[sheetSize]);
    return (
      <Box
        data-testid="garden-plan-sheet"
        data-size={sheetSize}
        sx={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}
        // Follows the visible height (keyboard open or not): an inline style, not one class per pixel.
        style={sheetSize === 'full' ? { height: sheetPx } : { maxHeight: sheetPx }}
      >
        <PanelFrame {...frame} />
      </Box>
    );
  }
  return (
    <Box
      data-testid="garden-plan-side-panel-dock"
      sx={{
        width: PANEL_WIDTH_PX,
        flex: 'none',
        display: 'flex',
        flexDirection: 'column',
        minHeight: 0,
      }}
      style={heightPx !== undefined ? { height: heightPx } : { maxHeight: '80vh' }}
    >
      <PanelFrame {...frame} />
    </Box>
  );
}
