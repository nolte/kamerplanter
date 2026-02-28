import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import ListSubheader from '@mui/material/ListSubheader';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
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
import EventNoteIcon from '@mui/icons-material/EventNote';
import WaterIcon from '@mui/icons-material/Water';
import BugReportIcon from '@mui/icons-material/BugReport';
import CoronavirusIcon from '@mui/icons-material/Coronavirus';
import MedicationIcon from '@mui/icons-material/Medication';
import AgricultureIcon from '@mui/icons-material/Agriculture';
import TaskAltIcon from '@mui/icons-material/TaskAlt';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import SettingsIcon from '@mui/icons-material/Settings';
import FileUploadIcon from '@mui/icons-material/FileUpload';
import { sidebarWidth } from '@/theme/tokens';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { navItemConfig, navSectionConfig } from '@/config/fieldConfigs';
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
  const navigate = useNavigate();
  const { isNavVisible } = useExpertiseLevel();

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
      label: t('nav.pflege'),
      path: '/pflege',
      icon: <NotificationsActiveIcon />,
    },
    {
      label: t('nav.calendar'),
      path: '/kalender',
      icon: <CalendarMonthIcon />,
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
        {
          label: t('nav.wateringEvents'),
          path: '/standorte/watering-events',
          icon: <WaterIcon />,
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
          label: t('nav.feedingEvents'),
          path: '/duengung/feeding-events',
          icon: <EventNoteIcon />,
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

  return (
    <Drawer
      variant="persistent"
      open={open}
      data-testid="sidebar"
      sx={{
        width: open ? sidebarWidth : 0,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: sidebarWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Toolbar>
        <Typography variant="h6" noWrap>
          Kamerplanter
        </Typography>
      </Toolbar>
      <Box component="nav" aria-label={t('nav.mainNavigation')} sx={{ overflow: 'auto', flex: 1 }}>
        <List>
          {navItems.map((section) => {
            if ('path' in section && typeof section.path === 'string') {
              if (!isItemVisible(section.path)) return null;
              const { path } = section;
              const isActive = location.pathname === path;
              return (
                <ListItemButton
                  key={path}
                  selected={isActive}
                  onClick={() => navigate(path)}
                  aria-current={isActive ? 'page' : undefined}
                  data-testid={`nav-${path}`}
                >
                  <ListItemIcon>{section.icon}</ListItemIcon>
                  <ListItemText primary={section.label} />
                </ListItemButton>
              );
            }
            const navSection = section as NavSection;
            if (!isSectionVisible(navSection.sectionKey)) return null;
            const visibleItems = navSection.items.filter((item) => isItemVisible(item.path));
            if (visibleItems.length === 0) return null;
            return (
              <Box key={navSection.header}>
                <ListSubheader>{navSection.header}</ListSubheader>
                {visibleItems.map((item) => {
                  const isActive = location.pathname.startsWith(item.path);
                  return (
                    <ListItemButton
                      key={item.path}
                      selected={isActive}
                      onClick={() => navigate(item.path)}
                      aria-current={isActive ? 'page' : undefined}
                      data-testid={`nav-${item.path}`}
                    >
                      <ListItemIcon>{item.icon}</ListItemIcon>
                      <ListItemText primary={item.label} />
                    </ListItemButton>
                  );
                })}
              </Box>
            );
          })}
        </List>
      </Box>
      <List>
        <ListItemButton
          selected={location.pathname === '/settings'}
          onClick={() => navigate('/settings')}
          data-testid="nav-settings"
        >
          <ListItemIcon><SettingsIcon /></ListItemIcon>
          <ListItemText primary={t('nav.settings')} />
        </ListItemButton>
      </List>
    </Drawer>
  );
}
