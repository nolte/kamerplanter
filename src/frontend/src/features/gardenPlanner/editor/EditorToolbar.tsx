/**
 * The tool bar of the garden plan editor (REQ-053 GP-UX-001/010/066, §17.3; WP 2.4, WP 10.4).
 *
 * From md up it is a vertical rail left of the canvas (`orientation="vertical"`); below md the same tree is the bar
 * docked at the bottom edge next to the `TouchBar` (`orientation="horizontal"`, GP-UX-069). Top level: the tools of
 * GP-UX-001 that exist - select, pan ("Verschieben"), area, bed, garden object, plant ("Pflanze setzen") and measure
 * (area, plant and measure from GP-UX-071), read from the tool registry (`toolRegistry.ts`); area, bed and garden object open a sub-menu (at most
 * two levels) with "From template" (bed only, GP-FR-044) and "Add with dimensions" (GP-UX-046). Below them
 * the options of the tool that is on (shape, finish / cancel a drawing, polygon points) and the **selection group**
 * (rotate step, align, delete) - rendered only while something is selected, never as disabled buttons (AC-4).
 * Docked below md the selection group is one row that never wraps: align and delete stay in it, the rotation step -
 * a setting, not an action on the selection - is an entry of the header bar's overflow "⋮" there (`GardenPlanEditor`,
 * #2904; "no wrapping bars - what does not fit moves into the overflow", §17.3). A wrapping group grew past the
 * bottom edge of a phone and cut "Delete" off.
 *
 * The bar is one tab stop with a roving tabindex (arrow keys of its orientation, Home/End). Every target is at least
 * 48 px (UI-NFR-001 R-011); every control has a tooltip that names its verb (GP-UX-010), and on wide screens (xl,
 * 1440 px up) the rail shows the tools' short text as well - below that the canvas needs the width more.
 */
