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
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import KeyboardIcon from '@mui/icons-material/Keyboard';
import ImageIcon from '@mui/icons-material/Image';
import LayersIcon from '@mui/icons-material/Layers';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import WbSunnyOutlinedIcon from '@mui/icons-material/WbSunnyOutlined';
import WavesIcon from '@mui/icons-material/Waves';
import AcUnitIcon from '@mui/icons-material/AcUnit';
import LocalFloristOutlinedIcon from '@mui/icons-material/LocalFloristOutlined';
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
import { isApiError } from '@/api/errors';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { createBedTemplate } from '../api/gardenPlan';
import type { PlanModel } from '../model/planModel';
import { toShape } from '../model/geometry';
import type { GardenObjectType, PlanOperation, Point } from '../model/types';
import { nearestGridStep, stepZoom } from '../model/units';
import type { PlanRenderer, RenderSelection, RendererLabels, Viewport } from '../renderer';
import { snapCandidates } from '../renderer/planIndex';
import { markerLodBedKeys } from '../renderer/scene';
import { colorsOf, usePhaseNames } from '../planting/phaseColors';
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
import { ConflictDialog } from './ConflictDialog';
import { EditorHeaderActions } from './EditorHeaderActions';
import { EditorOverlay } from './EditorOverlay';
import { EditorToolbar, type AngleStep, type EditorTool } from './EditorToolbar';
import { Grid } from './Grid';
import { MiniMap } from './MiniMap';
import { miniMapVisible, panToCentre } from './miniMap';
import { KeyboardHelp } from './KeyboardHelp';
import { LiveRegion } from './LiveRegion';
import { NewTypeSelect } from './NewTypeSelect';
import { PlanListView } from './PlanListView';
import { buildTree, neighbourKey } from './planTree';
import { PropertiesPanel } from './PropertiesPanel';
import { SaveBar } from './SaveBar';
import { ScaleBar } from './ScaleBar';
import { SkipLinks } from './SkipLinks';
import { SnapMarker, type SnapMark } from './SnapMarker';
import { bedFrameGeometry } from '../templates/placeGeometry';
import { TemplateGhost } from '../templates/TemplateGhost';
import { useBedTemplates } from '../templates/useBedTemplates';
import { TouchBar } from './TouchBar';
import { TouchOverlay } from './TouchOverlay';
import { ViewBar, type LayerToggle } from './ViewBar';
import { BedZoneInfo } from '../zones/BedZoneInfo';
import { useUnderlay } from '../underlay/useUnderlay';
import { useIrrigationZones, useLastWatered } from '../zones/useZoneData';
import { useZoneLayers } from '../zones/useZoneLayers';
import { ZoneLegend } from '../zones/ZoneLegend';
import { useAnnouncement } from './useAnnouncement';
import { useBedTypes } from './useBedTypes';
import { useEditorKeyboard } from './useEditorKeyboard';
import { useEditorShortcuts } from './useEditorShortcuts';
import { TOGGLE_LAYERS, type LayerId } from './layers';
import { useLayerPrefs } from './useLayerPrefs';
import { useAttentionFilter } from './useAttentionFilter';
import { useLengthUnit } from './useLengthUnit';
import { useSingleKeyShortcuts } from './useSingleKeyShortcuts';
import { commonBedTypeKey, type DrawShape } from './tools/drawMachine';
import {
  alignAvailability,
  alignSelection,
  distributeSelection,
  type AlignMode,
  type DistributeAxis,
} from './tools/align';
import { duplicateSelection, multiDuplicate, type MultiDuplicateOptions } from './tools/duplicate';
import { deleteImpact, isPlanEntity, moveTargets, selectionRoots, type DeleteImpact } from './tools/hierarchy';
import type { ActionLabel } from './tools/machineTypes';
import { panIntoView } from './tools/touchGestures';
import { isSelected, resolveRef, selectAll, stackRefs } from './tools/selection';
import { resolveSnap, type SnapPointerType } from './tools/snap';
import { useEditorTools } from './tools/useEditorTools';
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
}

/** The wheel zooms stepless: `exp(-deltaY * this)` per event (the buttons and + / - use the fixed levels). */
const WHEEL_ZOOM_PER_PX = 0.0015;

