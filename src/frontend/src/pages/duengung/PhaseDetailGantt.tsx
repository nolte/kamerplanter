import { useMemo, useCallback, useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import { alpha, useTheme, type Theme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import type { NutrientPlanPhaseEntry, Fertilizer, ApplicationMethod } from '@/api/types';
import { PHASE_COLORS } from './PhaseGanttChart';

const AUTO_METHODS = new Set<ApplicationMethod>(['fertigation']);
const WATER_COLOR = '#0288d1'; // light-blue 700

interface Props {
  entries: NutrientPlanPhaseEntry[];
  fertilizers: Fertilizer[];
  title: string;
  currentWeek?: number;
  onEntriesChange?: (updatedEntries: NutrientPlanPhaseEntry[]) => void;
}

interface FertRow {
  fertKey: string;
  name: string;
  brand: string;
  mixingOrder: number;
  weekMap: Map<number, number>;
}

interface ChannelGroup {
  groupKey: 'auto' | 'manual';
  label: string;
  isAuto: boolean;
  ecMap: Map<number, number | null>;
  roMap: Map<number, number | null>;
  phMap: Map<number, number | null>;
  fertRows: FertRow[];
  weekStart: number;
  weekEnd: number;
}

/** Which cell is being edited */
interface EditingCell {
  week: number;
  groupKey: 'auto' | 'manual';
  type: 'ec' | 'ro' | 'ph' | 'fert';
  fertKey?: string;
}

/** Find all entries covering a given week */
function findEntriesForWeek(sorted: NutrientPlanPhaseEntry[], week: number): NutrientPlanPhaseEntry[] {
  return sorted.filter((e) => week >= e.week_start && week <= e.week_end);
}

/** Find the entry+channel with the best match for editing a specific field at a given week */
function findBestEntryForEdit(
  sorted: NutrientPlanPhaseEntry[],
  week: number,
  isAuto: boolean,
  type: 'ec' | 'ro' | 'ph' | 'fert',
  fertKey?: string,
): { entry: NutrientPlanPhaseEntry; channelIdx: number } | undefined {
  const candidates = findEntriesForWeek(sorted, week);

  // RO is entry-level, not channel-level — return first matching entry with any matching channel
  if (type === 'ro') {
    for (const entry of candidates) {
      const ci = entry.delivery_channels.findIndex((ch) => AUTO_METHODS.has(ch.application_method) === isAuto);
      if (ci >= 0) return { entry, channelIdx: ci };
    }
    return undefined;
  }

  let best: { entry: NutrientPlanPhaseEntry; channelIdx: number; value: number } | undefined;

  for (const entry of candidates) {
    for (let ci = 0; ci < entry.delivery_channels.length; ci++) {
      const ch = entry.delivery_channels[ci];
      if (AUTO_METHODS.has(ch.application_method) !== isAuto) continue;

      if (type === 'ec' && ch.target_ec_ms != null) {
        if (!best || ch.target_ec_ms > best.value) {
          best = { entry, channelIdx: ci, value: ch.target_ec_ms };
        }
      } else if (type === 'ph' && ch.target_ph != null) {
        if (!best || ch.target_ph > best.value) {
          best = { entry, channelIdx: ci, value: ch.target_ph };
        }
      } else if (type === 'fert' && fertKey) {
        const d = ch.fertilizer_dosages.find((fd) => fd.fertilizer_key === fertKey);
        if (d && (!best || d.ml_per_liter > best.value)) {
          best = { entry, channelIdx: ci, value: d.ml_per_liter };
        }
      }
    }
  }

  // Fallback: first entry with a matching channel
  if (!best) {
    for (const entry of candidates) {
      const ci = entry.delivery_channels.findIndex((ch) => AUTO_METHODS.has(ch.application_method) === isAuto);
      if (ci >= 0) return { entry, channelIdx: ci };
    }
  }

  return best;
}

export default function PhaseDetailGantt({ entries, fertilizers, title, currentWeek, onEntriesChange }: Props) {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [editing, setEditing] = useState<EditingCell | null>(null);
  const [editValue, setEditValue] = useState('');
  const editable = !!onEntriesChange;

  const sorted = useMemo(
    () => [...entries].sort((a, b) => a.sequence_order - b.sequence_order),
    [entries],
  );

  const channelGroups = useMemo(() => {
    if (sorted.length === 0) return [];
    const fertLookup = new Map(fertilizers.map((f) => [f.key, f]));
    const groupMap = new Map<string, ChannelGroup>();

    for (const entry of sorted) {
      for (const ch of entry.delivery_channels) {
        const isAuto = AUTO_METHODS.has(ch.application_method);
        const groupKey = isAuto ? 'auto' : 'manual';

        let group = groupMap.get(groupKey);
        if (!group) {
          group = {
            groupKey: groupKey as 'auto' | 'manual',
            label: ch.label || t(`enums.applicationMethod.${ch.application_method}`),
            isAuto,
            ecMap: new Map(),
            roMap: new Map(),
            phMap: new Map(),
            fertRows: [],
            weekStart: entry.week_start,
            weekEnd: entry.week_end,
          };
          groupMap.set(groupKey, group);
        }

        if (ch.label && ch.label.length > group.label.length) {
          group.label = ch.label;
        }

        group.weekStart = Math.min(group.weekStart, entry.week_start);
        group.weekEnd = Math.max(group.weekEnd, entry.week_end);

        for (let w = entry.week_start; w <= entry.week_end; w++) {
          if (ch.target_ec_ms != null) {
            const prev = group.ecMap.get(w);
            if (prev == null || ch.target_ec_ms > prev) {
              group.ecMap.set(w, ch.target_ec_ms);
            }
          } else if (!group.ecMap.has(w)) {
            group.ecMap.set(w, null);
          }
          // RO% is entry-level — collect once per entry/week (not per channel)
          if (entry.water_mix_ratio_ro_percent != null) {
            group.roMap.set(w, entry.water_mix_ratio_ro_percent);
          } else if (!group.roMap.has(w)) {
            group.roMap.set(w, null);
          }
          if (ch.target_ph != null) {
            group.phMap.set(w, ch.target_ph);
          }
        }

        for (const d of ch.fertilizer_dosages) {
          let row = group.fertRows.find((r) => r.fertKey === d.fertilizer_key);
          if (!row) {
            const f = fertLookup.get(d.fertilizer_key);
            row = {
              fertKey: d.fertilizer_key,
              name: f?.product_name ?? d.fertilizer_key,
              brand: f?.brand ?? '',
              mixingOrder: d.mixing_order,
              weekMap: new Map(),
            };
            group.fertRows.push(row);
          }
          for (let w = entry.week_start; w <= entry.week_end; w++) {
            row.weekMap.set(w, d.ml_per_liter);
          }
        }
      }
    }

    for (const group of groupMap.values()) {
      group.fertRows.sort((a, b) => a.mixingOrder - b.mixingOrder);
    }

    return [...groupMap.values()].sort((a, b) => (a.isAuto === b.isAuto ? 0 : a.isAuto ? -1 : 1));
  }, [sorted, fertilizers, t]);

  const handleMove = useCallback(
    (groupKey: 'auto' | 'manual', fertKey: string, direction: 'up' | 'down') => {
      if (!onEntriesChange) return;

      const group = channelGroups.find((g) => g.groupKey === groupKey);
      if (!group) return;

      const idx = group.fertRows.findIndex((r) => r.fertKey === fertKey);
      if (idx < 0) return;
      const swapIdx = direction === 'up' ? idx - 1 : idx + 1;
      if (swapIdx < 0 || swapIdx >= group.fertRows.length) return;

      const reordered = [...group.fertRows];
      [reordered[idx], reordered[swapIdx]] = [reordered[swapIdx], reordered[idx]];
      const orderMap = new Map(reordered.map((r, i) => [r.fertKey, i]));

      const isAutoGroup = groupKey === 'auto';
      const updatedEntries = sorted.map((entry) => ({
        ...entry,
        delivery_channels: entry.delivery_channels.map((ch) => {
          const chIsAuto = AUTO_METHODS.has(ch.application_method);
          if (chIsAuto !== isAutoGroup) return ch;
          return {
            ...ch,
            fertilizer_dosages: ch.fertilizer_dosages.map((d) => {
              const newOrder = orderMap.get(d.fertilizer_key);
              if (newOrder != null) {
                return { ...d, mixing_order: newOrder };
              }
              return d;
            }),
          };
        }),
      }));

      onEntriesChange(updatedEntries);
    },
    [channelGroups, sorted, onEntriesChange],
  );

  /** Start editing a cell */
  const startEdit = useCallback(
    (cell: EditingCell) => {
      if (!editable) return;
      const match = findBestEntryForEdit(sorted, cell.week, cell.groupKey === 'auto', cell.type, cell.fertKey);
      if (!match) return;
      const ch = match.entry.delivery_channels[match.channelIdx];

      let value = '';
      if (cell.type === 'ec') {
        value = ch.target_ec_ms != null ? String(ch.target_ec_ms) : '';
      } else if (cell.type === 'ro') {
        value = match.entry.water_mix_ratio_ro_percent != null ? String(match.entry.water_mix_ratio_ro_percent) : '';
      } else if (cell.type === 'ph') {
        value = ch.target_ph != null ? String(ch.target_ph) : '';
      } else if (cell.type === 'fert' && cell.fertKey) {
        const d = ch.fertilizer_dosages.find((fd) => fd.fertilizer_key === cell.fertKey);
        value = d ? String(d.ml_per_liter) : '';
      }
      setEditValue(value);
      setEditing(cell);
    },
    [editable, sorted],
  );

  /** Commit the edit */
  const commitEdit = useCallback(() => {
    if (!editing || !onEntriesChange) {
      setEditing(null);
      return;
    }

    const isAuto = editing.groupKey === 'auto';
    const match = findBestEntryForEdit(sorted, editing.week, isAuto, editing.type, editing.fertKey);
    if (!match) {
      setEditing(null);
      return;
    }

    const parsed = editValue.trim() === '' ? null : parseFloat(editValue);
    if (parsed != null && isNaN(parsed)) {
      setEditing(null);
      return;
    }

    const targetEntryKey = match.entry.key;
    const targetChannelIdx = match.channelIdx;

    const updatedEntries = sorted.map((e) => {
      if (e.key !== targetEntryKey) return e;
      // RO is entry-level, not channel-level
      if (editing.type === 'ro') {
        return { ...e, water_mix_ratio_ro_percent: parsed };
      }
      return {
        ...e,
        delivery_channels: e.delivery_channels.map((ch, ci) => {
          if (ci !== targetChannelIdx) return ch;
          if (editing.type === 'ec') {
            return { ...ch, target_ec_ms: parsed };
          }
          if (editing.type === 'ph') {
            return { ...ch, target_ph: parsed };
          }
          if (editing.type === 'fert' && editing.fertKey) {
            return {
              ...ch,
              fertilizer_dosages: ch.fertilizer_dosages.map((d) =>
                d.fertilizer_key === editing.fertKey
                  ? { ...d, ml_per_liter: parsed ?? d.ml_per_liter }
                  : d,
              ),
            };
          }
          return ch;
        }),
      };
    });

    onEntriesChange(updatedEntries);
    setEditing(null);
  }, [editing, editValue, sorted, onEntriesChange]);

  /** Cancel editing */
  const cancelEdit = useCallback(() => setEditing(null), []);

  if (sorted.length === 0 || channelGroups.length === 0) return null;

  const globalStart = Math.min(...sorted.map((e) => e.week_start));
  const globalEnd = Math.max(...sorted.map((e) => e.week_end));
  const totalWeeks = globalEnd - globalStart + 1;
  const weeks = Array.from({ length: totalWeeks }, (_, i) => globalStart + i);
  const labelWidth = isMobile ? 110 : 150;

  const phaseColor = PHASE_COLORS[sorted[0].phase_name] ?? theme.palette.grey[600];

  const weekPhaseMap = useMemo(() => {
    const map = new Map<number, { phase: string; color: string }>();
    for (const entry of sorted) {
      const c = PHASE_COLORS[entry.phase_name] ?? theme.palette.grey[600];
      for (let w = entry.week_start; w <= entry.week_end; w++) {
        map.set(w, { phase: entry.phase_name, color: c });
      }
    }
    return map;
  }, [sorted, theme]);

  const isEditing = (w: number, groupKey: string, type: string, fertKey?: string) =>
    editing?.week === w && editing.groupKey === groupKey && editing.type === type && editing.fertKey === fertKey;

  return (
    <Card sx={{ borderLeft: `3px solid ${phaseColor}` }}>
      <CardContent sx={{ pb: '12px !important' }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1.5 }}>
          {title}
        </Typography>

        {channelGroups.map((group) => (
          <Box key={group.groupKey} sx={{ mb: 2 }}>
            {/* Channel group header */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <Chip
                label={group.isAuto
                  ? t('pages.gantt.automatic')
                  : t('pages.gantt.manual')}
                size="small"
                color={group.isAuto ? 'primary' : 'default'}
                variant="outlined"
              />
              <Typography variant="body2" color="text.secondary">
                {group.label}
              </Typography>
            </Box>

            {/* Gantt grid */}
            <Box sx={{ overflowX: 'auto' }}>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: `${labelWidth}px repeat(${totalWeeks}, 1fr)`,
                  minWidth: labelWidth + totalWeeks * 40,
                  gap: 0,
                }}
              >
                {/* Week header */}
                <Box sx={{ borderBottom: 1, borderColor: 'divider', py: 0.5 }} />
                {weeks.map((w) => {
                  const info = weekPhaseMap.get(w);
                  const phaseName = info ? t(`enums.phaseName.${info.phase}`) : '';
                  const phaseWeek = w - globalStart + 1;
                  return (
                    <Box
                      key={w}
                      role="columnheader"
                      sx={{
                        textAlign: 'center',
                        borderBottom: 1,
                        borderColor: 'divider',
                        py: 0.25,
                        ...(w === currentWeek && {
                          bgcolor: alpha(theme.palette.error.main, 0.12),
                          borderLeft: `2px solid ${alpha(theme.palette.error.main, 0.6)}`,
                          borderRight: `2px solid ${alpha(theme.palette.error.main, 0.6)}`,
                        }),
                      }}
                    >
                      <Typography
                        variant="caption"
                        color={w === currentWeek ? 'error' : 'text.primary'}
                        sx={{ fontWeight: 600, display: 'block', lineHeight: 1.2, whiteSpace: 'nowrap' }}
                      >
                        {phaseName} {t('pages.gantt.week')}{phaseWeek}
                      </Typography>
                      <Typography
                        variant="caption"
                        color="text.disabled"
                        sx={{ fontSize: '0.55rem', lineHeight: 1 }}
                      >
                        {(phaseWeek - 1) * 7}d
                      </Typography>
                    </Box>
                  );
                })}

                {/* Phase bar row */}
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
                    {t('pages.gantt.phase')}
                  </Typography>
                </Box>
                {weeks.map((w) => {
                  const info = weekPhaseMap.get(w);
                  return (
                    <Box
                      key={w}
                      sx={{
                        py: 0.5,
                        px: '2px',
                        borderBottom: 1,
                        borderColor: 'divider',
                        display: 'flex',
                        alignItems: 'center',
                      }}
                    >
                      {info && (
                        <Tooltip title={t(`enums.phaseName.${info.phase}`)} arrow>
                          <Box
                            sx={{
                              width: '100%',
                              height: 12,
                              bgcolor: alpha(info.color, 0.7),
                              borderRadius: 0.5,
                            }}
                          />
                        </Tooltip>
                      )}
                    </Box>
                  );
                })}

                {/* EC row */}
                {group.ecMap.size > 0 && (
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
                    {weeks.map((w) => {
                      const ec = group.ecMap.get(w);
                      const hasEc = group.ecMap.has(w) && ec != null && ec > 0;
                      const isHatched = group.ecMap.has(w) && (ec == null || ec === 0);
                      const cellEditing = isEditing(w, group.groupKey, 'ec');
                      return (
                        <Box
                          key={w}
                          sx={{
                            py: 0.5,
                            px: '2px',
                            borderBottom: 1,
                            borderColor: 'divider',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            ...(editable && !cellEditing && { cursor: 'pointer' }),
                          }}
                          onClick={() => {
                            if (!cellEditing && group.ecMap.has(w)) {
                              startEdit({ week: w, groupKey: group.groupKey, type: 'ec' });
                            }
                          }}
                        >
                          {cellEditing ? (
                            <InlineInput
                              value={editValue}
                              onChange={setEditValue}
                              onCommit={commitEdit}
                              onCancel={cancelEdit}
                              color={theme.palette.warning.main}
                            />
                          ) : (
                            <>
                              {isHatched && (
                                <Box
                                  sx={{
                                    width: '100%',
                                    height: 22,
                                    bgcolor: alpha(theme.palette.warning.main, 0.10),
                                    borderRadius: 0.5,
                                    backgroundImage: `repeating-linear-gradient(
                                      45deg, transparent, transparent 3px,
                                      ${alpha(theme.palette.warning.main, 0.15)} 3px,
                                      ${alpha(theme.palette.warning.main, 0.15)} 6px
                                    )`,
                                  }}
                                />
                              )}
                              {hasEc && (
                                <Box
                                  sx={{
                                    width: '100%',
                                    height: 22,
                                    bgcolor: alpha(theme.palette.warning.main, 0.15),
                                    borderRadius: 0.5,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                  }}
                                >
                                  <Typography
                                    variant="caption"
                                    sx={{ fontSize: '0.65rem', fontWeight: 600, lineHeight: 1 }}
                                    color="warning.dark"
                                  >
                                    {ec}
                                  </Typography>
                                </Box>
                              )}
                            </>
                          )}
                        </Box>
                      );
                    })}
                  </>
                )}

                {/* RO% row */}
                {group.roMap.size > 0 && (
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
                        {t('pages.gantt.roTarget')}
                      </Typography>
                    </Box>
                    {weeks.map((w) => {
                      const ro = group.roMap.get(w);
                      const hasRo = group.roMap.has(w) && ro != null && ro > 0;
                      const isHatched = group.roMap.has(w) && (ro == null || ro === 0);
                      const cellEditing = isEditing(w, group.groupKey, 'ro');
                      return (
                        <Box
                          key={w}
                          sx={{
                            py: 0.5,
                            px: '2px',
                            borderBottom: 1,
                            borderColor: 'divider',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            ...(editable && !cellEditing && { cursor: 'pointer' }),
                          }}
                          onClick={() => {
                            if (!cellEditing && group.roMap.has(w)) {
                              startEdit({ week: w, groupKey: group.groupKey, type: 'ro' });
                            }
                          }}
                        >
                          {cellEditing ? (
                            <InlineInput
                              value={editValue}
                              onChange={setEditValue}
                              onCommit={commitEdit}
                              onCancel={cancelEdit}
                              color={WATER_COLOR}
                            />
                          ) : (
                            <>
                              {isHatched && (
                                <Box
                                  sx={{
                                    width: '100%',
                                    height: 22,
                                    bgcolor: alpha(WATER_COLOR, 0.10),
                                    borderRadius: 0.5,
                                    backgroundImage: `repeating-linear-gradient(
                                      45deg, transparent, transparent 3px,
                                      ${alpha(WATER_COLOR, 0.15)} 3px,
                                      ${alpha(WATER_COLOR, 0.15)} 6px
                                    )`,
                                  }}
                                />
                              )}
                              {hasRo && (
                                <Box
                                  sx={{
                                    width: '100%',
                                    height: 22,
                                    bgcolor: alpha(WATER_COLOR, 0.15 + (ro / 100) * 0.35),
                                    borderRadius: 0.5,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                  }}
                                >
                                  <Typography
                                    variant="caption"
                                    sx={{ fontSize: '0.65rem', fontWeight: 600, lineHeight: 1 }}
                                    color="primary.dark"
                                  >
                                    {ro}%
                                  </Typography>
                                </Box>
                              )}
                            </>
                          )}
                        </Box>
                      );
                    })}
                  </>
                )}

                {/* pH row */}
                {group.phMap.size > 0 && (
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
                        pH
                      </Typography>
                    </Box>
                    {weeks.map((w) => {
                      const ph = group.phMap.get(w);
                      const cellEditing = isEditing(w, group.groupKey, 'ph');
                      return (
                        <Box
                          key={w}
                          sx={{
                            py: 0.5,
                            px: '2px',
                            borderBottom: 1,
                            borderColor: 'divider',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            ...(editable && !cellEditing && ph != null && { cursor: 'pointer' }),
                          }}
                          onClick={() => {
                            if (!cellEditing && ph != null) {
                              startEdit({ week: w, groupKey: group.groupKey, type: 'ph' });
                            }
                          }}
                        >
                          {cellEditing ? (
                            <InlineInput
                              value={editValue}
                              onChange={setEditValue}
                              onCommit={commitEdit}
                              onCancel={cancelEdit}
                              color={theme.palette.info.main}
                            />
                          ) : (
                            ph != null && (
                              <Box
                                sx={{
                                  width: '100%',
                                  height: 22,
                                  bgcolor: alpha(theme.palette.info.main, 0.12),
                                  borderRadius: 0.5,
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                }}
                              >
                                <Typography
                                  variant="caption"
                                  sx={{ fontSize: '0.65rem', fontWeight: 600, lineHeight: 1 }}
                                  color="info.main"
                                >
                                  {ph}
                                </Typography>
                              </Box>
                            )
                          )}
                        </Box>
                      );
                    })}
                  </>
                )}

                {/* Fertilizer dosage rows */}
                {group.fertRows.map((row, idx) => (
                  <FertilizerRow
                    key={row.fertKey}
                    row={row}
                    index={idx}
                    totalRows={group.fertRows.length}
                    weeks={weeks}
                    theme={theme}
                    phaseColor={phaseColor}
                    currentWeek={currentWeek}
                    canReorder={editable}
                    onMoveUp={() => handleMove(group.groupKey, row.fertKey, 'up')}
                    onMoveDown={() => handleMove(group.groupKey, row.fertKey, 'down')}
                    editing={editing}
                    editValue={editValue}
                    groupKey={group.groupKey}
                    onStartEdit={startEdit}
                    onEditValueChange={setEditValue}
                    onCommit={commitEdit}
                    onCancel={cancelEdit}
                    editable={editable}
                  />
                ))}

                {/* (current week highlighting is done per-cell via w === currentWeek) */}
              </Box>
            </Box>
          </Box>
        ))}
      </CardContent>
    </Card>
  );
}

