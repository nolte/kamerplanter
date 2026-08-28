import { useLocation, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import ListSubheader from '@mui/material/ListSubheader';
import Toolbar from '@mui/material/Toolbar';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DashboardIcon from '@mui/icons-material/Dashboard';
import ParkIcon from '@mui/icons-material/Park';
import ScienceIcon from '@mui/icons-material/Science';
import Diversity3Icon from '@mui/icons-material/Diversity3';
import LoopIcon from '@mui/icons-material/Loop';
import PlaceIcon from '@mui/icons-material/Place';
import LayersIcon from '@mui/icons-material/Layers';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import CalculateIcon from '@mui/icons-material/Calculate';
import PlaylistAddCheckIcon from '@mui/icons-material/PlaylistAddCheck';
import EventRepeatIcon from '@mui/icons-material/EventRepeat';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import OpacityIcon from '@mui/icons-material/Opacity';
import ListAltIcon from '@mui/icons-material/ListAlt';
import BiotechIcon from '@mui/icons-material/Biotech';
import HistoryIcon from '@mui/icons-material/History';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import BugReportIcon from '@mui/icons-material/BugReport';
import PestControlIcon from '@mui/icons-material/PestControl';
import CoronavirusIcon from '@mui/icons-material/Coronavirus';
import MedicationIcon from '@mui/icons-material/Medication';
import AgricultureIcon from '@mui/icons-material/Agriculture';
import Inventory2Icon from '@mui/icons-material/Inventory2';
import TaskAltIcon from '@mui/icons-material/TaskAlt';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import TimelineIcon from '@mui/icons-material/Timeline';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import BookIcon from '@mui/icons-material/Book';
import SettingsIcon from '@mui/icons-material/Settings';
import TuneIcon from '@mui/icons-material/Tune';

import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import ContentCutIcon from '@mui/icons-material/ContentCut';
import FileUploadIcon from '@mui/icons-material/FileUpload';
import PhotoCameraIcon from '@mui/icons-material/PhotoCamera';
import AcUnitIcon from '@mui/icons-material/AcUnit';
import SetMealIcon from '@mui/icons-material/SetMeal';
import { sidebarWidth } from '@/theme/tokens';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { useModuleVisibility } from '@/hooks/useModuleVisibility';
import { navItemConfig, navSectionConfig } from '@/config/fieldConfigs';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { setSidebarOpen } from '@/store/slices/uiSlice';
import type { ExperienceLevel } from '@/api/types';

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
}

interface NavSection {
  header: string;
  sectionKey: string;
  items: NavItem[];
}

type NavEntry = NavItem | NavSection;

interface SidebarProps {
  open: boolean;
}