/** The bed whose task badge the event hit (`data-plan-badge`, drawn by the renderer), or `null`. */
function badgeKeyOf(event: { target: EventTarget | null }): string | null {
  const badge = event.target instanceof Element ? event.target.closest('[data-plan-badge]') : null;
  return badge?.getAttribute('data-plan-badge') ?? null;
}

function pointerKind(type: string): SnapPointerType {
  return type === 'touch' || type === 'pen' ? type : 'mouse';
}

const PREFIX = 'pages.gardenPlan.editor';
const ZONES = `${PREFIX}.zones`;
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
};

// The template picker, the "save as template" dialog and the multi-duplicate dialog are their own chunks:
// the plan route's budget (UI-NFR-003) carries none of them until they are opened.
const TemplatePanel = lazy(() => import('../templates/TemplatePanel'));
const SaveAsTemplateDialog = lazy(() => import('../templates/SaveAsTemplateDialog'));
const MultiDuplicateDialog = lazy(() => import('./MultiDuplicateDialog'));

const NO_KEYS: ReadonlySet<string> = new Set();
const NO_BED_KEYS: readonly string[] = [];
const NO_PHASE_KEYS: readonly (string | null | undefined)[] = [];

/** The turn a click on "Rotate" adds to the template being placed (GP-FR-044). */
const TEMPLATE_TURN_DEG = 90;

/** Where the bed template tool stands: the template picked (or none yet) and its turn. */
interface TemplateMode {
  templateKey: string | null;
  rotationDeg: number;
}

