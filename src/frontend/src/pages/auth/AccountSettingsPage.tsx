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
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import DialogContentText from '@mui/material/DialogContentText';
import Divider from '@mui/material/Divider';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import CircularProgress from '@mui/material/CircularProgress';
import ErrorIcon from '@mui/icons-material/Error';
import EmojiNatureIcon from '@mui/icons-material/EmojiNature';
import SchoolIcon from '@mui/icons-material/School';
import ScienceIcon from '@mui/icons-material/Science';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import HomeIcon from '@mui/icons-material/Home';
import GroupIcon from '@mui/icons-material/Group';
import BusinessIcon from '@mui/icons-material/Business';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ScheduleIcon from '@mui/icons-material/Schedule';
import PeopleIcon from '@mui/icons-material/People';
import ApartmentIcon from '@mui/icons-material/Apartment';
import PageTitle from '@/components/layout/PageTitle';
import { useSnackbar } from 'notistack';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { useNavigate } from 'react-router-dom';
import { fetchProfile } from '@/store/slices/authSlice';
import { updateUserPreferences, fetchPreferences } from '@/store/slices/userPreferencesSlice';
import { resetOnboarding } from '@/store/slices/onboardingSlice';
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
import { fetchAdminStats, fetchAdminTenants, fetchAdminUsers } from '@/api/endpoints/adminPlatform';
import EditIcon from '@mui/icons-material/Edit';
import {
  getSystemSettings,
  updateHaSettings,
  testHaConnection,
  clearHaSettings,
} from '@/api/endpoints/adminSettings';
import type { HATestResponse } from '@/api/endpoints/adminSettings';
import { parseApiError } from '@/api/errors';
import { isLightMode, isFullMode, KAMERPLANTER_MODE } from '@/config/mode';
import NotificationSettingsTab from './NotificationSettingsTab';
import type {
  AuthProviderInfo,
  SessionInfo,
  ExperienceLevel,
  ApiKeySummary,
  AdminTenant,
  AdminUser,
  AdminPlatformStats,
} from '@/api/types';

const EXPERIENCE_LEVELS: { level: ExperienceLevel; icon: React.ReactNode }[] = [
  { level: 'beginner', icon: <EmojiNatureIcon /> },
  { level: 'intermediate', icon: <SchoolIcon /> },
  { level: 'expert', icon: <ScienceIcon /> },
];

// Responsive grid that fills available width
const GRID_2COL = {
  display: 'grid',
  gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
  gap: 2,
} as const;

const GRID_3COL = {
  display: 'grid',
  gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: '1fr 1fr 1fr' },
  gap: 2,
} as const;

interface TabDef {
  key: string;
  label: string;
}

