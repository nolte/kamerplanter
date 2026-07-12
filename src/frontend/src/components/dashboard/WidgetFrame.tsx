import { Suspense, useState, createElement, type MouseEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import CardActionArea from '@mui/material/CardActionArea';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Skeleton from '@mui/material/Skeleton';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import AddIcon from '@mui/icons-material/Add';
import RemoveIcon from '@mui/icons-material/Remove';
import SettingsIcon from '@mui/icons-material/Settings';
import DeleteIcon from '@mui/icons-material/Delete';
import ErrorBoundary from '@/components/common/ErrorBoundary';
import { getWidgetComponent } from '@/components/dashboard/widgetRegistry';
import { dashboardWidgetCatalog, type DashboardWidgetDefinition } from '@/config/dashboardWidgetCatalog';
import { useModuleVisibility } from '@/hooks/useModuleVisibility';
import { WIDGET_KEBAB_INSET, WIDGET_KEBAB_SIZE } from '@/lib/dashboardEditGridGeometry';
import type { DashboardWidgetInstance } from '@/api/types';

/**
 * Widgets that render their own inner navigation (links/buttons). Wrapping them
 * in a panel-level anchor (issue #439) would nest interactive content inside an
 * ``<a>`` — invalid HTML that trips React hydration and screen readers. Their
 * existing inner controls already carry the same navigation intent, so the
 * panel-level wrapper is intentionally skipped for these keys.
 *
 * ``winter_protection`` renders a rich self-navigating body. The entity-list
 * widgets (issue #461) render deep-linkable rows/tiles to a *single* entity plus
 * their own header "open list" affordance — so they, too, must not sit inside a
 * panel ``<a>`` (that would nest a row ``<a>`` in a panel ``<a>``). Both groups
 * therefore opt out of the panel wrapper here.
 */
const SELF_NAVIGATING_KEYS: ReadonlySet<string> = new Set([
  'winter_protection',
  'tasks_today',
  'next_calendar_events',
  'plant_grid',
]);

interface WidgetFrameProps {
  instance: DashboardWidgetInstance;
  editMode: boolean;
  hasConfig: boolean;
  isFirst: boolean;
  isLast: boolean;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onGrow: () => void;
  onShrink: () => void;
  onRemove: () => void;
  onConfigure: () => void;
}

/**
 * REQ-045 — renders one widget, isolated by an ErrorBoundary (REQ-009 DoD). In
 * edit mode it also carries a keyboard-accessible kebab menu (UI-NFR-002 U-001)
 * as the full keyboard parity for drag/resize — the drag handle itself is not
 * focusable.
 */
export default function WidgetFrame({
  instance,
  editMode,
  hasConfig,
  isFirst,
  isLast,
  onMoveUp,
  onMoveDown,
  onGrow,
  onShrink,
  onRemove,
  onConfigure,
}: WidgetFrameProps) {
  const { t } = useTranslation();
  const { isPathVisible } = useModuleVisibility();
  const [anchor, setAnchor] = useState<null | HTMLElement>(null);
  const open = Boolean(anchor);
  const Component = getWidgetComponent(instance.widget_key);

  const close = () => setAnchor(null);
  const run = (fn: () => void) => () => {
    fn();
    close();
  };

  const widgetNode = Component
    ? createElement(Component, {
        instanceId: instance.instance_id,
        widgetKey: instance.widget_key,
        config: instance.config,
        // Entity-list widgets (#461) render row/tile deep links; they must stay
        // inert in edit mode so drag/resize and the kebab menu are never hijacked.
        editMode,
      })
    : null;

  // Issue #439 — a mapped, module-visible widget panel becomes a link to its
  // detail/list view in read-only mode. Edit mode keeps the panel inert so the
  // kebab menu and drag/resize interactions are never hijacked by navigation.
  const def: DashboardWidgetDefinition | undefined = (
    dashboardWidgetCatalog as Record<string, DashboardWidgetDefinition>
  )[instance.widget_key];
  const navigateTo = def?.navigateTo;
  const isNavigational =
    !editMode &&
    widgetNode !== null &&
    !SELF_NAVIGATING_KEYS.has(instance.widget_key) &&
    Boolean(navigateTo) &&
    isPathVisible(navigateTo as string);

  // Wrap only the widget body (inside the ErrorBoundary/Suspense) so the error
  // fallback's retry button is never nested inside the navigation anchor.
  const body =
    isNavigational && navigateTo ? (
      <CardActionArea
        component={RouterLink}
        to={navigateTo}
        aria-label={t('dashboard.nav.openWidget', {
          widget: t(`dashboard.widgets.${instance.widget_key}.label`),
        })}
        sx={{
          display: 'block',
          height: '100%',
          borderRadius: 1,
          // ButtonBase unconditionally resets the native outline (see MUI
          // source); its own focusHighlight is a subtle ~12% tint that is easy
          // to miss on a large, content-heavy panel. Match the explicit
          // focus-visible ring already established for clickable rows in
          // DataTable (WCAG 2.4.7) instead of relying on the tint alone.
          '&.Mui-focusVisible': {
            outline: '2px solid',
            outlineColor: 'primary.main',
            outlineOffset: -2,
          },
        }}
        data-testid={`widget-nav-${instance.widget_key}`}
      >
        {widgetNode}
        {/* Decorative "this panel opens a page" affordance. Hover/focus tint
            alone is not a persistent cue on touch devices (no :hover state),
            which is the primary usage environment (Mobile-First) — so a small,
            always-visible chevron distinguishes a navigable panel from a
            static one (e.g. weather_forecast, quick_actions) even before the
            first tap. Purely decorative: aria-hidden + pointer-events none so
            it never intercepts the tap and never duplicates the accessible
            name already carried by the CardActionArea. */}
        <ChevronRightIcon
          aria-hidden="true"
          fontSize="small"
          sx={{ position: 'absolute', top: 8, right: 8, color: 'text.disabled', pointerEvents: 'none' }}
          data-testid={`widget-nav-affordance-${instance.widget_key}`}
        />
      </CardActionArea>
    ) : (
      widgetNode
    );

  return (
    <Box sx={{ position: 'relative', height: '100%' }} data-testid={`widget-frame-${instance.widget_key}`}>
      {editMode && (
        <Box
          sx={{
            position: 'absolute',
            top: `${WIDGET_KEBAB_INSET}px`,
            right: `${WIDGET_KEBAB_INSET}px`,
            // DASH-1 (#487) — belt-and-suspenders over the handle-geometry fix
            // in DashboardEditGrid: the east resize handle is a *sibling* of
            // this widget in the `.react-grid-item` stacking context, so raise
            // the kebab above it (z-index) AND have it claim pointer events in
            // its own rectangle (pointer-events). z-index alone only reorders
            // paint; it does not re-route a pointer-down if the handle wins
            // hit-testing — both are needed to guarantee a tap opens the menu
            // (U-006, UI-NFR-001 R-011). Scoped to the grid item's stacking
            // context (`.react-grid-item` has a transform), so it never escapes
            // above the app chrome.
            zIndex: 3,
            pointerEvents: 'auto',
          }}
        >
          <IconButton
            size="small"
            aria-label={t('dashboard.edit.widgetMenu', { widget: t(`dashboard.widgets.${instance.widget_key}.label`) })}
            aria-haspopup="menu"
            aria-expanded={open}
            onClick={(e: MouseEvent<HTMLElement>) => setAnchor(e.currentTarget)}
            // A default IconButton (icon at rgba .54, no background) was nearly
            // invisible on a white widget card and read as part of the title. The
            // ≥48px touch target (mobile-first, U-006) lives on this outer button;
            // the opaque paper backdrop is painted on a smaller inner circle (see
            // `.widget-menu-affordance` below) so the *visible* footprint stays
            // well clear of a centred card title on narrow (minSize w=2) widgets
            // with long labels (e.g. "Pflanzenschutz-Warnungen") — same
            // hit-area-larger-than-visual technique already used for the grid
            // resize handles. Theme tokens keep contrast correct in light and
            // dark; `text.primary` on `background.paper` clears WCAG AA.
            sx={{
              width: WIDGET_KEBAB_SIZE,
              height: WIDGET_KEBAB_SIZE,
              p: 0,
              color: 'text.primary',
              '&:hover .widget-menu-affordance': { bgcolor: 'action.hover', boxShadow: 4 },
            }}
            data-testid={`widget-menu-${instance.widget_key}`}
          >
            <Box
              className="widget-menu-affordance"
              sx={{
                width: 34,
                height: 34,
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                bgcolor: 'background.paper',
                border: 1,
                borderColor: 'divider',
                boxShadow: 2,
              }}
            >
              <MoreVertIcon fontSize="small" />
            </Box>
          </IconButton>
          <Menu anchorEl={anchor} open={open} onClose={close}>
            {/* MUI's non-dense MenuItem resets `minHeight: 48` back to `auto` at
                the `sm` breakpoint (>=600px) — i.e. on every viewport wider than a
                phone, which is exactly where this edit-mode menu is used most
                (tablet drag/resize). Without an explicit floor the rendered row
                shrinks to ~36px, under the 48px touch target this same file
                already enforces for the trigger button and the resize handle
                (UI-NFR-001 R-011 MUSS, REQ-045 §3.8 U-006). */}
            <MenuItem
              onClick={run(onMoveUp)}
              disabled={isFirst}
              sx={{ minHeight: 48 }}
              data-testid={`widget-move-up-${instance.widget_key}`}
            >
              <ListItemIcon>
                <ArrowUpwardIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>{t('dashboard.edit.moveUp')}</ListItemText>
            </MenuItem>
            <MenuItem
              onClick={run(onMoveDown)}
              disabled={isLast}
              sx={{ minHeight: 48 }}
              data-testid={`widget-move-down-${instance.widget_key}`}
            >
              <ListItemIcon>
                <ArrowDownwardIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>{t('dashboard.edit.moveDown')}</ListItemText>
            </MenuItem>
            <MenuItem onClick={run(onGrow)} sx={{ minHeight: 48 }}>
              <ListItemIcon>
                <AddIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>{t('dashboard.edit.grow')}</ListItemText>
            </MenuItem>
            <MenuItem onClick={run(onShrink)} sx={{ minHeight: 48 }}>
              <ListItemIcon>
                <RemoveIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>{t('dashboard.edit.shrink')}</ListItemText>
            </MenuItem>
            {hasConfig && (
              <MenuItem
                onClick={run(onConfigure)}
                sx={{ minHeight: 48 }}
                data-testid={`widget-configure-${instance.widget_key}`}
              >
                <ListItemIcon>
                  <SettingsIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>{t('dashboard.edit.configure')}</ListItemText>
              </MenuItem>
            )}
            {/* Destructive action: red icon/text, matching the `color="error"`
                convention used for every other delete affordance in the codebase
                (e.g. detail-page delete buttons, CalendarPage/WorkflowDetailPage
                delete icon buttons) — the kebab menu was the one place still
                rendering "Remove" in the neutral default colour. */}
            <MenuItem
              onClick={run(onRemove)}
              sx={{ minHeight: 48, color: 'error.main' }}
              data-testid={`widget-remove-${instance.widget_key}`}
            >
              <ListItemIcon sx={{ color: 'error.main' }}>
                <DeleteIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>{t('dashboard.edit.remove')}</ListItemText>
            </MenuItem>
          </Menu>
        </Box>
      )}

      <ErrorBoundary
        title={t('dashboard.widgetError.title')}
        hint={t('dashboard.widgetError.hint')}
        retryLabel={t('common.retry')}
        testId={`widget-error-${instance.widget_key}`}
      >
        <Suspense fallback={<Skeleton variant="rounded" height="100%" sx={{ minHeight: 120 }} />}>
          {body}
        </Suspense>
      </ErrorBoundary>
    </Box>
  );
}
