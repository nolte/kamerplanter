/**
 * The header row of the plan editor (REQ-053 WP 2.5): grid step, grid and snap switches, zoom
 * with "fit to area", the length unit and the compass. A row of its own above the tool bar so
 * that the tool bar stays untouched (GP-FR-154: the grid step belongs in the header).
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import type { ReactNode } from 'react';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Tooltip from '@mui/material/Tooltip';
import AddIcon from '@mui/icons-material/Add';
import FitScreenIcon from '@mui/icons-material/FitScreen';
import GridOnIcon from '@mui/icons-material/GridOn';
import RemoveIcon from '@mui/icons-material/Remove';
import StraightenIcon from '@mui/icons-material/Straighten';
import {
  GRID_STEPS_M,
  gridStepLabel,
  pxPerMToPercent,
  type LengthUnit,
} from '../model/units';
import { Compass } from './Compass';

const PREFIX = 'pages.gardenPlan.editor';
const TARGET_PX = 44;

/**
 * The filter "only plants that need attention" (GP-UX-061): depends on the plant-state layer and is disabled while
 * that layer is off, so it never claims to filter something that is not drawn.
 */
export interface AttentionFilterToggle {
  active: boolean;
  /** The plant-state layer is on. */
  enabled: boolean;
  label: string;
  /** Tooltip while usable, and the reason while disabled. */
  hint: string;
  icon: ReactNode;
  onChange: (active: boolean) => void;
}

/** A layer switch of the registry (`layers.ts`) other than the grid: icon only, so its name is the aria-label. */
export interface LayerToggle {
  id: string;
  label: string;
  hint: string;
  icon: ReactNode;
  visible: boolean;
}

export interface ViewBarProps {
  /** The registry layers with a toggle of their own (zones, last watered, later more). */
  layerToggles?: readonly LayerToggle[];
  onLayer?: (id: string, visible: boolean) => void;
  /** Shown next to the layer toggles when the plan has a plant-state layer. */
  attentionFilter?: AttentionFilterToggle;
  gridStepM: number;
  onGridStep: (stepM: number) => void;
  gridVisible: boolean;
  onGridVisible: (visible: boolean) => void;
  snapEnabled: boolean;
  onSnapEnabled: (enabled: boolean) => void;
  pxPerM: number;
  minPxPerM: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFit: () => void;
  unit: LengthUnit;
  onUnit: (unit: LengthUnit) => void;
  northAngleDeg: number;
  /** Absent while the plan has no outline to carry the angle. */
  onNorthAngle?: (angleDeg: number) => void;
}

// A divider between wrapped rows would dangle at the line end on a phone: only where all fits.
const dividerSx = { display: { xs: 'none', md: 'block' } } as const;

const buttonSx = { minWidth: TARGET_PX, minHeight: TARGET_PX } as const;

