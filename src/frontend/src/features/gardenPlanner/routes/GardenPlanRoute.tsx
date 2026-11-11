/**
 * The garden plan page (REQ-053 WP 2.3): `standorte/sites/:key/plan`.
 *
 * This module is the lazy route chunk. It is the one place that chooses a renderer implementation
 * (`usePlanRenderer`, GP-NFR-009: SVG, or Konva from its own chunk for a plan of 3 000 objects and more, D-01)
 * and that injects the plan slice into the root reducer, so neither the renderer, the plan model nor the
 * slice are part of the initial bundle (UI-NFR-003).
 *
 * The page loads the plan, explains the empty and error states and mounts the editor (WP 2.4:
 * select, pan, draw, handles). An empty plan offers its one next step to the roles that may edit
 * (GP-UX-049, #2617): "add the first bed" mounts the editor on a default area with "add with
 * dimensions" open. It owns the viewport - fitted to the plan, then panned and zoomed
 * (WP 2.5: zoom levels, wheel, "fit to area").
 *
 * Offline (WP 9.2, GP-UX-024): a plan that comes from the plan cache is drawn read-only with a "Stand von
 * hh:mm" banner. A plan loaded online stays in the editor when the connection drops (tool, selection and
 * unsaved edits survive); its edits, undo/redo and saves are refused until it is back. Either way a hint
 * (not an error) says geometry is online-only. A site never loaded online shows an empty state with a
 * hint. Import/export and the bed list need the server and are hidden while offline.
 *
 * Field mode (WP 5.1, GP-UX-020) is the default on xs and `?mode=field` everywhere; `?mode=plan` forces
 * planning mode. Field mode is its own lazy chunk (`field/FieldModeView`), so the route budget only carries
 * the switch. The route still chooses the renderer for it.
 *
 * Tabs (WP 10.2, GP-UX-064/065): planning mode shows Plan · Liste · Beete, the open one in `?tab=` next to `?mode=`
 * (field mode has no tabs and ignores the parameter). Plan and Liste are the editor's two views; Beete is the bed
 * list. The editor stays mounted behind the Beete tab - hidden, not unmounted - so its own state (tool options,
 * open panels) survives a switch just like the slice (unsaved operations, undo history, selection) and the route's
 * viewport. A tab switch only changes `tab`, which the unsaved-changes guard lets through; leaving the route asks.
 *
 * Workspace (WP 10.3, §17.3, GP-UX-063/067): with the editor on screen there is one header bar - the editor's - and it
 * carries back, the tabs, field mode and export/import (in its overflow); the page header shows only the title
 * ("Verhältnis zu Shell und Seitenkopf", UI-NFR-021). The canvas reports the room it has and the plan is fitted into
 * exactly that (`fillViewport`). A plan the editor cannot show (loading, error, empty, read-only) keeps the page
 * header actions and a tab row of its own.
 *
 * Indoor plan (WP 10.8, §9.8, GP-FR-182/183): a site of type `indoor`, `windowsill` or `grow_tent` uses the same page.
 * Its empty plan invites to draw the flat or to load a photo of it as a template (the underlay, GP-FR-033), and the
 * "Beete" tab reads "Pflanzplätze" - its URL value stays `beds`. The editor hides the frost layer of such a plan.
 */
