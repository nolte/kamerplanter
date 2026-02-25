import IconButton from '@mui/material/IconButton';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import { useThemeMode } from '@/theme';

export default function ThemeToggle() {
  const { mode, toggleTheme } = useThemeMode();

  return (
    <IconButton color="inherit" onClick={toggleTheme} aria-label="toggle theme">
      {mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
    </IconButton>
  );
}
