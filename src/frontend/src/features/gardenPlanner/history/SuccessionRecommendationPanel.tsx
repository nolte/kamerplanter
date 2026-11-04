/**
 * The follow-up crop recommendation under the planting timeline (REQ-053 GP-FR-133, §16.3): which step of the feeder
 * cycle - heavy feeder, medium feeder, light feeder, green manure or fallow - comes after the latest year, and which
 * families and species of the catalogue fit it. **Order only**: no nitrogen amount, no fertiliser dose. A species
 * without a stored feeder level never appears; an empty list says why.
 */
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import PlannerGlossary from '../glossary/PlannerGlossary';
import type { SuccessionFamily, SuccessionRecommendation, SuccessionSpecies } from './historyTypes';
import type { SuccessionState } from './useSuccessionRecommendation';

type T = (key: string, options?: Record<string, unknown>) => string;

const REASON_KEYS = ['nitrogen_fixation', 'soil_structure', 'biofumigation', 'pest_break'];

function demandText(value: string | null, t: T): string | null {
  return value ? t(`enums.nutrientDemandLevel.${value}`, { defaultValue: value }) : null;
}

function speciesLabel(species: SuccessionSpecies): string {
  return species.common_name ? `${species.common_name} (${species.scientific_name})` : species.scientific_name;
}

function FamilyEntry({ family, t }: { family: SuccessionFamily; t: T }) {
  const reason =
    family.benefit_reason && REASON_KEYS.includes(family.benefit_reason)
      ? t(`pages.bed.history.succession.reasons.${family.benefit_reason}`)
      : null;
  return (
    <Box component="li" sx={{ listStyle: 'none', py: 1, borderBottom: 1, borderColor: 'divider' }} data-testid={`succession-family-${family.family_key}`}>
      <Typography variant="subtitle2" component="h3">
        {family.family_name ?? family.family_key}
      </Typography>
      {reason && (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
          {reason}
        </Typography>
      )}
      {family.pause_years === null && (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
          {t('pages.bed.history.succession.pauseUnknown')}
        </Typography>
      )}
      <Box component="ul" role="list" sx={{ m: 0, mt: 0.5, p: 0 }}>
        {family.species.map((species) => (
          <Typography component="li" variant="body2" key={species.species_key} sx={{ listStyle: 'none' }}>
            {speciesLabel(species)}
            {species.nutrient_demand && (
              <Typography component="span" variant="caption" color="text.secondary">
                {' · '}
                {demandText(species.nutrient_demand, t)}
              </Typography>
            )}
            {species.nitrogen_fixing === true && (
              <Typography component="span" variant="caption" color="text.secondary">
                {' · '}
                {t('pages.bed.history.succession.nitrogenFixing')}
              </Typography>
            )}
          </Typography>
        ))}
      </Box>
    </Box>
  );
}

function Body({ recommendation, t }: { recommendation: SuccessionRecommendation; t: T }) {
  const { previous, target } = recommendation;
  const basis =
    previous && target
      ? t('pages.bed.history.succession.basis', {
          year: previous.year,
          previous:
            previous.step === 'restoring'
              ? t('pages.bed.history.succession.stepRestoring')
              : (demandText(previous.nutrient_demand, t) ?? ''),
          next: t(`pages.bed.history.succession.target.${target}`),
        })
      : null;
  return (
    <>
      {basis && (
        <Typography variant="body2" data-testid="succession-basis">
          {basis}
        </Typography>
      )}
      {recommendation.status !== 'ok' && (
        <Alert severity="info" data-testid="succession-status">
          {t(`pages.bed.history.succession.status.${recommendation.status}`)}
        </Alert>
      )}
      {recommendation.families.length > 0 && (
        <Box component="ul" role="list" sx={{ m: 0, p: 0 }} aria-label={t('pages.bed.history.succession.listLabel')}>
          {recommendation.families.map((family) => (
            <FamilyEntry key={family.family_key} family={family} t={t} />
          ))}
        </Box>
      )}
      {recommendation.fallow_option && (
        <Typography variant="body2" data-testid="succession-fallow">
          {t('pages.bed.history.succession.fallowOption')}
        </Typography>
      )}
      {recommendation.held_back.length > 0 && (
        <Box data-testid="succession-held-back">
          <Typography variant="caption" color="text.secondary" component="p" sx={{ m: 0 }}>
            {t('pages.bed.history.succession.heldBack')}
          </Typography>
          <Box component="ul" role="list" sx={{ m: 0, p: 0 }}>
            {recommendation.held_back.map((held) => (
              <Typography component="li" variant="caption" color="text.secondary" key={held.family_key} sx={{ listStyle: 'none' }}>
                {t('pages.bed.history.succession.heldBackLine', {
                  family: held.family_name ?? held.family_key,
                  year: held.last_year,
                  pause: held.pause_years,
                })}
              </Typography>
            ))}
          </Box>
        </Box>
      )}
    </>
  );
}

export default function SuccessionRecommendationPanel({ state, onRetry }: { state: SuccessionState; onRetry: () => void }) {
  const { t } = useTranslation();
  // The check being off for this bed is already told by the timeline; nothing to recommend then.
  if (state.status === 'ready' && state.recommendation.status === 'not_applicable') return null;
  return (
    <Box component="section" aria-labelledby="succession-title" data-testid="succession-panel" aria-busy={state.status === 'loading'} sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      <Typography id="succession-title" variant="h6" component="h2">
        {t('pages.bed.history.succession.title')}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {t('pages.bed.history.succession.hint')}
      </Typography>
      <PlannerGlossary id="succession" terms={['zehrerklassen', 'anbaupause', 'gruenduengung']} />
      {state.status === 'loading' && <LoadingSkeleton variant="card" />}
      {state.status === 'error' && (
        <Alert
          severity="warning"
          data-testid="succession-error"
          action={
            <Button color="inherit" size="small" onClick={onRetry} sx={{ minHeight: 44 }}>
              {t('common.retry')}
            </Button>
          }
        >
          {t('pages.bed.history.succession.loadFailed')}
        </Alert>
      )}
      {state.status === 'ready' && <Body recommendation={state.recommendation} t={t as T} />}
    </Box>
  );
}
