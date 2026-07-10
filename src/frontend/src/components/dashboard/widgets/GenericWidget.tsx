import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Skeleton from '@mui/material/Skeleton';
import Chip from '@mui/material/Chip';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import TaskAltIcon from '@mui/icons-material/TaskAlt';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import EventIcon from '@mui/icons-material/Event';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import BugReportIcon from '@mui/icons-material/BugReport';
import AgricultureIcon from '@mui/icons-material/Agriculture';
import TipsAndUpdatesIcon from '@mui/icons-material/TipsAndUpdates';
import GroupsIcon from '@mui/icons-material/Groups';
import TimelineIcon from '@mui/icons-material/Timeline';
import GridViewIcon from '@mui/icons-material/GridView';
import WidgetsIcon from '@mui/icons-material/Widgets';
import type { SvgIconComponent } from '@mui/icons-material';
import HelpTooltip from '@/components/common/HelpTooltip';
import { useWidgetPayload } from '@/components/dashboard/DashboardDataContext';
import { useLocalizedField } from '@/hooks/useLocalizedField';
import { formatDate } from '@/utils/formatting';
import type { WidgetComponentProps } from '@/components/dashboard/widgetRegistry';

/**
 * Widgets whose title is itself a domain jargon term (UI-NFR-011) get the
 * shared glossary tooltip next to the heading. Only map keys with an existing
 * `glossary.<term>` entry — see `i18n/locales/{de,en}/translation.json`.
 */
const WIDGET_GLOSSARY_TERM: Partial<Record<string, string>> = {
  ipm_alerts: 'ipm',
};

/**
 * A recognisable icon per widget so every card carries a visual identity in its
 * header (not just a text label). Unmapped keys fall back to a neutral glyph.
 */
const WIDGET_ICON: Partial<Record<string, SvgIconComponent>> = {
  tasks_today: TaskAltIcon,
  care_reminders: NotificationsActiveIcon,
  active_plants_summary: LocalFloristIcon,
  tank_status: WaterDropIcon,
  next_calendar_events: EventIcon,
  onboarding_progress: RocketLaunchIcon,
  ipm_alerts: BugReportIcon,
  harvest_forecast: AgricultureIcon,
  daily_tip: TipsAndUpdatesIcon,
  community_activity: GroupsIcon,
  phase_timeline: TimelineIcon,
  plant_grid: GridViewIcon,
};

/**
 * A raw task document as delivered in the aggregated `upcoming_tasks` slice.
 * These are unmapped Arango docs, so the identifier is `_key` (not `key`).
 */
interface UpcomingTask {
  _key?: string;
  name?: string;
  name_de?: string;
  category?: string;
  due_date?: string;
}

/**
 * REQ-045 — generic widget shell for widgets whose rich REQ-009 view is not yet
 * implemented. It renders the catalog label with a header icon and one of four
 * mandatory states (REQ-009 DoD):
 *   1. loading   — skeleton,
 *   2. events    — the `upcoming_tasks` slice as a dated list (tasks_today,
 *                  next_calendar_events),
 *   3. metrics   — any numeric slices as stat tiles (care_reminders, …),
 *   4. empty     — an icon + description + "in preparation" chip, so a widget
 *                  without a data source reads as intentional, not broken.
 */
