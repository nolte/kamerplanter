/**
 * The plant-state part of the plan's layer legend (REQ-053 GP-UX-005, GP-UX-061, #2488): the rings and badges the
 * markers draw, and the colour of every growth phase present on the plan. Its own chunk (UI-NFR-003): the plan route
 * carries only the section frame until the layer is switched on.
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { phaseColor } from '../planting/phaseColors';
import { PlantStateLegendItems } from '../planting/PlantStateLegendItems';

const PREFIX = 'pages.gardenPlan.editor.zones.legend';
const SWATCH_PX = 16;

interface Props {
  /** Names of the growth phases present on the plan (as the phase definitions name them). */
  phases: readonly string[];
}

/** `enums.phaseName.<name>` for a known phase name ("Flowering" and "flowering" alike), else the stored name. */
function phaseKeyOf(name: string): string {
  return name.trim().toLowerCase().replace(/[\s-]+/g, '_');
}

export default function PlantStateLegendSection({ phases }: Props) {
  const { t } = useTranslation();
  return (
    <>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1, maxWidth: 360 }}>
        {t(`${PREFIX}.plantStateIntro`)}
      </Typography>
      <PlantStateLegendItems />
      <Typography variant="body2" sx={{ mt: 1.5, mb: 0.75, fontWeight: 600 }}>
        {t(`${PREFIX}.phasesTitle`)}
      </Typography>
      {phases.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          {t(`${PREFIX}.phasesNone`)}
        </Typography>
      ) : (
        <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0, display: 'grid', gap: 0.75 }}>
          {phases.map((name) => (
            <Box
              component="li"
              key={name}
              data-legend-phase={name}
              sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}
            >
              <svg width={32} height={SWATCH_PX + 4} aria-hidden="true" focusable="false">
                <circle cx={16} cy={(SWATCH_PX + 4) / 2} r={SWATCH_PX / 2} fill={phaseColor(name)} stroke="currentColor" />
              </svg>
              <Typography variant="body2">
                {t(`enums.phaseName.${phaseKeyOf(name)}`, { defaultValue: name })}
              </Typography>
            </Box>
          ))}
        </Box>
      )}
    </>
  );
}
