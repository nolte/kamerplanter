/**
 * The "Map" tab of field mode (REQ-053 GP-UX-020/022/025, §18.1 step 2): the plan without tools, grid or
 * handles. A tap on a bed - or close to one too small to hit - opens its sheet and brings it into view.
 * Every gesture has a button: zoom in, zoom out and "whole plan" are 64 px targets, and there is no pan
 * gesture at all (tapping a bed is the way to move). The view is remembered per site on this device and
 * only restored while it still shows the plan on the current canvas; otherwise the map opens on "fit".
 */
import { useCallback, useMemo, useRef, useState, type MouseEvent } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';
import ZoomOutMapIcon from '@mui/icons-material/ZoomOutMap';
import { KIOSK_TOUCH_TARGET } from '@/kiosk/kioskTheme';
import { boundingBox } from '../model/geometry';
import type { PlanModel } from '../model/planModel';
import type { Point } from '../model/types';
import { stepZoom, zoomAround } from '../model/units';
import type { PlanRenderer, RendererLabels } from '../renderer/types';
import { fitViewport, focusViewport, planContentBounds } from '../routes/fitViewport';
import { useElementWidth } from '../routes/useElementWidth';
import { bedOfKey, MIN_BED_TARGET_PX, nearestBed, restoreFieldView } from './fieldMapLogic';
import type { FieldViewport } from './fieldPrefs';

/** The drawing may take this share of the viewport height in the field. */
const MAX_HEIGHT_SHARE = 0.6;
const CANVAS_BORDER_PX = 4;

interface FieldMapProps {
  plan: PlanModel;
  renderer: PlanRenderer;
  labels: RendererLabels;
  /** The beds of the list; only they open a sheet. */
  bedKeys: ReadonlySet<string>;
  selectedBedKey: string | null;
  /** The view this device last had on this site, if any; validated before it is applied. */
  initialView: FieldViewport | null;
  onViewChange: (view: FieldViewport) => void;
  onSelectBed: (bedKey: string) => void;
}

