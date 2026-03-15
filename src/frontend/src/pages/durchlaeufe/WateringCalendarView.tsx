import { useMemo, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import Popover from '@mui/material/Popover';
import CircularProgress from '@mui/material/CircularProgress';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import TodayIcon from '@mui/icons-material/Today';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import OpacityIcon from '@mui/icons-material/Opacity';
import LocalDrinkIcon from '@mui/icons-material/LocalDrink';
import { alpha, useTheme } from '@mui/material/styles';
import type { ChannelCalendarEntry, PhaseTimelineEntry } from '@/api/types';

// ── Helpers ──────────────────────────────────────────────────────────

function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfWeek(year: number, month: number): number {
  const day = new Date(year, month, 1).getDay();
  return day === 0 ? 6 : day - 1; // Monday=0
}

function formatDateISO(year: number, month: number, day: number): string {
  const m = String(month + 1).padStart(2, '0');
  const d = String(day).padStart(2, '0');
  return `${year}-${m}-${d}`;
}

// ── Phase colors ────────────────────────────────────────────────────

const PHASE_COLORS: Record<string, string> = {
  germination: '#a5d6a7',
  seedling: '#81c784',
  vegetative: '#4caf50',
  flowering: '#f48fb1',
  ripening: '#ffcc80',
  harvest: '#ffb74d',
  drying: '#bcaaa4',
  curing: '#a1887f',
  flushing: '#90caf9',
  juvenile: '#c5e1a5',
  climbing: '#aed581',
  mature: '#66bb6a',
  dormancy: '#b0bec5',
  senescence: '#ef9a9a',
};

// ── Channel color palette ────────────────────────────────────────────

const CHANNEL_COLORS = [
  '#1976d2', // blue
  '#2e7d32', // green
  '#ed6c02', // orange
  '#9c27b0', // purple
  '#d32f2f', // red
  '#0288d1', // light blue
  '#689f38', // lime
  '#f57c00', // deep orange
];

// ── Application method icons ─────────────────────────────────────────

const METHOD_ICONS: Record<string, typeof OpacityIcon> = {
  tank_drip: LocalDrinkIcon,
  watering_can: OpacityIcon,
  foliar_spray: OpacityIcon,
  drip: LocalDrinkIcon,
};

// Manual methods: collapse times_per_day into a single entry
const MANUAL_METHODS = new Set(['watering_can', 'foliar_spray', 'drench', 'foliar', 'top_dress']);

// ── Types ────────────────────────────────────────────────────────────

interface CalendarDayEntry {
  dateStr: string;
  channelId?: string;
  label: string;
  color: string;
  occurrence: number;
  timesPerDay: number;
  method?: string;
  type: 'watering' | 'tank_fill';
}

interface WateringCalendarViewProps {
  dates: string[];
  channelCalendars: ChannelCalendarEntry[];
  quickConfirming: string | null;
  onQuickConfirm: (dateStr: string, channelId?: string, stateKey?: string) => void;
  onConfirm: (dateStr: string, channelId?: string) => void;
  phases?: PhaseTimelineEntry[];
}

export default function WateringCalendarView({
  dates,
  channelCalendars,
  quickConfirming,
  onQuickConfirm,
  onConfirm,
  phases,
}: WateringCalendarViewProps) {
  const { t, i18n } = useTranslation();
  const theme = useTheme();
  const todayDate = useMemo(() => new Date(), []);
  const [currentYear, setCurrentYear] = useState(todayDate.getFullYear());
  const [currentMonth, setCurrentMonth] = useState(todayDate.getMonth());
  const [popoverAnchor, setPopoverAnchor] = useState<HTMLElement | null>(null);
  const [popoverDay, setPopoverDay] = useState<number | null>(null);

  // Build flat list of watering entries with color assignments
  const allEntries = useMemo(() => {
    const entries: CalendarDayEntry[] = [];
    if (channelCalendars.length > 0) {
      channelCalendars.forEach((ch, idx) => {
        const color = CHANNEL_COLORS[idx % CHANNEL_COLORS.length];
        const tpd = ch.times_per_day ?? 1;
        const isTank = ch.application_method === 'tank_drip' || ch.application_method === 'drip';
        const isManual = MANUAL_METHODS.has(ch.application_method);
        for (const dateStr of ch.dates) {
          // Tank fill entry (once per date for tank channels)
          if (isTank) {
            entries.push({
              dateStr,
              channelId: ch.channel_id,
              label: `${t('pages.wateringSchedule.tankFill')}: ${ch.label}`,
              color: '#5d4037',
              occurrence: 1,
              timesPerDay: 1,
              method: ch.application_method,
              type: 'tank_fill',
            });
          }
          if (isManual) {
            // Manual methods: single entry per day, times_per_day is irrelevant
            entries.push({
              dateStr,
              channelId: ch.channel_id,
              label: ch.label,
              color,
              occurrence: 1,
              timesPerDay: 1,
              method: ch.application_method,
              type: 'watering',
            });
          } else {
            // Automatic methods: one entry per occurrence
            for (let occ = 1; occ <= tpd; occ++) {
              entries.push({
                dateStr,
                channelId: ch.channel_id,
                label: ch.label,
                color,
                occurrence: occ,
                timesPerDay: tpd,
                method: ch.application_method,
                type: 'watering',
              });
            }
          }
        }
      });
    } else {
      for (const dateStr of dates) {
        entries.push({
          dateStr,
          label: t('pages.wateringSchedule.title'),
          color: theme.palette.primary.main,
          occurrence: 1,
          timesPerDay: 1,
          type: 'watering',
        });
      }
    }
    return entries;
  }, [dates, channelCalendars, t, theme.palette.primary.main]);

  // Determine active phase for each day of the current month
  const phaseByDay = useMemo(() => {
    const map = new Map<number, { name: string; displayName: string; color: string }>();
    if (!phases || phases.length === 0) return map;

    const daysInM = getDaysInMonth(currentYear, currentMonth);
    for (let day = 1; day <= daysInM; day++) {
      const dayTs = new Date(currentYear, currentMonth, day).getTime();
      for (const p of phases) {
        const startStr = p.actual_entered_at ?? p.projected_start;
        const endStr = p.actual_exited_at ?? p.projected_end;
        if (!startStr) continue;
        const startTs = new Date(startStr).getTime();
        const endTs = endStr ? new Date(endStr).getTime() : Date.now() + 365 * 86400000;
        if (dayTs >= startTs && dayTs <= endTs) {
          map.set(day, {
            name: p.phase_name,
            displayName: p.display_name || p.phase_name,
            color: PHASE_COLORS[p.phase_name.toLowerCase()] ?? '#e0e0e0',
          });
          break;
        }
      }
    }
    return map;
  }, [phases, currentYear, currentMonth]);

  // Group entries by day number for the current month
  const entriesByDay = useMemo(() => {
    const map = new Map<number, CalendarDayEntry[]>();
    for (const entry of allEntries) {
      const d = new Date(entry.dateStr);
      if (d.getFullYear() === currentYear && d.getMonth() === currentMonth) {
        const day = d.getDate();
        const existing = map.get(day) ?? [];
        existing.push(entry);
        map.set(day, existing);
      }
    }
    return map;
  }, [allEntries, currentYear, currentMonth]);

  // Weekday headers (locale-aware, Monday first)
  const weekdayHeaders = useMemo(() => {
    const baseDate = new Date(2024, 0, 1); // Monday
    const headers: string[] = [];
    for (let i = 0; i < 7; i++) {
      const d = new Date(baseDate);
      d.setDate(d.getDate() + i);
      headers.push(
        d.toLocaleDateString(i18n.language === 'de' ? 'de-DE' : 'en-US', { weekday: 'short' }),
      );
    }
    return headers;
  }, [i18n.language]);

  const formatMonthYear = useMemo(() => {
    const d = new Date(currentYear, currentMonth, 1);
    return d.toLocaleDateString(i18n.language === 'de' ? 'de-DE' : 'en-US', {
      month: 'long',
      year: 'numeric',
    });
  }, [currentYear, currentMonth, i18n.language]);

  const goToday = useCallback(() => {
    setCurrentYear(todayDate.getFullYear());
    setCurrentMonth(todayDate.getMonth());
  }, [todayDate]);

  const goPrev = useCallback(() => {
    setCurrentMonth((m) => {
      if (m === 0) {
        setCurrentYear((y) => y - 1);
        return 11;
      }
      return m - 1;
    });
  }, []);

  const goNext = useCallback(() => {
    setCurrentMonth((m) => {
      if (m === 11) {
        setCurrentYear((y) => y + 1);
        return 0;
      }
      return m + 1;
    });
  }, []);

  const handleDayClick = useCallback(
    (e: React.MouseEvent<HTMLElement>, day: number) => {
      const dayEntries = entriesByDay.get(day);
      if (dayEntries && dayEntries.length > 0) {
        setPopoverAnchor(e.currentTarget);
        setPopoverDay(day);
      }
    },
    [entriesByDay],
  );

  const handleClosePopover = useCallback(() => {
    setPopoverAnchor(null);
    setPopoverDay(null);
  }, []);

  // Month grid
  const daysInMonth = getDaysInMonth(currentYear, currentMonth);
  const firstDayOfWeek = getFirstDayOfWeek(currentYear, currentMonth);
  const totalCells = Math.ceil((firstDayOfWeek + daysInMonth) / 7) * 7;
  const isTodayCell = (day: number) =>
    todayDate.getFullYear() === currentYear &&
    todayDate.getMonth() === currentMonth &&
    todayDate.getDate() === day;

  const popoverEntries = popoverDay != null ? entriesByDay.get(popoverDay) ?? [] : [];

  // Channel legend
  const channelLegend = useMemo(() => {
    if (channelCalendars.length === 0) return [];
    return channelCalendars.map((ch, idx) => ({
      label: ch.label,
      method: ch.application_method,
      phase: ch.phase_name,
      color: CHANNEL_COLORS[idx % CHANNEL_COLORS.length],
    }));
  }, [channelCalendars]);

  return (
    <Box data-testid="watering-calendar-view">
      {/* Header: nav + month/year */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <IconButton size="small" onClick={goPrev} aria-label={t('common.back')}>
            <ChevronLeftIcon />
          </IconButton>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, minWidth: 160, textAlign: 'center' }}>
            {formatMonthYear}
          </Typography>
          <IconButton size="small" onClick={goNext} aria-label={t('common.next')}>
            <ChevronRightIcon />
          </IconButton>
        </Box>
        <Tooltip title={t('pages.calendar.today')} arrow>
          <IconButton size="small" onClick={goToday}>
            <TodayIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Channel legend */}
      {channelLegend.length > 0 && (
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', alignItems: 'center', mb: 1.5 }}>
          <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5 }}>
            {t('pages.wateringSchedule.channel')}:
          </Typography>
          {channelLegend.map((ch) => {
            const MethodIcon = METHOD_ICONS[ch.method] ?? OpacityIcon;
            return (
              <Chip
                key={ch.label}
                icon={<MethodIcon sx={{ fontSize: 14 }} />}
                label={`${ch.label} (${t(`enums.applicationMethod.${ch.method}`)})`}
                size="small"
                sx={{
                  bgcolor: alpha(ch.color, 0.15),
                  borderLeft: `3px solid ${ch.color}`,
                  fontWeight: 500,
                  fontSize: '0.7rem',
                }}
              />
            );
          })}
          <Chip
            icon={<LocalDrinkIcon sx={{ fontSize: 14 }} />}
            label={t('pages.wateringSchedule.tankFill')}
            size="small"
            sx={{
              bgcolor: alpha('#5d4037', 0.15),
              borderLeft: '3px solid #5d4037',
              fontWeight: 500,
              fontSize: '0.7rem',
            }}
          />
        </Box>
      )}

      {/* Weekday header row */}
      <Box sx={{ display: 'flex', bgcolor: 'action.hover', borderRadius: '4px 4px 0 0' }} role="row">
        {weekdayHeaders.map((wh) => (
          <Box
            key={wh}
            role="columnheader"
            sx={{ flex: '1 0 calc(100% / 7)', textAlign: 'center', py: 0.5 }}
          >
            <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'text.secondary' }}>
              {wh}
            </Typography>
          </Box>
        ))}
      </Box>

      {/* Day grid */}
      {(() => {
        const rows: React.ReactNode[] = [];
        let cells: React.ReactNode[] = [];

        for (let i = 0; i < totalCells; i++) {
          const dayNum = i - firstDayOfWeek + 1;
          const isValidDay = dayNum >= 1 && dayNum <= daysInMonth;
          const dayEntries = isValidDay ? entriesByDay.get(dayNum) ?? [] : [];
          const hasEntries = dayEntries.length > 0;
          const isToday = isValidDay && isTodayCell(dayNum);
          const phase = isValidDay ? phaseByDay.get(dayNum) : undefined;
          const isFuture = isValidDay && new Date(currentYear, currentMonth, dayNum) > todayDate;

          cells.push(
            <Box
              key={i}
              onClick={isValidDay && hasEntries ? (e) => handleDayClick(e, dayNum) : undefined}
              role={isValidDay && hasEntries ? 'button' : undefined}
              tabIndex={isValidDay && hasEntries ? 0 : undefined}
              onKeyDown={
                isValidDay && hasEntries
                  ? (e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        handleDayClick(e as unknown as React.MouseEvent<HTMLElement>, dayNum);
                      }
                    }
                  : undefined
              }
              sx={{
                flex: '1 0 calc(100% / 7)',
                minHeight: { xs: '3rem', sm: '4rem' },
                border: 1,
                borderColor: 'divider',
                p: 0.5,
                cursor: hasEntries ? 'pointer' : 'default',
                bgcolor: !isValidDay
                  ? 'action.disabledBackground'
                  : isToday
                    ? 'action.selected'
                    : phase
                      ? alpha(phase.color, 0.1)
                      : 'background.paper',
                '&:hover': hasEntries ? { bgcolor: phase ? alpha(phase.color, 0.2) : 'action.hover' } : {},
                position: 'relative',
                // Phase left-border indicator
                ...(phase
                  ? { borderLeft: `3px solid ${phase.color}` }
                  : {}),
                // Dim future days slightly
                ...(isFuture && !hasEntries ? { opacity: 0.7 } : {}),
              }}
            >
              {isValidDay && (
                <>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <Typography
                      variant="body2"
                      sx={{
                        fontWeight: isToday ? 'bold' : 'normal',
                        color: isToday ? 'primary.main' : 'text.primary',
                        fontSize: { xs: '0.7rem', sm: '0.8rem' },
                      }}
                    >
                      {dayNum}
                    </Typography>
                    {/* Phase abbreviation on small screens */}
                    {phase && (
                      <Typography
                        variant="caption"
                        sx={{
                          color: phase.color,
                          fontSize: '0.55rem',
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          lineHeight: 1,
                          display: { xs: 'none', sm: 'block' },
                        }}
                      >
                        {phase.displayName.slice(0, 3)}
                      </Typography>
                    )}
                  </Box>
                  {hasEntries && (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: '2px', mt: 0.25 }}>
                      {dayEntries.map((entry, idx) => {
                        const isTankFill = entry.type === 'tank_fill';
                        return (
                          <Tooltip key={`${entry.channelId ?? 'plan'}-${entry.type}-${idx}`} title={entry.label} arrow>
                            <Box
                              component="span"
                              sx={{
                                width: { xs: '0.5rem', sm: '0.625rem' },
                                height: { xs: '0.5rem', sm: '0.625rem' },
                                borderRadius: isTankFill ? '2px' : '50%',
                                bgcolor: entry.color,
                                display: 'inline-block',
                                flexShrink: 0,
                              }}
                            />
                          </Tooltip>
                        );
                      })}
                    </Box>
                  )}
                </>
              )}
            </Box>,
          );

          if ((i + 1) % 7 === 0) {
            rows.push(
              <Box key={`row-${i}`} sx={{ display: 'flex' }}>
                {cells}
              </Box>,
            );
            cells = [];
          }
        }

        return rows;
      })()}

      {/* Day popover with confirm actions */}
      <Popover
        open={Boolean(popoverAnchor) && popoverDay != null}
        anchorEl={popoverAnchor}
        onClose={handleClosePopover}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
      >
        {popoverDay != null && (
          <Box sx={{ p: 2, minWidth: 280, maxWidth: 400 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="subtitle2">
                {new Date(currentYear, currentMonth, popoverDay).toLocaleDateString(
                  i18n.language === 'de' ? 'de-DE' : 'en-US',
                  { weekday: 'long', day: 'numeric', month: 'long' },
                )}
              </Typography>
              {phaseByDay.get(popoverDay) && (
                <Chip
                  label={phaseByDay.get(popoverDay)!.displayName}
                  size="small"
                  sx={{
                    bgcolor: alpha(phaseByDay.get(popoverDay)!.color, 0.25),
                    fontSize: '0.7rem',
                  }}
                />
              )}
            </Box>
            {popoverEntries.map((entry, idx) => {
              const dateStr = formatDateISO(currentYear, currentMonth, popoverDay);
              const isFutureDate = new Date(dateStr) > todayDate;
              const stateKey = entry.channelId
                ? `${entry.channelId}-${dateStr}-${entry.occurrence}`
                : `${dateStr}-${entry.occurrence}`;
              const isTankFill = entry.type === 'tank_fill';
              const displayLabel = entry.timesPerDay > 1 && !isTankFill
                ? t('pages.wateringSchedule.timesPerDayOccurrence', { label: entry.label, current: entry.occurrence, total: entry.timesPerDay })
                : entry.label;
              const MethodIcon = METHOD_ICONS[entry.method ?? ''] ?? OpacityIcon;
              return (
                <Box
                  key={`${entry.channelId ?? 'plan'}-${entry.type}-${idx}`}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 1,
                    py: 0.75,
                    borderBottom: idx < popoverEntries.length - 1 ? 1 : 0,
                    borderColor: 'divider',
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0 }}>
                    <Box
                      sx={{
                        width: 10,
                        height: 10,
                        borderRadius: isTankFill ? '2px' : '50%',
                        bgcolor: entry.color,
                        flexShrink: 0,
                      }}
                    />
                    <MethodIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                    <Typography variant="body2" noWrap>
                      {displayLabel}
                    </Typography>
                  </Box>
                  {!isTankFill && (
                    <Box sx={{ display: 'flex', gap: 0.5, flexShrink: 0 }}>
                      {isFutureDate ? (
                        <Chip label={t('pages.wateringSchedule.projected')} size="small" variant="outlined" />
                      ) : (
                        <>
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={<CheckCircleIcon />}
                            disabled={quickConfirming === stateKey}
                            onClick={() => {
                              onQuickConfirm(dateStr, entry.channelId, stateKey);
                              handleClosePopover();
                            }}
                          >
                            {quickConfirming === stateKey ? <CircularProgress size={14} /> : t('pages.wateringSchedule.quickConfirm')}
                          </Button>
                          <Button
                            size="small"
                            variant="contained"
                            onClick={() => {
                              onConfirm(dateStr, entry.channelId);
                              handleClosePopover();
                            }}
                          >
                            {t('pages.wateringSchedule.confirm')}
                          </Button>
                        </>
                      )}
                    </Box>
                  )}
                </Box>
              );
            })}
          </Box>
        )}
      </Popover>
    </Box>
  );
}
