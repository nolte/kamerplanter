/**
 * The item menu (REQ-053 GP-FR-027, GP-UX-040): the same menu opens at the pointer on a right
 * click (mouse and pen) and under the "⋯" button of the panel (touch has no context menu). The
 * caller decides which actions exist; every entry is at least 48 px high.
 */
import type { ReactNode } from 'react';
import Divider from '@mui/material/Divider';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';

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
}

interface ContextMenuProps {
  anchor: MenuAnchor | null;
  actions: readonly MenuAction[];
  onClose: () => void;
  label: string;
  testId?: string;
}

export function ContextMenu({
  anchor,
  actions,
  onClose,
  label,
  testId = 'garden-plan-menu',
}: ContextMenuProps) {
  return (
    <Menu
      open={anchor !== null}
      onClose={onClose}
      anchorReference={anchor?.kind === 'position' ? 'anchorPosition' : 'anchorEl'}
      anchorPosition={anchor?.kind === 'position' ? { top: anchor.y, left: anchor.x } : undefined}
      anchorEl={anchor?.kind === 'element' ? anchor.element : undefined}
      slotProps={{
        list: { 'aria-label': label, dense: false },
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
          sx={{ minHeight: 48 }}
          data-testid={`garden-plan-menu-${action.id}`}
        >
          {action.icon && <ListItemIcon>{action.icon}</ListItemIcon>}
          <ListItemText>{action.label}</ListItemText>
        </MenuItem>,
      ])}
    </Menu>
  );
}
