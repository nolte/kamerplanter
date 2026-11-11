/**
 * The frame of the plan editor's workspace (REQ-053 §17.3, WP 10.3): the skip links, the one header bar, and the
 * content below it - messages and tool hints, the canvas row (or the list) with the side panel docked beside it, or
 * below md with the dock under it. `GardenPlanEditor` is the content: it owns the state and hands the parts in; the
 * frame owns only the arrangement, so desktop, tablet and phone come from this one tree (GP-UX-069).
 *
 * Behind the tab "Beete" the content is hidden, not unmounted (GP-UX-065): the header bar stays, because the tabs
 * live in it. With the route's tabs the content is the tab panel of Plan and Liste (`garden-plan-tabpanel-editor`).
 */
import type { KeyboardEvent as ReactKeyboardEvent, ReactNode } from 'react';
import Box from '@mui/material/Box';

/** The tab panel attributes of the content, when the route's tabs show it. */
export interface WorkspacePanel {
  id: string;
  /** The tab that names the panel; absent while the tabs are in the overflow. */
  labelledBy?: string;
  /** The name of the panel while its tab is not on screen. */
  label?: string;
}

interface EditorWorkspaceProps {
  /** The skip links (GP-NFR-070): the first tab stops, not rendered while the content is hidden. */
  skipLinks: ReactNode;
  header: ReactNode;
  /** Save messages, notices, hints and the rows above the plan. */
  above: ReactNode;
  /**
   * The canvas row (tool rail, canvas area) or the list, and the side panel at its one place: docked beside the
   * canvas from md up, below md in the bottom dock as a sheet above the TouchBar and the tool bar (#2882).
   */
  body: ReactNode;
  /** Live region and dialogs: always mounted, also behind the "Beete" tab. */
  overlays: ReactNode;
  /** The tab "Beete" is open: everything under the header bar is hidden. */
  contentHidden?: boolean;
  panel?: WorkspacePanel;
  onKeyDown: (event: ReactKeyboardEvent<HTMLElement>) => void;
}

export function EditorWorkspace({
  skipLinks,
  header,
  above,
  body,
  overlays,
  contentHidden = false,
  panel,
  onKeyDown,
}: EditorWorkspaceProps) {
  const panelProps = panel
    ? {
        id: panel.id,
        'data-testid': panel.id,
        ...(panel.labelledBy
          ? { role: 'tabpanel', 'aria-labelledby': panel.labelledBy }
          : { role: 'region', 'aria-label': panel.label }),
      }
    : {};
  return (
    <Box
      data-testid="garden-plan-editor"
      onKeyDown={onKeyDown}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
        minWidth: 0,
        // GP-NFR-026: no motion for people who ask for none (ripples, tooltips, dialogs, ghost fading).
        '@media (prefers-reduced-motion: reduce)': {
          '& *, & *::before, & *::after': {
            transition: 'none !important',
            animation: 'none !important',
            scrollBehavior: 'auto !important',
          },
        },
      }}
    >
      {!contentHidden && skipLinks}
      {header}
      <Box
        {...panelProps}
        hidden={contentHidden}
        // `display` would override the `hidden` attribute: the hidden content takes no room at all.
        sx={{ display: contentHidden ? 'none' : 'flex', flexDirection: 'column', gap: 1, minWidth: 0 }}
      >
        {above}
        {body}
      </Box>
      {overlays}
    </Box>
  );
}
