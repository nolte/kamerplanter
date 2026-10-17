/**
 * The garden plan page (REQ-053 WP 2.3): `standorte/sites/:key/plan`.
 *
 * This module is the lazy route chunk. It is the one place that chooses a renderer implementation
 * (`SvgPlanRenderer`, GP-NFR-009) and that injects the plan slice into the root reducer, so neither
 * the renderer, the plan model nor the slice are part of the initial bundle (UI-NFR-003).
 *
 * The page loads the plan, explains the empty and error states and mounts the editor (WP 2.4:
 * select, pan, draw, handles). It owns the viewport - fitted to the plan, shifted by the pan tool;
 * zoom and the fit button follow in WP 2.5. `?mode=field` is only recognised and announced
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
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import PageTitle from '@/components/layout/PageTitle';
import { registerLazySlice } from '@/store/lazySlices';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { setBreadcrumbs } from '@/store/slices/uiSlice';
import {
  gardenPlanSlice,
  loadGardenPlan,
  resetGardenPlan,
  selectGardenPlanState,
} from '../state/gardenPlanSlice';
import { SvgPlanRenderer } from '../renderer/SvgPlanRenderer';
import { useRendererLabels } from '../renderer/useRendererLabels';
import { GardenPlanEditor } from '../editor/GardenPlanEditor';
import { EDITOR_SIDEBAR_RESERVE_PX } from '../editor/layout';
import type { BoundingBox, Point } from '../model/types';
import { fitViewport, planContentBounds } from './fitViewport';

// Register the slice before the first render of the page; idempotent, so a re-evaluated module
// (tests, HMR) is harmless.
registerLazySlice(gardenPlanSlice);

/** Width used until the container has been measured (and where ResizeObserver does not exist). */
const FALLBACK_WIDTH_PX = 640;
/** The drawing may take this share of the viewport height before the page scrolls. */
const MAX_HEIGHT_SHARE = 0.7;
/** Both sides of the 1px canvas border; the drawing must fit inside it or the box scrolls sideways. */
const CANVAS_BORDER_PX = 2;

/** The width of the element the ref points at, kept up to date while it resizes. */
function useElementWidth<T extends HTMLElement>(): [React.RefObject<T | null>, number] {
  const ref = useRef<T | null>(null);
  const [width, setWidth] = useState(FALLBACK_WIDTH_PX);
  useEffect(() => {
    const element = ref.current;
    if (element === null || typeof ResizeObserver === 'undefined') return undefined;
    const measure = () => {
      if (element.clientWidth > 0) setWidth(element.clientWidth);
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  return [ref, width];
}

export default function GardenPlanRoute() {
  const { key } = useParams<{ key: string }>();
  const [searchParams] = useSearchParams();
  const { t } = useTranslation();
  const theme = useTheme();
  const navigate = useNavigate();
  // From md up the properties panel sits beside the plan and takes its width from the drawing.
  const sidebarBeside = useMediaQuery(theme.breakpoints.up('md'));
  const dispatch = useAppDispatch();
  const { plan, loadStatus, loadError, loadRequestId } = useAppSelector(selectGardenPlanState);
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

  // The pan tool shifts the fitted view (model metres). The shift belongs to one site: another
  // site starts unshifted again, without an effect to reset it.
  const [pan, setPan] = useState<{ siteKey: string | undefined; offsetM: Point }>({ siteKey: key, offsetM: [0, 0] });
  const fittedPxPerM = fitted?.pxPerM ?? 1;
  const onPan = useCallback(
    (dxPx: number, dyPx: number) => {
      // Dragging the plan right moves the viewport origin left; screen y points down, model y up.
      setPan((previous) => {
        const [x, y] = previous.siteKey === key ? previous.offsetM : [0, 0];
        return { siteKey: key, offsetM: [x - dxPx / fittedPxPerM, y + dyPx / fittedPxPerM] };
      });
    },
    [fittedPxPerM, key],
  );
  const viewport = useMemo(() => {
    if (!fitted) return null;
    const [panX, panY] = pan.siteKey === key ? pan.offsetM : [0, 0];
    return { ...fitted, originM: [fitted.originM[0] + panX, fitted.originM[1] + panY] as Point };
  }, [fitted, pan, key]);

  const backLink = (
    <Button
      component={RouterLink}
      to={`/standorte/sites/${key ?? ''}`}
      startIcon={<ArrowBackIcon />}
      data-testid="garden-plan-back-link"
      sx={{ minHeight: 44 }}
    >
      {t('pages.gardenPlan.backToSite')}
    </Button>
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
      {/* The measured box exists in every state, so the first drawing already fits the width. */}
      <Box ref={canvasRef}>{content}</Box>
    </Box>
  );
}
