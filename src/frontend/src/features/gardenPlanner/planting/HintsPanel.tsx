/**
 * Crop-rotation and companion hints with a strength (REQ-053 GP-FR-132, D-09): shown in the planting
 * dialog before the layout is chosen, never as a blocker. From a warning on, the grower plants anyway
 * only with a reason ("Trotzdem pflanzen"), which the run stores as `rotation_override_reason`.
 */
import { Fragment } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Checkbox from '@mui/material/Checkbox';
import CircularProgress from '@mui/material/CircularProgress';
import FormControlLabel from '@mui/material/FormControlLabel';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import type { HintState, MixPair } from './useBedHints';
import SiteFitHint from './SiteFitHint';
import type { SpeciesSiteFit } from './siteFitOf';
import type { SunExposure } from '../model/types';
import { needsOverrideReason } from './plantingLogic';
import type { NeighbourHint, RotationFinding, RotationSeverity } from './plantingTypes';

const ALERT_SEVERITY: Record<RotationSeverity, 'success' | 'info' | 'warning' | 'error'> = {
  OK: 'success',
  INFO: 'info',
  WARNING: 'warning',
  CRITICAL: 'error',
};

export const MAX_OVERRIDE_REASON = 500;

interface HintsPanelProps {
  /** Entries in the dialog's order: the species, its display name and the state of its request. */
  species: readonly {
    key: string;
    name: string;
    state: HintState | undefined;
    /** The site-fit hint of the species on this bed; `null` = nothing to say (GP-FR-160). */
    siteFit?: SpeciesSiteFit | null;
  }[];
  /** The sun class of the bed, named in the site-fit line. */
  bedSun?: SunExposure;
  /** Names of species by key, for the neighbours the server names. */
  speciesNames: ReadonlyMap<string, string>;
  mix: readonly MixPair[];
  /** The strongest rotation/companion severity of all chosen species needs a reason. */
  overrideChecked: boolean;
  overrideReason: string;
  showReasonError: boolean;
  onOverrideChecked: (checked: boolean) => void;
  onOverrideReason: (reason: string) => void;
  /** Worst severity over all species; decides whether the "plant anyway" step is needed. */
  severity: RotationSeverity;
}

function findingText(
  finding: RotationFinding,
  t: (key: string, options?: Record<string, unknown>) => string,
): string {
  switch (finding.code) {
    case 'rotation.pause_not_elapsed':
      return t('pages.bed.planting.hints.pauseNotElapsed', {
        family: finding.family_key ?? '',
        years: finding.years_since ?? 0,
        pause: finding.pause_years ?? 0,
        source: t(`pages.bed.planting.hints.pauseSource.${finding.pause_source ?? 'default'}`),
      });
    case 'rotation.pest_risk':
      return t('pages.bed.planting.hints.pestRisk', { family: finding.family_key ?? '' });
    case 'rotation.no_family':
      return t('pages.bed.planting.hints.noFamily');
    case 'rotation.no_history':
      return t('pages.bed.planting.hints.noHistory');
    default:
      return finding.message;
  }
}

function neighbourText(
  hint: NeighbourHint,
  names: ReadonlyMap<string, string>,
  t: (key: string, options?: Record<string, unknown>) => string,
): string {
  const name = names.get(hint.species_key) ?? hint.species_key;
  if (hint.code === 'companion.incompatible') {
    return t('pages.bed.planting.hints.incompatibleNeighbour', { name });
  }
  if (hint.code === 'companion.compatible') {
    return t('pages.bed.planting.hints.compatibleNeighbour', { name });
  }
  return hint.message;
}

