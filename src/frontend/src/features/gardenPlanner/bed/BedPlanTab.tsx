/**
 * The "Plan" tab of the bed view (REQ-053 GP-FR-041): the bed frame with its slots, rows, zones and
 * plant markers at scale, plus the dimensions. It loads the site plan (GP-API-001), keeps the bed's
 * subtree and draws it read-only with the same renderer as the garden plan; editing stays on the
 * garden plan page, which this tab links to.
 */
import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState, type FocusEvent, type MouseEvent, type PointerEvent } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import EmptyState from '@/components/common/EmptyState';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { parseApiError } from '@/api/errors';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import { getGardenPlan } from '../api/gardenPlan';
import { boundingBox } from '../model/geometry';
import { locationSubtree, normalizePlan, type PlanModel } from '../model/planModel';
import { SvgPlanRenderer } from '../renderer/SvgPlanRenderer';
import { useRendererLabels } from '../renderer/useRendererLabels';
import { fitViewport } from '../routes/fitViewport';
import { useElementWidth } from '../routes/useElementWidth';
import PlantActionHost, { type PlantActionTarget } from '../planting/PlantActionHost';
import { usePhaseColors } from '../planting/phaseColors';
import PlantInfoPopover from '../planting/PlantInfoPopover';
import PlantStateLegend from '../planting/PlantStateLegend';
import { usePlantInfoHover } from '../planting/usePlantInfoHover';
import { usePlantStates } from '../planting/usePlantStates';
import { usePlantStateText } from '../planting/usePlantStateText';
import type { BedSummary } from './types';

