import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import IconButton from '@mui/material/IconButton';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import { alpha, useTheme, type Theme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import Chip from '@mui/material/Chip';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SaveIcon from '@mui/icons-material/Save';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/species';
import type { GrowingPeriod, Species } from '@/api/types';

const MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
const CELL_MIN_W = 40;
const BAR_H = 20;
const ROW_H = 32;

type BarKind = 'sow' | 'growth' | 'harvest' | 'bloom';

const BAR_COLORS: Record<BarKind, string> = {
  sow: '#66BB6A',
  growth: '#42A5F5',
  harvest: '#FF8F00',
  bloom: '#AB47BC',
};

function emptyPeriod(): GrowingPeriod {
  return {
    label: '',
    sowing_indoor_weeks_before_last_frost: null,
    sowing_outdoor_after_last_frost_days: null,
    direct_sow_months: [],
    growth_months: [],
    harvest_months: [],
    bloom_months: [],
    harvest_from_year: null,
    bloom_from_year: null,
  };
}

function monthsToRanges(months: number[]): [number, number][] {
  if (months.length === 0) return [];
  const sorted = [...months].sort((a, b) => a - b);
  const ranges: [number, number][] = [];
  let start = sorted[0];
  let end = sorted[0];
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i] === end + 1) {
      end = sorted[i];
    } else {
      ranges.push([start, end]);
      start = sorted[i];
      end = sorted[i];
    }
  }
  ranges.push([start, end]);
  return ranges;
}

function rangesToMonths(ranges: [number, number][]): number[] {
  const months = new Set<number>();
  for (const [start, end] of ranges) {
    for (let m = start; m <= end; m++) {
      months.add(m);
    }
  }
  return [...months].sort((a, b) => a - b);
}

// ── Computed timeline (mirrors SowingCalendarEngine) ─────────────────

type TimelinePhase = 'indoor_sowing' | 'outdoor_planting' | 'growth' | 'harvest' | 'flowering';

interface TimelineBar {
  phase: TimelinePhase;
  startMonth: number;
  endMonth: number;
  fromYear: number | null;
}

const TIMELINE_COLORS: Record<TimelinePhase, string> = {
  indoor_sowing: '#FDD835',
  outdoor_planting: '#66BB6A',
  growth: '#42A5F5',
  harvest: '#FFA726',
  flowering: '#EC407A',
};

const DEFAULT_LAST_FROST_MONTH = 5; // May

