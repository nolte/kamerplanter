import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import InputLabel from '@mui/material/InputLabel';
import FormControl from '@mui/material/FormControl';
import { useNotification } from '@/hooks/useNotification';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchProfile } from '@/store/slices/authSlice';
import { updateProfile, deleteAccount } from '@/api/endpoints/auth';
import { parseApiError } from '@/api/errors';
import ErasurePreviewNotice from '@/components/privacy/ErasurePreviewNotice';
import { useErasurePreview } from '@/hooks/useErasurePreview';
import StepUpConfirmDialog from '@/components/common/StepUpConfirmDialog';
import type { StepUpConfirmation } from '@/components/common/StepUpConfirmDialog';
import { useStepUpResume } from '@/hooks/useStepUpReauth';
import { toStepUpBody } from '@/utils/stepUp';
import { isLightMode } from '@/config/mode';
import { clearOfflineData } from '@/pwa/offlineData';
import EmailChangeCard from '../EmailChangeCard';
import SettingsSection from './SettingsSection';
import { GRID_2COL } from './settingsLayout';
import { findSettingsSection, type SettingsGroupProps } from '@/config/settingsGroups';

/** Group "Profile & account": the profile and region form, the e-mail change and closing the account. */
export default function AccountSettingsGroup({ sections }: SettingsGroupProps) {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const notification = useNotification();
  const user = useAppSelector((s) => s.auth.user);

  const profileSection = findSettingsSection(sections, 'profile');
  const accountSection = findSettingsSection(sections, 'account');

  const [displayName, setDisplayName] = useState('');
  const [locale, setLocale] = useState('de');
  const [timezone, setTimezone] = useState('Europe/Berlin');
  const [error, setError] = useState('');
  // #1815 — back from the fresh sign-in at the identity provider: reopen the
  // account-deletion dialog it was started from (it then sends the token).
  const resumeDeleteAccount = useStepUpResume('delete-account');
  const [deleteAccountOpen, setDeleteAccountOpen] = useState(resumeDeleteAccount);
  // AK-FK-06 — the personal tenants this deletion takes along, read when the dialog opens.
  const erasurePreview = useErasurePreview(deleteAccountOpen);

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name);
      setLocale(user.locale);
      setTimezone(user.timezone || 'Europe/Berlin');
    }
  }, [user]);

  const handleProfileSave = async () => {
    setError('');
    try {
      await updateProfile({ display_name: displayName, locale, timezone });
      dispatch(fetchProfile());
      notification.success(t('common.saved'));
    } catch (err) {
      setError(parseApiError(err, t));
    }
  };

  // Closing the own account is a step-up (#1813): the own e-mail typed back and,
  // for an account with a local password, the current password. A rejection
  // propagates to the dialog, which shows it and stays open.
  const handleDeleteAccount = async ({ echo, ...credentials }: StepUpConfirmation) => {
    await deleteAccount({ confirm_email: echo, ...toStepUpBody(credentials) });
    setDeleteAccountOpen(false);
    // The closed account's offline data goes before the page does (REQ-053 WP 9.2, #2789 review S3):
    // the reload's refresh fails, and nothing else would clear the plan cache or the API caches. The account's
    // unsent offline entries go too (REQ-053 WP 9.4); other users' entries on the device stay.
    await clearOfflineData({ discardWriteQueueOf: user?.key ?? null });
    // Full reload, not a router navigation: the session is gone server-side and
    // every in-memory slice belongs to the closed account.
    window.location.href = '/login';
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {error && <Alert severity="error">{error}</Alert>}

      {profileSection && (
        <SettingsSection section={profileSection}>
          <Box sx={GRID_2COL}>
            {/* Personal Data */}
            <Card variant="outlined">
              <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
                <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                  {t('pages.auth.profileSection')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {t('pages.auth.profileSectionDesc')}
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <TextField
                    label={t('pages.auth.displayName')}
                    fullWidth
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    data-testid="profile-display-name"
                  />
                  <TextField
                    label={t('pages.auth.email')}
                    fullWidth
                    value={user?.email || ''}
                    disabled
                    helperText={isLightMode ? t('pages.auth.emailReadOnly') : t('pages.emailChange.emailFieldHint')}
                    data-testid="profile-email"
                  />
                  <Button variant="contained" onClick={handleProfileSave} sx={{ alignSelf: 'flex-start' }} data-testid="profile-save-btn">
                    {t('common.save')}
                  </Button>
                </Box>
              </CardContent>
            </Card>

            {/* Language & Region */}
            <Card variant="outlined">
              <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
                <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                  {t('pages.auth.regionSection')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {t('pages.auth.regionSectionDesc')}
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <FormControl fullWidth>
                    <InputLabel id="locale-label">{t('pages.auth.locale')}</InputLabel>
                    <Select
                      labelId="locale-label"
                      value={locale}
                      label={t('pages.auth.locale')}
                      onChange={(e) => setLocale(e.target.value)}
                      data-testid="profile-locale"
                    >
                      <MenuItem value="de">Deutsch</MenuItem>
                      <MenuItem value="en">English</MenuItem>
                    </Select>
                  </FormControl>
                  <TextField
                    label={t('pages.auth.timezone')}
                    fullWidth
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    helperText={t('pages.auth.timezoneHelper')}
                    data-testid="profile-timezone"
                  />
                </Box>
              </CardContent>
            </Card>

            {/* E-mail change (REQ-025 Art. 16, #1848) — accounts exist in full mode only. */}
            {!isLightMode && <EmailChangeCard currentEmail={user?.email ?? ''} />}
          </Box>
        </SettingsSection>
      )}

      {accountSection && (
        <SettingsSection section={accountSection}>
          <Box sx={{ maxWidth: 600 }}>
            <Card>
              <CardContent>
                <Alert severity="warning" sx={{ mb: 2 }}>
                  {t('pages.auth.deleteAccountWarning')}
                </Alert>
                <Typography variant="subtitle2" color="error" gutterBottom>
                  {t('pages.auth.dangerZone')}
                </Typography>
                <Box sx={{ p: 2, border: 1, borderColor: 'error.main', borderRadius: 1 }}>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    {t('pages.auth.deleteAccountDescription')}
                  </Typography>
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={() => setDeleteAccountOpen(true)}
                    disabled={!user?.email}
                    data-testid="delete-account-btn"
                  >
                    {t('pages.auth.deleteAccount')}
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Box>
        </SettingsSection>
      )}

      {/* Delete Account Step-Up Dialog (#1813) */}
      {accountSection && (
        <StepUpConfirmDialog
          open={deleteAccountOpen}
          title={t('pages.auth.deleteAccountDialogTitle')}
          description={
            <>
              {t('pages.auth.deleteAccountConfirm')}
              <ErasurePreviewNotice preview={erasurePreview} testIdPrefix="delete-account-preview" />
            </>
          }
          echoLabel={t('pages.auth.deleteAccountEmailLabel')}
          echoHelper={t('pages.auth.deleteAccountEmailHelper', { email: user?.email ?? '' })}
          expectedEcho={user?.email ?? ''}
          echoMatch="caseInsensitive"
          echoInputType="email"
          confirmLabel={t('pages.auth.deleteAccountConfirmButton')}
          testIdPrefix="delete-account"
          stepUpAction="account_erasure"
          testIds={{ echo: 'delete-account-email' }}
          onConfirm={handleDeleteAccount}
          onCancel={() => setDeleteAccountOpen(false)}
        />
      )}
    </Box>
  );
}
