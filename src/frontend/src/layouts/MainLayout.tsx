import { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import Avatar from '@mui/material/Avatar';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import Alert from '@mui/material/Alert';
import SettingsIcon from '@mui/icons-material/Settings';
import LogoutIcon from '@mui/icons-material/Logout';
import PersonIcon from '@mui/icons-material/Person';
import Sidebar from './Sidebar';
import Breadcrumbs from '@/components/layout/Breadcrumbs';
import LanguageSelector from '@/components/layout/LanguageSelector';
import NotificationBell from '@/components/layout/NotificationBell';
import TenantSwitcher from '@/components/layout/TenantSwitcher';
import ThemeToggle from '@/components/layout/ThemeToggle';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { toggleSidebar } from '@/store/slices/uiSlice';
import { logoutUser } from '@/store/slices/authSlice';
import { isLightMode } from '@/config/mode';

function isPrivateNetwork(): boolean {
  const { hostname } = window.location;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return true;
  if (hostname.startsWith('10.')) return true;
  if (hostname.startsWith('192.168.')) return true;
  if (/^172\.(1[6-9]|2\d|3[01])\./.test(hostname)) return true;
  return false;
}

export default function MainLayout() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const sidebarOpen = useAppSelector((s) => s.ui.sidebarOpen);
  const user = useAppSelector((s) => s.auth.user);

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [lightModeWarningDismissed, setLightModeWarningDismissed] = useState(false);

  const showLightModeWarning = isLightMode && !isPrivateNetwork() && !lightModeWarningDismissed;

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleSettings = () => {
    handleMenuClose();
    navigate('/settings');
  };

  const handleLogout = async () => {
    handleMenuClose();
    await dispatch(logoutUser());
    navigate('/login');
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Box
        component="a"
        href="#main-content"
        sx={{
          position: 'absolute',
          left: '-9999px',
          top: 'auto',
          width: '1px',
          height: '1px',
          overflow: 'hidden',
          '&:focus': {
            position: 'fixed',
            top: 8,
            left: 8,
            width: 'auto',
            height: 'auto',
            overflow: 'visible',
            zIndex: (theme) => theme.zIndex.tooltip + 1,
            bgcolor: 'background.paper',
            color: 'text.primary',
            px: 2,
            py: 1,
            borderRadius: 1,
            boxShadow: 3,
          },
        }}
      >
        {t('common.skipToContent')}
      </Box>

      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => dispatch(toggleSidebar())}
            sx={{ mr: 2 }}
            aria-label={t('common.toggleSidebar')}
          >
            <MenuIcon />
          </IconButton>
          <Box sx={{ flexGrow: 1 }} />
          {!isLightMode && <TenantSwitcher />}
          <LanguageSelector />
          <ThemeToggle />
          <NotificationBell />

          {/* User menu — full mode: avatar + dropdown; light mode: settings icon only */}
          {isLightMode ? (
            <IconButton
              color="inherit"
              onClick={() => navigate('/settings')}
              sx={{ ml: 1 }}
              aria-label={t('pages.auth.accountSettings')}
            >
              <SettingsIcon />
            </IconButton>
          ) : (
            <>
              <IconButton
                onClick={handleMenuOpen}
                sx={{ ml: 1 }}
                aria-label={t('pages.auth.accountMenu')}
              >
                <Avatar
                  sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}
                  src={user?.avatar_url || undefined}
                >
                  {user?.display_name?.[0]?.toUpperCase() || <PersonIcon />}
                </Avatar>
              </IconButton>
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
                transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
              >
                <Box sx={{ px: 2, py: 1 }}>
                  <Typography variant="subtitle2">{user?.display_name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {user?.email}
                  </Typography>
                </Box>
                <Divider />
                <MenuItem onClick={handleSettings}>
                  <ListItemIcon><SettingsIcon fontSize="small" /></ListItemIcon>
                  {t('pages.auth.accountSettings')}
                </MenuItem>
                <MenuItem onClick={handleLogout}>
                  <ListItemIcon><LogoutIcon fontSize="small" /></ListItemIcon>
                  {t('pages.auth.logout')}
                </MenuItem>
              </Menu>
            </>
          )}
        </Toolbar>
      </AppBar>

      <Sidebar open={sidebarOpen} />

      <Box
        component="main"
        id="main-content"
        tabIndex={-1}
        sx={{
          flexGrow: 1,
          transition: 'margin 225ms cubic-bezier(0, 0, 0.2, 1)',
          width: '100%',
          px: 2,
          py: 1,
          '&:focus': { outline: 'none' },
        }}
      >
        <Toolbar />
        {showLightModeWarning && (
          <Alert
            severity="warning"
            onClose={() => setLightModeWarningDismissed(true)}
            sx={{ mb: 2 }}
          >
            {t('common.lightModeWarning')}
          </Alert>
        )}
        <Breadcrumbs />
        <Outlet />
      </Box>
    </Box>
  );
}
