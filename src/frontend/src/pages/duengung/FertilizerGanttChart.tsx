import { useMemo, useState, useCallback, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Popover from '@mui/material/Popover';
import OpacityIcon from '@mui/icons-material/Opacity';
import AddIcon from '@mui/icons-material/Add';
import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import UnfoldMoreIcon from '@mui/icons-material/UnfoldMore';
import UnfoldLessIcon from '@mui/icons-material/UnfoldLess';
import { alpha, useTheme, type Theme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import type { NutrientPlanPhaseEntry, Fertilizer } from '@/api/types';
import { MONTH_WEEK_SPANS, getShortMonthName } from '@/utils/weekCalculation';

/** Iterate effective calendar weeks for an entry, wrapping week_end > calendarSize to 1..N. */
function* iterEntryWeeks(weekStart: number, weekEnd: number, calendarSize = 52): Generator<number> {
  if (weekEnd <= calendarSize) {
    for (let w = weekStart; w <= weekEnd; w++) yield w;
  } else {
    // Phase wraps: e.g. W49-W66 → yield 49..52, then 1..14
    for (let w = weekStart; w <= calendarSize; w++) yield w;
    for (let w = 1; w <= weekEnd - calendarSize; w++) yield w;
  }
}

/** Check if a calendar week falls within a span, handling year-boundary wrap (weekEnd > 52). */
function spanContainsWeek(s: { weekStart: number; weekEnd: number }, absWeek: number, calendarSize = 52): boolean {
  if (s.weekEnd <= calendarSize) {
    return absWeek >= s.weekStart && absWeek <= s.weekEnd;
  }
  // Wrap: e.g. weekStart=49, weekEnd=66 → covers 49-52 and 1-14
  return absWeek >= s.weekStart || absWeek <= s.weekEnd - calendarSize;
}

/** Check if absWeek is the visual start of a (possibly wrapping) span. */
function isSpanStart(s: { weekStart: number; weekEnd: number }, absWeek: number, calendarSize = 52): boolean {
  if (s.weekEnd <= calendarSize) return absWeek === s.weekStart;
  return absWeek === s.weekStart || absWeek === 1;
}

/** Check if absWeek is the visual end of a (possibly wrapping) span. */
function isSpanEnd(s: { weekStart: number; weekEnd: number }, absWeek: number, calendarSize = 52): boolean {
  if (s.weekEnd <= calendarSize) return absWeek === s.weekEnd;
  return absWeek === calendarSize || absWeek === s.weekEnd - calendarSize;
}

// ── Data transformation ─────────────────────────────────────────────

interface FertSpan {
  weekStart: number;
  weekEnd: number;
  phaseName: string;
  mlPerLiter: number;
  entryKey: string;
  channelId: string;
}

interface FertilizerRow {
  fertKey: string;
  fertName: string;
  brand: string;
  spans: FertSpan[];
}

interface MethodGroup {
  method: string;
  rows: FertilizerRow[];
  /** All entry/channel pairs for this method — used for "add fertilizer" action. */
  channels: { entryKey: string; channelId: string }[];
}

function buildMethodGroups(
  entries: NutrientPlanPhaseEntry[],
  fertilizers: Fertilizer[],
): MethodGroup[] {
  const fertLookup = new Map(fertilizers.map((f) => [f.key, f]));
  // method -> fertKey -> FertilizerRow
  const groupMap = new Map<string, Map<string, FertilizerRow>>();
  const channelMap = new Map<string, { entryKey: string; channelId: string }[]>();

  for (const entry of entries) {
    for (const ch of entry.delivery_channels) {
      const method = ch.application_method;
      if (!groupMap.has(method)) {
        groupMap.set(method, new Map());
        channelMap.set(method, []);
      }
      channelMap.get(method)!.push({ entryKey: entry.key, channelId: ch.channel_id });
      const fertMap = groupMap.get(method)!;

      for (const dosage of ch.fertilizer_dosages) {
        let row = fertMap.get(dosage.fertilizer_key);
        if (!row) {
          const f = fertLookup.get(dosage.fertilizer_key);
          row = {
            fertKey: dosage.fertilizer_key,
            fertName: f ? f.product_name : dosage.fertilizer_key,
            brand: f?.brand ?? '',
            spans: [],
          };
          fertMap.set(dosage.fertilizer_key, row);
        }
        row.spans.push({
          weekStart: entry.week_start,
          weekEnd: entry.week_end,
          phaseName: entry.phase_name,
          mlPerLiter: dosage.ml_per_liter,
          entryKey: entry.key,
          channelId: ch.channel_id,
        });
      }
    }
  }

  return [...groupMap.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([method, fertMap]) => ({
      method,
      rows: [...fertMap.values()].sort((a, b) => a.fertName.localeCompare(b.fertName)),
      channels: channelMap.get(method) ?? [],
    }));
}

// ── Color palette ───────────────────────────────────────────────────

const METHOD_COLORS: Record<string, string> = {
  fertigation: '#1976d2',
  drench: '#2e7d32',
  foliar: '#ed6c02',
  top_dress: '#9c27b0',
};

function getMethodColor(method: string): string {
  return METHOD_COLORS[method] ?? '#757575';
}

// ── Tank info (resolved from Location) ───────────────────────────────

interface ResolvedTank {
  key: string;
  name: string;
  volumeLiters: number;
}

// ── Phase transition type ────────────────────────────────────────────

export interface PhaseTransition {
  week: number;
  endWeek?: number;   // projected end week of this phase (from projected_end / actual_exited_at)
  date: string;
  phaseName: string;  // phase_name value (e.g. "vegetative", "flowering")
}

// ── Component ───────────────────────────────────────────────────────

/** Save the RO water mix ratio for a specific entry. */
export interface WaterMixSavePayload {
  entryKey: string;
  roPercent: number;
}

/** Save the EC target for a specific entry/channel. */
export interface EcTargetSavePayload {
  entryKey: string;
  channelId: string;
  ecMs: number;
}

/** Save a dosage change for a specific fertilizer in a specific entry/channel. */
export interface DosageSavePayload {
  entryKey: string;
  channelId: string;
  fertilizerKey: string;
  mlPerLiter: number;
}

/** Remove a fertilizer completely from a specific entry/channel. */
export interface DosageRemovePayload {
  entryKey: string;
  channelId: string;
  fertilizerKey: string;
}

/** Remove a fertilizer from ALL entries/channels where it appears. */
export interface FertilizerRemoveAllPayload {
  fertilizerKey: string;
  fertilizerName: string;
  /** All entry/channel pairs where this fertilizer is present. */
  targets: { entryKey: string; channelId: string }[];
}

interface FertilizerGanttChartProps {
  entries: NutrientPlanPhaseEntry[];
  fertilizers: Fertilizer[];
  currentWeek?: number;
  phaseTransitions?: PhaseTransition[];
  tank?: ResolvedTank | null;
  weekOffset?: number;
  weekLabel?: string;
  totalWeeksOverride?: number;
  showMonthHeaders?: boolean;
  onAddFertilizer?: (entryKey: string, channelId: string) => void;
  onSaveDosage?: (payload: DosageSavePayload) => void;
  onRemoveDosage?: (payload: DosageRemovePayload) => void;
  onRemoveFertilizerFromAll?: (payload: FertilizerRemoveAllPayload) => void;
  /** RO water mix ratio (0–100 %) plan-level default. */
  roPercent?: number | null;
  onSaveWaterMix?: (payload: WaterMixSavePayload) => void;
  onSaveEcTarget?: (payload: EcTargetSavePayload) => void;
  /** Week number where the perennial cycle restarts (draws a visual separator). */
  cycleRestartWeek?: number;
}

export default function FertilizerGanttChart({
  entries,
  fertilizers,
  currentWeek,
  phaseTransitions,
  tank = null,
  weekOffset = 0,
  weekLabel,
  totalWeeksOverride,
  showMonthHeaders,
  onAddFertilizer,
  onSaveDosage,
  onRemoveDosage,
  onRemoveFertilizerFromAll,
  roPercent,
  onSaveWaterMix,
  onSaveEcTarget,
  cycleRestartWeek,
}: FertilizerGanttChartProps) {
  const { t, i18n } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Manual methods (drench, foliar, …): user-editable volume (e.g. watering can)
  const [manualVolume, setManualVolume] = useState(10);
  const [showManualTotal, setShowManualTotal] = useState(false);

  const groups = useMemo(() => buildMethodGroups(entries, fertilizers), [entries, fertilizers]);

  // Build week → { entryKey, channelId } maps per application method
  const weekChannelMaps = useMemo(() => {
    const maps = new Map<string, Map<number, { entryKey: string; channelId: string }>>();
    const calSize = totalWeeksOverride ?? 52;
    for (const entry of entries) {
      for (const ch of entry.delivery_channels) {
        const method = ch.application_method;
        if (!maps.has(method)) maps.set(method, new Map());
        const wm = maps.get(method)!;
        for (const w of iterEntryWeeks(entry.week_start, entry.week_end, calSize)) {
          wm.set(w, { entryKey: entry.key, channelId: ch.channel_id });
        }
      }
    }
    return maps;
  }, [entries, totalWeeksOverride]);

  // Build week → { roPercent, entryKey } map: per-entry override falls back to plan-level roPercent
  const weekRoMap = useMemo(() => {
    if (roPercent == null && entries.every((e) => e.water_mix_ratio_ro_percent == null)) {
      return null;
    }
    const calSize = totalWeeksOverride ?? 52;
    const map = new Map<number, { ro: number; entryKey: string }>();
    for (const entry of entries) {
      const ro = entry.water_mix_ratio_ro_percent ?? roPercent;
      if (ro == null || ro <= 0) continue;
      for (const w of iterEntryWeeks(entry.week_start, entry.week_end, calSize)) {
        map.set(w, { ro, entryKey: entry.key });
      }
    }
    return map.size > 0 ? map : null;
  }, [entries, roPercent, totalWeeksOverride]);

  // Build week → { ecMs, entryKey, channelId } maps per application method
  const weekEcMaps = useMemo(() => {
    const maps = new Map<string, Map<number, { ec: number; entryKey: string; channelId: string }>>();
    const calSize = totalWeeksOverride ?? 52;
    for (const entry of entries) {
      for (const ch of entry.delivery_channels) {
        if (ch.target_ec_ms == null) continue;
        const method = ch.application_method;
        if (!maps.has(method)) maps.set(method, new Map());
        const wm = maps.get(method)!;
        for (const w of iterEntryWeeks(entry.week_start, entry.week_end, calSize)) {
          wm.set(w, { ec: ch.target_ec_ms, entryKey: entry.key, channelId: ch.channel_id });
        }
      }
    }
    return maps;
  }, [entries, totalWeeksOverride]);

  const totalWeeks = useMemo(() => {
    if (totalWeeksOverride != null) return totalWeeksOverride;
    let max = 0;
    for (const e of entries) {
      if (e.week_end > max) max = e.week_end;
    }
    // Extend to cover phases beyond the last entry (e.g. harvest with no fertilizer)
    if (phaseTransitions && phaseTransitions.length > 0) {
      const lastTransition = phaseTransitions[phaseTransitions.length - 1];
      const phaseEnd = lastTransition.endWeek ?? lastTransition.week + 1;
      if (phaseEnd > max) max = phaseEnd;
    }
    return max - weekOffset;
  }, [entries, phaseTransitions, weekOffset, totalWeeksOverride]);

  // Build transition lookup: week -> PhaseTransition
  const transitionMap = useMemo(() => {
    if (!phaseTransitions || phaseTransitions.length === 0) return null;
    const map = new Map<number, PhaseTransition>();
    for (const pt of phaseTransitions) {
      map.set(pt.week, pt);
    }
    return map;
  }, [phaseTransitions]);

  // Build phase-week lookup: for each week → { phaseName, phaseWeek (1-based within phase) }
  // Prefer transitions (no overlap issues) over entries (can overlap after adaptation)
  const phaseWeekInfo = useMemo(() => {
    const map = new Map<number, { phaseName: string; phaseWeek: number }>();
    if (phaseTransitions && phaseTransitions.length > 0) {
      const calSize = totalWeeksOverride ?? 52;
      const sorted = [...phaseTransitions].sort((a, b) => a.week - b.week);
      for (let i = 0; i < sorted.length; i++) {
        const start = sorted[i].week;
        const rawEnd = i + 1 < sorted.length ? sorted[i + 1].week - 1 : totalWeeks;
        const end = Math.min(rawEnd, calSize);
        for (let w = start; w <= end; w++) {
          map.set(w, { phaseName: sorted[i].phaseName, phaseWeek: w - start + 1 });
        }
        // Handle year-boundary wrap: if endWeek > calSize, fill weeks 1..wrapEnd
        const transEndWeek = sorted[i].endWeek;
        if (transEndWeek != null && transEndWeek > calSize + 1) {
          const wrapEnd = transEndWeek - 1 - calSize;
          const phaseWeekBase = end - start + 2; // continue numbering after end-of-year portion
          for (let w = 1; w <= wrapEnd; w++) {
            map.set(w, { phaseName: sorted[i].phaseName, phaseWeek: phaseWeekBase + w - 1 });
          }
        }
      }
    } else {
      const calSize = totalWeeksOverride ?? 52;
      for (const entry of entries) {
        let phaseWeek = 1;
        for (const w of iterEntryWeeks(entry.week_start, entry.week_end, calSize)) {
          map.set(w, { phaseName: entry.phase_name, phaseWeek });
          phaseWeek++;
        }
      }
    }
    return map;
  }, [entries, phaseTransitions, totalWeeks, totalWeeksOverride]);

  // ── Viewport windowing ────────────────────────────────────────────
  const VIEWPORT_SIZE = 12;
  const needsViewport = totalWeeks > VIEWPORT_SIZE;
  const [showAll, setShowAll] = useState(!needsViewport);
  // Position current week at 1/4 from left — shows more future context (3/4 ahead)
  const viewportOffset = Math.floor(VIEWPORT_SIZE / 4);
  const [viewportStart, setViewportStart] = useState(() => {
    if (!needsViewport) return 1;
    if (currentWeek != null) {
      const absStart = currentWeek - weekOffset;
      const positioned = absStart - viewportOffset;
      return Math.max(1, Math.min(positioned, totalWeeks - VIEWPORT_SIZE + 1));
    }
    return 1;
  });

  // Reset viewport when data changes
  useEffect(() => {
    /* eslint-disable react-hooks/set-state-in-effect -- sync viewport position from props */
    if (!needsViewport) {
      setShowAll(true);
      return;
    }
    if (showAll) return;
    if (currentWeek != null) {
      const absStart = currentWeek - weekOffset;
      const positioned = absStart - viewportOffset;
      setViewportStart(Math.max(1, Math.min(positioned, totalWeeks - VIEWPORT_SIZE + 1)));
    } else {
      setViewportStart(1);
    }
    /* eslint-enable react-hooks/set-state-in-effect */
  }, [totalWeeks, currentWeek, weekOffset, needsViewport]); // eslint-disable-line react-hooks/exhaustive-deps

  const visibleStart = showAll ? 1 : viewportStart;
  const visibleCount = showAll ? totalWeeks : Math.min(VIEWPORT_SIZE, totalWeeks);
  const visibleEnd = visibleStart + visibleCount - 1;
  const canPrev = !showAll && viewportStart > 1;
  const canNext = !showAll && viewportStart + VIEWPORT_SIZE - 1 < totalWeeks;

  const handlePrev = useCallback(() => {
    setViewportStart((s) => Math.max(1, s - VIEWPORT_SIZE));
  }, []);

  const handleNext = useCallback(() => {
    setViewportStart((s) => Math.min(s + VIEWPORT_SIZE, totalWeeks - VIEWPORT_SIZE + 1));
  }, [totalWeeks]);

  if (groups.length === 0 || totalWeeks === 0) return null;

  const hasVolumeToggle = tank != null || groups.some((g) => g.method !== 'fertigation');
  const labelWidth = isMobile ? 100 : 160;
  const weeks = Array.from({ length: visibleCount }, (_, i) => visibleStart + i);

  // Cycle restart separator style (dashed left border on the restart week)
  const cycleRestartSx = (w: number) =>
    cycleRestartWeek != null && w === cycleRestartWeek
      ? { borderLeft: 2, borderLeftColor: 'warning.main', borderLeftStyle: 'dashed' }
      : {};

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* Current week + volume toggle */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
        {currentWeek != null && (
          <Chip
            label={`${t('pages.gantt.currentWeek')}: ${weekLabel ?? t('pages.gantt.week')}${currentWeek}`}
            color="primary"
            variant="outlined"
            size="small"
          />
        )}

        {/* Viewport navigation */}
        {needsViewport && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {!showAll && (
              <>
                <IconButton size="small" onClick={handlePrev} disabled={!canPrev}>
                  <ChevronLeftIcon fontSize="small" />
                </IconButton>
                <Typography variant="caption" color="text.secondary" sx={{ minWidth: 60, textAlign: 'center' }}>
                  {t('pages.gantt.week')}{visibleStart + weekOffset}–{t('pages.gantt.week')}{visibleEnd + weekOffset}
                </Typography>
                <IconButton size="small" onClick={handleNext} disabled={!canNext}>
                  <ChevronRightIcon fontSize="small" />
                </IconButton>
              </>
            )}
            <Tooltip title={showAll ? t('pages.fertilizerGantt.collapseView') : t('pages.fertilizerGantt.expandView')}>
              <IconButton
                size="small"
                onClick={() => setShowAll((v) => !v)}
                color={showAll ? 'primary' : 'default'}
              >
                {showAll ? <UnfoldLessIcon fontSize="small" /> : <UnfoldMoreIcon fontSize="small" />}
              </IconButton>
            </Tooltip>
          </Box>
        )}

        <Box sx={{ flex: 1 }} />
        {tank && (
          <Chip
            label={`${tank.name} (${tank.volumeLiters} L)`}
            size="small"
            variant="outlined"
            color="primary"
          />
        )}
        {hasVolumeToggle && (
          <>
            <Switch
              size="small"
              checked={showManualTotal}
              onChange={(_, checked) => setShowManualTotal(checked)}
            />
            <Typography variant="body2" color={showManualTotal ? 'text.primary' : 'text.secondary'} sx={{ whiteSpace: 'nowrap' }}>
              {t('pages.fertilizerGantt.totalMode')}
            </Typography>
            {showManualTotal && groups.some((g) => g.method !== 'fertigation') && (
              <TextField
                size="small"
                type="number"
                value={manualVolume}
                onChange={(e) => {
                  const v = parseFloat(e.target.value);
                  if (v > 0) setManualVolume(v);
                }}
                slotProps={{
                  input: {
                    endAdornment: <InputAdornment position="end">L</InputAdornment>,
                  },
                  htmlInput: { min: 0.1, step: 0.5 },
                }}
                sx={{ width: 120 }}
              />
            )}
          </>
        )}
      </Box>

      {groups.map((group) => {
        const color = getMethodColor(group.method);

        return (
          <Card key={group.method}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    bgcolor: color,
                    flexShrink: 0,
                  }}
                />
                <Typography variant="h6" sx={{ flex: 1 }}>
                  {t(`enums.applicationMethod.${group.method}`)}
                </Typography>
                {onAddFertilizer && group.channels.length > 0 && (
                  <Button
                    size="small"
                    startIcon={<AddIcon />}
                    onClick={() => {
                      const ch = group.channels[0];
                      onAddFertilizer(ch.entryKey, ch.channelId);
                    }}
                  >
                    {t('pages.nutrientPlans.addFertilizer')}
                  </Button>
                )}
              </Box>

              <Box sx={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch', mx: isMobile ? -1 : 0 }}>
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: `${labelWidth}px repeat(${visibleCount}, 1fr)`,
                    minWidth: labelWidth + visibleCount * (isMobile ? 32 : 48),
                    gap: 0,
                  }}
                >
                  {/* Top-left corner — spans both header rows when phase row exists */}
                  <Box
                    sx={{
                      position: 'sticky',
                      left: 0,
                      bgcolor: 'background.paper',
                      zIndex: 1,
                      borderBottom: 1,
                      borderColor: 'divider',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      py: 0.5,
                      ...(transitionMap && { gridRow: 'span 2' }),
                    }}
                  >
                    {/* Show volume when toggle active */}
                    {showManualTotal &&
                      ((group.method === 'fertigation' && tank) ||
                      (group.method !== 'fertigation')) && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <OpacityIcon fontSize="small" color="primary" />
                        <Typography variant="h5" sx={{ fontWeight: 700 }}>
                          {group.method === 'fertigation' ? tank!.volumeLiters : manualVolume} L
                        </Typography>
                      </Box>
                    )}
                  </Box>
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
                            borderBottom: transitionMap ? 0 : 1,
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
                            borderBottom: transitionMap ? 0 : 1,
                            borderColor: 'divider',
                            py: 0.5,
                            ...(absWeek === currentWeek && {
                              bgcolor: alpha(theme.palette.primary.main, 0.10),
                            }),
                            ...cycleRestartSx(w),
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

                  {/* Phase row with transition dates + phase-internal week */}
                  {transitionMap && (
                    <>
                      {weeks.map((w) => {
                        const absWeek = w + weekOffset;
                        const tr = transitionMap.get(absWeek);
                        const info = phaseWeekInfo.get(absWeek);
                        return (
                          <Box
                            key={w}
                            sx={{
                              textAlign: 'center',
                              borderBottom: 1,
                              borderColor: 'divider',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              py: '2px',
                              ...(absWeek === currentWeek && {
                                bgcolor: alpha(theme.palette.primary.main, 0.10),
                              }),
                              ...cycleRestartSx(w),
                            }}
                          >
                            {tr ? (
                              <Box>
                                <Typography
                                  variant="caption"
                                  sx={{ fontWeight: 600, lineHeight: 1.2, fontSize: '0.65rem', display: 'block' }}
                                  color="text.secondary"
                                >
                                  {t(`enums.phaseName.${tr.phaseName}`)}
                                </Typography>
                                <Typography
                                  variant="caption"
                                  sx={{ lineHeight: 1.2, fontSize: '0.6rem', display: 'block' }}
                                  color="text.secondary"
                                >
                                  {new Date(tr.date).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' })}
                                </Typography>
                              </Box>
                            ) : info ? (
                              <Typography
                                variant="caption"
                                sx={{ fontSize: '0.6rem' }}
                                color="text.disabled"
                              >
                                {info.phaseWeek}
                              </Typography>
                            ) : null}
                          </Box>
                        );
                      })}
                    </>
                  )}

                  {/* Water mix row (RO/tap ratio) — for all water-based methods */}
                  {weekRoMap != null && group.method !== 'top_dress' && (
                    <WaterMixRow
                      weekRoMap={weekRoMap}
                      totalWeeks={visibleCount}
                      visibleStart={visibleStart}
                      labelWidth={labelWidth}
                      t={t}
                      theme={theme}
                      currentWeek={currentWeek}
                      weekOffset={weekOffset}
                      onSave={onSaveWaterMix}
                      cycleRestartWeek={cycleRestartWeek}
                    />
                  )}

                  {/* EC target row */}
                  {weekEcMaps.has(group.method) && (
                    <EcTargetRow
                      weekEcMap={weekEcMaps.get(group.method)!}
                      totalWeeks={visibleCount}
                      visibleStart={visibleStart}
                      labelWidth={labelWidth}
                      t={t}
                      theme={theme}
                      currentWeek={currentWeek}
                      weekOffset={weekOffset}
                      onSave={onSaveEcTarget}
                      cycleRestartWeek={cycleRestartWeek}
                    />
                  )}

                  {/* Fertilizer rows */}
                  {group.rows.map((row) => (
                    <FertilizerRow
                      key={row.fertKey}
                      row={row}
                      color={color}
                      totalWeeks={visibleCount}
                      visibleStart={visibleStart}
                      labelWidth={labelWidth}
                      t={t}
                      theme={theme}
                      currentWeek={currentWeek}
                      phaseInfo={phaseWeekInfo}
                      weekOffset={weekOffset}
                      weekChannelMap={weekChannelMaps.get(group.method) ?? new Map()}
                      showTotal={
                        group.method === 'fertigation'
                          ? showManualTotal && !!tank
                          : showManualTotal
                      }
                      volumeLiters={
                        group.method === 'fertigation'
                          ? (tank?.volumeLiters ?? 0)
                          : manualVolume
                      }
                      onSaveDosage={onSaveDosage}
                      onRemoveDosage={onRemoveDosage}
                      onRemoveFertilizerFromAll={onRemoveFertilizerFromAll}
                      cycleRestartWeek={cycleRestartWeek}
                    />
                  ))}
                </Box>
              </Box>
            </CardContent>
          </Card>
        );
      })}

      {/* Legend */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, flexWrap: 'wrap', px: 0.5 }}>
        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
          {t('pages.fertilizerGantt.legendTitle')}:
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 32,
              height: 14,
              bgcolor: alpha('#1976d2', 0.7),
              borderRadius: 0.5,
              flexShrink: 0,
            }}
          />
          <Typography variant="caption" color="text.secondary">
            {t('pages.fertilizerGantt.legendDefined')}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box
            sx={{
              width: 32,
              height: 14,
              background: `repeating-linear-gradient(-45deg, ${alpha('#1976d2', 0.35)}, ${alpha('#1976d2', 0.35)} 3px, ${alpha('#1976d2', 0.12)} 3px, ${alpha('#1976d2', 0.12)} 6px)`,
              borderRadius: 0.5,
              flexShrink: 0,
            }}
          />
          <Typography variant="caption" color="text.secondary">
            {t('pages.fertilizerGantt.legendExtrapolated')}
          </Typography>
        </Box>
        {cycleRestartWeek != null && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 0,
                height: 14,
                borderLeft: 2,
                borderLeftColor: 'warning.main',
                borderLeftStyle: 'dashed',
                flexShrink: 0,
              }}
            />
            <Typography variant="caption" color="text.secondary">
              {t('pages.fertilizerGantt.legendCycleRestart')}
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  );
}

