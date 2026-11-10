/**
 * The overflow "⋮" at the end of the editor header bar (REQ-053 §17.3, GP-UX-052/063, UI-NFR-021 R-017…R-020):
 * the rare actions (keyboard help, underlay, select all, export and import, …) and every header control the bar
 * moved out for lack of room, in the bar's order. The button carries `aria-label`, `aria-haspopup="menu"`,
 * `aria-expanded` and `aria-controls`; every entry has an icon and a text and is at least 48 px high (the menu is
 * `ContextMenu`, so arrow keys, Home/End and Esc work as in every MUI menu). "Save" is never in here.
 */
import { useId, useState, type Ref } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import { ContextMenu, type MenuAction, type MenuAnchor } from './ContextMenu';

const PREFIX = 'pages.gardenPlan.editor';

interface EditorHeaderActionsProps {
  actions: readonly MenuAction[];
  /** The button, so a dialog opened from an entry can give the focus back to it when it closes (WCAG 2.4.3). */
  buttonRef?: Ref<HTMLButtonElement>;
}

export function EditorHeaderActions({ actions, buttonRef }: EditorHeaderActionsProps) {
  const { t } = useTranslation();
  const menuId = useId();
  const [anchor, setAnchor] = useState<MenuAnchor | null>(null);
  const label = t(`${PREFIX}.contextMenu.overflow`);
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', flexShrink: 0 }} data-testid="garden-plan-header-actions">
      <Tooltip title={label}>
        <IconButton
          ref={buttonRef}
          aria-label={label}
          aria-haspopup="menu"
          aria-expanded={anchor !== null}
          aria-controls={anchor !== null ? menuId : undefined}
          onClick={(event) => setAnchor({ kind: 'element', element: event.currentTarget })}
          sx={{ width: 48, height: 48 }}
          data-testid="garden-plan-overflow"
        >
          <MoreVertIcon />
        </IconButton>
      </Tooltip>
      <ContextMenu
        id={menuId}
        anchor={anchor}
        actions={actions}
        onClose={() => setAnchor(null)}
        label={label}
        testId="garden-plan-overflow-menu"
      />
    </Box>
  );
}
