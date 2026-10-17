/**
 * The touch action bars of the editor (REQ-053 GP-UX-036/037, WP 2.6). While a draw tool is active
 * the bar offers "set point · undo · finish · cancel" (each at least 48 px) - the crosshair in the
 * middle of the plan marks where "set point" puts the point, and two fingers pan the plan under
 * it. With the select tool it offers the multi-select switch: while on, every tap adds or removes
 * an object and a drag on empty ground draws a selection frame (otherwise it pans).
 */
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import ToggleButton from '@mui/material/ToggleButton';
import AddLocationAltOutlinedIcon from '@mui/icons-material/AddLocationAltOutlined';
import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';
import UndoIcon from '@mui/icons-material/Undo';
import PlaylistAddCheckIcon from '@mui/icons-material/PlaylistAddCheck';
import type { PlanTool } from '../state/gardenPlanSlice';
import type { DrawShape } from './tools/drawMachine';

const TARGET_PX = 48;
const PREFIX = 'pages.gardenPlan.editor.touch';

interface TouchBarProps {
  tool: PlanTool;
  drawShape: DrawShape;
  draftPoints: number;
  onPlacePoint: () => void;
  onUndoPoint: () => void;
  onFinish: () => void;
  onCancel: () => void;
  multiSelect: boolean;
  onMultiSelect: (on: boolean) => void;
}

const buttonSx = { minWidth: TARGET_PX, minHeight: TARGET_PX } as const;

export function TouchBar({
  tool,
  drawShape,
  draftPoints,
  onPlacePoint,
  onUndoPoint,
  onFinish,
  onCancel,
  multiSelect,
  onMultiSelect,
}: TouchBarProps) {
  const { t } = useTranslation();
  const drawing = tool === 'bed' || tool === 'garden_object';
  const pointShape = drawShape === 'polygon' || drawShape === 'polyline';
  const minPoints = drawShape === 'polygon' ? 3 : 2;
  if (!drawing && tool !== 'select') return null;

  return (
    <Paper
      variant="outlined"
      role="toolbar"
      aria-label={t(`${PREFIX}.label`)}
      data-testid="garden-plan-touchbar"
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        p: 0.5,
        flexWrap: 'wrap',
        bgcolor: 'background.paper',
      }}
    >
      {drawing && (
        <>
          <Button
            variant="contained"
            size="small"
            startIcon={<AddLocationAltOutlinedIcon />}
            onClick={onPlacePoint}
            sx={buttonSx}
            data-testid="garden-plan-touch-place"
          >
            {t(`${PREFIX}.place`)}
          </Button>
          <Button
            size="small"
            startIcon={<UndoIcon />}
            onClick={onUndoPoint}
            disabled={draftPoints === 0}
            sx={buttonSx}
            data-testid="garden-plan-touch-undo"
          >
            {t(`${PREFIX}.undo`)}
          </Button>
          {pointShape && (
            <Button
              size="small"
              startIcon={<CheckIcon />}
              onClick={onFinish}
              disabled={draftPoints < minPoints}
              sx={buttonSx}
              data-testid="garden-plan-touch-finish"
            >
              {t(`${PREFIX}.finish`)}
            </Button>
          )}
          <Button
            size="small"
            color="inherit"
            startIcon={<CloseIcon />}
            onClick={onCancel}
            sx={buttonSx}
            data-testid="garden-plan-touch-cancel"
          >
            {t(`${PREFIX}.cancel`)}
          </Button>
        </>
      )}
      {tool === 'select' && (
        <ToggleButton
          value="multi"
          selected={multiSelect}
          size="small"
          onChange={() => onMultiSelect(!multiSelect)}
          sx={{ ...buttonSx, px: 1.5 }}
          data-testid="garden-plan-touch-multi"
        >
          <PlaylistAddCheckIcon sx={{ mr: 0.75 }} />
          {t(`${PREFIX}.multiSelect`)}
        </ToggleButton>
      )}
    </Paper>
  );
}