// ── Dosage Edit Popover ─────────────────────────────────────────────

interface DosagePopoverState {
  anchorEl: HTMLElement;
  entryKey: string;
  channelId: string;
  fertilizerKey: string;
  fertName: string;
  mlPerLiter: number;
  phaseName: string;
  week: number;
}

function DosageEditPopover({
  state,
  onClose,
  onSave,
  onRemove,
  t,
}: {
  state: DosagePopoverState | null;
  onClose: () => void;
  onSave: (payload: DosageSavePayload) => void;
  onRemove?: (payload: DosageRemovePayload) => void;
  t: (key: string, opts?: Record<string, unknown>) => string;
}) {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (state) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- sync popover value from state prop
      setValue(String(state.mlPerLiter));
      // Auto-focus + select after popover opens
      setTimeout(() => inputRef.current?.select(), 50);
    }
  }, [state]);

  const handleSave = useCallback(() => {
    if (!state) return;
    const parsed = parseFloat(value);
    if (Number.isNaN(parsed) || parsed < 0) return;
    onSave({
      entryKey: state.entryKey,
      channelId: state.channelId,
      fertilizerKey: state.fertilizerKey,
      mlPerLiter: parsed,
    });
    onClose();
  }, [state, value, onSave, onClose]);

  const handleRemove = useCallback(() => {
    if (!state || !onRemove) return;
    onRemove({
      entryKey: state.entryKey,
      channelId: state.channelId,
      fertilizerKey: state.fertilizerKey,
    });
    onClose();
  }, [state, onRemove, onClose]);

  return (
    <Popover
      open={state != null}
      anchorEl={state?.anchorEl ?? null}
      onClose={onClose}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      transformOrigin={{ vertical: 'top', horizontal: 'center' }}
      slotProps={{ paper: { sx: { p: 2, minWidth: 220 } } }}
    >
      {state && (
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
            {state.fertName}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1.5 }}>
            {t(`enums.phaseName.${state.phaseName}`)} &middot; {t('pages.gantt.week')}{state.week}
          </Typography>

          <TextField
            inputRef={inputRef}
            size="small"
            type="number"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSave();
              if (e.key === 'Escape') onClose();
            }}
            slotProps={{
              input: {
                endAdornment: <InputAdornment position="end">ml/L</InputAdornment>,
              },
              htmlInput: { min: 0, step: 0.1 },
            }}
            fullWidth
            autoFocus
          />

          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1.5 }}>
            {onRemove ? (
              <IconButton size="small" color="error" onClick={handleRemove}>
                <DeleteOutlineIcon fontSize="small" />
              </IconButton>
            ) : (
              <Box />
            )}
            <Box sx={{ display: 'flex', gap: 0.5 }}>
              <IconButton size="small" onClick={onClose}>
                <CloseIcon fontSize="small" />
              </IconButton>
              <IconButton size="small" color="primary" onClick={handleSave}>
                <CheckIcon fontSize="small" />
              </IconButton>
            </Box>
          </Box>
        </Box>
      )}
    </Popover>
  );
}

