/**
 * The garden plan editor (REQ-053 WP 2.4): the canvas with its tools, handles and overlay, the tool
 * bar and the delete confirmation. It reads and writes the plan only through the Redux slice
 * (`applyAction` - one user action is one undo step) and reaches the renderer only through the
 * `PlanRenderer` interface the route hands in (GP-NFR-009). Grid, snap, zoom, scale bar, compass and
 * dimension text (WP 2.5) live here too, and so do the properties panel (a sidebar, on phones a
 * bottom sheet), the item menu, duplicate / lock / z-order, "add with dimensions" and the touch
 * layer (WP 2.6). Saving, the conflict dialog and undo/redo (WP 2.8: `SaveBar`, `ConflictDialog`,
 * `useEditorShortcuts`) are mounted here; the list view and full keyboard (WP 2.7) plug into the
 * seams marked in `useEditorTools`.
 *
 * Wave 10 (§17.3, WP 10.3): the editor is the content of the workspace frame `EditorWorkspace`. Above the plan
 * there is one header bar (`EditorHeaderBar`: back, save group, tabs, field mode, panel switch, overflow "⋮"),
 * the canvas takes the rest of the viewport height (`useCanvasArea`, GP-UX-067) and zoom, scale bar and mini-map
 * are overlays on it. The list switch is gone: the tabs Plan · Liste of the route are the one way between the two
 * views (GP-UX-064).
 *
 * WP 10.5: the side panel (`SidePanel`) carries the tabs Eigenschaften, Ansicht (`ViewBar`), Ebenen (`LayersTab` with
 * the legend) and Zonen (`ZonePanel`); its switch is in the header bar, its state rule in `useSidePanel`. Its form
 * follows the width (GP-UX-069): docked beside the canvas from md up, a bottom sheet below md (#2885).
 * Collapsed it takes no width.
 */
import {
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type MouseEvent as ReactMouseEvent,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
} from 'react';
import { useTranslation } from 'react-i18next';
import type { TFunction } from 'i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import AddBoxOutlinedIcon from '@mui/icons-material/AddBoxOutlined';
import KeyboardIcon from '@mui/icons-material/Keyboard';
import RotateRightIcon from '@mui/icons-material/RotateRight';
import SelectAllIcon from '@mui/icons-material/SelectAll';
import ImageIcon from '@mui/icons-material/Image';
import LayersIcon from '@mui/icons-material/Layers';
import ViewSidebarOutlinedIcon from '@mui/icons-material/ViewSidebarOutlined';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import WbSunnyOutlinedIcon from '@mui/icons-material/WbSunnyOutlined';
import WavesIcon from '@mui/icons-material/Waves';
import AcUnitIcon from '@mui/icons-material/AcUnit';
import LocalFloristOutlinedIcon from '@mui/icons-material/LocalFloristOutlined';
import Diversity3OutlinedIcon from '@mui/icons-material/Diversity3Outlined';
import PriorityHighIcon from '@mui/icons-material/PriorityHigh';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import BookmarkAddOutlinedIcon from '@mui/icons-material/BookmarkAddOutlined';
import ContentCopyOutlinedIcon from '@mui/icons-material/FileCopyOutlined';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import FlipToBackIcon from '@mui/icons-material/FlipToBack';
import FlipToFrontIcon from '@mui/icons-material/FlipToFront';
import LockIcon from '@mui/icons-material/Lock';
import LockOpenIcon from '@mui/icons-material/LockOpen';
import YardIcon from '@mui/icons-material/Yard';
import DrawOutlinedIcon from '@mui/icons-material/DrawOutlined';
import CloseIcon from '@mui/icons-material/Close';
import Tooltip from '@mui/material/Tooltip';
import { isApiError } from '@/api/errors';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import ErrorBoundary from '@/components/common/ErrorBoundary';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { createBedTemplate } from '../api/gardenPlan';
import type { PlanModel } from '../model/planModel';
import { toShape } from '../model/geometry';
import type { GardenObjectType, PlanOperation, Point } from '../model/types';
import { formatLength, MAX_PX_PER_M, planGridStep, stepZoom, type LengthUnit } from '../model/units';
import type { PlanRenderer, RenderSelection, RendererLabels, Viewport } from '../renderer';
import { BOUNDARY_KEY, snapCandidates } from '../renderer/planIndex';
import { toScreen as projectToScreen } from '../renderer/viewport';
import { markerLodBedKeys } from '../renderer/scene';
import type { CompanionPairItem } from '../api/companionEdges';
import { cullCompanionLines } from '../renderer/companionLines';
import { usePlantStateLayer } from '../planting/usePlantStateLayer';
import { usePlanPlantStates } from '../planting/usePlanPlantStates';
import { planContentBounds } from '../routes/fitViewport';
import {
  applyAction,
  clearEditError,
  placeTemplateAt,
  selectGardenPlanState,
  selectInvalidKeys,
  setSelection,
  setStack,
  setTool,
  type PlanTool,
} from '../state/gardenPlanSlice';
import { AddWithDimensionsDialog } from './AddWithDimensionsDialog';
import { EDITOR_ANCHORS } from './anchors';
import { ALIGN_MODES, DISTRIBUTE_AXES } from './AlignMenu';
import { ContextMenu, type MenuAction, type MenuAnchor } from './ContextMenu';
import { DimensionLabels, type DimensionItem } from './DimensionLabels';
import { MeasureOverlay } from './MeasureOverlay';
import { ConflictDialog } from './ConflictDialog';
import { EditorHeaderBar, type HeaderNav, type HeaderTabs } from './EditorHeaderBar';
import { EditorWorkspace } from './EditorWorkspace';
import { EditorOverlay } from './EditorOverlay';
import { LiveMoveLayer } from './LiveMoveLayer';
import { usePendingZoom } from './usePendingZoom';
import {
  ANGLE_STEPS,
  EditorToolbar,
  type AngleStep,
  type EditorTool,
  type ToolbarSelectionGroup,
} from './EditorToolbar';
import { Grid } from './Grid';
import { MiniMap } from './MiniMap';
import { miniMapVisible, panToCentre } from './miniMap';
import { KeyboardHelp } from './KeyboardHelp';
import { LiveRegion } from './LiveRegion';
import { NewTypeSelect } from './NewTypeSelect';
import { PlanListView } from './PlanListView';
import { buildTree, neighbourKey } from './planTree';
import { ITEM_MENU_ID, PropertiesPanel } from './PropertiesPanel';
import { SaveMessages, UndoRedoButtons } from './SaveBar';
import { ScaleBar } from './ScaleBar';
import { SkipLinks } from './SkipLinks';
import { SnapMarker, type SnapMark } from './SnapMarker';
import { bedFrameGeometry, originForCentre, placeGeometry } from '../templates/placeGeometry';
import { TemplateGhost } from '../templates/TemplateGhost';
import { useBedTemplates } from '../templates/useBedTemplates';
import { TouchBar } from './TouchBar';
import { behaviourOf, canvasKindOf, cursorOf, TOOL_DEFS } from './toolRegistry';
import { TouchOverlay } from './TouchOverlay';
import { ViewBar } from './ViewBar';
import { LayersTab, type LayerToggle } from './LayersTab';
import { SidePanel, type SheetSize, type SidePanelVariant } from './SidePanel';
import { useSidePanel, type SidePanelTab } from './sidePanelState';
import { PANEL_GAP_PX, PANEL_WIDTH_PX } from './layout';
import { ZoomOverlay } from './ZoomOverlay';
import { useAutoSave } from './useAutoSave';
import { useCanvasArea, type CanvasAreaSize } from './useCanvasArea';
import { BedZoneInfo } from '../zones/BedZoneInfo';
import { useUnderlay } from '../underlay/useUnderlay';
import { useIrrigationZones, useLastWatered } from '../zones/useZoneData';
import { useWateringNow } from '../zones/useWateringNow';
import { useZoneLayers } from '../zones/useZoneLayers';
import { ZoneLegend } from '../zones/ZoneLegend';
import ObjectLegend from '../planting/ObjectLegend';
import { useAnnouncement } from './useAnnouncement';
import { useAreaTypes } from './useAreaTypes';
import { useBedTypes } from './useBedTypes';
import { useEditorKeyboard } from './useEditorKeyboard';
import { useEditorShortcuts } from './useEditorShortcuts';
import { TOGGLE_LAYERS, type LayerId } from './layers';
import { isIndoorPlanSite } from '../model/siteKind';
import { useLayerPrefs } from './useLayerPrefs';
import { useAttentionFilter } from './useAttentionFilter';
import { companionBedKeys, useCompanionEdges } from './useCompanionEdges';
import { useLengthUnit } from './useLengthUnit';
import { useSingleKeyShortcuts } from './useSingleKeyShortcuts';
import type { DimensionTarget } from './tools/addDimensions';
import {
  BOUNDARY_SHAPES,
  commonBedTypeKey,
  FALLBACK_AREA_TYPE_KEY,
  nextLocationNumber,
  type DrawShape,
} from './tools/drawMachine';
import {
  alignAvailability,
  alignSelection,
  distributeSelection,
  type AlignMode,
  type DistributeAxis,
} from './tools/align';
import {
  duplicateSelection,
  multiDuplicate,
  type MultiDuplicateOptions,
  type MultiRefusal,
} from './tools/duplicate';
import { deleteImpact, isPlanEntity, moveTargets, selectionRoots, type DeleteImpact } from './tools/hierarchy';
import { zoomToEditPxPerM } from './tools/handles';
import type { ActionLabel } from './tools/machineTypes';
import { panIntoView } from './tools/touchGestures';
import { isSelected, resolveRef, selectAll, stackRefs } from './tools/selection';
import { resolveMoveSnap, resolveSnap, snapPointerType, type SnapPointerType } from './tools/snap';
import type { MeasureView } from './tools/measureMachine';
import { useEditorTools } from './tools/useEditorTools';
import { violationOfNew } from './tools/validation';
import { useVisibleHeight } from './tools/useVisibleHeight';
import { useTouchInput } from './tools/useTouchInput';
import { zOrderOps, type ZMove } from './tools/zOrder';

export interface GardenPlanEditorProps {
  plan: PlanModel;
  viewport: Viewport;
  renderer: PlanRenderer;
  labels: RendererLabels;
  /** The pan tool moved the view by this many pixels; the route owns the viewport. */
  onPan: (dxPx: number, dyPx: number) => void;
  /** Zoom to `pxPerM` keeping the model point under `anchorPx` (canvas pixels) in place (WP 2.5); also the pinch. */
  onZoom?: (pxPerM: number, anchorPx: Point) => void;
  /** "Fit to area": back to the zoom that shows the whole plan (GP-FR-009). */
  onFit?: () => void;
  /** The lowest zoom allowed, the fit zoom (GP-FR-150). */
  minPxPerM?: number;
  /** Opens the detail page of a bed ("Details öffnen" / "Bepflanzen"). */
  onOpenLocation?: (locationKey: string) => void;
  /** Opens the care tab of a bed: the task badge on the plan and the panel button (GP-FR-089). */
  onOpenCare?: (locationKey: string) => void;
  /** Open "add with dimensions" when the editor mounts: the empty plan's "add the first bed" (#2617). */
  initialAddOpen?: boolean;
  /** Open the underlay dialog when the editor mounts: the empty indoor plan's "photo as a template" (WP 10.8). */
  initialUnderlayOpen?: boolean;
  /** Start the boundary mode when the editor mounts: the empty indoor plan's "draw the floor plan" (#2890). */
  initialBoundaryOpen?: boolean;
  /**
   * Plan or list (GP-NFR-023), when the route owns it: the tabs Plan · Liste keep it in the URL (GP-UX-064).
   * Without it the editor keeps the choice itself.
   */
  view?: EditorView;
  /** The editor's own controls (the skip links) ask for the other view. */
  onViewChange?: (view: EditorView) => void;
  /** Back, field mode and export/import of the header bar (§17.3, GP-UX-063); only the route knows them. */
  nav?: HeaderNav;
  /** The route's tabs Plan · Liste · Beete, shown in the header bar (GP-UX-064); `panelId` names the content. */
  tabs?: EditorTabs;
  /** The tab "Beete" is open: the header bar stays, the rest is hidden but stays mounted (GP-UX-065). */
  contentHidden?: boolean;
  /** The room the canvas has (GP-UX-067); the route fits the plan into it. Not called where nothing is laid out. */
  onCanvasSize?: (size: CanvasAreaSize) => void;
}

/** The route's tabs as the header bar shows them, plus the panel the editor content is for Plan and Liste. */
export interface EditorTabs extends HeaderTabs {
  panelId: string;
  /** Whether the tabs are in the bar or in its overflow, so the route can name the "Beete" panel. */
  onInlineChange?: (inline: boolean) => void;
}

/** The two surfaces of the editor: the drawing, or the same plan as a list (GP-NFR-023). */
export type EditorView = 'plan' | 'list';

/** The companion line the event hit (`data-companion-edge`, drawn by the renderer's companion layer), or `null`. */
function companionEdgeOf(event: { target: EventTarget | null }): string | null {
  const line = event.target instanceof Element ? event.target.closest('[data-companion-edge]') : null;
  return line?.getAttribute('data-companion-edge') ?? null;
}

/** The bed whose task badge the event hit (`data-plan-badge`, drawn by the renderer), or `null`. */
function badgeKeyOf(event: { target: EventTarget | null }): string | null {
  const badge = event.target instanceof Element ? event.target.closest('[data-plan-badge]') : null;
  return badge?.getAttribute('data-plan-badge') ?? null;
}

