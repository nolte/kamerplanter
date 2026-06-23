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
import { visuallyHidden } from '@mui/utils';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import EmptyState from '@/components/common/EmptyState';
import * as api from '@/api/endpoints/species';
import type { GrowingPeriod, HarvestPattern, PropagationConfig, Species } from '@/api/types';

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
  const { isFieldVisible } = useExpertiseLevel();
  // Progressive Disclosure (R-030): drag editing is held back for beginners; the
  // numeric detail block (pre-culture weeks, days-after-frost) is expert-only.
  const allowDrag = isFieldVisible('intermediate');
  const showNumericDetails = isFieldVisible('expert');
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

  // Lifespan heuristic (R-016 / R-002): `cycle_type` is not reliably available on
  // `Species` today, so we infer "likely perennial" from the data instead of
  // forcing a false linear "sow → harvest" sequence. The overlap itself is NOT a
  // perennial signal here (that would be circular — the overlap is exactly what
  // we want to frame). Instead we look for independent perennial markers:
  //   • harvest_pattern === 'perennial' (explicit recurring harvest), or
  //   • the species bears no harvest but blooms (typical of a perennial
  //     ornamental whose bloom recurs on the established plant).
  // When such a marker is present we frame an Aussaat∩Ernte/Blüte overlap as
  // "normal for perennials" (R-020); for a clearly annual-looking species (no
  // perennial marker) we do NOT downplay it but flag it for review (R-016 row 1).
  // Documented as a heuristic (R-050 transparency); the clean fix is the E2
  // lifespan split (spec §8).
  const isLikelyPerennial = useMemo(
    () =>
      species.harvest_pattern === 'perennial' ||
      (!species.allows_harvest && periods.some((p) => p.bloom_months.length > 0)),
    [species.harvest_pattern, species.allows_harvest, periods],
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

  // Plant-type-adaptive track visibility (§4). A track is hidden when it would be
  // a *misinformation* rather than a neutral empty row (e.g. a harvest row on an
  // ornamental reads as "never harvested"; a sow row on a strictly vegetatively
  // propagated plant reads as "must be sown").
  const showSowTrack = useMemo(
    // R-013: show the sow track only if the species can be raised from seed
    // (seed propagation config) OR sowing months are actually maintained. With
    // purely vegetative propagation and no sow data the propagation track alone
    // carries the timing.
    () => hasSeedPropagation || periods.some((p) => p.direct_sow_months.length > 0),
    [hasSeedPropagation, periods],
  );
  // R-010: hide the harvest track for non-harvestable (ornamental) species.
  const showHarvestTrack = species.allows_harvest === true;

  const getBarKinds = useCallback(
    // Propagation first — it's a species-level, read-only summary row that frames
    // the editable sow/growth/harvest/bloom timing below. Sow (R-013) and harvest
    // (R-010) are conditional on the adaptive visibility above.
    (): BarKind[] => {
      const kinds: BarKind[] = ['propagation'];
      if (showSowTrack) kinds.push('sow');
      kinds.push('growth');
      if (showHarvestTrack) kinds.push('harvest');
      kinds.push('bloom');
      return kinds;
    },
    [showSowTrack, showHarvestTrack],
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

  // R-012: derive the section title from the tracks actually shown, so it never
  // names a harvest that has no row. With harvest → "Sowing, Harvest & Bloom";
  // without harvest but with sow → "Sowing & Bloom"; with neither (pure
  // ornamental: only propagation + bloom) → "Propagation & Bloom".
  const timingChartTitleKey = barKinds.includes('harvest')
    ? 'pages.species.timingChartTitle'
    : barKinds.includes('sow')
      ? 'pages.species.timingChartTitleSowBloom'
      : 'pages.species.timingChartTitlePropBloom';

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
              {t(timingChartTitleKey)}
            </Typography>
            {hasSowHarvestOverlap && (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ display: 'block', mb: 1.5 }}
              >
                {/* R-016/R-002: only frame the overlap as "normal" when the
                    heuristic suggests a perennial; otherwise flag it for review
                    instead of downplaying a real annual-season contradiction. */}
                {t(
                  isLikelyPerennial
                    ? 'pages.species.sowHarvestOverlapHint'
                    : 'pages.species.sowHarvestOverlapHintAnnual',
                )}
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
                    harvestPattern={species.harvest_pattern}
                    allowDrag={allowDrag}
                    showNumericDetails={showNumericDetails}
                  />
                ))}
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Empty state (QW-6): shared EmptyState with a primary "add period" CTA.
          The vegetative-only hint is surfaced as the EmptyState description. */}
      {periods.length === 0 && (
        <EmptyState
          message={t('pages.species.noPeriodsDefined')}
          description={
            propagationConfigs.length > 0 && !hasSeedPropagation
              ? t('pages.species.noPeriodsVegetativeHint', { methods: propagationLabels })
              : undefined
          }
          actionLabel={t('pages.species.addPeriod')}
          onAction={handleAdd}
        />
      )}

      {/* Actions — the "add period" CTA already lives in the empty state, so the
          action bar (and the disabled "save" with nothing to save) is only shown
          once at least one period exists (QW-6). */}
      {periods.length > 0 && (
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
      )}
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
  harvestPattern: HarvestPattern | null;
  /** Drag editing is enabled from `intermediate` upward (R-030). */
  allowDrag: boolean;
  /** Numeric detail fields (pre-culture weeks, days-after-frost) are expert-only (R-030). */
  showNumericDetails: boolean;
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
  harvestPattern,
  allowDrag,
  showNumericDetails,
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
            // Propagation is always read-only (R-006). For beginners, the
            // editable tracks are shown but not draggable (R-030: "without edit
            // handles in the foreground").
            readOnly={kind === 'propagation' || !allowDrag}
            harvestPattern={kind === 'harvest' ? harvestPattern : null}
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
              // R-030: the two numeric pre-culture fields are expert-only, so the
              // md column count adapts (5 data fields + delete for experts, 3 + delete otherwise).
              gridTemplateColumns: {
                xs: '1fr',
                sm: '1fr 1fr',
                md: showNumericDetails ? 'repeat(5, 1fr) auto' : 'repeat(3, 1fr) auto',
              },
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
            {/* R-030: numeric detail parameters (pre-culture weeks, days after last
                frost) are expert-only progressive-disclosure fields. */}
            {showNumericDetails && (
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
            )}
            {showNumericDetails && (
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
            )}
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
  /** Harvest pattern for the harvest track only (R-021); null for every other track. */
  harvestPattern?: HarvestPattern | null;
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
  harvestPattern = null,
}: BarRowProps) {
  const color = BAR_COLORS[kind];
  const gridRef = useRef<HTMLDivElement>(null);
  // aria-live announcement (R-044): the new month range after a drag/keyboard
  // edit, verbalised for screen-reader users via a visually-hidden polite region.
  const [announcement, setAnnouncement] = useState('');

  // R-021: differentiate the harvest bar by harvest pattern. `single` → a narrow,
  // point-like bar (single harvest); `continuous`/`perennial` → the full-width
  // continuous bar (multiple/recurring harvest). Only the harvest track is affected.
  const isSingleHarvest = kind === 'harvest' && harvestPattern === 'single';
  const harvestPatternTooltip =
    kind === 'harvest' && harvestPattern
      ? t(
          harvestPattern === 'single'
            ? 'pages.species.harvestPatternSingleTooltip'
            : harvestPattern === 'continuous'
              ? 'pages.species.harvestPatternContinuousTooltip'
              : 'pages.species.harvestPatternPerennialTooltip',
        )
      : '';

  // Human-readable range label for a range, e.g. "März–April" or "Mai".
  const rangeText = useCallback(
    (s: number, e: number): string =>
      s === e
        ? t(`pages.species.months.${s}`)
        : `${t(`pages.species.months.${s}`)}–${t(`pages.species.months.${e}`)}`,
    [t],
  );

  // Announce the full track range after an edit settles (R-044 aria-live).
  const announceRanges = useCallback(
    (rs: [number, number][]) => {
      const range = rs.map(([s, e]) => rangeText(s, e)).join(', ');
      setAnnouncement(t('pages.species.barRangeAnnouncement', { kind: kindLabel, range }));
    },
    [rangeText, t, kindLabel],
  );

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
    // Announce the settled range (R-044). After a pointer drag the ranges prop is
    // already updated for the next render, so verbalise the current ranges.
    announceRanges(ranges);
    onDragEnd();
  }, [onDragEnd, announceRanges, ranges]);

  // R-044: keyboard resize of a handle. ArrowLeft/Right move the edge month by
  // ∓1 using the exact same clamping logic as the pointer drag (start ≤ end ≤ 12,
  // start ≥ 1), then announce the new range.
  const handleHandleKeyDown = useCallback(
    (e: React.KeyboardEvent, rangeIdx: number, edge: 'start' | 'end') => {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
      e.preventDefault();
      const delta = e.key === 'ArrowRight' ? 1 : -1;
      const [s, eMonth] = ranges[rangeIdx];
      const current = edge === 'start' ? s : eMonth;
      const target = Math.max(1, Math.min(12, current + delta));
      onDragStart({ periodIdx, kind, rangeIdx, edge, originMonth: current });
      onDragMove(periodIdx, kind, rangeIdx, edge, target);
      onDragEnd();
      // Reflect the clamped move in the announcement (mirror handleBarDrag clamps).
      const next: [number, number] =
        edge === 'start' ? [Math.min(target, eMonth), eMonth] : [s, Math.max(target, s)];
      const updated = ranges.map((r, i) => (i === rangeIdx ? next : r));
      announceRanges(updated);
    },
    [ranges, periodIdx, kind, onDragStart, onDragMove, onDragEnd, announceRanges],
  );

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
                    // R-042 base tooltip (kind + month range), plus R-007 read-only
                    // hint and R-021 harvest-pattern note where applicable.
                    `${kindLabel}: ${t(`pages.species.months.${ranges[rangeIdx][0]}`)}–${t(`pages.species.months.${ranges[rangeIdx][1]}`)}` +
                    (readOnly ? ` — ${t('pages.species.barKindReadOnlyHint')}` : '') +
                    (harvestPatternTooltip ? ` — ${harvestPatternTooltip}` : '')
                  }
                  arrow
                  disableInteractive
                >
                  <Box
                    // R-021 marker for assertions: which harvest rendering applies.
                    data-bar-variant={
                      kind === 'harvest' ? (isSingleHarvest ? 'single' : 'continuous') : undefined
                    }
                    sx={{
                      // R-021: a single (final) harvest renders as a narrow,
                      // point-like bar centred in the cell; continuous/perennial
                      // (and every non-harvest track) keep the full-width bar.
                      width: isSingleHarvest ? '40%' : '100%',
                      mx: isSingleHarvest ? 'auto' : 0,
                      height: BAR_H,
                      bgcolor: alpha(color, 0.75),
                      borderRadius: isSingleHarvest
                        ? '4px'
                        : `${isStart ? 4 : 0}px ${isEnd ? 4 : 0}px ${isEnd ? 4 : 0}px ${isStart ? 4 : 0}px`,
                      position: 'relative',
                    }}
                  >
                    {/* Drag handles are omitted on read-only rows (e.g. propagation):
                        the bar is purely visual and edited elsewhere. The visible
                        handle stays 8px wide; an invisible ::before overlay provides
                        the ≥44×44px touch target (R-041) without widening the optic. */}
                    {!readOnly && isStart && (
                      <Box
                        role="slider"
                        tabIndex={0}
                        aria-label={t('pages.species.barResizeStartAriaLabel', { kind: kindLabel })}
                        aria-valuemin={1}
                        aria-valuemax={12}
                        aria-valuenow={ranges[rangeIdx][0]}
                        aria-valuetext={t(`pages.species.months.${ranges[rangeIdx][0]}`)}
                        onPointerDown={(e) => handlePointerDown(e, rangeIdx, 'start')}
                        onKeyDown={(e) => handleHandleKeyDown(e, rangeIdx, 'start')}
                        sx={{
                          position: 'absolute',
                          left: -2,
                          top: 0,
                          width: 8,
                          height: '100%',
                          cursor: 'ew-resize',
                          zIndex: 3,
                          // R-041: invisible centred 44×44px touch/hit target.
                          '&::before': {
                            content: '""',
                            position: 'absolute',
                            left: '50%',
                            top: '50%',
                            transform: 'translate(-50%, -50%)',
                            width: 44,
                            height: 44,
                          },
                          '&:focus-visible': {
                            outline: `2px solid ${theme.palette.primary.main}`,
                            outlineOffset: 1,
                          },
                          '&:hover, &:active, &:focus-visible': {
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
                        role="slider"
                        tabIndex={0}
                        aria-label={t('pages.species.barResizeEndAriaLabel', { kind: kindLabel })}
                        aria-valuemin={1}
                        aria-valuemax={12}
                        aria-valuenow={ranges[rangeIdx][1]}
                        aria-valuetext={t(`pages.species.months.${ranges[rangeIdx][1]}`)}
                        onPointerDown={(e) => handlePointerDown(e, rangeIdx, 'end')}
                        onKeyDown={(e) => handleHandleKeyDown(e, rangeIdx, 'end')}
                        sx={{
                          position: 'absolute',
                          right: -2,
                          top: 0,
                          width: 8,
                          height: '100%',
                          cursor: 'ew-resize',
                          zIndex: 3,
                          '&::before': {
                            content: '""',
                            position: 'absolute',
                            left: '50%',
                            top: '50%',
                            transform: 'translate(-50%, -50%)',
                            width: 44,
                            height: 44,
                          },
                          '&:focus-visible': {
                            outline: `2px solid ${theme.palette.primary.main}`,
                            outlineOffset: 1,
                          },
                          '&:hover, &:active, &:focus-visible': {
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

      {/* R-044: visually-hidden polite live region announcing the new range after
          a drag/keyboard edit. Spans the full row so it sits in the grid flow. */}
      {!readOnly && (
        <Box
          aria-live="polite"
          data-testid={`bar-live-${periodIdx}-${kind}`}
          sx={{ ...visuallyHidden, gridColumn: '1 / -1' }}
        >
          {announcement}
        </Box>
      )}
    </>
  );
}
