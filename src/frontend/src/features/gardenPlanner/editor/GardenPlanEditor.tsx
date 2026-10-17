/**
 * The garden plan editor (REQ-053 WP 2.4): the canvas with its tools, handles and overlay, the tool
 * bar and the delete confirmation. It reads and writes the plan only through the Redux slice
 * (`applyAction` - one user action is one undo step) and reaches the renderer only through the
 * `PlanRenderer` interface the route hands in (GP-NFR-009). Grid/snap/zoom (WP 2.5), the property
 * panel and context menu (WP 2.6), the list view and full keyboard (WP 2.7) and saving (WP 2.8)
 * plug into the seams marked in `useEditorTools`.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import KeyboardIcon from '@mui/icons-material/Keyboard';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import type { PlanModel } from '../model/planModel';
import type { PlanOperation } from '../model/types';
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
import { EDITOR_ANCHORS } from './anchors';
import { EditorOverlay } from './EditorOverlay';
import { EditorToolbar, type AngleStep, type EditorTool } from './EditorToolbar';
import { KeyboardHelp } from './KeyboardHelp';
import { LiveRegion } from './LiveRegion';
import { PlanListView } from './PlanListView';
import { buildTree, neighbourKey } from './planTree';
import { SkipLinks } from './SkipLinks';
import { useAnnouncement } from './useAnnouncement';
import { stepOf, useEditorKeyboard } from './useEditorKeyboard';
import { useSingleKeyShortcuts } from './useSingleKeyShortcuts';
import type { DrawShape } from './tools/drawMachine';
import { deleteImpact, isPlanEntity, type DeleteImpact } from './tools/hierarchy';
import type { ActionLabel } from './tools/machineTypes';
import { resolveRef } from './tools/selection';
import { useEditorTools } from './tools/useEditorTools';

export interface GardenPlanEditorProps {
  plan: PlanModel;
  viewport: Viewport;
  renderer: PlanRenderer;
  labels: RendererLabels;
  fieldMode: boolean;
  /** The pan tool moved the view by this many pixels; the route owns the viewport. */
  onPan: (dxPx: number, dyPx: number) => void;
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
}: GardenPlanEditorProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  // On phones the bar docks to the bottom; it follows the canvas in the DOM there so that the
  // tab order is the visual order (WCAG 2.4.3). On md+ it sits above the plan.
  const toolbarBelow = useMediaQuery(theme.breakpoints.down('md'));
  const dispatch = useAppDispatch();
  const { selection, stack, tool, editError, past, future } = useAppSelector(selectGardenPlanState);
  const [drawShape, setDrawShape] = useState<DrawShape>('rect');
  const [angleStep, setAngleStep] = useState<AngleStep>(15);
  const [notice, setNotice] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<DeleteImpact | null>(null);
  const deleteTexts = useDeleteTexts(pendingDelete, plan, labels);
  const [view, setView] = useState<'plan' | 'list'>('plan');
  const [helpOpen, setHelpOpen] = useState(false);
  const shortcuts = useSingleKeyShortcuts();
  const canvasRef = useRef<HTMLDivElement | null>(null);
  const listRef = useRef<HTMLDivElement | null>(null);
  const announcement = useAnnouncement(plan, past, future, t(`${PREFIX}.liveRegion.unnamed`));
  // Where the focus goes after the next render (GP-NFR-070 - never to the body): an object key,
  // or one of the two surfaces.
  const pendingFocus = useRef<{ key: string } | 'plan' | 'list' | null>(null);

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
    onCommit,
    onNotice: setNotice,
    onPan,
    onHelp: openHelp,
  });

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
  });

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
  const { onKeyDown: toolsKeyDown, ...pointerProps } = tools.containerProps;
  const onCanvasKeyDown = useCallback(
    (event: Parameters<typeof toolsKeyDown>[0]) => {
      if (!keyboard.handleKey(event)) toolsKeyDown(event);
    },
    [keyboard, toolsKeyDown],
  );
  // Buttons that disappear once they have acted must not take the focus with them.
  const thenFocusPlan = useCallback(
    (action: () => void) => () => {
      action();
      focusPlan();
    },
    [focusPlan],
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
      onFinishDraw={thenFocusPlan(tools.finishDraw)}
      onCancelDraw={thenFocusPlan(tools.cancel)}
      canDelete={selection.some(isPlanEntity)}
      onDelete={requestDelete}
      vertexPicked={tools.vertex !== null}
      canDeleteVertex={tools.vertex !== null}
      onDeleteVertex={thenFocusPlan(tools.deleteVertex)}
      onInsertVertex={thenFocusPlan(tools.insertVertexAfter)}
    />
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
      {...pointerProps}
      onKeyDown={onCanvasKeyDown}
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
        '&:focus-visible': {
          outline: 3,
          outlineStyle: 'solid',
          outlineColor: 'primary.main',
          outlineOffset: 2,
        },
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
    </Box>
  );

  return (
    <Box
      data-testid="garden-plan-editor"
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
      <SkipLinks listShown={listShown} onToList={showList} onToPlan={showPlan} />
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
          onClick={() => setHelpOpen(true)}
          sx={{ minHeight: 44 }}
          data-testid="garden-plan-keyboard-help-button"
        >
          {t(`${PREFIX}.keyboard.open`)}
        </Button>
      </Box>
      {!listShown && !toolbarBelow && toolbar}
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
      {!listShown && singleTooSmall && (
        <Alert severity="info" role="status" data-testid="garden-plan-too-small">
          {t(`${PREFIX}.tooSmall`)}
        </Alert>
      )}
      {listShown ? (
        <Box ref={listRef} sx={{ display: 'contents' }}>
          <PlanListView
            plan={plan}
            labels={labels}
            selection={selection}
            stepM={stepOf(plan)}
            onSelect={onListSelect}
            onMove={keyboard.moveSelection}
            onRequestDelete={requestDelete}
          />
        </Box>
      ) : (
        canvasSurface
      )}
      {!listShown && toolbarBelow && toolbar}
      <LiveRegion message={announcement} />
      <KeyboardHelp
        open={helpOpen}
        onClose={() => setHelpOpen(false)}
        singleKeyShortcuts={shortcuts.enabled}
        onSingleKeyShortcuts={shortcuts.setEnabled}
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
