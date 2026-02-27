import { useEffect, useState, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Popover from '@mui/material/Popover';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
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
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import TodayIcon from '@mui/icons-material/Today';
import CalendarViewMonthIcon from '@mui/icons-material/CalendarViewMonth';
import ViewListIcon from '@mui/icons-material/ViewList';
import RssFeedIcon from '@mui/icons-material/RssFeed';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import RefreshIcon from '@mui/icons-material/Refresh';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import AddIcon from '@mui/icons-material/Add';
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
} from '@/store/slices/calendarSlice';
import { useNotification } from '@/hooks/useNotification';
import type { CalendarEvent, CalendarEventCategory, CalendarFeed } from '@/api/types';

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
  custom: 'pages.calendar.custom',
};

type ViewMode = 'month' | 'list';

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

export default function CalendarPage() {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  const notification = useNotification();
  const { events, feeds, loading, feedsLoading } = useAppSelector((state) => state.calendar);

  const today = new Date();
  const [currentYear, setCurrentYear] = useState(today.getFullYear());
  const [currentMonth, setCurrentMonth] = useState(today.getMonth());
  const [viewMode, setViewMode] = useState<ViewMode>('month');
  const [selectedCategories, setSelectedCategories] = useState<Set<CalendarEventCategory>>(
    new Set(ALL_CATEGORIES),
  );
  const [feedsSectionOpen, setFeedsSectionOpen] = useState(false);
  const [createFeedDialogOpen, setCreateFeedDialogOpen] = useState(false);
  const [newFeedName, setNewFeedName] = useState('');
  const [deleteFeedKey, setDeleteFeedKey] = useState<string | null>(null);
  const [deleteFeedName, setDeleteFeedName] = useState('');

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

  // Filter events by selected categories
  const filteredEvents = useMemo(
    () => events.filter((e) => selectedCategories.has(e.category as CalendarEventCategory)),
    [events, selectedCategories],
  );

  // Group events by date for the month grid
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

    for (let i = 0; i < totalCells; i++) {
      const dayNum = i - firstDayOfWeek + 1;
      const isValidDay = dayNum >= 1 && dayNum <= daysInMonth;
      const dayEvents = isValidDay ? eventsByDay.get(dayNum) ?? [] : [];
      const maxDotsShown = 3;

      cells.push(
        <Box
          key={i}
          onClick={isValidDay ? (e) => handleDayClick(e, currentYear, currentMonth, dayNum) : undefined}
          role={isValidDay ? 'button' : undefined}
          tabIndex={isValidDay && dayEvents.length > 0 ? 0 : undefined}
          aria-label={
            isValidDay
              ? `${dayNum}. ${formatMonthYear}${dayEvents.length > 0 ? `, ${dayEvents.length} ${t('pages.calendar.title')}` : ''}`
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
            minHeight: { xs: '3rem', sm: '4.5rem', md: '5.5rem' },
            border: 1,
            borderColor: 'divider',
            p: 0.5,
            cursor: isValidDay && dayEvents.length > 0 ? 'pointer' : 'default',
            bgcolor: isValidDay
              ? isToday(dayNum)
                ? 'action.selected'
                : 'background.paper'
              : 'action.disabledBackground',
            '&:hover': isValidDay && dayEvents.length > 0 ? { bgcolor: 'action.hover' } : {},
          }}
        >
          {isValidDay && (
            <>
              <Typography
                variant="body2"
                sx={{
                  fontWeight: isToday(dayNum) ? 'bold' : 'normal',
                  color: isToday(dayNum) ? 'primary.main' : 'text.primary',
                }}
              >
                {dayNum}
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.25, mt: 0.25 }}>
                {dayEvents.slice(0, maxDotsShown).map((ev) => (
                  <Tooltip key={ev.id} title={ev.title} arrow>
                    <Box
                      component="span"
                      onClick={(e) => handleEventClick(e, ev)}
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
                        width: { xs: '0.5rem', sm: '0.625rem' },
                        height: { xs: '0.5rem', sm: '0.625rem' },
                        borderRadius: '50%',
                        bgcolor: ev.color || CATEGORY_COLORS[ev.category as CalendarEventCategory] || 'grey.500',
                        cursor: 'pointer',
                        display: 'inline-block',
                        flexShrink: 0,
                      }}
                    />
                  </Tooltip>
                ))}
                {dayEvents.length > maxDotsShown && (
                  <Typography variant="caption" sx={{ color: 'text.secondary', lineHeight: 1 }}>
                    +{dayEvents.length - maxDotsShown}
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
      return <EmptyState message={t('pages.calendar.noEvents')} />;
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
                onClick={(e) => handleEventClick(e, event)}
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

      {/* Toolbar: navigation + view toggle */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 1,
          mb: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
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
        </Box>

        <ToggleButtonGroup
          value={viewMode}
          exclusive
          onChange={(_e, val) => {
            if (val) setViewMode(val as ViewMode);
          }}
          size="small"
          aria-label={t('pages.calendar.monthView')}
        >
          <ToggleButton value="month" aria-label={t('pages.calendar.monthView')} data-testid="calendar-view-month">
            <CalendarViewMonthIcon />
          </ToggleButton>
          <ToggleButton value="list" aria-label={t('pages.calendar.listView')} data-testid="calendar-view-list">
            <ViewListIcon />
          </ToggleButton>
        </ToggleButtonGroup>
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
      {loading ? (
        <LoadingSkeleton variant="table" />
      ) : viewMode === 'month' ? (
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
          <Box sx={{ p: 2, minWidth: '15rem', maxWidth: '20rem' }}>
            <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
              {new Date(dayPopoverDate.year, dayPopoverDate.month, dayPopoverDate.day).toLocaleDateString(
                i18n.language === 'de' ? 'de-DE' : 'en-US',
                { day: 'numeric', month: 'long', year: 'numeric' },
              )}
            </Typography>
            <Divider sx={{ mb: 1 }} />
            {dayPopoverEvents.map((ev) => (
              <Box
                key={ev.id}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  py: 0.5,
                  cursor: 'pointer',
                  '&:hover': { bgcolor: 'action.hover' },
                  borderRadius: 1,
                  px: 0.5,
                }}
                role="button"
                tabIndex={0}
                onClick={(e) => {
                  handleCloseDayPopover();
                  handleEventClick(e, ev);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleCloseDayPopover();
                    handleEventClick(e as unknown as React.MouseEvent<HTMLElement>, ev);
                  }
                }}
              >
                <Box
                  sx={{
                    width: '0.5rem',
                    height: '0.5rem',
                    borderRadius: '50%',
                    bgcolor: ev.color || CATEGORY_COLORS[ev.category as CalendarEventCategory] || 'grey.500',
                    flexShrink: 0,
                  }}
                />
                <Typography variant="body2" noWrap>
                  {!ev.all_day && ev.start && (
                    <Typography component="span" variant="caption" sx={{ color: 'text.secondary', mr: 0.5 }}>
                      {formatEventTime(ev.start)}
                    </Typography>
                  )}
                  {ev.title}
                </Typography>
              </Box>
            ))}
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
