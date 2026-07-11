import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Box from '@mui/material/Box';
import ButtonBase from '@mui/material/ButtonBase';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Skeleton from '@mui/material/Skeleton';
import Chip from '@mui/material/Chip';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
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
import { useModuleVisibility } from '@/hooks/useModuleVisibility';
import { dashboardWidgetCatalog, type WidgetKey } from '@/config/dashboardWidgetCatalog';
import { formatDate, humanizeSlug } from '@/utils/formatting';
import type { WidgetComponentProps } from '@/components/dashboard/widgetRegistry';

/**
 * REQ-045 / issue #461 — entity deep links.
 *
 * Widgets that render a list of individual entities let the user jump straight
 * to a single entity (row/tile → detail) in addition to the panel-level "open
 * list" affordance in the header. The panel-level ``<a>`` wrapper (issue #439)
 * is intentionally skipped for these keys in ``WidgetFrame`` so a row ``<a>`` is
 * never nested inside a panel ``<a>`` (invalid, a11y-breaking markup).
 */
const TASK_ROW_LINK_BASE = '/aufgaben/tasks';
const PLANT_TILE_LINK_BASE = '/pflanzen/plant-instances';
/** Widgets whose ``upcoming_tasks`` rows deep-link to a single task detail view. */
const TASK_ROW_WIDGETS: ReadonlySet<string> = new Set(['tasks_today', 'next_calendar_events']);

