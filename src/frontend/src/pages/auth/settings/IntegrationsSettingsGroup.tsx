import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import Link from '@mui/material/Link';
import { Link as RouterLink } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { updateUserPreferences } from '@/store/slices/userPreferencesSlice';
import HaPublishSettingsTab from '../HaPublishSettingsTab';
import SettingsSection from './SettingsSection';
import { findSettingsSection, settingsGroupPath, type SettingsGroupProps } from '@/config/settingsGroups';
import { useSettingsGates } from './useSettingsGates';

/**
 * Group "Integrations": the per-user half of the former `ha` tab — the
 * smart-home switch — and the HA publish selection. The installation-wide Home
 * Assistant connection lives in the Installation group (F-11).
 */
export default function IntegrationsSettingsGroup({ sections }: SettingsGroupProps) {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const preferences = useAppSelector((s) => s.userPreferences.preferences);
  const { gates } = useSettingsGates();

  const smartHomeSection = findSettingsSection(sections, 'ha');
  const haPublishSection = findSettingsSection(sections, 'ha-publish');

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {smartHomeSection && (
        <SettingsSection section={smartHomeSection}>
          {/* Smart Home Master Toggle — a per-user preference, visible to everyone. */}
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t('pages.auth.smartHome.title')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.auth.smartHome.description')}
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={preferences?.smart_home_enabled ?? false}
                    onChange={async (e) => {
                      await dispatch(updateUserPreferences({ updates: { smart_home_enabled: e.target.checked } }));
                    }}
                    data-testid="smart-home-master-toggle"
                  />
                }
                label={t('pages.auth.smartHome.toggle')}
              />
              {!preferences?.smart_home_enabled && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  {t('pages.auth.smartHome.disabledInfo')}
                </Alert>
              )}
              {/* The operator's pointer to where the Home Assistant connection and the
                  Pl@ntNet key went: they used to sit right below this switch. */}
              {gates.canManageInstanceSettings && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }} data-testid="integrations-installation-hint">
                  {t('pages.settings.integrationsInstallationHint')}{' '}
                  <Link component={RouterLink} to={settingsGroupPath('installation')}>
                    {t('pages.settings.groups.installation.title')}
                  </Link>
                </Typography>
              )}
            </CardContent>
          </Card>
        </SettingsSection>
      )}

      {haPublishSection && (
        <SettingsSection section={haPublishSection}>
          <HaPublishSettingsTab />
        </SettingsSection>
      )}
    </Box>
  );
}
