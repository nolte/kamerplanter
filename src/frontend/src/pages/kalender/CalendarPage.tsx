import { useEffect, useState, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Popover from '@mui/material/Popover';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Collapse from '@mui/material/Collapse';
import TextField from '@mui/material/TextField';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemSecondaryAction from '@mui/material/ListItemSecondaryAction';
import Tooltip from '@mui/material/Tooltip';
import Divider from '@mui/material/Divider';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import InputLabel from '@mui/material/InputLabel';
import FormControl from '@mui/material/FormControl';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import TodayIcon from '@mui/icons-material/Today';
import CalendarViewMonthIcon from '@mui/icons-material/CalendarViewMonth';
import ViewListIcon from '@mui/icons-material/ViewList';
import GrassIcon from '@mui/icons-material/Grass';
import BarChartIcon from '@mui/icons-material/BarChart';
import RssFeedIcon from '@mui/icons-material/RssFeed';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import RefreshIcon from '@mui/icons-material/Refresh';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import AddIcon from '@mui/icons-material/Add';
import StarIcon from '@mui/icons-material/Star';
import TimelineIcon from '@mui/icons-material/Timeline';
import SowingCalendarView from './SowingCalendarView';
import SeasonOverviewView from './SeasonOverviewView';
import PhaseTimelineView from './PhaseTimelineView';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import EmptyState from '@/components/common/EmptyState';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  fetchCalendarEvents,
  fetchCalendarFeeds,
  createCalendarFeed,
  deleteCalendarFeed,
  regenerateCalendarFeedToken,
  fetchSowingCalendar,
  fetchSeasonOverview,
} from '@/store/slices/calendarSlice';
import { fetchSites } from '@/store/slices/sitesSlice';
import { useNotification } from '@/hooks/useNotification';
import { useSowingFavorites } from '@/hooks/useSowingFavorites';
import { confirmReminder } from '@/api/endpoints/careReminders';
import type { CalendarEvent, CalendarEventCategory, CalendarFeed } from '@/api/types';
import { kamiCalendar } from '@/assets/brand/illustrations';
import PlantFilterTree from './PlantFilterTree';

// ── Constants ────────────────────────────────────────────────────────

const ALL_CATEGORIES: CalendarEventCategory[] = [
  'training',
  'pruning',
  'transplanting',
  'feeding',
  'ipm',
  'harvest',
  'maintenance',
  'phase_transition',
  'tank_maintenance',
  'watering_forecast',
  'custom',
];

const CATEGORY_COLORS: Record<CalendarEventCategory, string> = {
  training: '#4CAF50',
  pruning: '#8BC34A',
  transplanting: '#795548',
  feeding: '#2196F3',
  ipm: '#FF9800',
  harvest: '#F44336',
  maintenance: '#9E9E9E',
  phase_transition: '#9C27B0',
  tank_maintenance: '#00BCD4',
  watering_forecast: '#42A5F5',
  custom: '#607D8B',
};

const CATEGORY_I18N_KEYS: Record<CalendarEventCategory, string> = {
  training: 'pages.calendar.training',
  pruning: 'pages.calendar.pruning',
  transplanting: 'pages.calendar.transplanting',
  feeding: 'pages.calendar.feeding',
  ipm: 'pages.calendar.ipm',
  harvest: 'pages.calendar.harvest',
  maintenance: 'pages.calendar.maintenance',
  phase_transition: 'pages.calendar.phaseTransition',
  tank_maintenance: 'pages.calendar.tankMaintenance',
  watering_forecast: 'pages.calendar.wateringForecast',
  custom: 'pages.calendar.custom',
};

type ViewMode = 'month' | 'list' | 'phases' | 'sowing' | 'season';

// ── Helpers ──────────────────────────────────────────────────────────

function getMonthStart(year: number, month: number): Date {
  return new Date(year, month, 1);
}

function getMonthEnd(year: number, month: number): Date {
  return new Date(year, month + 1, 0);
}

function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfWeek(year: number, month: number): number {
  const day = new Date(year, month, 1).getDay();
  // Convert from Sunday=0 to Monday=0
  return day === 0 ? 6 : day - 1;
}

