/**
 * Zoom −/%/+ and "fit to area" as an overlay in the top right corner of the canvas (REQ-053 §17.3, GP-UX-067,
 * GP-FR-009/150): no row of their own above the plan. The overlay is a sibling of the canvas region inside the
 * canvas area, not a child of it, so a press on a button never reaches the canvas gestures and the canvas keys.
 * Targets are 48 px like the rail and the header; the test ids are the ones the zoom had in the view row (GP-UX-070).
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import Tooltip from '@mui/material/Tooltip';
import AddIcon from '@mui/icons-material/Add';
import FitScreenIcon from '@mui/icons-material/FitScreen';
import RemoveIcon from '@mui/icons-material/Remove';
import { pxPerMToPercent } from '../model/units';
import { unavailableProps } from './unavailable';

const PREFIX = 'pages.gardenPlan.editor';
const TARGET_PX = 48;
const buttonSx = { minWidth: TARGET_PX, minHeight: TARGET_PX } as const;

export interface ZoomOverlayProps {
  pxPerM: number;
  /** The fit zoom: zooming out stops there (GP-FR-150). */
  minPxPerM: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFit: () => void;
}

export function ZoomOverlay({ pxPerM, minPxPerM, onZoomIn, onZoomOut, onFit }: ZoomOverlayProps) {
  const { t } = useTranslation();
  const percent = pxPerMToPercent(pxPerM);
  const atMin = pxPerM <= minPxPerM + 1e-6;
  return (
    <Paper
      elevation={2}
      role="group"
      aria-label={t(`${PREFIX}.zoom.label`)}
      data-testid="garden-plan-zoom-overlay"
      sx={{
        position: 'absolute',
        top: 8,
        right: 8,
        zIndex: 1,
        display: 'flex',
        alignItems: 'center',
        flexWrap: 'nowrap',
        // A soft backing like the scale bar: readable over beds and the grid.
        bgcolor: 'background.paper',
        opacity: 0.95,
      }}
    >
      <Tooltip title={t(`${PREFIX}.zoom.outHint`)}>
        <span>
          <IconButton
            // At the fit zoom it does nothing but keeps the focus (GP-NFR-070); "-" stops there as well.
            onClick={atMin ? undefined : onZoomOut}
            {...unavailableProps(atMin)}
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
        sx={{ minWidth: 52, textAlign: 'center', typography: 'body2', whiteSpace: 'nowrap' }}
      >
        {percent} %
      </Box>
      <Tooltip title={t(`${PREFIX}.zoom.inHint`)}>
        <IconButton
          onClick={onZoomIn}
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
          onClick={onFit}
          startIcon={<FitScreenIcon />}
          aria-keyshortcuts="0"
          data-testid="garden-plan-zoom-fit"
          sx={{ ...buttonSx, whiteSpace: 'nowrap' }}
        >
          {t(`${PREFIX}.zoom.fit`)}
        </Button>
      </Tooltip>
    </Paper>
  );
}
