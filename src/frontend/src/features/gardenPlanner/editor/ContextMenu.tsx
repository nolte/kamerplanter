/**
 * The item menu (REQ-053 GP-FR-027, GP-UX-040): the same menu opens at the pointer on a right
 * click (mouse and pen) and under the "⋯" button of the panel (touch has no context menu). The
 * caller decides which actions exist; every entry is at least 48 px high. The overflow "⋮" of the
 * editor header bar (GP-UX-063) uses it too: there an entry may be a switch (`checked` with
 * `kind: 'checkbox'`) or one of a group (`kind: 'radio'`, the tabs), and keeps the `data-testid` of the
 * control it stands in for (`testId`, GP-UX-070).
 */
import type { ReactNode } from 'react';
import Divider from '@mui/material/Divider';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Typography from '@mui/material/Typography';
import CheckIcon from '@mui/icons-material/Check';

export type MenuAnchor =
  { kind: 'position'; x: number; y: number } | { kind: 'element'; element: HTMLElement };

export interface MenuAction {
  id: string;
  label: string;
  icon?: ReactNode;
  onClick: () => void;
  disabled?: boolean;
  /** A divider is drawn above this entry. */
  separated?: boolean;
  /** The key combination that runs the same action, shown at the end of the entry (e.g. Ctrl/Cmd + D). */
  shortcut?: { label: string; aria: string };
  /** A second line under the label, e.g. why the entry is disabled. */
  secondary?: string | null;
  /** On/off of a switch (`kind: 'checkbox'`) or the chosen one of a group (`kind: 'radio'`). */
  checked?: boolean;
  kind?: 'checkbox' | 'radio';
  /** The `data-testid` of the entry; defaults to `garden-plan-menu-<id>`. */
  testId?: string;
}

interface ContextMenuProps {
  anchor: MenuAnchor | null;
  actions: readonly MenuAction[];
  onClose: () => void;
  label: string;
  testId?: string;
  /** The id of the list, for the `aria-controls` of the button that opens it. */
  id?: string;
}

function roleOf(action: MenuAction): 'menuitem' | 'menuitemcheckbox' | 'menuitemradio' {
  if (action.kind === 'checkbox') return 'menuitemcheckbox';
  if (action.kind === 'radio') return 'menuitemradio';
  return 'menuitem';
}

export function ContextMenu({
  anchor,
  actions,
  onClose,
  label,
  testId = 'garden-plan-menu',
  id,
}: ContextMenuProps) {
  return (
    <Menu
      open={anchor !== null}
      onClose={onClose}
      anchorReference={anchor?.kind === 'position' ? 'anchorPosition' : 'anchorEl'}
      anchorPosition={anchor?.kind === 'position' ? { top: anchor.y, left: anchor.x } : undefined}
      anchorEl={anchor?.kind === 'element' ? anchor.element : undefined}
      slotProps={{
        list: { 'aria-label': label, dense: false, ...(id ? { id } : {}) },
        paper: { 'data-testid': testId } as never,
      }}
    >
      {actions.flatMap((action) => [
        action.separated ? <Divider key={`${action.id}-divider`} component="li" /> : null,
        <MenuItem
          key={action.id}
          disabled={action.disabled}
          onClick={() => {
            onClose();
            action.onClick();
          }}
          role={roleOf(action)}
          aria-checked={action.kind ? action.checked === true : undefined}
          selected={action.kind === 'radio' && action.checked === true}
          // MUI drops the item height to `auto` from sm up in a media rule that beats a plain `minHeight`: the
          // doubled class keeps every entry at the 48 px target (UI-NFR-001 R-011, GP-UX-052).
          sx={{ '&&': { minHeight: 48 } }}
          aria-keyshortcuts={action.shortcut?.aria}
          data-testid={action.testId ?? `garden-plan-menu-${action.id}`}
        >
          {action.icon && <ListItemIcon>{action.icon}</ListItemIcon>}
          <ListItemText secondary={action.secondary ?? undefined}>{action.label}</ListItemText>
          {action.kind && action.checked && (
            <CheckIcon fontSize="small" color="primary" sx={{ ml: 2 }} aria-hidden />
          )}
          {action.shortcut && (
            <Typography variant="body2" color="text.secondary" sx={{ ml: 2 }} aria-hidden>
              {action.shortcut.label}
            </Typography>
          )}
        </MenuItem>,
      ])}
    </Menu>
  );
}
