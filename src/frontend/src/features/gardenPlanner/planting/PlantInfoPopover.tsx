/**
 * The plant info (REQ-053 GP-FR-190, GP-UX-058): the facts of one plant in at most eight lines - the content
 * shared by the hover bubble and the touch sheet - and the hoverable, dismissible bubble itself.
 *
 * The bubble renders from the already-loaded plant state; it never requests anything (GP-FR-191). It stays
 * until the pointer leaves marker **and** bubble, and closes on Esc (WCAG 1.4.13). The marker points at it with
 * `aria-describedby` (the same text a screen reader gets), the bubble never covers the marker, and a link opens
 * the plant detail page.
 */
import { useLayoutEffect, useRef, useState, type CSSProperties } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import { PLANT_INFO_ID } from '../renderer/plantMarkerStyle';
import { usePlantStateText } from './usePlantStateText';
import type { PlantStateView } from './usePlantStates';

/** Route of the plant detail page. */
export function plantDetailPath(plantKey: string): string {
  return `/pflanzen/plant-instances/${plantKey}`;
}

interface PlantInfoContentProps {
  view: PlantStateView;
}

/** Head (name, scientific name, cultivar, id) and the lines of the plant info; empty lines are left out. */
export function PlantInfoContent({ view }: PlantInfoContentProps) {
  const text = usePlantStateText();
  const lines = text.lines(view);
  const subtitle = [view.scientific_name, view.cultivar_name].filter(Boolean).join(' · ');
  return (
    <Box data-testid="plant-info-content" sx={{ overflowWrap: 'anywhere' }}>
      <Typography variant="subtitle2" component="p" sx={{ lineHeight: 1.3 }}>
        {text.name(view)}
        <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
          {view.instance_id}
        </Typography>
      </Typography>
      {subtitle ? (
        <Typography variant="caption" color="text.secondary" component="p" sx={{ fontStyle: 'italic' }}>
          {subtitle}
        </Typography>
      ) : null}
      <Box component="ul" sx={{ listStyle: 'none', m: 0, mt: 0.5, p: 0 }}>
        {lines.map((line) => (
          <Typography
            key={line.key}
            component="li"
            variant="body2"
            color={line.alert ? 'error.main' : 'text.primary'}
            sx={{ fontWeight: line.alert ? 600 : undefined }}
            data-line={line.key}
          >
            {line.text}
          </Typography>
        ))}
      </Box>
    </Box>
  );
}

const BUBBLE_WIDTH_PX = 280;
const GAP_PX = 10;
/** Distance the bubble keeps to the canvas edge on a narrow screen. */
const GUTTER_PX = 16;

interface PlantInfoPopoverProps {
  view: PlantStateView;
  /** The canvas the marker is drawn in; the bubble is positioned inside it. */
  container: HTMLElement | null;
  onPointerEnter: () => void;
  onPointerLeave: () => void;
}

/** Where the bubble goes: beside the marker (right, else left), inside the canvas, never on the marker. */
function place(marker: DOMRect, box: DOMRect, bubbleHeight: number): CSSProperties {
  // On a canvas narrower than bubble + gutters the bubble shrinks instead of running out of the canvas.
  const width = Math.max(0, Math.min(BUBBLE_WIDTH_PX, box.width - 2 * GUTTER_PX));
  const gutter = width < BUBBLE_WIDTH_PX ? GUTTER_PX : 0;
  const markerLeft = marker.left - box.left;
  const markerRight = marker.right - box.left;
  const markerTop = marker.top - box.top;
  const fitsRight = markerRight + GAP_PX + width <= box.width - gutter;
  const left = fitsRight
    ? markerRight + GAP_PX
    : Math.max(gutter, Math.min(box.width - width - gutter, markerLeft - GAP_PX - width));
  const top = Math.max(0, Math.min(Math.max(0, box.height - bubbleHeight), markerTop - 12));
  return { left, top, width };
}

export default function PlantInfoPopover({ view, container, onPointerEnter, onPointerLeave }: PlantInfoPopoverProps) {
  const { t } = useTranslation();
  const text = usePlantStateText();
  const bubble = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState<CSSProperties>({ visibility: 'hidden' });

  useLayoutEffect(() => {
    if (!container || !bubble.current) return;
    const marker = container.querySelector<SVGGraphicsElement>(`[data-plan-key="${CSS.escape(view.plant_key)}"]`);
    if (!marker) return;
    setPosition(place(marker.getBoundingClientRect(), container.getBoundingClientRect(), bubble.current.offsetHeight));
  }, [container, view]);

  return (
    <Paper
      ref={bubble}
      id={PLANT_INFO_ID}
      role="group"
      aria-label={t('pages.gardenPlan.plantState.info.label', { name: text.name(view) })}
      elevation={4}
      onPointerEnter={onPointerEnter}
      onPointerLeave={onPointerLeave}
      data-testid="plant-info-popover"
      sx={{ position: 'absolute', zIndex: 2, width: BUBBLE_WIDTH_PX, maxWidth: '100%', p: 1.25 }}
      style={position}
    >
      <PlantInfoContent view={view} />
      <Link
        component={RouterLink}
        to={plantDetailPath(view.plant_key)}
        variant="body2"
        sx={{ display: 'inline-block', mt: 0.5, py: 0.5 }}
        data-testid="plant-info-details"
      >
        {t('pages.gardenPlan.plantState.info.details')}
      </Link>
    </Paper>
  );
}
