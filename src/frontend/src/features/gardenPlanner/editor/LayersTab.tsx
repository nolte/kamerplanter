/**
 * The side panel's tab "Ebenen" (REQ-053 §17.3, GP-UX-068, AC-6, WP 10.5): the layer switches of the registry
 * (`layers.ts`) with a visible text label each, the filter "only plants that need attention" (GP-UX-061), and the
 * legend (GP-UX-005: object classes and phase colours, together with the zone legend), which can be hidden here.
 *
 * The switches keep their test ids `garden-plan-layer-<id>` and their `aria-pressed` state (GP-UX-070); before wave
 * 10 they were icon buttons in the view row above the canvas.
 */
import { useId, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import FormControlLabel from '@mui/material/FormControlLabel';
import Stack from '@mui/material/Stack';
import Switch from '@mui/material/Switch';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Tooltip from '@mui/material/Tooltip';
import type { Theme } from '@mui/material/styles';
import { visuallyHidden } from '@mui/utils';

const PREFIX = 'pages.gardenPlan.editor';
const TARGET_PX = 48;

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

/** A layer switch of the registry (`layers.ts`) other than the grid (the grid is in the tab "Ansicht"). */
export interface LayerToggle {
  id: string;
  label: string;
  hint: string;
  icon: ReactNode;
  visible: boolean;
}

interface LayersTabProps {
  layerToggles: readonly LayerToggle[];
  onLayer: (id: string, visible: boolean) => void;
  /** Shown under the layer switches when the plan has a plant-state layer. */
  attentionFilter?: AttentionFilterToggle;
  /** The legend of the layers that are on (`ZoneLegend`); it renders nothing while no layer with a legend is on. */
  legend: ReactNode;
}

const switchSx = {
  minHeight: TARGET_PX,
  gap: 1,
  justifyContent: 'flex-start',
  textAlign: 'start',
  textTransform: 'none',
} as const;
/** The look of a disabled button on one that stays focusable (`aria-disabled`). */
const disabledLookSx = (theme: Theme) => ({
  color: theme.palette.action.disabled,
  cursor: 'not-allowed',
});

export function LayersTab({ layerToggles, onLayer, attentionFilter, legend }: LayersTabProps) {
  const { t } = useTranslation();
  const attentionHintId = useId();
  // Shown by default: the legend explains what the switched-on layers draw (GP-UX-005, hideable here).
  const [legendShown, setLegendShown] = useState(true);
  return (
    <Stack spacing={2} sx={{ minWidth: 0 }}>
      {layerToggles.length > 0 && (
        <ToggleButtonGroup
          orientation="vertical"
          size="small"
          fullWidth
          aria-label={t(`${PREFIX}.zones.layers.group`)}
          data-testid="garden-plan-layer-toggles"
        >
          {layerToggles.map((layer) => (
            <Tooltip key={layer.id} title={layer.hint} placement="left" describeChild>
              <ToggleButton
                value={layer.id}
                selected={layer.visible}
                onChange={() => onLayer(layer.id, !layer.visible)}
                // The visible text, also as the name: the tooltip describes the switch, it never names it.
                aria-label={layer.label}
                data-testid={`garden-plan-layer-${layer.id}`}
                sx={switchSx}
              >
                {layer.icon}
                {layer.label}
              </ToggleButton>
            </Tooltip>
          ))}
        </ToggleButtonGroup>
      )}
      {attentionFilter && (
        <Box>
          <Tooltip title={attentionFilter.hint} placement="left">
            {/*
              Disabled by `aria-disabled`, not `disabled`: the button stays in the tab order, so a keyboard or screen
              reader user reaches it and hears why it is disabled (the hidden text below); a click does nothing.
            */}
            <ToggleButton
              size="small"
              fullWidth
              value="attentionOnly"
              selected={attentionFilter.active && attentionFilter.enabled}
              aria-disabled={attentionFilter.enabled ? undefined : true}
              onChange={() => {
                if (attentionFilter.enabled) attentionFilter.onChange(!attentionFilter.active);
              }}
              // The name is the visible text; set here so the tooltip does not name the button with its hint.
              aria-label={attentionFilter.label}
              aria-describedby={attentionHintId}
              data-testid="garden-plan-attention-filter"
              sx={attentionFilter.enabled ? switchSx : [switchSx, disabledLookSx]}
            >
              {attentionFilter.icon}
              {attentionFilter.label}
            </ToggleButton>
          </Tooltip>
          <Box component="span" id={attentionHintId} sx={visuallyHidden}>
            {attentionFilter.hint}
          </Box>
        </Box>
      )}
      <FormControlLabel
        control={
          <Switch
            checked={legendShown}
            onChange={(_event, checked) => setLegendShown(checked)}
            slotProps={{
              input: { 'data-testid': 'garden-plan-legend-toggle' } as Record<string, string>,
            }}
          />
        }
        label={t(`${PREFIX}.sidePanel.legendShown`)}
        sx={{ minHeight: TARGET_PX, mx: 0 }}
      />
      {legendShown && legend}
    </Stack>
  );
}
