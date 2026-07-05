import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import { useTheme } from '@mui/material/styles';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import type { SurvivalStats } from '@/api/types';

interface Props {
  stats: SurvivalStats;
}

/** Which loss dimension the chart visualises. */
type LossDimension = 'phase' | 'cause';

interface ChartDatum {
  label: string;
  count: number;
}

/**
 * Survival-rate / failure-cause analytics panel (REQ-003 G1).
 *
 * Presents the same data twice for accessibility: a numeric table (survival
 * rate + outcome/cause breakdown) and a bar chart of the losses, toggleable
 * between "by growth phase" (which phase dominates loss) and "by cause". The
 * table is the accessible text alternative to the chart.
 */
export default function SurvivalStatsPanel({ stats }: Props) {
  const { t } = useTranslation();
  const theme = useTheme();
  const [dimension, setDimension] = useState<LossDimension>('phase');

  // Categorical palette that stays legible in both light and dark themes —
  // all drawn from the MUI palette (theme-aware) rather than fixed hex values.
  const categoryColors = useMemo(
    () => [
      theme.palette.error.main,
      theme.palette.warning.main,
      theme.palette.info.main,
      theme.palette.secondary.main,
      theme.palette.success.main,
      theme.palette.primary.main,
    ],
    [theme.palette],
  );

  const survivalPercent = useMemo(() => Math.round(stats.survival_rate * 1000) / 10, [stats.survival_rate]);

  const phaseLabel = (name: string) =>
    name ? t(`enums.phaseName.${name}`, { defaultValue: name }) : t('pages.plantInstances.survival.phaseUnknown');

  const chartData = useMemo<ChartDatum[]>(() => {
    if (dimension === 'phase') {
      return stats.loss_by_phase.map((p) => ({ label: phaseLabel(p.phase_name), count: p.count }));
    }
    return stats.by_termination_cause.map((c) => ({
      label: t(`enums.terminationCause.${c.termination_cause}`),
      count: c.count,
    }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dimension, stats.loss_by_phase, stats.by_termination_cause, t]);

  const hasLosses = stats.died > 0;

  const survivalColor: 'success' | 'warning' | 'error' =
    survivalPercent >= 80 ? 'success' : survivalPercent >= 50 ? 'warning' : 'error';

  return (
    <Card sx={{ mb: 3 }} data-testid="survival-stats-panel">
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, flexWrap: 'wrap', mb: 0.5 }}>
          <Typography variant="h6" component="h2">
            {t('pages.plantInstances.survival.title')}
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.plantInstances.survival.intro')}
        </Typography>

        {stats.total === 0 ? (
          <Typography variant="body2" color="text.secondary" data-testid="survival-empty">
            {t('pages.plantInstances.survival.empty')}
          </Typography>
        ) : (
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
              gap: { xs: 2, md: 3 },
              alignItems: 'start',
            }}
          >
            {/* ── Numeric table ── */}
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5, flexWrap: 'wrap' }}>
                <Chip
                  color={survivalColor}
                  label={t('pages.plantInstances.survival.rateChip', { percent: survivalPercent })}
                  data-testid="survival-rate-chip"
                />
                <Typography variant="body2" color="text.secondary">
                  {t('pages.plantInstances.survival.rateCaption', {
                    survived: stats.survived,
                    terminated: stats.terminated,
                  })}
                </Typography>
              </Box>

              <Table size="small" aria-label={t('pages.plantInstances.survival.tableAria')}>
                <TableBody>
                  <TableRow>
                    <TableCell>{t('pages.plantInstances.survival.total')}</TableCell>
                    <TableCell align="right" data-testid="survival-total">{stats.total}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>{t('pages.plantInstances.survival.active')}</TableCell>
                    <TableCell align="right">{stats.active}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>{t('pages.plantInstances.survival.survived')}</TableCell>
                    <TableCell align="right" data-testid="survival-survived">{stats.survived}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ color: 'error.main' }}>{t('pages.plantInstances.survival.died')}</TableCell>
                    <TableCell align="right" sx={{ color: 'error.main' }} data-testid="survival-died">
                      {stats.died}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>

              {stats.by_termination_type.length > 0 && (
                <>
                  <Typography variant="subtitle2" sx={{ mt: 2, mb: 0.5 }}>
                    {t('pages.plantInstances.survival.byTypeTitle')}
                  </Typography>
                  <Table size="small" aria-label={t('pages.plantInstances.survival.byTypeTitle')}>
                    <TableHead>
                      <TableRow>
                        <TableCell>{t('pages.plantInstances.survival.outcome')}</TableCell>
                        <TableCell align="right">{t('pages.plantInstances.survival.count')}</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {stats.by_termination_type.map((row) => (
                        <TableRow key={row.termination_type}>
                          <TableCell>{t(`enums.terminationType.${row.termination_type}`)}</TableCell>
                          <TableCell align="right">{row.count}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </>
              )}

              {/* Text alternative for the "by phase" chart dimension (accessibility parity). */}
              {stats.loss_by_phase.length > 0 && (
                <>
                  <Typography variant="subtitle2" sx={{ mt: 2, mb: 0.5 }}>
                    {t('pages.plantInstances.survival.byPhaseTitle')}
                  </Typography>
                  <Table size="small" aria-label={t('pages.plantInstances.survival.byPhaseTitle')}>
                    <TableHead>
                      <TableRow>
                        <TableCell>{t('pages.plantInstances.survival.phase')}</TableCell>
                        <TableCell align="right">{t('pages.plantInstances.survival.count')}</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {stats.loss_by_phase.map((row) => (
                        <TableRow key={row.phase_name || 'unknown'}>
                          <TableCell>{phaseLabel(row.phase_name)}</TableCell>
                          <TableCell align="right">{row.count}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </>
              )}

              {stats.by_termination_cause.length > 0 && (
                <>
                  <Typography variant="subtitle2" sx={{ mt: 2, mb: 0.5 }}>
                    {t('pages.plantInstances.survival.byCauseTitle')}
                  </Typography>
                  <Table size="small" aria-label={t('pages.plantInstances.survival.byCauseTitle')}>
                    <TableHead>
                      <TableRow>
                        <TableCell>{t('pages.plantInstances.survival.cause')}</TableCell>
                        <TableCell align="right">{t('pages.plantInstances.survival.count')}</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {stats.by_termination_cause.map((row) => (
                        <TableRow key={row.termination_cause}>
                          <TableCell>{t(`enums.terminationCause.${row.termination_cause}`)}</TableCell>
                          <TableCell align="right">{row.count}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </>
              )}
            </Box>

            {/* ── Chart ── */}
            <Box>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 1,
                  flexWrap: 'wrap',
                  mb: 1,
                }}
              >
                <Typography variant="subtitle2" component="h3">
                  {t('pages.plantInstances.survival.chartTitle')}
                </Typography>
                <ToggleButtonGroup
                  size="small"
                  exclusive
                  value={dimension}
                  onChange={(_, v: LossDimension | null) => v && setDimension(v)}
                  aria-label={t('pages.plantInstances.survival.dimensionToggleAria')}
                >
                  <ToggleButton value="phase" data-testid="dimension-phase">
                    {t('pages.plantInstances.survival.byPhase')}
                  </ToggleButton>
                  <ToggleButton value="cause" data-testid="dimension-cause">
                    {t('pages.plantInstances.survival.byCause')}
                  </ToggleButton>
                </ToggleButtonGroup>
              </Box>

              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                {dimension === 'phase'
                  ? t('pages.plantInstances.survival.byPhaseHint')
                  : t('pages.plantInstances.survival.byCauseHint')}
              </Typography>

              {!hasLosses || chartData.length === 0 ? (
                <Typography variant="body2" color="text.secondary" data-testid="survival-chart-empty">
                  {t('pages.plantInstances.survival.noLosses')}
                </Typography>
              ) : (
                <Box
                  role="img"
                  aria-label={t('pages.plantInstances.survival.chartAria')}
                  data-testid="survival-chart"
                  sx={{ height: { xs: 220, md: 260 } }}
                >
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 24, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} vertical={false} />
                      <XAxis
                        dataKey="label"
                        tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                        stroke={theme.palette.divider}
                        interval={0}
                        angle={-20}
                        textAnchor="end"
                        height={48}
                      />
                      <YAxis
                        allowDecimals={false}
                        tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                        stroke={theme.palette.divider}
                        width={32}
                        label={{
                          value: t('pages.plantInstances.survival.count'),
                          angle: -90,
                          position: 'insideLeft',
                          offset: 12,
                          style: { fontSize: 11, fill: theme.palette.text.secondary, textAnchor: 'middle' },
                        }}
                      />
                      <Tooltip
                        cursor={{ fill: theme.palette.action.hover }}
                        contentStyle={{
                          backgroundColor: theme.palette.background.paper,
                          border: `1px solid ${theme.palette.divider}`,
                          borderRadius: 4,
                          fontSize: '0.8rem',
                        }}
                        labelStyle={{ color: theme.palette.text.primary }}
                        formatter={(value) => [value as number, t('pages.plantInstances.survival.count')]}
                      />
                      <Bar dataKey="count" radius={[4, 4, 0, 0]} isAnimationActive={false}>
                        {chartData.map((d, i) => (
                          <Cell key={d.label} fill={categoryColors[i % categoryColors.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              )}
            </Box>
          </Box>
        )}

        <Divider sx={{ mt: 2 }} />
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          {t('pages.plantInstances.survival.definitionNote')}
        </Typography>
      </CardContent>
    </Card>
  );
}