import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link as RouterLink, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import AddIcon from '@mui/icons-material/Add';
import DrawOutlinedIcon from '@mui/icons-material/DrawOutlined';
import AddPhotoAlternateOutlinedIcon from '@mui/icons-material/AddPhotoAlternateOutlined';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import GridViewOutlinedIcon from '@mui/icons-material/GridViewOutlined';
import MapOutlinedIcon from '@mui/icons-material/MapOutlined';
import ViewListOutlinedIcon from '@mui/icons-material/ViewListOutlined';
import TouchAppIcon from '@mui/icons-material/TouchApp';
import EmptyState from '@/components/common/EmptyState';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import PageTitle from '@/components/layout/PageTitle';
import { useNotification } from '@/hooks/useNotification';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import { registerLazySlice } from '@/store/lazySlices';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { setBreadcrumbs } from '@/store/slices/uiSlice';
import {
  gardenPlanSlice,
  loadGardenPlan,
  resetGardenPlan,
  selectGardenPlanState,
  setPlanOffline,
  setSelection,
  selectIsDirty,
  type LoadStatus,
} from '../state/gardenPlanSlice';
import type { PlanModel } from '../model/planModel';
import { usePlanRenderer } from '../renderer/createRenderer';
import { useRendererLabels } from '../renderer/useRendererLabels';
import { GardenPlanEditor, type EditorTabs, type EditorView } from '../editor/GardenPlanEditor';
import { PlanViewTabs, type HeaderNav } from '../editor/EditorHeaderBar';
import type { CanvasAreaSize } from '../editor/useCanvasArea';
import { EDITOR_ANCHORS } from '../editor/anchors';
import type { BoundingBox, Point } from '../model/types';
import { zoomAround } from '../model/units';
import BedListSection from '../bed/BedListSection';
import { bedListReloadToken } from '../bed/bedListReload';
import { PlanIoMenu, usePlanIo } from '../io/PlanIoMenu';
import type { PlanSelection } from '../io/types';
import type { BedListItem } from '../bed/types';
import { boundingBox } from '../model/geometry';
import { isIndoorPlanSite } from '../model/siteKind';
import { EMPTY_PLAN_BOUNDS, fitIntoCanvas, fitViewport, focusViewport, planContentBounds } from './fitViewport';
import { useElementWidth } from './useElementWidth';
import { planModeHref, resolvePlanMode } from './planMode';
import { isTabOnlyChange, planTabSearch, resolvePlanTab, type PlanTab } from './planTab';
import CachedDataBanner from '../offline/CachedDataBanner';
import OfflineCacheMiss from '../offline/OfflineCacheMiss';
import ReadOnlyPlanView from '../offline/ReadOnlyPlanView';
import { useReloadOnReconnect } from '../offline/useReloadOnReconnect';

// Field mode is its own chunk (GP-UX-020): it loads only when the page opens in field mode.
const FieldModeView = lazy(() => import('../field/FieldModeView'));

// Register the slice before the first render of the page; idempotent, so a re-evaluated module
// (tests, HMR) is harmless.
registerLazySlice(gardenPlanSlice);

/** The first step an empty plan offers (#2617, WP 10.8): a bed in a garden; indoor, drawing the flat or a photo. */
type FirstStep = 'bed' | 'draw' | 'underlay';

/** The drawing may take this share of the viewport height before the page scrolls. */
const MAX_HEIGHT_SHARE = 0.7;
/** Both sides of the 1px canvas border; the drawing must fit inside it or the box scrolls sideways. */
const CANVAS_BORDER_PX = 2;

/** The ids that tie the tabs to their panels (WAI-ARIA "Tabs"); Plan and Liste share the editor's panel. */
const TAB_ID: Record<PlanTab, string> = {
  plan: 'garden-plan-tab-plan',
  list: 'garden-plan-tab-list',
  beds: 'garden-plan-tab-beds',
};
const EDITOR_PANEL_ID = 'garden-plan-tabpanel-editor';
const BEDS_PANEL_ID = 'garden-plan-tabpanel-beds';
const TAB_ICON: Record<PlanTab, React.ReactNode> = {
  plan: <MapOutlinedIcon fontSize="small" />,
  list: <ViewListOutlinedIcon fontSize="small" />,
  beds: <GridViewOutlinedIcon fontSize="small" />,
};

