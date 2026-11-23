import Box from '@mui/material/Box';
import NotificationSettingsTab from '../NotificationSettingsTab';
import SettingsSection from './SettingsSection';
import { findSettingsSection, type SettingsGroupProps } from '@/config/settingsGroups';

/** Group "Notifications" (REQ-030): channels, quiet hours and per-type settings. */
export default function NotificationsSettingsGroup({ sections }: SettingsGroupProps) {
  const notificationsSection = findSettingsSection(sections, 'notifications');

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {notificationsSection && (
        <SettingsSection section={notificationsSection}>
          <NotificationSettingsTab />
        </SettingsSection>
      )}
    </Box>
  );
}