// ── Inline value edit popover (shared by water-mix and EC rows) ─────

interface InlinePopoverState {
  anchorEl: HTMLElement;
  value: number;
  entryKey: string;
  channelId?: string;
  label: string;
  week: number;
}

function InlineValuePopover({
  state,
  onClose,
  onSave,
  unit,
  min,
  max,
  step,
}: {
  state: InlinePopoverState | null;
  onClose: () => void;
  onSave: (state: InlinePopoverState, newValue: number) => void;
  unit: string;
  min: number;
  max: number;
  step: number;
}) {
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (state) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- sync popover value from state prop
      setValue(String(state.value));
      setTimeout(() => inputRef.current?.select(), 50);
    }
  }, [state]);

  const handleSave = useCallback(() => {
    if (!state) return;
    const parsed = parseFloat(value);
    if (Number.isNaN(parsed) || parsed < min) return;
    onSave(state, parsed);
    onClose();
  }, [state, value, onSave, onClose, min]);

  return (
    <Popover
      open={state != null}
      anchorEl={state?.anchorEl ?? null}
      onClose={onClose}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      transformOrigin={{ vertical: 'top', horizontal: 'center' }}
      slotProps={{ paper: { sx: { p: 2, minWidth: 200 } } }}
    >
      {state && (
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
            {state.label}
          </Typography>
          <TextField
            inputRef={inputRef}
            size="small"
            type="number"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSave();
              if (e.key === 'Escape') onClose();
            }}
            slotProps={{
              input: { endAdornment: <InputAdornment position="end">{unit}</InputAdornment> },
              htmlInput: { min, max, step },
            }}
            fullWidth
            autoFocus
          />
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
            <IconButton size="small" onClick={onClose}>
              <CloseIcon fontSize="small" />
            </IconButton>
            <IconButton size="small" color="primary" onClick={handleSave}>
              <CheckIcon fontSize="small" />
            </IconButton>
          </Box>
        </Box>
      )}
    </Popover>
  );
}