export function ViewBar(props: ViewBarProps) {
  const { t, i18n } = useTranslation();
  const percent = pxPerMToPercent(props.pxPerM);
  const atMin = props.pxPerM <= props.minPxPerM + 1e-6;
  return (
    <Paper
      variant="outlined"
      role="group"
      aria-label={t(`${PREFIX}.view.label`)}
      data-testid="garden-plan-view-bar"
      sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 0.5, flexWrap: 'wrap' }}
    >
      <TextField
        select
        size="small"
        label={t(`${PREFIX}.grid.step`)}
        value={String(props.gridStepM)}
        onChange={(event) => props.onGridStep(Number(event.target.value))}
        slotProps={{
          select: { native: true },
          htmlInput: { 'data-testid': 'garden-plan-grid-step' },
        }}
        sx={{ minWidth: 104, '& select': { minHeight: TARGET_PX, boxSizing: 'border-box', display: 'flex', alignItems: 'center' } }}
      >
        {GRID_STEPS_M.map((step) => (
          <option key={step} value={String(step)}>
            {gridStepLabel(step, i18n.language)}
          </option>
        ))}
      </TextField>
      <ToggleButtonGroup size="small" aria-label={t(`${PREFIX}.grid.toggles`)}>
        <Tooltip title={t(`${PREFIX}.grid.toggleHint`)}>
          <ToggleButton
            value="grid"
            selected={props.gridVisible}
            onChange={() => props.onGridVisible(!props.gridVisible)}
            aria-label={t(`${PREFIX}.grid.toggle`)}
            aria-keyshortcuts="G"
            data-testid="garden-plan-grid-toggle"
            sx={buttonSx}
          >
            <GridOnIcon />
          </ToggleButton>
        </Tooltip>
        <Tooltip title={t(`${PREFIX}.snap.hint`)}>
          <ToggleButton
            value="snap"
            selected={props.snapEnabled}
            onChange={() => props.onSnapEnabled(!props.snapEnabled)}
            aria-label={t(`${PREFIX}.snap.toggle`)}
            data-testid="garden-plan-snap-toggle"
            sx={{ ...buttonSx, px: 1.5 }}
          >
            {t(`${PREFIX}.snap.short`)}
          </ToggleButton>
        </Tooltip>
      </ToggleButtonGroup>

      {props.layerToggles && props.layerToggles.length > 0 && (
        <Divider orientation="vertical" flexItem sx={dividerSx} />
      )}
      {props.layerToggles && props.layerToggles.length > 0 && (
        <ToggleButtonGroup size="small" aria-label={t(`${PREFIX}.zones.layers.group`)} data-testid="garden-plan-layer-toggles">
          {props.layerToggles.map((layer) => (
            <Tooltip key={layer.id} title={layer.hint}>
              <ToggleButton
                value={layer.id}
                selected={layer.visible}
                onChange={() => props.onLayer?.(layer.id, !layer.visible)}
                aria-label={layer.label}
                data-testid={`garden-plan-layer-${layer.id}`}
                sx={buttonSx}
              >
                {layer.icon}
              </ToggleButton>
            </Tooltip>
          ))}
        </ToggleButtonGroup>
      )}
      {props.attentionFilter && (
        <Tooltip title={props.attentionFilter.hint}>
          {/* A disabled button fires no events: the span keeps the tooltip that says why it is disabled. */}
          <span>
            <ToggleButton
              size="small"
              value="attentionOnly"
              selected={props.attentionFilter.active && props.attentionFilter.enabled}
              disabled={!props.attentionFilter.enabled}
              onChange={() => props.attentionFilter?.onChange(!props.attentionFilter.active)}
              aria-label={props.attentionFilter.label}
              data-testid="garden-plan-attention-filter"
              sx={buttonSx}
            >
              {props.attentionFilter.icon}
            </ToggleButton>
          </span>
        </Tooltip>
      )}

      <Divider orientation="vertical" flexItem sx={dividerSx} />

      <Box role="group" aria-label={t(`${PREFIX}.zoom.label`)} sx={{ display: 'flex', alignItems: 'center' }}>
        <Tooltip title={t(`${PREFIX}.zoom.outHint`)}>
          <span>
            <IconButton
              onClick={props.onZoomOut}
              disabled={atMin}
              aria-label={t(`${PREFIX}.zoom.out`)}
              aria-keyshortcuts="-"
              data-testid="garden-plan-zoom-out"
              sx={buttonSx}
            >
              <RemoveIcon />
            </IconButton>
          </span>
        </Tooltip>
        <Box
          component="span"
          role="status"
          aria-label={t(`${PREFIX}.zoom.level`, { percent })}
          data-testid="garden-plan-zoom-level"
          sx={{ minWidth: 52, textAlign: 'center', typography: 'body2' }}
        >
          {percent} %
        </Box>
        <Tooltip title={t(`${PREFIX}.zoom.inHint`)}>
          <IconButton
            onClick={props.onZoomIn}
            aria-label={t(`${PREFIX}.zoom.in`)}
            aria-keyshortcuts="+"
            data-testid="garden-plan-zoom-in"
            sx={buttonSx}
          >
            <AddIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title={t(`${PREFIX}.zoom.fitHint`)}>
          <Button
            onClick={props.onFit}
            startIcon={<FitScreenIcon />}
            aria-keyshortcuts="0"
            data-testid="garden-plan-zoom-fit"
            sx={buttonSx}
          >
            {t(`${PREFIX}.zoom.fit`)}
          </Button>
        </Tooltip>
      </Box>

      <Divider orientation="vertical" flexItem sx={dividerSx} />

      <ToggleButtonGroup
        exclusive
        size="small"
        value={props.unit}
        aria-label={t(`${PREFIX}.grid.unit`)}
        onChange={(_event, next: LengthUnit | null) => {
          if (next) props.onUnit(next);
        }}
      >
        {(['m', 'cm'] as const).map((unit) => (
          <ToggleButton
            key={unit}
            value={unit}
            aria-label={t(`${PREFIX}.grid.unitOption.${unit}`)}
            data-testid={`garden-plan-unit-${unit}`}
            sx={{ ...buttonSx, px: 1.25 }}
          >
            {unit === 'm' ? <StraightenIcon fontSize="small" sx={{ mr: 0.5 }} /> : null}
            {unit}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>

      <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'block' } }} />
      <Compass angleDeg={props.northAngleDeg} onChange={props.onNorthAngle} />
    </Paper>
  );
}