/**
 * Which opened plan the renderer is chosen for (D-01, `usePlanRenderer`): the site and the load that brought the
 * plan, so a reload, an import or the live plan after a cached one is decided afresh from its size, while an edit
 * (also a re-read after a placed template, which keeps the load) never swaps the drawing surface. `null` while a load
 * is under way: the plan still shown is the old one and keeps its renderer.
 */
function planLoadIdentity(plan: PlanModel | null, loadStatus: LoadStatus, loadRequestId: string | null): string | null {
  return plan !== null && loadStatus === 'ready' ? `${plan.siteKey}#${loadRequestId ?? ''}` : null;
}

export default function GardenPlanRoute() {
  const { key } = useParams<{ key: string }>();
  const [searchParams] = useSearchParams();
  const { pathname } = useLocation();
  const theme = useTheme();
  // `noSsr`: the first render already knows the width, so a phone never flashes the planning editor.
  const narrow = useMediaQuery(theme.breakpoints.down('sm'), { noSsr: true });
  // The default is decided once per visit: turning a tablet must not swap the editor (and its unsaved
  // changes) for field mode. The parameter still switches at any time.
  const [narrowAtOpen] = useState(narrow);
  const mode = resolvePlanMode(searchParams.get('mode'), narrowAtOpen);
  if (mode === 'field' && key) {
    return <FieldModeRoute siteKey={key} planningHref={planModeHref(pathname, searchParams, 'plan')} />;
  }
  return <PlanningPage fieldHref={planModeHref(pathname, searchParams, 'field')} />;
}

function FieldModeRoute({ siteKey, planningHref }: { siteKey: string; planningHref: string }) {
  const labels = useRendererLabels();
  // Field mode loads the plan into the same slice; the renderer follows its size like in planning mode.
  const fieldPlan = useAppSelector((state) => selectGardenPlanState(state).plan);
  const loadStatus = useAppSelector((state) => selectGardenPlanState(state).loadStatus);
  const loadRequestId = useAppSelector((state) => selectGardenPlanState(state).loadRequestId);
  const renderer = usePlanRenderer(fieldPlan, planLoadIdentity(fieldPlan, loadStatus, loadRequestId));
  return (
    <Box data-testid="garden-plan-page">
      <Suspense fallback={<LoadingSkeleton variant="card" />}>
        <FieldModeView siteKey={siteKey} renderer={renderer} labels={labels} planningHref={planningHref} />
      </Suspense>
    </Box>
  );
}

