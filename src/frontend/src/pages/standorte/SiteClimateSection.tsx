import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Skeleton from '@mui/material/Skeleton';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import EmptyState from '@/components/common/EmptyState';
import WeatherProvenanceBadge from '@/components/weather/WeatherProvenanceBadge';
import { useSiteClimateNormals } from '@/hooks/useSiteClimateNormals';
import type { ClimateNormal } from '@/api/types';

interface Props {
  siteKey: string;
  /** Site's IANA/BCP-47 language is taken from the app locale; no prop needed. */
}

interface MonthRow {
  month: string;
  tempAvg: number | null;
  tempMin: number | null;
  precip: number | null;
  solar: number | null;
}

/** Localised short month labels (Jan…Dez / Jan…Dec) from the active app locale. */
function useMonthLabels(): string[] {
  const { i18n } = useTranslation();
  return useMemo(() => {
    const fmt = new Intl.DateTimeFormat(i18n.language, { month: 'short' });
    return Array.from({ length: 12 }, (_, idx) => fmt.format(new Date(2001, idx, 1)));
  }, [i18n.language]);
}

function at(series: number[], idx: number): number | null {
  return idx < series.length ? series[idx] : null;
}

/**
 * REQ-041 — "Klima am Standort": renders a site's long-term monthly climate
 * normals (NASA POWER reanalysis) as a 12-month chart + table, with the source
 * provenance badge and the mandatory CC-BY attribution. Graceful: shows an empty
 * state until the monthly fetch beat has populated the site's normals.
 */
export default function SiteClimateSection({ siteKey }: Props) {
  const { t } = useTranslation();
  const theme = useTheme();
  const months = useMonthLabels();
  const { loading, error, normals, refetch } = useSiteClimateNormals(siteKey);

  // One record per source; the NASA POWER (reanalysis) record is the REQ-041
  // primary — prefer it, else fall back to the first available source.
  const normal: ClimateNormal | null = useMemo(() => {
    if (normals.length === 0) return null;
    return normals.find((n) => n.source === 'nasa-power') ?? normals[0];
  }, [normals]);

  const rows: MonthRow[] = useMemo(() => {
    if (!normal) return [];
    return months.map((month, idx) => ({
      month,
      tempAvg: at(normal.monthly_temp_avg_c, idx),
      tempMin: at(normal.monthly_temp_min_c, idx),
      precip: at(normal.monthly_precip_mm, idx),
      solar: at(normal.monthly_solar_mj_m2, idx),
    }));
  }, [normal, months]);

  const period =
    normal?.period_start_year && normal?.period_end_year
      ? `${normal.period_start_year}–${normal.period_end_year}`
      : null;

  return (
    <Card variant="outlined" sx={{ mt: 4 }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 0.5 }}>
          {t('pages.siteDetail.climate.title')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.siteDetail.climate.description')}
        </Typography>

        {loading && <Skeleton variant="rectangular" height={220} sx={{ borderRadius: 1 }} />}

        {!loading && error && (
          <Alert
            severity="error"
            action={
              <Button color="inherit" size="small" onClick={refetch}>
                {t('common.retry')}
              </Button>
            }
          >
            {t('pages.siteDetail.climate.loadError')}
          </Alert>
        )}

        {!loading && !error && !normal && (
          <EmptyState message={t('pages.siteDetail.climate.empty')} />
        )}

        {!loading && !error && normal && (
          <Stack spacing={2}>
            <Box sx={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
              <WeatherProvenanceBadge source={normal.source} dataKind="reanalysis" />
              {period && (
                <Typography variant="caption" color="text.secondary">
                  {t('pages.siteDetail.climate.period', { period })}
                </Typography>
              )}
            </Box>

            <Box sx={{ width: '100%', height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} stroke={theme.palette.text.secondary} />
                  <YAxis
                    yAxisId="temp"
                    tick={{ fontSize: 11 }}
                    stroke={theme.palette.text.secondary}
                    width={44}
                    unit="°C"
                  />
                  <YAxis
                    yAxisId="precip"
                    orientation="right"
                    tick={{ fontSize: 11 }}
                    stroke={theme.palette.text.secondary}
                    width={44}
                    unit="mm"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme.palette.background.paper,
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: theme.shape.borderRadius,
                      fontSize: '0.8rem',
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '0.75rem' }} />
                  <Bar
                    yAxisId="precip"
                    dataKey="precip"
                    name={t('pages.siteDetail.climate.precip')}
                    fill={theme.palette.info.main}
                    fillOpacity={0.5}
                    radius={[2, 2, 0, 0]}
                  />
                  <Line
                    yAxisId="temp"
                    type="monotone"
                    dataKey="tempAvg"
                    name={t('pages.siteDetail.climate.tempAvg')}
                    stroke={theme.palette.error.main}
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    yAxisId="temp"
                    type="monotone"
                    dataKey="tempMin"
                    name={t('pages.siteDetail.climate.tempMin')}
                    stroke={theme.palette.primary.main}
                    strokeWidth={2}
                    strokeDasharray="4 3"
                    dot={false}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </Box>

            <TableContainer>
              <Table size="small" aria-label={t('pages.siteDetail.climate.tableLabel')}>
                <TableHead>
                  <TableRow>
                    <TableCell>{t('pages.siteDetail.climate.month')}</TableCell>
                    <TableCell align="right">{t('pages.siteDetail.climate.tempAvg')} (°C)</TableCell>
                    <TableCell align="right">{t('pages.siteDetail.climate.tempMin')} (°C)</TableCell>
                    <TableCell align="right">{t('pages.siteDetail.climate.precip')} (mm)</TableCell>
                    <TableCell align="right">{t('pages.siteDetail.climate.solar')} (MJ/m²)</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows.map((row) => (
                    <TableRow key={row.month}>
                      <TableCell>{row.month}</TableCell>
                      <TableCell align="right">{row.tempAvg?.toFixed(1) ?? '–'}</TableCell>
                      <TableCell align="right">{row.tempMin?.toFixed(1) ?? '–'}</TableCell>
                      <TableCell align="right">{row.precip?.toFixed(0) ?? '–'}</TableCell>
                      <TableCell align="right">{row.solar?.toFixed(1) ?? '–'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {(normal.annual_temp_avg_c != null || normal.annual_precip_mm != null) && (
              <Typography variant="body2" color="text.secondary">
                {t('pages.siteDetail.climate.annual', {
                  temp: normal.annual_temp_avg_c?.toFixed(1) ?? '–',
                  precip: normal.annual_precip_mm?.toFixed(0) ?? '–',
                })}
              </Typography>
            )}

            {normal.attribution && (
              <Typography variant="caption" color="text.secondary" data-testid="climate-attribution">
                {normal.attribution}
              </Typography>
            )}
          </Stack>
        )}
      </CardContent>
    </Card>
  );
}
