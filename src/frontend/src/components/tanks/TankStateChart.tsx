import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import { useTheme } from '@mui/material/styles';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import dayjs from 'dayjs';
import type { TankState } from '@/api/types';

/** Metric keys that can be toggled on/off in the chart. */
type MetricKey = 'ph' | 'ec_ms' | 'water_temp_celsius' | 'fill_level_percent';

interface TankStateChartProps {
  states: TankState[];
}

interface ChartDataPoint {
  time: number;
  ph?: number;
  ec_ms?: number;
  water_temp_celsius?: number;
  fill_level_percent?: number;
}

interface TooltipPayloadEntry {
  dataKey?: string | number;
  name?: string;
  value?: number;
  color?: string;
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TooltipPayloadEntry[];
  label?: number;
}) {
  if (!active || !payload?.length) return null;
  const d = dayjs(label);
  return (
    <Box
      role="tooltip"
      sx={{
        bgcolor: 'background.paper',
        border: 1,
        borderColor: 'divider',
        borderRadius: 1,
        p: 1,
        fontSize: '0.8rem',
        boxShadow: 2,
      }}
    >
      <Typography variant="caption" sx={{ display: 'block', mb: 0.5, color: 'text.secondary' }}>
        {d.format('DD.MM.YYYY HH:mm')}
      </Typography>
      {payload.map((p) => (
        <Box key={String(p.dataKey)} sx={{ color: p.color, lineHeight: 1.6 }}>
          {p.name}: <strong>{typeof p.value === 'number' ? p.value.toFixed(2) : p.value}</strong>
        </Box>
      ))}
    </Box>
  );
}

/**
 * Chart component displaying tank state measurements over time.
 * Shows pH, EC, temperature and fill level as separate line series
 * with toggle buttons to show/hide individual metrics.
 */
