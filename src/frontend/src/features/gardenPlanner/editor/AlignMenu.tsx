/**
 * The "Align" menu of the tool bar (REQ-053 GP-FR-029): align the selected objects to their left / right / top /
 * bottom edge or their centre, or spread them with equal gaps. Every entry is one undo step; an entry is
 * disabled while the selection cannot do it (two objects align, three distribute; locked ones do not count).
 */
import { useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import AlignHorizontalLeftIcon from '@mui/icons-material/AlignHorizontalLeft';
import type { AlignMode, DistributeAxis } from './tools/align';

const PREFIX = 'pages.gardenPlan.editor.align';
const TARGET_PX = 44;

export const ALIGN_MODES: readonly AlignMode[] = [
  'left',
  'right',
  'top',
  'bottom',
  'centerH',
  'centerV',
];
export const DISTRIBUTE_AXES: readonly DistributeAxis[] = ['horizontal', 'vertical'];

interface AlignMenuProps {
  canAlign: boolean;
  canDistribute: boolean;
  onAlign: (mode: AlignMode) => void;
  onDistribute: (axis: DistributeAxis) => void;
}

export function AlignMenu({ canAlign, canDistribute, onAlign, onDistribute }: AlignMenuProps) {
  const { t } = useTranslation();
  const id = useId();
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const close = () => setAnchor(null);
  return (
    <>
      <Button
        size="small"
        startIcon={<AlignHorizontalLeftIcon />}
        onClick={(event) => setAnchor(event.currentTarget)}
        disabled={!canAlign}
        aria-haspopup="menu"
        aria-expanded={anchor !== null}
        aria-controls={anchor ? id : undefined}
        data-testid="garden-plan-align-button"
        sx={{ minWidth: TARGET_PX, minHeight: TARGET_PX }}
      >
        {t(`${PREFIX}.button`)}
      </Button>
      <Menu
        id={id}
        anchorEl={anchor}
        open={anchor !== null}
        onClose={close}
        slotProps={{ list: { 'aria-label': t(`${PREFIX}.label`) } }}
      >
        {ALIGN_MODES.map((mode) => (
          <MenuItem
            key={mode}
            sx={{ minHeight: 48 }}
            data-testid={`garden-plan-align-${mode}`}
            onClick={() => {
              close();
              onAlign(mode);
            }}
          >
            {t(`${PREFIX}.mode.${mode}`)}
          </MenuItem>
        ))}
        <Divider />
        {DISTRIBUTE_AXES.map((axis) => (
          <MenuItem
            key={axis}
            sx={{ minHeight: 48 }}
            disabled={!canDistribute}
            data-testid={`garden-plan-distribute-${axis}`}
            onClick={() => {
              close();
              onDistribute(axis);
            }}
          >
            {t(`${PREFIX}.distribute.${axis}`)}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
}
