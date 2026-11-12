/**
 * The "Align" menu of the tool bar (REQ-053 GP-FR-029): align the selected objects to their left / right / top /
 * bottom edge or their centre, or spread them with equal gaps. Every entry is one undo step; an entry is
 * disabled while the selection cannot do it (two objects align, three distribute; locked ones do not count).
 * It belongs to the selection group of the tool bar (GP-UX-066, WP 10.4): on the narrow rail the button shows
 * its icon only (`textSx` hides the text), its name and tooltip stay.
 */
import { useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Tooltip, { type TooltipProps } from '@mui/material/Tooltip';
import type { SxProps, Theme } from '@mui/material/styles';
import AlignHorizontalLeftIcon from '@mui/icons-material/AlignHorizontalLeft';
import type { AlignMode, DistributeAxis } from './tools/align';
import { unavailableProps } from './unavailable';

const PREFIX = 'pages.gardenPlan.editor.align';
const TARGET_PX = 48;

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
  fullWidth?: boolean;
  /** The text next to the icon; hidden where the bar is narrow (the name stays in `aria-label`). */
  textSx?: SxProps<Theme>;
  tooltipPlacement?: TooltipProps['placement'];
}

export function AlignMenu({
  canAlign,
  canDistribute,
  onAlign,
  onDistribute,
  fullWidth = false,
  textSx = { ml: 0.75 },
  tooltipPlacement = 'top',
}: AlignMenuProps) {
  const { t } = useTranslation();
  const id = useId();
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const close = () => setAnchor(null);
  return (
    <>
      <Tooltip title={t(`${PREFIX}.hint`)} placement={tooltipPlacement}>
        {/* An unavailable button takes no pointer: the span carries the tooltip (two objects are needed to align). It is
            aria-disabled, not disabled, so it keeps the focus and stays a tool bar item (GP-NFR-070). */}
        <Box component="span" sx={{ display: fullWidth ? 'block' : 'inline-block' }}>
          <Button
            size="small"
            fullWidth={fullWidth}
            onClick={canAlign ? (event) => setAnchor(event.currentTarget) : undefined}
            {...unavailableProps(!canAlign)}
            aria-label={t(`${PREFIX}.button`)}
            aria-haspopup="menu"
            aria-expanded={anchor !== null}
            aria-controls={anchor ? id : undefined}
            data-testid="garden-plan-align-button"
            sx={{ minWidth: TARGET_PX, minHeight: TARGET_PX }}
          >
            <AlignHorizontalLeftIcon />
            <Box component="span" sx={textSx}>
              {t(`${PREFIX}.button`)}
            </Box>
          </Button>
        </Box>
      </Tooltip>
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
