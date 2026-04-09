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
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import OpacityIcon from '@mui/icons-material/Opacity';
import ListAltIcon from '@mui/icons-material/ListAlt';
import BiotechIcon from '@mui/icons-material/Biotech';
import HistoryIcon from '@mui/icons-material/History';
import BugReportIcon from '@mui/icons-material/BugReport';
import CoronavirusIcon from '@mui/icons-material/Coronavirus';
import MedicationIcon from '@mui/icons-material/Medication';
import AgricultureIcon from '@mui/icons-material/Agriculture';
import TaskAltIcon from '@mui/icons-material/TaskAlt';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import SettingsIcon from '@mui/icons-material/Settings';

import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import ContentCutIcon from '@mui/icons-material/ContentCut';
import FileUploadIcon from '@mui/icons-material/FileUpload';
import { sidebarWidth } from '@/theme/tokens';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { navItemConfig, navSectionConfig } from '@/config/fieldConfigs';
import { useAppDispatch } from '@/store/hooks';
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
  const { isNavVisible } = useExpertiseLevel();
  const dispatch = useAppDispatch();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const handleClose = () => {
    dispatch(setSidebarOpen(false));
  };

  const isItemVisible = (path: string): boolean => {
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
      header: t('nav.pflanzen'),
      sectionKey: 'pflanzen',
      items: [
        {
          label: t('nav.plantInstances'),
          path: '/pflanzen/plant-instances',
          icon: <LocalFloristIcon />,
        },
        {
          label: t('nav.calculations'),
          path: '/pflanzen/calculations',
          icon: <CalculateIcon />,
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
            if (!isSectionVisible(navSection.sectionKey)) return null;
            const visibleItems = navSection.items.filter((item) => isItemVisible(item.path));
            if (visibleItems.length === 0) return null;
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
                    color: 'text.disabled',
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
