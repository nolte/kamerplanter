import type { ComponentType, MouseEvent } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Paper from '@mui/material/Paper';
import BottomNavigation from '@mui/material/BottomNavigation';
import BottomNavigationAction from '@mui/material/BottomNavigationAction';
import GlobalStyles from '@mui/material/GlobalStyles';
import DashboardIcon from '@mui/icons-material/Dashboard';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import TaskAltIcon from '@mui/icons-material/TaskAlt';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { setSidebarOpen } from '@/store/slices/uiSlice';
import { BOTTOM_NAV_HEIGHT, BOTTOM_NAV_OFFSET } from './bottomNavOffset';

interface Destination {
  key: string;
  /** Where the entry leads. */
  path: string;
  /** Path prefixes under which the entry is the active one (the list and its detail pages). */
  activeFor: readonly string[];
  labelKey: string;
  icon: ComponentType;
}

/**
 * UI-NFR-005 R-024/R-025 — the same four destinations for every experience level, in this order. Experience
 * level and module visibility act on the drawer behind "Mehr" (R-026), never here: the bar keeps its place
 * when the level changes.
 */
export const BOTTOM_NAV_DESTINATIONS: readonly Destination[] = [
  { key: 'start', path: '/dashboard', activeFor: ['/dashboard'], labelKey: 'nav.bottomNav.start', icon: DashboardIcon },
  {
    key: 'plants',
    path: '/pflanzen/plant-instances',
    activeFor: ['/pflanzen/plant-instances'],
    labelKey: 'nav.bottomNav.plants',
    icon: LocalFloristIcon,
  },
  {
    key: 'tasks',
    path: '/aufgaben/queue',
    // A task's detail page belongs to the queue it was opened from.
    activeFor: ['/aufgaben/queue', '/aufgaben/tasks'],
    labelKey: 'nav.bottomNav.tasks',
    icon: TaskAltIcon,
  },
  { key: 'calendar', path: '/kalender', activeFor: ['/kalender'], labelKey: 'nav.bottomNav.calendar', icon: CalendarMonthIcon },
];

const MORE = 'more';

function isUnder(pathname: string, prefix: string): boolean {
  return pathname === prefix || pathname.startsWith(`${prefix}/`);
}

/** A plain primary click — a modified one (new tab, new window) is the browser's, not ours. */
function isPlainClick(event: MouseEvent): boolean {
  return event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey;
}

function scrollToTop(): void {
  const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
  window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
}

const offset = `var(${BOTTOM_NAV_OFFSET})`;

/** What has to clear the bar while it is there (see `BOTTOM_NAV_OFFSET`). */
const clearanceStyles = {
  ':root': {
    [BOTTOM_NAV_OFFSET]: `calc(${BOTTOM_NAV_HEIGHT}px + env(safe-area-inset-bottom, 0px))`,
    // The document is the shell's scroll container (`main` does not scroll), and the root's `scroll-padding`
    // is what the viewport uses: whatever the browser scrolls into view — a control reached with Tab, an
    // anchor, `scrollIntoView` — stops above the bar instead of behind it (WCAG 2.2 SC 2.4.11). A pinned
    // form row may override it inline with its own, larger reservation (`useStickyBarScrollPadding`).
    scrollPaddingBottom: offset,
  },
  // A dialog covers the bar (full screen below `sm`): inside it nothing has to clear it.
  '.MuiDialog-root': { [BOTTOM_NAV_OFFSET]: '0px' },
  // notistack's bottom container sits 14 px above the edge, MUI's Snackbar 8 px (24 px from `sm`).
  'body .notistack-SnackbarContainer': { bottom: `calc(14px + ${offset})` },
  'body .MuiSnackbar-anchorOriginBottomLeft, body .MuiSnackbar-anchorOriginBottomCenter, body .MuiSnackbar-anchorOriginBottomRight':
    { bottom: `calc(8px + ${offset})` },
} as const;

/**
 * UI-NFR-005 R-023..R-031 — the bottom navigation of the phone layout (below `md`).
 *
 * Four links and "Mehr", which opens the existing sidebar as a drawer instead of a second menu. Every
 * destination is a real `<a>` (R-013a), the active one carries `aria-current="page"`; tapping the active
 * destination again scrolls to the top (R-029) without a new history entry. Labels are always shown.
 */
export default function MobileBottomNav() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { pathname } = useLocation();
  const drawerOpen = useAppSelector((s) => s.ui.sidebarOpen);

  const active = BOTTOM_NAV_DESTINATIONS.find((d) => d.activeFor.some((prefix) => isUnder(pathname, prefix)));

  const actionSx = {
    // MUI's 80 px minimum would make five entries 400 px wide — wider than a 360-390 px phone.
    minWidth: 0,
    minHeight: BOTTOM_NAV_HEIGHT,
    px: 0.5,
    // The selected label keeps its size, so the row does not shift on a tap.
    '& .MuiBottomNavigationAction-label, & .MuiBottomNavigationAction-label.Mui-selected': {
      fontSize: '0.75rem',
      // At a large text zoom a label stays on one line inside its 1/5 of the bar instead of spilling into
      // the neighbour; the accessible name is the full text either way.
      display: 'block',
      maxWidth: '100%',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
    },
    // The theme's ring sits outside the control; at the screen edge it would be cut off.
    '&.Mui-focusVisible': { outlineOffset: -2 },
  };

  return (
    <>
      <GlobalStyles styles={clearanceStyles} />
      <Paper
        component="nav"
        aria-label={t('nav.bottomNav.label')}
        data-testid="bottom-nav"
        elevation={8}
        square
        sx={{
          position: 'fixed',
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: (theme) => theme.zIndex.appBar,
          // The home indicator / gesture bar of the phone stays free.
          pb: 'env(safe-area-inset-bottom, 0px)',
        }}
      >
        <BottomNavigation showLabels value={active?.key ?? false} sx={{ height: BOTTOM_NAV_HEIGHT }}>
          {BOTTOM_NAV_DESTINATIONS.map((destination) => {
            const Icon = destination.icon;
            const isActive = destination === active;
            return (
              <BottomNavigationAction
                key={destination.key}
                value={destination.key}
                label={t(destination.labelKey)}
                icon={<Icon />}
                component={RouterLink}
                to={destination.path}
                aria-current={isActive ? 'page' : undefined}
                data-testid={`bottom-nav-${destination.key}`}
                onClick={(event: MouseEvent) => {
                  if (!isPlainClick(event) || pathname !== destination.path) return;
                  // Already there: back to the top instead of a second visit of the same page (R-029).
                  event.preventDefault();
                  scrollToTop();
                }}
                sx={actionSx}
              />
            );
          })}
          <BottomNavigationAction
            value={MORE}
            label={t('nav.bottomNav.more')}
            icon={<MoreHorizIcon />}
            aria-haspopup="dialog"
            aria-expanded={drawerOpen}
            data-testid="bottom-nav-more"
            onClick={() => dispatch(setSidebarOpen(true))}
            sx={actionSx}
          />
        </BottomNavigation>
      </Paper>
    </>
  );
}
