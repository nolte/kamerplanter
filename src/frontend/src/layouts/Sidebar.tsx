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
import { sidebarWidth } from '@/theme/tokens';

interface SidebarProps {
  open: boolean;
}

export default function Sidebar({ open }: SidebarProps) {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();

  const navItems = [
    { label: t('nav.dashboard'), path: '/dashboard', icon: <DashboardIcon /> },
    {
      header: t('nav.stammdaten'),
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
      ],
    },
    {
      header: t('nav.standorte'),
      items: [
        { label: t('nav.sites'), path: '/standorte/sites', icon: <PlaceIcon /> },
        {
          label: t('nav.substrates'),
          path: '/standorte/substrates',
          icon: <LayersIcon />,
        },
      ],
    },
    {
      header: t('nav.pflanzen'),
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
      header: t('nav.durchlaeufe'),
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
      <Box component="nav" aria-label={t('nav.mainNavigation')} sx={{ overflow: 'auto' }}>
        <List>
          {navItems.map((section) => {
            if ('path' in section && typeof section.path === 'string') {
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
            return (
              <Box key={section.header}>
                <ListSubheader>{section.header}</ListSubheader>
                {section.items.map((item) => {
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
    </Drawer>
  );
}