function computeTimeline(period: GrowingPeriod, isOrnamental: boolean): TimelineBar[] {
  const bars: TimelineBar[] = [];

  // 1. Indoor sowing (Voranzucht)
  let indoorEndMonth: number | null = null;
  if (period.sowing_indoor_weeks_before_last_frost != null) {
    const weeksBack = period.sowing_indoor_weeks_before_last_frost;
    const monthsBack = Math.ceil(weeksBack / 4.33);
    const startMonth = Math.max(1, DEFAULT_LAST_FROST_MONTH - monthsBack);
    const endMonth = DEFAULT_LAST_FROST_MONTH - 1;
    if (endMonth >= startMonth) {
      bars.push({ phase: 'indoor_sowing', startMonth, endMonth, fromYear: null });
      indoorEndMonth = endMonth;
    }
  }

  // 2. Outdoor planting (Direktsaat)
  if (period.direct_sow_months.length > 0) {
    for (const [s, e] of monthsToRanges(period.direct_sow_months)) {
      const start = indoorEndMonth != null && s <= indoorEndMonth ? indoorEndMonth + 1 : s;
      if (start > e) continue;
      bars.push({ phase: 'outdoor_planting', startMonth: start, endMonth: e, fromYear: null });
    }
  } else if (period.sowing_outdoor_after_last_frost_days != null) {
    const startMonth = DEFAULT_LAST_FROST_MONTH;
    bars.push({ phase: 'outdoor_planting', startMonth, endMonth: startMonth, fromYear: null });
  }

  // 3. Terminal phase (harvest or flowering)
  const terminalMonths = isOrnamental && period.bloom_months.length > 0
    ? period.bloom_months
    : period.harvest_months;
  const terminalPhase: TimelinePhase = isOrnamental && period.bloom_months.length > 0
    ? 'flowering' : 'harvest';
  const terminalFromYear = isOrnamental && period.bloom_months.length > 0
    ? (period.bloom_from_year ?? null)
    : (period.harvest_from_year ?? null);

  // Build occupied-months set for sowing to use in terminal clipping
  const sowBars = bars.filter((b) => b.phase === 'indoor_sowing' || b.phase === 'outdoor_planting');

  if (terminalMonths.length > 0) {
    for (const [s, e] of monthsToRanges(terminalMonths)) {
      let start = s;
      // Clip terminal start to after the sowing range it overlaps with.
      // Year-crossing exception: if terminal range is entirely before the
      // sowing range (e.g. harvest Jun-Aug, sow Oct-Nov), keep as-is.
      for (const sow of sowBars) {
        if (start >= sow.startMonth && start <= sow.endMonth && e > sow.endMonth) {
          start = sow.endMonth + 1;
        }
      }
      if (start > e) continue;
      bars.push({ phase: terminalPhase, startMonth: start, endMonth: e, fromYear: terminalFromYear });
    }
  }

  // 4. Growth — explicit growth_months preferred, otherwise circular per-range gap-fill
  if (period.growth_months.length > 0) {
    for (const [s, e] of monthsToRanges(period.growth_months)) {
      bars.push({ phase: 'growth', startMonth: s, endMonth: e, fromYear: null });
    }
  } else {
    const termBars = bars.filter((b) => b.phase === 'harvest' || b.phase === 'flowering');

    if (sowBars.length > 0 && termBars.length > 0) {
      // Build set of months occupied by sowing or terminal bars
      const occupied = new Set<number>();
      for (const bar of [...sowBars, ...termBars]) {
        for (let m = bar.startMonth; m <= bar.endMonth; m++) occupied.add(m);
      }

      // For each sowing bar, trace forward circularly until hitting an
      // occupied month (terminal or another sow range). Unoccupied months
      // in between become growth. This handles year-crossing naturally.
      const growthSet = new Set<number>();
      for (const sow of sowBars) {
        for (let offset = 1; offset <= 11; offset++) {
          const m = ((sow.endMonth - 1 + offset) % 12) + 1;
          if (occupied.has(m)) break;
          growthSet.add(m);
        }
      }

      // Convert collected growth months to ranges
      const sortedGrowth = [...growthSet].sort((a, b) => a - b);
      for (const [s, e] of monthsToRanges(sortedGrowth)) {
        bars.push({ phase: 'growth', startMonth: s, endMonth: e, fromYear: null });
      }
    }

    // 4-fallback: No sowing bars but terminal bars exist (indoor ornamentals).
    // Fill all non-terminal months with growth.
    if (sowBars.length === 0 && termBars.length > 0) {
      const terminalSet = new Set<number>();
      for (const bar of termBars) {
        for (let m = bar.startMonth; m <= bar.endMonth; m++) terminalSet.add(m);
      }
      const growthMonths: number[] = [];
      for (let m = 1; m <= 12; m++) {
        if (!terminalSet.has(m)) growthMonths.push(m);
      }
      for (const [s, e] of monthsToRanges(growthMonths)) {
        bars.push({ phase: 'growth', startMonth: s, endMonth: e, fromYear: null });
      }
    }
  }

  // Also show bloom for non-ornamental if bloom_months exist and we used harvest as terminal
  if (!isOrnamental && period.bloom_months.length > 0) {
    for (const [s, e] of monthsToRanges(period.bloom_months)) {
      bars.push({ phase: 'flowering', startMonth: s, endMonth: e, fromYear: period.bloom_from_year ?? null });
    }
  }

  return bars;
}

interface DragState {
  periodIdx: number;
  kind: BarKind;
  rangeIdx: number;
  edge: 'start' | 'end';
  originMonth: number;
}

interface Props {
  speciesKey: string;
  species: Species;
  onSaved?: () => void;
}