/** Planning mode: the editor with its tools, the bed list and import/export. */
function PlanningPage({ fieldHref }: { fieldHref: string }) {
  const { key } = useParams<{ key: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = resolvePlanTab(searchParams.get('tab'));
  // Every switch is a history entry, so "Back" returns to the previous tab (GP-UX-064).
  const selectTab = useCallback(
    (next: PlanTab) => setSearchParams((previous) => planTabSearch(previous, next)),
    [setSearchParams],
  );
  const onEditorView = useCallback((next: EditorView) => selectTab(next), [selectTab]);
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { canDelete, canEdit } = useTenantPermissions();
  const dispatch = useAppDispatch();
  const { plan, loadStatus, loadError, loadRequestId, cachedAt, offlineMiss } = useAppSelector(selectGardenPlanState);
  const online = useOnlineStatus();
  // Only a plan that came from the cache replaces the editor; a live plan keeps it mounted, locked while offline.
  const readOnlyReason: 'offline' | 'cached' | null = cachedAt === null ? null : online ? 'cached' : 'offline';
  // Import/export, the bed list and "add the first bed" need the server.
  const serverReachable = online && cachedAt === null;
  useEffect(() => {
    dispatch(setPlanOffline(!online));
  }, [dispatch, online]);
  const dirty = useAppSelector(selectIsDirty);
  const selected = useAppSelector((state) => selectGardenPlanState(state).selection);
  // The plan's selection as the keys the partial export names (GP-FR-172); slots and plants are no plan entities.
  const ioSelection = useMemo<PlanSelection>(
    () => ({
      locationKeys: selected.filter((ref) => ref.entity === 'location').map((ref) => ref.key),
      objectKeys: selected.filter((ref) => ref.entity === 'garden_object').map((ref) => ref.key),
    }),
    [selected],
  );
  const bedNames = useMemo<Record<string, string>>(
    () => Object.fromEntries(Object.values(plan?.locations ?? {}).map((location) => [location.key, location.name])),
    [plan],
  );
  const labels = useRendererLabels();
  const renderer = usePlanRenderer(plan, planLoadIdentity(plan, loadStatus, loadRequestId));
  const [canvasRef, canvasWidth] = useElementWidth<HTMLDivElement>();

  const load = useCallback(() => {
    if (key) void dispatch(loadGardenPlan(key));
  }, [dispatch, key]);
  // GP-FR-174: after a CSV bed list the new beds are selected once the plan is back, ready to be arranged.
  const loadAndSelectBeds = useCallback(
    (locationKeys: string[]) => {
      if (!key) return;
      void dispatch(loadGardenPlan(key)).then((action) => {
        if (loadGardenPlan.fulfilled.match(action) && locationKeys.length > 0) {
          dispatch(setSelection(locationKeys.map((locationKey) => ({ entity: 'location' as const, key: locationKey }))));
        }
      });
    },
    [dispatch, key],
  );

  useEffect(() => {
    load();
    // Leaving (or switching the site) forgets the plan: no stale garden flashes up next time.
    return () => {
      dispatch(resetGardenPlan());
    };
  }, [load, dispatch]);

  // A plan read from the cache, or missed offline, is read from the server again once the connection is back.
  useReloadOnReconnect(cachedAt !== null || offlineMiss, load);

  const siteName = plan?.siteName ?? null;
  useEffect(() => {
    if (!key || siteName === null) return undefined;
    dispatch(
      setBreadcrumbs([
        { label: 'nav.dashboard', path: '/dashboard' },
        { label: 'nav.sites', path: '/standorte/sites' },
        { label: siteName, path: `/standorte/sites/${key}` },
        { label: 'nav.gardenPlan' },
      ]),
    );
    return () => {
      dispatch(setBreadcrumbs([]));
    };
  }, [dispatch, key, siteName]);

  // The view is fitted once per load, not per edit: drawing or moving a bed must not make the plan
  // jump under the pointer. (State adjusted during render, the documented derived-state pattern.)
  const [fit, setFit] = useState<{ requestId: string | null; bounds: BoundingBox | null } | null>(null);
  if (plan !== null && loadStatus === 'ready' && fit?.requestId !== loadRequestId) {
    setFit({ requestId: loadRequestId, bounds: planContentBounds(plan) });
  }
  const contentBounds = fit?.bounds ?? null;
  // The empty plan's first step (#2617, WP 10.8): "add the first bed", or - indoor - "draw the flat" and "photo as a
  // template". The site it was chosen for keeps the editor on the default area of an empty plan, also once something
  // exists - the fit follows the content only on the next load.
  const [firstStep, setFirstStep] = useState<{ site: string; action: FirstStep } | null>(null);
  const startAction = key !== undefined && firstStep?.site === key ? firstStep.action : null;
  const startingFirstBed = startAction !== null;
  const startFirst = useCallback(
    (action: FirstStep) => {
      if (key) setFirstStep({ site: key, action });
    },
    [key],
  );
  const bounds = contentBounds ?? (startingFirstBed ? EMPTY_PLAN_BOUNDS : null);
  const indoor = isIndoorPlanSite(plan?.siteType);
  // The room the editor's canvas has (GP-UX-067): the plan is fitted into exactly that. Until the canvas has been
  // measured (and where nothing is laid out) the drawing takes the width and a share of the window height.
  const [canvasSize, setCanvasSize] = useState<CanvasAreaSize | null>(null);
  const fitted = useMemo(() => {
    if (bounds === null) return null;
    if (canvasSize !== null) {
      // A side panel that a selection docked beside the canvas still counts for the fit (WP 10.5): the plan keeps
      // its zoom and its top-left corner, so selecting a bed does not move it under the pointer.
      return fitIntoCanvas(
        bounds,
        Math.max(1, canvasSize.widthPx - CANVAS_BORDER_PX),
        Math.max(1, canvasSize.heightPx - CANVAS_BORDER_PX),
        Math.max(1, (canvasSize.fitWidthPx ?? canvasSize.widthPx) - CANVAS_BORDER_PX),
      );
    }
    // Not measured yet: a collapsed side panel reserves no width (§17.3, AC-5), so the drawing takes the full width.
    const viewportHeight = typeof window === 'undefined' ? 800 : window.innerHeight;
    return fitViewport(bounds, Math.max(1, canvasWidth - CANVAS_BORDER_PX), Math.max(240, viewportHeight * MAX_HEIGHT_SHARE));
  }, [bounds, canvasSize, canvasWidth]);

  // The user's view: pan and zoom replace the fitted view until "fit to area" (or another load)
  // drops them. It belongs to one site and one load, so neither needs an effect to reset it.
  const [view, setView] = useState<{
    siteKey: string | undefined;
    requestId: string | null;
    pxPerM: number;
    originM: Point;
  } | null>(null);
  const activeView = view && view.siteKey === key && view.requestId === loadRequestId ? view : null;
  const viewport = useMemo(() => {
    if (!fitted) return null;
    return activeView ? { ...fitted, pxPerM: activeView.pxPerM, originM: activeView.originM } : fitted;
  }, [fitted, activeView]);
  const viewportRef = useRef(viewport);
  useEffect(() => {
    viewportRef.current = viewport;
  });
  // The plan fitted into the canvas that is visible right now, without the room a docked panel takes (WP 10.5):
  // "fit to area" shows exactly that, and it is the lowest zoom (GP-FR-150) - the whole plan in view.
  const visibleFit = useMemo(() => {
    if (bounds === null || canvasSize === null) return null;
    const reserved = (canvasSize.fitWidthPx ?? canvasSize.widthPx) > canvasSize.widthPx;
    return reserved
      ? fitIntoCanvas(
          bounds,
          Math.max(1, canvasSize.widthPx - CANVAS_BORDER_PX),
          Math.max(1, canvasSize.heightPx - CANVAS_BORDER_PX),
        )
      : null;
  }, [bounds, canvasSize]);
  const minPxPerM = Math.min(fitted?.pxPerM ?? 1, visibleFit?.pxPerM ?? Number.POSITIVE_INFINITY);

  const onPan = useCallback(
    (dxPx: number, dyPx: number) => {
      const current = viewportRef.current;
      if (!current) return;
      // Dragging the plan right moves the viewport origin left; screen y points down, model y up.
      setView((previous) => {
        const base = previous && previous.siteKey === key && previous.requestId === loadRequestId ? previous : null;
        const origin = base ? base.originM : current.originM;
        const pxPerM = base ? base.pxPerM : current.pxPerM;
        return {
          siteKey: key,
          requestId: loadRequestId,
          pxPerM,
          originM: [origin[0] - dxPx / pxPerM, origin[1] + dyPx / pxPerM],
        };
      });
    },
    [key, loadRequestId],
  );
  const onZoom = useCallback(
    (pxPerM: number, anchorPx: Point) => {
      const current = viewportRef.current;
      if (!current) return;
      const next = zoomAround(current, pxPerM, anchorPx, minPxPerM);
      setView({ siteKey: key, requestId: loadRequestId, ...next });
    },
    [key, loadRequestId, minPxPerM],
  );
  // "Fit to area": back to the fitted view - or, while a selection's panel is docked beside the canvas, the plan
  // fitted into what is visible, kept as the user's view so the panel closing later does not move it again.
  const onFit = useCallback(() => {
    if (visibleFit === null) {
      setView(null);
      return;
    }
    setView({ siteKey: key, requestId: loadRequestId, pxPerM: visibleFit.pxPerM, originM: visibleFit.originM });
  }, [visibleFit, key, loadRequestId]);

  // GP-ACC-016, GP-FR-042: a row of the bed list opens the plan, selects the bed and brings its bounding box into
  // view. The canvas is shown one navigation later, so scrolling to it and focusing it wait for that render.
  const fittedWidth = fitted?.widthPx ?? 0;
  const fittedHeight = fitted?.heightPx ?? 0;
  const revealCanvas = useRef(false);
  const onSelectBed = useCallback(
    (bed: BedListItem) => {
      const placed = plan?.locations[bed.key];
      const geometry = placed?.geometry ?? null;
      if (!placed || !geometry) {
        // A bed that is not drawn yet has nothing to highlight; say so instead of selecting a ghost.
        notification.info(t('pages.bed.list.notPlaced', { name: bed.name }));
        return;
      }
      dispatch(setSelection([{ entity: 'location', key: bed.key }]));
      revealCanvas.current = true;
      selectTab('plan');
      if (fittedWidth === 0) return;
      const bounds = placed.bbox ?? boundingBox(geometry);
      const next = focusViewport(bounds, fittedWidth, fittedHeight, minPxPerM);
      setView({ siteKey: key, requestId: loadRequestId, ...next });
    },
    [dispatch, plan, fittedWidth, fittedHeight, minPxPerM, key, loadRequestId, notification, t, selectTab],
  );
  useEffect(() => {
    if (!revealCanvas.current || tab !== 'plan') return;
    revealCanvas.current = false;
    const canvas = document.getElementById(EDITOR_ANCHORS.canvas);
    canvas?.scrollIntoView?.({ block: 'nearest' });
    // The row that was clicked is hidden now; the focus follows the bed onto the plan (WCAG 2.4.3).
    canvas?.focus({ preventScroll: true });
  }, [tab]);

  const ioProps = {
    siteKey: key ?? '',
    siteName: plan?.siteName ?? '',
    canImport: canDelete,
    dirty,
    onImported: load,
    onBedsImported: loadAndSelectBeds,
    selection: ioSelection,
    bedNames,
  };
  // Export and import of the editor's overflow (GP-UX-050/051); they need the server.
  const io = usePlanIo(ioProps);
  const siteHref = `/standorte/sites/${key ?? ''}`;
  const openFieldMode = useCallback(() => navigate(fieldHref), [navigate, fieldHref]);
  const headerNav = useMemo<HeaderNav>(
    () => ({
      backHref: siteHref,
      siteName: plan?.siteName ?? t('pages.gardenPlan.title'),
      fieldHref,
      onFieldMode: openFieldMode,
      ioItems: key && serverReachable ? io.items : undefined,
    }),
    [siteHref, plan?.siteName, t, fieldHref, openFieldMode, key, serverReachable, io.items],
  );
  // Whether the tabs stand in the editor's header bar or in its overflow (GP-UX-063 step 4): the "Beete" panel is
  // named by its tab only while that tab is on screen.
  const [tabsInline, setTabsInline] = useState(true);
  const editorTabs = useMemo<EditorTabs>(
    () => ({
      value: tab,
      label: t('pages.gardenPlan.tabs.label'),
      items: (['plan', 'list', 'beds'] as const).map((value) => ({
        value,
        // GP-UX-064: indoor the "Beete" tab is "Pflanzplätze"; its URL value stays `beds`.
        label: t(value === 'beds' && indoor ? 'pages.gardenPlan.tabs.plantingSpots' : `pages.gardenPlan.tabs.${value}`),
        icon: TAB_ICON[value],
        id: TAB_ID[value],
        controls: value === 'beds' ? BEDS_PANEL_ID : EDITOR_PANEL_ID,
      })),
      onChange: (next: string) => selectTab(resolvePlanTab(next)),
      panelId: EDITOR_PANEL_ID,
      onInlineChange: setTabsInline,
    }),
    [tab, t, selectTab, indoor],
  );

  const backLink = (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
      <Button
        component={RouterLink}
        to={siteHref}
        startIcon={<ArrowBackIcon />}
        data-testid="garden-plan-back-link"
        sx={{ minHeight: 44 }}
      >
        {t('pages.gardenPlan.backToSite')}
      </Button>
      <Button
        component={RouterLink}
        to={fieldHref}
        variant="outlined"
        startIcon={<TouchAppIcon />}
        data-testid="garden-plan-mode-field"
        sx={{ minHeight: 44 }}
      >
        {t('pages.gardenPlan.field.toField')}
      </Button>
      {key && serverReachable && <PlanIoMenu {...ioProps} siteKey={key} />}
    </Box>
  );

  let content: React.ReactNode;
  // The editor brings the one header bar (back, tabs, field mode, export/import); every other state keeps the page
  // header actions and a tab row of its own.
  let editorShown = false;
  if (loadStatus === 'error' && offlineMiss) {
    content = <OfflineCacheMiss subject="plan" testId="garden-plan-offline-miss" onRetry={load} />;
  } else if (loadStatus === 'error' && loadError) {
    content = <ErrorDisplay error={loadError} onRetry={load} />;
  } else if (plan === null || loadStatus !== 'ready') {
    content = <LoadingSkeleton variant="card" />;
  } else if (viewport === null) {
    // GP-UX-049: a describing text and its next step - for the roles that may create beds. Indoor (GP-FR-182) the
    // step is the flat: draw it, or trace a photo of it.
    const empty = indoor ? 'pages.gardenPlan.emptyIndoor' : 'pages.gardenPlan.empty';
    const mayStart = canEdit && key !== undefined && serverReachable;
    content = (
      <Box data-testid="garden-plan-empty" data-plan-kind={indoor ? 'indoor' : 'garden'}>
        <EmptyState
          message={t(`${empty}.title`)}
          description={t(mayStart ? `${empty}.descriptionCanEdit` : `${empty}.description`)}
        />
        {mayStart && (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 2, pb: 4 }}>
            {indoor ? (
              <>
                <Button
                  variant="contained"
                  startIcon={<DrawOutlinedIcon />}
                  onClick={() => startFirst('draw')}
                  data-testid="garden-plan-empty-draw"
                  sx={{ minHeight: 48 }}
                >
                  {t('pages.gardenPlan.emptyIndoor.draw')}
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<AddPhotoAlternateOutlinedIcon />}
                  onClick={() => startFirst('underlay')}
                  data-testid="garden-plan-empty-underlay"
                  sx={{ minHeight: 48 }}
                >
                  {t('pages.gardenPlan.emptyIndoor.underlay')}
                </Button>
              </>
            ) : (
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => startFirst('bed')}
                data-testid="garden-plan-empty-add-bed"
                sx={{ minHeight: 48 }}
              >
                {t('pages.gardenPlan.empty.addFirstBed')}
              </Button>
            )}
          </Box>
        )}
      </Box>
    );
  } else if (readOnlyReason !== null) {
    content = (
      <ReadOnlyPlanView plan={plan} viewport={viewport} renderer={renderer} labels={labels} reason={readOnlyReason} />
    );
  } else {
    editorShown = true;
    content = (
      <>
        {!online && (
          <Alert severity="info" role="status" sx={{ mb: 2 }} data-testid="garden-plan-geometry-locked">
            {t('pages.gardenPlan.offline.geometryLocked.offline')}
          </Alert>
        )}
        <GardenPlanEditor
          plan={plan}
          viewport={viewport}
          renderer={renderer}
          labels={labels}
          onPan={onPan}
          onOpenLocation={(locationKey) => navigate(`/standorte/locations/${locationKey}`)}
          onOpenCare={(locationKey) => navigate(`/standorte/locations/${locationKey}#care`)}
          onZoom={onZoom}
          onFit={onFit}
          minPxPerM={minPxPerM}
          initialAddOpen={startAction === 'bed' && contentBounds === null}
          initialUnderlayOpen={startAction === 'underlay' && contentBounds === null}
          view={tab === 'list' ? 'list' : 'plan'}
          onViewChange={onEditorView}
          nav={headerNav}
          tabs={editorTabs}
          contentHidden={tab === 'beds'}
          onCanvasSize={setCanvasSize}
        />
      </>
    );
  }

  // The tabs belong to a loaded plan; while the first load runs or fails there is nothing to switch between.
  const showTabs = plan !== null;
  const editorTab: PlanTab = tab === 'list' ? 'list' : 'plan';
  const bedsShown = showTabs && tab === 'beds';
  // With the editor the tab panel of Plan and Liste is the editor's content; otherwise it is the box below.
  const ownPanel = showTabs && !editorShown;
  const bedsLabelled = !editorShown || tabsInline;

  return (
    <Box data-testid="garden-plan-page">
      {/* On the editor the header bar carries the actions; the page header shows only the title (§17.3). */}
      <PageTitle title={plan?.siteName ?? t('pages.gardenPlan.title')} action={editorShown ? undefined : backLink} />
      {/* The editor gives the canvas the height the intro would take (GP-UX-067); every other state explains. */}
      {!editorShown && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.gardenPlan.intro')}
        </Typography>
      )}
      {/* Unsaved changes (GP-NFR-005): a reload, a closed tab or a route change asks first - a tab switch does
          not (GP-UX-065), it keeps the editor mounted. */}
      <UnsavedChangesGuard dirty={dirty} allowNavigation={isTabOnlyChange} />
      {cachedAt !== null && plan !== null && loadStatus === 'ready' && <CachedDataBanner cachedAt={cachedAt} />}
      {ownPanel && (
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <PlanViewTabs tabs={editorTabs} />
        </Box>
      )}
      {/* The measured box exists in every state, so the first drawing already fits the width. Behind the Beete tab
          the editor hides its own content and keeps its header bar; any other content is hidden here. */}
      <Box
        ref={canvasRef}
        {...(ownPanel
          ? {
              id: EDITOR_PANEL_ID,
              role: 'tabpanel',
              'aria-labelledby': TAB_ID[editorTab],
              hidden: bedsShown,
              'data-testid': EDITOR_PANEL_ID,
            }
          : {})}
      >
        {content}
      </Box>
      {plan !== null && (
        <Box
          id={BEDS_PANEL_ID}
          role="tabpanel"
          {...(bedsLabelled
            ? { 'aria-labelledby': TAB_ID.beds }
            : { 'aria-label': t(indoor ? 'pages.gardenPlan.tabs.plantingSpots' : 'pages.gardenPlan.tabs.beds') })}
          hidden={!bedsShown}
          data-testid={BEDS_PANEL_ID}
          sx={{ mt: editorShown ? 1 : 0 }}
        >
          {/* Mounted on every tab, as under the plan before: it keeps its filters and follows every load and save
              (#2813), so the tab always shows the saved state. */}
          {key && serverReachable ? (
            <BedListSection
              siteKey={key}
              indoor={indoor}
              reloadToken={bedListReloadToken(loadRequestId, plan.revision)}
              onSelectBed={onSelectBed}
            />
          ) : (
            <Alert severity="info" role="status" data-testid="garden-plan-beds-offline">
              {t('pages.gardenPlan.tabs.bedsOffline')}
            </Alert>
          )}
        </Box>
      )}
      {io.dialogs}
    </Box>
  );
}
