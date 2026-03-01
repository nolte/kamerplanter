import { useMemo, useState } from 'react';
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
import OpacityIcon from '@mui/icons-material/Opacity';
import { alpha, useTheme, type Theme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import type { NutrientPlanPhaseEntry, Fertilizer } from '@/api/types';

// ── Data transformation ─────────────────────────────────────────────

interface FertSpan {
  weekStart: number;
  weekEnd: number;
  phaseName: string;
  mlPerLiter: number;
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
}

function buildMethodGroups(
  entries: NutrientPlanPhaseEntry[],
  fertilizers: Fertilizer[],
): MethodGroup[] {
  const fertLookup = new Map(fertilizers.map((f) => [f.key, f]));
  // method -> fertKey -> FertilizerRow
  const groupMap = new Map<string, Map<string, FertilizerRow>>();

  for (const entry of entries) {
    for (const ch of entry.delivery_channels) {
      const method = ch.application_method;
      if (!groupMap.has(method)) {
        groupMap.set(method, new Map());
      }
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
        });
      }
    }
  }

  return [...groupMap.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([method, fertMap]) => ({
      method,
      rows: [...fertMap.values()].sort((a, b) => a.fertName.localeCompare(b.fertName)),
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
  date: string;
  phaseName: string;  // phase_name value (e.g. "vegetative", "flowering")
}

// ── Component ───────────────────────────────────────────────────────

interface FertilizerGanttChartProps {
  entries: NutrientPlanPhaseEntry[];
  fertilizers: Fertilizer[];
  currentWeek?: number;
  phaseTransitions?: PhaseTransition[];
  tank?: ResolvedTank | null;
}

export default function FertilizerGanttChart({
  entries,
  fertilizers,
  currentWeek,
  phaseTransitions,
  tank = null,
}: FertilizerGanttChartProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Manual methods (drench, foliar, …): user-editable volume (e.g. watering can)
  const [manualVolume, setManualVolume] = useState(10);
  const [showManualTotal, setShowManualTotal] = useState(false);

  const groups = useMemo(() => buildMethodGroups(entries, fertilizers), [entries, fertilizers]);

  const totalWeeks = useMemo(() => {
    let max = 0;
    for (const e of entries) {
      if (e.week_end > max) max = e.week_end;
    }
    // Extend to cover phases beyond the last entry (e.g. harvest with no fertilizer)
    if (phaseTransitions && phaseTransitions.length > 0) {
      const lastTransition = phaseTransitions[phaseTransitions.length - 1];
      // Add at least 1 week for the last phase to be visible
      if (lastTransition.week >= max) max = lastTransition.week + 1;
    }
    return max;
  }, [entries, phaseTransitions]);

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
      const sorted = [...phaseTransitions].sort((a, b) => a.week - b.week);
      for (let i = 0; i < sorted.length; i++) {
        const start = sorted[i].week;
        const end = i + 1 < sorted.length ? sorted[i + 1].week - 1 : totalWeeks;
        for (let w = start; w <= end; w++) {
          map.set(w, { phaseName: sorted[i].phaseName, phaseWeek: w - start + 1 });
        }
      }
    } else {
      for (const entry of entries) {
        for (let w = entry.week_start; w <= entry.week_end; w++) {
          map.set(w, { phaseName: entry.phase_name, phaseWeek: w - entry.week_start + 1 });
        }
      }
    }
    return map;
  }, [entries, phaseTransitions, totalWeeks]);

  if (groups.length === 0 || totalWeeks === 0) return null;

  const hasManualMethods = groups.some((g) => g.method !== 'fertigation');
  const labelWidth = isMobile ? 120 : 160;
  const weeks = Array.from({ length: totalWeeks }, (_, i) => i + 1);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {/* Current week + volume toggle */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
        {currentWeek != null && (
          <Chip
            label={`${t('pages.gantt.currentWeek')}: ${t('pages.gantt.week')}${currentWeek}`}
            color="primary"
            variant="outlined"
            size="small"
          />
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
        {hasManualMethods && (
          <>
            <Switch
              size="small"
              checked={showManualTotal}
              onChange={(_, checked) => setShowManualTotal(checked)}
            />
            <Typography variant="body2" color={showManualTotal ? 'text.primary' : 'text.secondary'} sx={{ whiteSpace: 'nowrap' }}>
              {t('pages.fertilizerGantt.totalMode')}
            </Typography>
            {showManualTotal && (
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
                <Typography variant="h6">
                  {t(`enums.applicationMethod.${group.method}`)}
                </Typography>
              </Box>

              <Box sx={{ overflowX: 'auto' }}>
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: `${labelWidth}px repeat(${totalWeeks}, 1fr)`,
                    minWidth: labelWidth + totalWeeks * 48,
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
                    {/* Fertigation: always show tank volume; manual: show when toggled */}
                    {((group.method === 'fertigation' && tank) ||
                      (group.method !== 'fertigation' && showManualTotal)) && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <OpacityIcon fontSize="small" color="primary" />
                        <Typography variant="h5" sx={{ fontWeight: 700 }}>
                          {group.method === 'fertigation' ? tank!.volumeLiters : manualVolume} L
                        </Typography>
                      </Box>
                    )}
                  </Box>
                  {weeks.map((w) => (
                    <Box
                      key={w}
                      role="columnheader"
                      sx={{
                        textAlign: 'center',
                        borderBottom: transitionMap ? 0 : 1,
                        borderColor: 'divider',
                        py: 0.5,
                        ...(w === currentWeek && {
                          bgcolor: alpha(theme.palette.primary.main, 0.10),
                        }),
                      }}
                    >
                      <Typography
                        variant="caption"
                        color={w === currentWeek ? 'primary' : 'text.secondary'}
                        sx={w === currentWeek ? { fontWeight: 700 } : undefined}
                      >
                        {t('pages.gantt.week')}{w}
                      </Typography>
                    </Box>
                  ))}

                  {/* Phase row with transition dates + phase-internal week */}
                  {transitionMap && (
                    <>
                      {weeks.map((w) => {
                        const tr = transitionMap.get(w);
                        const info = phaseWeekInfo.get(w);
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
                              ...(w === currentWeek && {
                                bgcolor: alpha(theme.palette.primary.main, 0.10),
                              }),
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

                  {/* Fertilizer rows */}
                  {group.rows.map((row) => (
                    <FertilizerRow
                      key={row.fertKey}
                      row={row}
                      color={color}
                      totalWeeks={totalWeeks}
                      labelWidth={labelWidth}
                      t={t}
                      theme={theme}
                      currentWeek={currentWeek}
                      phaseInfo={phaseWeekInfo}
                      showTotal={
                        group.method === 'fertigation'
                          ? !!tank
                          : showManualTotal
                      }
                      volumeLiters={
                        group.method === 'fertigation'
                          ? (tank?.volumeLiters ?? 0)
                          : manualVolume
                      }
                    />
                  ))}
                </Box>
              </Box>
            </CardContent>
          </Card>
        );
      })}
    </Box>
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
  labelWidth,
  t,
  theme,
  currentWeek,
  phaseInfo,
  showTotal,
  volumeLiters,
}: {
  row: FertilizerRow;
  color: string;
  totalWeeks: number;
  labelWidth: number;
  t: (key: string, opts?: Record<string, unknown>) => string;
  theme: Theme;
  currentWeek?: number;
  phaseInfo: Map<number, { phaseName: string; phaseWeek: number }>;
  showTotal: boolean;
  volumeLiters: number;
}) {
  const weeks = Array.from({ length: totalWeeks }, (_, i) => i + 1);

  // Precompute extended weeks: fill gaps within the same phase with the
  // last active dosage. These are rendered with a striped pattern.
  const extendedWeeks = useMemo(() => {
    if (phaseInfo.size === 0) return new Map<number, ExtendedWeekInfo>();
    const map = new Map<number, ExtendedWeekInfo>();
    let lastDosage: number | null = null;
    let lastPhase: string | null = null;

    for (const w of weeks) {
      const activeSpans = row.spans.filter((s) => w >= s.weekStart && w <= s.weekEnd);
      const phase = phaseInfo.get(w)?.phaseName ?? null;

      if (activeSpans.length > 0) {
        lastDosage = Math.max(...activeSpans.map((s) => s.mlPerLiter));
        lastPhase = phase;
      } else if (lastDosage !== null && phase !== null && phase === lastPhase && (!currentWeek || w <= currentWeek)) {
        map.set(w, { mlPerLiter: lastDosage });
      } else {
        lastDosage = null;
        lastPhase = null;
      }
    }

    return map;
  }, [row.spans, phaseInfo, weeks]);

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
        <Box sx={{ minWidth: 0 }}>
          <Typography
            variant="body2"
            noWrap
            sx={{ fontWeight: 600, maxWidth: labelWidth - 16 }}
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
      </Box>

      {/* Bar cells */}
      {weeks.map((w) => {
        const activeSpans = row.spans.filter((s) => w >= s.weekStart && w <= s.weekEnd);
        const inRange = activeSpans.length > 0;
        const extended = !inRange ? extendedWeeks.get(w) : undefined;
        const isStart = inRange && activeSpans.some((s) => w === s.weekStart);
        const isEnd = inRange && activeSpans.some((s) => w === s.weekEnd);
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
              ...(w === currentWeek && {
                bgcolor: alpha(theme.palette.primary.main, 0.10),
              }),
            }}
          >
            {inRange && (
              <Tooltip
                title={<Box sx={{ whiteSpace: 'pre-line' }}>{cellTooltip}</Box>}
                arrow
              >
                <Box
                  sx={{
                    width: '100%',
                    height: 24,
                    bgcolor: alpha(color, 0.7),
                    borderRadius: `${isStart ? 4 : 0}px ${isEnd ? 4 : 0}px ${isEnd ? 4 : 0}px ${isStart ? 4 : 0}px`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    overflow: 'hidden',
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
          </Box>
        );
      })}
    </>
  );
}