export default function GrowingPeriodsSection({ speciesKey, species, onSaved }: Props) {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const notification = useNotification();
  const { handleError } = useApiError();
  const [periods, setPeriods] = useState<GrowingPeriod[]>([]);
  const [saving, setSaving] = useState(false);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const [dragState, setDragState] = useState<DragState | null>(null);

  const isOrnamental = !species.allows_harvest;
  const currentMonth = new Date().getMonth() + 1;

  // Computed timeline bars (mirrors SowingCalendarEngine)
  const timelineBars = useMemo(() => {
    if (periods.length === 0) return [];
    return periods.flatMap((p, i) =>
      computeTimeline(p, isOrnamental).map((b) => ({ ...b, periodIdx: i })),
    );
  }, [periods, isOrnamental]);

  useEffect(() => {
    if (species.growing_periods?.length) {
      setPeriods([...species.growing_periods]);
    } else {
      // Fallback: synthesize a period from legacy flat fields (same logic as SowingCalendarEngine)
      const hasLegacy =
        species.sowing_indoor_weeks_before_last_frost != null ||
        species.sowing_outdoor_after_last_frost_days != null ||
        (species.direct_sow_months?.length ?? 0) > 0 ||
        (species.harvest_months?.length ?? 0) > 0 ||
        (species.bloom_months?.length ?? 0) > 0;
      if (hasLegacy) {
        setPeriods([{
          label: '',
          sowing_indoor_weeks_before_last_frost: species.sowing_indoor_weeks_before_last_frost ?? null,
          sowing_outdoor_after_last_frost_days: species.sowing_outdoor_after_last_frost_days ?? null,
          direct_sow_months: species.direct_sow_months ?? [],
          growth_months: [],
          harvest_months: species.harvest_months ?? [],
          bloom_months: species.bloom_months ?? [],
          harvest_from_year: species.harvest_from_year ?? null,
          bloom_from_year: species.bloom_from_year ?? null,
        }]);
      } else {
        setPeriods([]);
      }
    }
  }, [species]);

  const handleChange = useCallback((index: number, period: GrowingPeriod) => {
    setPeriods((prev) => prev.map((p, i) => (i === index ? period : p)));
  }, []);

  const handleDelete = useCallback((index: number) => {
    setPeriods((prev) => prev.filter((_, i) => i !== index));
    setExpandedIdx(null);
  }, []);

  const handleAdd = useCallback(() => {
    setPeriods((prev) => [...prev, emptyPeriod()]);
    setExpandedIdx(periods.length);
  }, [periods.length]);

  const handleSave = async () => {
    try {
      setSaving(true);
      await api.updateSpecies(speciesKey, {
        scientific_name: species.scientific_name,
        growing_periods: periods,
      });
      notification.success(t('common.save'));
      onSaved?.();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const getBarKinds = useCallback(
    (): BarKind[] => ['sow', 'growth', 'harvest', 'bloom'],
    [],
  );

  const getMonthsForKind = useCallback(
    (period: GrowingPeriod, kind: BarKind): number[] => {
      switch (kind) {
        case 'sow': return period.direct_sow_months;
        case 'growth': return period.growth_months;
        case 'harvest': return period.harvest_months;
        case 'bloom': return period.bloom_months;
      }
    },
    [],
  );

  const setMonthsForKind = useCallback(
    (period: GrowingPeriod, kind: BarKind, months: number[]): GrowingPeriod => {
      switch (kind) {
        case 'sow': return { ...period, direct_sow_months: months };
        case 'growth': return { ...period, growth_months: months };
        case 'harvest': return { ...period, harvest_months: months };
        case 'bloom': return { ...period, bloom_months: months };
      }
    },
    [],
  );

  const handleBarDrag = useCallback(
    (periodIdx: number, kind: BarKind, rangeIdx: number, edge: 'start' | 'end', newMonth: number) => {
      setPeriods((prev) =>
        prev.map((p, i) => {
          if (i !== periodIdx) return p;
          const months = getMonthsForKind(p, kind);
          const ranges = monthsToRanges(months);
          if (!ranges[rangeIdx]) return p;
          const [s, e] = ranges[rangeIdx];
          if (edge === 'start') {
            ranges[rangeIdx] = [Math.min(newMonth, e), e];
          } else {
            ranges[rangeIdx] = [s, Math.max(newMonth, s)];
          }
          return setMonthsForKind(p, kind, rangesToMonths(ranges));
        }),
      );
    },
    [getMonthsForKind, setMonthsForKind],
  );

  const labelWidth = isMobile ? 100 : 150;
  const barKinds = getBarKinds();

  return (
    <Box sx={{ maxWidth: 1100 }}>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.species.growingPeriodsHelper')}
      </Typography>

      {/* Computed timeline preview */}
      {timelineBars.length > 0 && (
        <Card variant="outlined" sx={{ mb: 2 }}>
          <CardContent sx={{ pb: '16px !important' }}>
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
              {t('pages.species.computedTimeline')}
            </Typography>
            <Box sx={{ overflowX: 'auto' }}>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: `100px repeat(12, 1fr)`,
                  minWidth: 100 + 12 * CELL_MIN_W,
                }}
              >
                {/* Month header */}
                <Box sx={{ borderBottom: 1, borderColor: 'divider' }} />
                {MONTHS.map((m) => (
                  <Box
                    key={m}
                    sx={{
                      textAlign: 'center',
                      borderBottom: 1,
                      borderColor: 'divider',
                      py: 0.25,
                      ...(m === currentMonth && { bgcolor: alpha(theme.palette.primary.main, 0.08) }),
                    }}
                  >
                    <Typography
                      variant="caption"
                      sx={{
                        fontWeight: m === currentMonth ? 700 : 400,
                        color: m === currentMonth ? theme.palette.primary.main : theme.palette.text.secondary,
                      }}
                    >
                      {t(`pages.species.months.${m}`)}
                    </Typography>
                  </Box>
                ))}

                {/* Phase rows */}
                {(['indoor_sowing', 'outdoor_planting', 'growth', 'flowering', 'harvest'] as TimelinePhase[])
                  .filter((phase) => timelineBars.some((b) => b.phase === phase))
                  .map((phase) => {
                    const phaseBars = timelineBars.filter((b) => b.phase === phase);
                    const fromYear = phaseBars.find((b) => b.fromYear != null && b.fromYear > 1)?.fromYear ?? null;
                    return (
                      <React.Fragment key={phase}>
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            pl: 1,
                            borderBottom: 1,
                            borderColor: 'divider',
                            height: ROW_H,
                          }}
                        >
                          <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: TIMELINE_COLORS[phase], mr: 0.75, flexShrink: 0 }} />
                          <Typography variant="caption" noWrap color="text.secondary">
                            {t(`pages.species.timelinePhase.${phase}`)}
                          </Typography>
                          {fromYear != null && (
                            <Chip
                              label={t('pages.species.fromYear', { year: fromYear })}
                              size="small"
                              variant="outlined"
                              sx={{ ml: 0.5, height: 18, fontSize: '0.65rem', '& .MuiChip-label': { px: 0.5 } }}
                            />
                          )}
                        </Box>
                        {MONTHS.map((m) => {
                          const bar = phaseBars.find((b) => m >= b.startMonth && m <= b.endMonth);
                          if (!bar) {
                            return (
                              <Box
                                key={m}
                                sx={{
                                  borderBottom: 1,
                                  borderColor: 'divider',
                                  height: ROW_H,
                                  ...(m === currentMonth && { bgcolor: alpha(theme.palette.primary.main, 0.06) }),
                                }}
                              />
                            );
                          }
                          const isStart = m === bar.startMonth;
                          const isEnd = m === bar.endMonth;
                          return (
                            <Box
                              key={m}
                              sx={{
                                display: 'flex',
                                alignItems: 'center',
                                px: '1px',
                                borderBottom: 1,
                                borderColor: 'divider',
                                height: ROW_H,
                                ...(m === currentMonth && { bgcolor: alpha(theme.palette.primary.main, 0.06) }),
                              }}
                            >
                              <Box
                                sx={{
                                  width: '100%',
                                  height: BAR_H,
                                  bgcolor: alpha(TIMELINE_COLORS[phase], 0.75),
                                  borderRadius: `${isStart ? 4 : 0}px ${isEnd ? 4 : 0}px ${isEnd ? 4 : 0}px ${isStart ? 4 : 0}px`,
                                }}
                              />
                            </Box>
                          );
                        })}
                      </React.Fragment>
                    );
                  })}
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Gantt chart */}
      {periods.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ pb: '16px !important' }}>
            <Box sx={{ overflowX: 'auto' }}>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: `${labelWidth}px repeat(12, 1fr)`,
                  minWidth: labelWidth + 12 * CELL_MIN_W,
                }}
              >
                {/* Month header */}
                <Box
                  sx={{
                    position: 'sticky',
                    left: 0,
                    bgcolor: 'background.paper',
                    zIndex: 2,
                    borderBottom: 1,
                    borderColor: 'divider',
                  }}
                />
                {MONTHS.map((m) => (
                  <Box
                    key={m}
                    sx={{
                      textAlign: 'center',
                      borderBottom: 1,
                      borderColor: 'divider',
                      py: 0.5,
                      ...(m === currentMonth && {
                        bgcolor: alpha(theme.palette.primary.main, 0.08),
                      }),
                    }}
                  >
                    <Typography
                      variant="caption"
                      sx={{
                        fontWeight: m === currentMonth ? 700 : 400,
                        color: m === currentMonth
                          ? theme.palette.primary.main
                          : theme.palette.text.secondary,
                      }}
                    >
                      {t(`pages.species.months.${m}`)}
                    </Typography>
                  </Box>
                ))}

                {/* Period rows */}
                {periods.map((period, pIdx) => (
                  <PeriodGanttRows
                    key={pIdx}
                    period={period}
                    periodIdx={pIdx}
                    barKinds={barKinds}
                    labelWidth={labelWidth}
                    currentMonth={currentMonth}
                    theme={theme}
                    t={t}
                    isExpanded={expandedIdx === pIdx}
                    onToggleExpand={() =>
                      setExpandedIdx((prev) => (prev === pIdx ? null : pIdx))
                    }
                    onChange={handleChange}
                    onDelete={handleDelete}
                    dragState={dragState}
                    onDragStart={setDragState}
                    onDragMove={handleBarDrag}
                    onDragEnd={() => setDragState(null)}
                    getMonthsForKind={getMonthsForKind}
                  />
                ))}
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Empty state */}
      {periods.length === 0 && (
        <Card variant="outlined" sx={{ mb: 3, textAlign: 'center', py: 4 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.species.noPeriodsDefined')}
          </Typography>
        </Card>
      )}

      {/* Actions */}
      <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
        <Button variant="outlined" startIcon={<AddIcon />} onClick={handleAdd}>
          {t('pages.species.addPeriod')}
        </Button>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleSave}
          disabled={saving}
        >
          {t('common.save')}
        </Button>
      </Box>
    </Box>
  );
}