const PlantInfoSheet = lazy(() => import('../planting/PlantInfoSheet'));

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
  const { canEdit } = useTenantPermissions();
  const canvasBoxRef = useRef<HTMLDivElement | null>(null);
  // The bubble is placed inside the canvas: it needs the element in render, the handlers read the ref.
  const [canvasBox, setCanvasBox] = useState<HTMLDivElement | null>(null);
  const canvasBoxCallback = useCallback((element: HTMLDivElement | null) => {
    canvasBoxRef.current = element;
    setCanvasBox(element);
  }, []);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [target, setTarget] = useState<PlantActionTarget | null>(null);
  const [sheetKey, setSheetKey] = useState<string | null>(null);
  const lastPointerType = useRef('mouse');
  const placed = Boolean(bed.geometry);
  const siteKey = bed.site_key;
  const bedKey = bed.key;
  const { states, refresh: refreshStates } = usePlantStates(bedKey, placed);
  const stateText = usePlantStateText();

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
    refreshStates();
  }, [refreshStates]);

  const model = state.status === 'ready' ? state.model : null;
  const location = model?.locations[bedKey] ?? null;
  const geometry = location?.geometry ?? null;
  const viewport = useMemo(() => {
    if (!location || !geometry) return null;
    const bounds = location.bbox ?? boundingBox(geometry);
    const windowHeight = typeof window === 'undefined' ? 800 : window.innerHeight;
    return fitViewport(bounds, Math.max(1, canvasWidth - CANVAS_BORDER_PX), Math.max(240, windowHeight * MAX_HEIGHT_SHARE));
  }, [location, geometry, canvasWidth]);
  const selectedPlant = selectedKey && model ? (model.plants[selectedKey] ?? null) : null;
  const selection = useMemo(
    () => ({ selectedKeys: new Set(selectedPlant ? [bedKey, selectedPlant.key] : [bedKey]) }),
    [bedKey, selectedPlant],
  );
  const plantPhases = useMemo(
    () => (model ? Object.values(model.plants).map((plant) => plant.phase_key) : []),
    [model],
  );
  const phaseColors = usePhaseColors(plantPhases);
  const markerStates = useMemo(
    () => Object.fromEntries(Object.entries(states).map(([key, view]) => [key, stateText.marker(view)])),
    [states, stateText],
  );

  // The plant under a client point: the hover bubble reads the local state, it never requests anything.
  const plantAt = useCallback(
    (clientX: number, clientY: number): string | null => {
      const box = canvasBoxRef.current;
      if (!box || !model) return null;
      const rect = box.getBoundingClientRect();
      const key = renderer.hitTest([clientX - rect.left, clientY - rect.top]);
      return key && model.plants[key] ? key : null;
    },
    [renderer, model],
  );
  const hover = usePlantInfoHover({ keyAt: plantAt });
  const { openByFocus } = hover;
  const openView = hover.open ? (states[hover.open.key] ?? null) : null;
  const sheetView = sheetKey ? (states[sheetKey] ?? null) : null;
  const onFocusKey = useCallback(
    (key: string) => {
      if (key in states) openByFocus(key);
    },
    [states, openByFocus],
  );
  const rendered = useMemo(
    () =>
      model && viewport
        ? renderer.render(model, viewport, selection, {
            labels,
            enteredLocationKey: bedKey,
            phaseColors,
            plantStates: markerStates,
            describedPlantKey: openView?.plant_key ?? null,
            onFocusKey,
            onActivateKey: (key) => setSelectedKey((current) => (current === key ? null : key)),
          })
        : null,
    [renderer, model, viewport, selection, labels, bedKey, phaseColors, markerStates, openView, onFocusKey],
  );

  // A pointer or a tap on a plant marker selects it; the panel below offers the plant's actions. A tap on touch
  // also opens the plant info as a sheet (GP-UX-040); the mouse gets the hover bubble instead.
  const onCanvasClick = (event: MouseEvent<HTMLDivElement>) => {
    const key = plantAt(event.clientX, event.clientY);
    if (key) setSelectedKey((current) => (current === key ? null : key));
    else setSelectedKey(null);
    if (key && lastPointerType.current !== 'mouse' && key in states) {
      hover.close();
      setSheetKey(key);
    }
  };
  const onCanvasPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    lastPointerType.current = event.pointerType;
  };
  const onCanvasBlur = (event: FocusEvent<HTMLDivElement>) => {
    const next = event.relatedTarget;
    if (!(next instanceof Node) || !event.currentTarget.contains(next)) hover.closeFocus();
  };

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
            ref={canvasBoxCallback}
            onClick={onCanvasClick}
            onPointerDown={onCanvasPointerDown}
            onPointerMove={hover.onPointerMove}
            onPointerLeave={hover.onPointerLeave}
            onBlur={onCanvasBlur}
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
            {openView ? (
              <PlantInfoPopover
                view={openView}
                container={canvasBox}
                onPointerEnter={hover.onBubbleEnter}
                onPointerLeave={hover.onBubbleLeave}
              />
            ) : null}
          </Box>
        )}
      </Box>
      {Object.keys(states).length > 0 ? <PlantStateLegend /> : null}
      {selectedPlant ? (
        <Box
          component="section"
          aria-label={t('pages.bed.plan.plantPanel', { id: selectedPlant.instance_id })}
          data-testid="bed-plan-plant-panel"
          sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 1 }}
        >
          <Typography variant="subtitle2" component="h3" sx={{ flex: '1 1 auto' }}>
            {t('pages.bed.plan.plantPanel', { id: selectedPlant.instance_id })}
          </Typography>
          {canEdit && selectedPlant.slot_key ? (
            <Button
              onClick={() =>
                setTarget({
                  action: 'correct',
                  plantKey: selectedPlant.key,
                  slotKey: selectedPlant.slot_key ?? null,
                  plantLabel: selectedPlant.instance_id,
                })
              }
              sx={{ minHeight: 44 }}
              data-testid="bed-plan-correct"
            >
              {t('pages.bed.planting.tab.correct')}
            </Button>
          ) : null}
          {canEdit ? (
            <Button
              onClick={() =>
                setTarget({
                  action: 'transplant',
                  plantKey: selectedPlant.key,
                  slotKey: selectedPlant.slot_key ?? null,
                  plantLabel: selectedPlant.instance_id,
                })
              }
              sx={{ minHeight: 44 }}
              data-testid="bed-plan-transplant"
            >
              {t('pages.bed.planting.tab.transplant')}
            </Button>
          ) : null}
        </Box>
      ) : null}
      <PlantActionHost bed={bed} target={target} onClose={() => setTarget(null)} onChanged={retry} />
      {sheetView ? (
        <Suspense fallback={null}>
          <PlantInfoSheet view={sheetView} onClose={() => setSheetKey(null)} />
        </Suspense>
      ) : null}
    </Box>
  );
}
