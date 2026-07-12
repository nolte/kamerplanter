import { useCallback, useMemo, useState, type MouseEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import ButtonBase from '@mui/material/ButtonBase';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Skeleton from '@mui/material/Skeleton';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import type { TFunction } from 'i18next';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import EventIcon from '@mui/icons-material/Event';
import GridViewIcon from '@mui/icons-material/GridView';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import PlaceIcon from '@mui/icons-material/Place';
import SpaIcon from '@mui/icons-material/Spa';
import ViewAgendaIcon from '@mui/icons-material/ViewAgenda';
import ViewModuleIcon from '@mui/icons-material/ViewModule';
import { useModuleVisibility } from '@/hooks/useModuleVisibility';
import { useColumnFilters } from '@/hooks/useColumnFilters';
import { ColumnFilterBar, type ColumnFilterDef } from '@/components/common/ColumnFilterBar';
import { useWidgetPayload } from '@/components/dashboard/DashboardDataContext';
import { dashboardWidgetCatalog } from '@/config/dashboardWidgetCatalog';
import { formatDate, humanizeSlug } from '@/utils/formatting';
import type { WidgetComponentProps } from '@/components/dashboard/widgetRegistry';

/**
 * DASH-2 / issue #488 — rich, filterable plant-instance grid widget.
 *
 * Turns the ``plant_grid`` panel from #461's icon+name tile strip into a
 * first-class overview: every active plant instance is its own compact card
 * carrying glanceable status (cultivar, current growth phase, location, next
 * due date), plants with an open task/care reminder are visibly flagged, the
 * panel is filterable on phase / location / open-task, and the user can switch
 * between a *detailed* (fewer, richer cards) and a *compact* (more, denser
 * cards) format.
 *
 * Data comes from the aggregated ``plant_grid`` payload (``useWidgetPayload``),
 * enriched server-side in a single AQL round-trip (no extra fetch, no N+1) — see
 * ``ArangoPlantInstanceRepository.list_active_for_tenant``.
 */

/** Route the panel + each card deep-link into (mirrors #461). */
const PLANT_LINK_BASE = '/pflanzen/plant-instances';

/** URL-param ids owned by this widget's filters (namespaced so several dashboard
 *  widgets can coexist without clashing query params). */
const FILTER_PHASE = 'pg_phase';
const FILTER_LOCATION = 'pg_location';
const FILTER_TASK = 'pg_task';
const FILTER_IDS = [FILTER_PHASE, FILTER_LOCATION, FILTER_TASK] as const;

/** Sentinel filter token for plants missing a phase / location. */
const NONE_TOKEN = '__none__';
/** Open-task facet tokens. */
const TASK_OPEN = 'open';
const TASK_NONE = 'none';

/** localStorage key persisting the chosen card format per user/browser (#488 AC6). */
const FORMAT_STORAGE_KEY = 'kp-plant-grid-format';
type CardFormat = 'detailed' | 'compact';
const DEFAULT_FORMAT: CardFormat = 'detailed';

/** One enriched plant-instance card as delivered in the aggregated ``plant_grid`` slice. */
export interface PlantGridEntry {
  _key?: string;
  plant_name?: string | null;
  species_key?: string;
  cultivar_key?: string | null;
  cultivar_name?: string | null;
  phase_key?: string | null;
  phase_name?: string | null;
  location_key?: string | null;
  location_name?: string | null;
  has_open_task?: boolean;
  next_due_date?: string | null;
}

function readStoredFormat(): CardFormat {
  try {
    const raw = window.localStorage.getItem(FORMAT_STORAGE_KEY);
    return raw === 'compact' || raw === 'detailed' ? raw : DEFAULT_FORMAT;
  } catch {
    // jsdom / privacy modes may throw on localStorage access — fall back silently.
    return DEFAULT_FORMAT;
  }
}

function persistFormat(format: CardFormat): void {
  try {
    window.localStorage.setItem(FORMAT_STORAGE_KEY, format);
  } catch {
    // Non-fatal: the choice simply won't survive a reload.
  }
}

export default function PlantGridWidget({ widgetKey, editMode = false }: WidgetComponentProps) {
  const { t } = useTranslation();
  const { isPathVisible } = useModuleVisibility();
  const { payload, loading } = useWidgetPayload(widgetKey);
  const columnFilters = useColumnFilters(FILTER_IDS);

  // Card format is user-owned and persisted in localStorage (AC6). Keeping it in
  // localStorage (not the dashboard widget config) keeps the widget self-contained
  // and makes the switch work identically in read-only and edit mode.
  const [format, setFormat] = useState<CardFormat>(readStoredFormat);
  const handleFormatChange = useCallback((_e: MouseEvent<HTMLElement>, next: CardFormat | null) => {
    if (next) {
      setFormat(next);
      persistFormat(next);
    }
  }, []);

  const plants = useMemo<PlantGridEntry[]>(() => {
    const obj =
      payload && typeof payload === 'object' && !Array.isArray(payload)
        ? (payload as Record<string, unknown>)
        : null;
    return obj && Array.isArray(obj.plants) ? (obj.plants as PlantGridEntry[]) : [];
  }, [payload]);

  const { values } = columnFilters;

  // ── Filter facet options, derived from the plants actually present ──
  const filterDefs = useMemo<ColumnFilterDef[]>(() => {
    const phaseByToken = new Map<string, string>();
    const locationByToken = new Map<string, string>();
    for (const p of plants) {
      const phaseToken = p.phase_key || NONE_TOKEN;
      phaseByToken.set(
        phaseToken,
        phaseToken === NONE_TOKEN
          ? t('dashboard.plantGrid.filterValues.noPhase')
          : p.phase_name || humanizeSlug(p.phase_key) || phaseToken,
      );
      const locToken = p.location_key || NONE_TOKEN;
      locationByToken.set(
        locToken,
        locToken === NONE_TOKEN
          ? t('dashboard.plantGrid.filterValues.noLocation')
          : p.location_name || humanizeSlug(p.location_key) || locToken,
      );
    }
    const toOptions = (m: Map<string, string>) =>
      [...m.entries()]
        .map(([value, label]) => ({ value, label }))
        // Stable, locale-aware ordering; the "none" sentinel sinks to the bottom.
        .sort((a, b) => {
          if (a.value === NONE_TOKEN) return 1;
          if (b.value === NONE_TOKEN) return -1;
          return a.label.localeCompare(b.label);
        });
    return [
      { id: FILTER_PHASE, label: t('dashboard.plantGrid.filters.phase'), options: toOptions(phaseByToken) },
      { id: FILTER_LOCATION, label: t('dashboard.plantGrid.filters.location'), options: toOptions(locationByToken) },
      {
        id: FILTER_TASK,
        label: t('dashboard.plantGrid.filters.task'),
        options: [
          { value: TASK_OPEN, label: t('dashboard.plantGrid.filterValues.hasTask') },
          { value: TASK_NONE, label: t('dashboard.plantGrid.filterValues.noTask') },
        ],
      },
    ];
  }, [plants, t]);

  // ── Client-side filtering (the payload is already loaded in full) ──
  const filtered = useMemo<PlantGridEntry[]>(() => {
    const phases = values[FILTER_PHASE] ?? [];
    const locations = values[FILTER_LOCATION] ?? [];
    const tasks = values[FILTER_TASK] ?? [];
    if (phases.length === 0 && locations.length === 0 && tasks.length === 0) return plants;
    return plants.filter((p) => {
      const phaseToken = p.phase_key || NONE_TOKEN;
      const locToken = p.location_key || NONE_TOKEN;
      const taskToken = p.has_open_task ? TASK_OPEN : TASK_NONE;
      if (phases.length > 0 && !phases.includes(phaseToken)) return false;
      if (locations.length > 0 && !locations.includes(locToken)) return false;
      if (tasks.length > 0 && !tasks.includes(taskToken)) return false;
      return true;
    });
  }, [plants, values]);

  const cardsLinkable = !editMode && isPathVisible(PLANT_LINK_BASE);
  const listPath = dashboardWidgetCatalog.plant_grid.navigateTo;
  const showListLink = !editMode && Boolean(listPath) && isPathVisible(listPath ?? '');
  const widgetLabel = t(`dashboard.widgets.${widgetKey}.label`);

  return (
    <Card sx={{ height: '100%' }} data-testid={`widget-${widgetKey}`}>
      <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 1 }}>
        {/* Header: icon + label + (read-only) open-list affordance. */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Typography
            variant="subtitle1"
            component="h3"
            sx={{ display: 'flex', alignItems: 'center', gap: 0.75, flexGrow: 1, minWidth: 0, m: 0 }}
          >
            <GridViewIcon color="primary" fontSize="small" aria-hidden="true" sx={{ flexShrink: 0 }} />
            <Box component="span" sx={{ minWidth: 0, overflowWrap: 'break-word' }}>
              {widgetLabel}
            </Box>
          </Typography>
          {showListLink && listPath && (
            <Tooltip title={t('dashboard.nav.openListNamed', { widget: widgetLabel })}>
              <IconButton
                component={RouterLink}
                to={listPath}
                size="small"
                aria-label={t('dashboard.nav.openListNamed', { widget: widgetLabel })}
                sx={{ width: 48, height: 48, color: 'text.secondary', flexShrink: 0 }}
                data-testid={`widget-${widgetKey}-open-list`}
              >
                <ChevronRightIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>

        {/* Controls (hidden in edit mode so drag/resize + kebab own the pointer). */}
        {!editMode && !loading && plants.length > 0 && (
          <Box
            sx={{
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'flex-start',
              justifyContent: 'space-between',
              gap: 1,
            }}
          >
            <Box sx={{ flexGrow: 1, minWidth: 0 }}>
              <ColumnFilterBar filters={filterDefs} state={columnFilters} />
            </Box>
            <ToggleButtonGroup
              value={format}
              exclusive
              onChange={handleFormatChange}
              size="small"
              aria-label={t('dashboard.plantGrid.format.label')}
              data-testid="plant-grid-format-switch"
            >
              <ToggleButton
                value="detailed"
                aria-label={t('dashboard.plantGrid.format.detailed')}
                sx={{ minWidth: 48, minHeight: 48 }}
                data-testid="plant-grid-format-detailed"
              >
                <Tooltip title={t('dashboard.plantGrid.format.detailed')}>
                  <ViewAgendaIcon fontSize="small" />
                </Tooltip>
              </ToggleButton>
              <ToggleButton
                value="compact"
                aria-label={t('dashboard.plantGrid.format.compact')}
                sx={{ minWidth: 48, minHeight: 48 }}
                data-testid="plant-grid-format-compact"
              >
                <Tooltip title={t('dashboard.plantGrid.format.compact')}>
                  <ViewModuleIcon fontSize="small" />
                </Tooltip>
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>
        )}

        {/* Body */}
        <Box sx={{ flexGrow: 1, minHeight: 0 }}>
          {loading ? (
            <Box
              aria-busy="true"
              aria-label={t('common.loading')}
              data-testid={`widget-${widgetKey}-loading`}
              sx={{ display: 'grid', gap: 1, gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))' }}
            >
              <Skeleton variant="rounded" height={72} />
              <Skeleton variant="rounded" height={72} />
              <Skeleton variant="rounded" height={72} />
            </Box>
          ) : plants.length === 0 ? (
            <Typography
              variant="body2"
              color="text.secondary"
              role="status"
              aria-live="polite"
              sx={{ textAlign: 'center', py: 3 }}
              data-testid={`widget-${widgetKey}-empty`}
            >
              {t('dashboard.plantGrid.empty')}
            </Typography>
          ) : filtered.length === 0 ? (
            <Typography
              variant="body2"
              color="text.secondary"
              role="status"
              aria-live="polite"
              sx={{ textAlign: 'center', py: 3 }}
              data-testid={`widget-${widgetKey}-no-matches`}
            >
              {t('dashboard.plantGrid.noMatches')}
            </Typography>
          ) : (
            <Box
              sx={{
                display: 'grid',
                gap: 1,
                gridTemplateColumns:
                  format === 'compact'
                    ? 'repeat(auto-fill, minmax(150px, 1fr))'
                    : 'repeat(auto-fill, minmax(220px, 1fr))',
              }}
              data-testid={`widget-${widgetKey}-cards`}
            >
              {filtered.map((p, i) => (
                <PlantGridCard
                  key={p._key ?? i}
                  plant={p}
                  format={format}
                  linkable={cardsLinkable && Boolean(p._key)}
                  t={t}
                />
              ))}
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}

interface PlantGridCardProps {
  plant: PlantGridEntry;
  format: CardFormat;
  linkable: boolean;
  t: TFunction;
}

function PlantGridCard({ plant, format, linkable, t }: PlantGridCardProps) {
  const title = plant.plant_name || humanizeSlug(plant.species_key) || t('dashboard.plantGrid.unnamed');
  const detailed = format === 'detailed';
  const hasTask = plant.has_open_task === true;

  // A single accessible name conveys the open-task flag non-visually (AC4 a11y),
  // so a screen reader announces it even though the visual cue is a coloured
  // accent + badge.
  const openTaskSuffix = hasTask ? ` — ${t('dashboard.plantGrid.card.openTaskAria')}` : '';
  const ariaLabel = (linkable ? t('dashboard.nav.openPlant', { plant: title }) : title) + openTaskSuffix;

  const cardSx = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'stretch',
    gap: 0.5,
    minHeight: 48, // ≥48px touch target (UI-NFR-001, Mobile-First)
    px: 1,
    py: 0.75,
    borderRadius: 1,
    border: 1,
    // Open-task plants get an accent border + left keyline so they stand out at a
    // glance (AC4). The colour cue is paired with a text badge below so the signal
    // is never colour-only.
    borderColor: hasTask ? 'warning.main' : 'divider',
    borderLeft: hasTask ? 4 : 1,
    borderLeftColor: hasTask ? 'warning.main' : 'divider',
    width: '100%',
    textAlign: 'left',
    bgcolor: 'background.paper',
  } as const;

  const body = (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, minWidth: 0 }}>
        <LocalFloristIcon color="primary" fontSize="small" aria-hidden="true" sx={{ flexShrink: 0 }} />
        <Typography variant="body2" sx={{ fontWeight: 600, minWidth: 0, overflowWrap: 'break-word' }}>
          {title}
        </Typography>
        {hasTask && (
          <NotificationsActiveIcon
            color="warning"
            fontSize="small"
            aria-hidden="true"
            sx={{ ml: 'auto', flexShrink: 0 }}
            data-testid={`plant-grid-open-task-${plant._key}`}
          />
        )}
      </Box>

      {detailed && plant.cultivar_name && (
        // Secondary content only (the plant name above is the primary,
        // never-truncated identifier) — `noWrap` keeps narrow compact-grid
        // cards tidy, and the `Tooltip` restores the full value on hover/tap
        // when it does clip.
        <Tooltip title={plant.cultivar_name}>
          <Typography variant="caption" color="text.secondary" noWrap>
            {plant.cultivar_name}
          </Typography>
        </Tooltip>
      )}

      {plant.phase_name && (
        <Chip
          icon={<SpaIcon />}
          label={plant.phase_name}
          size="small"
          variant="outlined"
          color="primary"
          aria-label={`${t('dashboard.plantGrid.card.phase')}: ${plant.phase_name}`}
          sx={{ alignSelf: 'flex-start', maxWidth: '100%' }}
        />
      )}

      {detailed && plant.location_name && (
        <Tooltip title={plant.location_name}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: 'text.secondary', minWidth: 0 }}>
            <PlaceIcon fontSize="inherit" aria-hidden="true" sx={{ flexShrink: 0 }} />
            <Typography variant="caption" noWrap>
              {plant.location_name}
            </Typography>
          </Box>
        </Tooltip>
      )}

      {detailed && plant.next_due_date && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, color: 'text.secondary', minWidth: 0 }}>
          <EventIcon fontSize="inherit" aria-hidden="true" sx={{ flexShrink: 0 }} />
          <Typography variant="caption" noWrap>
            {t('dashboard.plantGrid.card.nextDue', { date: formatDate(plant.next_due_date) })}
          </Typography>
        </Box>
      )}

      {hasTask && (
        <Chip
          label={t('dashboard.plantGrid.card.openTask')}
          size="small"
          color="warning"
          variant="outlined"
          sx={{ alignSelf: 'flex-start', mt: 0.25 }}
          data-testid={`plant-grid-open-task-chip-${plant._key}`}
        />
      )}
    </>
  );

  if (linkable) {
    return (
      <ButtonBase
        component={RouterLink}
        to={`${PLANT_LINK_BASE}/${plant._key}`}
        aria-label={ariaLabel}
        sx={{ ...cardSx, '&:hover': { bgcolor: 'action.hover' } }}
        data-testid={`plant-grid-card-${plant._key}`}
      >
        {body}
      </ButtonBase>
    );
  }
  return (
    <Box sx={cardSx} aria-label={hasTask ? ariaLabel : undefined} data-testid={`plant-grid-card-${plant._key}`}>
      {body}
    </Box>
  );
}
