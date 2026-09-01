import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import Skeleton from '@mui/material/Skeleton';
import ScienceOutlinedIcon from '@mui/icons-material/ScienceOutlined';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import NutrientPlanCard from '../components/NutrientPlanCard';
import type { NutrientPlanMatch, ExperienceLevel } from '@/api/types';
import LoadingStatus from '@/components/common/LoadingStatus';

interface NutrientPlanStepProps {
  plans: NutrientPlanMatch[];
  loading: boolean;
  favoriteNutrientPlanKeys: string[];
  onToggleFavoritePlan: (planKey: string) => void;
  experienceLevel: ExperienceLevel;
}

export default function NutrientPlanStep({
  plans,
  loading,
  favoriteNutrientPlanKeys,
  onToggleFavoritePlan,
  experienceLevel,
}: NutrientPlanStepProps) {
  const { t } = useTranslation();

  if (loading) {
    return (
      <Box data-testid="onboarding-step-nutrient-plans">
        <Typography variant="h6" gutterBottom>
          {t('pages.onboarding.nutrientPlans.title')}
        </Typography>
        {/* The `aria-live="polite"` that used to sit on this wrapper announced
            nothing: its only content was decorative skeletons, and the whole
            block is unmounted when loading finishes rather than updated in
            place, so there was never a content change to announce. The
            announcement now comes from a live region that has words in it
            (#1324). */}
        <Box aria-busy="true">
          <LoadingStatus />
          <Grid container spacing={2}>
            {[1, 2, 3].map((i) => (
              <Grid key={i} size={{ xs: 12, sm: 6 }}>
                {/* Skeleton height matches actual card more accurately */}
                <Skeleton variant="rounded" height={120} />
              </Grid>
            ))}
          </Grid>
        </Box>
      </Box>
    );
  }

  return (
    <Box data-testid="onboarding-step-nutrient-plans">
      <Typography variant="h6" gutterBottom>
        {t('pages.onboarding.nutrientPlans.title')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t('pages.onboarding.nutrientPlans.subtitle')}
      </Typography>

      {plans.length === 0 ? (
        /* Structured empty state instead of bare text */
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 1.5,
            py: 6,
            px: 3,
            border: 1,
            borderColor: 'divider',
            borderRadius: 2,
            textAlign: 'center',
          }}
        >
          <ScienceOutlinedIcon sx={{ fontSize: 40, color: 'text.disabled' }} aria-hidden="true" />
          <Typography variant="body1" color="text.secondary">
            {t('pages.onboarding.nutrientPlans.noPlans')}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {t('pages.onboarding.nutrientPlans.noPlansDetail')}
          </Typography>
        </Box>
      ) : (
        <>
          {/* role="listbox" groups the cards semantically as a selection list */}
          <Grid
            container
            spacing={2}
            role="listbox"
            aria-label={t('pages.onboarding.nutrientPlans.title')}
            aria-multiselectable="true"
          >
            {plans.map((plan) => (
              <Grid key={plan.plan_key} size={{ xs: 12, sm: 6 }}>
                <NutrientPlanCard
                  plan={plan}
                  favorited={favoriteNutrientPlanKeys.includes(plan.plan_key)}
                  onToggleFavorite={() => onToggleFavoritePlan(plan.plan_key)}
                  experienceLevel={experienceLevel}
                />
              </Grid>
            ))}
          </Grid>

          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5, mt: 2 }}>
            <InfoOutlinedIcon
              fontSize="small"
              sx={{ color: 'text.secondary', mt: '1px', flexShrink: 0 }}
              aria-hidden="true"
            />
            <Typography variant="caption" color="text.secondary">
              {t('pages.onboarding.nutrientPlans.favoriteHint')}
            </Typography>
          </Box>
        </>
      )}
    </Box>
  );
}
