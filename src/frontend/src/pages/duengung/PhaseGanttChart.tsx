import React, { useState, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import { alpha, useTheme, type Theme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import IconButton from '@mui/material/IconButton';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import EditIcon from '@mui/icons-material/Edit';
import type { NutrientPlanPhaseEntry, Fertilizer, PhaseName } from '@/api/types';
import { MONTH_WEEK_SPANS, getShortMonthName } from '@/utils/weekCalculation';

/** Map week number (1-52) → month index for boundary detection. */
const weekToMonth = new Map<number, number>();
for (const ms of MONTH_WEEK_SPANS) {
  for (let w = ms.weekStart; w <= ms.weekEnd; w++) weekToMonth.set(w, ms.month);
}

export const PHASE_COLORS: Record<PhaseName, string> = {
  germination: '#8D6E63',
  seedling: '#66BB6A',
  vegetative: '#2E7D32',
  flowering: '#AB47BC',
  flushing: '#26C6DA',
  dormancy: '#78909C',
  harvest: '#FF8F00',
};

interface PhaseGanttChartProps {
  entries: NutrientPlanPhaseEntry[];
  fertilizers: Fertilizer[];
  currentWeek?: number;
  weekOffset?: number;
  title?: string;
  weekLabel?: string;
  totalWeeksOverride?: number;
  showMonthHeaders?: boolean;
  onPhaseClick?: (entryKey: string) => void;
  onEditEntry?: (entry: NutrientPlanPhaseEntry) => void;
  selectedPhaseKey?: string;
}

export default function PhaseGanttChart({ entries, fertilizers, currentWeek, weekOffset = 0, title, weekLabel, totalWeeksOverride, showMonthHeaders, onPhaseClick, onEditEntry, selectedPhaseKey }: PhaseGanttChartProps) {
  const { t, i18n } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [expandedPhases, setExpandedPhases] = useState<Set<string>>(new Set());

  const sorted = useMemo(
    () => [...entries].sort((a, b) => a.sequence_order - b.sequence_order),
    [entries],
  );

  const totalWeeks = useMemo(() => {
    if (totalWeeksOverride != null) return totalWeeksOverride;
    if (sorted.length === 0) return 0;
    return Math.max(...sorted.map((e) => e.week_end)) - weekOffset;
  }, [sorted, weekOffset, totalWeeksOverride]);

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

  // Build week → EC target map from delivery channels
  // null = phase exists but no EC target (hatched), number > 0 = show value
  const weekEcMap = useMemo(() => {
    const map = new Map<number, number | null>();
    const calSize = totalWeeksOverride ?? 52;
    const setWeeks = (ws: number, we: number, val: number | null) => {
      if (we <= calSize) {
        for (let w = ws; w <= we; w++) {
          const prev = map.get(w);
          // Real EC > 0 takes priority over null/0
          if (prev == null || (val != null && val > (prev ?? 0))) map.set(w, val);
        }
      } else {
        for (let w = ws; w <= calSize; w++) {
          const prev = map.get(w);
          if (prev == null || (val != null && val > (prev ?? 0))) map.set(w, val);
        }
        for (let w = 1; w <= we - calSize; w++) {
          const prev = map.get(w);
          if (prev == null || (val != null && val > (prev ?? 0))) map.set(w, val);
        }
      }
    };
    for (const entry of sorted) {
      const ecValues = entry.delivery_channels
        .filter((ch) => ch.target_ec_ms != null && ch.target_ec_ms > 0)
        .map((ch) => ch.target_ec_ms!);
      if (ecValues.length > 0) {
        setWeeks(entry.week_start, entry.week_end, Math.max(...ecValues));
      } else {
        // Phase has no real EC target → hatched
        setWeeks(entry.week_start, entry.week_end, null);
      }
    }
    return map;
  }, [sorted, totalWeeksOverride]);

  if (sorted.length === 0 || totalWeeks === 0) return null;

  const labelWidth = isMobile ? 100 : 140;
  const weeks = Array.from({ length: totalWeeks }, (_, i) => i + 1);

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {title ?? t('pages.gantt.title')}
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
            {showMonthHeaders ? (
              MONTH_WEEK_SPANS.map((ms) => {
                const isCurrent = currentWeek != null && currentWeek >= ms.weekStart && currentWeek <= ms.weekEnd;
                return (
                  <Box
                    key={ms.month}
                    role="columnheader"
                    sx={{
                      gridColumn: `span ${ms.span}`,
                      textAlign: 'center',
                      borderBottom: 1,
                      borderColor: 'divider',
                      borderLeft: ms.month > 0 ? 1 : 0,
                      py: 0.5,
                      ...(isCurrent && {
                        bgcolor: alpha(theme.palette.primary.main, 0.10),
                      }),
                    }}
                  >
                    <Typography
                      variant="caption"
                      color={isCurrent ? 'primary' : 'text.secondary'}
                      sx={isCurrent ? { fontWeight: 700 } : undefined}
                    >
                      {getShortMonthName(ms.month, i18n.language)}
                    </Typography>
                  </Box>
                );
              })
            ) : (
              weeks.map((w) => {
                const absWeek = w + weekOffset;
                return (
                  <Box
                    key={w}
                    role="columnheader"
                    sx={{
                      textAlign: 'center',
                      borderBottom: 1,
                      borderColor: 'divider',
                      py: 0.5,
                      ...(absWeek === currentWeek && {
                        bgcolor: alpha(theme.palette.primary.main, 0.10),
                      }),
                    }}
                  >
                    <Typography
                      variant="caption"
                      color={absWeek === currentWeek ? 'primary' : 'text.secondary'}
                      sx={absWeek === currentWeek ? { fontWeight: 700 } : undefined}
                    >
                      {weekLabel ?? t('pages.gantt.week')}{absWeek}
                    </Typography>
                  </Box>
                );
              })
            )}

            {/* EC target row */}
            {weekEcMap.size > 0 && (
              <>
                <Box
                  sx={{
                    position: 'sticky',
                    left: 0,
                    bgcolor: 'background.paper',
                    zIndex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    py: 0.5,
                    px: 0.5,
                    borderBottom: 1,
                    borderColor: 'divider',
                  }}
                >
                  <Typography variant="caption" noWrap sx={{ fontWeight: 600 }} color="text.secondary">
                    {t('pages.gantt.ecTarget')}
                  </Typography>
                </Box>
                {(() => {
                  // Build runs of consecutive weeks with same EC status, split at month boundaries
                  type EcRun = { startCol: number; span: number; type: 'empty' | 'hatched' | 'value'; ec: number };
                  const runs: EcRun[] = [];
                  const useMonthSnap = showMonthHeaders;
                  for (const w of weeks) {
                    const absWeek = w + weekOffset;
                    const hasWeek = weekEcMap.has(absWeek);
                    const ecVal = hasWeek ? weekEcMap.get(absWeek) : undefined;
                    const type: EcRun['type'] = hasWeek && (ecVal == null || ecVal === 0)
                      ? 'hatched'
                      : hasWeek && ecVal != null && ecVal > 0
                        ? 'value'
                        : 'empty';
                    const ec = (type === 'value' ? ecVal! : 0);
                    const prev = runs[runs.length - 1];
                    const monthBoundary = useMonthSnap && prev
                      && weekToMonth.get(absWeek) !== weekToMonth.get(absWeek - 1);
                    if (prev && prev.type === type && prev.ec === ec && !monthBoundary) {
                      prev.span += 1;
                    } else {
                      runs.push({ startCol: w + 1, span: 1, type, ec }); // +1 for label column
                    }
                  }
                  return runs.map((run) => (
                    <Box
                      key={run.startCol}
                      sx={{
                        gridColumn: `${run.startCol} / span ${run.span}`,
                        py: 0.5,
                        px: '2px',
                        borderBottom: 1,
                        borderColor: 'divider',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      {run.type === 'hatched' && (
                        <Box
                          sx={{
                            width: '100%',
                            height: 20,
                            bgcolor: alpha(theme.palette.warning.main, 0.10),
                            borderRadius: 1,
                            backgroundImage: `repeating-linear-gradient(
                              45deg,
                              transparent,
                              transparent 3px,
                              ${alpha(theme.palette.warning.main, 0.15)} 3px,
                              ${alpha(theme.palette.warning.main, 0.15)} 6px
                            )`,
                          }}
                        />
                      )}
                      {run.type === 'value' && (
                        <Box
                          sx={{
                            width: '100%',
                            height: 20,
                            bgcolor: alpha(theme.palette.warning.main, 0.15),
                            borderRadius: 1,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          <Typography
                            variant="caption"
                            sx={{ fontSize: '0.6rem', fontWeight: 600, lineHeight: 1 }}
                            color="warning.dark"
                          >
                            {run.ec}
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  ));
                })()}
              </>
            )}

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
                  weekOffset={weekOffset}
                  weekLabel={weekLabel}
                  onPhaseClick={onPhaseClick}
                  onEditEntry={onEditEntry}
                  isSelected={selectedPhaseKey === entry.key}
                  monthSnap={showMonthHeaders}
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
  weekOffset = 0,
  weekLabel,
  onPhaseClick,
  onEditEntry,
  isSelected,
  monthSnap,
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
  weekOffset?: number;
  weekLabel?: string;
  onPhaseClick?: (entryKey: string) => void;
  onEditEntry?: (entry: NutrientPlanPhaseEntry) => void;
  isSelected?: boolean;
  monthSnap?: boolean;
}) {
  const phaseLabel = t(`enums.phaseName.${entry.phase_name}`);
  const npkStr = entry.npk_ratio.join('-');
  const channelCount = entry.delivery_channels.length;

  // EC target from delivery channels
  const ecValues = entry.delivery_channels
    .filter((ch) => ch.target_ec_ms != null)
    .map((ch) => ch.target_ec_ms!);
  const ecUnique = [...new Set(ecValues)];
  const ecLabel = ecUnique.length === 1
    ? `EC ${ecUnique[0]}`
    : ecUnique.length > 1
      ? `EC ${Math.min(...ecUnique)}–${Math.max(...ecUnique)}`
      : null;

  // Detect year-boundary wrap: week_end > totalWeeks means the phase wraps around
  const wraps = entry.week_end > totalWeeks + weekOffset;
  const wrapEnd = wraps ? entry.week_end - totalWeeks : 0;

  const wPrefix = weekLabel ?? t('pages.gantt.week');
  const displayEnd = wraps ? wrapEnd : entry.week_end;
  const phaseTooltip = [
    phaseLabel,
    wraps
      ? `${wPrefix}${entry.week_start}–${wPrefix}${displayEnd} (${duration})`
      : `${wPrefix}${entry.week_start}–${entry.week_end} (${duration})`,
    `NPK: ${npkStr}`,
    ecLabel ? `${ecLabel} mS/cm` : null,
    t('pages.gantt.channels', { count: channelCount }),
  ].filter(Boolean).join('\n');

  return (
    <>
      {/* Phase label cell */}
      <Box
        role="button"
        tabIndex={0}
        aria-expanded={hasChannels ? isExpanded : undefined}
        aria-label={phaseLabel}
        onClick={() => {
          if (onPhaseClick) onPhaseClick(entry.key);
          else if (hasChannels) onToggle(entry.key);
        }}
        onKeyDown={(e: React.KeyboardEvent) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            if (onPhaseClick) onPhaseClick(entry.key);
            else if (hasChannels) onToggle(entry.key);
          }
        }}
        sx={{
          position: 'sticky',
          left: 0,
          bgcolor: isSelected ? alpha(color, 0.08) : 'background.paper',
          zIndex: 1,
          display: 'flex',
          alignItems: 'center',
          gap: 0.5,
          py: 0.5,
          px: 0.5,
          cursor: 'pointer',
          borderBottom: 1,
          borderColor: 'divider',
          borderLeft: isSelected ? `3px solid ${color}` : '3px solid transparent',
          transition: 'background-color 0.2s, border-color 0.2s',
          '&:hover': { bgcolor: alpha(color, 0.12) },
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
        <Box sx={{ minWidth: 0, flex: 1 }}>
          <Typography
            variant="body2"
            noWrap
            sx={{
              fontWeight: 600,
              maxWidth: labelWidth - (onEditEntry ? 56 : 30),
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
            {wPrefix}{entry.week_start}–{wraps ? displayEnd : entry.week_end}
            {ecLabel && <> · {ecLabel}</>}
          </Typography>
        </Box>
        {onEditEntry && (
          <Tooltip title={t('common.edit')} arrow>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onEditEntry(entry);
              }}
              sx={{
                flexShrink: 0,
                p: 0.25,
                opacity: 0.6,
                '&:hover': { opacity: 1 },
              }}
            >
              <EditIcon sx={{ fontSize: 14 }} />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      {/* Phase bar cells — merged into contiguous blocks */}
      {(() => {
        type PhaseRun = { startCol: number; span: number; inRange: boolean; isStart: boolean; isEnd: boolean };
        const runs: PhaseRun[] = [];
        const allWeeks = Array.from({ length: totalWeeks }, (_, i) => i + 1);
        for (const w of allWeeks) {
          const absWeek = w + weekOffset;
          const inNormalRange = absWeek >= entry.week_start && absWeek <= entry.week_end;
          const inWrapRange = wraps && absWeek >= 1 + weekOffset && absWeek <= wrapEnd + weekOffset;
          const inRange = inNormalRange || inWrapRange;
          const isStart = absWeek === entry.week_start || (inWrapRange && absWeek === 1 + weekOffset);
          const isEnd = (!wraps && absWeek === entry.week_end)
            || (wraps && absWeek === totalWeeks + weekOffset && inNormalRange)
            || (wraps && absWeek === wrapEnd + weekOffset && inWrapRange);
          const prev = runs[runs.length - 1];
          const mb = monthSnap && prev
            && weekToMonth.get(absWeek) !== weekToMonth.get(absWeek - 1);
          if (prev && prev.inRange === inRange && inRange && !isStart && !mb) {
            prev.span += 1;
            prev.isEnd = isEnd;
          } else if (prev && !prev.inRange && !inRange && !mb) {
            prev.span += 1;
          } else {
            runs.push({ startCol: w + 1, span: 1, inRange, isStart, isEnd }); // +1 for label column
          }
        }
        return runs.map((run) => (
          <Box
            key={run.startCol}
            sx={{
              gridColumn: `${run.startCol} / span ${run.span}`,
              py: 0.75,
              px: '2px',
              borderBottom: 1,
              borderColor: 'divider',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            {run.inRange && (
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
                    borderRadius: `${run.isStart ? 4 : 0}px ${run.isEnd ? 4 : 0}px ${run.isEnd ? 4 : 0}px ${run.isStart ? 4 : 0}px`,
                  }}
                />
              </Tooltip>
            )}
          </Box>
        ));
      })()}

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
            weekOffset={weekOffset}
            monthSnap={monthSnap}
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
  weekOffset = 0,
  monthSnap,
}: {
  channel: NutrientPlanPhaseEntry['delivery_channels'][number];
  entry: NutrientPlanPhaseEntry;
  color: string;
  totalWeeks: number;
  labelWidth: number;
  getFertilizerName: (key: string) => string;
  t: (key: string, opts?: Record<string, unknown>) => string;
  theme: Theme;
  weekOffset?: number;
  monthSnap?: boolean;
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

      {/* Channel bar cells — merged into contiguous blocks */}
      {(() => {
        const wrapsChannel = entry.week_end > totalWeeks + weekOffset;
        const wrapEndChannel = wrapsChannel ? entry.week_end - totalWeeks : 0;
        const dosageTexts = channel.fertilizer_dosages
          .map((d) => `${d.ml_per_liter} ml/L`)
          .join(' · ');

        type ChRun = { startCol: number; span: number; inRange: boolean; isStart: boolean; isEnd: boolean };
        const runs: ChRun[] = [];
        for (const w of weekCells) {
          const absWeek = w + weekOffset;
          const inNormal = absWeek >= entry.week_start && absWeek <= entry.week_end;
          const inWrap = wrapsChannel && absWeek >= 1 + weekOffset && absWeek <= wrapEndChannel + weekOffset;
          const inRange = inNormal || inWrap;
          const isStart = absWeek === entry.week_start || (inWrap && absWeek === 1 + weekOffset);
          const isEnd = (!wrapsChannel && absWeek === entry.week_end)
            || (wrapsChannel && absWeek === totalWeeks + weekOffset && inNormal)
            || (wrapsChannel && absWeek === wrapEndChannel + weekOffset && inWrap);
          const prev = runs[runs.length - 1];
          const mb = monthSnap && prev
            && weekToMonth.get(absWeek) !== weekToMonth.get(absWeek - 1);
          if (prev && prev.inRange === inRange && inRange && !isStart && !mb) {
            prev.span += 1;
            prev.isEnd = isEnd;
          } else if (prev && !prev.inRange && !inRange && !mb) {
            prev.span += 1;
          } else {
            runs.push({ startCol: w + 1, span: 1, inRange, isStart, isEnd });
          }
        }
        return runs.map((run) => (
          <Box
            key={run.startCol}
            sx={{
              gridColumn: `${run.startCol} / span ${run.span}`,
              py: 0.5,
              px: '2px',
              borderBottom: 1,
              borderColor: theme.palette.divider,
              display: 'flex',
              alignItems: 'center',
            }}
          >
            {run.inRange && (
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
                    height: 18,
                    bgcolor: alpha(color, 0.4),
                    borderRadius: `${run.isStart ? 3 : 0}px ${run.isEnd ? 3 : 0}px ${run.isEnd ? 3 : 0}px ${run.isStart ? 3 : 0}px`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {dosageTexts && (
                    <Typography
                      variant="caption"
                      sx={{
                        fontSize: '0.5rem',
                        fontWeight: 600,
                        lineHeight: 1,
                        color: 'text.primary',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {dosageTexts}
                    </Typography>
                  )}
                </Box>
              </Tooltip>
            )}
          </Box>
        ));
      })()}

    </>
  );
}
