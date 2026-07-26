import { useCallback, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Skeleton from '@mui/material/Skeleton';
import Typography from '@mui/material/Typography';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import HarvestReadinessCard from '@/pages/ernte/HarvestReadinessCard';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchReadiness } from '@/store/slices/harvestSlice';

interface HarvestReadinessSectionProps {
  /** Document key of the plant instance whose harvest readiness is assessed. */
  plantKey: string;
}

/**
 * Harvest-readiness section of the plant-instance detail page (REQ-007 §3
 * "Reife-Visualisierung", §6 DoD).
 *
 * Owns the data lifecycle around {@link HarvestReadinessCard}, which is a pure
 * presentation component: this section dispatches the readiness assessment for
 * the plant and renders one of four honest states — loading, load failure (with
 * retry), "no ripeness observations recorded yet", and the card itself.
 *
 * The no-data state matters because the backend never 404s here: a plant without
 * observations still yields a well-formed assessment of ``overall_score: 0`` /
 * ``recommendation: "immature"`` / ``indicators: []``. Rendering the card for
 * that payload would show a red "Unreif" gauge that looks like a measurement but
 * is really an absence of data, so the empty indicator list is surfaced as an
 * explanation instead.
 */
export default function HarvestReadinessSection({
  plantKey,
}: HarvestReadinessSectionProps) {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const readiness = useAppSelector((state) => state.harvest.readiness);
  const readinessPlantKey = useAppSelector((state) => state.harvest.readinessPlantKey);
  const loading = useAppSelector((state) => state.harvest.readinessLoading);
  const error = useAppSelector((state) => state.harvest.readinessError);

  const load = useCallback(() => {
    dispatch(fetchReadiness(plantKey));
  }, [dispatch, plantKey]);

  useEffect(() => {
    load();
  }, [load]);

  // The slice holds a single, shared readiness slot. Only consume it once it is
  // known to describe *this* plant — otherwise a sibling's cached assessment
  // would flash on screen for the render between mount and the dispatch above.
  const isOwnResult = readinessPlantKey === plantKey;
  const ownReadiness = isOwnResult ? readiness : null;
  const ownError = isOwnResult ? error : null;

  if (ownError) {
    return (
      <Box sx={{ mb: 3 }} data-testid="harvest-readiness-section">
        <Card data-testid="harvest-readiness-error">
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('pages.harvest.readiness')}
            </Typography>
            <ErrorDisplay error={ownError} onRetry={load} />
          </CardContent>
        </Card>
      </Box>
    );
  }

  // ``ownReadiness === null`` covers the render between mount and the effect's
  // dispatch as well as the in-flight request, so the section never has a gap in
  // which it renders nothing at all — the E2E suite's
  // ``wait_for_loading_complete()`` relies on the skeleton marker being present
  // for the whole load.
  if (loading || ownReadiness === null) {
    return (
      <Box sx={{ mb: 3 }} data-testid="harvest-readiness-section">
        <Card data-testid="harvest-readiness-loading">
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('pages.harvest.readiness')}
            </Typography>
            <Box
              aria-busy="true"
              aria-live="polite"
              aria-label={t('pages.harvest.readinessLoading')}
              data-testid="loading-skeleton"
            >
              <Skeleton variant="text" width="30%" height={48} />
              <Skeleton variant="rectangular" height={8} sx={{ borderRadius: 1, mb: 2 }} />
              <Skeleton variant="text" width="45%" height={24} />
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  }

  if (ownReadiness.indicators.length === 0) {
    return (
      <Box sx={{ mb: 3 }} data-testid="harvest-readiness-section">
        <Card data-testid="harvest-readiness-empty">
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('pages.harvest.readiness')}
            </Typography>
            <Alert severity="info" variant="outlined">
              <AlertTitle>{t('pages.harvest.readinessNoData')}</AlertTitle>
              {t('pages.harvest.readinessNoDataHint')}
            </Alert>
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
    <Box sx={{ mb: 3 }} data-testid="harvest-readiness-section">
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {t('pages.harvest.readinessIntro')}
      </Typography>
      <HarvestReadinessCard readiness={ownReadiness} />
    </Box>
  );
}
