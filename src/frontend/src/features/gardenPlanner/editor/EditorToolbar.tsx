/**
 * The tool bar of the garden plan editor (REQ-053 GP-UX-001/010, WP 2.4): select, pan, bed and
 * garden object tools, the shape of what is drawn, the rotate-snap step and the actions that need
 * a button because they have no gesture on touch (finish, cancel, delete, polygon points). On
 * desktop it sits above the plan, on xs it sticks to the bottom edge where the thumb is. Every
 * target is at least 44 px; every tool has a tooltip with its verb.
 */
import { useMemo, type ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import Paper from '@mui/material/Paper';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Tooltip from '@mui/material/Tooltip';
import CropSquareIcon from '@mui/icons-material/CropSquare';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import NearMeIcon from '@mui/icons-material/NearMe';
import PanToolIcon from '@mui/icons-material/PanTool';
import ParkIcon from '@mui/icons-material/Park';
import PentagonIcon from '@mui/icons-material/Pentagon';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import TimelineIcon from '@mui/icons-material/Timeline';
import YardIcon from '@mui/icons-material/Yard';
import type { PlanTool } from '../state/gardenPlanSlice';
import type { DrawShape } from './tools/drawMachine';

const TARGET_PX = 44;

/** The tools in the bar; the rest of `PlanTool` arrives with later work packages. */
export type EditorTool = Extract<PlanTool, 'select' | 'pan' | 'bed' | 'garden_object'>;

export const ANGLE_STEPS = [15, 45, 90] as const;
export type AngleStep = (typeof ANGLE_STEPS)[number];

interface EditorToolbarProps {
  tool: PlanTool;
  onTool: (tool: EditorTool) => void;
  drawShape: DrawShape;
  onDrawShape: (shape: DrawShape) => void;
  angleStep: AngleStep;
  onAngleStep: (step: AngleStep) => void;
  /** Points placed so far by a polygon or polyline being drawn. */
  draftPoints: number;
  onFinishDraw: () => void;
  onCancelDraw: () => void;
  /** A location or garden object is selected. */
  canDelete: boolean;
  onDelete: () => void;
  /** A polygon/polyline point is picked (GP-FR-023). */
  vertexPicked: boolean;
  canDeleteVertex: boolean;
  onDeleteVertex: () => void;
  onInsertVertex: () => void;
}

const SHAPES: { shape: DrawShape; icon: ReactElement }[] = [
  { shape: 'rect', icon: <CropSquareIcon /> },
  { shape: 'circle', icon: <RadioButtonUncheckedIcon /> },
  { shape: 'polygon', icon: <PentagonIcon /> },
  { shape: 'polyline', icon: <TimelineIcon /> },
];

const buttonSx = { minWidth: TARGET_PX, minHeight: TARGET_PX } as const;

export function EditorToolbar(props: EditorToolbarProps) {
  const { t } = useTranslation();
  const tools = useMemo(
    () => [
      { tool: 'select' as const, icon: <NearMeIcon /> },
      { tool: 'pan' as const, icon: <PanToolIcon /> },
      { tool: 'bed' as const, icon: <YardIcon /> },
      { tool: 'garden_object' as const, icon: <ParkIcon /> },
    ],
    [],
  );
  const drawing = props.tool === 'bed' || props.tool === 'garden_object';
  // A bed is an area; only a garden object can be a line.
  const shapes = SHAPES.filter(
    (entry) => props.tool === 'garden_object' || entry.shape !== 'polyline',
  );
  const pointShape = props.drawShape === 'polygon' || props.drawShape === 'polyline';
  const minPoints = props.drawShape === 'polygon' ? 3 : 2;
  const finishReady = props.draftPoints >= minPoints;
  const prefix = 'pages.gardenPlan.editor';

  return (
    <Paper
      variant="outlined"
      role="toolbar"
      aria-label={t(`${prefix}.toolbar.label`)}
      data-testid="garden-plan-toolbar"
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        p: 0.5,
        // Wrap instead of scrolling sideways: a control scrolled out of sight cannot be used.
        flexWrap: 'wrap',
        // Thumb reach: the bar docks to the bottom of the screen on phones. The editor puts it
        // after the canvas in the DOM there, so the tab order matches what is on screen (WCAG 2.4.3).
        position: { xs: 'sticky', md: 'static' },
        bottom: 0,
        zIndex: 2,
        bgcolor: 'background.paper',
      }}
    >
      <ToggleButtonGroup
        exclusive
        size="small"
        value={props.tool}
        aria-label={t(`${prefix}.toolbar.tools`)}
        onChange={(_event, next: EditorTool | null) => {
          if (next) props.onTool(next);
        }}
      >
        {tools.map(({ tool, icon }) => (
          <Tooltip key={tool} title={t(`${prefix}.tools.${tool}.hint`)}>
            <ToggleButton
              value={tool}
              aria-label={t(`${prefix}.tools.${tool}.label`)}
              data-testid={`garden-plan-tool-${tool}`}
              sx={buttonSx}
            >
              {icon}
              <Box component="span" sx={{ display: { xs: 'none', lg: 'inline' }, ml: 0.75 }}>
                {t(`${prefix}.tools.${tool}.short`)}
              </Box>
            </ToggleButton>
          </Tooltip>
        ))}
      </ToggleButtonGroup>

      {drawing && (
        <ToggleButtonGroup
          exclusive
          size="small"
          value={props.drawShape}
          aria-label={t(`${prefix}.toolbar.shapes`)}
          onChange={(_event, next: DrawShape | null) => {
            if (next) props.onDrawShape(next);
          }}
        >
          {shapes.map(({ shape, icon }) => (
            <Tooltip key={shape} title={t(`${prefix}.shapes.${shape}.hint`)}>
              <ToggleButton
                value={shape}
                aria-label={t(`${prefix}.shapes.${shape}.label`)}
                data-testid={`garden-plan-shape-${shape}`}
                sx={buttonSx}
              >
                {icon}
              </ToggleButton>
            </Tooltip>
          ))}
        </ToggleButtonGroup>
      )}

      {props.tool === 'select' && (
        <ToggleButtonGroup
          exclusive
          size="small"
          value={props.angleStep}
          aria-label={t(`${prefix}.toolbar.angleStep`)}
          onChange={(_event, next: AngleStep | null) => {
            if (next) props.onAngleStep(next);
          }}
        >
          {ANGLE_STEPS.map((step) => (
            <Tooltip key={step} title={t(`${prefix}.angleStep.hint`, { step })}>
              <ToggleButton
                value={step}
                aria-label={t(`${prefix}.angleStep.label`, { step })}
                data-testid={`garden-plan-angle-${step}`}
                sx={{ ...buttonSx, px: 1 }}
              >
                {step}°
              </ToggleButton>
            </Tooltip>
          ))}
        </ToggleButtonGroup>
      )}

      {drawing && pointShape && (
        <>
          <Divider orientation="vertical" flexItem />
          <Tooltip
            title={
              finishReady
                ? t(`${prefix}.draw.finishHint`)
                : t(`${prefix}.draw.finishDisabled`, { count: minPoints })
            }
          >
            <span>
              <Button
                variant="contained"
                size="small"
                onClick={props.onFinishDraw}
                disabled={!finishReady}
                data-testid="garden-plan-draw-finish"
                sx={buttonSx}
              >
                {t(`${prefix}.draw.finish`)}
              </Button>
            </span>
          </Tooltip>
        </>
      )}
      {props.draftPoints > 0 && (
        <Button
          size="small"
          onClick={props.onCancelDraw}
          data-testid="garden-plan-draw-cancel"
          sx={buttonSx}
        >
          {t(`${prefix}.draw.cancel`)}
        </Button>
      )}

      {props.vertexPicked && (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Button
            size="small"
            onClick={props.onInsertVertex}
            data-testid="garden-plan-vertex-insert"
            sx={buttonSx}
          >
            {t(`${prefix}.vertex.insert`)}
          </Button>
          <Button
            size="small"
            onClick={props.onDeleteVertex}
            disabled={!props.canDeleteVertex}
            data-testid="garden-plan-vertex-delete"
            sx={buttonSx}
          >
            {t(`${prefix}.vertex.delete`)}
          </Button>
        </Box>
      )}

      <Box sx={{ flexGrow: 1 }} />
      <Tooltip title={t(`${prefix}.delete.hint`)}>
        <span>
          <Button
            size="small"
            color="error"
            startIcon={<DeleteOutlinedIcon />}
            onClick={props.onDelete}
            disabled={!props.canDelete}
            data-testid="garden-plan-delete-button"
            sx={buttonSx}
          >
            {t(`${prefix}.delete.label`)}
          </Button>
        </span>
      </Tooltip>
    </Paper>
  );
}
