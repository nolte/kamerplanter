import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import LinearProgress from '@mui/material/LinearProgress';
import Chip from '@mui/material/Chip';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import type { ReadinessAssessment } from '@/api/types';

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
          />
        </Box>

        {/* Recommendation chip */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {t('pages.harvest.recommendation')}:
          </Typography>
          <Chip
            label={t(`enums.readinessRecommendation.${readiness.recommendation}`)}
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

        {/* Indicator breakdown */}
        {readiness.indicators.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              {t('pages.harvest.indicatorBreakdown')}
            </Typography>
            <Table size="small" aria-label={t('pages.harvest.indicatorBreakdown')}>
              <TableHead>
                <TableRow>
                  <TableCell>{t('pages.harvest.indicator')}</TableCell>
                  <TableCell>{t('pages.harvest.stage')}</TableCell>
                  <TableCell align="right">{t('pages.harvest.score')}</TableCell>
                  <TableCell align="right">
                    {t('pages.harvest.reliability')}
                  </TableCell>
                  <TableCell align="right">
                    {t('pages.harvest.contribution')}
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {readiness.indicators.map((ind) => (
                  <TableRow key={ind.indicator_key}>
                    <TableCell>{ind.indicator_key}</TableCell>
                    <TableCell>
                      <Chip
                        label={t(`enums.ripenessStage.${ind.stage}`)}
                        size="small"
                        color={
                          ind.stage === 'peak'
                            ? 'success'
                            : ind.stage === 'approaching'
                              ? 'warning'
                              : ind.stage === 'overripe'
                                ? 'error'
                                : 'default'
                        }
                      />
                    </TableCell>
                    <TableCell align="right">{ind.score}</TableCell>
                    <TableCell align="right">
                      {(ind.reliability * 100).toFixed(0)}%
                    </TableCell>
                    <TableCell align="right">
                      {ind.weighted_contribution.toFixed(1)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