function formatDateISO(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function isSameDay(dateStr: string | null, year: number, month: number, day: number): boolean {
  if (!dateStr) return false;
  const d = new Date(dateStr);
  return d.getFullYear() === year && d.getMonth() === month && d.getDate() === day;
}

// ── Component ────────────────────────────────────────────────────────

function getEventLink(event: CalendarEvent): string | null {
  if (event.source === 'phase_transition') {
    const meta = event.metadata as Record<string, string>;
    if (meta?.plant_instance_key) {
      return `/pflanzen/plant-instances/${meta.plant_instance_key}`;
    }
  }
  if (event.task_key) {
    return `/aufgaben/tasks/${event.task_key}`;
  }
  return null;
}

function getRunLink(runKey: string): string {
  return `/durchlaeufe/planting-runs/${runKey}`;
}

export default function CalendarPage() {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const notification = useNotification();
  const { events, feeds, loading, feedsLoading, sowingEntries, sowingFrostConfig, sowingYear, sowingLoading, seasonOverview, seasonLoading } = useAppSelector((state) => state.calendar);
  const { sites } = useAppSelector((state) => state.sites);

  const today = new Date();
  const [currentYear, setCurrentYear] = useState(today.getFullYear());
  const [currentMonth, setCurrentMonth] = useState(today.getMonth());
  const [viewMode, setViewMode] = useState<ViewMode>('month');
  const [selectedSiteKey, setSelectedSiteKey] = useState<string>('');
  const [selectedCategories, setSelectedCategories] = useState<Set<CalendarEventCategory>>(
    new Set(ALL_CATEGORIES),
  );
  const [feedsSectionOpen, setFeedsSectionOpen] = useState(false);
  const [createFeedDialogOpen, setCreateFeedDialogOpen] = useState(false);
  const [newFeedName, setNewFeedName] = useState('');
  const [deleteFeedKey, setDeleteFeedKey] = useState<string | null>(null);
  const [deleteFeedName, setDeleteFeedName] = useState('');
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);

  // Plant tree filter state
  const [checkedPlantKeys, setCheckedPlantKeys] = useState<Set<string> | null>(null); // null = all checked (initial)
  const [expandedRuns, setExpandedRuns] = useState<Set<string>>(new Set());

  // Sowing calendar favorites (shared hook)
  const { favorites: sowingFavorites, toggleFavorite: handleToggleSowingFavorite } = useSowingFavorites();

  // Event popover state
  const [popoverAnchor, setPopoverAnchor] = useState<HTMLElement | null>(null);
  const [popoverEvent, setPopoverEvent] = useState<CalendarEvent | null>(null);

  // Day detail popover
  const [dayPopoverAnchor, setDayPopoverAnchor] = useState<HTMLElement | null>(null);
  const [dayPopoverDate, setDayPopoverDate] = useState<{ year: number; month: number; day: number } | null>(
    null,
  );

  // Fetch events when month changes
  useEffect(() => {
    const start = formatDateISO(getMonthStart(currentYear, currentMonth));
    const end = formatDateISO(getMonthEnd(currentYear, currentMonth));
    dispatch(fetchCalendarEvents({ start, end }));
  }, [dispatch, currentYear, currentMonth]);

  // Fetch feeds once
  useEffect(() => {
    dispatch(fetchCalendarFeeds({}));
  }, [dispatch]);

  // Fetch sites for site selector
  useEffect(() => {
    if (sites.length === 0) {
      dispatch(fetchSites({}));
    }
  }, [dispatch, sites.length]);

  // Derive all plant keys from events for the tree filter
  const allEventPlantKeys = useMemo(() => {
    const keys = new Set<string>();
    for (const ev of events) {
      const meta = ev.metadata as Record<string, string> | undefined;
      const pk = meta?.plant_instance_key || ev.plant_key;
      if (pk) keys.add(pk);
    }
    return keys;
  }, [events]);

  // Effective checked keys: null means "all checked" (initial state)
  const effectiveCheckedKeys = useMemo(
    () => checkedPlantKeys ?? allEventPlantKeys,
    [checkedPlantKeys, allEventPlantKeys],
  );

  // Fetch sowing calendar when view mode or site changes
  useEffect(() => {
    if (viewMode === 'sowing') {
      dispatch(fetchSowingCalendar({ siteId: selectedSiteKey || undefined, year: currentYear }));
    }
  }, [dispatch, viewMode, selectedSiteKey, currentYear]);

  // Fetch season overview when view mode or site changes
  useEffect(() => {
    if (viewMode === 'season') {
      dispatch(fetchSeasonOverview({ siteId: selectedSiteKey || undefined, year: currentYear }));
    }
  }, [dispatch, viewMode, selectedSiteKey, currentYear]);

  // Filter events by selected categories + plant tree filter
  const isPlantFiltering = checkedPlantKeys !== null && effectiveCheckedKeys.size < allEventPlantKeys.size;
  const filteredEvents = useMemo(() => {
    let result = events.filter((e) => selectedCategories.has(e.category as CalendarEventCategory));
    if (isPlantFiltering) {
      result = result.filter((e) => {
        const meta = e.metadata as Record<string, string> | undefined;
        const pk = meta?.plant_instance_key || e.plant_key;
        // Events without plant association pass through
        if (!pk) return true;
        return effectiveCheckedKeys.has(pk);
      });
    }
    return result;
  }, [events, selectedCategories, isPlantFiltering, effectiveCheckedKeys]);

  // Grouped day entry: either a single event or a collapsed run group
  type DayEntry = { type: 'event'; event: CalendarEvent } | { type: 'run'; runKey: string; runName: string; events: CalendarEvent[]; color: string };

  // Group events by date for the month grid — collapse run instances into single entries
  const eventsByDay = useMemo(() => {
    const map = new Map<number, CalendarEvent[]>();
    for (const event of filteredEvents) {
      if (event.start) {
        const d = new Date(event.start);
        if (d.getFullYear() === currentYear && d.getMonth() === currentMonth) {
          const day = d.getDate();
          const existing = map.get(day) ?? [];
          existing.push(event);
          map.set(day, existing);
        }
      }
    }
    return map;
  }, [filteredEvents, currentYear, currentMonth]);

  // Build grouped entries per day (runs collapsed)
  const groupedByDay = useMemo(() => {
    const map = new Map<number, DayEntry[]>();
    for (const [day, dayEvents] of eventsByDay) {
      const entries: DayEntry[] = [];
      const runBuckets = new Map<string, CalendarEvent[]>();
      for (const ev of dayEvents) {
        const meta = ev.metadata as Record<string, string> | undefined;
        const rk = meta?.run_key;
        if (rk) {
          const bucket = runBuckets.get(rk) ?? [];
          bucket.push(ev);
          runBuckets.set(rk, bucket);
        } else {
          entries.push({ type: 'event', event: ev });
        }
      }
      for (const [runKey, runEvents] of runBuckets) {
        const meta = runEvents[0].metadata as Record<string, string>;
        entries.push({
          type: 'run',
          runKey,
          runName: meta?.run_name ?? runKey,
          events: runEvents,
          color: runEvents[0].color || CATEGORY_COLORS[runEvents[0].category as CalendarEventCategory] || '#9E9E9E',
        });
      }
      map.set(day, entries);
    }
    return map;
  }, [eventsByDay]);

  // Sort events for list view
  const sortedEvents = useMemo(
    () =>
      [...filteredEvents].sort((a, b) => {
        if (!a.start) return 1;
        if (!b.start) return -1;
        return new Date(a.start).getTime() - new Date(b.start).getTime();
      }),
    [filteredEvents],
  );

  // Events for a specific day (for day popover)
  const dayPopoverEvents = useMemo(() => {
    if (!dayPopoverDate) return [];
    return filteredEvents.filter((e) =>
      isSameDay(e.start, dayPopoverDate.year, dayPopoverDate.month, dayPopoverDate.day),
    );
  }, [filteredEvents, dayPopoverDate]);

  // Group day popover events: phase_transition events grouped by planting run, rest ungrouped
  const dayPopoverGrouped = useMemo(() => {
    const phaseEvents: CalendarEvent[] = [];
    const otherEvents: CalendarEvent[] = [];
    for (const ev of dayPopoverEvents) {
      if (ev.source === 'phase_transition') {
        phaseEvents.push(ev);
      } else {
        otherEvents.push(ev);
      }
    }
    // Group phase events by run_key (or '' for no run)
    const runGroups = new Map<string, { runName: string; runKey: string; events: CalendarEvent[] }>();
    for (const ev of phaseEvents) {
      const meta = ev.metadata as Record<string, string>;
      const rk = meta?.run_key ?? '';
      if (!runGroups.has(rk)) {
        runGroups.set(rk, { runKey: rk, runName: meta?.run_name ?? '', events: [] });
      }
      runGroups.get(rk)!.events.push(ev);
    }
    return { runGroups: [...runGroups.values()], otherEvents };
  }, [dayPopoverEvents]);

  // ── Navigation ───────────────────────────────────────────────────

  const goToPreviousMonth = useCallback(() => {
    if (currentMonth === 0) {
      setCurrentYear((y) => y - 1);
      setCurrentMonth(11);
    } else {
      setCurrentMonth((m) => m - 1);
    }
  }, [currentMonth]);

  const goToNextMonth = useCallback(() => {
    if (currentMonth === 11) {
      setCurrentYear((y) => y + 1);
      setCurrentMonth(0);
    } else {
      setCurrentMonth((m) => m + 1);
    }
  }, [currentMonth]);

  const goToToday = useCallback(() => {
    const now = new Date();
    setCurrentYear(now.getFullYear());
    setCurrentMonth(now.getMonth());
  }, []);

  // ── Category toggle ──────────────────────────────────────────────

  const toggleCategory = useCallback((category: CalendarEventCategory) => {
    setSelectedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  }, []);

  // ── Event popover ────────────────────────────────────────────────

  const handleEventClick = useCallback(
    (event: React.MouseEvent<HTMLElement>, calendarEvent: CalendarEvent) => {
      event.stopPropagation();
      setPopoverAnchor(event.currentTarget);
      setPopoverEvent(calendarEvent);
    },
    [],
  );

  const handleClosePopover = useCallback(() => {
    setPopoverAnchor(null);
    setPopoverEvent(null);
  }, []);

  // ── Day popover ──────────────────────────────────────────────────

  const handleDayClick = useCallback(
    (event: React.MouseEvent<HTMLElement>, year: number, month: number, day: number) => {
      const dayEvents = eventsByDay.get(day) ?? [];
      if (dayEvents.length > 0) {
        setDayPopoverAnchor(event.currentTarget);
        setDayPopoverDate({ year, month, day });
      }
    },
    [eventsByDay],
  );

  const handleCloseDayPopover = useCallback(() => {
    setDayPopoverAnchor(null);
    setDayPopoverDate(null);
  }, []);

  // ── Feed management ──────────────────────────────────────────────

  const handleCreateFeed = useCallback(async () => {
    if (!newFeedName.trim()) return;
    await dispatch(
      createCalendarFeed({
        name: newFeedName.trim(),
        filters: { categories: [...selectedCategories], site_key: null },
      }),
    ).unwrap();
    notification.success(t('common.saved'));
    setNewFeedName('');
    setCreateFeedDialogOpen(false);
  }, [dispatch, newFeedName, selectedCategories, notification, t]);

  const handleDeleteFeed = useCallback(async () => {
    if (!deleteFeedKey) return;
    await dispatch(deleteCalendarFeed(deleteFeedKey)).unwrap();
    notification.success(t('common.saved'));
    setDeleteFeedKey(null);
    setDeleteFeedName('');
  }, [dispatch, deleteFeedKey, notification, t]);

  const handleRegenerateToken = useCallback(
    async (key: string) => {
      await dispatch(regenerateCalendarFeedToken(key)).unwrap();
      notification.success(t('common.saved'));
    },
    [dispatch, notification, t],
  );

  const handleCopyUrl = useCallback(
    async (url: string) => {
      await navigator.clipboard.writeText(url);
      notification.success(t('pages.calendar.urlCopied'));
    },
    [notification, t],
  );

  // ── Watering confirmation ────────────────────────────────────────

  const [confirmingWatering, setConfirmingWatering] = useState<string | null>(null);

  const handleConfirmWatering = useCallback(
    async (plantKey: string) => {
      setConfirmingWatering(plantKey);
      try {
        await confirmReminder(plantKey, 'watering');
        notification.success(t('pages.calendar.wateringConfirmed'));
        handleClosePopover();
        handleCloseDayPopover();
        // Re-fetch calendar events so forecasts update
        const start = formatDateISO(getMonthStart(currentYear, currentMonth));
        const end = formatDateISO(getMonthEnd(currentYear, currentMonth));
        dispatch(fetchCalendarEvents({ start, end }));
      } catch {
        notification.error(t('common.retry'));
      } finally {
        setConfirmingWatering(null);
      }
    },
    [dispatch, currentYear, currentMonth, notification, t, handleClosePopover, handleCloseDayPopover],
  );

  // ── Format date for display ──────────────────────────────────────

  const formatMonthYear = useMemo(() => {
    const date = new Date(currentYear, currentMonth, 1);
    return date.toLocaleDateString(i18n.language === 'de' ? 'de-DE' : 'en-US', {
      month: 'long',
      year: 'numeric',
    });
  }, [currentYear, currentMonth, i18n.language]);

  const formatEventDate = useCallback(
    (dateStr: string | null) => {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return date.toLocaleDateString(i18n.language === 'de' ? 'de-DE' : 'en-US', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      });
    },
    [i18n.language],
  );

  const formatEventTime = useCallback(
    (dateStr: string | null) => {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return date.toLocaleTimeString(i18n.language === 'de' ? 'de-DE' : 'en-US', {
        hour: '2-digit',
        minute: '2-digit',
      });
    },
    [i18n.language],
  );

  // ── Weekday headers ──────────────────────────────────────────────

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

  // ── Render month grid ────────────────────────────────────────────

  const daysInMonth = getDaysInMonth(currentYear, currentMonth);
  const firstDayOfWeek = getFirstDayOfWeek(currentYear, currentMonth);
  const totalCells = Math.ceil((firstDayOfWeek + daysInMonth) / 7) * 7;
  const isToday = (day: number) =>
    today.getFullYear() === currentYear && today.getMonth() === currentMonth && today.getDate() === day;

  const renderMonthGrid = () => {
    const rows: React.ReactNode[] = [];
    let cells: React.ReactNode[] = [];
    const maxEntriesShown = 3;

    for (let i = 0; i < totalCells; i++) {
      const dayNum = i - firstDayOfWeek + 1;
      const isValidDay = dayNum >= 1 && dayNum <= daysInMonth;
      const dayEvents = isValidDay ? eventsByDay.get(dayNum) ?? [] : [];
      const dayEntries = isValidDay ? groupedByDay.get(dayNum) ?? [] : [];
      const overflowCount = dayEntries.length - maxEntriesShown;

      cells.push(
        <Box
          key={i}
          onClick={isValidDay ? (e) => handleDayClick(e, currentYear, currentMonth, dayNum) : undefined}
          role={isValidDay ? 'button' : undefined}
          tabIndex={isValidDay && dayEvents.length > 0 ? 0 : undefined}
          aria-label={
            isValidDay
              ? `${dayNum}. ${formatMonthYear}${dayEntries.length > 0 ? `, ${dayEntries.length} ${t('pages.calendar.title')}` : ''}`
              : undefined
          }
          onKeyDown={
            isValidDay
              ? (e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleDayClick(
                      e as unknown as React.MouseEvent<HTMLElement>,
                      currentYear,
                      currentMonth,
                      dayNum,
                    );
                  }
                }
              : undefined
          }
          data-testid={isValidDay ? `calendar-day-${dayNum}` : undefined}
          sx={{
            flex: '1 0 calc(100% / 7)',
            minHeight: { xs: '3.5rem', sm: '5.5rem', md: '7rem' },
            border: 1,
            borderColor: 'divider',
            p: { xs: 0.25, sm: 0.5 },
            cursor: isValidDay && dayEvents.length > 0 ? 'pointer' : 'default',
            bgcolor: isValidDay
              ? isToday(dayNum)
                ? 'action.selected'
                : 'background.paper'
              : 'action.disabledBackground',
            overflow: 'hidden',
            '&:hover': isValidDay && dayEvents.length > 0 ? { bgcolor: 'action.hover' } : {},
          }}
        >
          {isValidDay && (
            <>
              <Typography
                variant="caption"
                sx={{
                  fontWeight: isToday(dayNum) ? 700 : 500,
                  color: isToday(dayNum) ? 'primary.main' : 'text.secondary',
                  display: 'block',
                  lineHeight: 1.4,
                  mb: 0.25,
                }}
              >
                {dayNum}
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                {dayEntries.slice(0, maxEntriesShown).map((entry) => {
                  if (entry.type === 'run') {
                    const entryColor = entry.color;
                    return (
                      <Box
                        key={`run-${entry.runKey}`}
                        component="span"
                        role="button"
                        tabIndex={0}
                        aria-label={entry.runName}
                        sx={{
                          display: 'block',
                          borderLeft: `3px solid ${entryColor}`,
                          bgcolor: `${entryColor}18`,
                          borderRadius: '0 3px 3px 0',
                          px: 0.5,
                          py: '1px',
                          cursor: 'pointer',
                          overflow: 'hidden',
                          whiteSpace: 'nowrap',
                          textOverflow: 'ellipsis',
                          fontSize: '0.65rem',
                          lineHeight: 1.3,
                          color: 'text.primary',
                          '&:hover': { bgcolor: `${entryColor}30` },
                        }}
                      >
                        {entry.runName} ({entry.events.length})
                      </Box>
                    );
                  }
                  const ev = entry.event;
                  const evColor = ev.color || CATEGORY_COLORS[ev.category as CalendarEventCategory] || '#9E9E9E';
                  return (
                    <Box
                      key={ev.id}
                      component="span"
                      onClick={(e) => { e.stopPropagation(); handleEventClick(e, ev); }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          handleEventClick(e as unknown as React.MouseEvent<HTMLElement>, ev);
                        }
                      }}
                      role="button"
                      tabIndex={0}
                      aria-label={ev.title}
                      data-testid={`calendar-event-dot-${ev.id}`}
                      sx={{
                        display: 'block',
                        borderLeft: `3px solid ${evColor}`,
                        bgcolor: `${evColor}18`,
                        borderRadius: '0 3px 3px 0',
                        px: 0.5,
                        py: '1px',
                        cursor: 'pointer',
                        overflow: 'hidden',
                        whiteSpace: 'nowrap',
                        textOverflow: 'ellipsis',
                        fontSize: '0.65rem',
                        lineHeight: 1.3,
                        color: 'text.primary',
                        '&:hover': { bgcolor: `${evColor}30` },
                      }}
                    >
                      {ev.title}
                    </Box>
                  );
                })}
                {overflowCount > 0 && (
                  <Typography
                    variant="caption"
                    sx={{
                      color: 'text.secondary',
                      fontSize: '0.6rem',
                      lineHeight: 1.2,
                      fontWeight: 500,
                      cursor: 'pointer',
                      '&:hover': { color: 'primary.main' },
                    }}
                  >
                    +{overflowCount} {t('common.more')}
                  </Typography>
                )}
              </Box>
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
  };

  // ── Render list view ─────────────────────────────────────────────

  const renderListView = () => {
    if (sortedEvents.length === 0) {
      return <EmptyState illustration={kamiCalendar} message={t('pages.calendar.noEvents')} />;
    }

    return (
      <TableContainer component={Paper}>
        <Table size="small" aria-label={t('pages.calendar.title')}>
          <TableHead>
            <TableRow>
              <TableCell>{t('common.createdAt')}</TableCell>
              <TableCell>{t('pages.calendar.title')}</TableCell>
              <TableCell>{t('pages.calendar.categories')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedEvents.map((event) => (
              <TableRow
                key={event.id}
                hover
                sx={{ cursor: 'pointer' }}
                onClick={(e) => {
                  const link = getEventLink(event);
                  if (link) {
                    navigate(link);
                  } else {
                    handleEventClick(e, event);
                  }
                }}
                data-testid={`calendar-list-event-${event.id}`}
              >
                <TableCell>
                  <Typography variant="body2">
                    {formatEventDate(event.start)}
                    {!event.all_day && event.start && (
                      <Typography component="span" variant="caption" sx={{ ml: 1, color: 'text.secondary' }}>
                        {formatEventTime(event.start)}
                      </Typography>
                    )}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">{event.title}</Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={t(CATEGORY_I18N_KEYS[event.category as CalendarEventCategory] ?? 'pages.calendar.custom')}
                    sx={{
                      bgcolor: event.color || CATEGORY_COLORS[event.category as CalendarEventCategory] || 'grey.500',
                      color: 'common.white',
                      fontWeight: 500,
                    }}
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  // ── Render feed item ─────────────────────────────────────────────

  const renderFeedItem = (feed: CalendarFeed) => (
    <ListItem key={feed.key} divider data-testid={`feed-item-${feed.key}`}>
      <ListItemText
        primary={feed.name}
        secondary={
          feed.ical_url ? (
            <Typography
              variant="caption"
              component="span"
              sx={{
                display: 'block',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                maxWidth: '20rem',
              }}
            >
              {feed.ical_url}
            </Typography>
          ) : null
        }
      />
      <ListItemSecondaryAction>
        <Tooltip title={t('pages.calendar.copyUrl')}>
          <IconButton
            size="small"
            onClick={() => handleCopyUrl(feed.ical_url)}
            aria-label={t('pages.calendar.copyUrl')}
            data-testid={`feed-copy-${feed.key}`}
          >
            <ContentCopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title={t('pages.calendar.regenerateToken')}>
          <IconButton
            size="small"
            onClick={() => handleRegenerateToken(feed.key)}
            aria-label={t('pages.calendar.regenerateToken')}
            data-testid={`feed-regenerate-${feed.key}`}
          >
            <RefreshIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title={t('pages.calendar.deleteFeed')}>
          <IconButton
            size="small"
            onClick={() => {
              setDeleteFeedKey(feed.key);
              setDeleteFeedName(feed.name);
            }}
            aria-label={t('pages.calendar.deleteFeed')}
            data-testid={`feed-delete-${feed.key}`}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </ListItemSecondaryAction>
    </ListItem>
  );

  // ── Main render ──────────────────────────────────────────────────

  return (
    <Box data-testid="calendar-page">
      <PageTitle title={t('pages.calendar.title')} />

      {/* Toolbar: navigation + contextual filters */}
      <Box sx={{ mb: 2 }}>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 1,
            mb: 1,
          }}
        >
          <IconButton
            onClick={goToPreviousMonth}
            aria-label={t('common.back')}
            data-testid="calendar-prev-month"
          >
            <ChevronLeftIcon />
          </IconButton>
          <Typography variant="h6" component="span" sx={{ minWidth: '10rem', textAlign: 'center' }}>
            {formatMonthYear}
          </Typography>
          <IconButton
            onClick={goToNextMonth}
            aria-label={t('pages.calendar.monthView')}
            data-testid="calendar-next-month"
          >
            <ChevronRightIcon />
          </IconButton>
          <Button
            variant="outlined"
            size="small"
            startIcon={<TodayIcon />}
            onClick={goToToday}
            data-testid="calendar-today-btn"
          >
            {t('pages.calendar.today')}
          </Button>
          {(viewMode === 'sowing' || viewMode === 'season') && (
            <FormControl size="small" sx={{ minWidth: 140, ml: { xs: 0, sm: 'auto' } }}>
              <InputLabel id="calendar-site-label">{t('entities.site')}</InputLabel>
              <Select
                labelId="calendar-site-label"
                value={selectedSiteKey}
                label={t('entities.site')}
                onChange={(e) => setSelectedSiteKey(e.target.value)}
                data-testid="calendar-site-select"
              >
                <MenuItem value="">{t('common.all')}</MenuItem>
                {sites.map((s) => (
                  <MenuItem key={s.key} value={s.key}>{s.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          {viewMode === 'sowing' && (
            <Chip
              icon={<StarIcon />}
              label={t('pages.calendar.sowingCalendar.showFavoritesOnly')}
              variant={showFavoritesOnly ? 'filled' : 'outlined'}
              color="warning"
              onClick={() => setShowFavoritesOnly((p) => !p)}
              data-testid="sowing-favorites-filter"
            />
          )}
        </Box>
        {/* View tabs — separate row for better Mobile usability */}
        <Tabs
          value={viewMode}
          onChange={(_e, val) => setViewMode(val as ViewMode)}
          variant="scrollable"
          scrollButtons="auto"
          aria-label={t('pages.calendar.title')}
          sx={{ minHeight: 40 }}
        >
          <Tab icon={<CalendarViewMonthIcon />} iconPosition="start" label={t('pages.calendar.monthView')} value="month" data-testid="calendar-view-month" sx={{ minHeight: 40, py: 0.5, textTransform: 'none' }} />
          <Tab icon={<ViewListIcon />} iconPosition="start" label={t('pages.calendar.listView')} value="list" data-testid="calendar-view-list" sx={{ minHeight: 40, py: 0.5, textTransform: 'none' }} />
          <Tab icon={<TimelineIcon />} iconPosition="start" label={t('pages.calendar.phaseTimeline.title')} value="phases" data-testid="calendar-view-phases" sx={{ minHeight: 40, py: 0.5, textTransform: 'none' }} />
          <Tab icon={<GrassIcon />} iconPosition="start" label={t('pages.calendar.sowingCalendar.title')} value="sowing" data-testid="calendar-view-sowing" sx={{ minHeight: 40, py: 0.5, textTransform: 'none' }} />
          <Tab icon={<BarChartIcon />} iconPosition="start" label={t('pages.calendar.seasonOverview.title')} value="season" data-testid="calendar-view-season" sx={{ minHeight: 40, py: 0.5, textTransform: 'none' }} />
        </Tabs>
      </Box>

      {/* Category filter chips */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75, mb: 2 }} role="group" aria-label={t('pages.calendar.categories')}>
        {ALL_CATEGORIES.map((cat) => (
          <Chip
            key={cat}
            label={t(CATEGORY_I18N_KEYS[cat])}
            size="small"
            variant={selectedCategories.has(cat) ? 'filled' : 'outlined'}
            onClick={() => toggleCategory(cat)}
            data-testid={`category-filter-${cat}`}
            sx={{
              bgcolor: selectedCategories.has(cat) ? CATEGORY_COLORS[cat] : 'transparent',
              color: selectedCategories.has(cat) ? 'common.white' : 'text.primary',
              borderColor: CATEGORY_COLORS[cat],
              '&:hover': {
                bgcolor: selectedCategories.has(cat) ? CATEGORY_COLORS[cat] : `${CATEGORY_COLORS[cat]}22`,
              },
            }}
          />
        ))}
      </Box>

      {/* Calendar content */}
      {viewMode === 'sowing' ? (
        sowingLoading ? (
          <LoadingSkeleton variant="table" />
        ) : (
          <SowingCalendarView
            entries={sowingEntries}
            frostConfig={sowingFrostConfig}
            year={sowingYear}
            favorites={sowingFavorites}
            onToggleFavorite={handleToggleSowingFavorite}
            showFavoritesOnly={showFavoritesOnly}
          />
        )
      ) : viewMode === 'season' ? (
        seasonLoading ? (
          <LoadingSkeleton variant="table" />
        ) : seasonOverview ? (
          <SeasonOverviewView
            months={seasonOverview.months}
            year={seasonOverview.year}
            onMonthClick={(month) => {
              setCurrentMonth(month - 1);
              setViewMode('month');
            }}
          />
        ) : null
      ) : viewMode === 'phases' ? (
        loading ? (
          <LoadingSkeleton variant="table" />
        ) : (
          <PhaseTimelineView events={events} year={currentYear} month={currentMonth} />
        )
      ) : loading ? (
        <LoadingSkeleton variant="table" />
      ) : (
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
          {/* Main content */}
          <Box sx={{ flex: 1, minWidth: 0 }}>
            {viewMode === 'month' ? (
              <Paper sx={{ overflow: 'hidden' }} role="table" aria-label={t('pages.calendar.monthView')}>
                {/* Weekday headers */}
                <Box sx={{ display: 'flex', bgcolor: 'action.hover' }} role="row">
                  {weekdayHeaders.map((wh) => (
                    <Box
                      key={wh}
                      role="columnheader"
                      sx={{
                        flex: '1 0 calc(100% / 7)',
                        textAlign: 'center',
                        py: 0.75,
                      }}
                    >
                      <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'text.secondary' }}>
                        {wh}
                      </Typography>
                    </Box>
                  ))}
                </Box>
                {/* Day cells */}
                {filteredEvents.length === 0 && !loading ? (
                  <Box sx={{ p: 4 }}>
                    {renderMonthGrid()}
                  </Box>
                ) : (
                  renderMonthGrid()
                )}
              </Paper>
            ) : (
              renderListView()
            )}
          </Box>
          {/* Plant filter sidebar */}
          <Box sx={{ width: 280, flexShrink: 0, display: { xs: 'none', md: 'block' } }}>
            <PlantFilterTree
              events={events}
              checkedPlantKeys={effectiveCheckedKeys}
              onCheckedChange={setCheckedPlantKeys}
              expandedRuns={expandedRuns}
              onExpandedChange={setExpandedRuns}
            />
          </Box>
        </Box>
      )}

      {/* Event detail popover */}
      <Popover
        open={Boolean(popoverAnchor)}
        anchorEl={popoverAnchor}
        onClose={handleClosePopover}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
        data-testid="event-popover"
      >
        {popoverEvent && (
          <Box sx={{ p: 2, maxWidth: '20rem' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Box
                sx={{
                  width: '0.75rem',
                  height: '0.75rem',
                  borderRadius: '50%',
                  bgcolor:
                    popoverEvent.color ||
                    CATEGORY_COLORS[popoverEvent.category as CalendarEventCategory] ||
                    'grey.500',
                  flexShrink: 0,
                }}
              />
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                {popoverEvent.title}
              </Typography>
            </Box>
            <Chip
              size="small"
              label={t(
                CATEGORY_I18N_KEYS[popoverEvent.category as CalendarEventCategory] ?? 'pages.calendar.custom',
              )}
              sx={{
                bgcolor:
                  popoverEvent.color ||
                  CATEGORY_COLORS[popoverEvent.category as CalendarEventCategory] ||
                  'grey.500',
                color: 'common.white',
                mb: 1,
              }}
            />
            {popoverEvent.start && (
              <Typography variant="body2" sx={{ color: 'text.secondary', mb: 0.5 }}>
                {formatEventDate(popoverEvent.start)}
                {!popoverEvent.all_day && ` ${formatEventTime(popoverEvent.start)}`}
                {popoverEvent.end && !popoverEvent.all_day && ` - ${formatEventTime(popoverEvent.end)}`}
              </Typography>
            )}
            {popoverEvent.description && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                {popoverEvent.description}
              </Typography>
            )}
            {/* Phase-specific dosage hints for watering forecast events */}
            {popoverEvent.source === 'watering_forecast' && popoverEvent.metadata && (
              (() => {
                const meta = popoverEvent.metadata as Record<string, unknown>;
                const dosages = meta.dosages as Array<{ fertilizer_key: string; ml_per_liter: number; product_name?: string }> | undefined;
                const hasHints = meta.target_ec_ms != null || meta.target_ph != null || meta.volume_liters != null || (dosages && dosages.length > 0);
                if (!hasHints) return null;
                return (
                  <Box sx={{ mt: 1 }}>
                    <Divider sx={{ mb: 1 }} />
                    {meta.phase_name != null && (
                      <Chip
                        label={t(`enums.phaseName.${String(meta.phase_name)}`, { defaultValue: String(meta.phase_name) })}
                        size="small"
                        color="info"
                        variant="filled"
                        sx={{ mb: 0.75 }}
                      />
                    )}
                    <Box sx={{ display: 'flex', gap: 0.75, flexWrap: 'wrap', mb: 0.75 }}>
                      {meta.target_ec_ms != null && (
                        <Chip label={`EC ${meta.target_ec_ms} mS`} size="small" variant="outlined" />
                      )}
                      {meta.target_ph != null && (
                        <Chip label={`pH ${meta.target_ph}`} size="small" variant="outlined" />
                      )}
                      {meta.volume_liters != null && (
                        <Chip label={`${meta.volume_liters} L`} size="small" variant="outlined" />
                      )}
                    </Box>
                    {dosages && dosages.length > 0 && (
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                        {dosages.map((d) => (
                          <Chip
                            key={d.fertilizer_key}
                            label={`${d.product_name ?? d.fertilizer_key}: ${d.ml_per_liter} ml/L`}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    )}
                  </Box>
                );
              })()
            )}
            {(() => {
              const link = getEventLink(popoverEvent);
              if (!link) return null;
              return (
                <Button
                  size="small"
                  variant="text"
                  endIcon={<OpenInNewIcon sx={{ fontSize: '0.875rem' }} />}
                  onClick={() => {
                    handleClosePopover();
                    navigate(link);
                  }}
                  sx={{ mt: 1, textTransform: 'none' }}
                >
                  {t('pages.calendar.goToDetail')}
                </Button>
              );
            })()}
            {popoverEvent.source === 'watering_forecast' && popoverEvent.plant_key && (
              <Button
                size="small"
                variant="contained"
                color="success"
                startIcon={<CheckCircleOutlineIcon />}
                disabled={confirmingWatering === popoverEvent.plant_key}
                onClick={() => handleConfirmWatering(popoverEvent.plant_key!)}
                sx={{ mt: 1, textTransform: 'none' }}
                data-testid="confirm-watering-btn"
              >
                {t('pages.calendar.confirmWatering')}
              </Button>
            )}
          </Box>
        )}
      </Popover>

      {/* Day detail popover */}
      <Popover
        open={Boolean(dayPopoverAnchor)}
        anchorEl={dayPopoverAnchor}
        onClose={handleCloseDayPopover}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        transformOrigin={{ vertical: 'top', horizontal: 'center' }}
        data-testid="day-popover"
      >
        {dayPopoverDate && (
          <Box sx={{ p: 2, minWidth: '18rem', maxWidth: '24rem' }}>
            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
              {new Date(dayPopoverDate.year, dayPopoverDate.month, dayPopoverDate.day).toLocaleDateString(
                i18n.language === 'de' ? 'de-DE' : 'en-US',
                { day: 'numeric', month: 'long', year: 'numeric' },
              )}
            </Typography>
            <Divider sx={{ mb: 1 }} />
            {/* Phase transition events grouped by planting run */}
            {dayPopoverGrouped.runGroups.map((group) => (
              <Box key={group.runKey || '_ungrouped'} sx={{ mb: 1 }}>
                {group.runKey && (
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 0.5,
                      mb: 0.5,
                      cursor: 'pointer',
                      '&:hover': { textDecoration: 'underline' },
                    }}
                    role="link"
                    tabIndex={0}
                    onClick={() => {
                      handleCloseDayPopover();
                      navigate(getRunLink(group.runKey));
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        handleCloseDayPopover();
                        navigate(getRunLink(group.runKey));
                      }
                    }}
                  >
                    <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                      {group.runName || group.runKey}
                    </Typography>
                    <OpenInNewIcon sx={{ fontSize: '0.75rem', color: 'primary.main' }} />
                  </Box>
                )}
                {group.events.map((ev) => {
                  const link = getEventLink(ev);
                  const evColor = ev.color || CATEGORY_COLORS[ev.category as CalendarEventCategory] || '#9E9E9E';
                  return (
                    <Box
                      key={ev.id}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 0.75,
                        py: 0.5,
                        px: 0.75,
                        ml: group.runKey ? 1.5 : 0,
                        cursor: link ? 'pointer' : 'default',
                        '&:hover': link ? { bgcolor: 'action.hover' } : {},
                        borderRadius: 1,
                        borderLeft: `3px solid ${evColor}`,
                        bgcolor: `${evColor}0A`,
                      }}
                      role={link ? 'link' : undefined}
                      tabIndex={link ? 0 : undefined}
                      onClick={() => {
                        if (link) {
                          handleCloseDayPopover();
                          navigate(link);
                        }
                      }}
                      onKeyDown={(e) => {
                        if (link && (e.key === 'Enter' || e.key === ' ')) {
                          e.preventDefault();
                          handleCloseDayPopover();
                          navigate(link);
                        }
                      }}
                    >
                      <Typography variant="body2" noWrap sx={{ flex: 1, color: link ? 'primary.main' : 'text.primary' }}>
                        {ev.title}
                      </Typography>
                      {link && <OpenInNewIcon sx={{ fontSize: '0.75rem', color: 'text.secondary', flexShrink: 0 }} />}
                    </Box>
                  );
                })}
              </Box>
            ))}
            {/* Other (non-phase) events */}
            {dayPopoverGrouped.otherEvents.map((ev) => {
              const link = getEventLink(ev);
              const evColor = ev.color || CATEGORY_COLORS[ev.category as CalendarEventCategory] || '#9E9E9E';
              return (
                <Box
                  key={ev.id}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 0.75,
                    py: 0.5,
                    px: 0.75,
                    cursor: 'pointer',
                    '&:hover': { bgcolor: 'action.hover' },
                    borderRadius: 1,
                    borderLeft: `3px solid ${evColor}`,
                    bgcolor: `${evColor}0A`,
                    mb: 0.5,
                  }}
                  role="button"
                  tabIndex={0}
                  onClick={(e) => {
                    if (link) {
                      handleCloseDayPopover();
                      navigate(link);
                    } else {
                      handleCloseDayPopover();
                      handleEventClick(e, ev);
                    }
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      if (link) {
                        handleCloseDayPopover();
                        navigate(link);
                      } else {
                        handleCloseDayPopover();
                        handleEventClick(e as unknown as React.MouseEvent<HTMLElement>, ev);
                      }
                    }
                  }}
                >
                  <Typography variant="body2" noWrap sx={{ flex: 1, color: link ? 'primary.main' : 'text.primary' }}>
                    {!ev.all_day && ev.start && (
                      <Typography component="span" variant="caption" sx={{ color: 'text.secondary', mr: 0.5 }}>
                        {formatEventTime(ev.start)}
                      </Typography>
                    )}
                    {ev.title}
                  </Typography>
                  <Chip
                    size="small"
                    label={t(CATEGORY_I18N_KEYS[ev.category as CalendarEventCategory] ?? 'pages.calendar.custom')}
                    sx={{
                      bgcolor: evColor,
                      color: 'common.white',
                      height: 18,
                      fontSize: '0.6rem',
                      flexShrink: 0,
                      '& .MuiChip-label': { px: 0.75 },
                    }}
                  />
                  {link && <OpenInNewIcon sx={{ fontSize: '0.75rem', color: 'text.secondary', flexShrink: 0 }} />}
                  {ev.source === 'watering_forecast' && ev.plant_key && (
                    <Tooltip title={t('pages.calendar.confirmWatering')} arrow>
                      <IconButton
                        size="small"
                        color="success"
                        disabled={confirmingWatering === ev.plant_key}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleConfirmWatering(ev.plant_key!);
                        }}
                        aria-label={t('pages.calendar.confirmWatering')}
                        data-testid={`day-confirm-watering-${ev.plant_key}`}
                        sx={{ flexShrink: 0, p: 0.25 }}
                      >
                        <CheckCircleOutlineIcon sx={{ fontSize: '1rem' }} />
                      </IconButton>
                    </Tooltip>
                  )}
                </Box>
              );
            })}
          </Box>
        )}
      </Popover>

      {/* iCal Feeds section */}
      <Box sx={{ mt: 3 }}>
        <Button
          onClick={() => setFeedsSectionOpen((p) => !p)}
          startIcon={<RssFeedIcon />}
          endIcon={feedsSectionOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          variant="text"
          data-testid="feeds-toggle"
        >
          {t('pages.calendar.feeds')}
        </Button>
        <Collapse in={feedsSectionOpen}>
          <Paper sx={{ mt: 1, p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="subtitle1">{t('pages.calendar.feeds')}</Typography>
              <Button
                startIcon={<AddIcon />}
                size="small"
                variant="contained"
                onClick={() => setCreateFeedDialogOpen(true)}
                data-testid="create-feed-btn"
              >
                {t('pages.calendar.createFeed')}
              </Button>
            </Box>
            {feedsLoading ? (
              <LoadingSkeleton variant="card" />
            ) : feeds.length === 0 ? (
              <EmptyState
                illustration={kamiCalendar}
                message={t('pages.calendar.noEvents')}
                actionLabel={t('pages.calendar.createFeed')}
                onAction={() => setCreateFeedDialogOpen(true)}
              />
            ) : (
              <List dense>{feeds.map(renderFeedItem)}</List>
            )}
          </Paper>
        </Collapse>
      </Box>

      {/* Create feed dialog */}
      <Dialog
        open={createFeedDialogOpen}
        onClose={() => setCreateFeedDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        data-testid="create-feed-dialog"
      >
        <DialogTitle>{t('pages.calendar.createFeed')}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label={t('pages.calendar.feedName')}
            fullWidth
            value={newFeedName}
            onChange={(e) => setNewFeedName(e.target.value)}
            data-testid="feed-name-input"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateFeedDialogOpen(false)} data-testid="feed-cancel-btn">
            {t('common.cancel')}
          </Button>
          <Button
            onClick={handleCreateFeed}
            variant="contained"
            disabled={!newFeedName.trim()}
            data-testid="feed-save-btn"
          >
            {t('common.create')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete feed confirm dialog */}
      <ConfirmDialog
        open={Boolean(deleteFeedKey)}
        title={t('pages.calendar.deleteFeed')}
        message={t('common.deleteConfirm', { name: deleteFeedName })}
        onConfirm={handleDeleteFeed}
        onCancel={() => {
          setDeleteFeedKey(null);
          setDeleteFeedName('');
        }}
        destructive
      />
    </Box>
  );
}
