/**
 * The "Plan" tab of the bed view (REQ-053 GP-FR-041): the bed frame with its slots, rows, zones and
 * plant markers at scale, plus the dimensions. It loads the site plan (GP-API-001), keeps the bed's
 * subtree and draws it read-only with the same renderer as the garden plan; editing stays on the
 * garden plan page, which this tab links to.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import EmptyState from '@/components/common/EmptyState';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { parseApiError } from '@/api/errors';
import { getGardenPlan } from '../api/gardenPlan';
import { boundingBox } from '../model/geometry';
import { locationSubtree, normalizePlan, type PlanModel } from '../model/planModel';
import { SvgPlanRenderer } from '../renderer/SvgPlanRenderer';
import { useRendererLabels } from '../renderer/useRendererLabels';
import { fitViewport } from '../routes/fitViewport';
import { useElementWidth } from '../routes/useElementWidth';
import type { BedSummary } from './types';

/** The drawing may take this share of the window height before the page scrolls. */
const MAX_HEIGHT_SHARE = 0.6;
/** Both sides of the 1px canvas border; the drawing must fit inside it. */
const CANVAS_BORDER_PX = 2;

interface BedPlanTabProps {
  bed: BedSummary;
  /** Offer the link to the garden plan (the module may be switched off). */
  planLinkVisible: boolean;
}

type PlanState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; model: PlanModel };

/** The plan reduced to the bed and everything below it; the rest of the garden is not this view's business. */
export function bedSubModel(plan: PlanModel, bedKey: string): PlanModel {
  const keys = new Set(locationSubtree(plan, bedKey));
  const pick = <T,>(items: Record<string, T>, keep: (item: T) => boolean): Record<string, T> =>
    Object.fromEntries(Object.entries(items).filter(([, item]) => keep(item)));
  const slots = pick(plan.slots, (slot) => keys.has(slot.location_key));
  return {
    ...plan,
    settings: null,
    locations: pick(plan.locations, (location) => keys.has(location.key)),
    gardenObjects: {},
    slots,
    plants: pick(plan.plants, (plant) =>
      plant.slot_key ? plant.slot_key in slots : plant.location_key != null && keys.has(plant.location_key),
    ),
  };
}

export default function BedPlanTab({ bed, planLinkVisible }: BedPlanTabProps) {
  const { t } = useTranslation();
  const labels = useRendererLabels();
  const renderer = useMemo(() => new SvgPlanRenderer(), []);
  const [canvasRef, canvasWidth] = useElementWidth<HTMLDivElement>();
  const [state, setState] = useState<PlanState>({ status: 'loading' });
  const [attempt, setAttempt] = useState(0);
  const placed = Boolean(bed.geometry);
  const siteKey = bed.site_key;
  const bedKey = bed.key;

  useEffect(() => {
    if (!placed) return undefined;
    let cancelled = false;
    getGardenPlan(siteKey, ['plants'])
      .then((response) => {
        if (!cancelled) setState({ status: 'ready', model: bedSubModel(normalizePlan(response), bedKey) });
      })
      .catch((error: unknown) => {
        if (!cancelled) setState({ status: 'error', message: parseApiError(error) });
      });
    return () => {
      cancelled = true;
    };
  }, [placed, siteKey, bedKey, attempt]);

  const retry = useCallback(() => {
    setState({ status: 'loading' });
    setAttempt((value) => value + 1);
  }, []);

  const model = state.status === 'ready' ? state.model : null;
  const location = model?.locations[bedKey] ?? null;
  const geometry = location?.geometry ?? null;
  const viewport = useMemo(() => {
    if (!location || !geometry) return null;
    const bounds = location.bbox ?? boundingBox(geometry);
    const windowHeight = typeof window === 'undefined' ? 800 : window.innerHeight;
    return fitViewport(bounds, Math.max(1, canvasWidth - CANVAS_BORDER_PX), Math.max(240, windowHeight * MAX_HEIGHT_SHARE));
  }, [location, geometry, canvasWidth]);
  const selection = useMemo(() => ({ selectedKeys: new Set([bedKey]) }), [bedKey]);
  const rendered = useMemo(
    () =>
      model && viewport
        ? renderer.render(model, viewport, selection, { labels, enteredLocationKey: bedKey })
        : null,
    [renderer, model, viewport, selection, labels, bedKey],
  );

  const planLink = planLinkVisible ? (
    <Button
      component={RouterLink}
      to={`/standorte/sites/${siteKey}/plan`}
      sx={{ minHeight: 44 }}
      data-testid="bed-plan-open-garden"
    >
      {t('pages.bed.plan.openGarden')}
    </Button>
  ) : null;

  if (!placed) {
    return (
      <Box data-testid="bed-plan-tab">
        <EmptyState
          message={t('pages.bed.plan.notPlaced.title')}
          description={t('pages.bed.plan.notPlaced.description')}
        />
        <Box sx={{ display: 'flex', justifyContent: 'center' }}>{planLink}</Box>
      </Box>
    );
  }

  const slotCount = model ? Object.keys(model.slots).length : 0;
  const plantCount = model ? Object.keys(model.plants).length : 0;

  return (
    <Box data-testid="bed-plan-tab">
      <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 1, mb: 1 }}>
        <Typography variant="body2" color="text.secondary" data-testid="bed-plan-dimensions">
          {geometry && location
            ? t('pages.bed.plan.summary', {
                size: labels.size(geometry, location.area_m2),
                slots: slotCount,
                plants: plantCount,
              })
            : t('pages.bed.plan.loading')}
        </Typography>
        {planLink}
      </Box>
      <Box ref={canvasRef}>
        {state.status === 'error' ? (
          <ErrorDisplay error={state.message} onRetry={retry} />
        ) : rendered === null ? (
          <LoadingSkeleton variant="card" />
        ) : (
          <Box
            data-testid="bed-plan-canvas"
            sx={{
              position: 'relative',
              overflow: 'hidden',
              width: viewport ? viewport.widthPx + CANVAS_BORDER_PX : undefined,
              maxWidth: '100%',
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              bgcolor: 'background.paper',
            }}
          >
            {rendered}
          </Box>
        )}
      </Box>
    </Box>
  );
}
