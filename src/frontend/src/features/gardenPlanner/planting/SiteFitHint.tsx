/**
 * The site-fit traffic light of one species against the bed (REQ-053 GP-FR-160, E-05, TC-053-037):
 * "Beet: Schatten — Tomate braucht Vollsonne". It names the verdict in words as well as colour, never
 * blocks (like the rotation hints, D-09) and is absent when either side is unknown - an unknown gives
 * no hint, not a green one.
 */
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Typography from '@mui/material/Typography';
import type { LightRequirement, SiteFitResult } from '../model/siteFit';
import type { SunExposure } from '../model/types';

const SEVERITY = { ok: 'success', marginal: 'warning', poor: 'error' } as const;

interface SiteFitHintProps {
  speciesKey: string;
  speciesName: string;
  bedSun: SunExposure;
  lightRequirement: LightRequirement;
  shadeTolerance: string | null;
  result: SiteFitResult;
}

export default function SiteFitHint({
  speciesKey,
  speciesName,
  bedSun,
  lightRequirement,
  shadeTolerance,
  result,
}: SiteFitHintProps) {
  const { t } = useTranslation();
  if (result.fit === 'unknown') return null;
  const fit = t(`pages.bed.planting.siteFit.fit.${result.fit}`);
  return (
    <Alert severity={SEVERITY[result.fit]} data-testid={`planting-site-fit-${speciesKey}`}>
      <Typography variant="subtitle2" component="div">
        {t('pages.bed.planting.siteFit.summary', { name: speciesName, fit })}
      </Typography>
      <Typography variant="body2" component="div">
        {t('pages.bed.planting.siteFit.line', {
          bed: t(`enums.sunExposure.${bedSun}`),
          name: speciesName,
          need: t(`pages.bed.planting.siteFit.needs.${lightRequirement}`),
        })}{' '}
        {t(`pages.bed.planting.siteFit.reason.${result.reason}`, {
          tolerance: shadeTolerance ? t(`enums.sunExposure.${shadeTolerance}`) : '',
        })}
      </Typography>
    </Alert>
  );
}