// ── Water mix row (RO/tap ratio) ────────────────────────────────────

const WATER_COLOR = '#0288d1'; // light-blue 700

function WaterMixRow({
  weekRoMap,
  totalWeeks,
  visibleStart = 1,
  labelWidth,
  t,
  theme,
  currentWeek,
  weekOffset = 0,
  onSave,
  cycleRestartWeek,
}: {
  weekRoMap: Map<number, { ro: number; entryKey: string }>;
  totalWeeks: number;
  visibleStart?: number;
  labelWidth: number;
  t: (key: string, opts?: Record<string, unknown>) => string;
  theme: Theme;
  currentWeek?: number;
  weekOffset?: number;
  onSave?: (payload: WaterMixSavePayload) => void;
  cycleRestartWeek?: number;
}) {
  const weeks = Array.from({ length: totalWeeks }, (_, i) => visibleStart + i);
  const [popover, setPopover] = useState<InlinePopoverState | null>(null);
  const editable = !!onSave;

  const handleSave = useCallback(
    (state: InlinePopoverState, newValue: number) => {
      if (!onSave) return;
      onSave({ entryKey: state.entryKey, roPercent: newValue });
    },
    [onSave],
  );

  return (
    <>
      {/* Label cell */}
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
        <Box sx={{ minWidth: 0 }}>
          <Typography variant="body2" noWrap sx={{ fontWeight: 600, maxWidth: labelWidth - 16 }}>
            {t('pages.fertilizerGantt.roWater')}
          </Typography>
          <Typography variant="caption" noWrap color="text.secondary" sx={{ lineHeight: 1.2 }}>
            %
          </Typography>
        </Box>
      </Box>

      {/* Bar cells */}
      {weeks.map((w) => {
        const absWeek = w + weekOffset;
        const info = weekRoMap.get(absWeek);
        const crSx = cycleRestartWeek != null && w === cycleRestartWeek ? { borderLeft: 2, borderLeftColor: 'warning.main', borderLeftStyle: 'dashed' } : {};
        if (!info) {
          return (
            <Box key={w} sx={{ py: 0.75, px: '2px', borderBottom: 1, borderColor: 'divider', ...crSx }} />
          );
        }
        // Lighter = higher RO: opacity goes from 0.15 (0% RO) to 0.85 (100% RO)
        const cellAlpha = 0.15 + (info.ro / 100) * 0.7;
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
              ...(absWeek === currentWeek && {
                bgcolor: alpha(theme.palette.primary.main, 0.10),
              }),
              ...crSx,
            }}
          >
            <Tooltip
              title={`${info.ro}% ${t('pages.fertilizerGantt.roWater')}`}
              arrow
              disableHoverListener={popover != null}
              disableFocusListener={popover != null}
            >
              <Box
                onClick={editable ? (e: React.MouseEvent<HTMLElement>) => {
                  setPopover({
                    anchorEl: e.currentTarget,
                    value: info.ro,
                    entryKey: info.entryKey,
                    label: t('pages.fertilizerGantt.roWater'),
                    week: absWeek,
                  });
                } : undefined}
                sx={{
                  width: '100%',
                  height: 24,
                  bgcolor: alpha(WATER_COLOR, cellAlpha),
                  borderRadius: 0.5,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  overflow: 'hidden',
                  ...(editable && {
                    cursor: 'pointer',
                    transition: 'filter 0.15s',
                    '&:hover': { filter: 'brightness(1.15)' },
                  }),
                }}
              >
                <Typography
                  sx={{
                    fontSize: '0.7rem',
                    lineHeight: 1,
                    color: info.ro >= 50 ? '#fff' : 'text.primary',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {info.ro}%
                </Typography>
              </Box>
            </Tooltip>
          </Box>
        );
      })}

      {onSave && (
        <InlineValuePopover
          state={popover}
          onClose={() => setPopover(null)}
          onSave={handleSave}
          unit="%"
          min={0}
          max={100}
          step={5}
        />
      )}
    </>
  );
}