export default function GenericWidget({ widgetKey }: WidgetComponentProps) {
  const { t } = useTranslation();
  const l = useLocalizedField();
  const { payload, loading } = useWidgetPayload(widgetKey);
  const glossaryTerm = WIDGET_GLOSSARY_TERM[widgetKey];
  const HeaderIcon = WIDGET_ICON[widgetKey] ?? WidgetsIcon;

  const payloadObj =
    payload && typeof payload === 'object' && !Array.isArray(payload)
      ? (payload as Record<string, unknown>)
      : null;

  const numbers = payloadObj
    ? Object.entries(payloadObj).filter(([, v]) => typeof v === 'number')
    : [];

  // Widgets carrying an `upcoming_tasks` slice (next_calendar_events) render an
  // event list. A non-null-but-empty array still renders a proper "nothing due"
  // state rather than falling through to the coming-soon placeholder.
  const events =
    payloadObj && Array.isArray(payloadObj.upcoming_tasks)
      ? (payloadObj.upcoming_tasks as UpcomingTask[])
      : null;

  return (
    <Card sx={{ height: '100%' }} data-testid={`widget-${widgetKey}`}>
      <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Typography
          variant="subtitle1"
          component="h3"
          gutterBottom
          sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.75 }}
        >
          <HeaderIcon color="primary" fontSize="small" aria-hidden="true" />
          {t(`dashboard.widgets.${widgetKey}.label`)}
          {glossaryTerm && <HelpTooltip term={glossaryTerm} iconOnly />}
        </Typography>

        {/* Body fills the remaining card height and vertical-centres its content
            so short widgets sit in the middle of a fixed-height grid cell rather
            than clinging to the top. Horizontal centring is per-block (metrics /
            empty state centre; the event list stays full-width, left-aligned). */}
        <Box
          sx={{
            flexGrow: 1,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            width: '100%',
          }}
        >
        {loading ? (
          <Box
            aria-busy="true"
            aria-label={t('common.loading')}
            data-testid={`widget-${widgetKey}-loading`}
          >
            <Skeleton variant="rounded" height={48} />
          </Box>
        ) : numbers.length > 0 ? (
          // Numeric slices → centred stat tiles. A widget that carries a metric
          // (e.g. tasks_today) shows only its count; the upcoming-task list lives
          // in the dedicated next_calendar_events widget, so a task due today is
          // never counted here and repeated as a list row below.
          <Box sx={{ display: 'flex', gap: { xs: 2.5, sm: 3 }, flexWrap: 'wrap', justifyContent: 'center' }}>
            {numbers.map(([k, v]) => {
              const metricLabel = t(`dashboard.widgets.${widgetKey}.metrics.${k}`, {
                defaultValue: k.replace(/_/g, ' '),
              });
              return (
                // Value + label are exposed as a single accessible name so a
                // screen reader announces "<label>: <value>" instead of the
                // visual top-to-bottom order (number, then caption).
                <Box key={k} role="group" aria-label={`${metricLabel}: ${v}`} sx={{ minWidth: 72, textAlign: 'center' }}>
                  <Typography
                    variant="h4"
                    component="p"
                    color="primary.main"
                    aria-hidden="true"
                    sx={{ fontWeight: 600, lineHeight: 1.1 }}
                  >
                    {String(v)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" aria-hidden="true">
                    {metricLabel}
                  </Typography>
                </Box>
              );
            })}
          </Box>
        ) : events !== null ? (
          events.length > 0 ? (
            <List
              dense
              disablePadding
              sx={{ width: '100%', textAlign: 'left' }}
              data-testid={`widget-${widgetKey}-events`}
            >
              {events.map((ev, i) => {
                const categoryLabel = ev.category
                  ? t(`enums.taskCategory.${ev.category}`, { defaultValue: ev.category })
                  : null;
                return (
                  <ListItem
                    key={ev._key ?? i}
                    disableGutters
                    secondaryAction={
                      categoryLabel ? (
                        <Chip
                          label={categoryLabel}
                          size="small"
                          variant="outlined"
                          aria-label={`${t('enums.category')}: ${categoryLabel}`}
                        />
                      ) : undefined
                    }
                  >
                    {/* Task/event names must stay fully readable (no noWrap /
                        ellipsis on primary content, see UI-NFR-008 overflow
                        rules) — only secondary metadata may truncate. */}
                    <ListItemText
                      primary={l(ev, 'name') || t('dashboard.events.untitled')}
                      secondary={formatDate(ev.due_date)}
                    />
                  </ListItem>
                );
              })}
            </List>
          ) : (
            <Typography
              variant="body2"
              color="text.secondary"
              aria-live="polite"
              sx={{ textAlign: 'center' }}
              data-testid={`widget-${widgetKey}-events-empty`}
            >
              {t('dashboard.events.none')}
            </Typography>
          )
        ) : (
          <Box
            role="status"
            aria-live="polite"
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
              gap: 1,
              py: 3,
              px: 1,
            }}
            data-testid={`widget-${widgetKey}-empty`}
          >
            <HeaderIcon sx={{ fontSize: 40, color: 'text.disabled' }} aria-hidden="true" />
            <Typography variant="body2" color="text.secondary">
              {t(`dashboard.widgets.${widgetKey}.description`)}
            </Typography>
            <Chip
              label={t('dashboard.widgets.comingSoon')}
              size="small"
              variant="outlined"
            />
          </Box>
        )}
        </Box>
      </CardContent>
    </Card>
  );
}
