import { useState, useEffect, useCallback } from 'react';
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
import DeleteIcon from '@mui/icons-material/Delete';
import Chip from '@mui/material/Chip';
import { useSnackbar } from 'notistack';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchProfile } from '@/store/slices/authSlice';
import {
  updateProfile,
  changePassword,
  listProviders,
  unlinkProvider,
  listSessions,
  revokeSession,
  deleteAccount,
} from '@/api/endpoints/auth';
import { parseApiError } from '@/api/errors';
import type { AuthProviderInfo, SessionInfo } from '@/api/types';

export default function AccountSettingsPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const user = useAppSelector((s) => s.auth.user);

  const [tab, setTab] = useState(0);
  const [displayName, setDisplayName] = useState('');
  const [locale, setLocale] = useState('de');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [providers, setProviders] = useState<AuthProviderInfo[]>([]);
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name);
      setLocale(user.locale);
    }
  }, [user]);

  const loadProviders = useCallback(() => {
    listProviders().then(setProviders).catch(() => {});
  }, []);

  const loadSessions = useCallback(() => {
    listSessions().then(setSessions).catch(() => {});
  }, []);

  useEffect(() => {
    loadProviders();
    loadSessions();
  }, [loadProviders, loadSessions]);

  const handleProfileSave = async () => {
    setError('');
    try {
      await updateProfile({ display_name: displayName, locale });
      dispatch(fetchProfile());
      enqueueSnackbar(t('common.saved'), { variant: 'success' });
    } catch (err) {
      setError(parseApiError(err));
    }
  };

  const handlePasswordChange = async () => {
    setError('');
    try {
      await changePassword(currentPassword, newPassword);
      setCurrentPassword('');
      setNewPassword('');
      enqueueSnackbar(t('pages.auth.passwordChanged'), { variant: 'success' });
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
      <Typography variant="h5" gutterBottom>
        {t('pages.auth.accountSettings')}
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('pages.auth.tabProfile')} />
        <Tab label={t('pages.auth.tabSecurity')} />
        <Tab label={t('pages.auth.tabSessions')} />
        <Tab label={t('pages.auth.tabAccount')} />
      </Tabs>

      {tab === 0 && (
        <Card>
          <CardContent>
            <TextField
              label={t('pages.auth.displayName')}
              fullWidth
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              sx={{ mb: 2 }}
            />
            <TextField
              label={t('pages.auth.email')}
              fullWidth
              value={user?.email || ''}
              disabled
              sx={{ mb: 2 }}
            />
            <Button variant="contained" onClick={handleProfileSave}>
              {t('common.save')}
            </Button>
          </CardContent>
        </Card>
      )}

      {tab === 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('pages.auth.changePassword')}
            </Typography>
            <TextField
              label={t('pages.auth.currentPassword')}
              type="password"
              fullWidth
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              sx={{ mb: 2 }}
            />
            <TextField
              label={t('pages.auth.newPassword')}
              type="password"
              fullWidth
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              sx={{ mb: 2 }}
            />
            <Button variant="contained" onClick={handlePasswordChange} sx={{ mb: 3 }}>
              {t('pages.auth.changePasswordButton')}
            </Button>

            <Typography variant="h6" gutterBottom>
              {t('pages.auth.linkedProviders')}
            </Typography>
            <List>
              {providers.map((p) => (
                <ListItem
                  key={p.key}
                  secondaryAction={
                    providers.length > 1 && (
                      <IconButton edge="end" onClick={() => handleUnlinkProvider(p.key)}>
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

      {tab === 2 && (
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
                      </Box>
                    }
                    secondary={`IP: ${s.ip_address || '-'} | ${t('pages.auth.expires')}: ${new Date(s.expires_at).toLocaleDateString()}`}
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {tab === 3 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom color="error">
              {t('pages.auth.dangerZone')}
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              {t('pages.auth.deleteAccountWarning')}
            </Typography>
            <Button variant="outlined" color="error" onClick={handleDeleteAccount}>
              {t('pages.auth.deleteAccount')}
            </Button>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