// ── Inline input for cell editing ────────────────────────────────────

function InlineInput({
  value,
  onChange,
  onCommit,
  onCancel,
  color,
}: {
  value: string;
  onChange: (v: string) => void;
  onCommit: () => void;
  onCancel: () => void;
  color: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
    inputRef.current?.select();
  }, []);

  return (
    <input
      ref={inputRef}
      type="number"
      step="any"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onBlur={onCommit}
      onKeyDown={(e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          onCommit();
        }
        if (e.key === 'Escape') {
          e.preventDefault();
          onCancel();
        }
      }}
      style={{
        width: '100%',
        height: 22,
        border: `2px solid ${color}`,
        borderRadius: 4,
        textAlign: 'center',
        fontSize: '0.7rem',
        fontWeight: 600,
        outline: 'none',
        background: 'transparent',
        color: 'inherit',
        padding: 0,
        boxSizing: 'border-box',
        MozAppearance: 'textfield',
      }}
    />
  );
}

// ── Fertilizer row ───────────────────────────────────────────────────

function FertilizerRow({
  row,
  index,
  totalRows,
  weeks,
  theme,
  phaseColor,
  currentWeek,
  canReorder,
  onMoveUp,
  onMoveDown,
  editing,
  editValue,
  groupKey,
  onStartEdit,
  onEditValueChange,
  onCommit,
  onCancel,
  editable,
}: {
  row: FertRow;
  index: number;
  totalRows: number;
  weeks: number[];
  theme: Theme;
  phaseColor: string;
  currentWeek?: number;
  canReorder: boolean;
  onMoveUp: () => void;
  onMoveDown: () => void;
  editing: EditingCell | null;
  editValue: string;
  groupKey: 'auto' | 'manual';
  onStartEdit: (cell: EditingCell) => void;
  onEditValueChange: (v: string) => void;
  onCommit: () => void;
  onCancel: () => void;
  editable: boolean;
}) {
  const cellEditing = (w: number) =>
    editing?.week === w && editing.groupKey === groupKey && editing.type === 'fert' && editing.fertKey === row.fertKey;

  return (
    <>
      <Box
        sx={{
          position: 'sticky',
          left: 0,
          bgcolor: 'background.paper',
          zIndex: 1,
          display: 'flex',
          alignItems: 'center',
          py: 0.25,
          px: 0.5,
          borderBottom: 1,
          borderColor: 'divider',
          minWidth: 0,
          gap: 0.25,
        }}
      >
        {canReorder && (
          <Box sx={{ display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
            <IconButton
              size="small"
              onClick={onMoveUp}
              disabled={index === 0}
              sx={{ p: 0, opacity: index === 0 ? 0.2 : 0.6, '&:hover': { opacity: 1 } }}
            >
              <ArrowUpwardIcon sx={{ fontSize: 12 }} />
            </IconButton>
            <IconButton
              size="small"
              onClick={onMoveDown}
              disabled={index === totalRows - 1}
              sx={{ p: 0, opacity: index === totalRows - 1 ? 0.2 : 0.6, '&:hover': { opacity: 1 } }}
            >
              <ArrowDownwardIcon sx={{ fontSize: 12 }} />
            </IconButton>
          </Box>
        )}
        <Box sx={{ minWidth: 0 }}>
          <Typography variant="caption" noWrap sx={{ fontWeight: 600, display: 'block' }} color="text.secondary">
            {row.name}
          </Typography>
          {row.brand && (
            <Typography variant="caption" noWrap sx={{ fontSize: '0.6rem', display: 'block', lineHeight: 1.2 }} color="text.disabled">
              {row.brand}
            </Typography>
          )}
        </Box>
      </Box>
      {weeks.map((w) => {
        const ml = row.weekMap.get(w);
        const isEdit = cellEditing(w);
        return (
          <Box
            key={w}
            sx={{
              py: 0.5,
              px: '2px',
              borderBottom: 1,
              borderColor: 'divider',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              ...(w === currentWeek && {
                bgcolor: alpha(theme.palette.error.main, 0.08),
                borderLeft: `2px solid ${alpha(theme.palette.error.main, 0.4)}`,
                borderRight: `2px solid ${alpha(theme.palette.error.main, 0.4)}`,
              }),
              ...(editable && !isEdit && ml != null && { cursor: 'pointer' }),
            }}
            onClick={() => {
              if (!isEdit && ml != null) {
                onStartEdit({ week: w, groupKey, type: 'fert', fertKey: row.fertKey });
              }
            }}
          >
            {isEdit ? (
              <InlineInput
                value={editValue}
                onChange={onEditValueChange}
                onCommit={onCommit}
                onCancel={onCancel}
                color={phaseColor}
              />
            ) : (
              ml != null && (
                <Tooltip title={`${row.name}: ${ml} ml/L`} arrow>
                  <Box
                    sx={{
                      width: '100%',
                      height: 22,
                      bgcolor: alpha(phaseColor, 0.12),
                      borderRadius: 0.5,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Typography
                      variant="caption"
                      sx={{ fontSize: '0.65rem', fontWeight: 600, lineHeight: 1, whiteSpace: 'nowrap' }}
                      color="text.primary"
                    >
                      {ml}
                    </Typography>
                  </Box>
                </Tooltip>
              )
            )}
          </Box>
        );
      })}
    </>
  );
}
