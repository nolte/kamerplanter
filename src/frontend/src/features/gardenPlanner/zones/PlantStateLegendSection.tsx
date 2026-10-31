/**
 * The plant-state part of the plan's layer legend (REQ-053 GP-UX-005, GP-UX-061, #2488): the rings and badges the
 * markers draw, and the colour of every growth phase present on the plan. Its own chunk (UI-NFR-003): the plan route
 * carries only the section frame until the layer is switched on.
 */
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { phaseColor } from '../planting/phaseColors';
import { PlantStateLegendItems } from '../planting/PlantStateLegendItems';

const PREFIX = 'pages.gardenPlan.editor.zones.legend';
const SWATCH_PX = 16;

interface Props {
  /** Names of the growth phases present on the plan (as the phase definitions name them), in any order. */
  phases: readonly string[];
}

/** `enums.phaseName.<name>` for a known phase name ("Flowering" and "flowering" alike), else the stored name. */
function phaseKeyOf(name: string): string {
  return name.trim().toLowerCase().replace(/[\s-]+/g, '_');
}

export default function PlantStateLegendSection({ phases }: Props) {
  const { t, i18n } = useTranslation();
  // Sorted by what the reader sees, in the active language ("Blüte" before "Keimung", "Flowering" before "Germination").
  const entries = useMemo(() => {
    const collator = new Intl.Collator(i18n.resolvedLanguage ?? i18n.language);
    return [...new Set(phases)]
      .map((name) => ({ name, label: t(`enums.phaseName.${phaseKeyOf(name)}`, { defaultValue: name }) }))
      .sort((a, b) => collator.compare(a.label, b.label));
  }, [phases, t, i18n.resolvedLanguage, i18n.language]);
  return (
    <>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1, maxWidth: 360 }}>
        {t(`${PREFIX}.plantStateIntro`)}
      </Typography>
      <PlantStateLegendItems />
      <Typography variant="body2" sx={{ mt: 1.5, mb: 0.75, fontWeight: 600 }}>
        {t(`${PREFIX}.phasesTitle`)}
      </Typography>
      {entries.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          {t(`${PREFIX}.phasesNone`)}
        </Typography>
      ) : (
        <Box component="ul" sx={{ listStyle: 'none', m: 0, p: 0, display: 'grid', gap: 0.75 }}>
          {entries.map(({ name, label }) => (
            <Box
              component="li"
              key={name}
              data-legend-phase={name}
              sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}
            >
              <svg width={32} height={SWATCH_PX + 4} aria-hidden="true" focusable="false">
                <circle cx={16} cy={(SWATCH_PX + 4) / 2} r={SWATCH_PX / 2} fill={phaseColor(name)} stroke="currentColor" />
              </svg>
              <Typography variant="body2">{label}</Typography>
            </Box>
          ))}
        </Box>
      )}
    </>
  );
}
