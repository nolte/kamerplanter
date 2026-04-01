import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardActionArea from '@mui/material/CardActionArea';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import ScienceIcon from '@mui/icons-material/Science';
import PageTitle from '@/components/layout/PageTitle';
import EmptyState from '@/components/common/EmptyState';
import { useApiError } from '@/hooks/useApiError';
import * as speciesApi from '@/api/endpoints/species';
import * as activityPlanApi from '@/api/endpoints/activityPlans';
import type { Species, ActivityPlanResponse } from '@/api/types';

interface SpeciesPlanPreview {
  species: Species;
  plan: ActivityPlanResponse | null;
  loading: boolean;
  cultivarCount: number | null;
}

export default function ActivityPlanOverviewPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { handleError } = useApiError();
  const [speciesList, setSpeciesList] = useState<Species[]>([]);
  const [loading, setLoading] = useState(true);
  const [previews, setPreviews] = useState<Map<string, SpeciesPlanPreview>>(new Map());

  useEffect(() => {
    speciesApi
      .listSpecies(0, 200)
      .then((r) => {
        setSpeciesList(r.items);
      })
      .catch(handleError)
      .finally(() => setLoading(false));
  }, [handleError]);

  // Auto-generate previews for all species
  useEffect(() => {
    if (speciesList.length === 0) return;

    for (const sp of speciesList) {
      if (previews.has(sp.key)) continue;

      // eslint-disable-next-line react-hooks/set-state-in-effect -- set loading placeholder before async fetch
      setPreviews((prev) => new Map(prev).set(sp.key, { species: sp, plan: null, loading: true, cultivarCount: null }));

      const planPromise = activityPlanApi
        .generatePlan({ species_key: sp.key })
        .catch(() => null);
      const cultivarPromise = speciesApi
        .listCultivars(sp.key)
        .then((list) => list.length)
        .catch(() => 0);

      Promise.all([planPromise, cultivarPromise]).then(([plan, cultivarCount]) => {
        setPreviews((prev) => {
          const next = new Map(prev);
          next.set(sp.key, { species: sp, plan, loading: false, cultivarCount });
          return next;
        });
      });
    }
  }, [speciesList]); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <PageTitle title={t('pages.activityPlanOverview.title')} />

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t('pages.activityPlanOverview.description')}
      </Typography>

      {speciesList.length === 0 && (
        <EmptyState
          message={t('pages.activityPlanOverview.noSpecies')}
          actionLabel={t('pages.activityPlanOverview.addSpeciesCta')}
          onAction={() => navigate('/stammdaten/species')}
        />
      )}

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' },
          gap: 2,
        }}
      >
        {speciesList.map((sp) => {
          const preview = previews.get(sp.key);
          const plan = preview?.plan;
          const isLoading = preview?.loading ?? true;

          return (
            <Card key={sp.key} variant="outlined">
              <CardActionArea
                onClick={() => navigate(`/aufgaben/activity-plans/${sp.key}`)}
                disabled={isLoading || !plan}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Box>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        {sp.common_names?.[0] ?? sp.scientific_name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {sp.scientific_name}
                      </Typography>
                    </Box>
                    <ScienceIcon color="action" />
                  </Box>

                  {isLoading && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                      <CircularProgress size={16} />
                      <Typography variant="caption" color="text.secondary">
                        {t('pages.activityPlanOverview.generating')}
                      </Typography>
                    </Box>
                  )}

                  {!isLoading && plan && (
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 1 }}>
                      <Chip
                        label={t('pages.activityPlanOverview.phases', { count: new Set(plan.templates.map((tt) => tt.trigger_phase)).size })}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        label={t('pages.activityPlanOverview.activities', { count: plan.total_activities })}
                        size="small"
                        color="primary"
                      />
                      <Chip
                        label={`${plan.total_duration_days}d`}
                        size="small"
                        variant="outlined"
                      />
                      {preview?.cultivarCount != null && preview.cultivarCount > 0 && (
                        <Chip
                          label={t('pages.activityPlanOverview.cultivars', { count: preview.cultivarCount })}
                          size="small"
                          color="secondary"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  )}

                  {!isLoading && !plan && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                      {t('pages.activityPlanOverview.noPlan')}
                    </Typography>
                  )}
                </CardContent>
              </CardActionArea>
            </Card>
          );
        })}
      </Box>
    </Box>
  );
}