function cursorOf(tool: PlanTool): string {
  if (tool === 'pan') return 'grab';
  if (tool === 'bed' || tool === 'garden_object') return 'crosshair';
  return 'default';
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
}: GardenPlanEditorProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  // On phones the bar docks to the bottom; it follows the canvas in the DOM there so that the
  // tab order is the visual order (WCAG 2.4.3). On md+ it sits above the plan.
  const toolbarBelow = useMediaQuery(theme.breakpoints.down('md'));
  const coarsePointer = useMediaQuery('(pointer: coarse)');
  const touchUi = toolbarBelow || coarsePointer;
  const visibleHeight = useVisibleHeight();
  const dispatch = useAppDispatch();
  const { selection, stack, tool, editError, past, future, pending } =
    useAppSelector(selectGardenPlanState);
  const invalidKeys = useAppSelector(selectInvalidKeys);
  const [drawShape, setDrawShape] = useState<DrawShape>('rect');
  const [angleStep, setAngleStep] = useState<AngleStep>(15);
  const [notice, setNotice] = useState<string | null>(null);
  const [gridStepM, setGridStepM] = useState(() => nearestGridStep(plan.settings?.default_grid_m));
  // The grid switch is a per-user layer choice kept in localStorage (GP-FR-031).
  const { prefs: layerPrefs, setLayer } = useLayerPrefs();
  const gridVisible = layerPrefs.grid;
  const setGridVisible = useCallback(
    (visible: boolean) => setLayer('grid', visible),
    [setLayer],
  );
  const setLayerById = useCallback((id: string, visible: boolean) => setLayer(id as LayerId, visible), [setLayer]);
  // The irrigation layers (WP 7.6 / 7.7): zones come with the plan; the endpoint is read once the panel opens.
  const [zonesOpen, setZonesOpen] = useState(false);
  const [layerRefresh, setLayerRefresh] = useState(0);
  const zonesButtonRef = useRef<HTMLButtonElement | null>(null);
  const zonesWereOpen = useRef(false);
  // Closing the panel returns the focus to the button that opened it (WCAG 2.4.3).
  useEffect(() => {
    if (!zonesOpen && zonesWereOpen.current) zonesButtonRef.current?.focus();
    zonesWereOpen.current = zonesOpen;
  }, [zonesOpen]);
  const [nowMs] = useState(() => Date.now());
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
  const [underlayOpen, setUnderlayOpen] = useState(false);
  const underlayButtonRef = useRef<HTMLButtonElement | null>(null);
  const underlayWasOpen = useRef(false);
  useEffect(() => {
    if (!underlayOpen && underlayWasOpen.current) underlayButtonRef.current?.focus();
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
  const onZonesChanged = useCallback(() => {
    setLayerRefresh((value) => value + 1);
    refreshPlanStates();
  }, [refreshPlanStates]);
  // Phase names are read only for the plants whose states are loaded (beds at marker LOD), never for the whole plan.
  const planPhaseKeys = useMemo(() => {
    const plantKeys = Object.keys(planStates.states);
    return plantStateOn && plantKeys.length > 0
      ? plantKeys.map((plantKey) => plan.plants[plantKey]?.phase_key)
      : NO_PHASE_KEYS;
  }, [plantStateOn, planStates.states, plan.plants]);
  const fetchedPhaseNames = usePhaseNames(planPhaseKeys);
  // A phase-sequence entry key is unknown to `/growth-phases/{key}`; the state answer names it. The fetched name wins.
  const phaseNames = useMemo(
    () => ({ ...planStates.phaseNames, ...fetchedPhaseNames }),
    [planStates.phaseNames, fetchedPhaseNames],
  );
  const phaseColors = useMemo(() => colorsOf(phaseNames), [phaseNames]);
  const plantStateLayer = useMemo(
    () => (plantStateOn ? { states: planStates.states, attentionOnly } : undefined),
    [plantStateOn, planStates.states, attentionOnly],
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
  const hasUnderlay = underlayState.underlay !== null;
  const layerToggles = useMemo<LayerToggle[]>(
    () =>
      (TOGGLE_LAYERS as readonly Exclude<LayerId, 'grid'>[])
        .filter((id) => id !== 'underlay' || hasUnderlay)
        .map((id) => ({
        id,
        label: t(`${ZONES}.layers.${id}`),
        hint: t(`${ZONES}.layers.${id}Hint`),
        icon: LAYER_ICONS[id],
        visible: layerPrefs[id],
      })),
    [layerPrefs, t, hasUnderlay],
  );
  const onShortcut = useEditorShortcuts();
  const [snapEnabled, setSnapEnabled] = useState(true);
  const [snapMark, setSnapMark] = useState<SnapMark | null>(null);
  const [unit, setUnit] = useLengthUnit();
  const [pendingDelete, setPendingDelete] = useState<DeleteImpact | null>(null);
  const [multiSelect, setMultiSelect] = useState(false);
  const [bedTypeChoice, setBedTypeChoice] = useState<string | null>(null);
  const [objectType, setObjectType] = useState<GardenObjectType>('other');
  const [menuAnchor, setMenuAnchor] = useState<MenuAnchor | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [templateMode, setTemplateMode] = useState<TemplateMode | null>(null);
  const [placing, setPlacing] = useState(false);
  const [ghostPoint, setGhostPoint] = useState<Point | null>(null);
  const [saveTemplateOpen, setSaveTemplateOpen] = useState(false);
  const [multiOpen, setMultiOpen] = useState(false);
  const [info, setInfo] = useState<string | null>(null);
  const deleteTexts = useDeleteTexts(pendingDelete, plan, labels);
  const [view, setView] = useState<'plan' | 'list'>('plan');
  const [helpOpen, setHelpOpen] = useState(false);
  const shortcuts = useSingleKeyShortcuts();
  const dockRef = useRef<HTMLDivElement | null>(null);
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
  const focusSurface = useCallback(() => {
    pendingFocus.current = view === 'plan' ? 'plan' : 'list';
  }, [view]);
  useEffect(() => {
    const request = pendingFocus.current;
    if (request === null) return;
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
  const movingKeys = useMemo(
    () =>
      tool === 'select' && templateMode === null
        ? new Set(moveTargets(plan, selection).map((entry) => entry.key))
        : NO_KEYS,
    [plan, selection, templateMode, tool],
  );
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
    snapPoint,
  });

  const zoomCenter = useMemo<Point>(
    () => [viewport.widthPx / 2, viewport.heightPx / 2],
    [viewport.widthPx, viewport.heightPx],
  );
  const zoomBy = useCallback(
    (direction: 1 | -1) => onZoom?.(stepZoom(pxPerM, direction, minPxPerM), zoomCenter),
    [minPxPerM, onZoom, pxPerM, zoomCenter],
  );
  const zoomIn = useCallback(() => zoomBy(1), [zoomBy]);
  const zoomOut = useCallback(() => zoomBy(-1), [zoomBy]);
  const fit = useCallback(() => onFit?.(), [onFit]);

  // The wheel zooms around the pointer (with Ctrl/Cmd or a focused canvas). A listener of its own: React's wheel handlers are passive
  // and could not keep the page from scrolling.
  const wheelState = useRef({ pxPerM, onZoom });
  useEffect(() => {
    wheelState.current = { pxPerM, onZoom };
  });
  useEffect(() => {
    const element = canvasRef.current;
    if (element === null) return undefined;
    const onWheel = (event: WheelEvent) => {
      const { pxPerM: current, onZoom: zoom } = wheelState.current;
      if (!zoom) return;
      // A plain wheel (or a two-finger touchpad scroll) scrolls the page; zooming needs Ctrl/Cmd
      // (a touchpad pinch arrives as Ctrl + wheel) or the focus on the canvas.
      const focused = element.contains(document.activeElement);
      if (!event.ctrlKey && !event.metaKey && !focused) return;
      event.preventDefault();
      const box = element.getBoundingClientRect();
      const lines = event.deltaMode === 1 ? 16 : 1;
      zoom(current * Math.exp(-event.deltaY * lines * WHEEL_ZOOM_PER_PX), [
        event.clientX - box.left - element.clientLeft,
        event.clientY - box.top - element.clientTop,
      ]);
    };
    element.addEventListener('wheel', onWheel, { passive: false });
    return () => element.removeEventListener('wheel', onWheel);
    // The canvas element is a new one each time the list view has been shown in between.
  }, [view]);

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

  // The snap marker follows the pointer of the draw tools, of the template tool and of a move under way
  // (where the next point will land); on an object edge it draws that edge as a guide (GP-FR-154).
  const drawTool = tool === 'bed' || tool === 'garden_object';
  const templateTool = templateMode !== null;
  const { onPointerMove: toolPointerMove, onPointerUp: toolPointerUp } = tools.containerProps;
  const toolBusy = tools.busy;
  const onPointerMove = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      toolPointerMove(event);
      const box = event.currentTarget.getBoundingClientRect();
      const pointM = renderer.toModel([
        event.clientX - box.left - event.currentTarget.clientLeft,
        event.clientY - box.top - event.currentTarget.clientTop,
      ]);
      if (templateTool) {
        // The ghost sits where the click would put the template: on the snapped point.
        const landing = snapPoint(pointM, event.altKey, pointerKind(event.pointerType));
        setGhostPoint((previous) =>
          previous && previous[0] === landing[0] && previous[1] === landing[1] ? previous : landing,
        );
      }
      if (!(drawTool || templateTool || toolBusy) || !snapEnabled || event.altKey) {
        setSnapMark((previous) => (previous === null ? previous : null));
        return;
      }
      const result = resolveSnap(pointM, {
        gridM: gridStepM,
        gridEnabled: true,
        bypass: false,
        pxPerM,
        pointerType: pointerKind(event.pointerType),
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
      drawTool,
      gridStepM,
      pxPerM,
      renderer,
      snapEnabled,
      snapPoint,
      templateTool,
      toolBusy,
      toolPointerMove,
    ],
  );
  const onPointerLeave = useCallback(() => {
    setSnapMark(null);
    setGhostPoint(null);
  }, []);
  const onPointerUp = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      toolPointerUp(event);
      if (event.pointerType === 'touch') setSnapMark(null); // there is no hover to follow
    },
    [toolPointerUp],
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
    () => ({ ...tools.containerProps, onKeyDown, onPointerMove, onPointerUp }),
    [onKeyDown, onPointerMove, onPointerUp, tools.containerProps],
  );
  // Pinch: the factor of one step is applied to the current zoom; the route clamps it like the buttons.
  const onPinch = useMemo(
    () =>
      onZoom
        ? (factor: number, centerPx: Point) =>
            onZoom(wheelState.current.pxPerM * factor, centerPx)
        : undefined,
    [onZoom],
  );
  const touch = useTouchInput({
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
  const boundary = plan.settings?.boundary ?? null;
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
    const step = plan.settings?.default_grid_m ?? 0.1;
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
    (options: MultiDuplicateOptions): string | null => {
      const outcome = multiDuplicate(plan, selection, { ...options, pendingCount: pending.length });
      if (!outcome.ok) return outcome.code;
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
    setTemplateMode((previous) => (previous ? null : { templateKey: null, rotationDeg: 0 }));
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
          }),
        ).unwrap();
        if (outcome.ok) {
          setNotice(null);
          setInfo(t(`${PREFIX}.templates.placed`));
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
  /** The skip link "To the properties panel": the panel's own region takes the focus. */
  const focusPanelRegion = useCallback(() => {
    document.getElementById(EDITOR_ANCHORS.panel)?.focus();
  }, []);

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
        onClick: () => window.setTimeout(focusPanel, 0),
      },
      {
        id: 'duplicate',
        label: t(`${PREFIX}.contextMenu.duplicate`),
        icon: <ContentCopyIcon fontSize="small" />,
        onClick: duplicate,
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
    plan,
    requestDelete,
    selection,
    setLocked,
    singleBed,
    t,
  ]);

  const headerExtraItems = useMemo<MenuAction[]>(
    () => [
      {
        id: 'multiDuplicate',
        label: t(`${PREFIX}.contextMenu.multiDuplicate`),
        icon: <ContentCopyOutlinedIcon fontSize="small" />,
        onClick: () => setMultiOpen(true),
        disabled: !selection.some(isPlanEntity),
      },
    ],
    [selection, t],
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
    setView('list');
  }, []);
  const showPlan = useCallback(() => {
    pendingFocus.current = 'plan';
    setView('plan');
  }, []);
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
        onActivateKey,
        invalidKeys,
        underlayLayer: underlayState.entry,
        ...zoneLayers,
        sunLayer: layerPrefs.sun,
        moistureLayer: layerPrefs.moisture,
        frostLayer: layerPrefs.frost,
        ...(plantStateLayer ? { plantStateLayer, phaseColors } : {}),
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
      layerPrefs.frost,
      plantStateLayer,
      phaseColors,
    ],
  );

  const selectChooseTool = useCallback(
    (next: EditorTool) => {
      dispatch(setTool(next));
      setTemplateMode(null);
      setGhostPoint(null);
      if (next === 'bed' && drawShape === 'polyline') setDrawShape('rect');
    },
    [dispatch, drawShape],
  );

  // On a phone the selected object is panned above the sheet that opens for it (GP-UX-052).
  const selectionSignature = selection.map((ref) => `${ref.entity}:${ref.key}`).join('|');
  const latestView = useRef({ plan, renderer, onPan, selection });
  useEffect(() => {
    latestView.current = { plan, renderer, onPan, selection };
  });
  useEffect(() => {
    const dock = dockRef.current;
    const canvas = canvasRef.current;
    if (!toolbarBelow || selectionSignature === '' || !dock || !canvas) return;
    const free = dock.getBoundingClientRect().top - canvas.getBoundingClientRect().top;
    if (free <= 0) return;
    const latest = latestView.current;
    const ref = latest.selection.length === 1 ? latest.selection[0] : null;
    if (!ref || !isPlanEntity(ref)) return;
    const source =
      ref.entity === 'location' ? latest.plan.locations[ref.key] : latest.plan.gardenObjects[ref.key];
    const bbox = source?.bbox;
    if (!bbox) return;
    const ys = [
      latest.renderer.toScreen([bbox[0], bbox[1]])[1],
      latest.renderer.toScreen([bbox[2], bbox[3]])[1],
    ];
    const dy = panIntoView(Math.min(...ys), Math.max(...ys), free);
    if (dy !== 0) latest.onPan(0, dy);
  }, [selectionSignature, toolbarBelow]);

  const code = notice ?? editError;
  const noticeText = code
    ? t(`${PREFIX}.notice.${code}`, { defaultValue: t(`${PREFIX}.notice.generic`) })
    : null;
  const handles = tools.handles;
  const singleTooSmall = handles !== null && handles.density === 'none';

  const drawing = tool === 'bed' || tool === 'garden_object';
  // With a finger the hints speak of the crosshair and "Set point" - dragging would pan the plan.
  const hintBase = touchUi ? `${PREFIX}.touch.hint` : `${PREFIX}.drawHint`;
  const hintKey = !drawing
    ? null
    : tools.draftPoints > 0
      ? `${hintBase}.${drawShape}.next`
      : `${hintBase}.${drawShape}.start`;

  const toolbar = (
    <EditorToolbar
      tool={tool}
      onTool={selectChooseTool}
      drawShape={drawShape}
      onDrawShape={setDrawShape}
      angleStep={angleStep}
      onAngleStep={setAngleStep}
      draftPoints={tools.draftPoints}
      onFinishDraw={thenFocusPlan(tools.finishDraw)}
      onCancelDraw={thenFocusPlan(tools.cancel)}
      canDelete={selection.some(isPlanEntity)}
      onDelete={requestDelete}
      vertexPicked={tools.vertex !== null}
      canDeleteVertex={tools.vertex !== null}
      onDeleteVertex={thenFocusPlan(tools.deleteVertex)}
      onInsertVertex={thenFocusPlan(tools.insertVertexAfter)}
      templateActive={templateTool}
      onTemplate={toggleTemplateTool}
      canSaveTemplate={singleBed !== null}
      onSaveTemplate={() => setSaveTemplateOpen(true)}
      align={{
        canAlign: availability.align,
        canDistribute: availability.distribute,
        onAlign: align,
        onDistribute: distribute,
      }}
    />
  );

  const centerPx: Point = [viewport.widthPx / 2, viewport.heightPx / 2];
  const touchBar = touchUi ? (
    <TouchBar
      tool={tool}
      drawShape={drawShape}
      draftPoints={tools.draftPoints}
      onPlacePoint={() => tools.placePointAt(centerPx)}
      onUndoPoint={tools.undoPoint}
      onFinish={tools.finishDraw}
      onCancel={tools.cancel}
      multiSelect={multiSelect}
      onMultiSelect={setMultiSelect}
    />
  ) : null;

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

  const stackLists = stack !== null && stack.keys.length >= 2;
  const sheetOpen = toolbarBelow && (selection.length > 0 || stackLists);
  const panel = (layout: 'sidebar' | 'sheet') => (
    <PropertiesPanel
      plan={plan}
      selection={selection}
      stack={stack}
      labels={labels}
      layout={layout}
      onCommit={onCommit}
      onSelect={onSelect}
      onStack={onStack}
      onClose={() => {
        onSelect([]);
        onStack(null);
        focusSurface(); // the close button disappears with the sheet: keep the focus on the plan or the list
      }}
      onMore={(element) => setMenuAnchor({ kind: 'element', element })}
      onDuplicate={duplicate}
      onDelete={requestDelete}
      onZOrder={moveInZ}
      onDrawBed={() => dispatch(setTool('bed'))}
      onOpenLocation={onOpenLocation}
      onOpenCare={onOpenCare}
      bedInfo={bedInfo}
    />
  );

  const viewBar = (
    <ViewBar
      layerToggles={layerToggles}
      onLayer={setLayerById}
      attentionFilter={attentionFilter}
      gridStepM={gridStepM}
      onGridStep={setGridStepM}
      gridVisible={gridVisible}
      onGridVisible={setGridVisible}
      snapEnabled={snapEnabled}
      onSnapEnabled={setSnapEnabled}
      pxPerM={pxPerM}
      minPxPerM={minPxPerM}
      onZoomIn={zoomIn}
      onZoomOut={zoomOut}
      onFit={fit}
      unit={unit}
      onUnit={setUnit}
      northAngleDeg={northAngleDeg}
      onNorthAngle={onNorthAngle}
    />
  );

  // A task badge on a bed opens its care tab (GP-FR-089). The press that lands on it starts no gesture (a pan or the
  // first finger of a pinch would otherwise select or drag the bed), and the tab opens on the click that follows:
  // a click exists only when the pointer went down and up on the badge itself, so a drag that merely starts there
  // opens nothing. The canvas would capture the pointer and swallow that click, which is why the press is not
  // handed to the tools at all.
  // The template tool takes the press the same way: the click that follows places the template, so no
  // gesture (selection, marquee, pan) may start under it.
  const touchPointerDown = touch.containerProps.onPointerDown;
  const onCanvasPointerDown = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      if (templateTool && event.button === 0) return;
      if (onOpenCare && tool === 'select' && event.button === 0 && badgeKeyOf(event) !== null) return;
      touchPointerDown(event);
    },
    [onOpenCare, templateTool, tool, touchPointerDown],
  );
  const onCanvasClick = useCallback(
    (event: ReactMouseEvent<HTMLElement>) => {
      if (templateTool) {
        const box = event.currentTarget.getBoundingClientRect();
        const pointM = renderer.toModel([
          event.clientX - box.left - event.currentTarget.clientLeft,
          event.clientY - box.top - event.currentTarget.clientTop,
        ]);
        // The same tolerance as the ghost shown under the pointer (a finger or a pen snaps wider).
        const kind = 'pointerType' in event.nativeEvent ? String(event.nativeEvent.pointerType) : 'mouse';
        void placeTemplate(snapPoint(pointM, event.altKey, pointerKind(kind)));
        return;
      }
      const key = badgeKeyOf(event);
      if (key && onOpenCare && tool === 'select') onOpenCare(key);
    },
    [onOpenCare, placeTemplate, renderer, snapPoint, templateTool, tool],
  );

  const selectedTemplate = useMemo(
    () => templateCatalogue.templates.find((item) => item.key === templateMode?.templateKey) ?? null,
    [templateCatalogue.templates, templateMode?.templateKey],
  );
  const closeTemplateTool = useCallback(() => {
    setTemplateMode(null);
    setGhostPoint(null);
  }, []);

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
        cursor: cursorOf(tool),
        border: 1,
        borderColor: 'divider',
        borderRadius: 1,
        bgcolor: 'background.paper',
        flexShrink: 0,
        '&:focus-visible': {
          outline: 3,
          outlineStyle: 'solid',
          outlineColor: 'primary.main',
          outlineOffset: 2,
        },
      }}
    >
      {rendered}
      {gridVisible && <Grid viewport={viewport} stepM={gridStepM} />}
      <EditorOverlay
        overlay={tools.overlay}
        handles={handles}
        vertex={tools.vertex}
        toScreen={renderer.toScreen.bind(renderer)}
        pxPerM={viewport.pxPerM}
        widthPx={viewport.widthPx}
        heightPx={viewport.heightPx}
      >
        <DimensionLabels
          items={dimensionItems}
          toScreen={renderer.toScreen.bind(renderer)}
          unit={unit}
        />
        {selectedTemplate && ghostPoint && templateMode && (
          <TemplateGhost
            template={selectedTemplate}
            originM={ghostPoint}
            rotationDeg={templateMode.rotationDeg}
            toScreen={renderer.toScreen.bind(renderer)}
            pxPerM={pxPerM}
          />
        )}
        {snapMark && (
          <SnapMarker
            mark={snapMark}
            toScreen={renderer.toScreen.bind(renderer)}
            widthPx={viewport.widthPx}
            heightPx={viewport.heightPx}
          />
        )}
      </EditorOverlay>
      <ScaleBar pxPerM={pxPerM} />
      {showMiniMap && extent && (
        <MiniMap plan={plan} extent={extent} viewport={viewport} onJump={jumpTo} />
      )}
      <TouchOverlay
        ring={touch.ring}
        crosshair={touchUi && drawing ? centerPx : null}
        widthPx={viewport.widthPx}
        heightPx={viewport.heightPx}
      />
    </Box>
  );

  return (
    <Box
      data-testid="garden-plan-editor"
      onKeyDown={onShortcut}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
        // GP-NFR-026: no motion for people who ask for none (ripples, tooltips, dialogs, ghost fading).
        '@media (prefers-reduced-motion: reduce)': {
          '& *, & *::before, & *::after': {
            transition: 'none !important',
            animation: 'none !important',
            scrollBehavior: 'auto !important',
          },
        },
      }}
    >
      <SkipLinks
        listShown={listShown}
        panelAvailable={!toolbarBelow || sheetOpen}
        onToList={showList}
        onToPlan={showPlan}
        onToPanel={focusPanelRegion}
      />
      <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1 }}>
        <FormControlLabel
          sx={{ m: 0, minHeight: 44 }}
          control={
            <Switch
              checked={listShown}
              onChange={(event) => (event.target.checked ? showList() : showPlan())}
              slotProps={{ input: { 'data-testid': 'garden-plan-view-list' } as object }}
            />
          }
          label={t(`${PREFIX}.list.switch`)}
        />
        <Button
          startIcon={<KeyboardIcon />}
          onClick={openHelp}
          sx={{ minHeight: 44 }}
          data-testid="garden-plan-keyboard-help-button"
        >
          {t(`${PREFIX}.keyboard.open`)}
        </Button>
        <Button
          ref={zonesButtonRef}
          startIcon={<WaterDropIcon />}
          onClick={() => setZonesOpen((open) => !open)}
          aria-expanded={zonesOpen}
          aria-controls="garden-plan-zone-panel-region"
          sx={{ minHeight: 44 }}
          data-testid="garden-plan-zones-open"
        >
          {t(`${ZONES}.open`)}
        </Button>
        <Button
          ref={underlayButtonRef}
          startIcon={<ImageIcon />}
          onClick={() => setUnderlayOpen(true)}
          aria-haspopup="dialog"
          sx={{ minHeight: 44 }}
          data-testid="garden-plan-underlay-open"
        >
          {t(`${UNDERLAY}.open`)}
        </Button>
      </Box>
      <SaveBar />
      <EditorHeaderActions
        onAddWithDimensions={() => setAddOpen(true)}
        onSelectAll={doSelectAll}
        extraItems={headerExtraItems}
      />
      {!listShown && viewBar}
      {!listShown && (
        <ZoneLegend
          zones={zoneData.zones}
          showZones={layerPrefs.zones}
          showLastWatered={layerPrefs.lastWatered}
          showSun={layerPrefs.sun}
          showMoisture={layerPrefs.moisture}
          showFrost={layerPrefs.frost}
          showPlantState={plantStateOn}
          phases={legendPhases}
        />
      )}
      {!listShown && !toolbarBelow && toolbar}
      {!listShown && !toolbarBelow && touchBar}
      {!listShown && drawing && (
        <NewTypeSelect
          target={tool === 'bed' ? 'bed' : 'garden_object'}
          labels={labels}
          bedTypes={bedTypes}
          bedTypeKey={bedTypeKey}
          onBedTypeKey={setBedTypeChoice}
          objectType={objectType}
          onObjectType={setObjectType}
        />
      )}
      {!listShown && templateMode && (
        <Suspense fallback={null}>
          <TemplatePanel
            catalogue={templateCatalogue}
            templateKey={templateMode.templateKey}
            onTemplateKey={(key) =>
              setTemplateMode((previous) => (previous ? { ...previous, templateKey: key } : previous))
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
            onPlaceCenter={() => void placeTemplate(snapPoint(renderer.toModel(centerPx), false))}
            onClose={closeTemplateTool}
          />
        </Suspense>
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
      {!listShown && singleTooSmall && (
        <Alert severity="info" role="status" data-testid="garden-plan-too-small">
          {t(`${PREFIX}.tooSmall`)}
        </Alert>
      )}
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
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
          canvasSurface
        )}
        {!toolbarBelow && panel('sidebar')}
      </Box>
      {underlayOpen && (
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
      )}
      <Box id="garden-plan-zone-panel-region">
        {zonesOpen && (
          <Suspense fallback={<Box sx={{ minHeight: 120 }} aria-busy="true" />}>
            <ZonePanel
              plan={plan}
              zoneData={zoneData}
              selectedBedKeys={selectedBedKeys}
              onChanged={onZonesChanged}
              onClose={() => setZonesOpen(false)}
            />
          </Suspense>
        )}
      </Box>
      {toolbarBelow && (!listShown || sheetOpen) && (
        <Box
          ref={dockRef}
          data-testid="garden-plan-dock"
          sx={{
            position: 'sticky',
            bottom: 0,
            zIndex: 2,
            display: 'flex',
            flexDirection: 'column',
            gap: 0.5,
          }}
        >
          {sheetOpen && (
            <Box
              sx={{ maxHeight: Math.round(visibleHeight * 0.45), overflowY: 'auto' }}
              data-testid="garden-plan-sheet"
            >
              {panel('sheet')}
            </Box>
          )}
          {!listShown && touchBar}
          {!listShown && toolbar}
        </Box>
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
      />
      <AddWithDimensionsDialog
        open={addOpen}
        plan={plan}
        labels={labels}
        bedTypes={bedTypes}
        fallbackBedTypeKey={fallbackBedType}
        defaultPosition={renderer.toModel(centerPx)}
        suggestedName={newBedName(Object.keys(plan.locations).length + 1)}
        onAdd={addWithDimensions}
        onClose={() => setAddOpen(false)}
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
    </Box>
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
