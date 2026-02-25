import { Outlet } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import IconButton from '@mui/material/IconButton';
import MenuIcon from '@mui/icons-material/Menu';
import Sidebar from './Sidebar';
import Breadcrumbs from '@/components/layout/Breadcrumbs';
import LanguageSelector from '@/components/layout/LanguageSelector';
import ThemeToggle from '@/components/layout/ThemeToggle';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { toggleSidebar } from '@/store/slices/uiSlice';

export default function MainLayout() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const sidebarOpen = useAppSelector((s) => s.ui.sidebarOpen);

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
          <LanguageSelector />
          <ThemeToggle />
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
        <Breadcrumbs />
        <Outlet />
      </Box>
    </Box>
  );
}
