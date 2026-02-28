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
import { alpha, useTheme } from '@mui/material/styles';
import type { ChannelCalendarEntry } from '@/api/types';

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

// ── Types ────────────────────────────────────────────────────────────

interface WateringDateEntry {
  dateStr: string;
  channelId?: string;
  label: string;
  color: string;
  occurrence: number;
  timesPerDay: number;
}

interface WateringCalendarViewProps {
  dates: string[];
  channelCalendars: ChannelCalendarEntry[];
  quickConfirming: string | null;
  onQuickConfirm: (dateStr: string, channelId?: string, stateKey?: string) => void;
  onConfirm: (dateStr: string, channelId?: string) => void;
}

export default function WateringCalendarView({
  dates,
  channelCalendars,
  quickConfirming,
  onQuickConfirm,
  onConfirm,
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
    const entries: WateringDateEntry[] = [];
    if (channelCalendars.length > 0) {
      channelCalendars.forEach((ch, idx) => {
        const color = CHANNEL_COLORS[idx % CHANNEL_COLORS.length];
        const tpd = ch.times_per_day ?? 1;
        for (const dateStr of ch.dates) {
          for (let occ = 1; occ <= tpd; occ++) {
            entries.push({ dateStr, channelId: ch.channel_id, label: ch.label, color, occurrence: occ, timesPerDay: tpd });
          }
        }
      });
    } else {
      for (const dateStr of dates) {
        entries.push({ dateStr, label: t('pages.wateringSchedule.title'), color: theme.palette.primary.main, occurrence: 1, timesPerDay: 1 });
      }
    }
    return entries;
  }, [dates, channelCalendars, t, theme.palette.primary.main]);

  // Group entries by day number for the current month
  const entriesByDay = useMemo(() => {
    const map = new Map<number, WateringDateEntry[]>();
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
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
          {channelLegend.map((ch) => (
            <Chip
              key={ch.label}
              label={ch.label}
              size="small"
              sx={{
                bgcolor: alpha(ch.color, 0.15),
                borderLeft: `3px solid ${ch.color}`,
                fontWeight: 500,
              }}
            />
          ))}
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
                minHeight: { xs: '2.5rem', sm: '3.5rem' },
                border: 1,
                borderColor: 'divider',
                p: 0.5,
                cursor: hasEntries ? 'pointer' : 'default',
                bgcolor: isValidDay
                  ? isToday
                    ? 'action.selected'
                    : 'background.paper'
                  : 'action.disabledBackground',
                '&:hover': hasEntries ? { bgcolor: 'action.hover' } : {},
                position: 'relative',
              }}
            >
              {isValidDay && (
                <>
                  <Typography
                    variant="body2"
                    sx={{
                      fontWeight: isToday ? 'bold' : 'normal',
                      color: isToday ? 'primary.main' : 'text.primary',
                      fontSize: { xs: '0.75rem', sm: '0.875rem' },
                    }}
                  >
                    {dayNum}
                  </Typography>
                  {hasEntries && (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: '2px', mt: 0.25 }}>
                      {dayEntries.map((entry, idx) => (
                        <Tooltip key={`${entry.channelId ?? 'plan'}-${idx}`} title={entry.label} arrow>
                          <Box
                            component="span"
                            sx={{
                              width: { xs: '0.5rem', sm: '0.625rem' },
                              height: { xs: '0.5rem', sm: '0.625rem' },
                              borderRadius: '50%',
                              bgcolor: entry.color,
                              display: 'inline-block',
                              flexShrink: 0,
                            }}
                          />
                        </Tooltip>
                      ))}
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
          <Box sx={{ p: 2, minWidth: 260, maxWidth: 360 }}>
            <Typography variant="subtitle2" gutterBottom>
              {new Date(currentYear, currentMonth, popoverDay).toLocaleDateString(
                i18n.language === 'de' ? 'de-DE' : 'en-US',
                { weekday: 'long', day: 'numeric', month: 'long' },
              )}
            </Typography>
            {popoverEntries.map((entry, idx) => {
              const dateStr = formatDateISO(currentYear, currentMonth, popoverDay);
              const stateKey = entry.channelId
                ? `${entry.channelId}-${dateStr}-${entry.occurrence}`
                : `${dateStr}-${entry.occurrence}`;
              const displayLabel = entry.timesPerDay > 1
                ? t('pages.wateringSchedule.timesPerDayOccurrence', { label: entry.label, current: entry.occurrence, total: entry.timesPerDay })
                : entry.label;
              return (
                <Box
                  key={`${entry.channelId ?? 'plan'}-${idx}`}
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
                        borderRadius: '50%',
                        bgcolor: entry.color,
                        flexShrink: 0,
                      }}
                    />
                    <Typography variant="body2" noWrap>
                      {displayLabel}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 0.5, flexShrink: 0 }}>
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
                  </Box>
                </Box>
              );
            })}
          </Box>
        )}
      </Popover>
    </Box>
  );
}