// ── EC target row ───────────────────────────────────────────────────

const EC_COLOR = '#f57c00'; // orange 700

function EcTargetRow({
  weekEcMap,
  totalWeeks,
  visibleStart = 1,
  labelWidth,
  t,
  theme,
  currentWeek,
  weekOffset = 0,
  onSave,
  cycleRestartWeek,
}: {
  weekEcMap: Map<number, { ec: number; entryKey: string; channelId: string }>;
  totalWeeks: number;
  visibleStart?: number;
  labelWidth: number;
  t: (key: string, opts?: Record<string, unknown>) => string;
  theme: Theme;
  currentWeek?: number;
  weekOffset?: number;
  onSave?: (payload: EcTargetSavePayload) => void;
  cycleRestartWeek?: number;
}) {
  const weeks = Array.from({ length: totalWeeks }, (_, i) => visibleStart + i);
  const [popover, setPopover] = useState<InlinePopoverState | null>(null);
  const editable = !!onSave;

  const handleSave = useCallback(
    (state: InlinePopoverState, newValue: number) => {
      if (!onSave || !state.channelId) return;
      onSave({ entryKey: state.entryKey, channelId: state.channelId, ecMs: newValue });
    },
    [onSave],
  );

  // Find max EC across all weeks for relative color intensity
  const maxEc = useMemo(() => {
    let m = 0;
    for (const v of weekEcMap.values()) {
      if (v.ec > m) m = v.ec;
    }
    return m || 1;
  }, [weekEcMap]);

  return (
    <>
      {/* Label cell */}
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
        <Box sx={{ minWidth: 0 }}>
          <Typography variant="body2" noWrap sx={{ fontWeight: 600, maxWidth: labelWidth - 16 }}>
            {t('pages.fertilizerGantt.ecTarget')}
          </Typography>
          <Typography variant="caption" noWrap color="text.secondary" sx={{ lineHeight: 1.2 }}>
            mS/cm
          </Typography>
        </Box>
      </Box>

      {/* Bar cells */}
      {weeks.map((w) => {
        const absWeek = w + weekOffset;
        const info = weekEcMap.get(absWeek);
        const crSx = cycleRestartWeek != null && w === cycleRestartWeek ? { borderLeft: 2, borderLeftColor: 'warning.main', borderLeftStyle: 'dashed' } : {};
        if (!info) {
          return (
            <Box key={w} sx={{ py: 0.75, px: '2px', borderBottom: 1, borderColor: 'divider', ...crSx }} />
          );
        }
        const cellAlpha = 0.2 + (info.ec / maxEc) * 0.6;
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
              ...(absWeek === currentWeek && {
                bgcolor: alpha(theme.palette.primary.main, 0.10),
              }),
              ...crSx,
            }}
          >
            <Tooltip
              title={`EC ${info.ec} mS/cm`}
              arrow
              disableHoverListener={popover != null}
              disableFocusListener={popover != null}
            >
              <Box
                onClick={editable ? (e: React.MouseEvent<HTMLElement>) => {
                  setPopover({
                    anchorEl: e.currentTarget,
                    value: info.ec,
                    entryKey: info.entryKey,
                    channelId: info.channelId,
                    label: t('pages.fertilizerGantt.ecTarget'),
                    week: absWeek,
                  });
                } : undefined}
                sx={{
                  width: '100%',
                  height: 24,
                  bgcolor: alpha(EC_COLOR, cellAlpha),
                  borderRadius: 0.5,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  overflow: 'hidden',
                  ...(editable && {
                    cursor: 'pointer',
                    transition: 'filter 0.15s',
                    '&:hover': { filter: 'brightness(1.15)' },
                  }),
                }}
              >
                <Typography
                  sx={{
                    fontSize: '0.7rem',
                    lineHeight: 1,
                    color: cellAlpha >= 0.5 ? '#fff' : 'text.primary',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {info.ec}
                </Typography>
              </Box>
            </Tooltip>
          </Box>
        );
      })}

      {onSave && (
        <InlineValuePopover
          state={popover}
          onClose={() => setPopover(null)}
          onSave={handleSave}
          unit="mS/cm"
          min={0}
          max={10}
          step={0.1}
        />
      )}
    </>
  );
}

