/**
 * The header row of the plan editor (REQ-053 WP 2.5): grid step, grid and snap switches, zoom
 * with "fit to area", the length unit and the compass. A row of its own above the tool bar so
 * that the tool bar stays untouched (GP-FR-154: the grid step belongs in the header).
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
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

export interface ViewBarProps {
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
        sx={{ minWidth: 104 }}
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

      <Divider orientation="vertical" flexItem />

      <Box role="group" aria-label={t(`${PREFIX}.zoom.label`)} sx={{ display: 'flex', alignItems: 'center' }}>
        <Tooltip title={t(`${PREFIX}.zoom.outHint`)}>
          <span>
            <IconButton
              onClick={props.onZoomOut}
              disabled={atMin}
              aria-label={t(`${PREFIX}.zoom.out`)}
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
            data-testid="garden-plan-zoom-fit"
            sx={buttonSx}
          >
            {t(`${PREFIX}.zoom.fit`)}
          </Button>
        </Tooltip>
      </Box>

      <Divider orientation="vertical" flexItem />

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

      <Box sx={{ flexGrow: 1 }} />
      <Compass angleDeg={props.northAngleDeg} onChange={props.onNorthAngle} />
    </Paper>
  );
}