export default function FieldMap({
  plan,
  renderer,
  labels,
  bedKeys,
  selectedBedKey,
  initialView,
  onViewChange,
  onSelectBed,
}: FieldMapProps) {
  const { t } = useTranslation();
  const [boxRef, boxWidth] = useElementWidth<HTMLDivElement>();
  const svgBoxRef = useRef<HTMLDivElement>(null);
  const bounds = useMemo(() => planContentBounds(plan), [plan]);
  const fitted = useMemo(() => {
    if (bounds === null) return null;
    const height = typeof window === 'undefined' ? 800 : window.innerHeight;
    return fitViewport(bounds, Math.max(1, boxWidth - CANVAS_BORDER_PX), Math.max(240, height * MAX_HEIGHT_SHARE));
  }, [bounds, boxWidth]);
  const [view, setView] = useState<FieldViewport | null>(initialView);
  const minPxPerM = fitted?.pxPerM ?? 1;
  const viewport = useMemo(() => {
    if (!fitted || !bounds) return null;
    // The remembered view is checked against the current canvas and plan; one that would show nothing
    // (another device, a turned phone) falls back to the whole plan.
    const restored = restoreFieldView(view, bounds, fitted.widthPx, fitted.heightPx, minPxPerM);
    return restored ? { ...fitted, ...restored } : fitted;
  }, [fitted, bounds, view, minPxPerM]);

  const changeView = useCallback(
    (next: FieldViewport | null) => {
      setView(next);
      if (next) onViewChange(next);
      else if (fitted) onViewChange({ pxPerM: fitted.pxPerM, originM: fitted.originM });
    },
    [fitted, onViewChange],
  );

  const zoom = (direction: 1 | -1) => {
    if (!viewport) return;
    const center: Point = [viewport.widthPx / 2, viewport.heightPx / 2];
    changeView(zoomAround(viewport, stepZoom(viewport.pxPerM, direction, minPxPerM), center, minPxPerM));
  };

  const focusBed = useCallback(
    (bedKey: string) => {
      const location = plan.locations[bedKey];
      if (!fitted || !location?.geometry) return;
      const box = location.bbox ?? boundingBox(location.geometry);
      changeView(focusViewport(box, fitted.widthPx, fitted.heightPx, minPxPerM));
    },
    [plan, fitted, minPxPerM, changeView],
  );

  const choose = useCallback(
    (bedKey: string) => {
      focusBed(bedKey);
      onSelectBed(bedKey);
    },
    [focusBed, onSelectBed],
  );

  const onActivateKey = useCallback(
    (key: string) => {
      const bedKey = bedOfKey(plan, key, bedKeys);
      if (bedKey) choose(bedKey);
    },
    [plan, bedKeys, choose],
  );

  const selection = useMemo(
    () => ({ selectedKeys: new Set(selectedBedKey ? [selectedBedKey] : []), focusKey: selectedBedKey }),
    [selectedBedKey],
  );
  const drawing = useMemo(
    () =>
      viewport ? renderer.render(plan, viewport, selection, { labels, fieldMode: true, onActivateKey }) : null,
    [renderer, plan, viewport, selection, labels, onActivateKey],
  );

  const onTap = (event: MouseEvent<HTMLDivElement>) => {
    if (!viewport) return;
    // Screen coordinates are relative to the drawing itself, inside the frame's border.
    const rect = svgBoxRef.current?.querySelector('svg')?.getBoundingClientRect();
    const point: Point = [event.clientX - (rect?.left ?? 0), event.clientY - (rect?.top ?? 0)];
    for (const key of renderer.hitTestAll(point)) {
      const bedKey = bedOfKey(plan, key, bedKeys);
      if (bedKey) {
        choose(bedKey);
        return;
      }
    }
    // A bed smaller than the minimum target is still found by a tap next to it (auto-zoom on the bed).
    const near = nearestBed(plan, bedKeys, renderer.toModel(point), MIN_BED_TARGET_PX / 2 / viewport.pxPerM);
    if (near) choose(near);
  };

  const buttonSx = { minHeight: KIOSK_TOUCH_TARGET, minWidth: KIOSK_TOUCH_TARGET, borderWidth: 2 };

  return (
    <Box ref={boxRef} data-testid="field-map">
      <Box
        role="toolbar"
        aria-label={t('pages.gardenPlan.field.map.toolbar')}
        sx={{ display: 'flex', gap: 1, mb: 1, flexWrap: 'wrap' }}
      >
        <Button
          variant="outlined"
          color="inherit"
          onClick={() => zoom(1)}
          aria-label={t('pages.gardenPlan.field.map.zoomIn')}
          sx={buttonSx}
          data-testid="field-map-zoom-in"
        >
          <ZoomInIcon />
        </Button>
        <Button
          variant="outlined"
          color="inherit"
          onClick={() => zoom(-1)}
          disabled={!viewport || viewport.pxPerM <= minPxPerM}
          aria-label={t('pages.gardenPlan.field.map.zoomOut')}
          sx={buttonSx}
          data-testid="field-map-zoom-out"
        >
          <ZoomOutIcon />
        </Button>
        <Button
          variant="outlined"
          color="inherit"
          onClick={() => changeView(null)}
          startIcon={<ZoomOutMapIcon />}
          sx={buttonSx}
          data-testid="field-map-fit"
        >
          {t('pages.gardenPlan.field.map.fit')}
        </Button>
      </Box>
      {viewport === null ? (
        <Box data-testid="field-map-empty" sx={{ p: 2, border: 2, borderColor: 'divider', borderRadius: 1 }}>
          {t('pages.gardenPlan.empty.title')}
        </Box>
      ) : (
        <Box
          ref={svgBoxRef}
          onClick={onTap}
          data-testid="field-map-canvas"
          sx={{
            width: viewport.widthPx + CANVAS_BORDER_PX,
            maxWidth: '100%',
            border: 2,
            borderColor: 'text.primary',
            borderRadius: 1,
            overflow: 'hidden',
          }}
        >
          {drawing}
        </Box>
      )}
    </Box>
  );
}