// ── Fertilizer row ──────────────────────────────────────────────────

interface ExtendedWeekInfo {
  mlPerLiter: number;
}

function FertilizerRow({
  row,
  color,
  totalWeeks,
  visibleStart = 1,
  labelWidth,
  t,
  theme,
  currentWeek,
  phaseInfo,
  showTotal,
  volumeLiters,
  weekOffset = 0,
  weekChannelMap,
  onSaveDosage,
  onRemoveDosage,
  onRemoveFertilizerFromAll,
  cycleRestartWeek,
}: {
  row: FertilizerRow;
  color: string;
  totalWeeks: number;
  visibleStart?: number;
  labelWidth: number;
  t: (key: string, opts?: Record<string, unknown>) => string;
  theme: Theme;
  currentWeek?: number;
  phaseInfo: Map<number, { phaseName: string; phaseWeek: number }>;
  showTotal: boolean;
  volumeLiters: number;
  weekOffset?: number;
  weekChannelMap: Map<number, { entryKey: string; channelId: string }>;
  onSaveDosage?: (payload: DosageSavePayload) => void;
  onRemoveDosage?: (payload: DosageRemovePayload) => void;
  onRemoveFertilizerFromAll?: (payload: FertilizerRemoveAllPayload) => void;
  cycleRestartWeek?: number;
}) {
  const weeks = Array.from({ length: totalWeeks }, (_, i) => visibleStart + i);
  const [popover, setPopover] = useState<DosagePopoverState | null>(null);
  const [tooltipWeek, setTooltipWeek] = useState<number | null>(null);

  const handleCellClick = useCallback(
    (e: React.MouseEvent<HTMLElement>, span: FertSpan, absWeek: number) => {
      if (!onSaveDosage) return;
      setTooltipWeek(null);
      setPopover({
        anchorEl: e.currentTarget,
        entryKey: span.entryKey,
        channelId: span.channelId,
        fertilizerKey: row.fertKey,
        fertName: row.fertName,
        mlPerLiter: span.mlPerLiter,
        phaseName: span.phaseName,
        week: absWeek,
      });
    },
    [onSaveDosage, row.fertKey, row.fertName],
  );

  const handleEmptyCellClick = useCallback(
    (e: React.MouseEvent<HTMLElement>, absWeek: number) => {
      if (!onSaveDosage) return;
      const channel = weekChannelMap.get(absWeek);
      if (!channel) return;
      const info = phaseInfo.get(absWeek);
      if (!info) return;
      setTooltipWeek(null);
      setPopover({
        anchorEl: e.currentTarget,
        entryKey: channel.entryKey,
        channelId: channel.channelId,
        fertilizerKey: row.fertKey,
        fertName: row.fertName,
        mlPerLiter: 0,
        phaseName: info.phaseName,
        week: absWeek,
      });
    },
    [onSaveDosage, row.fertKey, row.fertName, weekChannelMap, phaseInfo],
  );

  // Precompute extended weeks: fill gaps within the same phase with the
  // last active dosage. These are rendered with a striped pattern.
  // Keys in this map are relative week numbers (1..totalWeeks).
  const extendedWeeks = useMemo(() => {
    if (phaseInfo.size === 0) return new Map<number, ExtendedWeekInfo>();
    const map = new Map<number, ExtendedWeekInfo>();
    let lastDosage: number | null = null;
    let lastPhase: string | null = null;

    for (const w of weeks) {
      const absW = w + weekOffset;
      const activeSpans = row.spans.filter((s) => spanContainsWeek(s, absW));
      const phase = phaseInfo.get(absW)?.phaseName ?? null;

      if (activeSpans.length > 0) {
        lastDosage = Math.max(...activeSpans.map((s) => s.mlPerLiter));
        lastPhase = phase;
      } else if (lastDosage !== null && phase !== null && phase === lastPhase && (!currentWeek || absW <= currentWeek)) {
        map.set(w, { mlPerLiter: lastDosage });
      } else {
        lastDosage = null;
        lastPhase = null;
      }
    }

    return map;
  }, [row.spans, phaseInfo, weeks, weekOffset, currentWeek]);

  const editable = !!onSaveDosage;

  return (
    <>
      {/* Fertilizer label cell */}
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
        <Box sx={{ minWidth: 0, flex: 1 }}>
          <Typography
            variant="body2"
            noWrap
            sx={{ fontWeight: 600, maxWidth: labelWidth - (onRemoveFertilizerFromAll ? 40 : 16) }}
          >
            {row.fertName}
          </Typography>
          {row.brand && (
            <Typography
              variant="caption"
              noWrap
              color="text.secondary"
              sx={{ lineHeight: 1.2 }}
            >
              {row.brand}
            </Typography>
          )}
        </Box>
        {onRemoveFertilizerFromAll && (
          <Tooltip title={t('pages.fertilizerGantt.removeFertilizer')} arrow>
            <IconButton
              size="small"
              color="error"
              onClick={() => {
                // Collect unique entry/channel pairs from all spans
                const seen = new Set<string>();
                const targets: { entryKey: string; channelId: string }[] = [];
                for (const span of row.spans) {
                  const id = `${span.entryKey}::${span.channelId}`;
                  if (!seen.has(id)) {
                    seen.add(id);
                    targets.push({ entryKey: span.entryKey, channelId: span.channelId });
                  }
                }
                onRemoveFertilizerFromAll({
                  fertilizerKey: row.fertKey,
                  fertilizerName: row.fertName,
                  targets,
                });
              }}
              sx={{ flexShrink: 0, ml: 0.25, p: 0.25 }}
            >
              <DeleteOutlineIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      {/* Bar cells */}
      {weeks.map((w) => {
        const absWeek = w + weekOffset;
        const activeSpans = row.spans.filter((s) => spanContainsWeek(s, absWeek));
        const inRange = activeSpans.length > 0;
        const extended = !inRange ? extendedWeeks.get(w) : undefined;
        const isStart = inRange && activeSpans.some((s) => isSpanStart(s, absWeek));
        const isEnd = inRange && activeSpans.some((s) => isSpanEnd(s, absWeek));
        // Extended bars: check neighbours for rounded corners
        const extStart = !!extended && !extendedWeeks.has(w - 1);
        const extEnd = !!extended && !extendedWeeks.has(w + 1);

        // Format dosage: ml/L or total ml based on toggle
        const fmtDose = (mlPerLiter: number) =>
          showTotal
            ? `${Math.round(mlPerLiter * volumeLiters * 10) / 10} ml`
            : `${mlPerLiter} ml/L`;

        const cellTooltip = inRange
          ? [
              row.fertName,
              row.brand ? `(${row.brand})` : null,
              ...activeSpans.map((s) => fmtDose(s.mlPerLiter)),
              editable ? t('pages.fertilizerGantt.clickToEdit') : null,
            ]
              .filter(Boolean)
              .join('\n')
          : extended
            ? [
                row.fertName,
                row.brand ? `(${row.brand})` : null,
                `${fmtDose(extended.mlPerLiter)} (${t('pages.fertilizerGantt.extrapolated')})`,
              ]
                .filter(Boolean)
                .join('\n')
            : '';

        // Whether this empty cell has a valid entry/channel (can be assigned)
        const emptyAssignable = !inRange && !extended && editable && weekChannelMap.has(absWeek);

        const crSx = cycleRestartWeek != null && w === cycleRestartWeek ? { borderLeft: 2, borderLeftColor: 'warning.main', borderLeftStyle: 'dashed' } : {};
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
              ...(absWeek === currentWeek && {
                bgcolor: alpha(theme.palette.primary.main, 0.10),
              }),
              ...crSx,
            }}
          >
            {inRange && (
              <Tooltip
                title={<Box sx={{ whiteSpace: 'pre-line' }}>{cellTooltip}</Box>}
                arrow
                open={tooltipWeek === w && popover == null}
                onOpen={() => { if (popover == null) setTooltipWeek(w); }}
                onClose={() => setTooltipWeek(null)}
                disableHoverListener={popover != null}
                disableFocusListener={popover != null}
              >
                <Box
                  onClick={editable ? (e: React.MouseEvent<HTMLElement>) => handleCellClick(e, activeSpans[0], absWeek) : undefined}
                  sx={{
                    width: '100%',
                    height: 24,
                    bgcolor: alpha(color, 0.7),
                    borderRadius: `${isStart ? 4 : 0}px ${isEnd ? 4 : 0}px ${isEnd ? 4 : 0}px ${isStart ? 4 : 0}px`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    overflow: 'hidden',
                    ...(editable && {
                      cursor: 'pointer',
                      transition: 'filter 0.15s',
                      '&:hover': { filter: 'brightness(1.2)' },
                    }),
                  }}
                >
                  <Typography
                    sx={{ fontSize: '0.7rem', lineHeight: 1, color: '#fff', fontWeight: 600, whiteSpace: 'nowrap' }}
                  >
                    {fmtDose(activeSpans[0].mlPerLiter)}
                  </Typography>
                </Box>
              </Tooltip>
            )}
            {extended && (
              <Tooltip
                title={<Box sx={{ whiteSpace: 'pre-line' }}>{cellTooltip}</Box>}
                arrow
                open={tooltipWeek === w && popover == null}
                onOpen={() => { if (popover == null) setTooltipWeek(w); }}
                onClose={() => setTooltipWeek(null)}
                disableHoverListener={popover != null}
                disableFocusListener={popover != null}
              >
                <Box
                  sx={{
                    width: '100%',
                    height: 24,
                    background: `repeating-linear-gradient(-45deg, ${alpha(color, 0.35)}, ${alpha(color, 0.35)} 3px, ${alpha(color, 0.12)} 3px, ${alpha(color, 0.12)} 6px)`,
                    borderRadius: `${extStart ? 4 : 0}px ${extEnd ? 4 : 0}px ${extEnd ? 4 : 0}px ${extStart ? 4 : 0}px`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    overflow: 'hidden',
                  }}
                >
                  <Typography
                    sx={{ fontSize: '0.7rem', lineHeight: 1, color: 'text.secondary', fontWeight: 500, whiteSpace: 'nowrap' }}
                  >
                    {fmtDose(extended.mlPerLiter)}
                  </Typography>
                </Box>
              </Tooltip>
            )}
            {emptyAssignable && (
              <Box
                onClick={(e: React.MouseEvent<HTMLElement>) => handleEmptyCellClick(e, absWeek)}
                sx={{
                  width: '100%',
                  height: 24,
                  borderRadius: 1,
                  cursor: 'pointer',
                  transition: 'background-color 0.15s',
                  '&:hover': {
                    bgcolor: alpha(color, 0.08),
                  },
                }}
              />
            )}
          </Box>
        );
      })}

      {/* Inline dosage edit popover */}
      {onSaveDosage && (
        <DosageEditPopover
          state={popover}
          onClose={() => setPopover(null)}
          onSave={onSaveDosage}
          onRemove={onRemoveDosage}
          t={t}
        />
      )}
    </>
  );
}