const PREFIX = 'pages.gardenPlan.editor';
const ZONES = `${PREFIX}.zones`;
const SIDE_PANEL = `${PREFIX}.sidePanel`;
const UNDERLAY = `${PREFIX}.underlay`;

// The zone panel is its own chunk (UI-NFR-003): the route chunk only carries the switch that mounts it.
const ZonePanel = lazy(() => import('../zones/ZonePanel'));
// The underlay dialog (GP-FR-033) likewise: nothing of it loads until somebody opens it.
const UnderlayDialog = lazy(() => import('../underlay/UnderlayDialog'));

/** Icon of each registry layer that has a toggle; the texts come from `pages.gardenPlan.editor.zones.layers.<id>`. */
const LAYER_ICONS: Record<Exclude<LayerId, 'grid'>, ReactNode> = {
  zones: <LayersIcon />,
  lastWatered: <WaterDropIcon />,
  underlay: <ImageIcon />,
  sun: <WbSunnyOutlinedIcon />,
  moisture: <WavesIcon />,
  frost: <AcUnitIcon />,
  plantState: <LocalFloristOutlinedIcon />,
  companion: <Diversity3OutlinedIcon />,
};

// The template picker, the "save as template" dialog and the multi-duplicate dialog are their own chunks:
// the plan route's budget (UI-NFR-003) carries none of them until they are opened.
const TemplatePanel = lazy(() => import('../templates/TemplatePanel'));
const SaveAsTemplateDialog = lazy(() => import('../templates/SaveAsTemplateDialog'));
const MultiDuplicateDialog = lazy(() => import('./MultiDuplicateDialog'));
// The info card of a companion line (GP-FR-134) loads with the first hover or tap.
const CompanionEdgeInfo = lazy(() => import('./CompanionEdgeInfo'));

const NO_KEYS: ReadonlySet<string> = new Set();
const BOUNDARY_ONLY: ReadonlySet<string> = new Set([BOUNDARY_KEY]);
/** The seeded area type of an indoor plan while the type list is not loaded (WP 10.8: rooms, #2913). */
const INDOOR_FALLBACK_AREA_TYPE_KEY = 'room';
const NO_BED_KEYS: readonly string[] = [];

/** The turn a click on "Rotate" adds to the template being placed (GP-FR-044). */
const TEMPLATE_TURN_DEG = 90;

/** Where the bed template tool stands: the template picked (or none yet) and its turn. */
interface TemplateMode {
  templateKey: string | null;
  rotationDeg: number;
  /** GP-FR-087: the opt-in "create recurring tasks", off by default and again for every newly picked template. */
  createRecurringTasks: boolean;
}

/**
 * The boundary mode (#2890): `draw` while the plan has no boundary, `edit` (unlocked, handles shown) once it has one,
 * `null` while another tool is on - then the boundary is locked (GP-FR-032).
 */
export type BoundaryMode = 'draw' | 'edit' | null;

/**
 * The measure tool's status text (GP-UX-071): the next step and, from the second fixed point on, the total. `mode`
 * is how the user sets points: the pointer, the touch bar, or the rail's "Set point" without a pointer.
 */
function measureStatusText(
  t: TFunction,
  measure: MeasureView | null,
  mode: 'pointer' | 'touch' | 'keyboard',
  unit: LengthUnit,
  language: string,
): string {
  const base = `${PREFIX}.measure.status.${mode}`;
  if (measure === null) return t(`${base}.start`);
  const segments = measure.fixedPoints - 1;
  if (segments < 1) return t(`${base}.first`);
  const total = formatLength(measure.fixedTotalM, unit, language);
  return t(`${base}.${measure.done ? 'done' : 'open'}`, { total, count: segments });
}

/** The body of the delete dialog: the children the delete takes along, by number (GP-FR-153). */
function useDeleteTexts(impact: DeleteImpact | null, plan: PlanModel, labels: RendererLabels) {
  const { t } = useTranslation();
  return useMemo(() => {
    if (impact === null) return { title: '', message: '' };
    const only = impact.roots.length === 1 ? impact.roots[0] : null;
    // An unnamed garden object is called by its type, never by an empty pair of quotes.
    const nameOf = (root: DeleteImpact['roots'][number]) =>
      root.name || labels.objectType(plan.gardenObjects[root.key]?.object_type ?? 'other');
    const title = only
      ? t(`${PREFIX}.deleteDialog.titleOne`, { name: nameOf(only) })
      : t(`${PREFIX}.deleteDialog.titleMany`, { count: impact.roots.length });
    const lines = [
      impact.childBeds > 0 && t(`${PREFIX}.deleteDialog.counts.beds`, { count: impact.childBeds }),
      impact.childObjects > 0 &&
        t(`${PREFIX}.deleteDialog.counts.objects`, { count: impact.childObjects }),
      impact.slots > 0 && t(`${PREFIX}.deleteDialog.counts.slots`, { count: impact.slots }),
      impact.plants > 0 && t(`${PREFIX}.deleteDialog.counts.plants`, { count: impact.plants }),
      impact.tasks > 0 && t(`${PREFIX}.deleteDialog.counts.tasks`, { count: impact.tasks }),
    ].filter((line): line is string => typeof line === 'string');
    const parts = [
      lines.length > 0
        ? `${t(`${PREFIX}.deleteDialog.alsoDeleted`)}\n${lines.map((line) => `• ${line}`).join('\n')}`
        : t(`${PREFIX}.deleteDialog.nothingElse`),
    ];
    parts.push(t(`${PREFIX}.deleteDialog.${impact.reversible ? 'reversible' : 'irreversible'}`));
    return { title, message: parts.join('\n\n') };
  }, [impact, labels, plan, t]);
}

