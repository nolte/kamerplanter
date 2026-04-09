import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Alert from '@mui/material/Alert';
import Skeleton from '@mui/material/Skeleton';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Typography from '@mui/material/Typography';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import dayjs from 'dayjs';
import * as observationsApi from '@/api/endpoints/observations';
import type {
  SensorReadingResponse,
  AggregatedReadingResponse,
} from '@/api/types';

type TimeRange = '24h' | '7d' | '30d' | '90d';

interface SensorHistoryChartProps {
  sensorKey: string;
  sensorName: string;
  metricType: string;
  unit?: string | null;
}

interface ChartDataPoint {
  time: number;
  value: number;
  min?: number;
  max?: number;
}

const RANGE_CONFIG: Record<TimeRange, { hours: number; resolution: 'raw' | 'hourly' | 'daily' }> = {
  '24h': { hours: 24, resolution: 'raw' },
  '7d': { hours: 168, resolution: 'hourly' },
  '30d': { hours: 720, resolution: 'daily' },
  '90d': { hours: 2160, resolution: 'daily' },
};

const METRIC_COLORS: Record<string, string> = {
  ph: '#4caf50',
  ec_ms: '#ff9800',
  water_temp_celsius: '#2196f3',
  temperature_celsius: '#f44336',
  humidity_percent: '#9c27b0',
  fill_level_percent: '#00bcd4',
  co2_ppm: '#795548',
  vpd_kpa: '#607d8b',
  ppfd: '#ffc107',
  tds_ppm: '#ff5722',
  dissolved_oxygen_mgl: '#03a9f4',
  orp_mv: '#8bc34a',
};

function isAggregated(item: SensorReadingResponse | AggregatedReadingResponse): item is AggregatedReadingResponse {
  return 'bucket' in item;
}

function formatTime(ts: number, range: TimeRange): string {
  const d = dayjs(ts);
  if (range === '24h') return d.format('HH:mm');
  if (range === '7d') return d.format('dd HH:mm');
  return d.format('DD.MM.');
}

interface TooltipPayloadEntry {
  dataKey?: string | number;
  name?: string;
  value?: number;
  color?: string;
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: TooltipPayloadEntry[]; label?: number }) {
  if (!active || !payload?.length) return null;
  const d = dayjs(label);
  return (
    <Box sx={{ bgcolor: 'background.paper', border: 1, borderColor: 'divider', borderRadius: 1, p: 1, fontSize: '0.8rem' }}>
      <Typography variant="caption" sx={{ display: 'block', mb: 0.5 }}>
        {d.format('DD.MM.YYYY HH:mm')}
      </Typography>
      {payload.map((p) => (
        <Box key={String(p.dataKey)} sx={{ color: p.color }}>
          {p.name}: {typeof p.value === 'number' ? p.value.toFixed(2) : p.value}
        </Box>
      ))}
    </Box>
  );
}

export default function SensorHistoryChart({ sensorKey, sensorName, metricType, unit }: SensorHistoryChartProps) {
  const { t } = useTranslation();
  const [range, setRange] = useState<TimeRange>('24h');
  const [data, setData] = useState<ChartDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [aggregated, setAggregated] = useState(false);

  const color = METRIC_COLORS[metricType] ?? '#1976d2';

  const fetchData = useCallback(async (r: TimeRange) => {
    setLoading(true);
    setError(null);
    try {
      const config = RANGE_CONFIG[r];
      const end = dayjs().toISOString();
      const start = dayjs().subtract(config.hours, 'hour').toISOString();
      const resp = await observationsApi.getSensorReadings(sensorKey, start, end, config.resolution);

      const isAgg = resp.resolution !== 'raw';
      setAggregated(isAgg);

      const points: ChartDataPoint[] = resp.items.map((item) => {
        if (isAggregated(item)) {
          return {
            time: dayjs(item.bucket).valueOf(),
            value: item.avg_value,
            min: item.min_value,
            max: item.max_value,
          };
        }
        return {
          time: dayjs(item.time).valueOf(),
          value: item.value,
        };
      });
      points.sort((a, b) => a.time - b.time);
      setData(points);
    } catch {
      setError(t('sensorChart.loadError'));
    } finally {
      setLoading(false);
    }
  }, [sensorKey, t]);

  useEffect(() => {
    fetchData(range);
  }, [range, fetchData]);

  const yLabel = unit ?? metricType;

  const tickFormatter = useMemo(() => (ts: number) => formatTime(ts, range), [range]);

  return (
    <Box sx={{ mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="subtitle2">
          {sensorName} ({yLabel})
        </Typography>
        <ToggleButtonGroup
          value={range}
          exclusive
          onChange={(_, v) => { if (v) setRange(v as TimeRange); }}
          size="small"
        >
          <ToggleButton value="24h">24h</ToggleButton>
          <ToggleButton value="7d">7d</ToggleButton>
          <ToggleButton value="30d">30d</ToggleButton>
          <ToggleButton value="90d">90d</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {loading && <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 1 }} />}

      {error && <Alert severity="error" sx={{ mb: 1 }}>{error}</Alert>}

      {!loading && !error && data.length === 0 && (
        <Alert severity="info">{t('sensorChart.noData')}</Alert>
      )}

      {!loading && !error && data.length > 0 && (
        <ResponsiveContainer width="100%" height={200}>
          {aggregated ? (
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                type="number"
                domain={['dataMin', 'dataMax']}
                tickFormatter={tickFormatter}
                tick={{ fontSize: 11 }}
              />
              <YAxis
                tick={{ fontSize: 11 }}
                width={50}
                domain={['auto', 'auto']}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="max"
                stroke="none"
                fill={color}
                fillOpacity={0.1}
                name="Max"
              />
              <Area
                type="monotone"
                dataKey="min"
                stroke="none"
                fill={color}
                fillOpacity={0.1}
                name="Min"
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke={color}
                fill={color}
                fillOpacity={0.2}
                strokeWidth={2}
                name={yLabel}
              />
            </AreaChart>
          ) : (
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                type="number"
                domain={['dataMin', 'dataMax']}
                tickFormatter={tickFormatter}
                tick={{ fontSize: 11 }}
              />
              <YAxis
                tick={{ fontSize: 11 }}
                width={50}
                domain={['auto', 'auto']}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="value"
                stroke={color}
                strokeWidth={2}
                dot={false}
                name={yLabel}
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      )}
    </Box>
  );
}
