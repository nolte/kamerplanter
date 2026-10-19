/**
 * The garden plan page (REQ-053 WP 2.3): `standorte/sites/:key/plan`.
 *
 * This module is the lazy route chunk. It is the one place that chooses a renderer implementation
 * (`SvgPlanRenderer`, GP-NFR-009) and that injects the plan slice into the root reducer, so neither
 * the renderer, the plan model nor the slice are part of the initial bundle (UI-NFR-003).
 *
 * The page loads the plan, explains the empty and error states and mounts the editor (WP 2.4:
 * select, pan, draw, handles). It owns the viewport - fitted to the plan, then panned and zoomed
 * (WP 2.5: zoom levels, wheel, "fit to area"). `?mode=field` is only recognised and announced
 * (GP-FR-182, §18).
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link as RouterLink, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import EmptyState from '@/components/common/EmptyState';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import PageTitle from '@/components/layout/PageTitle';
import { useNotification } from '@/hooks/useNotification';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import { registerLazySlice } from '@/store/lazySlices';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { setBreadcrumbs } from '@/store/slices/uiSlice';
import {
  gardenPlanSlice,
  loadGardenPlan,
  resetGardenPlan,
  selectGardenPlanState,
  setSelection,
  selectIsDirty,
} from '../state/gardenPlanSlice';
import { SvgPlanRenderer } from '../renderer/SvgPlanRenderer';
import { useRendererLabels } from '../renderer/useRendererLabels';
import { GardenPlanEditor } from '../editor/GardenPlanEditor';
import { EDITOR_SIDEBAR_RESERVE_PX } from '../editor/layout';
import { EDITOR_ANCHORS } from '../editor/anchors';
import type { BoundingBox, Point } from '../model/types';
import { zoomAround } from '../model/units';
import BedListSection from '../bed/BedListSection';
import { PlanIoMenu } from '../io/PlanIoMenu';
import type { BedListItem } from '../bed/types';
import { boundingBox } from '../model/geometry';
import { fitViewport, focusViewport, planContentBounds } from './fitViewport';
import { useElementWidth } from './useElementWidth';

// Register the slice before the first render of the page; idempotent, so a re-evaluated module
// (tests, HMR) is harmless.
registerLazySlice(gardenPlanSlice);

/** The drawing may take this share of the viewport height before the page scrolls. */
const MAX_HEIGHT_SHARE = 0.7;
/** Both sides of the 1px canvas border; the drawing must fit inside it or the box scrolls sideways. */
const CANVAS_BORDER_PX = 2;

export default function GardenPlanRoute() {
  const { key } = useParams<{ key: string }>();
  const [searchParams] = useSearchParams();
  const { t } = useTranslation();
  const theme = useTheme();
  const navigate = useNavigate();
  const notification = useNotification();
  const { canDelete } = useTenantPermissions();
  // From md up the properties panel sits beside the plan and takes its width from the drawing.
  const sidebarBeside = useMediaQuery(theme.breakpoints.up('md'));
  const dispatch = useAppDispatch();
  const { plan, loadStatus, loadError, loadRequestId } = useAppSelector(selectGardenPlanState);
  const dirty = useAppSelector(selectIsDirty);
  const labels = useRendererLabels();
  const renderer = useMemo(() => new SvgPlanRenderer(), []);
  const [canvasRef, canvasWidth] = useElementWidth<HTMLDivElement>();
  const fieldMode = searchParams.get('mode') === 'field';

  const load = useCallback(() => {
    if (key) void dispatch(loadGardenPlan(key));
  }, [dispatch, key]);

  useEffect(() => {
    load();
    // Leaving (or switching the site) forgets the plan: no stale garden flashes up next time.
    return () => {
      dispatch(resetGardenPlan());
    };
  }, [load, dispatch]);

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
  const bounds = fit?.bounds ?? null;
  const fitted = useMemo(() => {
    if (bounds === null) return null;
    const viewportHeight = typeof window === 'undefined' ? 800 : window.innerHeight;
    return fitViewport(bounds, Math.max(1, canvasWidth - CANVAS_BORDER_PX - (sidebarBeside ? EDITOR_SIDEBAR_RESERVE_PX : 0)), Math.max(240, viewportHeight * MAX_HEIGHT_SHARE));
  }, [bounds, canvasWidth, sidebarBeside]);

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
  const minPxPerM = fitted?.pxPerM ?? 1;

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
  const onFit = useCallback(() => setView(null), []);

  // GP-ACC-016: a row of the bed list selects the bed and brings its bounding box into view.
  const fittedWidth = fitted?.widthPx ?? 0;
  const fittedHeight = fitted?.heightPx ?? 0;
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
      if (fittedWidth === 0) return;
      const bounds = placed.bbox ?? boundingBox(geometry);
      const next = focusViewport(bounds, fittedWidth, fittedHeight, minPxPerM);
      setView({ siteKey: key, requestId: loadRequestId, ...next });
      document.getElementById(EDITOR_ANCHORS.canvas)?.scrollIntoView?.({ block: 'nearest' });
    },
    [dispatch, plan, fittedWidth, fittedHeight, minPxPerM, key, loadRequestId, notification, t],
  );

  const backLink = (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
      <Button
        component={RouterLink}
        to={`/standorte/sites/${key ?? ''}`}
        startIcon={<ArrowBackIcon />}
        data-testid="garden-plan-back-link"
        sx={{ minHeight: 44 }}
      >
        {t('pages.gardenPlan.backToSite')}
      </Button>
      {key && (
        <PlanIoMenu
          siteKey={key}
          siteName={plan?.siteName ?? ''}
          canImport={canDelete}
          dirty={dirty}
          fieldMode={fieldMode}
          onImported={load}
        />
      )}
    </Box>
  );

  let content: React.ReactNode;
  if (loadStatus === 'error' && loadError) {
    content = <ErrorDisplay error={loadError} onRetry={load} />;
  } else if (plan === null || loadStatus !== 'ready') {
    content = <LoadingSkeleton variant="card" />;
  } else if (bounds === null || viewport === null) {
    content = (
      <Box data-testid="garden-plan-empty">
        <EmptyState
          message={t('pages.gardenPlan.empty.title')}
          description={t('pages.gardenPlan.empty.description')}
        />
      </Box>
    );
  } else {
    content = (
      <GardenPlanEditor
        plan={plan}
        viewport={viewport}
        renderer={renderer}
        labels={labels}
        fieldMode={fieldMode}
        onPan={onPan}
        onOpenLocation={(locationKey) => navigate(`/standorte/locations/${locationKey}`)}
        onZoom={onZoom}
        onFit={onFit}
        minPxPerM={minPxPerM}
      />
    );
  }

  return (
    <Box data-testid="garden-plan-page">
      <PageTitle title={plan?.siteName ?? t('pages.gardenPlan.title')} action={backLink} />
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.gardenPlan.intro')}
      </Typography>
      {fieldMode && (
        <Alert severity="info" sx={{ mb: 2 }} data-testid="garden-plan-field-mode-hint">
          {t('pages.gardenPlan.fieldModeHint')}
        </Alert>
      )}
      {/* Unsaved changes (GP-NFR-005): a reload, a closed tab or a route change asks first. */}
      <UnsavedChangesGuard dirty={dirty} />
      {/* The measured box exists in every state, so the first drawing already fits the width. */}
      <Box ref={canvasRef}>{content}</Box>
      {key && plan !== null && (
        <BedListSection siteKey={key} reloadToken={loadRequestId} onSelectBed={onSelectBed} />
      )}
    </Box>
  );
}
