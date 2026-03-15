import { useState, useEffect, useCallback, useMemo } from 'react';
import { useTabUrl } from '@/hooks/useTabUrl';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import IconButton from '@mui/material/IconButton';
import Divider from '@mui/material/Divider';
import InputAdornment from '@mui/material/InputAdornment';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import InputLabel from '@mui/material/InputLabel';
import FormControl from '@mui/material/FormControl';
import DeleteIcon from '@mui/icons-material/Delete';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import Chip from '@mui/material/Chip';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import EmojiNatureIcon from '@mui/icons-material/EmojiNature';
import SchoolIcon from '@mui/icons-material/School';
import ScienceIcon from '@mui/icons-material/Science';
import PageTitle from '@/components/layout/PageTitle';
import { useSnackbar } from 'notistack';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchProfile } from '@/store/slices/authSlice';
import { updateUserPreferences, fetchPreferences } from '@/store/slices/userPreferencesSlice';
import {
  updateProfile,
  changePassword,
  listProviders,
  unlinkProvider,
  listSessions,
  revokeSession,
  deleteAccount,
  createApiKey,
  listApiKeys,
  revokeApiKey,
} from '@/api/endpoints/auth';
import { parseApiError } from '@/api/errors';
import { isLightMode } from '@/config/mode';
import type { AuthProviderInfo, SessionInfo, ExperienceLevel, ApiKeySummary } from '@/api/types';

const EXPERIENCE_LEVELS: { level: ExperienceLevel; icon: React.ReactNode }[] = [
  { level: 'beginner', icon: <EmojiNatureIcon /> },
  { level: 'intermediate', icon: <SchoolIcon /> },
  { level: 'expert', icon: <ScienceIcon /> },
];

// Tab definitions: in light mode only show Profile and Experience
interface TabDef {
  key: string;
  label: string;
}