import { useMemo, useRef, useState, type ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import Paper from '@mui/material/Paper';
import ToggleButton from '@mui/material/ToggleButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AddBoxOutlinedIcon from '@mui/icons-material/AddBoxOutlined';
import AddLocationAltOutlinedIcon from '@mui/icons-material/AddLocationAltOutlined';
import ArrowDropUpIcon from '@mui/icons-material/ArrowDropUp';
import ArrowRightIcon from '@mui/icons-material/ArrowRight';
import CropSquareIcon from '@mui/icons-material/CropSquare';
import DashboardCustomizeOutlinedIcon from '@mui/icons-material/DashboardCustomizeOutlined';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import PentagonIcon from '@mui/icons-material/Pentagon';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import TimelineIcon from '@mui/icons-material/Timeline';
import type { PlanTool } from '../state/gardenPlanSlice';
import { AlignMenu } from './AlignMenu';
import { ContextMenu, type MenuAction, type MenuAnchor } from './ContextMenu';
import { MenuTriggerTooltip } from './MenuTriggerTooltip';
import type { DimensionTarget } from './tools/addDimensions';
import type { AlignMode, DistributeAxis } from './tools/align';
import type { DrawShape } from './tools/drawMachine';
import { RAIL_TOOLS, TOOL_DEFS, type RailTool } from './toolRegistry';
import { unavailableProps } from './unavailable';
import { useRovingToolbar, type ToolbarOrientation } from './useRovingToolbar';

const TARGET_PX = 48;
const PREFIX = 'pages.gardenPlan.editor';

/** The tools in the bar: every tool of the registry with a rail button (GP-UX-001, GP-UX-071). */
export type EditorTool = RailTool;
/** The tools whose sub-menu has entries here (GP-UX-001: at most two levels). */
type MenuTool = Extract<EditorTool, 'area' | 'bed' | 'garden_object'>;

/** "Add with dimensions" per sub-menu: the bed entry keeps the test id of the former button (GP-UX-070). */
const DIMENSIONS_TEST_ID: Record<MenuTool, string> = {
  area: 'garden-plan-add-with-dimensions-area',
  bed: 'garden-plan-add-with-dimensions',
  garden_object: 'garden-plan-add-with-dimensions-object',
};

export const ANGLE_STEPS = [15, 45, 90] as const;
export type AngleStep = (typeof ANGLE_STEPS)[number];

/** The selection group of the bar (GP-UX-066): present only while something is selected. */
export interface ToolbarSelectionGroup {
  /** The rotation step; on the rail only - below md it is an entry of the header bar's overflow (#2904). */
  angleStep: AngleStep;
  onAngleStep: (step: AngleStep) => void;
  onDelete: () => void;
  /** Align / distribute the selection (GP-FR-029); absent = not offered. */
  align?: {
    canAlign: boolean;
    canDistribute: boolean;
    onAlign: (mode: AlignMode) => void;
    onDistribute: (axis: DistributeAxis) => void;
  };
}

interface EditorToolbarProps {
  /** `vertical`: the rail left of the canvas (md up); `horizontal`: the bar docked at the bottom (below md). */
  orientation: ToolbarOrientation;
  tool: PlanTool;
  onTool: (tool: EditorTool) => void;
  drawShape: DrawShape;
  onDrawShape: (shape: DrawShape) => void;
  /** Points placed so far by a polygon or polyline being drawn. */
  draftPoints: number;
  onFinishDraw: () => void;
  onCancelDraw: () => void;
  /** A polygon/polyline point is picked (GP-FR-023). */
  vertexPicked: boolean;
  canDeleteVertex: boolean;
  onDeleteVertex: () => void;
  onInsertVertex: () => void;
  /** "Bed ▸ From template" (GP-FR-044): the template tool is on. Absent = the entry is not offered. */
  templateActive?: boolean;
  onTemplate?: () => void;
  /** "Bed ▸ / Garden object ▸ Add with dimensions" (GP-UX-046); absent = not offered. */
  onAddWithDimensions?: (target: DimensionTarget) => void;
  /** The selection group; `null` while nothing is selected - then it is not rendered at all (AC-4). */
  selectionGroup: ToolbarSelectionGroup | null;
  /**
   * The boundary mode of the overflow (#2890): `draw` offers the boundary's shapes (rect, polygon) and the drawing
   * controls here; no top-level tool is pressed meanwhile - the mode is no tool of the rail (GP-UX-001).
   */
  boundaryMode?: 'draw' | 'edit' | null;
  /**
   * The measure tool's path without a pointer (GP-UX-071, WCAG 2.1.1): "Set point" puts a point at the crosshair in
   * the middle of the plan, "Finish" ends the measurement. `onAim` tells the editor to show the crosshair (the button
   * got the focus or was used). Absent = not offered; shown only while the measure tool is on.
   */
  measure?: { finishable: boolean; onPlace: () => void; onFinish: () => void; onAim: () => void };
  /**
   * Tools the user may not use and that are therefore not offered at all (never as a disabled button, AC-4): a viewer
   * does not get "Pflanze setzen", which writes a plant (REQ-049, GP-UX-071).
   */
  hiddenTools?: ReadonlySet<EditorTool>;
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
  const { orientation, onTemplate, templateActive, onAddWithDimensions, measure } = props;
  const measuring = TOOL_DEFS[props.tool].kind === 'measure';
  const vertical = orientation === 'vertical';
  const barRef = useRef<HTMLDivElement | null>(null);
  const roving = useRovingToolbar(barRef, orientation);
  // The tool keeps its menu while the menu fades out; `anchor` is null once it is closed.
  const [menu, setMenu] = useState<{ tool: MenuTool; anchor: MenuAnchor | null } | null>(null);

  const menuActions = useMemo<MenuAction[]>(() => {
    if (!menu) return [];
    const actions: MenuAction[] = [];
    if (menu.tool === 'bed' && onTemplate) {
      actions.push({
        id: 'template',
        label: t(`${PREFIX}.templates.tool.short`),
        secondary: t(`${PREFIX}.templates.tool.hint`),
        icon: <DashboardCustomizeOutlinedIcon fontSize="small" />,
        onClick: onTemplate,
        kind: 'checkbox',
        checked: templateActive === true,
        testId: 'garden-plan-tool-template',
      });
    }
    if (onAddWithDimensions) {
      const target: DimensionTarget = menu.tool;
      actions.push({
        id: 'addWithDimensions',
        label: t(`${PREFIX}.addWithDimensions.open`),
        secondary: t(`${PREFIX}.tools.${menu.tool}.dimensionsHint`),
        icon: <AddBoxOutlinedIcon fontSize="small" />,
        onClick: () => onAddWithDimensions(target),
        testId: DIMENSIONS_TEST_ID[menu.tool],
      });
    }
    return actions;
  }, [menu, onAddWithDimensions, onTemplate, t, templateActive]);

  // A tool with a sub-menu in the registry shows its button only when the menu has an entry to offer.
  const hasMenu = (tool: EditorTool): tool is MenuTool =>
    TOOL_DEFS[tool].menu === true &&
    ((tool === 'bed' && (onTemplate !== undefined || onAddWithDimensions !== undefined)) ||
      ((tool === 'area' || tool === 'garden_object') && onAddWithDimensions !== undefined));

  const boundaryDraw = props.boundaryMode === 'draw';
  const drawDef = TOOL_DEFS[props.tool].draw;
  // The shapes offered come from the registry (§9.5): a bed is an area, only a garden object can be a line, the
  // boundary is a rect or a polygon. The boundary mode offers them only while it draws.
  const drawing = drawDef !== undefined && (TOOL_DEFS[props.tool].kind === 'draw' || boundaryDraw);
  const shapes = SHAPES.filter((entry) => drawDef?.shapes.includes(entry.shape));
  const pointShape = props.drawShape === 'polygon' || props.drawShape === 'polyline';
  const minPoints = props.drawShape === 'polygon' ? 3 : 2;
  const finishReady = props.draftPoints >= minPoints;
  const group = props.selectionGroup;

  // The rail shows the tools' short text on wide screens (xl); the bar docked below md stays with icons (its row is
  // short). Below xl the rail is two 48 px targets wide: the canvas next to a docked panel needs the width more.
  const shortSx = { display: { xs: 'none', xl: vertical ? 'inline' : 'none' }, ml: 0.75 } as const;
  // Actions with text (align, delete): an icon on the narrow rail, the text from xl up, and always on the docked bar.
  const actionTextSx = vertical ? ({ display: { xs: 'none', xl: 'inline' }, ml: 0.75 } as const) : { ml: 0.75 };
  const tooltipPlacement = vertical ? 'right' : 'top';
  const stackSx = vertical
    ? ({ display: 'flex', flexDirection: 'column', gap: 0.5 } as const)
    : ({ display: 'flex', alignItems: 'center', gap: 0.5 } as const);
  const wrapSx = { display: 'flex', gap: 0.5, flexWrap: 'wrap' } as const;
  // Docked below md the selection group is one row that never wraps (#2904).
  const selectionRowSx = { display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'nowrap', flex: 'none' } as const;
  const divider = (
    <Divider orientation={vertical ? 'horizontal' : 'vertical'} flexItem sx={vertical ? { my: 0.25 } : undefined} />
  );

  return (
    <Paper
      ref={barRef}
      variant="outlined"
      role="toolbar"
      aria-orientation={orientation}
      aria-label={t(`${PREFIX}.toolbar.label`)}
      data-testid="garden-plan-toolbar"
      data-orientation={orientation}
      onKeyDown={roving.onKeyDown}
      onFocus={roving.onFocus}
      sx={
        vertical
          ? {
              display: 'flex',
              flexDirection: 'column',
              gap: 0.5,
              p: 0.5,
              // Two 48 px targets side by side (a tool and its sub-menu); the short texts need more from xl up.
              width: { xs: 112, xl: 176 },
              flex: 'none',
              height: '100%',
              boxSizing: 'border-box',
              // The rail never pushes the page: a long selection group scrolls inside it.
              overflowY: 'auto',
              overflowX: 'hidden',
              bgcolor: 'background.paper',
            }
          : {
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              p: 0.5,
              // Wrap instead of scrolling sideways: a control scrolled out of sight cannot be used.
              flexWrap: 'wrap',
              bgcolor: 'background.paper',
            }
      }
    >
      <Box role="group" aria-label={t(`${PREFIX}.toolbar.tools`)} sx={stackSx}>
        {RAIL_TOOLS.filter(({ tool }) => !props.hiddenTools?.has(tool)).map(({ tool, icon: Icon }) => {
          // While the template tool is on no other tool is: clicking "Select" must register as a change.
          const pressed = !templateActive && props.tool === tool;
          const menuOpen = menu?.tool === tool && menu.anchor !== null;
          return (
            <Box key={tool} sx={{ display: 'flex', gap: 0.5 }}>
              <Tooltip title={t(`${PREFIX}.tools.${tool}.hint`)} placement={tooltipPlacement}>
                <ToggleButton
                  value={tool}
                  size="small"
                  selected={pressed}
                  onChange={() => props.onTool(tool)}
                  aria-label={t(`${PREFIX}.tools.${tool}.label`)}
                  data-testid={`garden-plan-tool-${tool}`}
                  sx={{
                    ...buttonSx,
                    flex: 1,
                    justifyContent: vertical ? { xs: 'center', xl: 'flex-start' } : 'center',
                  }}
                >
                  <Icon />
                  <Box component="span" sx={shortSx}>
                    {t(`${PREFIX}.tools.${tool}.short`)}
                  </Box>
                </ToggleButton>
              </Tooltip>
              {hasMenu(tool) && (
                <MenuTriggerTooltip
                  title={t(`${PREFIX}.tools.${tool}.more`)}
                  placement={tooltipPlacement}
                  menuOpen={menuOpen}
                >
                  <Button
                    size="small"
                    color="inherit"
                    aria-label={t(`${PREFIX}.tools.${tool}.more`)}
                    aria-haspopup="menu"
                    aria-expanded={menuOpen}
                    aria-controls={menuOpen ? `garden-plan-tool-${tool}-submenu-list` : undefined}
                    onClick={(event) => setMenu({ tool, anchor: { kind: 'element', element: event.currentTarget } })}
                    data-testid={`garden-plan-tool-${tool}-menu`}
                    sx={{ ...buttonSx, p: 0, flex: 'none' }}
                  >
                    {vertical ? <ArrowRightIcon /> : <ArrowDropUpIcon />}
                  </Button>
                </MenuTriggerTooltip>
              )}
            </Box>
          );
        })}
      </Box>

      {drawing && (
        <>
          {divider}
          <Box role="group" aria-label={t(`${PREFIX}.toolbar.shapes`)} sx={wrapSx}>
            {shapes.map(({ shape, icon }) => (
              <Tooltip key={shape} title={t(`${PREFIX}.shapes.${shape}.hint`)} placement={tooltipPlacement}>
                <ToggleButton
                  value={shape}
                  size="small"
                  selected={props.drawShape === shape}
                  onChange={() => props.onDrawShape(shape)}
                  aria-label={t(`${PREFIX}.shapes.${shape}.label`)}
                  data-testid={`garden-plan-shape-${shape}`}
                  sx={buttonSx}
                >
                  {icon}
                </ToggleButton>
              </Tooltip>
            ))}
          </Box>
        </>
      )}

      {drawing && pointShape && (
        <Tooltip
          title={
            finishReady ? t(`${PREFIX}.draw.finishHint`) : t(`${PREFIX}.draw.finishDisabled`, { count: minPoints })
          }
          placement={tooltipPlacement}
        >
          <Box component="span" sx={{ display: vertical ? 'block' : 'inline-block' }}>
            <Button
              variant="contained"
              size="small"
              fullWidth={vertical}
              // Too few points, or the shape just finished: no-op, the focus stays (GP-NFR-070).
              onClick={finishReady ? props.onFinishDraw : undefined}
              {...unavailableProps(!finishReady)}
              data-testid="garden-plan-draw-finish"
              sx={buttonSx}
            >
              {t(`${PREFIX}.draw.finish`)}
            </Button>
          </Box>
        </Tooltip>
      )}
      {measuring && measure && (
        <Box role="group" aria-label={t(`${PREFIX}.measure.group`)} sx={stackSx}>
          <Tooltip title={t(`${PREFIX}.measure.placeHint`)} placement={tooltipPlacement}>
            <Button
              variant="contained"
              size="small"
              fullWidth={vertical}
              startIcon={<AddLocationAltOutlinedIcon />}
              onFocus={measure.onAim}
              onClick={() => {
                measure.onAim();
                measure.onPlace();
              }}
              data-testid="garden-plan-measure-place"
              sx={{ ...buttonSx, whiteSpace: 'nowrap' }}
            >
              {t(`${PREFIX}.measure.place`)}
            </Button>
          </Tooltip>
          <Tooltip
            title={t(`${PREFIX}.measure.${measure.finishable ? 'finishHint' : 'finishDisabled'}`)}
            placement={tooltipPlacement}
          >
            <Box component="span" sx={{ display: vertical ? 'block' : 'inline-block' }}>
              <Button
                size="small"
                fullWidth={vertical}
                // Fewer than two points, or already finished: no-op, the focus stays (GP-NFR-070).
                onClick={measure.finishable ? measure.onFinish : undefined}
                {...unavailableProps(!measure.finishable)}
                data-testid="garden-plan-measure-finish"
                sx={buttonSx}
              >
                {t(`${PREFIX}.measure.finish`)}
              </Button>
            </Box>
          </Tooltip>
        </Box>
      )}
      {props.draftPoints > 0 && (
        <Button
          size="small"
          fullWidth={vertical}
          onClick={props.onCancelDraw}
          data-testid="garden-plan-draw-cancel"
          sx={buttonSx}
        >
          {/* The measure tool's points are a measurement, not a draft: the button clears it (GP-UX-071). */}
          {t(measuring ? `${PREFIX}.measure.clear` : `${PREFIX}.draw.cancel`)}
        </Button>
      )}

      {props.vertexPicked && (
        <Box sx={stackSx}>
          <Button
            size="small"
            fullWidth={vertical}
            onClick={props.onInsertVertex}
            data-testid="garden-plan-vertex-insert"
            sx={buttonSx}
          >
            {t(`${PREFIX}.vertex.insert`)}
          </Button>
          <Button
            size="small"
            fullWidth={vertical}
            onClick={props.canDeleteVertex ? props.onDeleteVertex : undefined}
            {...unavailableProps(!props.canDeleteVertex)}
            data-testid="garden-plan-vertex-delete"
            sx={buttonSx}
          >
            {t(`${PREFIX}.vertex.delete`)}
          </Button>
        </Box>
      )}

      {group && (
        <>
          {vertical ? divider : <Box sx={{ flexGrow: 1 }} />}
          <Box
            role="group"
            aria-label={t(`${PREFIX}.toolbar.selection`)}
            data-testid="garden-plan-selection-group"
            // Below md the rotation step is in the header bar's overflow, so the row fits a phone.
            sx={vertical ? stackSx : selectionRowSx}
          >
            {vertical && (
              <>
                <Typography variant="caption" color="text.secondary" sx={{ px: 0.5 }} aria-hidden>
                  {t(`${PREFIX}.toolbar.rotate`)}
                </Typography>
                <Box role="group" aria-label={t(`${PREFIX}.toolbar.angleStep`)} sx={wrapSx}>
                  {ANGLE_STEPS.map((step) => (
                    <Tooltip key={step} title={t(`${PREFIX}.angleStep.hint`, { step })} placement={tooltipPlacement}>
                      <ToggleButton
                        value={step}
                        size="small"
                        selected={group.angleStep === step}
                        onChange={() => group.onAngleStep(step)}
                        aria-label={t(`${PREFIX}.angleStep.label`, { step })}
                        data-testid={`garden-plan-angle-${step}`}
                        sx={{ ...buttonSx, px: 1 }}
                      >
                        {step}°
                      </ToggleButton>
                    </Tooltip>
                  ))}
                </Box>
              </>
            )}
            {group.align && (
              <AlignMenu
                canAlign={group.align.canAlign}
                canDistribute={group.align.canDistribute}
                onAlign={group.align.onAlign}
                onDistribute={group.align.onDistribute}
                fullWidth={vertical}
                textSx={actionTextSx}
                tooltipPlacement={tooltipPlacement}
              />
            )}
            <Tooltip title={t(`${PREFIX}.delete.hint`)} placement={tooltipPlacement}>
              <Button
                size="small"
                color="error"
                fullWidth={vertical}
                onClick={group.onDelete}
                aria-label={t(`${PREFIX}.delete.label`)}
                data-testid="garden-plan-delete-button"
                sx={{ ...buttonSx, whiteSpace: 'nowrap' }}
              >
                <DeleteOutlinedIcon />
                <Box component="span" sx={actionTextSx}>
                  {t(`${PREFIX}.delete.label`)}
                </Box>
              </Button>
            </Tooltip>
          </Box>
        </>
      )}

      <ContextMenu
        anchor={menu?.anchor ?? null}
        actions={menuActions}
        onClose={() => setMenu((previous) => (previous ? { ...previous, anchor: null } : previous))}
        label={menu ? t(`${PREFIX}.tools.${menu.tool}.menu`) : t(`${PREFIX}.toolbar.label`)}
        testId={menu ? `garden-plan-tool-${menu.tool}-submenu` : undefined}
        id={menu ? `garden-plan-tool-${menu.tool}-submenu-list` : undefined}
      />
    </Paper>
  );
}
