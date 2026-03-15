import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PageTitle from '@/components/layout/PageTitle';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ActivityPlanTab from '@/pages/durchlaeufe/ActivityPlanTab';
import { useApiError } from '@/hooks/useApiError';
import * as speciesApi from '@/api/endpoints/species';
import type { Species } from '@/api/types';

export default function ActivityPlanDetailPage() {
  const { speciesKey } = useParams<{ speciesKey: string }>();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { handleError } = useApiError();
  const [species, setSpecies] = useState<Species | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!speciesKey) return;
    speciesApi
      .getSpecies(speciesKey)
      .then(setSpecies)
      .catch((err) => {
        handleError(err);
        setError(String(err));
      })
      .finally(() => setLoading(false));
  }, [speciesKey, handleError]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !species) {
    return <ErrorDisplay error={error ?? 'Species not found'} />;
  }

  return (
    <Box>
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate('/aufgaben/activity-plans')}
        sx={{ mb: 1 }}
        size="small"
      >
        {t('pages.activityPlanOverview.title')}
      </Button>

      <PageTitle
        title={`${t('pages.activityPlan.tabTitle')} — ${species.common_names?.[0] ?? species.scientific_name}`}
      />

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {species.scientific_name}
      </Typography>

      <ActivityPlanTab speciesKey={species.key} />
    </Box>
  );
}
