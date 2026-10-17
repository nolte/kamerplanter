/**
 * The garden plan editor (REQ-053 WP 2.4): the canvas with its tools, handles and overlay, the tool
 * bar and the delete confirmation. It reads and writes the plan only through the Redux slice
 * (`applyAction` - one user action is one undo step) and reaches the renderer only through the
 * `PlanRenderer` interface the route hands in (GP-NFR-009). Grid, snap, zoom, scale bar, compass and
 * dimension text (WP 2.5) live here too; the property
 * panel and context menu (WP 2.6), the list view and full keyboard (WP 2.7) and saving (WP 2.8)
 * plug into the seams marked in `useEditorTools`.
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type PointerEvent as ReactPointerEvent,
} from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import type { PlanModel } from '../model/planModel';
import { toShape } from '../model/geometry';
import type { PlanOperation, Point } from '../model/types';
import { nearestGridStep, stepZoom } from '../model/units';
import type { PlanRenderer, RenderSelection, RendererLabels, Viewport } from '../renderer';
import {
  applyAction,
  clearEditError,
  selectGardenPlanState,
  setSelection,
  setStack,
  setTool,
  type PlanTool,
} from '../state/gardenPlanSlice';
import { DimensionLabels, type DimensionItem } from './DimensionLabels';
import { EditorOverlay } from './EditorOverlay';
import { EditorToolbar, type AngleStep, type EditorTool } from './EditorToolbar';
import { Grid } from './Grid';
import { ScaleBar } from './ScaleBar';
import { SnapMarker, type SnapMark } from './SnapMarker';
import { ViewBar } from './ViewBar';
import { useLengthUnit } from './useLengthUnit';
import type { DrawShape } from './tools/drawMachine';
import { deleteImpact, isPlanEntity, type DeleteImpact } from './tools/hierarchy';
import type { ActionLabel } from './tools/machineTypes';
import { resolveRef } from './tools/selection';
import { resolveSnap, type SnapPointerType } from './tools/snap';
import { useEditorTools } from './tools/useEditorTools';

export interface GardenPlanEditorProps {
  plan: PlanModel;
  viewport: Viewport;
  renderer: PlanRenderer;
  labels: RendererLabels;
  fieldMode: boolean;
  /** The pan tool moved the view by this many pixels; the route owns the viewport. */
  onPan: (dxPx: number, dyPx: number) => void;
  /** Zoom to `pxPerM` keeping the model point under `anchorPx` (canvas pixels) in place (WP 2.5). */
  onZoom?: (pxPerM: number, anchorPx: Point) => void;
  /** "Fit to area": back to the zoom that shows the whole plan (GP-FR-009). */
  onFit?: () => void;
  /** The lowest zoom allowed, the fit zoom (GP-FR-150). */
  minPxPerM?: number;
}

/** The wheel zooms stepless: `exp(-deltaY * this)` per event (the buttons and + / - use the fixed levels). */
const WHEEL_ZOOM_PER_PX = 0.0015;

function pointerKind(type: string): SnapPointerType {
  return type === 'touch' || type === 'pen' ? type : 'mouse';
}