export default function Sidebar({ open }: SidebarProps) {
  const { t } = useTranslation();
  const location = useLocation();
  const { isNavVisible, level } = useExpertiseLevel();
  const { findModuleByPath, overrides, isSmartHomeEnabled } = useModuleVisibility();
  // Issue #685 — cluster-wide AI feature flag. `null` = unknown (probe pending):
  // keep the entry visible until we positively learn AI is off.
  const aiAvailable = useAppSelector((s) => s.aiStatus.available);
  const dispatch = useAppDispatch();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const handleClose = () => {
    dispatch(setSidebarOpen(false));
  };

  const isItemVisible = (path: string): boolean => {
    // REQ-042: personal module overrides take precedence over the level filter.
    const owner = findModuleByPath(path);
    // Issue #685: the KI-Assistent entry reflects the server-side AI feature flag.
    // Hide it only once the probe positively reports the feature is off, so a
    // pending/failed probe (available === null) never hides a working feature.
    // Glossar keeps its own module (decoupled from the AI flag, issue #684).
    if (owner?.key === 'ai_assistant' && aiAvailable === false) return false;
    // Issue #587: the smart-home gate wins over override + level so sensor/actuator
    // nav entries (e.g. Umgebungssteuerung) stay hidden until the user opts in.
    if (owner?.requiresSmartHome && !isSmartHomeEnabled) return false;
    if (owner && !owner.core) {
      const ov = overrides[owner.key];
      if (ov === 'disabled') return false;
      if (ov === 'enabled') return true;
    }
    const minLevel = navItemConfig[path];
    if (!minLevel) return true;
    return isNavVisible(minLevel);
  };

  const isSectionVisible = (sectionKey: string): boolean => {
    const minLevel = navSectionConfig[sectionKey];
    if (!minLevel) return true;
    return isNavVisible(minLevel as ExperienceLevel);
  };

  const navItems: NavEntry[] = [
    { label: t('nav.dashboard'), path: '/dashboard', icon: <DashboardIcon /> },
    {
      label: t('nav.calendar'),
      path: '/kalender',
      icon: <CalendarMonthIcon />,
    },
    {
      label: t('nav.wateringLog'),
      path: '/giessprotokoll',
      icon: <HistoryIcon />,
    },
    {
      // REQ-051 §6.2 — the tenant-wide diary overview. A top-level beginner
      // entry per REQ-021 §3.3, owned by the `diary` module (REQ-042 §1.3) and
      // therefore hideable like its siblings (AK-31).
      label: t('nav.diary'),
      path: '/tagebuch',
      icon: <BookIcon />,
    },
    {
      label: t('nav.kiAssistent'),
      path: '/ki-assistent',
      icon: <AutoAwesomeIcon />,
    },
    {
      // REQ-035 — light-mode-capable terminology glossary, ungated like
      // ki-assistent (no navItemConfig entry needed).
      label: t('nav.glossary'),
      path: '/glossar',
      icon: <MenuBookIcon />,
    },
    {
      header: t('nav.pflanzen'),
      sectionKey: 'pflanzen',
      items: [
        {
          label: t('nav.plantInstances'),
          path: '/pflanzen/plant-instances',
          icon: <LocalFloristIcon />,
        },
        {
          label: t('nav.plantIdentification'),
          path: '/pflanzen/identifikation',
          icon: <PhotoCameraIcon />,
        },
        {
          label: t('nav.calculations'),
          path: '/pflanzen/calculations',
          icon: <CalculateIcon />,
        },
        {
          label: t('nav.overwintering'),
          path: '/ueberwinterung/profile',
          icon: <AcUnitIcon />,
        },
        {
          label: t('nav.propagation'),
          path: '/vermehrung',
          icon: <AccountTreeIcon />,
        },
      ],
    },
    {
      header: t('nav.aufgaben'),
      sectionKey: 'aufgaben',
      items: [
        {
          label: t('nav.taskQueue'),
          path: '/aufgaben/queue',
          icon: <TaskAltIcon />,
        },
        {
          label: t('nav.workflows'),
          path: '/aufgaben/workflows',
          icon: <AccountTreeIcon />,
        },
      ],
    },
    {
      header: t('nav.stammdaten'),
      sectionKey: 'stammdaten',
      items: [
        {
          label: t('nav.botanicalFamilies'),
          path: '/stammdaten/botanical-families',
          icon: <ParkIcon />,
        },
        {
          label: t('nav.species'),
          path: '/stammdaten/species',
          icon: <ScienceIcon />,
        },
        {
          label: t('nav.companionPlanting'),
          path: '/stammdaten/companion-planting',
          icon: <Diversity3Icon />,
        },
        {
          label: t('nav.cropRotation'),
          path: '/stammdaten/crop-rotation',
          icon: <LoopIcon />,
        },
        {
          label: t('nav.activities'),
          path: '/stammdaten/activities',
          icon: <ContentCutIcon />,
        },
        {
          label: t('nav.import'),
          path: '/stammdaten/import',
          icon: <FileUploadIcon />,
        },
      ],
    },
    {
      header: t('nav.standorte'),
      sectionKey: 'standorte',
      items: [
        { label: t('nav.sites'), path: '/standorte/sites', icon: <PlaceIcon /> },
        {
          label: t('nav.substrates'),
          path: '/standorte/substrates',
          icon: <LayersIcon />,
        },
        {
          label: t('nav.tanks'),
          path: '/standorte/tanks',
          icon: <WaterDropIcon />,
        },
      ],
    },
    {
      header: t('nav.aquaponik'),
      sectionKey: 'aquaponik',
      items: [
        {
          label: t('nav.aquaponicSystems'),
          path: '/aquaponik',
          icon: <SetMealIcon />,
        },
      ],
    },
    {
      header: t('nav.umgebungssteuerung'),
      sectionKey: 'umgebungssteuerung',
      items: [
        {
          label: t('nav.environmentControl'),
          path: '/umgebungssteuerung',
          icon: <TuneIcon />,
        },
      ],
    },
    {
      header: t('nav.inventar'),
      sectionKey: 'inventree',
      items: [
        {
          label: t('nav.equipment'),
          path: '/inventree',
          icon: <Inventory2Icon />,
        },
      ],
    },
    {
      header: t('nav.duengung'),
      sectionKey: 'duengung',
      items: [
        {
          label: t('nav.fertilizers'),
          path: '/duengung/fertilizers',
          icon: <OpacityIcon />,
        },
        {
          label: t('nav.nutrientPlans'),
          path: '/duengung/plans',
          icon: <ListAltIcon />,
        },
        {
          label: t('nav.nutrientCalculations'),
          path: '/duengung/calculations',
          icon: <BiotechIcon />,
        },
      ],
    },
    {
      header: t('nav.pflanzenschutz'),
      sectionKey: 'pflanzenschutz',
      items: [
        {
          label: t('nav.pestDetection'),
          path: '/pflanzenschutz/erkennung',
          icon: <PestControlIcon />,
        },
        {
          label: t('nav.pests'),
          path: '/pflanzenschutz/pests',
          icon: <BugReportIcon />,
        },
        {
          label: t('nav.diseases'),
          path: '/pflanzenschutz/diseases',
          icon: <CoronavirusIcon />,
        },
        {
          label: t('nav.treatments'),
          path: '/pflanzenschutz/treatments',
          icon: <MedicationIcon />,
        },
      ],
    },
    {
      header: t('nav.ernte'),
      sectionKey: 'ernte',
      items: [
        {
          label: t('nav.harvestBatches'),
          path: '/ernte/batches',
          icon: <AgricultureIcon />,
        },
        {
          label: t('nav.postHarvest'),
          path: '/ernte/nachernte',
          icon: <Inventory2Icon />,
        },
      ],
    },
    {
      header: t('nav.phasen'),
      sectionKey: 'phasen',
      items: [
        {
          label: t('pages.phaseSequences.phaseDefinitions'),
          path: '/phasen/definitionen',
          icon: <TimelineIcon />,
        },
        {
          label: t('pages.phaseSequences.phaseSequences'),
          path: '/phasen/ablaeufe',
          icon: <AccountTreeIcon />,
        },
      ],
    },
    {
      header: t('nav.durchlaeufe'),
      sectionKey: 'durchlaeufe',
      items: [
        {
          label: t('nav.plantingRuns'),
          path: '/durchlaeufe/planting-runs',
          icon: <PlaylistAddCheckIcon />,
        },
        {
          label: t('nav.successionPlans'),
          path: '/durchlaeufe/succession-plans',
          icon: <EventRepeatIcon />,
        },
      ],
    },
  ];

  // Determine whether any top-level (non-section) items are visible
  const topLevelItems = navItems.filter(
    (item): item is NavItem =>
      'path' in item && typeof (item as NavItem).path === 'string',
  );
  const visibleTopLevelItems = topLevelItems.filter((item) => isItemVisible(item.path));
  const hasSections = navItems.some((item) => !('path' in item));

  return (
    <Drawer
      variant={isMobile ? 'temporary' : 'persistent'}
      open={open}
      onClose={handleClose}
      data-testid="sidebar"
      ModalProps={{ keepMounted: true }}
      sx={{
        width: !isMobile && open ? sidebarWidth : 0,
        flexShrink: 0,
        // The paper slides (MUI animates the persistent variant), but the docked
        // placeholder that reserves its space used to jump between 240px and 0
        // in a single frame — so the whole content region snapped sideways while
        // the navigation was still gliding. Animating the placeholder with the
        // theme's own timings puts the two halves back in sync. `easing.sharp`
        // and the standard enter/leave durations are what MUI's own Drawer uses.
        transition: theme.transitions.create('width', {
          easing: theme.transitions.easing.sharp,
          duration: open
            ? theme.transitions.duration.enteringScreen
            : theme.transitions.duration.leavingScreen,
        }),
        '& .MuiDrawer-paper': {
          width: sidebarWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Toolbar>
        <Typography variant="h6" noWrap component="span">
          Kamerplanter
        </Typography>
      </Toolbar>
      <Divider />
      <Box component="nav" aria-label={t('nav.mainNavigation')} sx={{ overflow: 'auto', flex: 1 }}>
        <List disablePadding>
          {navItems.map((section, sectionIndex) => {
            if ('path' in section && typeof section.path === 'string') {
              if (!isItemVisible(section.path)) return null;
              const { path } = section;
              const isActive = location.pathname === path || location.pathname.startsWith(path + '/');
              return (
                <ListItemButton
                  key={path}
                  component={Link}
                  to={path}
                  selected={isActive}
                  aria-current={isActive ? 'page' : undefined}
                  data-testid={`nav-${path}`}
                  onClick={isMobile ? handleClose : undefined}
                  sx={{
                    borderRadius: 1,
                    mx: 0.5,
                    my: 0.25,
                    '&.Mui-selected': {
                      fontWeight: 600,
                    },
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 40 }}>{section.icon}</ListItemIcon>
                  <ListItemText
                    primary={section.label} slotProps={{ primary: { sx: { fontSize: '0.875rem' } } }} />
                </ListItemButton>
              );
            }
            const navSection = section as NavSection;
            const visibleItems = navSection.items.filter((item) => isItemVisible(item.path));
            if (visibleItems.length === 0) return null;
            // REQ-042: a section whose experience level is above the user's must
            // still appear when one of its modules was explicitly enabled via a
            // personal override — otherwise the enabled menu item would be
            // unreachable. The section-level gate is override-blind, so check the
            // overrides here (isItemVisible already honoured them per item).
            const revealedByOverride = visibleItems.some((item) => {
              const owner = findModuleByPath(item.path);
              return owner != null && !owner.core && overrides[owner.key] === 'enabled';
            });
            if (!isSectionVisible(navSection.sectionKey) && !revealedByOverride) return null;
            // Add a divider before the first section if there are top-level items above
            const isFirstSection =
              hasSections &&
              visibleTopLevelItems.length > 0 &&
              navItems.findIndex((item) => !('path' in item)) === sectionIndex;
            return (
              <Box key={navSection.header}>
                {isFirstSection && <Divider sx={{ mt: 0.5 }} />}
                <ListSubheader
                  sx={{
                    lineHeight: '32px',
                    fontSize: '0.7rem',
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    // `text.secondary`, not `text.disabled`: this label is quiet,
                    // not inactive. MUI's `text.disabled` is rgba(0,0,0,0.38),
                    // which composites to #9e9e9e on the drawer's white paper —
                    // 2.67:1 at 11.2px, below WCAG AA's 4.5:1 (UI-NFR-002). The
                    // 1.4.3 exemption covers *disabled controls*, and a section
                    // header is neither. `text.secondary` composites to #666666
                    // (5.74:1) and is #000000 in the high-contrast palette.
                    color: 'text.secondary',
                    mt: 0.5,
                  }}
                >
                  {navSection.header}
                </ListSubheader>
                {visibleItems.map((item) => {
                  const isActive = location.pathname.startsWith(item.path);
                  return (
                    <ListItemButton
                      key={item.path}
                      component={Link}
                      to={item.path}
                      selected={isActive}
                      aria-current={isActive ? 'page' : undefined}
                      data-testid={`nav-${item.path}`}
                      onClick={isMobile ? handleClose : undefined}
                      sx={{
                        borderRadius: 1,
                        mx: 0.5,
                        my: 0.125,
                        '&.Mui-selected': {
                          fontWeight: 600,
                        },
                      }}
                    >
                      <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
                      <ListItemText
                        primary={item.label} slotProps={{ primary: { sx: { fontSize: '0.875rem' } } }} />
                    </ListItemButton>
                  );
                })}
              </Box>
            );
          })}
        </List>
        {level === 'beginner' && (
          <Box sx={{ px: 2, py: 1.5, mt: 'auto' }}>
            <Typography
              variant="caption"
              color="text.secondary"
              component={Link}
              to="/settings"
              sx={{
                display: 'block',
                textDecoration: 'none',
                '&:hover': { textDecoration: 'underline' },
              }}
              onClick={isMobile ? handleClose : undefined}
            >
              {t('nav.beginnerHint')}
            </Typography>
          </Box>
        )}
      </Box>
      <Divider />
      <List disablePadding sx={{ pb: 1 }}>
        <ListItemButton
          component={Link}
          to="/onboarding"
          selected={location.pathname === '/onboarding'}
          aria-current={location.pathname === '/onboarding' ? 'page' : undefined}
          data-testid="nav-onboarding"
          onClick={isMobile ? handleClose : undefined}
          sx={{ borderRadius: 1, mx: 0.5, my: 0.25 }}
        >
          <ListItemIcon sx={{ minWidth: 40 }}><RocketLaunchIcon /></ListItemIcon>
          <ListItemText
            primary={t('nav.onboarding')} slotProps={{ primary: { sx: { fontSize: '0.875rem' } } }} />
        </ListItemButton>
        <ListItemButton
          component={Link}
          to="/settings"
          selected={location.pathname === '/settings'}
          aria-current={location.pathname === '/settings' ? 'page' : undefined}
          data-testid="nav-settings"
          onClick={isMobile ? handleClose : undefined}
          sx={{ borderRadius: 1, mx: 0.5, my: 0.25 }}
        >
          <ListItemIcon sx={{ minWidth: 40 }}><SettingsIcon /></ListItemIcon>
          <ListItemText
            primary={t('nav.settings')} slotProps={{ primary: { sx: { fontSize: '0.875rem' } } }} />
        </ListItemButton>
      </List>
    </Drawer>
  );
}
