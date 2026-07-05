import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useSnackbar } from 'notistack';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Switch from '@mui/material/Switch';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import Stack from '@mui/material/Stack';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import { visuallyHidden } from '@mui/utils';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import AddIcon from '@mui/icons-material/Add';
import RemoveIcon from '@mui/icons-material/Remove';
import SettingsIcon from '@mui/icons-material/Settings';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import LockIcon from '@mui/icons-material/Lock';
import WidgetConfigDialog from '@/components/dashboard/WidgetConfigDialog';
import { useAppDispatch } from '@/store/hooks';
import { fetchWidgetCatalog } from '@/store/slices/dashboardSlice';
import { useDashboardLayout } from '@/hooks/useDashboardLayout';
import {
  dashboardWidgetCatalog,
  WIDGET_CATEGORIES,
  placementsForBreakpoint,
  type WidgetKey,
} from '@/config/dashboardWidgetCatalog';
import {
  toggleWidget,
  moveWidget,
  resizeWidget,
  setWidgetConfig,
  copyPlacementsToAllBreakpoints,
  sortByReadingOrder,
} from '@/lib/dashboardLayoutOps';
import type { DashboardLayout, DashboardWidgetInstance } from '@/api/types';

type Breakpoint = 'lg' | 'md' | 'sm';

/**
 * REQ-045 §3.8 — the primary, fully keyboard-accessible personalization surface
 * (Settings → Dashboard, deep-link /settings#dashboard). Add/remove widgets,
 * per-widget config, accessible reorder/resize (UI-NFR-002), per-breakpoint
 * editing, and reset-to-default.
 */
