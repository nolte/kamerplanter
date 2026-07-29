import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import LinearProgress from '@mui/material/LinearProgress';
import Chip from '@mui/material/Chip';
import DataTable, { type Column } from '@/components/common/DataTable';
import MobileCard from '@/components/common/MobileCard';
import HelpTooltip from '@/components/common/HelpTooltip';
import type { ReadinessAssessment, ReadinessIndicatorBreakdown } from '@/api/types';

interface HarvestReadinessCardProps {
  readiness: ReadinessAssessment;
}

function getRecommendationColor(
  recommendation: string,
): 'success' | 'warning' | 'info' | 'error' {
  switch (recommendation) {
    case 'optimal':
      return 'success';
    case 'approaching':
      return 'warning';
    case 'developing':
      return 'info';
    default:
      return 'error';
  }
}

function getScoreColor(
  score: number,
): 'success' | 'warning' | 'error' {
  if (score >= 80) return 'success';
  if (score >= 50) return 'warning';
  return 'error';
}

/** Chip colour for a ripeness stage, shared between the desktop table column
 *  and the mobile card renderer so both layouts agree on the same verdict
 *  colour. Falls back to the neutral palette default for an unmapped stage. */
function getStageColor(
  stage: string,
): 'success' | 'warning' | 'error' | 'default' {
  if (stage === 'peak') return 'success';
  if (stage === 'approaching') return 'warning';
  if (stage === 'overripe') return 'error';
  return 'default';
}

export default function HarvestReadinessCard({
  readiness,
}: HarvestReadinessCardProps) {
  const { t } = useTranslation();

  const recommendationColor = useMemo(
    () => getRecommendationColor(readiness.recommendation),
    [readiness.recommendation],
  );

  const scoreColor = useMemo(
    () => getScoreColor(readiness.overall_score),
    [readiness.overall_score],
  );

  const indicatorColumns: Column<ReadinessIndicatorBreakdown>[] = [
    {
      id: 'indicator',
      label: t('pages.harvest.indicator'),
      render: (ind) => ind.indicator_key,
    },
    {
      id: 'stage',
      label: t('pages.harvest.stage'),
      render: (ind) => (
        <Chip
          label={t(`enums.ripenessStage.${ind.stage}`, ind.stage)}
          size="small"
          color={getStageColor(ind.stage)}
        />
      ),
      searchValue: (ind) => ind.stage,
    },
    {
      id: 'score',
      label: t('pages.harvest.score'),
      align: 'right',
      render: (ind) => ind.score,
    },
    {
      id: 'reliability',
      label: t('pages.harvest.reliability'),
      align: 'right',
      render: (ind) => `${(ind.reliability * 100).toFixed(0)}%`,
    },
    {
      id: 'contribution',
      label: t('pages.harvest.contribution'),
      align: 'right',
      render: (ind) => ind.weighted_contribution.toFixed(1),
    },
  ];

  return (
    <Card data-testid="harvest-readiness-card">
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {t('pages.harvest.readiness')}
        </Typography>

        {/* Overall score gauge */}
        <Box sx={{ mb: 3 }}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 1,
            }}
          >
            <Typography variant="body2" color="text.secondary">
              {t('pages.harvest.overallScore')}
            </Typography>
            <Typography variant="h4" component="span">
              {readiness.overall_score}
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={Math.min(readiness.overall_score, 100)}
            color={scoreColor}
            sx={{ height: 8, borderRadius: 1 }}
            aria-label={t('pages.harvest.overallScore')}
          />
        </Box>

        {/* Recommendation chip */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {t('pages.harvest.recommendation')}:
          </Typography>
          {/* Both enum lookups pass the raw backend value as the i18n fallback:
              the recommendation/stage vocabularies are owned by the backend, so
              an as-yet-untranslated value must degrade to the value itself
              rather than leaking the literal key ("enums.ripenessStage.x") into
              the UI. Matches the `enums.phaseName` fallback on the detail page. */}
          <Chip
            label={t(
              `enums.readinessRecommendation.${readiness.recommendation}`,
              readiness.recommendation,
            )}
            color={recommendationColor}
            size="small"
          />
        </Box>

        {/* Estimated days */}
        {readiness.estimated_days != null && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              {t('pages.harvest.estimatedDays')}:{' '}
              <Typography component="span" variant="body2" sx={{ fontWeight: 'bold' }}>
                {readiness.estimated_days}{' '}
                {t('pages.harvest.days')}
              </Typography>
            </Typography>
          </Box>
        )}

        {/* Indicator breakdown. Reuses the mandatory `DataTable` (UI-NFR-010
            R-037) instead of a hand-rolled `<Table>` so the five-column
            breakdown gets the same mobile treatment as every other table in
            the app: below the `sm` breakpoint it switches to a stacked
            `MobileCard` per indicator instead of squashing five columns into
            a 393px viewport. */}
        {readiness.indicators.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
              <Typography variant="subtitle2">
                {t('pages.harvest.indicatorBreakdown')}
              </Typography>
              <HelpTooltip term="readiness_reliability" iconOnly />
            </Box>
            <DataTable
              columns={indicatorColumns}
              rows={readiness.indicators}
              getRowKey={(ind) => ind.indicator_key}
              variant="simple"
              ariaLabel={t('pages.harvest.indicatorBreakdown')}
              mobileCardRenderer={(ind) => (
                <MobileCard
                  title={ind.indicator_key}
                  titleId="indicator"
                  chips={[
                    {
                      id: 'stage',
                      content: (
                        <Chip
                          label={t(`enums.ripenessStage.${ind.stage}`, ind.stage)}
                          size="small"
                          color={getStageColor(ind.stage)}
                        />
                      ),
                    },
                  ]}
                  fields={[
                    { id: 'score', label: t('pages.harvest.score'), value: ind.score },
                    {
                      id: 'reliability',
                      label: t('pages.harvest.reliability'),
                      value: `${(ind.reliability * 100).toFixed(0)}%`,
                    },
                    {
                      id: 'contribution',
                      label: t('pages.harvest.contribution'),
                      value: ind.weighted_contribution.toFixed(1),
                    },
                  ]}
                />
              )}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