// ── Gantt rows for a single period ──────────────────────────────────

interface PeriodGanttRowsProps {
  period: GrowingPeriod;
  periodIdx: number;
  barKinds: BarKind[];
  labelWidth: number;
  currentMonth: number;
  theme: Theme;
  t: (key: string, opts?: Record<string, unknown>) => string;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onChange: (index: number, period: GrowingPeriod) => void;
  onDelete: (index: number) => void;
  dragState: DragState | null;
  onDragStart: (state: DragState) => void;
  onDragMove: (
    periodIdx: number,
    kind: BarKind,
    rangeIdx: number,
    edge: 'start' | 'end',
    newMonth: number,
  ) => void;
  onDragEnd: () => void;
  getMonthsForKind: (period: GrowingPeriod, kind: BarKind) => number[];
}

function PeriodGanttRows({
  period,
  periodIdx,
  barKinds,
  labelWidth,
  currentMonth,
  theme,
  t,
  isExpanded,
  onToggleExpand,
  onChange,
  onDelete,
  dragState,
  onDragStart,
  onDragMove,
  onDragEnd,
  getMonthsForKind,
}: PeriodGanttRowsProps) {
  const periodLabel =
    period.label || `${t('pages.species.growingPeriods')} ${periodIdx + 1}`;

  const update = (field: keyof GrowingPeriod, value: unknown) => {
    onChange(periodIdx, { ...period, [field]: value });
  };

  return (
    <>
      {/* Period label row */}
      <Box
        role="button"
        tabIndex={0}
        onClick={onToggleExpand}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            onToggleExpand();
          }
        }}
        sx={{
          position: 'sticky',
          left: 0,
          bgcolor: 'background.paper',
          zIndex: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 0.5,
          py: 0.5,
          px: 0.5,
          cursor: 'pointer',
          borderBottom: 1,
          borderColor: 'divider',
          gridColumn: '1 / -1',
          '&:hover': { bgcolor: 'action.hover' },
        }}
      >
        {isExpanded ? (
          <ExpandLessIcon
            sx={{ fontSize: 18, color: 'text.secondary', flexShrink: 0 }}
          />
        ) : (
          <ExpandMoreIcon
            sx={{ fontSize: 18, color: 'text.secondary', flexShrink: 0 }}
          />
        )}
        <Typography variant="subtitle2" noWrap>
          {periodLabel}
        </Typography>
        <EditIcon
          sx={{ fontSize: 14, color: 'text.disabled', ml: 0.5 }}
        />
      </Box>

      {/* Bar rows per kind */}
      {barKinds.map((kind) => {
        const months = getMonthsForKind(period, kind);
        const ranges = monthsToRanges(months);
        const kindLabel = t(`pages.species.barKind.${kind}`);
        const fromYear = kind === 'harvest' ? (period.harvest_from_year ?? null)
          : kind === 'bloom' ? (period.bloom_from_year ?? null)
          : null;

        return (
          <BarRow
            key={`${periodIdx}-${kind}`}
            kindLabel={kindLabel}
            kind={kind}
            ranges={ranges}
            periodIdx={periodIdx}
            labelWidth={labelWidth}
            currentMonth={currentMonth}
            theme={theme}
            t={t}
            dragState={dragState}
            onDragStart={onDragStart}
            onDragMove={onDragMove}
            onDragEnd={onDragEnd}
            fromYear={fromYear}
          />
        );
      })}

      {/* Inline detail form */}
      {isExpanded && (
        <Box
          sx={{
            gridColumn: '1 / -1',
            borderBottom: 1,
            borderColor: 'divider',
            px: 2,
            py: 1.5,
            bgcolor: alpha(theme.palette.action.hover, 0.3),
          }}
        >
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: 'repeat(5, 1fr) auto' },
              gap: 1.5,
              alignItems: 'start',
            }}
          >
            <TextField
              label={t('pages.species.periodLabel')}
              value={period.label}
              onChange={(e) => update('label', e.target.value)}
              size="small"
              fullWidth
              onClick={(e) => e.stopPropagation()}
            />
            <TextField
              label={t('pages.species.sowingIndoorWeeks')}
              helperText={t('pages.species.sowingIndoorWeeksHelper')}
              type="number"
              value={period.sowing_indoor_weeks_before_last_frost ?? ''}
              onChange={(e) =>
                update(
                  'sowing_indoor_weeks_before_last_frost',
                  e.target.value ? Number(e.target.value) : null,
                )
              }
              size="small"
              fullWidth
              slotProps={{ htmlInput: { min: 1, max: 26 } }}
              onClick={(e) => e.stopPropagation()}
            />
            <TextField
              label={t('pages.species.sowingOutdoorDays')}
              helperText={t('pages.species.sowingOutdoorDaysHelper')}
              type="number"
              value={period.sowing_outdoor_after_last_frost_days ?? ''}
              onChange={(e) =>
                update(
                  'sowing_outdoor_after_last_frost_days',
                  e.target.value ? Number(e.target.value) : null,
                )
              }
              size="small"
              fullWidth
              slotProps={{ htmlInput: { min: 0, max: 90 } }}
              onClick={(e) => e.stopPropagation()}
            />
            <TextField
              label={t('pages.species.harvestFromYear')}
              helperText={t('pages.species.harvestFromYearHelper')}
              type="number"
              value={period.harvest_from_year ?? ''}
              onChange={(e) =>
                update(
                  'harvest_from_year',
                  e.target.value ? Number(e.target.value) : null,
                )
              }
              size="small"
              fullWidth
              slotProps={{ htmlInput: { min: 1, max: 10 } }}
              onClick={(e) => e.stopPropagation()}
            />
            <TextField
              label={t('pages.species.bloomFromYear')}
              helperText={t('pages.species.bloomFromYearHelper')}
              type="number"
              value={period.bloom_from_year ?? ''}
              onChange={(e) =>
                update(
                  'bloom_from_year',
                  e.target.value ? Number(e.target.value) : null,
                )
              }
              size="small"
              fullWidth
              slotProps={{ htmlInput: { min: 1, max: 10 } }}
              onClick={(e) => e.stopPropagation()}
            />
            <IconButton
              size="small"
              color="error"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(periodIdx);
              }}
              sx={{ mt: 0.5 }}
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Box>
        </Box>
      )}
    </>
  );
}

