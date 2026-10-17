/**
 * The garden plan editor (REQ-053 WP 2.4): the canvas with its tools, handles and overlay, the tool
 * bar and the delete confirmation. It reads and writes the plan only through the Redux slice
 * (`applyAction` - one user action is one undo step) and reaches the renderer only through the
 * `PlanRenderer` interface the route hands in (GP-NFR-009). WP 2.6 adds the properties panel (a
 * sidebar, on phones a bottom sheet), the item menu, duplicate / lock / z-order, "add with
 * dimensions" and the touch layer. Grid/snap/zoom (WP 2.5), the list view and full keyboard
 * (WP 2.7) and saving (WP 2.8) plug into the seams marked in `useEditorTools`.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import FlipToBackIcon from '@mui/icons-material/FlipToBack';
import FlipToFrontIcon from '@mui/icons-material/FlipToFront';
import LockIcon from '@mui/icons-material/Lock';
import LockOpenIcon from '@mui/icons-material/LockOpen';
import YardIcon from '@mui/icons-material/Yard';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import type { PlanModel } from '../model/planModel';
import type { GardenObjectType, PlanOperation, Point } from '../model/types';
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
import { AddWithDimensionsDialog } from './AddWithDimensionsDialog';
import { ContextMenu, type MenuAction, type MenuAnchor } from './ContextMenu';
import { EditorHeaderActions } from './EditorHeaderActions';
import { EditorOverlay } from './EditorOverlay';
import { EditorToolbar, type AngleStep, type EditorTool } from './EditorToolbar';
import { NewTypeSelect } from './NewTypeSelect';
import { PropertiesPanel } from './PropertiesPanel';
import { TouchBar } from './TouchBar';
import { TouchOverlay } from './TouchOverlay';
import { commonBedTypeKey, type DrawShape } from './tools/drawMachine';
import { duplicateSelection } from './tools/duplicate';
import { deleteImpact, isPlanEntity, type DeleteImpact } from './tools/hierarchy';
import type { ActionLabel } from './tools/machineTypes';
import { panIntoView } from './tools/touchGestures';
import { isSelected, resolveRef, selectAll, stackRefs } from './tools/selection';
import { useBedTypes } from './useBedTypes';
import { useEditorTools } from './tools/useEditorTools';
import { useVisibleHeight } from './tools/useVisibleHeight';
import { useTouchInput } from './tools/useTouchInput';
import { zOrderOps, type ZMove } from './tools/zOrder';

export interface GardenPlanEditorProps {
  plan: PlanModel;
  viewport: Viewport;
  renderer: PlanRenderer;
  labels: RendererLabels;
  fieldMode: boolean;
  /** The pan tool moved the view by this many pixels; the route owns the viewport. */
  onPan: (dxPx: number, dyPx: number) => void;
  /** Pinch: zoom by `factor` about `centerPx`. Optional until the viewport can zoom (WP 2.5). */
  onZoom?: (factor: number, centerPx: Point) => void;
  /** Opens the detail page of a bed ("Details öffnen" / "Bepflanzen"). */
  onOpenLocation?: (locationKey: string) => void;
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
  onOpenLocation,
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
  const { selection, stack, tool, editError } = useAppSelector(selectGardenPlanState);
  const [drawShape, setDrawShape] = useState<DrawShape>('rect');
  const [angleStep, setAngleStep] = useState<AngleStep>(15);
  const [notice, setNotice] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<DeleteImpact | null>(null);
  const [multiSelect, setMultiSelect] = useState(false);
  const [bedTypeChoice, setBedTypeChoice] = useState<string | null>(null);
  const [objectType, setObjectType] = useState<GardenObjectType>('other');
  const [menuAnchor, setMenuAnchor] = useState<MenuAnchor | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const deleteTexts = useDeleteTexts(pendingDelete, plan, labels);
  const dockRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLDivElement | null>(null);

  const bedTypes = useBedTypes(tool === 'bed' || addOpen);
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
  });

  const onPlantsNearby = useCallback(
    (keys: string[], pointPx: Point) => {
      // Never a guessed single hit: the finger gets the list (GP-UX-034).
      dispatch(setSelection([]));
      dispatch(setStack({ keys, index: 0, pointPx }));
    },
    [dispatch],
  );
  const touch = useTouchInput({
    tool,
    multiSelect,
    plan,
    renderer,
    handles: tools.handles,
    base: tools.containerProps,
    onPan,
    onZoom,
    onPlantsNearby,
  });

  const confirmDelete = useCallback(() => {
    if (pendingDelete) onCommit(pendingDelete.ops, 'delete');
    setPendingDelete(null);
  }, [onCommit, pendingDelete]);

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
    ];
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
    duplicate,
    focusPanel,
    moveInZ,
    onOpenLocation,
    plan,
    requestDelete,
    selection,
    setLocked,
    t,
  ]);

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

  const selectChooseTool = useCallback(
    (next: EditorTool) => {
      dispatch(setTool(next));
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
    const view = latestView.current;
    const ref = view.selection.length === 1 ? view.selection[0] : null;
    if (!ref || !isPlanEntity(ref)) return;
    const source =
      ref.entity === 'location' ? view.plan.locations[ref.key] : view.plan.gardenObjects[ref.key];
    const bbox = source?.bbox;
    if (!bbox) return;
    const ys = [
      view.renderer.toScreen([bbox[0], bbox[1]])[1],
      view.renderer.toScreen([bbox[2], bbox[3]])[1],
    ];
    const dy = panIntoView(Math.min(...ys), Math.max(...ys), free);
    if (dy !== 0) view.onPan(0, dy);
  }, [selectionSignature, toolbarBelow]);

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
      }}
      onMore={(element) => setMenuAnchor({ kind: 'element', element })}
      onDuplicate={duplicate}
      onDelete={requestDelete}
      onZOrder={moveInZ}
      onDrawBed={() => dispatch(setTool('bed'))}
      onOpenLocation={onOpenLocation}
    />
  );

  return (
    <Box data-testid="garden-plan-editor" sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      <EditorHeaderActions onAddWithDimensions={() => setAddOpen(true)} onSelectAll={doSelectAll} />
      {!toolbarBelow && toolbar}
      {!toolbarBelow && touchBar}
      {drawing && (
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
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
        <Box
          ref={canvasRef}
          data-testid="garden-plan-canvas"
          role="region"
          aria-label={labels.canvas}
          // The region takes the editor's keys (Esc, Del, Ctrl+A); it must be reachable by keyboard (WCAG 2.1.1).
          tabIndex={0}
          {...touch.containerProps}
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
          }}
        >
          {renderer.render(plan, viewport, selectedKeys, { labels, fieldMode, onActivateKey })}
          <EditorOverlay
            overlay={tools.overlay}
            handles={handles}
            vertex={tools.vertex}
            toScreen={renderer.toScreen.bind(renderer)}
            pxPerM={viewport.pxPerM}
            widthPx={viewport.widthPx}
            heightPx={viewport.heightPx}
          />
          <TouchOverlay
            ring={touch.ring}
            crosshair={touchUi && drawing ? centerPx : null}
            widthPx={viewport.widthPx}
            heightPx={viewport.heightPx}
          />
        </Box>
        {!toolbarBelow && panel('sidebar')}
      </Box>
      {toolbarBelow && (
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
          {touchBar}
          {toolbar}
        </Box>
      )}
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