export function GardenPlanEditor({
  plan,
  viewport,
  renderer,
  labels,
  onPan,
  onZoom,
  onFit,
  minPxPerM = 0,
  onOpenLocation,
  onOpenCare,
  initialAddOpen = false,
  initialUnderlayOpen = false,
  initialBoundaryOpen = false,
  view: viewProp,
  onViewChange,
  nav,
  tabs,
  contentHidden = false,
  onCanvasSize,
}: GardenPlanEditorProps) {
  const { t, i18n } = useTranslation();
  const theme = useTheme();
  // On phones the bar docks to the bottom; it follows the canvas in the DOM there so that the
  // tab order is the visual order (WCAG 2.4.3). On md+ it sits above the plan.
  const toolbarBelow = useMediaQuery(theme.breakpoints.down('md'));
  const coarsePointer = useMediaQuery('(pointer: coarse)');
  const touchUi = toolbarBelow || coarsePointer;
  // The side panel's form follows the width alone (GP-UX-069): docked beside the canvas from md up, a sheet below md.
  // At md it docks too, never over the canvas: an overlay hid the zoom controls and the selection (#2885).
  const panelVariant: SidePanelVariant = toolbarBelow ? 'sheet' : 'docked';
  const visibleHeight = useVisibleHeight();
  const dispatch = useAppDispatch();
  const { selection, stack, tool, editError, past, future, pending } =
    useAppSelector(selectGardenPlanState);
  const invalidKeys = useAppSelector(selectInvalidKeys);
  const boundary = plan.settings?.boundary ?? null;
  const boundaryMode: BoundaryMode = tool === 'boundary' ? (boundary ? 'edit' : 'draw') : null;
  // What the active tool means for the canvas comes from the tool registry (GP-UX-071): one place, not tool names.
  const canvasKind = canvasKindOf(tool, boundary !== null);
  const toolBehaviour = behaviourOf(canvasKind);
  // The side panel (GP-UX-068): a new selection - or the touch list of objects at one spot - opens it on the properties.
  const stackLists = stack !== null && stack.keys.length >= 2;
  const panelSelection = useMemo(
    () =>
      [
        ...selection.map((ref) => `${ref.entity}:${ref.key}`),
        ...(stackLists && stack ? [`stack:${stack.keys.join(',')}`] : []),
      ].join('|'),
    [selection, stack, stackLists],
  );
  const sidePanel = useSidePanel(panelSelection);
  const [sheetSize, setSheetSize] = useState<SheetSize>('half');
  // The zone panel takes the focus when its overflow entry opened it, not when its tab was chosen in the tab list.
  const [zonesFocus, setZonesFocus] = useState(false);
  const [drawShape, setDrawShape] = useState<DrawShape>('rect');
  const [angleStep, setAngleStep] = useState<AngleStep>(15);
  const [notice, setNotice] = useState<string | null>(null);
  // A plan without a stored grid starts on its site type's (5 cm indoor, GP-FR-182, WP 10.8).
  const [gridStepM, setGridStepM] = useState(() => planGridStep(plan));
  // The grid switch is a per-user layer choice kept in localStorage (GP-FR-031).
  const { prefs: layerPrefs, setLayer } = useLayerPrefs();
  const gridVisible = layerPrefs.grid;
  const setGridVisible = useCallback(
    (visible: boolean) => setLayer('grid', visible),
    [setLayer],
  );
  const setLayerById = useCallback((id: string, visible: boolean) => setLayer(id as LayerId, visible), [setLayer]);
  // The irrigation layers (WP 7.6 / 7.7): zones come with the plan; the endpoint is read once the tab "Zonen" opens.
  const zonesOpen = sidePanel.open && sidePanel.tab === 'zones';
  const [layerRefresh, setLayerRefresh] = useState(0);
  // The overflow "⋮" opens the keyboard help and the underlay; their dialogs give the focus back to it (WCAG 2.4.3).
  const overflowButtonRef = useRef<HTMLButtonElement | null>(null);
  const panelButtonRef = useRef<HTMLButtonElement | null>(null);
  // The panel switch, or "⋮" while the switch is in the overflow on a narrow bar.
  const focusPanelToggle = useCallback(() => (panelButtonRef.current ?? overflowButtonRef.current)?.focus(), []);
  // Closing the panel by its own button returns the focus to the switch, after the render that removed the button.
  const focusToggleAfterClose = useRef(false);
  useEffect(() => {
    if (!focusToggleAfterClose.current || sidePanel.open) return;
    focusToggleAfterClose.current = false;
    focusPanelToggle();
  });
  const nowMs = useWateringNow();
  const zoneData = useIrrigationZones(plan.siteKey, plan.zones, zonesOpen);
  const lastWateredAt = useLastWatered(plan.siteKey, plan.locations, layerRefresh);
  const zoneLayers = useZoneLayers({
    zones: zoneData.zones,
    showZones: layerPrefs.zones,
    showLastWatered: layerPrefs.lastWatered,
    lastWateredAt,
    nowMs,
  });
  // The underlay (GP-FR-033): shown per user; its switch is listed only while the site has a picture.
  const [underlayOpen, setUnderlayOpen] = useState(initialUnderlayOpen);
  const underlayWasOpen = useRef(false);
  useEffect(() => {
    if (!underlayOpen && underlayWasOpen.current) overflowButtonRef.current?.focus();
    underlayWasOpen.current = underlayOpen;
  }, [underlayOpen]);
  const underlayState = useUnderlay(plan, layerPrefs.underlay);
  // The plant-state layer (GP-UX-061, #2488): the beds at marker LOD read their states while the layer is on; the
  // filter "only plants that need attention" depends on it. Phase colours are read for the plants whose states are loaded.
  const plantStateOn = layerPrefs.plantState;
  const [attentionOnly, setAttentionOnly] = useAttentionFilter();
  const stateBedKeys = useMemo(
    () => (plantStateOn ? markerLodBedKeys(plan, viewport) : NO_BED_KEYS),
    [plantStateOn, plan, viewport],
  );
  const planStates = usePlanPlantStates(plan.siteKey, stateBedKeys, plantStateOn);
  const refreshPlanStates = planStates.refresh;
  // A saved or reloaded plan, or a care action, may change what the plants need: the loaded states are read again.
  const seenRevision = useRef(plan.revision);
  useEffect(() => {
    if (seenRevision.current === plan.revision) return;
    seenRevision.current = plan.revision;
    refreshPlanStates();
  }, [plan.revision, refreshPlanStates]);
  // A zone write changes no bed's last watering (it is read from the care and watering events of the bed), so the
  // plan is not read again for it; the zone list reloads through `zoneData`. A watering round does change it.
  const onZonesChanged = refreshPlanStates;
  const onWatered = useCallback(() => {
    setLayerRefresh((value) => value + 1);
    refreshPlanStates();
  }, [refreshPlanStates]);
  // Phase names are read only for the plants whose states are loaded (beds at marker LOD), never for the whole plan;
  // the PNG export derives its markers through the same hook.
  const { planPhaseKeys, phaseNames, phaseColors, plantStateLayer } = usePlantStateLayer(
    plan,
    planStates,
    plantStateOn,
    attentionOnly,
  );
  // The legend sorts the translated names itself, in the active language.
  const legendPhases = useMemo(() => {
    if (!plantStateOn) return [];
    const present = new Set(planPhaseKeys.filter((key): key is string => Boolean(key)));
    const names = new Set<string>();
    for (const key of present) {
      const name = phaseNames[key];
      if (name) names.add(name);
    }
    return [...names];
  }, [plantStateOn, planPhaseKeys, phaseNames]);
  const attentionFilter = useMemo(
    () => ({
      active: attentionOnly,
      enabled: plantStateOn,
      label: t(`${ZONES}.layers.attentionFilter`),
      hint: t(`${ZONES}.layers.${plantStateOn ? 'attentionFilterHint' : 'attentionFilterDisabledHint'}`),
      icon: <PriorityHighIcon />,
      onChange: setAttentionOnly,
    }),
    [attentionOnly, plantStateOn, t, setAttentionOnly],
  );
  // The companion-planting layer (GP-FR-134): the visible beds at marker LOD read their judged neighbour pairs while
  // the layer is on; the lines are culled to the view and capped at 500 before the renderer sees them.
  const companionOn = layerPrefs.companion;
  const companionBeds = useMemo(
    () => (companionOn ? companionBedKeys(plan, viewport) : NO_BED_KEYS),
    [companionOn, plan, viewport],
  );
  const companion = useCompanionEdges(plan.siteKey, companionBeds, companionOn);
  const refreshCompanion = companion.refresh;
  // A saved or reloaded plan may have new neighbours or plantings: the loaded pairs are read again.
  const companionRevision = useRef(plan.revision);
  useEffect(() => {
    if (companionRevision.current === plan.revision) return;
    companionRevision.current = plan.revision;
    refreshCompanion();
  }, [plan.revision, refreshCompanion]);
  const companionCulled = useMemo(
    () => (companionOn ? cullCompanionLines(companion.lines, viewport) : null),
    [companionOn, companion.lines, viewport],
  );
  const companionLayer = useMemo(
    () => (companionCulled ? { lines: companionCulled.lines } : undefined),
    [companionCulled],
  );
  // The text twin of the lines for keyboard and screen reader users: the pairs in view, incompatible first.
  const companionPairs = useMemo<CompanionPairItem[]>(
    () =>
      (companionCulled?.lines ?? []).flatMap((line) => {
        const edge = companion.edges[line.id];
        return edge ? [{ id: line.id, edge }] : [];
      }),
    [companionCulled, companion.edges],
  );
  const companionCapped = (companionCulled?.capped ?? false) || companion.truncated;
  // Hover shows a line's card while the pointer is on it; a tap pins it until it is closed (touch has no hover).
  const [companionHover, setCompanionHover] = useState<string | null>(null);
  const [companionPinned, setCompanionPinned] = useState<string | null>(null);
  const closeCompanionInfo = useCallback(() => setCompanionPinned(null), []);
  const hasUnderlay = underlayState.underlay !== null;
  // An indoor plan has no frost (GP-FR-182, WP 10.8): its layer is neither offered, drawn nor in the legend.
  const indoor = isIndoorPlanSite(plan.siteType);
  const frostShown = layerPrefs.frost && !indoor;
  const layerToggles = useMemo<LayerToggle[]>(
    () =>
      (TOGGLE_LAYERS as readonly Exclude<LayerId, 'grid'>[])
        .filter((id) => id !== 'underlay' || hasUnderlay)
        .filter((id) => id !== 'frost' || !indoor)
        .map((id) => ({
        id,
        label: t(`${ZONES}.layers.${id}`),
        hint: t(`${ZONES}.layers.${id}Hint`),
        icon: LAYER_ICONS[id],
        visible: layerPrefs[id],
      })),
    [layerPrefs, t, hasUnderlay, indoor],
  );
  const [snapEnabled, setSnapEnabled] = useState(true);
  const [snapMark, setSnapMark] = useState<SnapMark | null>(null);
  const [unit, setUnit] = useLengthUnit();
  const [pendingDelete, setPendingDelete] = useState<DeleteImpact | null>(null);
  const [multiSelect, setMultiSelect] = useState(false);
  const [bedTypeChoice, setBedTypeChoice] = useState<string | null>(null);
  const [areaTypeChoice, setAreaTypeChoice] = useState<string | null>(null);
  const [objectType, setObjectType] = useState<GardenObjectType>('other');
  const [menuAnchor, setMenuAnchor] = useState<MenuAnchor | null>(null);
  const [addOpen, setAddOpen] = useState(initialAddOpen);
  // The sub-menu of "Bed" or "Garden object" that opened "Add with dimensions" (GP-UX-046, WP 10.4).
  const [addTarget, setAddTarget] = useState<DimensionTarget>('bed');
  const [templateMode, setTemplateMode] = useState<TemplateMode | null>(null);
  const [placing, setPlacing] = useState(false);
  const [ghostPoint, setGhostPoint] = useState<Point | null>(null);
  const [saveTemplateOpen, setSaveTemplateOpen] = useState(false);
  const [multiOpen, setMultiOpen] = useState(false);
  const [info, setInfo] = useState<string | null>(null);
  const deleteTexts = useDeleteTexts(pendingDelete, plan, labels);
  const [ownView, setOwnView] = useState<EditorView>('plan');
  const view = viewProp ?? ownView;
  const changeView = useCallback(
    (next: EditorView) => {
      if (onViewChange) onViewChange(next);
      else setOwnView(next);
    },
    [onViewChange],
  );
  const [helpOpen, setHelpOpen] = useState(false);
  const shortcuts = useSingleKeyShortcuts();
  // Auto-save lives as long as the editor (GP-UX-004): the header bar shows its switch inline or in the overflow.
  const autoSave = useAutoSave();
  const helpWasOpen = useRef(false);
  useEffect(() => {
    if (!helpOpen && helpWasOpen.current) overflowButtonRef.current?.focus();
    helpWasOpen.current = helpOpen;
  }, [helpOpen]);
  const dockRef = useRef<HTMLDivElement | null>(null);
  // The bars docked at the bottom on phones: the canvas keeps clear of them (the sheet above them may cover it).
  const dockBarsRef = useRef<HTMLDivElement | null>(null);
  const canvasAreaRef = useRef<HTMLDivElement | null>(null);
  // A panel that a selection docked beside the canvas still counts for the fit: the plan does not move (WP 10.5).
  const fitReservePx =
    panelVariant === 'docked' && sidePanel.open && sidePanel.openedBy === 'selection' && view === 'plan'
      ? PANEL_WIDTH_PX + PANEL_GAP_PX
      : 0;
  const canvasArea = useCanvasArea(canvasAreaRef, dockBarsRef, fitReservePx);
  useEffect(() => {
    if (canvasArea) onCanvasSize?.(canvasArea);
  }, [canvasArea, onCanvasSize]);
  // The phone's "pan the selection above the sheet" waits for the release when a pointer holds a gesture: a view
  // that moves under a pressed object would turn the press into a drag by the pan (GP-UX-052). The release bumps
  // `panAfterRelease`, so the pan runs after the render that shows where the selection now is.
  const panDeferred = useRef(false);
  const [panAfterRelease, setPanAfterRelease] = useState(0);
  const runPanIntoViewLater = useCallback(() => {
    if (!panDeferred.current) return;
    panDeferred.current = false;
    setPanAfterRelease((count) => count + 1);
  }, []);
  const canvasRef = useRef<HTMLDivElement | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);
  const announcement = useAnnouncement(plan, past, future, t(`${PREFIX}.liveRegion.unnamed`));
  // Where the focus goes after the next render (GP-NFR-070 - never to the body): an object key,
  // or one of the two surfaces.
  const pendingFocus = useRef<{ key: string } | 'plan' | 'list' | null>(null);

  const bedTypes = useBedTypes(tool === 'bed' || addOpen);
  const templateCatalogue = useBedTemplates(templateMode !== null);
  const fallbackBedType = useMemo(() => commonBedTypeKey(plan), [plan]);
  const bedTypeKey = bedTypeChoice ?? fallbackBedType;
  // The area tool's type (GP-UX-071, #2913): the choice while it is offered, else the first offered type, else the
  // seeded garden (indoor: room) while the list is not loaded.
  const areaTypes = useAreaTypes(tool === 'area' || addOpen, indoor);
  const fallbackAreaType = areaTypes[0]?.key ?? (indoor ? INDOOR_FALLBACK_AREA_TYPE_KEY : FALLBACK_AREA_TYPE_KEY);
  const areaTypeKey =
    areaTypeChoice !== null && areaTypes.some((type) => type.key === areaTypeChoice) ? areaTypeChoice : fallbackAreaType;

  const onCommit = useCallback(
    (ops: PlanOperation[], label: ActionLabel) => {
      dispatch(applyAction(ops, `${PREFIX}.actions.${label}`));
    },
    [dispatch],
  );
  const onSelect = useCallback(
    (next: typeof selection) => void dispatch(setSelection(next)),
    [dispatch],
  );
  const onStack = useCallback((next: typeof stack) => void dispatch(setStack(next)), [dispatch]);
  const onTool = useCallback((next: PlanTool) => void dispatch(setTool(next)), [dispatch]);
  const focusPlan = useCallback(() => canvasRef.current?.focus(), []);
  // The empty plan's "add the first bed" button is gone once the editor mounts, so closing the dialog it
  // opened would drop the focus to the page; it goes to the plan instead (WCAG 2.4.3, #2617).
  const addWasOpen = useRef(initialAddOpen);
  useEffect(() => {
    if (!addOpen && addWasOpen.current && initialAddOpen) focusPlan();
    addWasOpen.current = addOpen;
  }, [addOpen, initialAddOpen, focusPlan]);
  const focusSurface = useCallback(() => {
    pendingFocus.current = view === 'plan' ? 'plan' : 'list';
  }, [view]);
  useEffect(() => {
    const request = pendingFocus.current;
    if (request === null) return;
    // A surface asked for that is not shown yet waits for the render that shows it: with a route-owned view
    // (the tabs, GP-UX-064) the switch arrives one navigation later.
    if ((request === 'plan' || request === 'list') && request !== view) return;
    pendingFocus.current = null;
    const surface =
      view === 'plan'
        ? canvasRef.current
        : (listRef.current?.querySelector<HTMLElement>(`#${EDITOR_ANCHORS.list}`) ?? null);
    if (request === 'plan' || request === 'list') {
      surface?.focus();
      return;
    }
    const attribute = view === 'plan' ? 'data-plan-key' : 'data-list-key';
    const node = surface?.querySelector<HTMLElement>(`[${attribute}="${CSS.escape(request.key)}"]`);
    (node ?? surface)?.focus();
  });
  const newBedName = useCallback((n: number) => t(`${PREFIX}.newBedName`, { n }), [t]);
  const newAreaName = useCallback((n: number) => t(`${PREFIX}.area.newName`, { n }), [t]);

  const requestDelete = useCallback(() => {
    const impact = deleteImpact(plan, selection);
    if (impact.roots.length === 0) return;
    if (impact.lockedKeys.length > 0) {
      setNotice('object.locked'); // GP-FR-032: unlock first
      return;
    }
    setPendingDelete(impact);
  }, [plan, selection]);
  const openHelp = useCallback(() => setHelpOpen(true), []);
  const keyboard = useEditorKeyboard({
    plan,
    tool,
    selection,
    canvasRef,
    singleKeyShortcuts: shortcuts.enabled,
    stepM: gridStepM,
    onCommit,
    onNotice: setNotice,
    onPan,
    onHelp: openHelp,
  });

  // The seam of the tool machines for grid and snap (GP-FR-012, GP-FR-154). Object snap lands on the
  // corners and edges of the other visible objects (priority corner -> edge -> grid); what is being moved
  // is left out, or it would snap to itself.
  const pxPerM = viewport.pxPerM;
  const movingKeys = useMemo(() => {
    // The boundary being reshaped must not snap to its own corners (#2890).
    if (tool === 'boundary') return BOUNDARY_ONLY;
    return tool === 'select' && templateMode === null
      ? new Set(moveTargets(plan, selection).map((entry) => entry.key))
      : NO_KEYS;
  }, [plan, selection, templateMode, tool]);
  const candidates = useMemo(
    () => (snapEnabled ? snapCandidates(plan, movingKeys) : undefined),
    [plan, movingKeys, snapEnabled],
  );
  const snapPoint = useCallback(
    (point: Point, bypass: boolean, pointerType: SnapPointerType = 'mouse') =>
      resolveSnap(point, {
        gridM: gridStepM,
        gridEnabled: snapEnabled,
        bypass,
        pxPerM,
        pointerType,
        candidates,
      }).point,
    [candidates, gridStepM, snapEnabled, pxPerM],
  );
  // A moved object snaps with every vertex of its shape (GP-FR-154): its right edge can meet another's left edge.
  const snapMove = useCallback(
    (
      sources: readonly Point[],
      reference: Point,
      rawDelta: Point,
      bypass: boolean,
      pointerType: SnapPointerType = 'mouse',
    ) =>
      resolveMoveSnap(sources, reference, rawDelta, {
        gridM: gridStepM,
        gridEnabled: snapEnabled,
        bypass,
        pxPerM,
        pointerType,
        candidates,
      }),
    [candidates, gridStepM, snapEnabled, pxPerM],
  );

  const tools = useEditorTools({
    tool,
    drawShape,
    angleStepDeg: angleStep,
    plan,
    viewport,
    renderer,
    selection,
    stack,
    newBedName,
    onSelect,
    onStack,
    onCommit,
    onPan,
    onTool,
    onNotice: setNotice,
    onRequestDelete: requestDelete,
    additive: multiSelect,
    bedTypeKey,
    objectType,
    areaTypeKey,
    newAreaName,
    snapPoint,
    snapMove,
  });

  const zoomCenter = useMemo<Point>(
    () => [viewport.widthPx / 2, viewport.heightPx / 2],
    [viewport.widthPx, viewport.heightPx],
  );
  const {
    attachLayer: attachZoomLayer,
    zoomTo,
    newestView,
  } = usePendingZoom({ viewport, onZoom, onPan, minPxPerM, canvasRef, canvasKey: view });
  // The buttons and the keys step from the newest view: a wheel burst still pending is part of it.
  const zoomBy = useCallback(
    (direction: 1 | -1) => {
      if (onZoom) zoomTo(stepZoom(newestView().pxPerM, direction, minPxPerM), zoomCenter);
    },
    [minPxPerM, newestView, onZoom, zoomCenter, zoomTo],
  );
  const zoomIn = useCallback(() => zoomBy(1), [zoomBy]);
  const zoomOut = useCallback(() => zoomBy(-1), [zoomBy]);
  const fit = useCallback(() => onFit?.(), [onFit]);

  const toolKeyDown = tools.containerProps.onKeyDown;
  const onKeyDown = useCallback(
    (event: ReactKeyboardEvent<HTMLElement>) => {
      // Esc ends the template tool before anything else takes it (the bar's tools end it the same way).
      if (event.key === 'Escape' && templateMode !== null) {
        event.preventDefault();
        setTemplateMode(null);
        setGhostPoint(null);
        return;
      }
      // Arrows, PageUp/Down and ? first (WP 2.7); they report whether they took the key.
      if (keyboard.handleKey(event)) return;
      // The single printable keys of the view (WP 2.5) obey the WCAG 2.1.4 switch like `?` does.
      if (shortcuts.enabled && !event.ctrlKey && !event.metaKey && !event.altKey) {
        if (event.key === '+' || event.key === '=') {
          event.preventDefault();
          zoomIn();
          return;
        }
        if (event.key === '-' || event.key === '_') {
          event.preventDefault();
          zoomOut();
          return;
        }
        if (event.key === '0') {
          event.preventDefault();
          fit();
          return;
        }
        if (event.key === 'g' || event.key === 'G') {
          event.preventDefault();
          setGridVisible(!gridVisible);
          return;
        }
      }
      toolKeyDown(event);
    },
    [
      fit,
      gridVisible,
      keyboard,
      setGridVisible,
      shortcuts.enabled,
      templateMode,
      toolKeyDown,
      zoomIn,
      zoomOut,
    ],
  );

  // The snap marker follows the pointer of the draw tools, of the template tool and of a dragged handle (where
  // the next point will land); on an object edge it draws that edge as a guide (GP-FR-154). A select press, a
  // marquee or a move never shows the pointer's marker: a move shows where the moved object snapped
  // (`tools.moveSnap`), and the first pointer move of a drag still sees the press here.
  const drawTool = canvasKind === 'draw';
  const pointerSnaps = toolBehaviour.snapMarker;
  const templateTool = templateMode !== null;
  const {
    onPointerMove: toolPointerMove,
    onPointerUp: toolPointerUp,
    onPointerCancel: toolPointerCancel,
  } = tools.containerProps;
  const toolHandleDragging = tools.handleDragging;
  // While Space is held a press pans (GP-FR-010): no snap marker or template ghost follows the pointer.
  const spaceHeld = tools.panModifier;
  const onPointerMove = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      toolPointerMove(event);
      if (companionOn) {
        const edge = event.buttons === 0 ? companionEdgeOf(event) : null;
        setCompanionHover((previous) => (previous === edge ? previous : edge));
      }
      if (spaceHeld) {
        setSnapMark((previous) => (previous === null ? previous : null));
        return;
      }
      const snapping = (pointerSnaps || templateTool || toolHandleDragging) && snapEnabled && !event.altKey;
      if (!templateTool && !snapping) {
        // A move of the selection or a hover: no marker, and no layout read per pointer move (GP-NFR-033).
        setSnapMark((previous) => (previous === null ? previous : null));
        return;
      }
      const box = event.currentTarget.getBoundingClientRect();
      const pointM = renderer.toModel([
        event.clientX - box.left - event.currentTarget.clientLeft,
        event.clientY - box.top - event.currentTarget.clientTop,
      ]);
      if (templateTool) {
        // The ghost sits where the click would put the template: on the snapped point.
        const landing = snapPoint(pointM, event.altKey, snapPointerType(event.pointerType));
        setGhostPoint((previous) =>
          previous && previous[0] === landing[0] && previous[1] === landing[1] ? previous : landing,
        );
      }
      if (!snapping) {
        setSnapMark((previous) => (previous === null ? previous : null));
        return;
      }
      const result = resolveSnap(pointM, {
        gridM: gridStepM,
        gridEnabled: true,
        bypass: false,
        pxPerM,
        pointerType: snapPointerType(event.pointerType),
        candidates,
      });
      setSnapMark((previous) =>
        previous &&
        previous.kind === result.kind &&
        previous.point[0] === result.point[0] &&
        previous.point[1] === result.point[1] &&
        previous.guide === result.guide
          ? previous
          : result.kind === 'none'
            ? null
            : { point: result.point, kind: result.kind, guide: result.guide },
      );
    },
    [
      candidates,
      companionOn,
      gridStepM,
      pointerSnaps,
      pxPerM,
      renderer,
      snapEnabled,
      snapPoint,
      spaceHeld,
      templateTool,
      toolHandleDragging,
      toolPointerMove,
    ],
  );
  const onPointerLeave = useCallback(() => {
    setSnapMark(null);
    setGhostPoint(null);
    setCompanionHover(null);
  }, []);
  // A release or a cancel ends the gesture the marker belonged to; the next hover move draws it again.
  const onPointerUp = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      toolPointerUp(event);
      setSnapMark(null);
      runPanIntoViewLater();
    },
    [toolPointerUp, runPanIntoViewLater],
  );
  const onPointerCancel = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      toolPointerCancel(event);
      setSnapMark(null);
      runPanIntoViewLater();
    },
    [toolPointerCancel, runPanIntoViewLater],
  );
  const onPlantsNearby = useCallback(
    (keys: string[], pointPx: Point) => {
      // Never a guessed single hit: the finger gets the list (GP-UX-034).
      dispatch(setSelection([]));
      dispatch(setStack({ keys, index: 0, pointPx }));
    },
    [dispatch],
  );
  // The touch layer wraps the handlers above (keys, snap marker), so both layers work together.
  const touchBase = useMemo(
    () => ({ ...tools.containerProps, onKeyDown, onPointerMove, onPointerUp, onPointerCancel }),
    [onKeyDown, onPointerMove, onPointerUp, onPointerCancel, tools.containerProps],
  );
  // Pinch: the factor of one step is applied to the current zoom; the route clamps it like the buttons.
  const onPinch = useMemo(
    () =>
      onZoom
        ? (factor: number, centerPx: Point) =>
            zoomTo(newestView().pxPerM * factor, centerPx)
        : undefined,
    [newestView, onZoom, zoomTo],
  );
  // A finger that lands on a companion line must not lose the pan or the pinch (a dense bed is mostly line): the hook
  // pans on a drag and pins the card on a tap that did not move, and the press selects nothing (GP-FR-134).
  const passiveTarget = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => (companionOn ? companionEdgeOf(event) : null),
    [companionOn],
  );
  const touch = useTouchInput({
    passiveTarget,
    onPassiveTap: setCompanionPinned,
    tool,
    multiSelect,
    plan,
    renderer,
    handles: tools.handles,
    base: touchBase,
    onPan,
    onZoom: onPinch,
    onPlantsNearby,
  });

  const northAngleDeg = plan.settings?.north_angle_deg ?? 0;
  const onNorthAngle = useMemo(
    () =>
      boundary
        ? (angle: number) =>
            void dispatch(
              applyAction(
                [{ op: 'set_boundary', boundary, north_angle_deg: angle }],
                `${PREFIX}.actions.northAngle`,
              ),
            )
        : undefined,
    [boundary, dispatch],
  );

  // GP-FR-014: sizes at the selected object, and at every outline a gesture is drawing.
  const dimensionItems = useMemo<DimensionItem[]>(() => {
    if (tools.overlay.shapes.length > 0) {
      return tools.overlay.shapes.map(({ key, shape }) => ({ key, shape }));
    }
    if (selection.length !== 1 || !isPlanEntity(selection[0])) return [];
    const ref = selection[0];
    const source =
      ref.entity === 'location' ? plan.locations[ref.key] : plan.gardenObjects[ref.key];
    return source?.geometry ? [{ key: ref.key, shape: toShape(source.geometry) }] : [];
  }, [plan, selection, tools.overlay.shapes]);

  const confirmDelete = useCallback(() => {
    if (pendingDelete) {
      onCommit(pendingDelete.ops, 'delete');
      // The deleted object cannot keep the focus: hand it to its neighbour in the list.
      const next = neighbourKey(
        buildTree(plan, labels.objectType),
        new Set(pendingDelete.roots.map((root) => root.key)),
      );
      pendingFocus.current = next === null ? (view === 'plan' ? 'plan' : 'list') : { key: next };
    }
    setPendingDelete(null);
  }, [labels, onCommit, pendingDelete, plan, view]);

  // ── Actions of the panel, the item menu and the overflow ──────────────────

  const duplicate = useCallback(() => {
    const step = plan.settings?.default_grid_m ?? plan.defaultGridM ?? 0.1;
    const outcome = duplicateSelection(plan, selection, step, (name) =>
      t(`${PREFIX}.duplicate.name`, { name }),
    );
    if (!outcome.ok) {
      if (outcome.code !== 'nothing') setNotice(outcome.code);
      return;
    }
    onCommit(outcome.value.ops, 'duplicate');
    dispatch(setSelection(outcome.value.selection));
    dispatch(setStack(null));
  }, [dispatch, onCommit, plan, selection, t]);
  // Ctrl/Cmd+D runs the same duplicate as the panel and the item menu (GP-FR-025, WP 9.14); with no bed or
  // object selected the key stays the browser's.
  const canDuplicate = selection.some(isPlanEntity);
  const onShortcut = useEditorShortcuts(canDuplicate ? duplicate : null);

  /** Align / distribute: one batch of `update_geometry`, one undo step; a refusal says why (GP-FR-029). */
  const availability = useMemo(() => alignAvailability(plan, selection), [plan, selection]);
  const commitArrangement = useCallback(
    (outcome: ReturnType<typeof alignSelection>, label: 'align' | 'distribute') => {
      if (!outcome.ok) {
        if (outcome.code !== 'nothing') setNotice(outcome.code);
        return;
      }
      onCommit(outcome.ops, label);
    },
    [onCommit],
  );
  const align = useCallback(
    (mode: AlignMode) => commitArrangement(alignSelection(plan, selection, mode), 'align'),
    [commitArrangement, plan, selection],
  );
  const distribute = useCallback(
    (axis: DistributeAxis) =>
      commitArrangement(distributeSelection(plan, selection, axis), 'distribute'),
    [commitArrangement, plan, selection],
  );

  /** Duplicate several times (GP-FR-025): one undo step; the dialog shows a refusal. */
  const runMultiDuplicate = useCallback(
    (options: MultiDuplicateOptions): MultiRefusal | null => {
      const outcome = multiDuplicate(plan, selection, { ...options, pendingCount: pending.length });
      if (!outcome.ok) {
        return { code: outcome.code, failedCopy: outcome.failedCopy, failedName: outcome.failedName };
      }
      onCommit(outcome.value.ops, 'multiDuplicate');
      dispatch(setSelection(outcome.value.selection));
      dispatch(setStack(null));
      setMultiOpen(false);
      return null;
    },
    [dispatch, onCommit, pending.length, plan, selection],
  );
  const multiRoots = useMemo(
    () =>
      selectionRoots(plan, selection).filter(
        (ref) => ref.entity === 'location' && plan.locations[ref.key]?.geometry != null,
      ).length,
    [plan, selection],
  );

  // ── Bed templates (GP-FR-044/045) ──────────────────────────────────────────

  const singleBed = useMemo(() => {
    const ref = selection.length === 1 ? selection[0] : null;
    const location = ref?.entity === 'location' ? plan.locations[ref.key] : undefined;
    return location?.geometry && bedFrameGeometry(location.geometry) ? location : null;
  }, [plan, selection]);

  const toggleTemplateTool = useCallback(() => {
    setTemplateMode((previous) => (previous ? null : { templateKey: null, rotationDeg: 0, createRecurringTasks: false }));
    setGhostPoint(null);
    setSnapMark(null);
    dispatch(setTool('select'));
  }, [dispatch]);

  const placeTemplate = useCallback(
    async (originM: Point) => {
      const mode = templateMode;
      if (mode?.templateKey == null || placing) return;
      setPlacing(true);
      try {
        const outcome = await dispatch(
          placeTemplateAt({
            templateKey: mode.templateKey,
            origin: originM,
            rotationDeg: mode.rotationDeg,
            createRecurringTasks: mode.createRecurringTasks,
          }),
        ).unwrap();
        if (outcome.ok) {
          setNotice(null);
          setInfo(
            outcome.tasksFailed
              ? t(`${PREFIX}.templates.placedTasksFailed`)
              : outcome.createdTasks > 0
                ? t(`${PREFIX}.templates.placedWithTasks`, { count: outcome.createdTasks })
                : t(`${PREFIX}.templates.placed`),
          );
          if (outcome.locationKey) {
            dispatch(setSelection([{ entity: 'location', key: outcome.locationKey }]));
          }
        } else {
          setInfo(null);
          setNotice(outcome.code);
        }
      } finally {
        setPlacing(false);
      }
    },
    [dispatch, placing, t, templateMode],
  );

  const saveAsTemplate = useCallback(
    async (name: string): Promise<string | null> => {
      if (!singleBed?.geometry) return 'generic';
      const geometry = bedFrameGeometry(singleBed.geometry);
      if (!geometry) return 'generic';
      const height = singleBed.height_m;
      try {
        await createBedTemplate({
          name,
          location_type_key: singleBed.location_type_key,
          default_geometry: geometry,
          // A height outside the catalogue's range (GP-FR-043) is left out rather than refused.
          ...(height != null && height >= 0.1 && height <= 1.5 ? { height_m: height } : {}),
        });
      } catch (error) {
        if (isApiError(error)) return error.statusCode === 403 ? 'forbidden' : error.errorCode;
        return 'generic';
      }
      templateCatalogue.reload();
      setSaveTemplateOpen(false);
      setInfo(t(`${PREFIX}.templates.save.done`, { name }));
      return null;
    },
    [singleBed, t, templateCatalogue],
  );

  const setLocked = useCallback(
    (locked: boolean) => {
      const ops: PlanOperation[] = selection.filter(isPlanEntity).map((ref) => ({
        op: 'set_locked',
        entity: ref.entity,
        key: ref.key,
        locked,
      }));
      if (ops.length > 0) onCommit(ops, locked ? 'lock' : 'unlock');
    },
    [onCommit, selection],
  );

  const moveInZ = useCallback(
    (move: ZMove) => {
      const ops = zOrderOps(plan, selection, move);
      if (ops.length > 0) onCommit(ops, 'zOrder');
    },
    [onCommit, plan, selection],
  );

  const doSelectAll = useCallback(() => {
    dispatch(setSelection(selectAll(plan)));
    dispatch(setStack(null));
  }, [dispatch, plan]);

  const addWithDimensions = useCallback(
    (ops: PlanOperation[], created: (typeof selection)[number]) => {
      onCommit(ops, 'addWithDimensions');
      dispatch(setSelection([created]));
      dispatch(setStack(null));
      setAddOpen(false);
    },
    [dispatch, onCommit],
  );

  const focusPanel = useCallback(() => {
    document.querySelector<HTMLElement>('[data-testid="garden-plan-panel-name"]')?.focus();
  }, []);
  /** The skip link "To the properties panel": the open panel takes the focus, a collapsed one its switch (GP-UX-068). */
  const panelOpen = sidePanel.open;
  const focusPanelRegion = useCallback(() => {
    if (panelOpen) document.getElementById(EDITOR_ANCHORS.panel)?.focus();
    else focusPanelToggle();
  }, [panelOpen, focusPanelToggle]);
  const showPanelTab = sidePanel.showTab;
  const chooseTab = useCallback(
    (tab: SidePanelTab) => {
      setZonesFocus(false);
      showPanelTab(tab);
    },
    [showPanelTab],
  );

  const menuActions = useMemo<MenuAction[]>(() => {
    const entities = selection.filter(isPlanEntity);
    if (entities.length === 0) return [];
    const allLocked = entities.every((ref) => isLockedRefIn(plan, ref));
    const single = entities.length === 1 ? entities[0] : null;
    const actions: MenuAction[] = [
      {
        id: 'edit',
        label: t(`${PREFIX}.contextMenu.edit`),
        icon: <EditOutlinedIcon fontSize="small" />,
        onClick: () => {
          showPanelTab('properties');
          window.setTimeout(focusPanel, 0);
        },
      },
      {
        id: 'duplicate',
        label: t(`${PREFIX}.contextMenu.duplicate`),
        icon: <ContentCopyIcon fontSize="small" />,
        onClick: duplicate,
        shortcut: { label: t(`${PREFIX}.contextMenu.duplicateShortcut`), aria: 'Control+D Meta+D' },
      },
      {
        id: 'multiDuplicate',
        label: t(`${PREFIX}.contextMenu.multiDuplicate`),
        icon: <ContentCopyOutlinedIcon fontSize="small" />,
        onClick: () => setMultiOpen(true),
      },
    ];
    if (singleBed) {
      actions.push({
        id: 'saveTemplate',
        label: t(`${PREFIX}.templates.save.button`),
        icon: <BookmarkAddOutlinedIcon fontSize="small" />,
        onClick: () => setSaveTemplateOpen(true),
      });
    }
    if (availability.align) {
      for (const [index, mode] of ALIGN_MODES.entries()) {
        actions.push({
          id: `align-${mode}`,
          label: t(`${PREFIX}.align.mode.${mode}`),
          onClick: () => align(mode),
          separated: index === 0,
        });
      }
      for (const axis of DISTRIBUTE_AXES) {
        actions.push({
          id: `distribute-${axis}`,
          label: t(`${PREFIX}.align.distribute.${axis}`),
          onClick: () => distribute(axis),
          disabled: !availability.distribute,
        });
      }
    }
    if (single?.entity === 'location' && onOpenLocation) {
      actions.push({
        id: 'plant',
        label: t(`${PREFIX}.panel.plant`),
        icon: <YardIcon fontSize="small" />,
        onClick: () => onOpenLocation(single.key),
      });
    }
    actions.push(
      {
        id: 'front',
        label: t(`${PREFIX}.contextMenu.front`),
        icon: <FlipToFrontIcon fontSize="small" />,
        onClick: () => moveInZ('front'),
      },
      {
        id: 'back',
        label: t(`${PREFIX}.contextMenu.back`),
        icon: <FlipToBackIcon fontSize="small" />,
        onClick: () => moveInZ('back'),
      },
      {
        id: allLocked ? 'unlock' : 'lock',
        label: t(allLocked ? `${PREFIX}.contextMenu.unlock` : `${PREFIX}.contextMenu.lock`),
        icon: allLocked ? <LockOpenIcon fontSize="small" /> : <LockIcon fontSize="small" />,
        onClick: () => setLocked(!allLocked),
        separated: true,
      },
      {
        id: 'delete',
        label: t(`${PREFIX}.delete.label`),
        icon: <DeleteOutlinedIcon fontSize="small" color="error" />,
        onClick: requestDelete,
      },
    );
    return actions;
  }, [
    align,
    availability,
    distribute,
    duplicate,
    focusPanel,
    moveInZ,
    onOpenLocation,
    showPanelTab,
    plan,
    requestDelete,
    selection,
    setLocked,
    singleBed,
    t,
  ]);

  const openAddWithDimensions = useCallback((target: DimensionTarget) => {
    setAddTarget(target);
    setAddOpen(true);
  }, []);

  // ── The garden boundary / flat outline (UC-01, GP-FR-019/032, #2890) ─────

  /**
   * Draw the boundary, or unlock it for editing: the boundary mode. It is a plan-level action of the overflow, not a
   * tool of the rail (GP-UX-001 lists the rail's tools; §17.3 keeps the rare actions in "⋮"). Nothing stays selected:
   * the boundary's handles are the only ones on the plan meanwhile.
   */
  const startBoundary = useCallback(() => {
    dispatch(setSelection([]));
    dispatch(setStack(null));
    dispatch(setTool('boundary'));
    setTemplateMode(null);
    setGhostPoint(null);
    setDrawShape((shape) => (BOUNDARY_SHAPES.includes(shape) ? shape : 'rect'));
  }, [dispatch]);
  /** Leave the boundary mode: the boundary is locked again (GP-FR-032); unsaved changes of it stay pending. */
  const lockBoundary = useCallback(() => void dispatch(setTool('select')), [dispatch]);
  // The indoor empty state's "Grundriss zeichnen" starts the mode once, when the editor mounts.
  const boundaryStarted = useRef(false);
  useEffect(() => {
    if (!initialBoundaryOpen || boundaryStarted.current) return;
    boundaryStarted.current = true;
    startBoundary();
  }, [initialBoundaryOpen, startBoundary]);
  const boundaryTexts = `${PREFIX}.boundary.${indoor ? 'indoor' : 'garden'}`;
  const boundaryEntry = useMemo<MenuAction>(() => {
    if (boundaryMode !== null) {
      return {
        id: 'boundary',
        label: t(`${boundaryTexts}.lock`),
        secondary: t(`${PREFIX}.boundary.lockHint`),
        icon: <LockIcon fontSize="small" />,
        onClick: lockBoundary,
        testId: 'garden-plan-menu-boundary',
      };
    }
    const locked = boundary !== null;
    return {
      id: 'boundary',
      label: t(`${boundaryTexts}.${locked ? 'unlock' : 'draw'}`),
      secondary: t(`${PREFIX}.boundary.${locked ? 'entryUnlockHint' : 'entryDrawHint'}`),
      icon: locked ? <LockOpenIcon fontSize="small" /> : <DrawOutlinedIcon fontSize="small" />,
      onClick: startBoundary,
      testId: 'garden-plan-menu-boundary',
    };
  }, [boundary, boundaryMode, boundaryTexts, lockBoundary, startBoundary, t]);

  // The rare actions of the header bar's overflow (§17.3 target picture; GP-UX-046/052/066). Entries that stand in for
  // a former button keep its test id (GP-UX-070). "Add with dimensions" lives in the sub-menus of the tool bar
  // (WP 10.4); while the tab "Liste" hides the tool bar, the overflow offers it, so the list keeps a way to add.
  // "Save as template" is there only while exactly one bed is selected (AC-4) - not as a disabled entry. Below md the
  // rotation step of the tool bar's selection group stands in here too, while something is selected on the plan, so
  // the group stays one row on a phone (#2904); its entries keep the test ids of the rail's toggles (GP-UX-070).
  const angleStepInOverflow = toolbarBelow && view !== 'list' && selection.some(isPlanEntity);
  const overflowItems = useMemo<MenuAction[]>(
    () => [
      ...(view === 'list'
        ? [
            {
              id: 'addWithDimensions',
              label: t(`${PREFIX}.addWithDimensions.open`),
              icon: <AddBoxOutlinedIcon fontSize="small" />,
              onClick: () => openAddWithDimensions('bed'),
              testId: 'garden-plan-add-with-dimensions',
            },
          ]
        : []),
      ...(singleBed
        ? [
            {
              id: 'saveTemplate',
              label: t(`${PREFIX}.templates.save.button`),
              icon: <BookmarkAddOutlinedIcon fontSize="small" />,
              onClick: () => setSaveTemplateOpen(true),
              testId: 'garden-plan-save-template-button',
            },
          ]
        : []),
      {
        id: 'selectAll',
        label: t(`${PREFIX}.contextMenu.selectAll`),
        icon: <SelectAllIcon fontSize="small" />,
        onClick: doSelectAll,
      },
      {
        id: 'multiDuplicate',
        label: t(`${PREFIX}.contextMenu.multiDuplicate`),
        icon: <ContentCopyOutlinedIcon fontSize="small" />,
        onClick: () => setMultiOpen(true),
        disabled: !selection.some(isPlanEntity),
      },
      ...(angleStepInOverflow
        ? ANGLE_STEPS.map<MenuAction>((step, index) => ({
            id: `angle-${step}`,
            label: t(`${PREFIX}.angleStep.label`, { step }),
            icon: <RotateRightIcon fontSize="small" />,
            kind: 'radio',
            checked: angleStep === step,
            onClick: () => setAngleStep(step),
            testId: `garden-plan-angle-${step}`,
            separated: index === 0,
          }))
        : []),
      {
        id: 'underlay',
        label: t(`${UNDERLAY}.open`),
        icon: <ImageIcon fontSize="small" />,
        onClick: () => setUnderlayOpen(true),
        testId: 'garden-plan-underlay-open',
        separated: true,
      },
      // The boundary needs the drawing: the entry is there while the plan is shown (#2890).
      ...(view === 'plan' ? [boundaryEntry] : []),
      // The irrigation zones (§14) are the panel tab "Zonen"; this entry opens the panel on it in one step and keeps
      // the test id of the former zone button (GP-UX-070).
      {
        id: 'zones',
        label: t(`${ZONES}.open`),
        icon: <WaterDropIcon fontSize="small" />,
        onClick: () => {
          setZonesFocus(true);
          showPanelTab('zones');
        },
        testId: 'garden-plan-zones-open',
      },
      {
        id: 'keyboardHelp',
        label: t(`${PREFIX}.keyboard.open`),
        icon: <KeyboardIcon fontSize="small" />,
        onClick: openHelp,
        testId: 'garden-plan-keyboard-help-button',
      },
    ],
    [
      angleStep,
      angleStepInOverflow,
      boundaryEntry,
      doSelectAll,
      openAddWithDimensions,
      openHelp,
      selection,
      showPanelTab,
      singleBed,
      t,
      view,
    ],
  );

  /** Right click (mouse and pen): the object under the pointer, in a menu at the pointer (GP-FR-027). */
  const onContextMenu = useCallback(
    (event: React.MouseEvent<HTMLElement>) => {
      touch.containerProps.onContextMenu(event);
      if (touch.lastPointerType() === 'touch') return; // touch: the "⋯" button of the panel
      event.preventDefault();
      const box = event.currentTarget.getBoundingClientRect();
      const pointPx: Point = [
        event.clientX - box.left - event.currentTarget.clientLeft,
        event.clientY - box.top - event.currentTarget.clientTop,
      ];
      const top = stackRefs(plan, renderer.hitTestAll(pointPx)).find(isPlanEntity);
      if (!top) return;
      if (!isSelected(selection, top)) {
        dispatch(setSelection([top]));
        dispatch(setStack(null));
      }
      setMenuAnchor({ kind: 'position', x: event.clientX, y: event.clientY });
    },
    [dispatch, plan, renderer, selection, touch],
  );

  const selectedKeys = useMemo<RenderSelection>(
    () => ({ selectedKeys: new Set(selection.map((ref) => ref.key)) }),
    [selection],
  );
  // Enter or Space on a focused object picks it - the keyboard way to a selection.
  const onActivateKey = useCallback(
    (key: string) => {
      const ref = resolveRef(plan, key);
      if (ref) {
        dispatch(setSelection([ref]));
        dispatch(setStack(null));
      }
    },
    [dispatch, plan],
  );

  const onListSelect = useCallback(
    (ref: (typeof selection)[number]) => {
      dispatch(setSelection([ref]));
      dispatch(setStack(null));
    },
    [dispatch],
  );
  const showList = useCallback(() => {
    pendingFocus.current = 'list';
    changeView('list');
  }, [changeView]);
  const showPlan = useCallback(() => {
    pendingFocus.current = 'plan';
    changeView('plan');
  }, [changeView]);
  // Buttons that disappear once they have acted must not take the focus with them.
  const thenFocusPlan = useCallback(
    (action: () => void) => () => {
      action();
      focusPlan();
    },
    [focusPlan],
  );

  // The renderer output depends on the plan, view and selection only - not on the pointer.
  const rendered = useMemo(
    () => renderer.render(plan, viewport, selectedKeys, {
        labels,
        // The overlay prints the selection's dimensions, clear of the handles (GP-UX-047).
        dimensionsOnOverlay: true,
        onActivateKey,
        invalidKeys,
        underlayLayer: underlayState.entry,
        ...zoneLayers,
        sunLayer: layerPrefs.sun,
        moistureLayer: layerPrefs.moisture,
        frostLayer: frostShown,
        ...(plantStateLayer ? { plantStateLayer, phaseColors } : {}),
        ...(companionLayer ? { companionLayer } : {}),
      }),
    [
      renderer,
      plan,
      viewport,
      selectedKeys,
      labels,
      onActivateKey,
      invalidKeys,
      zoneLayers,
      underlayState.entry,
      layerPrefs.sun,
      layerPrefs.moisture,
      frostShown,
      plantStateLayer,
      phaseColors,
      companionLayer,
    ],
  );

  // The rail's "Set point" of the measure tool was focused or used: the crosshair it aims with is shown and the status
  // speaks of the keyboard path (GP-UX-071, WCAG 2.1.1). A mouse user who never touches it sees neither.
  const [measureAim, setMeasureAim] = useState(false);
  const aimMeasure = useCallback(() => setMeasureAim(true), []);
  const selectChooseTool = useCallback(
    (next: EditorTool) => {
      dispatch(setTool(next));
      setMeasureAim(false);
      setTemplateMode(null);
      setGhostPoint(null);
      // A shape the new tool does not offer falls back to its first (a bed is no line, §9.5).
      const shapes = TOOL_DEFS[next].draw?.shapes;
      if (shapes && !shapes.includes(drawShape)) setDrawShape(shapes[0]);
    },
    [dispatch, drawShape],
  );

  // On a phone the selected object is panned above the sheet that opens for it (GP-UX-052).
  const selectionSignature = selection.map((ref) => `${ref.entity}:${ref.key}`).join('|');
  const latestView = useRef({ plan, renderer, onPan, selection });
  useEffect(() => {
    latestView.current = { plan, renderer, onPan, selection };
  });
  const isPointerDown = tools.isPointerDown;
  // A panel docked beside the canvas narrows it while the plan keeps its fit (`fitReservePx`): a selection on the
  // right may now lie beyond the canvas edge. It pans back into the visible width (WCAG 2.2 SC 2.4.11, #2885).
  const panelBeside = panelVariant === 'docked' && sidePanel.open && view === 'plan';
  const canvasWidthPx = canvasArea?.widthPx;
  useEffect(() => {
    if (selectionSignature === '' || (!toolbarBelow && !panelBeside)) return;
    const run = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const latest = latestView.current;
      const ref = latest.selection.length === 1 ? latest.selection[0] : null;
      if (!ref || !isPlanEntity(ref)) return;
      const source =
        ref.entity === 'location' ? latest.plan.locations[ref.key] : latest.plan.gardenObjects[ref.key];
      const bbox = source?.bbox;
      if (!bbox) return;
      const corners = [
        latest.renderer.toScreen([bbox[0], bbox[1]]),
        latest.renderer.toScreen([bbox[2], bbox[3]]),
      ];
      const canvasRect = canvas.getBoundingClientRect();
      let dx = 0;
      let dy = 0;
      // Phones: above the sheet and the docked bars.
      const dock = toolbarBelow ? dockRef.current : null;
      const freeHeight = dock ? dock.getBoundingClientRect().top - canvasRect.top : 0;
      if (freeHeight > 0) {
        const ys = corners.map((corner) => corner[1]);
        dy = panIntoView(Math.min(...ys), Math.max(...ys), freeHeight);
      }
      // md and up: left of the docked panel, inside the canvas area.
      const area = panelBeside ? canvasAreaRef.current : null;
      const freeWidth = area ? area.getBoundingClientRect().right - canvasRect.left : 0;
      if (freeWidth > 0) {
        const xs = corners.map((corner) => corner[0]);
        dx = panIntoView(Math.min(...xs), Math.max(...xs), freeWidth);
      }
      if (dx !== 0 || dy !== 0) latest.onPan(dx, dy);
    };
    if (isPointerDown()) panDeferred.current = true;
    else run();
  }, [selectionSignature, toolbarBelow, panelBeside, canvasWidthPx, isPointerDown, panAfterRelease]);

  const code = notice ?? editError;
  const noticeText = code
    ? t(`${PREFIX}.notice.${code}`, { defaultValue: t(`${PREFIX}.notice.generic`) })
    : null;
  const handles = tools.handles;
  // One projection per viewport (SCR-006): the function changes when the plan moves and stays the same otherwise, so
  // the overlay's memos (dimension text placement) hold across renders that do not move it. It is the projection
  // every renderer uses (`BasePlanRenderer.toScreen` reads the viewport the frame was drawn with, this one).
  const toScreen = useCallback((pointM: Point): Point => projectToScreen(viewport, pointM), [viewport]);
  const handlesPx = useMemo(
    () => handles?.handles.map((handle) => toScreen(handle.pointM)),
    [handles, toScreen],
  );
  const singleTooSmall = handles !== null && handles.density === 'none';
  // GP-UX-048: an object too small for handles offers "zoom in to edit" - the zoom at which it gets its full set of
  // handles (capped at the highest zoom), around its centre, so it stays where it is on screen. Absent when even the
  // highest zoom would leave it without handles (SCR-003): the button would change nothing the hint speaks of.
  // The button disappears with the hint once the handles are there, so focus moves to the object (else to the plan
  // region) instead of dropping to the page (SCR-002, WCAG 2.4.3).
  const zoomToEdit = useMemo(() => {
    if (!singleTooSmall || !onZoom || selection.length !== 1) return null;
    const ref = selection[0];
    if (!isPlanEntity(ref)) return null;
    const source = ref.entity === 'location' ? plan.locations[ref.key] : plan.gardenObjects[ref.key];
    const pxPerMTarget = source?.geometry ? zoomToEditPxPerM(source.geometry, MAX_PX_PER_M) : null;
    const bbox = source?.bbox;
    if (pxPerMTarget === null || pxPerMTarget <= pxPerM || !bbox) return null;
    const centreM: Point = [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2];
    return { key: ref.key, pxPerM: pxPerMTarget, centreM };
  }, [singleTooSmall, onZoom, pxPerM, selection, plan]);
  const onZoomToEdit = useCallback(() => {
    if (!zoomToEdit || !onZoom) return;
    pendingFocus.current = { key: zoomToEdit.key };
    onZoom(zoomToEdit.pxPerM, toScreen(zoomToEdit.centreM));
  }, [zoomToEdit, onZoom, toScreen]);

  // The boundary is drawn with the same steps and hints as a bed (#2890).
  const drawing = drawTool;
  // The crosshair and the touch bar's "set point" serve every tool that sets points: drawing and measuring.
  const settingPoints = toolBehaviour.touch === 'points';
  // The type choice of a new bed or garden object (WP 2.6); the boundary has none.
  const drawTarget = drawTool && boundaryMode === null ? TOOL_DEFS[tool].draw?.target : undefined;
  const newObjectTarget =
    drawTarget === 'area' || drawTarget === 'bed' || drawTarget === 'garden_object' ? drawTarget : null;
  // The measure tool's status (GP-UX-071): what to do next and the measured total as text, announced politely - the
  // canvas overlay is hidden from assistive technology. It speaks of fixed points only, never of the hover.
  const measure = tools.measure;
  // Below md and with a coarse pointer the TouchBar carries "Set point"; elsewhere the rail offers it (GP-UX-071).
  const railMeasure = canvasKind === 'measure' && !touchUi;
  const aiming = railMeasure && measureAim;
  const { placePointAt, finishDraw } = tools;
  const measureControls = railMeasure
    ? {
        finishable: tools.measureFinishable,
        onPlace: () => placePointAt([viewport.widthPx / 2, viewport.heightPx / 2]),
        onFinish: finishDraw,
        onAim: aimMeasure,
      }
    : undefined;
  const measureStatus =
    canvasKind === 'measure'
      ? measureStatusText(t, measure, touchUi ? 'touch' : aiming ? 'keyboard' : 'pointer', unit, i18n.language)
      : null;
  // With a finger the hints speak of the crosshair and "Set point" - dragging would pan the plan.
  const hintBase = touchUi ? `${PREFIX}.touch.hint` : `${PREFIX}.drawHint`;
  const hintKey = !drawing
    ? null
    : tools.draftPoints > 0
      ? `${hintBase}.${drawShape}.next`
      : `${hintBase}.${drawShape}.start`;

  // The selection group of the tool bar exists only while something is selected (GP-UX-066, AC-4).
  const hasSelection = selection.some(isPlanEntity);
  const selectionGroup = useMemo<ToolbarSelectionGroup | null>(
    () =>
      hasSelection
        ? {
            angleStep,
            onAngleStep: setAngleStep,
            onDelete: requestDelete,
            align: {
              canAlign: availability.align,
              canDistribute: availability.distribute,
              onAlign: align,
              onDistribute: distribute,
            },
          }
        : null,
    [align, angleStep, availability, distribute, hasSelection, requestDelete],
  );
  // One tool bar, two forms (GP-UX-069): the rail left of the canvas from md up, the bar docked at the bottom below.
  const toolbar = (
    <EditorToolbar
      orientation={toolbarBelow ? 'horizontal' : 'vertical'}
      tool={tool}
      onTool={selectChooseTool}
      drawShape={drawShape}
      onDrawShape={setDrawShape}
      draftPoints={tools.draftPoints}
      onFinishDraw={thenFocusPlan(tools.finishDraw)}
      onCancelDraw={thenFocusPlan(tools.cancel)}
      vertexPicked={tools.vertex !== null}
      canDeleteVertex={tools.vertex !== null}
      onDeleteVertex={thenFocusPlan(tools.deleteVertex)}
      onInsertVertex={thenFocusPlan(tools.insertVertexAfter)}
      templateActive={templateTool}
      onTemplate={toggleTemplateTool}
      onAddWithDimensions={openAddWithDimensions}
      selectionGroup={selectionGroup}
      boundaryMode={boundaryMode}
      measure={measureControls}
    />
  );

  const centerPx: Point = [viewport.widthPx / 2, viewport.heightPx / 2];

  const bedInfo = useCallback(
    (bedKey: string) => (
      <BedZoneInfo bedKey={bedKey} zones={zoneData.zones} lastWateredAt={lastWateredAt[bedKey]} nowMs={nowMs} />
    ),
    [zoneData.zones, lastWateredAt, nowMs],
  );
  const selectedBedKeys = useMemo(
    () => selection.filter((ref) => ref.entity === 'location').map((ref) => ref.key),
    [selection],
  );

  const sheetOpen = panelVariant === 'sheet' && sidePanel.open;
  const closeSidePanel = sidePanel.close;
  /**
   * The panel's close button (and the zone panel's). The bottom sheet was the selection's sheet before wave 10 and
   * still clears it (GP-UX-052, the touch tests stay as they are); the focus goes to the plan or the list then. The
   * docked panel only collapses - the selection stays - and gives the focus back to its switch.
   */
  const closePanel = useCallback(() => {
    if (panelVariant === 'sheet' && panelSelection !== '') {
      onSelect([]);
      onStack(null);
      focusSurface(); // the close button disappears with the sheet: keep the focus on the plan or the list
    } else {
      focusToggleAfterClose.current = true;
    }
    closeSidePanel();
  }, [panelVariant, panelSelection, onSelect, onStack, focusSurface, closeSidePanel]);

  const viewBar = (
    <ViewBar
      gridStepM={gridStepM}
      onGridStep={setGridStepM}
      gridVisible={gridVisible}
      onGridVisible={setGridVisible}
      snapEnabled={snapEnabled}
      onSnapEnabled={setSnapEnabled}
      unit={unit}
      onUnit={setUnit}
      northAngleDeg={northAngleDeg}
      onNorthAngle={onNorthAngle}
      sunDirections={plan.sunDirections}
    />
  );

  // Only the active tab's content is built and mounted (the zone panel reads its endpoint only while it is open).
  let panelContent: ReactNode;
  if (sidePanel.tab === 'properties') {
    panelContent = (
      <PropertiesPanel
        plan={plan}
        selection={selection}
        stack={stack}
        labels={labels}
        layout={panelVariant === 'sheet' ? 'sheet' : 'sidebar'}
        onCommit={onCommit}
        onSelect={onSelect}
        onStack={onStack}
        onMore={(element) => setMenuAnchor({ kind: 'element', element })}
        moreOpen={menuAnchor?.kind === 'element'}
        onDuplicate={duplicate}
        onDelete={requestDelete}
        onZOrder={moveInZ}
        onDrawBed={() => dispatch(setTool('bed'))}
        onOpenLocation={onOpenLocation}
        onOpenCare={onOpenCare}
        bedInfo={bedInfo}
      />
    );
  } else if (sidePanel.tab === 'view') {
    panelContent = viewBar;
  } else if (sidePanel.tab === 'layers') {
    panelContent = (
      <LayersTab
        layerToggles={layerToggles}
        onLayer={setLayerById}
        attentionFilter={attentionFilter}
        legend={
          // GP-UX-005: the layer legend and the object legend (GP-FR-180, WP 10.6), hidden together by the switch.
          <Stack spacing={2}>
            <ZoneLegend
              zones={zoneData.zones}
              showZones={layerPrefs.zones}
              showLastWatered={layerPrefs.lastWatered}
              showSun={layerPrefs.sun}
              showMoisture={layerPrefs.moisture}
              showFrost={frostShown}
              showPlantState={plantStateOn}
              phases={legendPhases}
              showCompanion={companionOn}
              companionCapped={companionCapped}
              companionPairs={companionPairs}
            />
            <ObjectLegend objects={plan.gardenObjects} objectTypeLabel={labels.objectType} />
          </Stack>
        }
      />
    );
  } else {
    panelContent = (
      // A chunk that cannot load (typically gone after a deploy) stays rejected for the life of the page:
      // the fallback offers the reload, not a retry that would fail the same way.
      <ErrorBoundary
        title={t(`${ZONES}.panel.chunkFailedTitle`)}
        hint={t(`${ZONES}.panel.chunkFailedHint`)}
        reloadLabel={t('common.appError.reloadPage')}
        testId="garden-plan-zone-panel-error"
        boundaryName="garden-plan-zone-panel"
      >
        <Suspense fallback={<Box sx={{ minHeight: 120 }} aria-busy="true" />}>
          <ZonePanel
            plan={plan}
            zoneData={zoneData}
            selectedBedKeys={selectedBedKeys}
            onChanged={onZonesChanged}
            onWatered={onWatered}
            onClose={closePanel}
            focusOnOpen={zonesFocus}
          />
        </Suspense>
      </ErrorBoundary>
    );
  }
  const sidePanelElement = (
    <SidePanel
      variant={panelVariant}
      open={sidePanel.open}
      tab={sidePanel.tab}
      onTab={chooseTab}
      onClose={closePanel}
      heightPx={canvasArea && view === 'plan' ? canvasArea.heightPx : undefined}
      visibleHeight={visibleHeight}
      sheetSize={sheetSize}
      onSheetSize={setSheetSize}
    >
      {panelContent}
    </SidePanel>
  );

  // A task badge on a bed opens its care tab (GP-FR-089). The press that lands on it starts no gesture (a pan or the
  // first finger of a pinch would otherwise select or drag the bed), and the tab opens on the click that follows:
  // a click exists only when the pointer went down and up on the badge itself, so a drag that merely starts there
  // opens nothing. The canvas would capture the pointer and swallow that click, which is why the press is not
  // handed to the tools at all.
  // The template tool takes the press the same way: the click that follows places the template, so no
  // gesture (selection, marquee, pan) may start under it.
  // With Space held (GP-FR-010) every press goes to the tools, which pan; the click that follows it places, opens and
  // pins nothing.
  const touchPointerDown = touch.containerProps.onPointerDown;
  const spacePanPress = useRef(false);
  const panModifier = tools.panModifier;
  const onCanvasPointerDown = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      spacePanPress.current = panModifier && event.button === 0 && event.pointerType !== 'touch';
      if (spacePanPress.current) {
        touchPointerDown(event);
        return;
      }
      if (templateTool && event.button === 0) return;
      if (onOpenCare && tool === 'select' && event.button === 0 && badgeKeyOf(event) !== null) return;
      // A mouse press on a companion line opens its card on the click that follows, like the task badge: no gesture
      // starts. A finger is not skipped: the touch layer lets it pan and pinch and pins the card on a plain tap.
      if (
        companionOn &&
        tool === 'select' &&
        event.button === 0 &&
        event.pointerType !== 'touch' &&
        companionEdgeOf(event) !== null
      ) {
        return;
      }
      touchPointerDown(event);
    },
    [companionOn, onOpenCare, panModifier, templateTool, tool, touchPointerDown],
  );
  const onCanvasClick = useCallback(
    (event: ReactMouseEvent<HTMLElement>) => {
      if (spacePanPress.current) return;
      if (templateTool) {
        const box = event.currentTarget.getBoundingClientRect();
        const pointM = renderer.toModel([
          event.clientX - box.left - event.currentTarget.clientLeft,
          event.clientY - box.top - event.currentTarget.clientTop,
        ]);
        // The same tolerance as the ghost shown under the pointer (a finger or a pen snaps wider).
        const kind = 'pointerType' in event.nativeEvent ? String(event.nativeEvent.pointerType) : 'mouse';
        void placeTemplate(snapPoint(pointM, event.altKey, snapPointerType(kind)));
        return;
      }
      if (companionOn && tool === 'select') {
        const edge = companionEdgeOf(event);
        // A finger's tap on a line pinned the card on pointer-up; the click that follows a drag must not pin it.
        const fromTouch = 'pointerType' in event.nativeEvent && event.nativeEvent.pointerType === 'touch';
        if (!(edge && fromTouch)) setCompanionPinned(edge);
        if (edge) return;
      }
      const key = badgeKeyOf(event);
      if (key && onOpenCare && tool === 'select') onOpenCare(key);
    },
    [companionOn, onOpenCare, placeTemplate, renderer, snapPoint, templateTool, tool],
  );

  const selectedTemplate = useMemo(
    () => templateCatalogue.templates.find((item) => item.key === templateMode?.templateKey) ?? null,
    [templateCatalogue.templates, templateMode?.templateKey],
  );
  // "Place at centre": the middle of the turned template's box lands on the (snapped) middle of the view (#2536).
  const viewCentreX = viewport.widthPx / 2;
  const viewCentreY = viewport.heightPx / 2;
  const placeAtCentre = useCallback(() => {
    if (!selectedTemplate || !templateMode) return;
    const target = snapPoint(renderer.toModel([viewCentreX, viewCentreY]), false);
    const origin = originForCentre(
      selectedTemplate.default_geometry,
      templateMode.rotationDeg,
      target,
    );
    if (origin) void placeTemplate(origin);
  }, [placeTemplate, renderer, selectedTemplate, snapPoint, templateMode, viewCentreX, viewCentreY]);
  // The ghost turns red where the template would break a rule the client can check (V-01..V-03 against the garden
  // boundary - the server places it without a parent); a bed overlap stays the server's (#2536).
  const ghostInvalid = useMemo(() => {
    if (!selectedTemplate || !templateMode || !ghostPoint) return false;
    const placed = placeGeometry(selectedTemplate.default_geometry, ghostPoint, templateMode.rotationDeg);
    return placed !== null && violationOfNew(plan, placed, null) !== null;
  }, [ghostPoint, plan, selectedTemplate, templateMode]);
  const closeTemplateTool = useCallback(() => {
    setTemplateMode(null);
    setGhostPoint(null);
  }, []);

  // During a move the marker is the moved object's snapped corner or edge point (GP-FR-154), else the pointer's.
  const shownSnapMark = tools.moving ? tools.moveSnap : snapMark;

  // The mini-map shows only for a plan larger than four viewports (GP-UX-014, §9.6).
  const extent = useMemo(() => planContentBounds(plan), [plan]);
  const showMiniMap = extent !== null && miniMapVisible(extent, viewport);
  const jumpTo = useCallback(
    (target: Point) => {
      const [dx, dy] = panToCentre(viewport, target);
      onPan(dx, dy);
    },
    [onPan, viewport],
  );

  // The card of the pinned line, else of the hovered one; it sits at the line's midpoint and follows pan and zoom.
  const companionInfo = useMemo(() => {
    const id = companionOn ? (companionPinned ?? companionHover) : null;
    const edge = id ? companion.edges[id] : undefined;
    if (!id || !edge?.slot_a.position || !edge.slot_b.position) return null;
    const [x, y] = projectToScreen(viewport, [
      (edge.slot_a.position.x + edge.slot_b.position.x) / 2,
      (edge.slot_a.position.y + edge.slot_b.position.y) / 2,
    ]);
    return { edge, x, y, pinned: id === companionPinned };
  }, [companionOn, companionPinned, companionHover, companion.edges, viewport]);

  const listShown = view === 'list';
  const canvasSurface = (
    <Box
      ref={canvasRef}
      id={EDITOR_ANCHORS.canvas}
      data-testid="garden-plan-canvas"
      role="region"
      aria-label={labels.canvas}
      // The region takes the editor's keys (arrows, Esc, Del, Ctrl+A); it must be reachable by keyboard (WCAG 2.1.1).
      tabIndex={0}
      {...touch.containerProps}
      onPointerDown={onCanvasPointerDown}
      onClick={onCanvasClick}
      onPointerLeave={onPointerLeave}
      onContextMenu={onContextMenu}
      sx={{
        position: 'relative',
        overflow: 'hidden',
        touchAction: 'none',
        userSelect: 'none',
        cursor: cursorOf(toolBehaviour, tools.panModifier),
        border: 1,
        borderColor: 'divider',
        borderRadius: 1,
        bgcolor: 'background.paper',
        boxSizing: 'border-box',
        // The area has its height once measured (GP-UX-067); the canvas fills it, the plan is fitted into it.
        height: canvasArea ? '100%' : undefined,
        '&:focus-visible': {
          outline: 3,
          outlineStyle: 'solid',
          outlineColor: 'primary.main',
          outlineOffset: 2,
        },
      }}
    >
      {/* The plan layer: drawing, grid and the editor's overlays. A pending wheel zoom transforms all of it at once. */}
      <Box ref={attachZoomLayer} sx={{ position: 'relative', transformOrigin: '0 0' }} data-testid="garden-plan-zoom-layer">
        {rendered}
        {gridVisible && <Grid viewport={viewport} stepM={gridStepM} />}
        {companionInfo && (
          <Suspense fallback={null}>
            <CompanionEdgeInfo
              edge={companionInfo.edge}
              x={companionInfo.x}
              y={companionInfo.y}
              canvasWidthPx={viewport.widthPx}
              canvasHeightPx={viewport.heightPx}
              pinned={companionInfo.pinned}
              onClose={closeCompanionInfo}
            />
          </Suspense>
        )}
        {/* A move re-renders only this layer: the editor stays as it is until the gesture ends (GP-NFR-033). */}
        <LiveMoveLayer
          liveMove={tools.liveMove}
          overlay={tools.overlay}
          dimensionItems={dimensionItems}
          snapMark={shownSnapMark}
          handles={handles}
          handlesPx={handlesPx}
        >
          {(live) => (
            <EditorOverlay
              overlay={live.overlay}
              handles={live.handles}
              vertex={tools.vertex}
              toScreen={toScreen}
              pxPerM={viewport.pxPerM}
              widthPx={viewport.widthPx}
              heightPx={viewport.heightPx}
            >
              <DimensionLabels
                items={live.dimensionItems}
                toScreen={toScreen}
                unit={unit}
                handlesPx={live.handlesPx}
                heightPx={viewport.heightPx}
              />
              {measure && (
                <MeasureOverlay measure={measure} toScreen={toScreen} unit={unit} widthPx={viewport.widthPx} />
              )}
              {selectedTemplate && ghostPoint && templateMode && (
                <TemplateGhost
                  template={selectedTemplate}
                  invalid={ghostInvalid}
                  originM={ghostPoint}
                  rotationDeg={templateMode.rotationDeg}
                  toScreen={toScreen}
                  pxPerM={pxPerM}
                />
              )}
              {live.snapMark && (
                <SnapMarker
                  mark={live.snapMark}
                  toScreen={toScreen}
                  widthPx={viewport.widthPx}
                  heightPx={viewport.heightPx}
                />
              )}
            </EditorOverlay>
          )}
        </LiveMoveLayer>
      </Box>
      {/* Overlays in the corners of the canvas (GP-UX-067): they take no row of their own. */}
      <ScaleBar pxPerM={pxPerM} />
      {showMiniMap && extent && (
        <MiniMap plan={plan} extent={extent} viewport={viewport} onJump={jumpTo} />
      )}
      <TouchOverlay
        ring={touch.ring}
        crosshair={(touchUi && settingPoints) || aiming ? centerPx : null}
        widthPx={viewport.widthPx}
        heightPx={viewport.heightPx}
      />
    </Box>
  );

  // Below md undo and redo stand in the TouchBar while it is on screen (GP-UX-052/063); otherwise in the header bar.
  const undoInTouchBar = toolbarBelow && !listShown && !contentHidden;
  const touchBar = touchUi ? (
    <TouchBar
      tool={tool}
      drawing={settingPoints}
      measureFinishable={tools.measureFinishable}
      drawShape={drawShape}
      draftPoints={tools.draftPoints}
      onPlacePoint={() => tools.placePointAt(centerPx)}
      onUndoPoint={tools.undoPoint}
      onFinish={tools.finishDraw}
      onCancel={tools.cancel}
      multiSelect={multiSelect}
      onMultiSelect={setMultiSelect}
      leading={undoInTouchBar ? <UndoRedoButtons /> : undefined}
    />
  ) : null;

  // The switch of the side panel in the header bar (GP-UX-068): `aria-expanded`, `aria-controls` on the panel.
  const togglePanel = sidePanel.toggle;
  const panelToggle = useMemo(
    () => ({
      label: t(`${SIDE_PANEL}.toggle`),
      menuLabel: t(`${SIDE_PANEL}.toggleMenu`),
      icon: <ViewSidebarOutlinedIcon />,
      expanded: panelOpen,
      controls: EDITOR_ANCHORS.panel,
      onToggle: togglePanel,
      testId: 'garden-plan-panel-toggle',
    }),
    [t, panelOpen, togglePanel],
  );
  // While the tabs are in the overflow the content panel is named by its tab's label instead of the tab element.
  const [tabsInline, setTabsInline] = useState(true);
  const tabsInlineChanged = tabs?.onInlineChange;
  const onTabsInline = useCallback(
    (inline: boolean) => {
      setTabsInline(inline);
      tabsInlineChanged?.(inline);
    },
    [tabsInlineChanged],
  );

  const header = (
    <EditorHeaderBar
      autoSave={autoSave}
      narrow={toolbarBelow}
      undoRedo={!undoInTouchBar}
      nav={nav}
      tabs={tabs}
      onTabsInline={onTabsInline}
      panelToggle={panelToggle}
      panelButtonRef={panelButtonRef}
      overflowItems={overflowItems}
      overflowButtonRef={overflowButtonRef}
    />
  );

  const above = (
    <>
      <SaveMessages autoSave={autoSave} />
      {/* The view settings, layers and legend are tabs of the side panel (WP 10.5); nothing else stands above the
          plan but messages and the hints of the tool in use. */}
      {!listShown && !toolbarBelow && touchBar}
      {!listShown && newObjectTarget && (
        <NewTypeSelect
          target={newObjectTarget}
          labels={labels}
          bedTypes={bedTypes}
          bedTypeKey={bedTypeKey}
          onBedTypeKey={setBedTypeChoice}
          objectType={objectType}
          onObjectType={setObjectType}
          areaTypes={areaTypes}
          areaTypeKey={areaTypeKey}
          onAreaTypeKey={setAreaTypeChoice}
        />
      )}
      {!listShown && templateMode && (
        <Suspense fallback={null}>
          <TemplatePanel
            catalogue={templateCatalogue}
            templateKey={templateMode.templateKey}
            onTemplateKey={(key) =>
              setTemplateMode((previous) =>
                previous ? { ...previous, templateKey: key, createRecurringTasks: false } : previous,
              )
            }
            createRecurringTasks={templateMode.createRecurringTasks}
            onCreateRecurringTasks={(value) =>
              setTemplateMode((previous) => (previous ? { ...previous, createRecurringTasks: value } : previous))
            }
            rotationDeg={templateMode.rotationDeg}
            onRotate={() =>
              setTemplateMode((previous) =>
                previous
                  ? { ...previous, rotationDeg: (previous.rotationDeg + TEMPLATE_TURN_DEG) % 360 }
                  : previous,
              )
            }
            busy={placing}
            onPlaceCenter={placeAtCentre}
            ghostInvalid={ghostInvalid}
            onClose={closeTemplateTool}
          />
        </Suspense>
      )}
      {!listShown && boundaryMode && (
        // The boundary mode says what is going on and how it ends (GP-FR-032): drawing, or unlocked for editing.
        <Alert
          severity="info"
          role="status"
          data-testid="garden-plan-boundary-mode"
          data-mode={boundaryMode}
          icon={boundaryMode === 'edit' ? <LockOpenIcon /> : <DrawOutlinedIcon />}
          action={
            <Tooltip title={t(`${PREFIX}.boundary.${boundaryMode === 'edit' ? 'lockHint' : 'cancelHint'}`)}>
              <Button
                color="inherit"
                size="small"
                startIcon={boundaryMode === 'edit' ? <LockIcon /> : <CloseIcon />}
                onClick={thenFocusPlan(lockBoundary)}
                data-testid="garden-plan-boundary-done"
                sx={{ minHeight: 48 }}
              >
                {t(`${PREFIX}.boundary.${boundaryMode === 'edit' ? 'done' : 'cancel'}`)}
              </Button>
            </Tooltip>
          }
        >
          {t(`${boundaryTexts}.${boundaryMode === 'edit' ? 'editHint' : 'drawHint'}`)}
        </Alert>
      )}
      {!listShown && hintKey && (
        <Typography
          variant="body2"
          color="text.secondary"
          role="status"
          data-testid="garden-plan-draw-hint"
        >
          {t(hintKey, { count: tools.draftPoints })}
        </Typography>
      )}
      {!listShown && measureStatus && (
        <Typography
          variant="body2"
          color="text.secondary"
          role="status"
          aria-live="polite"
          data-testid="garden-plan-measure-status"
          data-done={measure?.done ? 'true' : 'false'}
        >
          {measureStatus}
        </Typography>
      )}
      {noticeText && (
        <Alert
          severity="warning"
          role="status"
          data-testid="garden-plan-notice"
          onClose={() => {
            setNotice(null);
            dispatch(clearEditError());
          }}
        >
          {noticeText}
        </Alert>
      )}
      {info && (
        <Alert
          severity="success"
          role="status"
          data-testid="garden-plan-info"
          onClose={() => setInfo(null)}
        >
          {info}
        </Alert>
      )}
    </>
  );

  // The side panel has ONE place in the tree for both of its forms (GP-UX-069, G-W10 b, #2882): the last item of the
  // canvas row. From md up its box takes no box of its own (`display: contents`), so the panel is the row's item
  // beside the canvas; below md the same box is the bottom dock - a sticky line of its own under the canvas holding the
  // sheet above the TouchBar and the tool bar. A resize across md only restyles it: what the panel holds (an open
  // dialog, a typed draft) stays mounted. A portal into a slot per form would not do: a portal whose container
  // changes mounts its content anew.
  // Below md the dock also carries the bars (none behind the list, unless the sheet is open over it).
  const panelSlotShown = toolbarBelow ? !listShown || sheetOpen : sidePanel.open;
  const body = (
    <Box sx={{ minWidth: 0 }}>
      <Box
        sx={{
          display: 'flex',
          flexWrap: toolbarBelow ? 'wrap' : 'nowrap',
          gap: 1,
          alignItems: 'flex-start',
          minWidth: 0,
        }}
      >
        {listShown ? (
          <Box ref={listRef} sx={{ flex: 1, minWidth: 0 }}>
            <PlanListView
              plan={plan}
              labels={labels}
              selection={selection}
              stepM={gridStepM}
              onSelect={onListSelect}
              onMove={keyboard.moveSelection}
              onRequestDelete={requestDelete}
            />
          </Box>
        ) : (
          <>
            {/* The tool rail (md up, GP-UX-066) is as high as the canvas area and scrolls inside when it is longer. */}
            {!toolbarBelow && (
              <Box
                style={canvasArea ? { height: canvasArea.heightPx } : undefined}
                sx={{ display: 'flex', flex: 'none' }}
              >
                {toolbar}
              </Box>
            )}
            {/* The canvas area: the rest of the viewport height, at least 400 px (GP-UX-067); the zoom sits on it. */}
            <Box
              ref={canvasAreaRef}
              data-testid="garden-plan-canvas-area"
              // A measured value that changes with every resize: an inline style, not one generated class per pixel.
              style={canvasArea ? { height: canvasArea.heightPx } : undefined}
              sx={{ position: 'relative', flex: '1 1 0', minWidth: 0, overflow: 'hidden' }}
            >
              {canvasSurface}
              {!listShown && singleTooSmall && (
                // An overlay on the canvas, not a row above it: it takes no layout height (AC-1, GP-UX-067). The
                // wrapper lets pointer events through to the canvas; only the alert itself takes them (its button).
                <Box
                  sx={{ position: 'absolute', left: 8, right: 8, bottom: 48, zIndex: 1, pointerEvents: 'none' }}
                >
                  <Alert
                    severity="info"
                    role="status"
                    aria-live="polite"
                    data-testid="garden-plan-too-small"
                    sx={{ maxWidth: 520, pointerEvents: 'auto', boxShadow: 2, py: 0 }}
                    action={
                      zoomToEdit ? (
                        <Button
                          color="inherit"
                          size="small"
                          onClick={onZoomToEdit}
                          data-testid="garden-plan-zoom-to-edit"
                          sx={{ minHeight: 48 }}
                        >
                          {t(`${PREFIX}.zoomToEdit`)}
                        </Button>
                      ) : undefined
                    }
                  >
                    {t(`${PREFIX}.tooSmall`)}
                  </Alert>
                </Box>
              )}
              <ZoomOverlay
                pxPerM={pxPerM}
                minPxPerM={minPxPerM}
                onZoomIn={zoomIn}
                onZoomOut={zoomOut}
                onFit={fit}
              />
            </Box>
          </>
        )}
        {panelSlotShown && (
          <Box
            ref={toolbarBelow ? dockRef : undefined}
            data-testid={toolbarBelow ? 'garden-plan-dock' : undefined}
            sx={
              toolbarBelow
                ? {
                    // A line of its own under the canvas (or the list), docked to the bottom while scrolling.
                    flex: '0 0 100%',
                    minWidth: 0,
                    position: 'sticky',
                    bottom: 0,
                    zIndex: 2,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 0.5,
                  }
                : { display: 'contents' }
            }
          >
            {sidePanelElement}
            {toolbarBelow && (
              <Box ref={dockBarsRef} sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                {!listShown && touchBar}
                {!listShown && toolbar}
              </Box>
            )}
          </Box>
        )}
      </Box>
    </Box>
  );

  const overlays = (
    <>
      {underlayOpen && (
        // A dialog chunk that cannot load (or a dialog that fails to render) says so in place; the plan stays
        // usable. As for the zone panel, the fallback offers the reload, not a retry that would fail the same way.
        <ErrorBoundary
          title={t(`${UNDERLAY}.chunkFailedTitle`)}
          hint={t(`${UNDERLAY}.chunkFailedHint`)}
          reloadLabel={t('common.appError.reloadPage')}
          testId="garden-plan-underlay-error"
          boundaryName="garden-plan-underlay-dialog"
        >
          <Suspense fallback={null}>
            <UnderlayDialog
              open
              siteKey={plan.siteKey}
              underlay={underlayState.underlay}
              onSaved={(next) => {
                underlayState.set(next);
                // A user who hid the layer earlier sees what they just saved.
                if (next !== null) setLayer('underlay', true);
              }}
              onClose={() => setUnderlayOpen(false)}
            />
          </Suspense>
        </ErrorBoundary>
      )}
      <LiveRegion message={announcement} />
      <KeyboardHelp
        open={helpOpen}
        onClose={() => setHelpOpen(false)}
        singleKeyShortcuts={shortcuts.enabled}
        onSingleKeyShortcuts={shortcuts.setEnabled}
      />
      <ContextMenu
        anchor={menuAnchor}
        actions={menuActions}
        onClose={() => setMenuAnchor(null)}
        label={t(`${PREFIX}.contextMenu.label`)}
        id={ITEM_MENU_ID}
      />
      <AddWithDimensionsDialog
        open={addOpen}
        plan={plan}
        labels={labels}
        bedTypes={bedTypes}
        fallbackBedTypeKey={fallbackBedType}
        defaultPosition={renderer.toModel(centerPx)}
        suggestedName={newBedName(nextLocationNumber(plan, false))}
        areaTypes={areaTypes}
        fallbackAreaTypeKey={areaTypeKey}
        suggestedAreaName={newAreaName(nextLocationNumber(plan, true))}
        onAdd={addWithDimensions}
        onClose={() => setAddOpen(false)}
        initialTarget={addTarget}
      />
      {saveTemplateOpen && (
        <Suspense fallback={null}>
          <SaveAsTemplateDialog
            open
            defaultName={singleBed?.name ?? ''}
            onSave={saveAsTemplate}
            onClose={() => setSaveTemplateOpen(false)}
          />
        </Suspense>
      )}
      {multiOpen && (
        <Suspense fallback={null}>
          <MultiDuplicateDialog
            open
            rootBeds={multiRoots}
            unit={unit}
            onRun={runMultiDuplicate}
            onClose={() => setMultiOpen(false)}
          />
        </Suspense>
      )}
      <ConflictDialog />
      <ConfirmDialog
        open={pendingDelete !== null}
        title={deleteTexts.title}
        message={deleteTexts.message}
        confirmLabel={t(`${PREFIX}.deleteDialog.confirm`)}
        destructive
        onConfirm={confirmDelete}
        onCancel={() => setPendingDelete(null)}
      />
    </>
  );

  return (
    <EditorWorkspace
      onKeyDown={onShortcut}
      contentHidden={contentHidden}
      panel={
        tabs
          ? {
              id: tabs.panelId,
              labelledBy: tabsInline ? tabs.items.find((item) => item.value === tabs.value)?.id : undefined,
              label: tabs.items.find((item) => item.value === tabs.value)?.label,
            }
          : undefined
      }
      skipLinks={
        <SkipLinks
          listShown={listShown}
          onToList={showList}
          onToPlan={showPlan}
          onToPanel={focusPanelRegion}
        />
      }
      header={header}
      above={above}
      body={body}
      overlays={overlays}
    />
  );
}

function isLockedRefIn(
  plan: PlanModel,
  ref: { entity: 'location' | 'garden_object'; key: string },
): boolean {
  return (
    (ref.entity === 'location' ? plan.locations[ref.key] : plan.gardenObjects[ref.key])?.locked ===
    true
  );
}
