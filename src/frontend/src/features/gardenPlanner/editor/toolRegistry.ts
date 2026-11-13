/**
 * The tools of the garden plan editor in one place (REQ-053 GP-UX-001, GP-UX-071, #2913). Every `PlanTool` has one
 * entry: which machine handles the canvas while it is on (`kind`), whether it is a button of the rail (`rail`), and
 * what it draws. What follows from the kind - cursor, snap marker, the touch bar's section - is a property of the kind
 * (`KIND_BEHAVIOUR`), so a new tool of an existing kind is one entry here plus its logic.
 *
 * The rail, the touch bar, the editor and the tool hook read this instead of comparing tool names.
 */
import type { SvgIconComponent } from '@mui/icons-material';
import CropFreeIcon from '@mui/icons-material/CropFree';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import NearMeIcon from '@mui/icons-material/NearMe';
import PanToolIcon from '@mui/icons-material/PanTool';
import ParkIcon from '@mui/icons-material/Park';
import StraightenIcon from '@mui/icons-material/Straighten';
import YardIcon from '@mui/icons-material/Yard';
import type { PlanTool } from '../state/gardenPlanSlice';
import { AREA_SHAPES, BOUNDARY_SHAPES, type DrawShape, type DrawTarget } from './tools/drawMachine';

/**
 * The machine that takes the canvas's pointer and keys while a tool is on. `boundary` is the plan-level boundary mode
 * (#2890): it draws while the plan has no boundary and reshapes it once there is one (see {@link canvasKindOf}).
 * `plant` is a click machine (GP-UX-071, #2913): a click on a free planting spot opens the dialog for it, a drag pans.
 */
export type ToolKind = 'select' | 'pan' | 'draw' | 'measure' | 'plant' | 'boundary';

/** What the kind of the active tool means for the canvas around it. */
export interface KindBehaviour {
  cursor: 'default' | 'grab' | 'crosshair' | 'pointer';
  /** The snap marker follows the pointer: the next click lands on it (GP-FR-154). */
  snapMarker: boolean;
  /**
   * The touch bar's section (GP-UX-036/037): `points` - set point at the crosshair, undo, finish, cancel;
   * `select` - the multi-select switch; `null` - none.
   */
  touch: 'points' | 'select' | null;
}

export const KIND_BEHAVIOUR: Record<Exclude<ToolKind, 'boundary'>, KindBehaviour> = {
  select: { cursor: 'default', snapMarker: false, touch: 'select' },
  pan: { cursor: 'grab', snapMarker: false, touch: null },
  draw: { cursor: 'crosshair', snapMarker: true, touch: 'points' },
  measure: { cursor: 'crosshair', snapMarker: true, touch: 'points' },
  // A tap or click picks a planting spot; there are no points to set, so the touch bar has nothing to offer.
  plant: { cursor: 'pointer', snapMarker: false, touch: null },
};

/** A boundary that exists is reshaped by its handles; a press elsewhere pans (#2890). */
const BOUNDARY_EDIT: KindBehaviour = { cursor: 'default', snapMarker: false, touch: null };

export interface ToolDef {
  kind: ToolKind;
  /** The icon of its rail button; absent = no tool of the rail (the boundary mode is an overflow entry). */
  rail?: SvgIconComponent;
  /** The rail button has a sub-menu (GP-UX-001: at most two levels); its entries are the tool bar's business. */
  menu?: boolean;
  /** A draw tool: what it creates and the shapes it offers (the first is the fallback). */
  draw?: { target: DrawTarget; shapes: readonly DrawShape[] };
}

/** In rail order (GP-UX-001, §17.3): the tools of the rail come first, the boundary mode last. */
export const TOOL_DEFS: Record<PlanTool, ToolDef> = {
  select: { kind: 'select', rail: NearMeIcon },
  pan: { kind: 'pan', rail: PanToolIcon },
  // GP-UX-071: an area location (garden, terrace, greenhouse...) - a rect or a polygon (§9.5); it parents the beds drawn
  // inside it afterwards. Its sub-menu holds "Add with dimensions".
  area: { kind: 'draw', rail: CropFreeIcon, menu: true, draw: { target: 'area', shapes: AREA_SHAPES } },
  // A bed is a surface; only a garden object can be a line (§9.5).
  bed: { kind: 'draw', rail: YardIcon, menu: true, draw: { target: 'bed', shapes: ['rect', 'circle', 'polygon'] } },
  garden_object: {
    kind: 'draw',
    rail: ParkIcon,
    menu: true,
    draw: { target: 'garden_object', shapes: ['rect', 'circle', 'polygon', 'polyline'] },
  },
  // GP-UX-071: one plant into the free point slot clicked; written at once through the plant API, not the plan batch.
  plant: { kind: 'plant', rail: LocalFloristIcon },
  // GP-UX-071: transient - nothing is stored, no plan operation, no undo step.
  measure: { kind: 'measure', rail: StraightenIcon },
  boundary: { kind: 'boundary', draw: { target: 'boundary', shapes: BOUNDARY_SHAPES } },
};

/** A tool with a button on the rail. */
export type RailTool = Exclude<PlanTool, 'boundary'>;

/** The rail's buttons, top to bottom. */
export const RAIL_TOOLS: readonly { tool: RailTool; icon: SvgIconComponent }[] = (
  Object.keys(TOOL_DEFS) as PlanTool[]
).flatMap((tool) => {
  const icon = TOOL_DEFS[tool].rail;
  return icon && tool !== 'boundary' ? [{ tool, icon }] : [];
});

/** The machine that handles the canvas for `tool`; the boundary mode draws until the plan has a boundary (#2890). */
export function canvasKindOf(tool: PlanTool, hasBoundary: boolean): ToolKind {
  const { kind } = TOOL_DEFS[tool];
  if (kind === 'boundary') return hasBoundary ? 'boundary' : 'draw';
  return kind;
}

export function behaviourOf(kind: ToolKind): KindBehaviour {
  return kind === 'boundary' ? BOUNDARY_EDIT : KIND_BEHAVIOUR[kind];
}

/** The canvas cursor; `panModifier`: Space is held on the canvas, a drag pans whatever the tool (GP-FR-010). */
export function cursorOf(behaviour: KindBehaviour, panModifier: boolean): KindBehaviour['cursor'] {
  return panModifier ? 'grab' : behaviour.cursor;
}
