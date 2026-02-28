import { useState, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import { alpha, useTheme, type Theme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import type { NutrientPlanPhaseEntry, Fertilizer, PhaseName } from '@/api/types';

const PHASE_COLORS: Record<PhaseName, string> = {
  germination: '#8D6E63',
  seedling: '#66BB6A',
  vegetative: '#2E7D32',
  flowering: '#AB47BC',
  harvest: '#FF8F00',
};

interface PhaseGanttChartProps {
  entries: NutrientPlanPhaseEntry[];
  fertilizers: Fertilizer[];
}

export default function PhaseGanttChart({ entries, fertilizers }: PhaseGanttChartProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set());

  const sorted = useMemo(
    () => [...entries].sort((a, b) => a.sequence_order - b.sequence_order),
    [entries],
  );

  const totalWeeks = useMemo(() => {
    if (sorted.length === 0) return 0;
    return Math.max(...sorted.map((e) => e.week_end));
  }, [sorted]);

  const togglePhase = useCallback((key: string) => {
    setExpandedPhases((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }, []);

  const getFertilizerName = useCallback(
    (fertKey: string): string => {
      const f = fertilizers.find((fert) => fert.key === fertKey);
      return f ? `${f.product_name} (${f.brand})` : fertKey;
    },
    [fertilizers],
  );

  if (sorted.length === 0 || totalWeeks === 0) return null;

  const labelWidth = isMobile ? 100 : 140;
  const weeks = Array.from({ length: totalWeeks }, (_, i) => i + 1);

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {t('pages.gantt.title')}
        </Typography>

        <Box sx={{ overflowX: 'auto' }}>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: `${labelWidth}px repeat(${totalWeeks}, 1fr)`,
              minWidth: labelWidth + totalWeeks * 32,
              gap: 0,
            }}
          >
            {/* Header row */}
            <Box
              sx={{
                position: 'sticky',
                left: 0,
                bgcolor: 'background.paper',
                zIndex: 1,
                borderBottom: 1,
                borderColor: 'divider',
                py: 0.5,
              }}
            />
            {weeks.map((w) => (
              <Box
                key={w}
                role="columnheader"
                sx={{
                  textAlign: 'center',
                  borderBottom: 1,
                  borderColor: 'divider',
                  py: 0.5,
                }}
              >
                <Typography variant="caption" color="text.secondary">
                  {t('pages.gantt.week')}{w}
                </Typography>
              </Box>
            ))}

            {/* Phase rows */}
            {sorted.map((entry) => {
              const color = PHASE_COLORS[entry.phase_name] ?? theme.palette.grey[600];
              const isExpanded = expandedPhases.has(entry.key);
              const hasChannels = entry.delivery_channels.length > 0;
              const duration = entry.week_end - entry.week_start + 1;

              return (
                <PhaseRow
                  key={entry.key}
                  entry={entry}
                  color={color}
                  isExpanded={isExpanded}
                  hasChannels={hasChannels}
                  duration={duration}
                  totalWeeks={totalWeeks}
                  labelWidth={labelWidth}
                  onToggle={togglePhase}
                  getFertilizerName={getFertilizerName}
                  t={t}
                  theme={theme}
                />
              );
            })}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

function PhaseRow({
  entry,
  color,
  isExpanded,
  hasChannels,
  duration,
  totalWeeks,
  labelWidth,
  onToggle,
  getFertilizerName,
  t,
  theme,
}: {
  entry: NutrientPlanPhaseEntry;
  color: string;
  isExpanded: boolean;
  hasChannels: boolean;
  duration: number;
  totalWeeks: number;
  labelWidth: number;
  onToggle: (key: string) => void;
  getFertilizerName: (key: string) => string;
  t: (key: string, opts?: Record<string, unknown>) => string;
  theme: Theme;
}) {
  const phaseLabel = t(`enums.phaseName.${entry.phase_name}`);
  const npkStr = entry.npk_ratio.join('-');
  const channelCount = entry.delivery_channels.length;

  const phaseTooltip = [
    phaseLabel,
    `${t('pages.gantt.week')}${entry.week_start}–${entry.week_end} (${duration})`,
    `NPK: ${npkStr}`,
    t('pages.gantt.channels', { count: channelCount }),
  ].join('\n');

  return (
    <>
      {/* Phase label cell */}
      <Box
        role="button"
        tabIndex={hasChannels ? 0 : undefined}
        aria-expanded={hasChannels ? isExpanded : undefined}
        aria-label={hasChannels ? (isExpanded ? t('pages.gantt.collapsePhase') : t('pages.gantt.expandPhase')) : phaseLabel}
        onClick={hasChannels ? () => onToggle(entry.key) : undefined}
        onKeyDown={hasChannels ? (e: React.KeyboardEvent) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onToggle(entry.key);
          }
        } : undefined}
        sx={{
          position: 'sticky',
          left: 0,
          bgcolor: 'background.paper',
          zIndex: 1,
          display: 'flex',
          alignItems: 'center',
          gap: 0.5,
          py: 0.5,
          px: 0.5,
          cursor: hasChannels ? 'pointer' : 'default',
          borderBottom: 1,
          borderColor: 'divider',
          '&:hover': hasChannels ? { bgcolor: 'action.hover' } : undefined,
          '&:focus-visible': {
            outline: `2px solid ${theme.palette.primary.main}`,
            outlineOffset: -2,
          },
        }}
      >
        {hasChannels && (
          isExpanded
            ? <ExpandLessIcon sx={{ fontSize: 16, color: 'text.secondary', flexShrink: 0 }} />
            : <ExpandMoreIcon sx={{ fontSize: 16, color: 'text.secondary', flexShrink: 0 }} />
        )}
        <Box sx={{ minWidth: 0 }}>
          <Typography
            variant="body2"
            noWrap
            sx={{
              fontWeight: 600,
              maxWidth: labelWidth - 30,
            }}
          >
            {phaseLabel}
          </Typography>
          <Typography
            variant="caption"
            noWrap
            color="text.secondary"
            sx={{ lineHeight: 1.2 }}
          >
            {t('pages.gantt.week')}{entry.week_start}–{entry.week_end}
          </Typography>
        </Box>
      </Box>

      {/* Phase bar cells */}
      {Array.from({ length: totalWeeks }, (_, i) => i + 1).map((w) => {
        const inRange = w >= entry.week_start && w <= entry.week_end;
        const isStart = w === entry.week_start;
        const isEnd = w === entry.week_end;
        return (
          <Box
            key={w}
            sx={{
              py: 0.75,
              px: '2px',
              borderBottom: 1,
              borderColor: 'divider',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            {inRange && (
              <Tooltip
                title={
                  <Box sx={{ whiteSpace: 'pre-line' }}>
                    {phaseTooltip}
                  </Box>
                }
                arrow
              >
                <Box
                  sx={{
                    width: '100%',
                    height: 24,
                    bgcolor: alpha(color, 0.85),
                    borderRadius: `${isStart ? 4 : 0}px ${isEnd ? 4 : 0}px ${isEnd ? 4 : 0}px ${isStart ? 4 : 0}px`,
                  }}
                />
              </Tooltip>
            )}
          </Box>
        );
      })}

      {/* Expanded channel sub-rows */}
      {isExpanded &&
        entry.delivery_channels.map((ch) => (
          <ChannelSubRow
            key={ch.channel_id}
            channel={ch}
            entry={entry}
            color={color}
            totalWeeks={totalWeeks}
            labelWidth={labelWidth}
            getFertilizerName={getFertilizerName}
            t={t}
            theme={theme}
          />
        ))}
    </>
  );
}

function ChannelSubRow({
  channel,
  entry,
  color,
  totalWeeks,
  labelWidth,
  getFertilizerName,
  t,
  theme,
}: {
  channel: NutrientPlanPhaseEntry['delivery_channels'][number];
  entry: NutrientPlanPhaseEntry;
  color: string;
  totalWeeks: number;
  labelWidth: number;
  getFertilizerName: (key: string) => string;
  t: (key: string, opts?: Record<string, unknown>) => string;
  theme: Theme;
}) {
  const methodLabel = t(`enums.applicationMethod.${channel.application_method}`);
  const fertList = channel.fertilizer_dosages
    .map((d) => `${getFertilizerName(d.fertilizer_key)}: ${d.ml_per_liter} ml/L`)
    .join('\n');

  const channelTooltip = [
    channel.label || channel.channel_id,
    methodLabel,
    channel.target_ec_ms != null ? `EC: ${channel.target_ec_ms} mS` : null,
    channel.target_ph != null ? `pH: ${channel.target_ph}` : null,
    fertList || null,
  ]
    .filter(Boolean)
    .join('\n');

  const weekCells = Array.from({ length: totalWeeks }, (_, i) => i + 1);

  return (
    <>
      {/* Channel label */}
      <Box
        sx={{
          position: 'sticky',
          left: 0,
          bgcolor: 'background.paper',
          zIndex: 1,
          display: 'flex',
          alignItems: 'center',
          py: 0.5,
          pl: 3,
          pr: 0.5,
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        <Typography
          variant="caption"
          noWrap
          color="text.secondary"
          sx={{ maxWidth: labelWidth - 30, fontStyle: 'italic' }}
        >
          {channel.label || channel.channel_id}
        </Typography>
      </Box>

      {/* Channel bar cells */}
      {weekCells.map((w) => {
        const inRange = w >= entry.week_start && w <= entry.week_end;
        const isStart = w === entry.week_start;
        const isEnd = w === entry.week_end;
        return (
          <Box
            key={w}
            sx={{
              py: 0.5,
              px: '2px',
              borderBottom: 1,
              borderColor: theme.palette.divider,
              display: 'flex',
              alignItems: 'center',
            }}
          >
            {inRange && (
              <Tooltip
                title={
                  <Box sx={{ whiteSpace: 'pre-line' }}>
                    {channelTooltip}
                  </Box>
                }
                arrow
              >
                <Box
                  sx={{
                    width: '100%',
                    height: 16,
                    bgcolor: alpha(color, 0.4),
                    borderRadius: `${isStart ? 3 : 0}px ${isEnd ? 3 : 0}px ${isEnd ? 3 : 0}px ${isStart ? 3 : 0}px`,
                  }}
                />
              </Tooltip>
            )}
          </Box>
        );
      })}

    </>
  );
}