export default function AccountSettingsPage() {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const user = useAppSelector((s) => s.auth.user);
  const preferences = useAppSelector((s) => s.userPreferences.preferences);
  const activeTenant = useAppSelector((s) => s.tenants.activeTenant);

  const tabs: TabDef[] = useMemo(() => {
    if (isLightMode) {
      return [
        { key: 'profile', label: t('pages.auth.tabProfile') },
        { key: 'notifications', label: t('pages.auth.tabNotifications') },
        { key: 'experience', label: t('pages.auth.tabExperience') },
        { key: 'ha', label: t('pages.auth.tabIntegrations') },
      ];
    }
    return [
      { key: 'profile', label: t('pages.auth.tabProfile') },
      { key: 'notifications', label: t('pages.auth.tabNotifications') },
      { key: 'experience', label: t('pages.auth.tabExperience') },
      { key: 'security', label: t('pages.auth.tabSecurity') },
      { key: 'sessions', label: t('pages.auth.tabSessions') },
      { key: 'apikeys', label: t('pages.auth.tabApiKeys') },
      { key: 'ha', label: t('pages.auth.tabIntegrations') },
      { key: 'platform', label: t('pages.auth.tabPlatform') },
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

  const [adminStats, setAdminStats] = useState<AdminPlatformStats | null>(null);
  const [adminTenants, setAdminTenants] = useState<AdminTenant[]>([]);
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([]);
  const [isPlatformAdmin, setIsPlatformAdmin] = useState(false);
  const [adminLoading, setAdminLoading] = useState(false);
  // HA Settings state
  const [haUrl, setHaUrl] = useState('');
  const [haAccessToken, setHaAccessToken] = useState('');
  const [haTimeout, setHaTimeout] = useState('10');
  const [maskedToken, setMaskedToken] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [sourceToken, setSourceToken] = useState('');
  const [sourceTimeout, setSourceTimeout] = useState('');
  const [haTestResult, setHaTestResult] = useState<HATestResponse | null>(null);
  const [haSaving, setHaSaving] = useState(false);
  const [haTesting, setHaTesting] = useState(false);
  const [haResetOpen, setHaResetOpen] = useState(false);
  const [haSaveSuccess, setHaSaveSuccess] = useState(false);
  const [haResetDone, setHaResetDone] = useState(false);
  const [haLoaded, setHaLoaded] = useState(false);

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
  }, [dispatch, activeTenant?.slug]);

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

  const loadAdminData = useCallback(async () => {
    if (isLightMode) return;
    setAdminLoading(true);
    try {
      const [stats, tenants, users] = await Promise.all([
        fetchAdminStats(),
        fetchAdminTenants(),
        fetchAdminUsers(),
      ]);
      setAdminStats(stats);
      setAdminTenants(tenants);
      setAdminUsers(users);
      setIsPlatformAdmin(true);
    } catch {
      setIsPlatformAdmin(false);
    } finally {
      setAdminLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'platform' && !isPlatformAdmin && !adminLoading) {
      loadAdminData();
    }
  }, [activeTab, isPlatformAdmin, adminLoading, loadAdminData]);

  // HA Settings loader — lazy load when admin tab is opened
  const loadHaSettings = useCallback(async () => {
    try {
      const resp = await getSystemSettings();
      const ha = resp.home_assistant;
      setHaUrl(ha.ha_url || '');
      setHaTimeout(String(ha.ha_timeout));
      setMaskedToken(ha.ha_access_token_masked);
      setSourceUrl(ha.source_ha_url);
      setSourceToken(ha.source_ha_access_token);
      setSourceTimeout(ha.source_ha_timeout);
      setHaAccessToken('');
      setHaLoaded(true);
    } catch {
      /* ignore — HA settings optional */
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'ha' && !haLoaded) {
      loadHaSettings();
    }
  }, [activeTab, haLoaded, loadHaSettings]);

  const handleHaTest = async () => {
    setHaTesting(true);
    setHaTestResult(null);
    try {
      const result = await testHaConnection({
        ha_url: haUrl || null,
        ha_access_token: haAccessToken || null,
        ha_timeout: haTimeout ? Number(haTimeout) : null,
      });
      setHaTestResult(result);
    } catch {
      setHaTestResult({ success: false, message: t('errors.network') });
    } finally {
      setHaTesting(false);
    }
  };

  const handleHaSave = async () => {
    setHaSaving(true);
    setHaSaveSuccess(false);
    try {
      await updateHaSettings({
        ha_url: haUrl || null,
        ha_access_token: haAccessToken || null,
        ha_timeout: haTimeout ? Number(haTimeout) : null,
      });
      setHaSaveSuccess(true);
      await loadHaSettings();
    } catch {
      setError(t('errors.server'));
    } finally {
      setHaSaving(false);
    }
  };

  const handleHaReset = async () => {
    setHaResetOpen(false);
    setHaResetDone(false);
    try {
      await clearHaSettings();
      setHaResetDone(true);
      await loadHaSettings();
    } catch {
      setError(t('errors.server'));
    }
  };

  const haSourceLabel = (source: string) => {
    switch (source) {
      case 'db': return t('pages.admin.sourceDb');
      case 'env': return t('pages.admin.sourceEnv');
      default: return t('pages.admin.sourceDefault');
    }
  };

  const haSourceColor = (source: string): 'primary' | 'default' | 'secondary' => {
    if (source === 'db') return 'primary';
    if (source === 'env') return 'secondary';
    return 'default';
  };

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
    dispatch(updateUserPreferences({ updates: { experience_level: newLevel } }));
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
    <Box data-testid="account-settings-page" sx={{ mt: 2 }}>
      <PageTitle title={t('pages.auth.accountSettings')} />

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Tabs value={tabIndex} onChange={(_, v) => setTabIndex(v)} sx={{ mb: 3 }} variant="scrollable" scrollButtons="auto">
        {tabs.map((tab) => (
          <Tab
            key={tab.key}
            label={tab.label}
            sx={tab.key === 'account' ? {
              color: 'error.main',
              '&.Mui-selected': { color: 'error.main' },
              ml: 1,
              borderLeft: 1,
              borderColor: 'divider',
            } : undefined}
          />
        ))}
      </Tabs>

      {/* ── Profile Tab ── */}
      {activeTab === 'profile' && (
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
        </Box>
      )}

      {/* ── Security Tab ── */}
      {activeTab === 'security' && (
        <Box sx={GRID_2COL}>
          {/* Password */}
          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {hasLocalProvider ? t('pages.auth.changePassword') : t('pages.auth.setPassword')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.auth.securitySectionDesc')}
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
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
                <Button
                  variant="contained"
                  onClick={handlePasswordChange}
                  disabled={!newPassword || (hasLocalProvider && !currentPassword)}
                  sx={{ alignSelf: 'flex-start' }}
                  data-testid="change-password-btn"
                >
                  {hasLocalProvider ? t('pages.auth.changePasswordButton') : t('pages.auth.setPasswordButton')}
                </Button>
              </Box>
            </CardContent>
          </Card>

          {/* Linked Providers */}
          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.auth.linkedProviders')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.auth.linkedProvidersDesc')}
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
                    <ListItemText primary={p.provider} secondary={p.provider_email} />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* ── Sessions Tab ── */}
      {activeTab === 'sessions' && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('pages.auth.activeSessions')}
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>{t('pages.auth.unknownDevice')}</TableCell>
                    <TableCell>{t('pages.auth.adminTenantType')}</TableCell>
                    <TableCell>IP</TableCell>
                    <TableCell>{t('pages.auth.expires')}</TableCell>
                    <TableCell align="right" />
                  </TableRow>
                </TableHead>
                <TableBody>
                  {sessions.map((s) => (
                    <TableRow key={s.key}>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2" sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {s.user_agent?.substring(0, 60) || t('pages.auth.unknownDevice')}
                          </Typography>
                          {s.is_current && <Chip label={t('pages.auth.currentSession')} size="small" color="primary" />}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={s.is_persistent ? t('pages.auth.sessionPersistent') : t('pages.auth.sessionTemporary')}
                          size="small"
                          variant="outlined"
                          color={s.is_persistent ? 'success' : 'default'}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>{s.ip_address || '\u2014'}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{new Date(s.expires_at).toLocaleDateString()}</Typography>
                      </TableCell>
                      <TableCell align="right">
                        {!s.is_current && (
                          <IconButton size="small" onClick={() => handleRevokeSession(s.key)}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* ── API Keys Tab ── */}
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
                <Typography variant="body2" sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                  {createdKeyRaw}
                </Typography>
              </Alert>
            )}

            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>{t('pages.auth.apiKeyLabel')}</TableCell>
                    <TableCell>Key</TableCell>
                    <TableCell>{t('pages.auth.adminTenantStatus')}</TableCell>
                    <TableCell>{t('pages.auth.lastUsed')}</TableCell>
                    <TableCell align="right" />
                  </TableRow>
                </TableHead>
                <TableBody>
                  {apiKeys.map((k) => (
                    <TableRow key={k.key}>
                      <TableCell>{k.label}</TableCell>
                      <TableCell>
                        <Chip label={k.key_prefix + '...'} size="small" variant="outlined" sx={{ fontFamily: 'monospace' }} />
                      </TableCell>
                      <TableCell>
                        {k.revoked
                          ? <Chip label={t('pages.auth.revoked')} size="small" color="error" />
                          : <Chip label={t('pages.auth.adminStatusActive')} size="small" color="success" />}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {k.last_used_at ? new Date(k.last_used_at).toLocaleDateString() : t('pages.auth.neverUsed')}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        {!k.revoked && (
                          <IconButton size="small" onClick={() => handleRevokeApiKey(k.key)}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                  {apiKeys.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} align="center">
                        <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                          {t('pages.auth.noApiKeys')}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* ── Experience Tab ── */}
      {activeTab === 'experience' && (
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
                    enqueueSnackbar(t('common.saved'), { variant: 'success' });
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
      )}

      {/* ── Notifications Tab ── */}
      {activeTab === 'notifications' && <NotificationSettingsTab />}

      {/* ── Admin Tab ── */}
      {activeTab === 'ha' && (
        <Box sx={GRID_2COL}>
          {/* Smart Home Master Toggle */}
          <Card variant="outlined" sx={{ gridColumn: '1 / -1' }}>
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
            </CardContent>
          </Card>

          {/* Home Assistant Integration */}
          {preferences?.smart_home_enabled && (
          <Card variant="outlined" sx={{ gridColumn: { xs: '1 / -1', md: '1 / 2' } }}>
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.admin.haSection')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
                {t('pages.admin.haSectionHelper')}
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                <Box>
                  <TextField
                    fullWidth
                    label={t('pages.admin.haUrl')}
                    value={haUrl}
                    onChange={(e) => setHaUrl(e.target.value)}
                    placeholder="http://homeassistant.local:8123"
                    helperText={t('pages.admin.haUrlHelper')}
                    data-testid="ha-url-field"
                  />
                  <Chip size="small" label={haSourceLabel(sourceUrl)} color={haSourceColor(sourceUrl)} sx={{ mt: 0.5 }} />
                </Box>

                <Box>
                  <TextField
                    fullWidth
                    type="password"
                    label={t('pages.admin.haAccessToken')}
                    value={haAccessToken}
                    onChange={(e) => setHaAccessToken(e.target.value)}
                    placeholder={t('pages.admin.haAccessTokenPlaceholder')}
                    helperText={
                      maskedToken
                        ? `${t('pages.admin.haAccessTokenHelper')}: ${maskedToken}`
                        : t('pages.admin.notConfigured')
                    }
                    data-testid="ha-token-field"
                  />
                  <Chip size="small" label={haSourceLabel(sourceToken)} color={haSourceColor(sourceToken)} sx={{ mt: 0.5 }} />
                </Box>

                <Box>
                  <TextField
                    fullWidth
                    type="number"
                    label={t('pages.admin.haTimeout')}
                    value={haTimeout}
                    onChange={(e) => setHaTimeout(e.target.value)}
                    slotProps={{ htmlInput: { min: 1, max: 120, inputMode: 'numeric' } }}
                    helperText={t('pages.admin.haTimeoutHelper')}
                    data-testid="ha-timeout-field"
                  />
                  <Chip size="small" label={haSourceLabel(sourceTimeout)} color={haSourceColor(sourceTimeout)} sx={{ mt: 0.5 }} />
                </Box>
              </Box>

              {haTestResult && (
                <Alert
                  severity={haTestResult.success ? 'success' : 'error'}
                  icon={haTestResult.success ? <CheckCircleIcon /> : <ErrorIcon />}
                  sx={{ mt: 2 }}
                  data-testid="test-result-alert"
                >
                  {haTestResult.message}
                  {haTestResult.ha_version && ` (v${haTestResult.ha_version})`}
                </Alert>
              )}
              {haSaveSuccess && (
                <Alert severity="success" sx={{ mt: 2 }} data-testid="save-success-alert">
                  {t('pages.admin.saved')}
                </Alert>
              )}
              {haResetDone && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  {t('pages.admin.resetDone')}
                </Alert>
              )}

              <Box sx={{ display: 'flex', gap: 1, mt: 3, flexWrap: 'wrap', alignItems: 'center' }}>
                <Button
                  variant="outlined"
                  onClick={handleHaTest}
                  disabled={haTesting || !haUrl}
                  startIcon={haTesting ? <CircularProgress size={16} /> : undefined}
                  data-testid="test-connection-btn"
                >
                  {t('pages.admin.testConnection')}
                </Button>
                <Button
                  variant="contained"
                  onClick={handleHaSave}
                  disabled={haSaving}
                  startIcon={haSaving ? <CircularProgress size={16} /> : undefined}
                  data-testid="save-settings-btn"
                >
                  {t('common.save')}
                </Button>
                <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />
                <Button
                  variant="text"
                  color="warning"
                  onClick={() => setHaResetOpen(true)}
                  data-testid="reset-settings-btn"
                >
                  {t('pages.admin.resetToDefaults')}
                </Button>
              </Box>
            </CardContent>
          </Card>
          )}
        </Box>
      )}

      {/* ── Platform Tab ── */}
      {activeTab === 'platform' && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {/* Mode Cards in 3-col grid */}
          <Box sx={GRID_3COL}>
            {/* Light Mode */}
            <Card
              variant="outlined"
              sx={{
                borderColor: KAMERPLANTER_MODE === 'light' ? 'primary.main' : 'divider',
                borderWidth: KAMERPLANTER_MODE === 'light' ? 2 : 1,
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
                  <HomeIcon color={KAMERPLANTER_MODE === 'light' ? 'primary' : 'action'} />
                  <Typography variant="h6">{t('pages.auth.platformModeLight')}</Typography>
                  {KAMERPLANTER_MODE === 'light' && (
                    <Chip icon={<CheckCircleIcon />} label={t('pages.auth.platformModeActive')} color="primary" size="small" />
                  )}
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                  {t('pages.auth.platformModeLightDescription')}
                </Typography>
                <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
                  {t('pages.auth.platformModeLightFeatures').split(';').map((f) => (
                    <Typography component="li" variant="body2" key={f} sx={{ mb: 0.25 }}>{f}</Typography>
                  ))}
                </Box>
              </CardContent>
            </Card>

            {/* Full Mode */}
            <Card
              variant="outlined"
              sx={{
                borderColor: KAMERPLANTER_MODE === 'full' ? 'primary.main' : 'divider',
                borderWidth: KAMERPLANTER_MODE === 'full' ? 2 : 1,
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
                  <GroupIcon color={KAMERPLANTER_MODE === 'full' ? 'primary' : 'action'} />
                  <Typography variant="h6">{t('pages.auth.platformModeFull')}</Typography>
                  {KAMERPLANTER_MODE === 'full' && (
                    <Chip icon={<CheckCircleIcon />} label={t('pages.auth.platformModeActive')} color="primary" size="small" />
                  )}
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                  {t('pages.auth.platformModeFullDescription')}
                </Typography>
                <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
                  {t('pages.auth.platformModeFullFeatures').split(';').map((f) => (
                    <Typography component="li" variant="body2" key={f} sx={{ mb: 0.25 }}>{f}</Typography>
                  ))}
                </Box>
              </CardContent>
            </Card>

            {/* Enterprise Mode */}
            <Card variant="outlined" sx={{ borderColor: 'divider', opacity: 0.7 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
                  <BusinessIcon color="action" />
                  <Typography variant="h6">{t('pages.auth.platformModeEnterprise')}</Typography>
                  <Chip icon={<ScheduleIcon />} label={t('pages.auth.platformModeComingSoon')} size="small" variant="outlined" />
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                  {t('pages.auth.platformModeEnterpriseDescription')}
                </Typography>
                <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
                  {t('pages.auth.platformModeEnterpriseFeatures').split(';').map((f) => (
                    <Typography component="li" variant="body2" key={f} sx={{ mb: 0.25 }}>{f}</Typography>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Box>

          <Alert severity="info">
            <Typography variant="body2">
              {t('pages.auth.platformModeEnvHint')}
              {' '}
              <Typography component="code" variant="body2" sx={{ fontFamily: 'monospace' }}>
                KAMERPLANTER_MODE=light | full
              </Typography>
            </Typography>
          </Alert>

          {/* Admin: Stats + Org/User tables */}
          {isFullMode && isPlatformAdmin && (
            <>
              {/* Stats in 4-col grid */}
              {adminStats && (
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', sm: 'repeat(4, 1fr)' }, gap: 2 }}>
                  {([
                    { value: adminStats.active_users, label: t('pages.auth.adminActiveUsers') },
                    { value: adminStats.total_users, label: t('pages.auth.adminTotalUsers') },
                    { value: adminStats.active_tenants, label: t('pages.auth.adminActiveTenants') },
                    { value: adminStats.total_memberships, label: t('pages.auth.adminTotalMemberships') },
                  ] as const).map(({ value, label }) => (
                    <Card key={label} variant="outlined">
                      <CardContent sx={{ textAlign: 'center', py: 2, '&:last-child': { pb: 2 } }}>
                        <Typography variant="h3" sx={{ fontWeight: 300 }}>{value}</Typography>
                        <Typography variant="caption" color="text.secondary">{label}</Typography>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}

              {/* Organizations & Users in 2-col grid on large, stacked on small */}
              <Box sx={GRID_2COL}>
                {/* Organizations */}
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                      <ApartmentIcon color="primary" />
                      <Typography variant="h6">{t('pages.auth.adminTenantsTitle')}</Typography>
                      <Chip label={adminTenants.length} size="small" />
                    </Box>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>{t('pages.auth.adminTenantName')}</TableCell>
                            <TableCell>{t('pages.auth.adminTenantType')}</TableCell>
                            <TableCell align="right">{t('pages.auth.adminTenantMembers')}</TableCell>
                            <TableCell>{t('pages.auth.adminTenantStatus')}</TableCell>
                            <TableCell align="right" />
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {adminTenants.map((tenant) => (
                            <TableRow key={tenant.key}>
                              <TableCell>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <Typography variant="body2" sx={{ fontWeight: 500 }}>{tenant.name}</Typography>
                                  {tenant.is_platform && (
                                    <Chip label="Platform" size="small" color="warning" variant="outlined" />
                                  )}
                                </Box>
                                <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                                  {tenant.slug}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Chip
                                  label={t(`enums.tenantType.${tenant.tenant_type}`)}
                                  size="small"
                                  variant="outlined"
                                  color={tenant.tenant_type === 'organization' ? 'info' : 'default'}
                                />
                              </TableCell>
                              <TableCell align="right">{tenant.member_count}</TableCell>
                              <TableCell>
                                <Chip
                                  label={tenant.is_active ? t('pages.auth.adminStatusActive') : t('pages.auth.adminStatusInactive')}
                                  size="small"
                                  color={tenant.is_active ? 'success' : 'default'}
                                />
                              </TableCell>
                              <TableCell align="right">
                                <IconButton
                                  size="small"
                                  onClick={() => navigate(`/admin/tenants/${tenant.key}`)}
                                  data-testid={`edit-tenant-${tenant.key}`}
                                  aria-label={t('pages.auth.editTenantTitle')}
                                >
                                  <EditIcon fontSize="small" />
                                </IconButton>
                              </TableCell>
                            </TableRow>
                          ))}
                          {adminTenants.length === 0 && (
                            <TableRow>
                              <TableCell colSpan={5} align="center">
                                <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                                  {t('pages.auth.adminNoTenants')}
                                </Typography>
                              </TableCell>
                            </TableRow>
                          )}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>

                {/* Users */}
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                      <PeopleIcon color="primary" />
                      <Typography variant="h6">{t('pages.auth.adminUsersTitle')}</Typography>
                      <Chip label={adminUsers.length} size="small" />
                    </Box>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>{t('pages.auth.adminUserName')}</TableCell>
                            <TableCell>{t('pages.auth.adminUserTenants')}</TableCell>
                            <TableCell>{t('pages.auth.adminUserStatus')}</TableCell>
                            <TableCell align="right" />
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {adminUsers.map((u) => (
                            <TableRow key={u.key}>
                              <TableCell>
                                <Typography variant="body2" sx={{ fontWeight: 500 }}>{u.display_name}</Typography>
                                <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                                  {u.email}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                                  {u.roles.map((r) => (
                                    <Chip
                                      key={r.tenant_key}
                                      label={`${r.tenant_name} (${r.role})`}
                                      size="small"
                                      variant="outlined"
                                      color={r.role === 'admin' ? 'warning' : r.role === 'grower' ? 'success' : 'default'}
                                    />
                                  ))}
                                  {u.roles.length === 0 && (
                                    <Typography variant="caption" color="text.secondary">
                                      {t('pages.auth.adminNoMemberships')}
                                    </Typography>
                                  )}
                                </Box>
                              </TableCell>
                              <TableCell>
                                <Box sx={{ display: 'flex', gap: 0.5, flexDirection: 'column', alignItems: 'flex-start' }}>
                                  <Chip
                                    label={u.is_active ? t('pages.auth.adminStatusActive') : t('pages.auth.adminStatusInactive')}
                                    size="small"
                                    color={u.is_active ? 'success' : 'default'}
                                  />
                                  {!u.email_verified && (
                                    <Chip label={t('pages.auth.adminUnverified')} size="small" color="warning" variant="outlined" />
                                  )}
                                </Box>
                              </TableCell>
                              <TableCell align="right">
                                <IconButton
                                  size="small"
                                  onClick={() => navigate(`/admin/users/${u.key}`)}
                                  data-testid={`edit-user-${u.key}`}
                                  aria-label={t('pages.auth.editUserTitle')}
                                >
                                  <EditIcon fontSize="small" />
                                </IconButton>
                              </TableCell>
                            </TableRow>
                          ))}
                          {adminUsers.length === 0 && (
                            <TableRow>
                              <TableCell colSpan={4} align="center">
                                <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                                  {t('pages.auth.adminNoUsers')}
                                </Typography>
                              </TableCell>
                            </TableRow>
                          )}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              </Box>
            </>
          )}

        </Box>
      )}

      {/* ── Account Tab ── */}
      {activeTab === 'account' && (
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
                  onClick={handleDeleteAccount}
                  data-testid="delete-account-btn"
                >
                  {t('pages.auth.deleteAccount')}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* Create API Key Dialog */}
      <Dialog fullScreen={fullScreen} open={newKeyDialogOpen} onClose={() => setNewKeyDialogOpen(false)} maxWidth="sm" fullWidth>
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

      {/* HA Reset Dialog */}
      <Dialog fullScreen={fullScreen} open={haResetOpen} onClose={() => setHaResetOpen(false)}>
        <DialogTitle>{t('pages.admin.resetToDefaults')}</DialogTitle>
        <DialogContent>
          <DialogContentText>{t('pages.admin.resetConfirm')}</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHaResetOpen(false)}>{t('common.cancel')}</Button>
          <Button onClick={handleHaReset} color="warning">
            {t('common.confirm')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