export default function TankStateChart({ states }: TankStateChartProps) {
  const { t } = useTranslation();
  const theme = useTheme();

  const [visibleMetrics, setVisibleMetrics] = useState<MetricKey[]>([
    'ph',
    'ec_ms',
    'water_temp_celsius',
    'fill_level_percent',
  ]);

  const metricConfig: Record<
    MetricKey,
    { label: string; color: string; yAxisId: string; unit: string }
  > = useMemo(
    () => ({
      ph: {
        label: t('enums.sensorMetricType.ph'),
        color: theme.palette.success.main,
        yAxisId: 'left',
        unit: '',
      },
      ec_ms: {
        label: t('enums.sensorMetricType.ec_ms'),
        color: theme.palette.warning.main,
        yAxisId: 'right',
        unit: ' mS/cm',
      },
      water_temp_celsius: {
        label: t('pages.tanks.waterTempShort'),
        color: theme.palette.info.main,
        yAxisId: 'right',
        unit: ' \u00B0C',
      },
      fill_level_percent: {
        label: t('pages.tanks.fillLevel'),
        color: theme.palette.secondary.main,
        yAxisId: 'right',
        unit: ' %',
      },
    }),
    [t, theme.palette],
  );

  const chartData = useMemo<ChartDataPoint[]>(() => {
    const points: ChartDataPoint[] = states
      .filter((s) => s.recorded_at != null)
      .map((s) => ({
        time: dayjs(s.recorded_at!).valueOf(),
        ...(s.ph != null ? { ph: s.ph } : {}),
        ...(s.ec_ms != null ? { ec_ms: s.ec_ms } : {}),
        ...(s.water_temp_celsius != null
          ? { water_temp_celsius: s.water_temp_celsius }
          : {}),
        ...(s.fill_level_percent != null
          ? { fill_level_percent: s.fill_level_percent }
          : {}),
      }));
    points.sort((a, b) => a.time - b.time);
    return points;
  }, [states]);

  const handleToggle = (_: React.MouseEvent<HTMLElement>, newMetrics: MetricKey[]) => {
    // Ensure at least one metric remains selected
    if (newMetrics.length > 0) {
      setVisibleMetrics(newMetrics);
    }
  };

  const tickFormatter = useMemo(() => {
    if (chartData.length < 2) return (ts: number) => dayjs(ts).format('DD.MM.');
    const rangeMs = chartData[chartData.length - 1].time - chartData[0].time;
    const rangeDays = rangeMs / (1000 * 60 * 60 * 24);
    if (rangeDays <= 2) return (ts: number) => dayjs(ts).format('DD.MM. HH:mm');
    if (rangeDays <= 14) return (ts: number) => dayjs(ts).format('dd DD.MM.');
    return (ts: number) => dayjs(ts).format('DD.MM.');
  }, [chartData]);

  // Check which Y-axes are needed based on visible metrics
  const showLeftAxis = visibleMetrics.includes('ph');
  const showRightAxis = visibleMetrics.some((m) => metricConfig[m].yAxisId === 'right');

  if (chartData.length < 2) {
    return null;
  }

  return (
    <Box
      data-testid="tank-state-chart"
      sx={{ mb: 3 }}
      role="region"
      aria-label={t('pages.tanks.chartTitle')}
    >
      {/* Header row: title + metric toggles */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 1,
          mb: 1.5,
        }}
      >
        <Typography variant="subtitle2" component="h3">
          {t('pages.tanks.chartTitle')}
        </Typography>

        <ToggleButtonGroup
          value={visibleMetrics}
          onChange={handleToggle}
          size="small"
          aria-label={t('pages.tanks.chartToggleLabel')}
          sx={{
            flexWrap: 'wrap',
            gap: 0.5,
            // Remove default border between wrapped rows
            '& .MuiToggleButtonGroup-grouped': {
              borderRadius: '4px !important',
              border: '1px solid !important',
              borderColor: 'divider !important',
            },
          }}
        >
          {(Object.keys(metricConfig) as MetricKey[]).map((key) => (
            <ToggleButton
              key={key}
              value={key}
              data-testid={`chart-toggle-${key}`}
              aria-label={metricConfig[key].label}
              sx={{
                fontSize: { xs: '0.7rem', sm: '0.75rem' },
                // Minimum 44px height for touch targets (close to 48px requirement)
                minHeight: { xs: 44, sm: 36 },
                px: { xs: 1, sm: 1.5 },
                py: { xs: 0.75, sm: 0.5 },
                lineHeight: 1.2,
              }}
            >
              <Box
                component="span"
                aria-hidden="true"
                sx={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  bgcolor: metricConfig[key].color,
                  display: 'inline-block',
                  mr: 0.75,
                  flexShrink: 0,
                }}
              />
              {metricConfig[key].label}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
      </Box>

      {/* Responsive chart height: 220px on mobile, 300px on md+ */}
      <Box sx={{ height: { xs: 220, md: 300 } }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 4, right: showRightAxis ? 8 : 4, bottom: 4, left: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
            <XAxis
              dataKey="time"
              type="number"
              domain={['dataMin', 'dataMax']}
              tickFormatter={tickFormatter}
              tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
              stroke={theme.palette.divider}
            />
            {showLeftAxis && (
              <YAxis
                yAxisId="left"
                tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                width={42}
                domain={['auto', 'auto']}
                stroke={theme.palette.divider}
                label={{
                  value: 'pH',
                  angle: -90,
                  position: 'insideLeft',
                  offset: 8,
                  style: { fontSize: 11, fill: theme.palette.text.secondary },
                }}
              />
            )}
            {showRightAxis && (
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fontSize: 11, fill: theme.palette.text.secondary }}
                width={42}
                domain={['auto', 'auto']}
                stroke={theme.palette.divider}
              />
            )}
            <Tooltip
              content={<CustomTooltip />}
              allowEscapeViewBox={{ x: false, y: true }}
            />
            {visibleMetrics.map((key) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                yAxisId={metricConfig[key].yAxisId}
                stroke={metricConfig[key].color}
                strokeWidth={2}
                dot={{ r: 3, strokeWidth: 0 }}
                activeDot={{ r: 5 }}
                name={metricConfig[key].label}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </Box>
    </Box>
  );
}
