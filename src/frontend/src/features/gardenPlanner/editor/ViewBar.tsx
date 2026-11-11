/**
 * The view settings of the plan editor (REQ-053 WP 2.5, GP-FR-154): grid step, the grid and snap switches, the
 * length unit and the compass with the north angle. Since wave 10 they are the content of the side panel's tab
 * "Ansicht" (§17.3, GP-UX-068, WP 10.5), also in the bottom sheet below md (GP-UX-052: grid step and snap in the
 * tab "Ansicht"). Zoom and "fit to area" are an overlay on the canvas (`ZoomOverlay`, GP-UX-067); the layer switches
 * are in the tab "Ebenen" (`LayersTab`). The test id `garden-plan-view-bar` stays on the group (GP-UX-070).
 */
import { useId } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import FilterCenterFocusIcon from '@mui/icons-material/FilterCenterFocus';
import GridOnIcon from '@mui/icons-material/GridOn';
import StraightenIcon from '@mui/icons-material/Straighten';
import { GRID_STEPS_M, gridStepLabel, type LengthUnit } from '../model/units';
import { Compass } from './Compass';

const PREFIX = 'pages.gardenPlan.editor';
const TARGET_PX = 48;

export interface ViewBarProps {
  gridStepM: number;
  onGridStep: (stepM: number) => void;
  gridVisible: boolean;
  onGridVisible: (visible: boolean) => void;
  snapEnabled: boolean;
  onSnapEnabled: (enabled: boolean) => void;
  unit: LengthUnit;
  onUnit: (unit: LengthUnit) => void;
  northAngleDeg: number;
  /** Absent while the plan has no outline to carry the angle. */
  onNorthAngle?: (angleDeg: number) => void;
}

const switchSx = { minHeight: TARGET_PX, gap: 1, justifyContent: 'flex-start', textTransform: 'none' } as const;

export function ViewBar(props: ViewBarProps) {
  const { t, i18n } = useTranslation();
  const unitLabelId = useId();
  return (
    <Stack
      role="group"
      aria-label={t(`${PREFIX}.view.label`)}
      data-testid="garden-plan-view-bar"
      spacing={2}
      sx={{ minWidth: 0 }}
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
        sx={{ '& select': { minHeight: TARGET_PX, boxSizing: 'border-box', display: 'flex', alignItems: 'center' } }}
      >
        {GRID_STEPS_M.map((step) => (
          <option key={step} value={String(step)}>
            {gridStepLabel(step, i18n.language)}
          </option>
        ))}
      </TextField>
      {/*
        Grid and snap carry their name as visible text: there is room for it in the panel (label in name). The tooltip
        describes them (`describeChild`); as a name it would replace the visible text (WCAG 2.5.3).
      */}
      <ToggleButtonGroup orientation="vertical" size="small" aria-label={t(`${PREFIX}.grid.toggles`)} fullWidth>
        <Tooltip title={t(`${PREFIX}.grid.toggleHint`)} placement="left" describeChild>
          <ToggleButton
            value="grid"
            selected={props.gridVisible}
            onChange={() => props.onGridVisible(!props.gridVisible)}
            aria-keyshortcuts="G"
            data-testid="garden-plan-grid-toggle"
            sx={switchSx}
          >
            <GridOnIcon fontSize="small" />
            {t(`${PREFIX}.grid.toggle`)}
          </ToggleButton>
        </Tooltip>
        <Tooltip title={t(`${PREFIX}.snap.hint`)} placement="left" describeChild>
          <ToggleButton
            value="snap"
            selected={props.snapEnabled}
            onChange={() => props.onSnapEnabled(!props.snapEnabled)}
            data-testid="garden-plan-snap-toggle"
            sx={switchSx}
          >
            <FilterCenterFocusIcon fontSize="small" />
            {t(`${PREFIX}.snap.toggle`)}
          </ToggleButton>
        </Tooltip>
      </ToggleButtonGroup>

      <Box>
        <Typography variant="body2" color="text.secondary" component="p" id={unitLabelId} sx={{ mb: 0.5 }}>
          {t(`${PREFIX}.grid.unit`)}
        </Typography>
        <ToggleButtonGroup
          exclusive
          size="small"
          value={props.unit}
          aria-labelledby={unitLabelId}
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
              sx={{ minWidth: TARGET_PX, minHeight: TARGET_PX, px: 1.25 }}
            >
              {unit === 'm' ? <StraightenIcon fontSize="small" sx={{ mr: 0.5 }} /> : null}
              {unit}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
      </Box>

      <Compass angleDeg={props.northAngleDeg} onChange={props.onNorthAngle} />
    </Stack>
  );
}
