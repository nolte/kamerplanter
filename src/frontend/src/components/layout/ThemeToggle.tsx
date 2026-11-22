import { useTranslation } from 'react-i18next';
import IconButton from '@mui/material/IconButton';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import { useThemeMode } from '@/theme';

export default function ThemeToggle() {
  const { t } = useTranslation();
  const { mode, toggleTheme } = useThemeMode();

  return (
    <IconButton
      color="inherit"
      onClick={toggleTheme}
      aria-label={t(mode === 'dark' ? 'common.switchToLightTheme' : 'common.switchToDarkTheme')}
    >
      {mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
    </IconButton>
  );
}
