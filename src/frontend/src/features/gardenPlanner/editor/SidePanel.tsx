/**
 * The side panel of the plan editor (REQ-053 §17.3, GP-UX-068/069, AC-5/AC-17, WP 10.5): the tabs Eigenschaften
 * (properties), Ansicht (view), Ebenen (layers) and Zonen (zones) in one panel that the user can collapse.
 *
 * Its form follows the width alone (GP-UX-069), from this one component:
 * - `docked` (md and up): beside the canvas, as high as the canvas area; the canvas gives up the width, so the panel
 *   never covers the zoom controls or a selected object (WCAG 2.2 SC 2.4.11, #2885). Collapsed it is not rendered at
 *   all, so it reserves no width (AC-5).
 * - `sheet` (below md): a bottom sheet in the dock above the tool bars, half or full height of what is visible
 *   above the on-screen keyboard (`visualViewport`, GP-UX-052); not modal, closed by its button.
 * Both forms are the same elements; only their attributes and styles differ. A change of the form therefore keeps
 * the content mounted - an open dialog or a typed draft in it survives a resize (#2882). The caller keeps the panel
 * at one place in its tree for the same reason.
 *
 * The tabs follow the WAI-ARIA "Tabs" pattern with manual activation: a `tablist` of `tab`s with `aria-selected`
 * and `aria-controls` on their `tabpanel` (which names itself by `aria-labelledby`), a roving tabindex - only the
 * active tab is a tab stop - and arrow left/right, Home and End move the focus between them; Enter or Space (or a
 * click) activates the focused tab. Arrowing across the tabs therefore neither loads the zone panel nor leaves
 * "Eigenschaften" with a draft in it (#2887). All four tab panels exist, the inactive ones hidden and empty: only the
 * active tab's content is mounted.
 */
import type { CSSProperties, KeyboardEvent as ReactKeyboardEvent, ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
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
export type SidePanelVariant = 'docked' | 'sheet';
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
      variant="outlined"
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
            // Manual activation (no `selectionFollowsFocus`): the arrows move the focus, Enter/Space activate (#2887).
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

/** The size of the panel's box per form: an inline style, because it follows measured heights (no class per pixel). */
function boxStyle(
  variant: SidePanelVariant,
  sheetSize: SheetSize,
  visibleHeight: number,
  heightPx: number | undefined,
): CSSProperties {
  if (variant === 'sheet') {
    // Follows the visible height (on-screen keyboard open or not).
    const sheetPx = Math.round(visibleHeight * SHEET_SHARE[sheetSize]);
    return sheetSize === 'full' ? { height: sheetPx } : { maxHeight: sheetPx };
  }
  return heightPx !== undefined ? { height: heightPx } : { maxHeight: '80vh' };
}

export function SidePanel({ open, heightPx, visibleHeight, ...frame }: SidePanelProps) {
  const { variant, sheetSize } = frame;
  if (!open) return null;
  const sheet = variant === 'sheet';
  // One box for both forms: a change of the form changes attributes and styles, never the elements (#2882).
  return (
    <Box
      data-testid={sheet ? 'garden-plan-sheet' : 'garden-plan-side-panel-dock'}
      data-size={sheet ? sheetSize : undefined}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: 0,
        ...(sheet ? {} : { width: PANEL_WIDTH_PX, flex: 'none' }),
      }}
      style={boxStyle(variant, sheetSize, visibleHeight, heightPx)}
    >
      <PanelFrame {...frame} />
    </Box>
  );
}