const PREFIX = 'pages.gardenPlan.editor';

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
  fieldMode,
  onPan,
  onZoom,
  onFit,
  minPxPerM = 0,
}: GardenPlanEditorProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  // On phones the bar docks to the bottom; it follows the canvas in the DOM there so that the
  // tab order is the visual order (WCAG 2.4.3). On md+ it sits above the plan.
  const toolbarBelow = useMediaQuery(theme.breakpoints.down('md'));
  const dispatch = useAppDispatch();
  const { selection, stack, tool, editError } = useAppSelector(selectGardenPlanState);
  const [drawShape, setDrawShape] = useState<DrawShape>('rect');
  const [angleStep, setAngleStep] = useState<AngleStep>(15);
  const [notice, setNotice] = useState<string | null>(null);
  const [gridStepM, setGridStepM] = useState(() => nearestGridStep(plan.settings?.default_grid_m));
  const [gridVisible, setGridVisible] = useState(true);
  const [snapEnabled, setSnapEnabled] = useState(true);
  const [snapMark, setSnapMark] = useState<SnapMark | null>(null);
  const [unit, setUnit] = useLengthUnit();
  const [pendingDelete, setPendingDelete] = useState<DeleteImpact | null>(null);
  const deleteTexts = useDeleteTexts(pendingDelete, plan, labels);

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

  // The seam of the tool machines for grid and snap (GP-FR-012, GP-FR-154). Object snap (corner,
  // edge) is a SHOULD and not wired in the MVP: no candidates are handed to the resolver.
  const pxPerM = viewport.pxPerM;
  const snapPoint = useCallback(
    (point: Point, bypass: boolean) =>
      resolveSnap(point, { gridM: gridStepM, gridEnabled: snapEnabled, bypass, pxPerM }).point,
    [gridStepM, snapEnabled, pxPerM],
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
    snapPoint,
  });

  const canvasRef = useRef<HTMLDivElement | null>(null);
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

  // The wheel zooms around the pointer. A listener of its own: React's wheel handlers are passive
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
  }, []);

  const toolKeyDown = tools.containerProps.onKeyDown;
  const onKeyDown = useCallback(
    (event: ReactKeyboardEvent<HTMLElement>) => {
      if (!event.ctrlKey && !event.metaKey && !event.altKey) {
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
          setGridVisible((visible) => !visible);
          return;
        }
      }
      toolKeyDown(event);
    },
    [fit, toolKeyDown, zoomIn, zoomOut],
  );

  // The snap marker follows the pointer of the draw tools (where the next point will land).
  const drawTool = tool === 'bed' || tool === 'garden_object';
  const { onPointerMove: toolPointerMove, onPointerUp: toolPointerUp } = tools.containerProps;
  const onPointerMove = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      toolPointerMove(event);
      if (!drawTool || !snapEnabled || event.altKey) {
        setSnapMark((previous) => (previous === null ? previous : null));
        return;
      }
      const box = event.currentTarget.getBoundingClientRect();
      const result = resolveSnap(
        renderer.toModel([
          event.clientX - box.left - event.currentTarget.clientLeft,
          event.clientY - box.top - event.currentTarget.clientTop,
        ]),
        {
          gridM: gridStepM,
          gridEnabled: true,
          bypass: false,
          pxPerM,
          pointerType: pointerKind(event.pointerType),
        },
      );
      setSnapMark((previous) =>
        previous &&
        previous.kind === result.kind &&
        previous.point[0] === result.point[0] &&
        previous.point[1] === result.point[1]
          ? previous
          : result.kind === 'none'
            ? null
            : { point: result.point, kind: result.kind },
      );
    },
    [drawTool, gridStepM, pxPerM, renderer, snapEnabled, toolPointerMove],
  );
  const onPointerLeave = useCallback(() => setSnapMark(null), []);
  const onPointerUp = useCallback(
    (event: ReactPointerEvent<HTMLElement>) => {
      toolPointerUp(event);
      if (event.pointerType === 'touch') setSnapMark(null); // there is no hover to follow
    },
    [toolPointerUp],
  );

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
    if (pendingDelete) onCommit(pendingDelete.ops, 'delete');
    setPendingDelete(null);
  }, [onCommit, pendingDelete]);

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

  // The renderer output depends on the plan, view and selection only - not on the pointer.
  const rendered = useMemo(
    () => renderer.render(plan, viewport, selectedKeys, { labels, fieldMode, onActivateKey }),
    [renderer, plan, viewport, selectedKeys, labels, fieldMode, onActivateKey],
  );

  const selectChooseTool = useCallback(
    (next: EditorTool) => {
      dispatch(setTool(next));
      if (next === 'bed' && drawShape === 'polyline') setDrawShape('rect');
    },
    [dispatch, drawShape],
  );

  const code = notice ?? editError;
  const noticeText = code
    ? t(`${PREFIX}.notice.${code}`, { defaultValue: t(`${PREFIX}.notice.generic`) })
    : null;
  const handles = tools.handles;
  const singleTooSmall = handles !== null && handles.density === 'none';

  const drawing = tool === 'bed' || tool === 'garden_object';
  const hintKey = !drawing
    ? null
    : tools.draftPoints > 0
      ? `${PREFIX}.drawHint.${drawShape}.next`
      : `${PREFIX}.drawHint.${drawShape}.start`;

  const toolbar = (
    <EditorToolbar
      tool={tool}
      onTool={selectChooseTool}
      drawShape={drawShape}
      onDrawShape={setDrawShape}
      angleStep={angleStep}
      onAngleStep={setAngleStep}
      draftPoints={tools.draftPoints}
      onFinishDraw={tools.finishDraw}
      onCancelDraw={tools.cancel}
      canDelete={selection.some(isPlanEntity)}
      onDelete={requestDelete}
      vertexPicked={tools.vertex !== null}
      canDeleteVertex={tools.vertex !== null}
      onDeleteVertex={tools.deleteVertex}
      onInsertVertex={tools.insertVertexAfter}
    />
  );

  const viewBar = (
    <ViewBar
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

  return (
    <Box data-testid="garden-plan-editor" sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      {viewBar}
      {!toolbarBelow && toolbar}
      {hintKey && (
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
      {singleTooSmall && (
        <Alert severity="info" role="status" data-testid="garden-plan-too-small">
          {t(`${PREFIX}.tooSmall`)}
        </Alert>
      )}
      <Box
        data-testid="garden-plan-canvas"
        role="region"
        aria-label={labels.canvas}
        // The region takes the editor's keys (Esc, Del, Ctrl+A); it must be reachable by keyboard (WCAG 2.1.1).
        tabIndex={0}
        ref={canvasRef}
        {...tools.containerProps}
        onKeyDown={onKeyDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerLeave}
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
      </Box>
      {toolbarBelow && toolbar}
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
