/**
 * The actions row above the plan (REQ-053 GP-UX-046/052): "Add with dimensions" and the "⋯"
 * overflow menu. The overflow holds what has no room on a phone - "select all" now; grid, zoom
 * steps, export and the other work packages' entries join through `extraItems` (every entry is at
 * least 48 px). Save status and undo/redo are NOT in here: they stay visible on every width.
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import AddBoxOutlinedIcon from '@mui/icons-material/AddBoxOutlined';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';
import { ContextMenu, type MenuAction, type MenuAnchor } from './ContextMenu';

const PREFIX = 'pages.gardenPlan.editor';

interface EditorHeaderActionsProps {
  onAddWithDimensions: () => void;
  onSelectAll: () => void;
  extraItems?: readonly MenuAction[];
}

export function EditorHeaderActions({
  onAddWithDimensions,
  onSelectAll,
  extraItems = [],
}: EditorHeaderActionsProps) {
  const { t } = useTranslation();
  const [anchor, setAnchor] = useState<MenuAnchor | null>(null);
  const actions: MenuAction[] = [
    { id: 'selectAll', label: t(`${PREFIX}.contextMenu.selectAll`), onClick: onSelectAll },
    ...extraItems,
  ];
  return (
    <Box
      sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
      data-testid="garden-plan-header-actions"
    >
      <Button
        startIcon={<AddBoxOutlinedIcon />}
        onClick={onAddWithDimensions}
        sx={{ minHeight: 48 }}
        data-testid="garden-plan-add-with-dimensions"
      >
        {t(`${PREFIX}.addWithDimensions.open`)}
      </Button>
      <Box sx={{ flexGrow: 1 }} />
      <Tooltip title={t(`${PREFIX}.contextMenu.overflow`)}>
        <IconButton
          aria-label={t(`${PREFIX}.contextMenu.overflow`)}
          aria-haspopup="menu"
          onClick={(event) => setAnchor({ kind: 'element', element: event.currentTarget })}
          sx={{ width: 48, height: 48 }}
          data-testid="garden-plan-overflow"
        >
          <MoreHorizIcon />
        </IconButton>
      </Tooltip>
      <ContextMenu
        anchor={anchor}
        actions={actions}
        onClose={() => setAnchor(null)}
        label={t(`${PREFIX}.contextMenu.overflow`)}
        testId="garden-plan-overflow-menu"
      />
    </Box>
  );
}