export default function HintsPanel({
  species,
  speciesNames,
  bedSun = 'unknown',
  mix,
  overrideChecked,
  overrideReason,
  showReasonError,
  onOverrideChecked,
  onOverrideReason,
  severity,
}: HintsPanelProps) {
  const { t } = useTranslation();
  const mustGiveReason = needsOverrideReason(severity);
  const nameOf = (key: string) => speciesNames.get(key) ?? key;

  /** The rotation and neighbour hints of one species, or the reason there are none. */
  const rotationBlock = (key: string, name: string, state: HintState | undefined) => {
    if (!state || state.status === 'loading') {
      return (
        <Box key={key} sx={{ display: 'flex', alignItems: 'center', gap: 1 }} role="status">
          <CircularProgress size={16} />
          <Typography variant="body2">{t('pages.bed.planting.hints.checking', { name })}</Typography>
        </Box>
      );
    }
    if (state.status === 'error') {
      return (
        <Alert key={key} severity="info" data-testid={`planting-hint-${key}`}>
          {t('pages.bed.planting.hints.unavailable', { name, message: state.message })}
        </Alert>
      );
    }
    const { data } = state;
    if (!data.rotation_applicable) {
      return (
        <Alert key={key} severity="info" data-testid={`planting-hint-${key}`}>
          {t('pages.bed.planting.hints.notApplicable', { name })}
        </Alert>
      );
    }
    const lines = [
      ...data.rotation.map((finding) => ({
        id: `${finding.code}-${finding.family_key ?? ''}`,
        severity: finding.severity,
        text: findingText(finding, t),
      })),
      ...data.neighbours.map((hint) => ({
        id: `${hint.code}-${hint.species_key}`,
        severity: hint.severity,
        text: neighbourText(hint, speciesNames, t),
      })),
    ];
    if (lines.length === 0) {
      return (
        <Alert key={key} severity="success" data-testid={`planting-hint-${key}`}>
          {t('pages.bed.planting.hints.allClear', { name })}
        </Alert>
      );
    }
    return (
      <Alert key={key} severity={ALERT_SEVERITY[data.severity]} data-testid={`planting-hint-${key}`}>
        <Typography variant="subtitle2" component="div">
          {t('pages.bed.planting.hints.forSpecies', {
            name,
            strength: t(`enums.rotationSeverity.${data.severity}`),
          })}
        </Typography>
        <Box component="ul" sx={{ m: 0, pl: 2 }}>
          {lines.map((line) => (
            <li key={line.id}>
              {line.text}
              {line.severity !== data.severity ? (
                <Typography component="span" variant="caption" color="text.secondary">
                  {' '}
                  ({t(`enums.rotationSeverity.${line.severity}`)})
                </Typography>
              ) : null}
            </li>
          ))}
        </Box>
      </Alert>
    );
  };

  return (
    <Box
      component="section"
      aria-label={t('pages.bed.planting.hints.title')}
      data-testid="planting-hints"
      sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}
    >
      <Typography variant="subtitle1" component="h3">
        {t('pages.bed.planting.hints.title')}
      </Typography>
      {species.map(({ key, name, state, siteFit }) => (
        <Fragment key={key}>
          {rotationBlock(key, name, state)}
          {siteFit ? (
            <SiteFitHint
              speciesKey={key}
              speciesName={name}
              bedSun={bedSun}
              lightRequirement={siteFit.lightRequirement}
              shadeTolerance={siteFit.shadeTolerance}
              result={siteFit.result}
            />
          ) : null}
        </Fragment>
      ))}
      {mix.map((pair) => (
        <Alert
          key={`${pair.a}|${pair.b}`}
          severity={pair.kind === 'incompatible' ? 'warning' : 'success'}
          data-testid={`planting-mix-${pair.a}-${pair.b}`}
        >
          {pair.kind === 'incompatible'
            ? t('pages.bed.planting.hints.mixIncompatible', { a: nameOf(pair.a), b: nameOf(pair.b) })
            : t('pages.bed.planting.hints.mixCompatible', { a: nameOf(pair.a), b: nameOf(pair.b) })}
          {pair.reason ? ` ${pair.reason}` : ''}
        </Alert>
      ))}

      {mustGiveReason ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={overrideChecked}
                onChange={(event) => onOverrideChecked(event.target.checked)}
                slotProps={{ input: { 'data-testid': 'planting-override-check' } as object }}
              />
            }
            label={t('pages.bed.planting.hints.plantAnyway')}
            sx={{ minHeight: 48 }}
          />
          {overrideChecked ? (
            <TextField
              label={t('pages.bed.planting.hints.reason')}
              value={overrideReason}
              onChange={(event) => onOverrideReason(event.target.value)}
              required
              multiline
              minRows={2}
              error={showReasonError && overrideReason.trim() === ''}
              helperText={
                showReasonError && overrideReason.trim() === ''
                  ? t('pages.bed.planting.hints.reasonRequired')
                  : t('pages.bed.planting.hints.reasonHelp')
              }
              slotProps={{
                htmlInput: { maxLength: MAX_OVERRIDE_REASON, 'data-testid': 'planting-override-reason' },
              }}
            />
          ) : (
            <Typography variant="body2" color="text.secondary">
              {t('pages.bed.planting.hints.confirmToContinue')}
            </Typography>
          )}
        </Box>
      ) : null}
    </Box>
  );
}