export default function DashboardSettingsTab() {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useAppDispatch();
  const { layout, catalogByKey, catalogLoaded, isWidgetRenderable, persist, reset } = useDashboardLayout();
  const [breakpoint, setBreakpoint] = useState<Breakpoint>('lg');

  // The settings tab is reachable directly via /settings#dashboard without
  // visiting /dashboard first — load the server-authoritative widget catalog so
  // gated widgets show as locked (not silently toggleable).
  useEffect(() => {
    if (!catalogLoaded) void dispatch(fetchWidgetCatalog());
  }, [dispatch, catalogLoaded]);
  const [announcement, setAnnouncement] = useState('');
  const [configTarget, setConfigTarget] = useState<DashboardWidgetInstance | null>(null);

  const activeKeys = useMemo(
    () => new Set(layout.widgets.map((w) => w.widget_key)),
    [layout.widgets],
  );

  const orderedActive = useMemo(() => {
    const placements = placementsForBreakpoint(layout, breakpoint);
    const byId = new Map(layout.widgets.map((w) => [w.instance_id, w]));
    return sortByReadingOrder(placements)
      .map((p) => byId.get(p.instance_id))
      .filter((w): w is DashboardWidgetInstance => Boolean(w));
  }, [layout, breakpoint]);

  const save = (next: DashboardLayout, announce?: string) => {
    persist(next);
    if (announce) setAnnouncement(announce);
    enqueueSnackbar(t('common.saved'), { variant: 'success' });
  };

  const handleToggle = (widgetKey: WidgetKey) => {
    save(toggleWidget(layout, widgetKey));
  };

  const handleConfigSave = (config: Record<string, unknown>) => {
    if (!configTarget) return;
    save(setWidgetConfig(layout, configTarget.instance_id, config));
  };

  const grouped = useMemo(
    () =>
      WIDGET_CATEGORIES.map((category) => ({
        category,
        widgets: Object.values(dashboardWidgetCatalog).filter((w) => w.category === category),
      })),
    [],
  );

  return (
    <Box data-testid="dashboard-settings-tab">
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 1,
          mb: 1,
        }}
      >
        <Typography variant="h6">{t('dashboard.settings.title')}</Typography>
        <Button
          startIcon={<RestartAltIcon />}
          onClick={() => {
            reset();
            enqueueSnackbar(t('common.saved'), { variant: 'success' });
          }}
          sx={{ minHeight: 48 }}
          data-testid="dashboard-reset"
        >
          {t('dashboard.settings.reset')}
        </Button>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('dashboard.settings.subtitle')}
      </Typography>

      <Box aria-live="polite" role="status" sx={visuallyHidden}>
        {announcement}
      </Box>

      {/* ── Active widgets: accessible reorder/resize (UI-NFR-002) ── */}
      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 1,
            }}
          >
            <Typography variant="subtitle1">{t('dashboard.settings.arrange')}</Typography>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
              <ToggleButtonGroup
                size="small"
                exclusive
                value={breakpoint}
                onChange={(_, v) => v && setBreakpoint(v)}
                aria-label={t('dashboard.edit.breakpointSwitcher')}
              >
                <ToggleButton value="lg" sx={{ minWidth: 48, minHeight: 48 }}>
                  {t('dashboard.edit.desktop')}
                </ToggleButton>
                <ToggleButton value="md" sx={{ minWidth: 48, minHeight: 48 }}>
                  {t('dashboard.edit.tablet')}
                </ToggleButton>
                <ToggleButton value="sm" sx={{ minWidth: 48, minHeight: 48 }}>
                  {t('dashboard.edit.mobile')}
                </ToggleButton>
              </ToggleButtonGroup>
              <Button
                size="small"
                onClick={() => save(copyPlacementsToAllBreakpoints(layout, breakpoint))}
                sx={{ minHeight: 48 }}
              >
                {t('dashboard.edit.applyToAllShort')}
              </Button>
            </Stack>
          </Box>
          <Divider sx={{ my: 1.5 }} />
          {orderedActive.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              {t('dashboard.settings.noActive')}
            </Typography>
          ) : (
            <Stack divider={<Divider flexItem />} spacing={0.5}>
              {orderedActive.map((instance, idx) => {
                const def = dashboardWidgetCatalog[instance.widget_key as WidgetKey];
                const renderable = isWidgetRenderable(instance.widget_key);
                const label = t(`dashboard.widgets.${instance.widget_key}.label`);
                return (
                  <Box
                    key={instance.instance_id}
                    sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 0.5 }}
                    data-testid={`dashboard-active-${instance.widget_key}`}
                  >
                    <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                      <Typography variant="body2" noWrap>
                        {label}
                      </Typography>
                      {!renderable && (
                        <Typography variant="caption" color="warning.main">
                          {t('dashboard.settings.inactiveModuleHidden')}
                        </Typography>
                      )}
                    </Box>
                    <Tooltip title={t('dashboard.edit.moveUp')}>
                      <span>
                        <IconButton
                          size="small"
                          disabled={idx === 0}
                          aria-label={t('dashboard.edit.moveUpOf', { widget: label })}
                          onClick={() =>
                            save(
                              moveWidget(layout, breakpoint, instance.instance_id, 'up'),
                              t('dashboard.edit.movedUp', { widget: label }),
                            )
                          }
                          sx={{ minWidth: 48, minHeight: 48 }}
                          data-testid={`dashboard-up-${instance.widget_key}`}
                        >
                          <ArrowUpwardIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
                    <Tooltip title={t('dashboard.edit.moveDown')}>
                      <span>
                        <IconButton
                          size="small"
                          disabled={idx === orderedActive.length - 1}
                          aria-label={t('dashboard.edit.moveDownOf', { widget: label })}
                          onClick={() =>
                            save(
                              moveWidget(layout, breakpoint, instance.instance_id, 'down'),
                              t('dashboard.edit.movedDown', { widget: label }),
                            )
                          }
                          sx={{ minWidth: 48, minHeight: 48 }}
                          data-testid={`dashboard-down-${instance.widget_key}`}
                        >
                          <ArrowDownwardIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
                    <Tooltip title={t('dashboard.edit.shrink')}>
                      <IconButton
                        size="small"
                        aria-label={t('dashboard.edit.shrinkOf', { widget: label })}
                        onClick={() =>
                          save(
                            resizeWidget(layout, breakpoint, instance.instance_id, -1, -1),
                            t('dashboard.edit.shrank', { widget: label }),
                          )
                        }
                        sx={{ minWidth: 48, minHeight: 48 }}
                      >
                        <RemoveIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={t('dashboard.edit.grow')}>
                      <IconButton
                        size="small"
                        aria-label={t('dashboard.edit.growOf', { widget: label })}
                        onClick={() =>
                          save(
                            resizeWidget(layout, breakpoint, instance.instance_id, 1, 1),
                            t('dashboard.edit.grew', { widget: label }),
                          )
                        }
                        sx={{ minWidth: 48, minHeight: 48 }}
                      >
                        <AddIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    {def?.hasConfig && (
                      <Tooltip title={t('dashboard.edit.configure')}>
                        <IconButton
                          size="small"
                          aria-label={t('dashboard.edit.configureOf', { widget: label })}
                          onClick={() => setConfigTarget(instance)}
                          sx={{ minWidth: 48, minHeight: 48 }}
                          data-testid={`dashboard-config-${instance.widget_key}`}
                        >
                          <SettingsIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                );
              })}
            </Stack>
          )}
        </CardContent>
      </Card>

      {/* ── Widget catalog: add / remove ── */}
      {grouped.map(({ category, widgets }) => {
        const categoryHeadingId = `dashboard-category-heading-${category}`;
        return (
          <Accordion key={category} defaultExpanded data-testid={`dashboard-category-${category}`}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />} id={categoryHeadingId}>
              <Typography>{t(`dashboard.categories.${category}`)}</Typography>
            </AccordionSummary>
            {/* role="group" + aria-labelledby link this widget list to its category
              heading so screen-readers announce the context (UI-NFR-002 R-010),
              analog ModulesSettingsTab.tsx (REQ-042). */}
            <AccordionDetails role="group" aria-labelledby={categoryHeadingId}>
              <Stack divider={<Divider flexItem />}>
                {widgets.map((def) => {
                  const entry = catalogByKey.get(def.key);
                  const gated = entry ? !entry.available : false;
                  const checked = activeKeys.has(def.key);
                  return (
                    <Box
                      key={def.key}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1.5,
                        py: 1,
                        minHeight: 48,
                        opacity: gated ? 0.6 : 1,
                      }}
                      data-testid={`dashboard-widget-row-${def.key}`}
                    >
                      <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                        <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                          <Typography variant="body1">{t(def.labelKey)}</Typography>
                          {gated && (
                            <Chip
                              size="small"
                              icon={<LockIcon />}
                              label={t(entry?.unavailable_reason ?? 'dashboard.gate.moduleHidden')}
                              color="default"
                            />
                          )}
                        </Stack>
                        <Typography variant="caption" color="text.secondary">
                          {t(def.descriptionKey)}
                        </Typography>
                      </Box>
                      <Switch
                        checked={checked}
                        disabled={gated}
                        onChange={() => handleToggle(def.key)}
                        slotProps={{ input: { 'aria-label': t(def.labelKey) } }}
                        data-testid={`dashboard-switch-${def.key}`}
                      />
                    </Box>
                  );
                })}
              </Stack>
            </AccordionDetails>
          </Accordion>
        );
      })}

      {configTarget && (
        <WidgetConfigDialog
          open
          widgetKey={configTarget.widget_key}
          config={configTarget.config ?? {}}
          onClose={() => setConfigTarget(null)}
          onSave={handleConfigSave}
        />
      )}
    </Box>
  );
}
