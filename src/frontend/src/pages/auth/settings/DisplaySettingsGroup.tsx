import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import InputAdornment from '@mui/material/InputAdornment';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import EmojiNatureIcon from '@mui/icons-material/EmojiNature';
import SchoolIcon from '@mui/icons-material/School';
import ScienceIcon from '@mui/icons-material/Science';
import { useNotification } from '@/hooks/useNotification';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { updateUserPreferences } from '@/store/slices/userPreferencesSlice';
import { resetOnboarding } from '@/store/slices/onboardingSlice';
import { parseApiError } from '@/api/errors';
import type { ExperienceLevel } from '@/api/types';
import KioskSettingsTab from '../KioskSettingsTab';
import ModulesSettingsTab from '../ModulesSettingsTab';
import DashboardSettingsTab from '../DashboardSettingsTab';
import SettingsSection from './SettingsSection';
import { GRID_3COL } from './settingsLayout';
import { findSettingsSection, type SettingsGroupProps } from '@/config/settingsGroups';

const EXPERIENCE_LEVELS: { level: ExperienceLevel; icon: React.ReactNode }[] = [
  { level: 'beginner', icon: <EmojiNatureIcon /> },
  { level: 'intermediate', icon: <SchoolIcon /> },
  { level: 'expert', icon: <ScienceIcon /> },
];

/** Group "Display & behaviour": experience level, kiosk mode, modules and the dashboard. */
export default function DisplaySettingsGroup({ sections }: SettingsGroupProps) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const notification = useNotification();
  const preferences = useAppSelector((s) => s.userPreferences.preferences);

  const experienceSection = findSettingsSection(sections, 'experience');
  const kioskSection = findSettingsSection(sections, 'kiosk');
  const modulesSection = findSettingsSection(sections, 'modules');
  const dashboardSection = findSettingsSection(sections, 'dashboard');

  const handleExperienceLevelChange = async (_: React.MouseEvent<HTMLElement>, newLevel: ExperienceLevel | null) => {
    if (!newLevel) return;
    const currentLevel = preferences?.experience_level ?? 'beginner';
    const order: Record<ExperienceLevel, number> = { beginner: 0, intermediate: 1, expert: 2 };
    if (order[newLevel] < order[currentLevel]) {
      if (!window.confirm(t('pages.auth.experienceLevelDowngradeWarning'))) return;
    }
    try {
      // Await persistence before confirming: an optimistic snackbar lets the
      // user (and E2E waits) navigate away while the PATCH is still in flight,
      // silently losing the level change on full reload.
      await dispatch(updateUserPreferences({ updates: { experience_level: newLevel } })).unwrap();
      notification.success(t('common.saved'));
    } catch (err) {
      notification.error(parseApiError(err, t));
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {experienceSection && (
        <SettingsSection section={experienceSection}>
          <Box sx={GRID_3COL}>
            {/* Experience Level Selector — spans full on small, 2 cols on large */}
            <Card variant="outlined" sx={{ gridColumn: { xs: '1 / -1', lg: '1 / 3' } }}>
              <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
                <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                  {t('pages.auth.experienceLevelTitle')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {t('pages.auth.experienceLevelSubtitle')}
                </Typography>

                <ToggleButtonGroup
                  value={preferences?.experience_level ?? 'beginner'}
                  exclusive
                  onChange={handleExperienceLevelChange}
                  fullWidth
                  orientation={fullScreen ? 'vertical' : 'horizontal'}
                  aria-label={t('pages.auth.experienceLevelTitle')}
                >
                  {EXPERIENCE_LEVELS.map(({ level, icon }) => (
                    <ToggleButton
                      key={level}
                      value={level}
                      sx={{ flexDirection: 'column', py: 2 }}
                      data-testid={`experience-toggle-${level}`}
                    >
                      {icon}
                      <Typography variant="subtitle2" sx={{ mt: 0.5 }}>
                        {t(`enums.experienceLevel.${level}`)}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {t(`pages.auth.experienceLevel.${level}Description`)}
                      </Typography>
                    </ToggleButton>
                  ))}
                </ToggleButtonGroup>
              </CardContent>
            </Card>

            {/* Watering Can Size */}
            <Card variant="outlined">
              <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2, display: 'flex', flexDirection: 'column', height: '100%' }}>
                <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                  {t('pages.auth.wateringCanSize')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {t('pages.auth.wateringCanSizeHelper')}
                </Typography>
                <TextField
                  type="number"
                  label={t('pages.auth.wateringCanSizeLiters')}
                  value={preferences?.watering_can_liters ?? 10}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value);
                    if (!isNaN(val) && val > 0) {
                      dispatch(updateUserPreferences({ updates: { watering_can_liters: val } }));
                      notification.success(t('common.saved'));
                    }
                  }}
                  slotProps={{
                    htmlInput: { min: 0.5, max: 100, step: 0.5, inputMode: 'decimal' },
                    input: { endAdornment: <InputAdornment position="end">L</InputAdornment> },
                  }}
                  sx={{ maxWidth: 220, mt: 'auto' }}
                  data-testid="watering-can-size-field"
                />
              </CardContent>
            </Card>

            {/* Re-run Onboarding */}
            <Card variant="outlined">
              <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2, display: 'flex', flexDirection: 'column', height: '100%' }}>
                <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                  {t('pages.auth.rerunOnboarding')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {t('pages.auth.rerunOnboardingDescription')}
                </Typography>
                <Button
                  variant="outlined"
                  onClick={async () => {
                    await dispatch(resetOnboarding());
                    navigate('/onboarding');
                  }}
                  sx={{ alignSelf: 'flex-start', mt: 'auto' }}
                  data-testid="rerun-onboarding-btn"
                >
                  {t('pages.auth.rerunOnboardingButton')}
                </Button>
              </CardContent>
            </Card>
          </Box>
        </SettingsSection>
      )}

      {/* UI-NFR-019 */}
      {kioskSection && (
        <SettingsSection section={kioskSection}>
          <KioskSettingsTab />
        </SettingsSection>
      )}

      {/* REQ-042 */}
      {modulesSection && (
        <SettingsSection section={modulesSection}>
          <ModulesSettingsTab />
        </SettingsSection>
      )}

      {/* REQ-045 */}
      {dashboardSection && (
        <SettingsSection section={dashboardSection}>
          <DashboardSettingsTab />
        </SettingsSection>
      )}
    </Box>
  );
}