/** A raw plant-instance tile as delivered in the aggregated ``plant_grid`` slice. */
interface PlantTile {
  _key?: string;
  plant_name?: string | null;
  species_key?: string;
}

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
export default function GenericWidget({ widgetKey, editMode = false }: WidgetComponentProps) {
  const { t } = useTranslation();
  const l = useLocalizedField();
  const { isPathVisible } = useModuleVisibility();
  const { payload, loading } = useWidgetPayload(widgetKey);
  const glossaryTerm = WIDGET_GLOSSARY_TERM[widgetKey];
  const HeaderIcon = WIDGET_ICON[widgetKey] ?? WidgetsIcon;
  const widgetLabel = t(`dashboard.widgets.${widgetKey}.label`);

  const payloadObj =
    payload && typeof payload === 'object' && !Array.isArray(payload)
      ? (payload as Record<string, unknown>)
      : null;

  const numbers = payloadObj
    ? Object.entries(payloadObj).filter(([, v]) => typeof v === 'number')
    : [];

  // Widgets carrying an `upcoming_tasks` slice render an event list. A
  // non-null-but-empty array renders a proper "nothing due" state. tasks_today
  // carries both counts *and* the list, so metrics and events are rendered
  // independently (not either/or) below.
  const events =
    payloadObj && Array.isArray(payloadObj.upcoming_tasks)
      ? (payloadObj.upcoming_tasks as UpcomingTask[])
      : null;

  // plant_grid carries a `plants` slice rendered as clickable tiles (#461).
  const plants =
    widgetKey === 'plant_grid' && payloadObj && Array.isArray(payloadObj.plants)
      ? (payloadObj.plants as PlantTile[])
      : null;

  // ── Deep-link enablement (#461) ──
  // Rows/tiles link to a single entity only in read-only mode (never edit mode,
  // where drag/resize + the kebab menu own the pointer) and only when the target
  // route's module is visible (REQ-042). The header "open list" affordance points
  // at the widget's catalog navigateTo (the same list the panel linked to before).
  const isEntityWidget = TASK_ROW_WIDGETS.has(widgetKey) || widgetKey === 'plant_grid';
  const taskRowsLinkable = !editMode && TASK_ROW_WIDGETS.has(widgetKey) && isPathVisible(TASK_ROW_LINK_BASE);
  const plantTilesLinkable = !editMode && widgetKey === 'plant_grid' && isPathVisible(PLANT_TILE_LINK_BASE);
  const listPath = dashboardWidgetCatalog[widgetKey as WidgetKey]?.navigateTo;
  const showListLink = isEntityWidget && !editMode && Boolean(listPath) && isPathVisible(listPath ?? '');

  return (
    <Card sx={{ height: '100%' }} data-testid={`widget-${widgetKey}`}>
      <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
          <Typography
            variant="subtitle1"
            component="h3"
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 0.75,
              flexGrow: 1,
              minWidth: 0,
              m: 0,
            }}
          >
            <HeaderIcon color="primary" fontSize="small" aria-hidden="true" sx={{ flexShrink: 0 }} />
            {/* `minWidth: 0` + `overflowWrap: 'break-word'` let a long, hyphen-less
                German compound label (e.g. "Pflegeerinnerungen") wrap mid-word
                instead of overflowing the card, where MUI Card's `overflow: hidden`
                would clip it right under the edit-mode kebab menu (WidgetFrame,
                top-right corner). */}
            <Box component="span" sx={{ minWidth: 0, overflowWrap: 'break-word' }}>
              {widgetLabel}
            </Box>
            {glossaryTerm && <HelpTooltip term={glossaryTerm} iconOnly />}
          </Typography>
          {/* Panel-level "open list" affordance (#461). The whole-panel link
              (issue #439) is skipped for entity widgets so their row/tile links
              are never nested in a panel <a>; this header link restores the
              panel → list navigation as a sibling anchor, gated by module
              visibility and hidden in edit mode. */}
          {showListLink && listPath && (
            <Tooltip title={t('dashboard.nav.openListNamed', { widget: widgetLabel })}>
              <IconButton
                component={RouterLink}
                to={listPath}
                size="small"
                aria-label={t('dashboard.nav.openListNamed', { widget: widgetLabel })}
                // ≥48×48px touch target (UI-NFR-001 R-011, MUSS, Mobile-First).
                sx={{ width: 48, height: 48, color: 'text.secondary', flexShrink: 0 }}
                data-testid={`widget-${widgetKey}-open-list`}
              >
                <ChevronRightIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>

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
        ) : plants !== null ? (
          // plant_grid → a grid of clickable plant tiles, each deep-linking to
          // its detail view (#461). An empty tenant renders an honest empty state.
          plants.length > 0 ? (
            <Box
              sx={{
                display: 'grid',
                gap: 1,
                gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
                width: '100%',
              }}
              data-testid={`widget-${widgetKey}-tiles`}
            >
              {plants.map((p, i) => {
                // A plant without a user-given name falls back to a humanized
                // species-key slug ("ocimum-basilicum" → "Ocimum Basilicum")
                // rather than the raw key — the dashboard aggregate has no
                // species-catalog lookup to resolve a real display name.
                const tileLabel = p.plant_name || humanizeSlug(p.species_key) || t('dashboard.plantGrid.unnamed');
                const tileLinkable = plantTilesLinkable && Boolean(p._key);
                const tileSx = {
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-start',
                  gap: 0.75,
                  minHeight: 48, // ≥48px touch target (Mobile-First)
                  px: 1,
                  py: 0.5,
                  borderRadius: 1,
                  border: 1,
                  borderColor: 'divider',
                  width: '100%',
                  textAlign: 'left',
                } as const;
                const inner = (
                  <>
                    <LocalFloristIcon color="primary" fontSize="small" aria-hidden="true" />
                    <Typography variant="body2" noWrap sx={{ minWidth: 0 }}>
                      {tileLabel}
                    </Typography>
                  </>
                );
                return tileLinkable ? (
                  <ButtonBase
                    key={p._key ?? i}
                    component={RouterLink}
                    to={`${PLANT_TILE_LINK_BASE}/${p._key}`}
                    aria-label={t('dashboard.nav.openPlant', { plant: tileLabel })}
                    sx={{ ...tileSx, '&:hover': { bgcolor: 'action.hover' } }}
                    data-testid={`widget-plant_grid-tile-${p._key}`}
                  >
                    {inner}
                  </ButtonBase>
                ) : (
                  <Box key={p._key ?? i} sx={tileSx}>
                    {inner}
                  </Box>
                );
              })}
            </Box>
          ) : (
            <Typography
              variant="body2"
              color="text.secondary"
              aria-live="polite"
              sx={{ textAlign: 'center' }}
              data-testid={`widget-${widgetKey}-tiles-empty`}
            >
              {t('dashboard.plantGrid.empty')}
            </Typography>
          )
        ) : numbers.length > 0 || events !== null ? (
          // Metrics and the event list are rendered independently (not either/or):
          // tasks_today carries both its counts *and* the upcoming-task rows.
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, width: '100%' }}>
            {numbers.length > 0 && (
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
            )}

            {events !== null &&
              (events.length > 0 ? (
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
                    const chip = categoryLabel ? (
                      <Chip
                        label={categoryLabel}
                        size="small"
                        variant="outlined"
                        aria-label={`${t('enums.category')}: ${categoryLabel}`}
                      />
                    ) : undefined;
                    // Task/event names must stay fully readable (no noWrap /
                    // ellipsis on primary content, UI-NFR-008) — only secondary
                    // metadata may truncate.
                    const primary = l(ev, 'name') || t('dashboard.events.untitled');
                    const secondary = formatDate(ev.due_date);
                    const rowLinkable = taskRowsLinkable && Boolean(ev._key);
                    // Deep-link the row to its single task (#461). The Chip is a
                    // non-interactive `secondaryAction` rendered *outside* the
                    // ListItemButton, so no interactive content is ever nested in
                    // the row <a>.
                    return rowLinkable ? (
                      <ListItem key={ev._key ?? i} disableGutters disablePadding secondaryAction={chip}>
                        <ListItemButton
                          component={RouterLink}
                          to={`${TASK_ROW_LINK_BASE}/${ev._key}`}
                          aria-label={t('dashboard.nav.openTask', { task: primary })}
                          sx={{ minHeight: 48, borderRadius: 1 }}
                          data-testid={`widget-${widgetKey}-row-${ev._key}`}
                        >
                          <ListItemText primary={primary} secondary={secondary} />
                        </ListItemButton>
                      </ListItem>
                    ) : (
                      <ListItem key={ev._key ?? i} disableGutters secondaryAction={chip}>
                        <ListItemText primary={primary} secondary={secondary} />
                      </ListItem>
                    );
                  })}
                </List>
              ) : (
                // Only surface a standalone "nothing due" when the events list is
                // the widget's primary content — next to a "0 due today" count it
                // would be redundant.
                numbers.length === 0 && (
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
              ))}
          </Box>
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
