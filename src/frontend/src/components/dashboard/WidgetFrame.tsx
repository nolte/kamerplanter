import { Suspense, useState, createElement, type MouseEvent } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Skeleton from '@mui/material/Skeleton';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import AddIcon from '@mui/icons-material/Add';
import RemoveIcon from '@mui/icons-material/Remove';
import SettingsIcon from '@mui/icons-material/Settings';
import DeleteIcon from '@mui/icons-material/Delete';
import ErrorBoundary from '@/components/common/ErrorBoundary';
import { getWidgetComponent } from '@/components/dashboard/widgetRegistry';
import type { DashboardWidgetInstance } from '@/api/types';

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
      })
    : null;

  return (
    <Box sx={{ position: 'relative', height: '100%' }} data-testid={`widget-frame-${instance.widget_key}`}>
      {editMode && (
        <Box sx={{ position: 'absolute', top: 4, right: 4, zIndex: 2 }}>
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
              width: 48,
              height: 48,
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
            <MenuItem onClick={run(onMoveUp)} disabled={isFirst} data-testid={`widget-move-up-${instance.widget_key}`}>
              <ListItemIcon>
                <ArrowUpwardIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>{t('dashboard.edit.moveUp')}</ListItemText>
            </MenuItem>
            <MenuItem onClick={run(onMoveDown)} disabled={isLast} data-testid={`widget-move-down-${instance.widget_key}`}>
              <ListItemIcon>
                <ArrowDownwardIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>{t('dashboard.edit.moveDown')}</ListItemText>
            </MenuItem>
            <MenuItem onClick={run(onGrow)}>
              <ListItemIcon>
                <AddIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>{t('dashboard.edit.grow')}</ListItemText>
            </MenuItem>
            <MenuItem onClick={run(onShrink)}>
              <ListItemIcon>
                <RemoveIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>{t('dashboard.edit.shrink')}</ListItemText>
            </MenuItem>
            {hasConfig && (
              <MenuItem onClick={run(onConfigure)} data-testid={`widget-configure-${instance.widget_key}`}>
                <ListItemIcon>
                  <SettingsIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>{t('dashboard.edit.configure')}</ListItemText>
              </MenuItem>
            )}
            <MenuItem onClick={run(onRemove)} data-testid={`widget-remove-${instance.widget_key}`}>
              <ListItemIcon>
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
          {widgetNode}
        </Suspense>
      </ErrorBoundary>
    </Box>
  );
}
