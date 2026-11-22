/**
 * The touch action bars of the editor (REQ-053 GP-UX-036/037, WP 2.6). While a draw tool or the measure tool
 * (GP-UX-071) is active the bar offers "set point · undo · finish · cancel" (each at least 48 px; the measure tool's
 * "cancel" clears the measurement) - the crosshair in the middle of the plan marks where "set point" puts the point,
 * and two fingers pan the plan under it. The text tool (GP-UX-071) gets "set point" alone: its anchor at the
 * crosshair, then the text dialog. Which section a tool gets comes from the tool registry. With the select tool it offers the multi-select switch: while on, every tap adds or removes
 * an object and a drag on empty ground draws a selection frame (otherwise it pans). Below md it also carries
 * undo and redo at its start (`leading`, REQ-053 §17.3 GP-UX-052/063): the header bar there keeps only
 * "back", the save status, "Save" and its overflow.
 */
import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import ToggleButton from '@mui/material/ToggleButton';
import AddLocationAltOutlinedIcon from '@mui/icons-material/AddLocationAltOutlined';
import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';
import UndoIcon from '@mui/icons-material/Undo';
import PlaylistAddCheckIcon from '@mui/icons-material/PlaylistAddCheck';
import type { PlanTool } from '../state/gardenPlanSlice';
import type { DrawShape } from './tools/drawMachine';
import { behaviourOf, TOOL_DEFS } from './toolRegistry';
import { unavailableProps } from './unavailable';

const TARGET_PX = 48;
const PREFIX = 'pages.gardenPlan.editor.touch';

interface TouchBarProps {
  tool: PlanTool;
  /**
   * The point actions are offered - a shape is drawn (a bed, a garden object, the boundary #2890) or a distance is
   * measured; default: the tools whose kind has the touch section `points` in the registry.
   */
  drawing?: boolean;
  /** The measurement can be finished (measure tool only; it is finished once and then cleared or restarted). */
  measureFinishable?: boolean;
  drawShape: DrawShape;
  draftPoints: number;
  onPlacePoint: () => void;
  onUndoPoint: () => void;
  onFinish: () => void;
  onCancel: () => void;
  multiSelect: boolean;
  onMultiSelect: (on: boolean) => void;
  /** Controls at the start of the bar, whatever the tool: undo and redo below md. */
  leading?: ReactNode;
}

const buttonSx = { minWidth: TARGET_PX, minHeight: TARGET_PX } as const;

export function TouchBar({
  tool,
  drawing: drawingProp,
  measureFinishable = false,
  drawShape,
  draftPoints,
  onPlacePoint,
  onUndoPoint,
  onFinish,
  onCancel,
  multiSelect,
  onMultiSelect,
  leading,
}: TouchBarProps) {
  const { t } = useTranslation();
  const { kind } = TOOL_DEFS[tool];
  const touch = behaviourOf(kind).touch;
  const drawing = drawingProp ?? touch === 'points';
  // The text tool sets one anchor (GP-UX-071): "set point" alone - there is nothing to undo, finish or clear.
  const placing = !drawing && touch === 'place';
  const selecting = touch === 'select';
  // A measurement is a line of points: always finished by "Finish", from two points on, and only once.
  const measuring = kind === 'measure';
  const pointShape = measuring || drawShape === 'polygon' || drawShape === 'polyline';
  const minPoints = drawShape === 'polygon' && !measuring ? 3 : 2;
  const canFinish = measuring ? measureFinishable : draftPoints >= minPoints;
  if (!drawing && !placing && !selecting && !leading) return null;

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
      {leading}
      {placing && (
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
      )}
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
            // No point left / too few points: no-op, the focus stays (GP-NFR-070).
            onClick={draftPoints === 0 ? undefined : onUndoPoint}
            {...unavailableProps(draftPoints === 0)}
            sx={buttonSx}
            data-testid="garden-plan-touch-undo"
          >
            {t(`${PREFIX}.undo`)}
          </Button>
          {pointShape && (
            <Button
              size="small"
              startIcon={<CheckIcon />}
              onClick={canFinish ? onFinish : undefined}
              {...unavailableProps(!canFinish)}
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
            {t(measuring ? `${PREFIX}.clear` : `${PREFIX}.cancel`)}
          </Button>
        </>
      )}
      {selecting && (
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
      {selecting && multiSelect && (
        <Typography
          variant="body2"
          color="text.secondary"
          role="status"
          sx={{ flex: '1 1 12rem', px: 0.5 }}
          data-testid="garden-plan-touch-multi-hint"
        >
          {t(`${PREFIX}.multiSelectOn`)}
        </Typography>
      )}
    </Paper>
  );
}