// ── Single bar row (sow / harvest / bloom) ──────────────────────────

interface BarRowProps {
  kindLabel: string;
  kind: BarKind;
  ranges: [number, number][];
  periodIdx: number;
  labelWidth: number;
  currentMonth: number;
  theme: Theme;
  t: (key: string, opts?: Record<string, unknown>) => string;
  dragState: DragState | null;
  onDragStart: (state: DragState) => void;
  onDragMove: (
    periodIdx: number,
    kind: BarKind,
    rangeIdx: number,
    edge: 'start' | 'end',
    newMonth: number,
  ) => void;
  onDragEnd: () => void;
  fromYear: number | null;
}

function BarRow({
  kindLabel,
  kind,
  ranges,
  periodIdx,
  labelWidth,
  currentMonth,
  theme,
  t,
  dragState,
  onDragStart,
  onDragMove,
  onDragEnd,
  fromYear,
}: BarRowProps) {
  const color = BAR_COLORS[kind];
  const gridRef = useRef<HTMLDivElement>(null);

  const monthFromPointer = useCallback(
    (clientX: number): number => {
      const grid = gridRef.current;
      if (!grid) return 1;
      const rect = grid.getBoundingClientRect();
      const x = clientX - rect.left;
      const cellW = rect.width / 12;
      const month = Math.round(x / cellW - 0.5) + 1;
      return Math.max(1, Math.min(12, month));
    },
    [],
  );

  const handlePointerDown = useCallback(
    (e: React.PointerEvent, rangeIdx: number, edge: 'start' | 'end') => {
      e.preventDefault();
      (e.target as HTMLElement).setPointerCapture(e.pointerId);
      const month = edge === 'start' ? ranges[rangeIdx][0] : ranges[rangeIdx][1];
      onDragStart({ periodIdx, kind, rangeIdx, edge, originMonth: month });
    },
    [periodIdx, kind, ranges, onDragStart],
  );

  const handlePointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!dragState) return;
      if (
        dragState.periodIdx !== periodIdx ||
        dragState.kind !== kind
      )
        return;
      const newMonth = monthFromPointer(e.clientX);
      onDragMove(periodIdx, kind, dragState.rangeIdx, dragState.edge, newMonth);
    },
    [dragState, periodIdx, kind, monthFromPointer, onDragMove],
  );

  const handlePointerUp = useCallback(() => {
    onDragEnd();
  }, [onDragEnd]);

  return (
    <>
      {/* Kind label */}
      <Box
        sx={{
          position: 'sticky',
          left: 0,
          bgcolor: 'background.paper',
          zIndex: 1,
          display: 'flex',
          alignItems: 'center',
          pl: 3,
          pr: 0.5,
          borderBottom: 1,
          borderColor: 'divider',
          height: ROW_H,
        }}
      >
        <Box
          sx={{
            width: 10,
            height: 10,
            borderRadius: '50%',
            bgcolor: color,
            mr: 0.75,
            flexShrink: 0,
          }}
        />
        <Typography
          variant="caption"
          noWrap
          color="text.secondary"
          sx={{ maxWidth: labelWidth - 50 }}
        >
          {kindLabel}
        </Typography>
        {fromYear != null && fromYear > 1 && (
          <Chip
            label={t('pages.species.fromYear', { year: fromYear })}
            size="small"
            variant="outlined"
            sx={{ ml: 0.5, height: 16, fontSize: '0.6rem', '& .MuiChip-label': { px: 0.5 } }}
          />
        )}
      </Box>

      {/* Month cells with bars */}
      <Box
        ref={gridRef}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        sx={{
          gridColumn: '2 / -1',
          display: 'grid',
          gridTemplateColumns: 'repeat(12, 1fr)',
          borderBottom: 1,
          borderColor: 'divider',
          height: ROW_H,
          position: 'relative',
          userSelect: 'none',
          touchAction: 'none',
        }}
      >
        {MONTHS.map((m) => {
          const inRange = ranges.some(([s, e]) => m >= s && m <= e);
          const rangeIdx = ranges.findIndex(([s, e]) => m >= s && m <= e);
          const isStart = ranges.some(([s]) => s === m);
          const isEnd = ranges.some(([, e]) => e === m);

          return (
            <Box
              key={m}
              sx={{
                display: 'flex',
                alignItems: 'center',
                px: '1px',
                position: 'relative',
                ...(m === currentMonth && {
                  bgcolor: alpha(theme.palette.primary.main, 0.06),
                }),
              }}
            >
              {inRange && (
                <Tooltip
                  title={`${kindLabel}: ${t(`pages.species.months.${ranges[rangeIdx][0]}`)}–${t(`pages.species.months.${ranges[rangeIdx][1]}`)}`}
                  arrow
                  disableInteractive
                >
                  <Box
                    sx={{
                      width: '100%',
                      height: BAR_H,
                      bgcolor: alpha(color, 0.75),
                      borderRadius: `${isStart ? 4 : 0}px ${isEnd ? 4 : 0}px ${isEnd ? 4 : 0}px ${isStart ? 4 : 0}px`,
                      position: 'relative',
                    }}
                  >
                    {/* Drag handle: start edge */}
                    {isStart && (
                      <Box
                        onPointerDown={(e) =>
                          handlePointerDown(e, rangeIdx, 'start')
                        }
                        sx={{
                          position: 'absolute',
                          left: -2,
                          top: 0,
                          width: 8,
                          height: '100%',
                          cursor: 'ew-resize',
                          zIndex: 3,
                          '&:hover, &:active': {
                            '&::after': {
                              content: '""',
                              position: 'absolute',
                              left: 2,
                              top: 2,
                              bottom: 2,
                              width: 3,
                              borderRadius: 1,
                              bgcolor: alpha(color, 1),
                            },
                          },
                        }}
                      />
                    )}
                    {/* Drag handle: end edge */}
                    {isEnd && (
                      <Box
                        onPointerDown={(e) =>
                          handlePointerDown(e, rangeIdx, 'end')
                        }
                        sx={{
                          position: 'absolute',
                          right: -2,
                          top: 0,
                          width: 8,
                          height: '100%',
                          cursor: 'ew-resize',
                          zIndex: 3,
                          '&:hover, &:active': {
                            '&::after': {
                              content: '""',
                              position: 'absolute',
                              right: 2,
                              top: 2,
                              bottom: 2,
                              width: 3,
                              borderRadius: 1,
                              bgcolor: alpha(color, 1),
                            },
                          },
                        }}
                      />
                    )}
                  </Box>
                </Tooltip>
              )}
            </Box>
          );
        })}
      </Box>
    </>
  );
}
