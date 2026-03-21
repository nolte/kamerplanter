import { useEffect, useState, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Link from '@mui/material/Link';
import Skeleton from '@mui/material/Skeleton';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { useApiError } from '@/hooks/useApiError';
import {
  fetchWaterMixRecommendationsBatch,
  type WaterMixBatchRecommendation,
  type WaterMixRecommendation,
} from '@/api/endpoints/nutrient-plans';

interface Props {
  planKey: string | null;
  siteKey: string | null;
}

const PHASE_COLORS: Record<string, 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info'> = {
  germination: 'default',
  seedling: 'info',
  vegetative: 'success',
  flowering: 'warning',
  flushing: 'secondary',
  harvest: 'error',
};

function PhaseRow({ rec }: { rec: WaterMixRecommendation }) {
  const { t } = useTranslation();
  const r = rec.recommendation;
  const needsCalmag = r.calmag_correction?.needs_correction ?? false;

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        flexWrap: 'wrap',
        py: 0.5,
      }}
      data-testid={`water-mix-phase-${rec.phase_name}`}
    >
      <Chip
        label={t(`enums.phaseName.${rec.phase_name}`, rec.phase_name)}
        size="small"
        color={PHASE_COLORS[rec.phase_name] ?? 'default'}
        sx={{ minWidth: 80 }}
      />
      <Tooltip title={r.reasoning} arrow>
        <Chip
          label={t('pages.nutrientPlans.waterMix.roRecommended', {
            percent: r.recommended_ro_percent,
          })}
          size="small"
          variant="outlined"
          icon={<WaterDropIcon sx={{ fontSize: '1rem' }} />}
          sx={{ cursor: 'help' }}
        />
      </Tooltip>
      <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'nowrap' }}>
        EC {r.effective_ec_ms.toFixed(2)} / {r.target_ec_ms.toFixed(2)} mS
      </Typography>
      {needsCalmag && (
        <Tooltip
          title={t('pages.nutrientPlans.waterMix.calmagNeeded', {
            ca: r.calmag_correction!.calcium_deficit_ppm.toFixed(1),
            mg: r.calmag_correction!.magnesium_deficit_ppm.toFixed(1),
          })}
          arrow
        >
          <Chip
            label={t('pages.nutrientPlans.waterMix.calmagNeededShort')}
            size="small"
            color="warning"
            variant="outlined"
            icon={<InfoOutlinedIcon sx={{ fontSize: '0.875rem' }} />}
            sx={{ cursor: 'help' }}
          />
        </Tooltip>
      )}
    </Box>
  );
}

export default function WaterMixSummaryCard({ planKey, siteKey }: Props) {
  const { t } = useTranslation();
  const { handleError } = useApiError();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<WaterMixBatchRecommendation | null>(null);

  const fetchData = useCallback(async () => {
    if (!planKey || !siteKey) return;
    try {
      setLoading(true);
      const result = await fetchWaterMixRecommendationsBatch(planKey, siteKey);
      setData(result);
    } catch (err) {
      // Silently fail — this is a supplementary display, not critical
      handleError(err);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [planKey, siteKey, handleError]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const sortedRecommendations = useMemo(
    () =>
      data?.recommendations
        ?.filter((r) => r.recommendation.recommended_ro_percent > 0)
        .sort((a, b) => a.sequence_order - b.sequence_order) ?? [],
    [data],
  );

  // Show nothing when no data, still loading initial, or no RO recommendations
  if (!planKey || !siteKey) return null;

  if (loading && !data) {
    return (
      <Card sx={{ mt: 2, mb: 1 }} data-testid="water-mix-summary-skeleton">
        <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
          <Stack spacing={1}>
            <Skeleton variant="text" width={220} height={28} />
            <Skeleton variant="rectangular" height={32} />
            <Skeleton variant="rectangular" height={32} />
          </Stack>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  if (sortedRecommendations.length === 0) {
    return (
      <Alert severity="info" sx={{ mt: 2, mb: 1 }} data-testid="water-mix-no-config-hint">
        {t('pages.nutrientPlans.waterMix.noWaterConfig', { siteName: data.site_name ?? '' })}
        {siteKey && (
          <Link component={RouterLink} to={`/standorte/sites/${siteKey}`} sx={{ ml: 0.5 }}>
            {t('pages.nutrientPlans.waterMix.configureSite')}
          </Link>
        )}
      </Alert>
    );
  }

  return (
    <Card
      sx={{ mt: 2, mb: 1 }}
      data-testid="water-mix-summary-card"
    >
      <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <WaterDropIcon color="primary" sx={{ fontSize: '1.25rem' }} />
          <Typography variant="subtitle2">
            {t('pages.nutrientPlans.waterMix.batchTitle')}
          </Typography>
        </Box>
        <Stack spacing={0.5}>
          {sortedRecommendations.map((rec) => (
            <PhaseRow key={rec.sequence_order} rec={rec} />
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
}
