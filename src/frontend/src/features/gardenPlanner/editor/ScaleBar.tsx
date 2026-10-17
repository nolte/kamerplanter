/**
 * The scale bar (REQ-053 GP-FR-009): always visible, 1 m / 5 m / 10 m (and neighbours) depending
 * on the zoom. Sits in the lower left corner of the canvas and takes no pointer events.
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import { scaleBarLabel, scaleBarLengthM } from '../model/units';

interface ScaleBarProps {
  pxPerM: number;
}

export function ScaleBar({ pxPerM }: ScaleBarProps) {
  const { t, i18n } = useTranslation();
  const lengthM = scaleBarLengthM(pxPerM);
  const label = scaleBarLabel(lengthM, i18n.language);
  return (
    <Box
      role="img"
      aria-label={t('pages.gardenPlan.editor.zoom.scaleBar', { length: label })}
      data-testid="garden-plan-scale-bar"
      data-length-m={lengthM}
      sx={{
        position: 'absolute',
        left: 8,
        bottom: 8,
        pointerEvents: 'none',
        color: 'text.primary',
        typography: 'caption',
        // A soft backing keeps the bar readable over beds and the grid.
        bgcolor: 'background.paper',
        opacity: 0.92,
        fontWeight: 600,
        px: 0.75,
        py: 0.25,
        border: 1,
        borderColor: 'divider',
        borderRadius: 0.5,
      }}
    >
      <Box
        aria-hidden="true"
        sx={{
          width: lengthM * pxPerM,
          height: 8,
          borderStyle: 'solid',
          borderColor: 'text.primary',
          borderWidth: '0 2px 2px 2px',
        }}
      />
      <Box aria-hidden="true" component="span">
        {label}
      </Box>
    </Box>
  );
}
