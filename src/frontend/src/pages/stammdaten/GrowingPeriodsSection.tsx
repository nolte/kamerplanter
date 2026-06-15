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
import TipsAndUpdatesIcon from '@mui/icons-material/TipsAndUpdates';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/species';
import type { GrowingPeriod, PropagationConfig, Species } from '@/api/types';

const MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
const CELL_MIN_W = 40;
const BAR_H = 20;
const ROW_H = 32;

type BarKind = 'sow' | 'growth' | 'harvest' | 'bloom' | 'propagation';

const BAR_COLORS: Record<BarKind, string> = {
  propagation: '#26A69A',
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

  const currentMonth = new Date().getMonth() + 1;

  // Propagation overview — clarifies why sowing data may be sparse or absent
  // (e.g. species propagated only via cuttings/division have no sowing periods).
  // Read-only here: the structured configs are edited on the Edit tab (WP-5).
  // Stabilise the array reference so downstream memos don't thrash on every render.
  const propagationConfigs = useMemo<PropagationConfig[]>(
    () => species.propagation_configs ?? [],
    [species.propagation_configs],
  );
  const hasSeedPropagation = useMemo(
    () => propagationConfigs.some((c) => c.method === 'seed'),
    [propagationConfigs],
  );
  // String primitive — memo avoids re-joining on unrelated re-renders.
  const propagationLabels = useMemo(
    () => propagationConfigs.map((c) => t(`enums.propagationMethod.${c.method}`)).join(', '),
    [propagationConfigs, t],
  );

  // Union of every config's months — drives the read-only propagation timeline bar.
  const propagationMonthsUnion = useMemo(
    () => [...new Set(propagationConfigs.flatMap((c) => c.months ?? []))].sort((a, b) => a - b),
    [propagationConfigs],
  );

  // Human-readable month range(s) for a single config's months, e.g. "März–April, Sep".
  const monthsLabel = useCallback(
    (months: number[]) =>
      monthsToRanges(months)
        .map(([s, e]) =>
          s === e
            ? t(`pages.species.months.${s}`)
            : `${t(`pages.species.months.${s}`)}–${t(`pages.species.months.${e}`)}`,
        )
        .join(', '),
    [t],
  );

  // Do sowing months overlap harvest/bloom months? For perennials this is normal
  // (sowing only establishes the plant; harvest/bloom recur on the established
  // plant) and would otherwise read as a contradiction — so we explain it inline.
  const hasSowHarvestOverlap = useMemo(
    () =>
      periods.some((p) => {
        const sow = new Set(p.direct_sow_months);
        return [...p.harvest_months, ...p.bloom_months].some((m) => sow.has(m));
      }),
    [periods],
  );

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
        setPeriods([
          {
            label: '',
            sowing_indoor_weeks_before_last_frost:
              species.sowing_indoor_weeks_before_last_frost ?? null,
            sowing_outdoor_after_last_frost_days:
              species.sowing_outdoor_after_last_frost_days ?? null,
            direct_sow_months: species.direct_sow_months ?? [],
            growth_months: [],
            harvest_months: species.harvest_months ?? [],
            bloom_months: species.bloom_months ?? [],
            harvest_from_year: species.harvest_from_year ?? null,
            bloom_from_year: species.bloom_from_year ?? null,
          },
        ]);
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
        // Configs are read-only on this tab — round-trip them so the update
        // (which replaces the species) does not drop the propagation data.
        propagation_configs: propagationConfigs,
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
    // Propagation first — it's a species-level, read-only summary row that frames
    // the editable sow/growth/harvest/bloom timing below.
    (): BarKind[] => ['propagation', 'sow', 'growth', 'harvest', 'bloom'],
    [],
  );

  const getMonthsForKind = useCallback(
    (period: GrowingPeriod, kind: BarKind): number[] => {
      switch (kind) {
        // Species-global union over all configs — identical for every period.
        case 'propagation':
          return propagationMonthsUnion;
        case 'sow':
          return period.direct_sow_months;
        case 'growth':
          return period.growth_months;
        case 'harvest':
          return period.harvest_months;
        case 'bloom':
          return period.bloom_months;
      }
    },
    [propagationMonthsUnion],
  );

  const setMonthsForKind = useCallback(
    (period: GrowingPeriod, kind: BarKind, months: number[]): GrowingPeriod => {
      switch (kind) {
        // Read-only row — never written through the timeline; edited in the card above.
        case 'propagation':
          return period;
        case 'sow':
          return { ...period, direct_sow_months: months };
        case 'growth':
          return { ...period, growth_months: months };
        case 'harvest':
          return { ...period, harvest_months: months };
        case 'bloom':
          return { ...period, bloom_months: months };
      }
    },
    [],
  );

  const handleBarDrag = useCallback(
    (
      periodIdx: number,
      kind: BarKind,
      rangeIdx: number,
      edge: 'start' | 'end',
      newMonth: number,
    ) => {
      // Propagation is read-only in the timeline — guard against any drag effect.
      if (kind === 'propagation') return;
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

      {/* Propagation overview — read-only per-method summary (method + best months +
          optional wood stage + notes). The structured configs are edited on the
          species Edit tab (WP-5); here they only contextualise the timing chart.
          Mirrors the Card framing of the timeline below. */}
      {propagationConfigs.length > 0 && (
        <Card variant="outlined" sx={{ mb: 2 }}>
          <CardContent sx={{ '&:last-child': { pb: 2 } }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 1,
                mb: 1.5,
              }}
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                {t('pages.species.propagationOverviewLabel')}
              </Typography>
              <Tooltip title={t('pages.species.barKindReadOnlyHint')} arrow>
                <EditIcon sx={{ fontSize: 16, color: 'text.disabled' }} aria-hidden="true" />
              </Tooltip>
            </Box>

            {/* Vegetative-only hint — compact caption, not a full-width Alert */}
            {!hasSeedPropagation && (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ display: 'block', mb: 1.5 }}
              >
                {t('pages.species.vegetativeOnlyNotice', { methods: propagationLabels })}
              </Typography>
            )}

            {/* One read-only block per configured method */}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              {propagationConfigs.map((cfg, idx) => (
                <Box
                  key={`${cfg.method}-${idx}`}
                  data-testid={`propagation-config-${idx}`}
                  sx={{
                    pb: idx < propagationConfigs.length - 1 ? 1.5 : 0,
                    borderBottom: idx < propagationConfigs.length - 1 ? '1px solid' : 'none',
                    borderColor: 'divider',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 0.75 }}>
                    <Chip
                      size="small"
                      variant="outlined"
                      color={cfg.method === 'seed' ? 'success' : 'default'}
                      label={t(`enums.propagationMethod.${cfg.method}`)}
                    />
                    {cfg.wood_stage && (
                      <Chip
                        size="small"
                        variant="outlined"
                        label={t(`enums.woodStage.${cfg.wood_stage}`)}
                      />
                    )}
                    {(cfg.months?.length ?? 0) > 0 && (
                      <Typography variant="body2" color="text.secondary">
                        {t('pages.species.propagationMonthsValue', {
                          range: monthsLabel(cfg.months),
                        })}
                      </Typography>
                    )}
                  </Box>
                  {cfg.notes?.trim() && (
                    <Box
                      role="note"
                      aria-label={t('pages.species.propagationNotesLabel')}
                      sx={{
                        mt: 1,
                        display: 'flex',
                        gap: 1,
                        alignItems: 'flex-start',
                        px: 1.5,
                        py: 1,
                        borderRadius: 1,
                        border: '1px solid',
                        borderColor: 'divider',
                        bgcolor: (th) => alpha(th.palette.action.selected, 0.04),
                      }}
                    >
                      <TipsAndUpdatesIcon
                        aria-hidden="true"
                        sx={{ fontSize: 18, color: 'text.secondary', mt: 0.25, flexShrink: 0 }}
                      />
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ whiteSpace: 'pre-line' }}
                      >
                        {cfg.notes}
                      </Typography>
                    </Box>
                  )}
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Single timing chart — the editable month grid below is the one source of
          truth. The former "computed timeline" was removed: its clipped sow→harvest
          sequence contradicted these raw months for perennials (REQ-001 review). */}
      {periods.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ pb: '16px !important' }}>
            <Typography
              variant="subtitle2"
              sx={{ fontWeight: 600, mb: hasSowHarvestOverlap ? 0.5 : 1.5 }}
            >
              {t('pages.species.timingChartTitle')}
            </Typography>
            {hasSowHarvestOverlap && (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ display: 'block', mb: 1.5 }}
              >
                {t('pages.species.sowHarvestOverlapHint')}
              </Typography>
            )}
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
                        color:
                          m === currentMonth
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
                    onToggleExpand={() => setExpandedIdx((prev) => (prev === pIdx ? null : pIdx))}
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
        <Card variant="outlined" sx={{ mb: 3, textAlign: 'center', py: 4, px: 2 }}>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mb: propagationConfigs.length > 0 && !hasSeedPropagation ? 1 : 0 }}
          >
            {t('pages.species.noPeriodsDefined')}
          </Typography>
          {propagationConfigs.length > 0 && !hasSeedPropagation && (
            <Typography variant="caption" color="text.secondary">
              {t('pages.species.noPeriodsVegetativeHint', { methods: propagationLabels })}
            </Typography>
          )}
        </Card>
      )}

      {/* Actions */}
      <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
        <Button variant="outlined" startIcon={<AddIcon />} onClick={handleAdd}>
          {t('pages.species.addPeriod')}
        </Button>
        <Button variant="contained" startIcon={<SaveIcon />} onClick={handleSave} disabled={saving}>
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
  const periodLabel = period.label || `${t('pages.species.growingPeriods')} ${periodIdx + 1}`;

  const update = (field: keyof GrowingPeriod, value: unknown) => {
    onChange(periodIdx, { ...period, [field]: value });
  };

  return (
    <>
      {/* Period label row */}
      <Box
        role="button"
        tabIndex={0}
        aria-expanded={isExpanded}
        aria-label={`${periodLabel} — ${isExpanded ? t('pages.species.periodCollapseLabel') : t('pages.species.periodExpandLabel')}`}
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
          <ExpandLessIcon sx={{ fontSize: 18, color: 'text.secondary', flexShrink: 0 }} />
        ) : (
          <ExpandMoreIcon sx={{ fontSize: 18, color: 'text.secondary', flexShrink: 0 }} />
        )}
        <Typography variant="subtitle2" noWrap>
          {periodLabel}
        </Typography>
        <EditIcon sx={{ fontSize: 14, color: 'text.disabled', ml: 0.5 }} />
      </Box>

      {/* Bar rows per kind */}
      {barKinds.map((kind) => {
        const months = getMonthsForKind(period, kind);
        const ranges = monthsToRanges(months);
        const kindLabel = t(`pages.species.barKind.${kind}`);
        const fromYear =
          kind === 'harvest'
            ? (period.harvest_from_year ?? null)
            : kind === 'bloom'
              ? (period.bloom_from_year ?? null)
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
            readOnly={kind === 'propagation'}
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
                update('harvest_from_year', e.target.value ? Number(e.target.value) : null)
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
                update('bloom_from_year', e.target.value ? Number(e.target.value) : null)
              }
              size="small"
              fullWidth
              slotProps={{ htmlInput: { min: 1, max: 10 } }}
              onClick={(e) => e.stopPropagation()}
            />
            <Tooltip title={t('pages.species.deletePeriodLabel', { label: periodLabel })} arrow>
              <IconButton
                size="small"
                color="error"
                aria-label={t('pages.species.deletePeriodLabel', { label: periodLabel })}
                data-testid={`delete-period-${periodIdx}`}
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(periodIdx);
                }}
                sx={{ mt: 0.5 }}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Tooltip>
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
  /** Static, display-only bar — no drag handles, no resize cursor (e.g. propagation). */
  readOnly?: boolean;
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
  readOnly = false,
}: BarRowProps) {
  const color = BAR_COLORS[kind];
  const gridRef = useRef<HTMLDivElement>(null);

  const monthFromPointer = useCallback((clientX: number): number => {
    const grid = gridRef.current;
    if (!grid) return 1;
    const rect = grid.getBoundingClientRect();
    const x = clientX - rect.left;
    const cellW = rect.width / 12;
    const month = Math.round(x / cellW - 0.5) + 1;
    return Math.max(1, Math.min(12, month));
  }, []);

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
      if (dragState.periodIdx !== periodIdx || dragState.kind !== kind) return;
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
      {/* Kind label — wrapped in Tooltip for read-only rows to surface the edit location */}
      <Tooltip
        title={readOnly ? t('pages.species.barKindReadOnlyHint') : ''}
        placement="right"
        arrow
        disableInteractive
      >
        <Box
          aria-label={
            readOnly ? `${kindLabel} — ${t('pages.species.barKindReadOnlyHint')}` : kindLabel
          }
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
      </Tooltip>

      {/* Month cells with bars */}
      <Box
        ref={gridRef}
        onPointerMove={readOnly ? undefined : handlePointerMove}
        onPointerUp={readOnly ? undefined : handlePointerUp}
        sx={{
          gridColumn: '2 / -1',
          display: 'grid',
          gridTemplateColumns: 'repeat(12, 1fr)',
          borderBottom: 1,
          borderColor: 'divider',
          height: ROW_H,
          position: 'relative',
          userSelect: 'none',
          ...(readOnly ? {} : { touchAction: 'none' }),
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
                  title={
                    readOnly
                      ? `${kindLabel}: ${t(`pages.species.months.${ranges[rangeIdx][0]}`)}–${t(`pages.species.months.${ranges[rangeIdx][1]}`)} — ${t('pages.species.barKindReadOnlyHint')}`
                      : `${kindLabel}: ${t(`pages.species.months.${ranges[rangeIdx][0]}`)}–${t(`pages.species.months.${ranges[rangeIdx][1]}`)}`
                  }
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
                    {/* Drag handles are omitted on read-only rows (e.g. propagation):
                        the bar is purely visual and edited elsewhere. */}
                    {!readOnly && isStart && (
                      <Box
                        onPointerDown={(e) => handlePointerDown(e, rangeIdx, 'start')}
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
                    {!readOnly && isEnd && (
                      <Box
                        onPointerDown={(e) => handlePointerDown(e, rangeIdx, 'end')}
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