export default function AccountSettingsPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const user = useAppSelector((s) => s.auth.user);
  const preferences = useAppSelector((s) => s.userPreferences.preferences);

  const tabs: TabDef[] = useMemo(() => {
    if (isLightMode) {
      return [
        { key: 'profile', label: t('pages.auth.tabProfile') },
        { key: 'experience', label: t('pages.auth.tabExperience') },
      ];
    }
    return [
      { key: 'profile', label: t('pages.auth.tabProfile') },
      { key: 'security', label: t('pages.auth.tabSecurity') },
      { key: 'sessions', label: t('pages.auth.tabSessions') },
      { key: 'apikeys', label: t('pages.auth.tabApiKeys') },
      { key: 'experience', label: t('pages.auth.tabExperience') },
      { key: 'account', label: t('pages.auth.tabAccount') },
    ];
  }, [t]);

  const [tabIndex, setTabIndex] = useTabUrl(tabs.map((t) => t.key));
  const activeTab = tabs[tabIndex]?.key ?? 'profile';

  const [displayName, setDisplayName] = useState('');
  const [locale, setLocale] = useState('de');
  const [timezone, setTimezone] = useState('Europe/Berlin');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [providers, setProviders] = useState<AuthProviderInfo[]>([]);
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [apiKeys, setApiKeys] = useState<ApiKeySummary[]>([]);
  const [newKeyLabel, setNewKeyLabel] = useState('');
  const [newKeyDialogOpen, setNewKeyDialogOpen] = useState(false);
  const [createdKeyRaw, setCreatedKeyRaw] = useState<string | null>(null);
  const [error, setError] = useState('');

  const hasLocalProvider = providers.some((p) => p.provider === 'local');

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name);
      setLocale(user.locale);
      setTimezone(user.timezone || 'Europe/Berlin');
    }
  }, [user]);

  useEffect(() => {
    dispatch(fetchPreferences());
  }, [dispatch]);

  const loadProviders = useCallback(() => {
    listProviders().then(setProviders).catch(() => {});
  }, []);

  const loadSessions = useCallback(() => {
    listSessions().then(setSessions).catch(() => {});
  }, []);

  const loadApiKeys = useCallback(() => {
    listApiKeys().then(setApiKeys).catch(() => {});
  }, []);

  useEffect(() => {
    if (isLightMode) return;
    loadProviders();
    loadSessions();
    loadApiKeys();
  }, [loadProviders, loadSessions, loadApiKeys]);

  const handleProfileSave = async () => {
    setError('');
    try {
      await updateProfile({ display_name: displayName, locale, timezone });
      dispatch(fetchProfile());
      enqueueSnackbar(t('common.saved'), { variant: 'success' });
    } catch (err) {
      setError(parseApiError(err));
    }
  };

  const handlePasswordChange = async () => {
    setError('');
    try {
      await changePassword(hasLocalProvider ? currentPassword : null, newPassword);
      setCurrentPassword('');
      setNewPassword('');
      enqueueSnackbar(t('pages.auth.passwordChanged'), { variant: 'success' });
      loadProviders();
    } catch (err) {
      setError(parseApiError(err));
    }
  };

  const handleUnlinkProvider = async (key: string) => {
    try {
      await unlinkProvider(key);
      loadProviders();
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    }
  };

  const handleRevokeSession = async (key: string) => {
    try {
      await revokeSession(key);
      loadSessions();
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    }
  };

  const handleCreateApiKey = async () => {
    try {
      const result = await createApiKey({ label: newKeyLabel });
      setCreatedKeyRaw(result.raw_key);
      setNewKeyLabel('');
      setNewKeyDialogOpen(false);
      loadApiKeys();
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    }
  };

  const handleRevokeApiKey = async (keyId: string) => {
    try {
      await revokeApiKey(keyId);
      loadApiKeys();
      enqueueSnackbar(t('pages.auth.apiKeyRevoked'), { variant: 'success' });
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    }
  };

  const handleExperienceLevelChange = (_: React.MouseEvent<HTMLElement>, newLevel: ExperienceLevel | null) => {
    if (!newLevel) return;
    const currentLevel = preferences?.experience_level ?? 'beginner';
    const order: Record<ExperienceLevel, number> = { beginner: 0, intermediate: 1, expert: 2 };
    if (order[newLevel] < order[currentLevel]) {
      if (!window.confirm(t('pages.auth.experienceLevelDowngradeWarning'))) return;
    }
    dispatch(updateUserPreferences({ experience_level: newLevel }));
    enqueueSnackbar(t('common.saved'), { variant: 'success' });
  };

  const handleDeleteAccount = async () => {
    if (!window.confirm(t('pages.auth.deleteAccountConfirm'))) return;
    try {
      await deleteAccount();
      window.location.href = '/login';
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    }
  };

  return (
    <Box sx={{ maxWidth: 700, mx: 'auto', mt: 2 }}>
      <PageTitle title={t('pages.auth.accountSettings')} />

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Tabs value={tabIndex} onChange={(_, v) => setTabIndex(v)} sx={{ mb: 2 }} variant="scrollable" scrollButtons="auto">
        {tabs.map((tab) => (
          <Tab key={tab.key} label={tab.label} />
        ))}
      </Tabs>

      {activeTab === 'profile' && (
        <Card>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              {t('pages.auth.profileSection')}
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 3 }}>
              <TextField
                label={t('pages.auth.displayName')}
                fullWidth
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                autoFocus
                data-testid="profile-display-name"
              />
              <TextField
                label={t('pages.auth.email')}
                fullWidth
                value={user?.email || ''}
                disabled
                helperText={t('pages.auth.emailReadOnly')}
                data-testid="profile-email"
              />
            </Box>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              {t('pages.auth.regionSection')}
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 3 }}>
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
            <Button variant="contained" onClick={handleProfileSave} data-testid="profile-save-btn">
              {t('common.save')}
            </Button>
          </CardContent>
        </Card>
      )}

      {activeTab === 'security' && (
        <Card>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              {hasLocalProvider ? t('pages.auth.changePassword') : t('pages.auth.setPassword')}
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 3 }}>
              {hasLocalProvider && (
                <TextField
                  label={t('pages.auth.currentPassword')}
                  type="password"
                  fullWidth
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  data-testid="current-password-field"
                />
              )}
              <TextField
                label={t('pages.auth.newPasswordField')}
                type="password"
                fullWidth
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                helperText={t('pages.auth.passwordHelp')}
                data-testid="new-password-field"
              />
            </Box>
            <Button
              variant="contained"
              onClick={handlePasswordChange}
              disabled={!newPassword || (hasLocalProvider && !currentPassword)}
              data-testid="change-password-btn"
            >
              {hasLocalProvider ? t('pages.auth.changePasswordButton') : t('pages.auth.setPasswordButton')}
            </Button>

            <Divider sx={{ my: 3 }} />
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              {t('pages.auth.linkedProviders')}
            </Typography>
            <List disablePadding>
              {providers.map((p) => (
                <ListItem
                  key={p.key}
                  disableGutters
                  secondaryAction={
                    providers.length > 1 && (
                      <IconButton
                        edge="end"
                        onClick={() => handleUnlinkProvider(p.key)}
                        aria-label={t('pages.auth.unlinkProvider')}
                        data-testid={`unlink-provider-${p.key}`}
                      >
                        <DeleteIcon />
                      </IconButton>
                    )
                  }
                >
                  <ListItemText
                    primary={p.provider}
                    secondary={p.provider_email}
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {activeTab === 'sessions' && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('pages.auth.activeSessions')}
            </Typography>
            <List>
              {sessions.map((s) => (
                <ListItem
                  key={s.key}
                  secondaryAction={
                    !s.is_current && (
                      <IconButton edge="end" onClick={() => handleRevokeSession(s.key)}>
                        <DeleteIcon />
                      </IconButton>
                    )
                  }
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {s.user_agent?.substring(0, 60) || t('pages.auth.unknownDevice')}
                        {s.is_current && <Chip label={t('pages.auth.currentSession')} size="small" color="primary" />}
                        <Chip
                          label={s.is_persistent ? t('pages.auth.sessionPersistent') : t('pages.auth.sessionTemporary')}
                          size="small"
                          variant="outlined"
                          color={s.is_persistent ? 'success' : 'default'}
                        />
                      </Box>
                    }
                    secondary={`IP: ${s.ip_address || '\u2014'} | ${t('pages.auth.expires')}: ${new Date(s.expires_at).toLocaleDateString()}`}
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {activeTab === 'apikeys' && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                {t('pages.auth.apiKeysTitle')}
              </Typography>
              <Button variant="contained" size="small" onClick={() => setNewKeyDialogOpen(true)}>
                {t('pages.auth.createApiKey')}
              </Button>
            </Box>

            {createdKeyRaw && (
              <Alert
                severity="warning"
                sx={{ mb: 2 }}
                action={
                  <IconButton
                    size="small"
                    onClick={() => {
                      navigator.clipboard.writeText(createdKeyRaw);
                      enqueueSnackbar(t('pages.auth.apiKeyCopied'), { variant: 'success' });
                    }}
                  >
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                }
                onClose={() => setCreatedKeyRaw(null)}
              >
                <Typography variant="body2" sx={{ mb: 0.5 }}>
                  {t('pages.auth.apiKeyCreatedWarning')}
                </Typography>
                <Typography variant="body2" fontFamily="monospace" sx={{ wordBreak: 'break-all' }}>
                  {createdKeyRaw}
                </Typography>
              </Alert>
            )}

            <List>
              {apiKeys.map((k) => (
                <ListItem
                  key={k.key}
                  secondaryAction={
                    !k.revoked && (
                      <IconButton edge="end" onClick={() => handleRevokeApiKey(k.key)}>
                        <DeleteIcon />
                      </IconButton>
                    )
                  }
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {k.label}
                        <Chip
                          label={k.key_prefix + '...'}
                          size="small"
                          variant="outlined"
                          sx={{ fontFamily: 'monospace' }}
                        />
                        {k.revoked && <Chip label={t('pages.auth.revoked')} size="small" color="error" />}
                      </Box>
                    }
                    secondary={
                      k.last_used_at
                        ? `${t('pages.auth.lastUsed')}: ${new Date(k.last_used_at).toLocaleDateString()}`
                        : t('pages.auth.neverUsed')
                    }
                  />
                </ListItem>
              ))}
              {apiKeys.length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                  {t('pages.auth.noApiKeys')}
                </Typography>
              )}
            </List>
          </CardContent>
        </Card>
      )}

      {activeTab === 'experience' && (
        <Card>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
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
              sx={{ mb: 4 }}
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

            <Divider sx={{ mb: 2 }} />
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
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
                  dispatch(updateUserPreferences({ watering_can_liters: val }));
                  enqueueSnackbar(t('common.saved'), { variant: 'success' });
                }
              }}
              slotProps={{ htmlInput: { min: 0.5, max: 100, step: 0.5, inputMode: 'decimal' } }}
              InputProps={{
                endAdornment: <InputAdornment position="end">L</InputAdornment>,
              }}
              sx={{ maxWidth: 220 }}
              data-testid="watering-can-size-field"
            />
          </CardContent>
        </Card>
      )}

      {activeTab === 'account' && (
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
                onClick={handleDeleteAccount}
                data-testid="delete-account-btn"
              >
                {t('pages.auth.deleteAccount')}
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Create API Key Dialog */}
      <Dialog open={newKeyDialogOpen} onClose={() => setNewKeyDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{t('pages.auth.createApiKey')}</DialogTitle>
        <DialogContent>
          <TextField
            label={t('pages.auth.apiKeyLabel')}
            fullWidth
            value={newKeyLabel}
            onChange={(e) => setNewKeyLabel(e.target.value)}
            sx={{ mt: 1 }}
            autoFocus
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewKeyDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button variant="contained" onClick={handleCreateApiKey} disabled={!newKeyLabel.trim()}>
            {t('common.create')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
