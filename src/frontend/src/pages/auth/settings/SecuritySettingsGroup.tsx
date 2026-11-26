import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import IconButton from '@mui/material/IconButton';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DeleteIcon from '@mui/icons-material/Delete';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CloseIcon from '@mui/icons-material/Close';
import QrCode2Icon from '@mui/icons-material/QrCode2';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import { useAsyncOptions } from '@/hooks/useAsyncOptions';
import { useNotification } from '@/hooks/useNotification';
import {
  changePassword,
  listProviders,
  unlinkProvider,
  listSessions,
  revokeSession,
  createApiKey,
  listApiKeys,
  revokeApiKey,
} from '@/api/endpoints/auth';
import {
  getStepUpErrorMessage,
  getStepUpReauthCallbackErrorMessage,
  isStepUpRejection,
  parseApiError,
} from '@/api/errors';
import StepUpConfirmDialog from '@/components/common/StepUpConfirmDialog';
import type { StepUpConfirmation } from '@/components/common/StepUpConfirmDialog';
import StepUpCodeField from '@/components/common/StepUpCodeField';
import StepUpReauthButton from '@/components/common/StepUpReauthButton';
import { useStepUpFactors } from '@/hooks/useStepUpFactors';
import { usePendingStepUpReauth, useStepUpResume } from '@/hooks/useStepUpReauth';
import { toCredentialStepUpBody } from '@/utils/stepUp';
import { isLightMode } from '@/config/mode';
import type { AuthProviderInfo, SessionInfo, ApiKeySummary } from '@/api/types';
import ConnectDeviceDialog, { CONNECT_DEVICE_STEP_UP_SURFACE } from '../ConnectDeviceDialog';
import SettingsSection from './SettingsSection';
import { GRID_2COL } from './settingsLayout';
import { findSettingsSection, type SettingsGroupProps } from '@/config/settingsGroups';
import { formatDate } from '@/utils/formatting';

/**
 * Minimum length of a new password — the backend schema's `min_length`
 * (`ChangePasswordRequest.new_password`). The button stays disabled below it rather
 * than spending a round trip on a 422.
 */
const NEW_PASSWORD_MIN_LENGTH = 10;

/**
 * Group "Security & access": password and sign-in methods, sessions and device
 * pairing, API keys, and — in light mode — the app-connect QR code.
 */
export default function SecuritySettingsGroup({ sections }: SettingsGroupProps) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();

  const passwordSection = findSettingsSection(sections, 'security');
  const sessionsSection = findSettingsSection(sections, 'sessions');
  const apiKeysSection = findSettingsSection(sections, 'apikeys');
  const connectSection = findSettingsSection(sections, 'connect');

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [providers, setProviders] = useState<AuthProviderInfo[]>([]);
  // Unknown until the list arrived — the password form fails closed on it (#1842).
  const [providersLoaded, setProvidersLoaded] = useState(false);
  const [providersLoadFailed, setProvidersLoadFailed] = useState(false);
  const [passwordStepUpCode, setPasswordStepUpCode] = useState('');
  const [apiKeys, setApiKeys] = useState<ApiKeySummary[]>([]);
  const [apiKeysLoading, setApiKeysLoading] = useState(true);
  const [apiKeysError, setApiKeysError] = useState(false);
  const [newKeyLabel, setNewKeyLabel] = useState('');
  // #1815/#1847 — back from the fresh sign-in at the identity provider: reopen
  // the label dialog the API-key step-up was started from. The label itself did
  // not survive the round trip; the pending token then confirms the creation.
  const resumeCreateApiKey = useStepUpResume('create-api-key');
  const [newKeyDialogOpen, setNewKeyDialogOpen] = useState(resumeCreateApiKey);
  // The step-up of minting an API key (#1847) — full mode only.
  const [apiKeyStepUpOpen, setApiKeyStepUpOpen] = useState(false);
  // The linked provider whose removal awaits its step-up (#1847).
  const [unlinkTarget, setUnlinkTarget] = useState<AuthProviderInfo | null>(null);
  // #1118 — the QR pairing dialog. Deliberately *not* a Redux flag: the dialog
  // holds a live one-time credential, so everything about it dies with the
  // sessions tab.
  // #1815/#1847 — back from the fresh sign-in: reopen the pairing step-up.
  const resumeConnectDevice = useStepUpResume(CONNECT_DEVICE_STEP_UP_SURFACE);
  const [connectDeviceOpen, setConnectDeviceOpen] = useState(resumeConnectDevice);
  const [createdKeyRaw, setCreatedKeyRaw] = useState<string | null>(null);
  const [error, setError] = useState('');

  // Which step-up factor the password form asks for — the same fail-closed
  // rule as StepUpConfirmDialog (#1842): the current-password field is hidden
  // only when a non-empty provider list positively lacks `local`; a pending,
  // failed or empty list shows it. A federated-only account confirms setting
  // its first password with an e-mailed code instead (#1815).
  const passwordFactors = useStepUpFactors(providersLoaded ? providers : null);
  // #1815 — an account whose provider can prove a fresh sign-in confirms with it.
  // The form is inline, so after the return it simply reads the pending token;
  // the resume context is consumed so it cannot reopen anything later.
  useStepUpResume('change-password');
  const passwordReauth = usePendingStepUpReauth('password_change', null);
  const passwordReauthed = passwordReauth.hasToken;
  // #1847 — removing a sign-in method is a step-up too. Which provider was being
  // removed does not survive the round trip to the identity provider, so the
  // resume context is only consumed here; the pending token is picked up by the
  // dialog when the user starts the removal again within its five minutes.
  useStepUpResume('unlink-provider');

  const loadProviders = useCallback(() => {
    listProviders()
      .then((list) => {
        setProviders(list);
        setProvidersLoaded(true);
        setProvidersLoadFailed(false);
      })
      .catch(() => {
        // Not swallowed silently any more (#1842): the list stays unknown, so
        // the password form keeps asking for the current password, and the
        // providers card says the list could not be loaded.
        setProvidersLoaded(false);
        setProvidersLoadFailed(true);
      });
  }, []);

  // #3013 (A-01): the sessions list is how a foreign session is spotted and revoked, so a failed
  // load renders an error with retry rather than an empty table. Light mode has no sessions endpoint.
  const fetchSessions = useCallback((): Promise<SessionInfo[]> => listSessions(), []);
  const sessionsLoad = useAsyncOptions(fetchSessions, { enabled: !isLightMode });
  const sessions = sessionsLoad.options;
  const loadSessions = sessionsLoad.reload;

  const loadApiKeys = useCallback(() => {
    setApiKeysLoading(true);
    setApiKeysError(false);
    listApiKeys()
      .then(setApiKeys)
      .catch(() => setApiKeysError(true))
      .finally(() => setApiKeysLoading(false));
  }, []);

  useEffect(() => {
    // API keys exist in BOTH modes (REQ-033 §4.3) — they are the only credential
    // the MCP interface accepts, and the tab is shown in light mode too. Loading
    // them must therefore not sit behind the light-mode guard; skipping it left
    // the tab permanently empty except right after creating a key, which
    // refreshes the list itself.
    loadApiKeys();
    // Linked providers and sessions presuppose real accounts: those endpoints do
    // not exist in light mode, so asking for them would only produce 404s.
    if (isLightMode) return;
    loadProviders();
  }, [loadProviders, loadApiKeys]);

  const handlePasswordChange = async () => {
    setError('');
    try {
      const { showPassword, showCode } = passwordFactors;
      if (passwordReauth.callbackError) passwordReauth.dismissError();
      // A pending fresh sign-in (#1815) is the factor on its own. The token stays
      // in storage until the outcome is known: spent on success or when the
      // step-up itself is refused (401/429), kept when e.g. the new password is
      // refused (422) — it is still valid then.
      const token = passwordReauthed ? (passwordReauth.peekToken() ?? undefined) : undefined;
      // In the both-fields state (federated list, then a plain 401) an empty
      // password is sent as `null`, as for an account without one.
      const current =
        !passwordReauthed && showPassword && currentPassword.length > 0 ? currentPassword : null;
      const code =
        !passwordReauthed && showCode && passwordStepUpCode.length > 0 ? passwordStepUpCode : undefined;
      await changePassword(current, newPassword, code, token);
      if (token) passwordReauth.consumeToken();
      setCurrentPassword('');
      setNewPassword('');
      setPasswordStepUpCode('');
      passwordFactors.reset();
      notification.success(t('pages.auth.passwordChanged'));
      loadProviders();
    } catch (err) {
      // A throttled step-up (429 STEP_UP_LOCKED, #1816) reads as the translated
      // lockout with its minutes, STEP_UP_CODE_REQUIRED asks for the e-mailed
      // code — never the backend's English message. The rejected secret is
      // cleared so it is not resent by accident.
      setError(getStepUpErrorMessage(err, t));
      setCurrentPassword('');
      setPasswordStepUpCode('');
      if (passwordReauthed && isStepUpRejection(err)) passwordReauth.consumeToken();
      passwordFactors.noteRejection(err);
    }
  };

  // Removing a sign-in method is a credential change (#1847): it passes the
  // step-up. A rejection propagates to the dialog, which shows it and stays open.
  const handleUnlinkProvider = async (credentials: StepUpConfirmation) => {
    if (!unlinkTarget) return;
    await unlinkProvider(unlinkTarget.key, toCredentialStepUpBody(credentials));
    setUnlinkTarget(null);
    notification.success(t('pages.auth.providerUnlinked'));
    loadProviders();
  };

  const handleRevokeSession = async (key: string) => {
    try {
      await revokeSession(key);
      loadSessions();
    } catch (err) {
      notification.error(parseApiError(err, t));
    }
  };

  const finishApiKeyCreation = (rawKey: string) => {
    setCreatedKeyRaw(rawKey);
    setNewKeyLabel('');
    setNewKeyDialogOpen(false);
    setApiKeyStepUpOpen(false);
    loadApiKeys();
  };

  // Light mode (REQ-027) mints the MCP key without a step-up: every request
  // there already is the system account and there is no password to ask for.
  // In full mode a key survives a password change, so minting one passes the
  // step-up first (#1847) — the label dialog hands over to the confirmation.
  const handleCreateApiKey = async () => {
    if (!isLightMode) {
      setNewKeyDialogOpen(false);
      setApiKeyStepUpOpen(true);
      return;
    }
    try {
      const result = await createApiKey({ label: newKeyLabel.trim() });
      finishApiKeyCreation(result.raw_key);
    } catch (err) {
      notification.error(parseApiError(err, t));
    }
  };

  // A rejection propagates to the step-up dialog, which shows it and stays open.
  const handleConfirmApiKey = async (credentials: StepUpConfirmation) => {
    const result = await createApiKey({ label: newKeyLabel.trim(), ...toCredentialStepUpBody(credentials) });
    finishApiKeyCreation(result.raw_key);
  };

  const handleRevokeApiKey = async (keyId: string) => {
    try {
      await revokeApiKey(keyId);
      loadApiKeys();
      notification.success(t('pages.auth.apiKeyRevoked'));
    } catch (err) {
      notification.error(parseApiError(err, t));
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {error && <Alert severity="error">{error}</Alert>}

      {passwordSection && (
        <SettingsSection section={passwordSection}>
            <Box sx={GRID_2COL}>
              {/* Password */}
              <Card variant="outlined">
                <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
                  <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                    {passwordFactors.showPassword ? t('pages.auth.changePassword') : t('pages.auth.setPassword')}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {t('pages.auth.securitySectionDesc')}
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
                    {passwordReauth.callbackError && (
                      <Alert severity="error" data-testid="change-password-reauth-callback-error">
                        {getStepUpReauthCallbackErrorMessage(passwordReauth.callbackError, t)}
                      </Alert>
                    )}
                    {passwordReauthed && (
                      <Alert severity="success" data-testid="change-password-reauth-done">
                        {t('pages.auth.stepUpReauthDone')}
                      </Alert>
                    )}
                    {passwordFactors.showReauth && !passwordReauthed && (
                      <StepUpReauthButton
                        stepUpAction="password_change"
                        providers={passwordFactors.reauthProviders}
                        surface="change-password"
                        onStart={() => {
                          setError('');
                          if (passwordReauth.callbackError) passwordReauth.dismissError();
                        }}
                        onUnavailable={() => {
                          setError(t('pages.auth.stepUpReauthUnavailable'));
                          passwordFactors.noteReauthUnavailable();
                        }}
                        onPasswordRequired={() => {
                          setError(t('pages.auth.stepUpCodeNotNeeded'));
                          passwordFactors.noteAccountHasPassword();
                        }}
                      />
                    )}
                    {passwordFactors.showPassword && !passwordReauthed && (
                      <TextField
                        label={t('pages.auth.currentPassword')}
                        type="password"
                        fullWidth
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        autoComplete="current-password"
                        data-testid="current-password-field"
                      />
                    )}
                    {passwordFactors.showCode && !passwordReauthed && (
                      <StepUpCodeField
                        value={passwordStepUpCode}
                        onChange={setPasswordStepUpCode}
                        testIdPrefix="change-password"
                        stepUpAction="password_change"
                        onAccountHasPassword={passwordFactors.noteAccountHasPassword}
                        onReauthRequired={passwordFactors.noteReauthRequired}
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
                      disabled={
                        newPassword.length < NEW_PASSWORD_MIN_LENGTH ||
                        !passwordFactors.isSatisfied(currentPassword, passwordStepUpCode, passwordReauthed)
                      }
                      sx={{ alignSelf: 'flex-start' }}
                      data-testid="change-password-btn"
                    >
                      {passwordFactors.showPassword
                        ? t('pages.auth.changePasswordButton')
                        : t('pages.auth.setPasswordButton')}
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
                  {providersLoadFailed && (
                    <Alert severity="warning" sx={{ mb: 2 }} data-testid="providers-load-failed">
                      {t('pages.auth.providersLoadFailed')}
                    </Alert>
                  )}
                  <List disablePadding>
                    {providers.map((p) => (
                      <ListItem
                        key={p.key}
                        disableGutters
                        secondaryAction={
                          providers.length > 1 && (
                            <IconButton
                              edge="end"
                              onClick={() => setUnlinkTarget(p)}
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
        </SettingsSection>
      )}

      {sessionsSection && (
        <SettingsSection section={sessionsSection}>
              <Card>
                <CardContent>
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: { xs: 'stretch', sm: 'center' },
                      flexDirection: { xs: 'column', sm: 'row' },
                      gap: 1,
                      mb: 1,
                    }}
                  >
                    <Typography variant="h6">
                      {t('pages.auth.activeSessions')}
                    </Typography>
                    {/* #1118 — pairing exists only where accounts do, and this tab is
                        full-mode-only, so light mode is gated by construction rather
                        than by a second check that could drift from the first. */}
                    <Button
                      variant="contained"
                      size="small"
                      startIcon={<QrCode2Icon />}
                      onClick={() => setConnectDeviceOpen(true)}
                      data-testid="connect-device-button"
                      // UI-NFR-001 R-011 — 48px minimum touch target on mobile,
                      // even though the label stays "small"-sized.
                      sx={{ minHeight: 48 }}
                    >
                      {t('pages.auth.devicePairing.connectDevice')}
                    </Button>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {t('pages.auth.devicePairing.sessionsHint')}
                  </Typography>
                  {sessionsLoad.error ? (
                    <ErrorDisplay error="pages.auth.sessionsLoadFailed" onRetry={sessionsLoad.reload} />
                  ) : sessionsLoad.loading && sessions.length === 0 ? (
                    <LoadingSkeleton variant="table" rows={3} />
                  ) : (
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>{t('pages.auth.sessionDevice')}</TableCell>
                          <TableCell>{t('pages.auth.adminTenantType')}</TableCell>
                          <TableCell>IP</TableCell>
                          <TableCell>{t('pages.auth.expires')}</TableCell>
                          <TableCell align="right" />
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {sessions.map((s) => {
                          // A device paired by QR code names itself (#1118); a browser
                          // session has no label, so the user agent stays the fallback
                          // and the row renders exactly as it did before that feature.
                          const userAgentLabel = s.user_agent?.substring(0, 60);
                          return (
                            <TableRow key={s.key} data-testid={`session-row-${s.key}`}>
                              <TableCell>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                  <Box sx={{ minWidth: 0 }}>
                                    <Typography
                                      variant="body2"
                                      data-testid={`session-device-${s.key}`}
                                      sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                                    >
                                      {s.device_name || userAgentLabel || t('pages.auth.unknownDevice')}
                                    </Typography>
                                    {s.device_name && userAgentLabel && (
                                      // Keep the technical identity visible next to the
                                      // self-chosen label: the label is what the owner
                                      // recognises, the user agent is what tells them
                                      // it is the app rather than a browser.
                                      <Typography
                                        variant="caption"
                                        color="text.secondary"
                                        data-testid={`session-user-agent-${s.key}`}
                                        sx={{ display: 'block', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                                      >
                                        {userAgentLabel}
                                      </Typography>
                                    )}
                                  </Box>
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
                                <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>{s.ip_address || '—'}</Typography>
                              </TableCell>
                              <TableCell>
                                <Typography variant="body2">{formatDate(s.expires_at)}</Typography>
                              </TableCell>
                              <TableCell align="right">
                                {!s.is_current && (
                                  <IconButton
                                    size="small"
                                    data-testid={`session-revoke-${s.key}`}
                                    aria-label={t('pages.auth.revokeSession')}
                                    onClick={() => handleRevokeSession(s.key)}
                                  >
                                    <DeleteIcon fontSize="small" />
                                  </IconButton>
                                )}
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </TableContainer>
                  )}
                </CardContent>
              </Card>
              {/* Mounted inside the sessions tab, not next to the page's other
                  dialogs: leaving the tab unmounts it, which is the cheapest possible
                  guarantee that a pairing code cannot linger behind a view the user
                  has walked away from. */}
              <ConnectDeviceDialog
                open={connectDeviceOpen}
                onClose={() => {
                  setConnectDeviceOpen(false);
                  // A device that paired while the dialog was open shows up as a new
                  // session; without this the list would keep claiming it isn't there.
                  loadSessions();
                }}
              />
        </SettingsSection>
      )}

      {apiKeysSection && (
        <SettingsSection section={apiKeysSection}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">
                    {t('pages.auth.apiKeysTitle')}
                  </Typography>
                  <Button
                    variant="contained"
                    size="small"
                    onClick={() => setNewKeyDialogOpen(true)}
                    data-testid="create-api-key-button"
                  >
                    {t('pages.auth.createApiKey')}
                  </Button>
                </Box>

                {createdKeyRaw && (
                  <Alert
                    severity="warning"
                    sx={{ mb: 2 }}
                    action={
                      // MUI only renders the built-in onClose dismiss button when no
                      // custom `action` is set, so the copy and close controls are
                      // both supplied explicitly here — otherwise this alert (which
                      // carries the one-time-visible raw secret) could never be
                      // dismissed from the UI.
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        <IconButton
                          size="small"
                          aria-label={t('pages.auth.copyApiKey')}
                          onClick={() => {
                            navigator.clipboard.writeText(createdKeyRaw);
                            notification.success(t('pages.auth.apiKeyCopied'));
                          }}
                        >
                          <ContentCopyIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          aria-label={t('common.close')}
                          onClick={() => setCreatedKeyRaw(null)}
                        >
                          <CloseIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    }
                  >
                    <Typography variant="body2" sx={{ mb: 0.5 }}>
                      {t('pages.auth.apiKeyCreatedWarning')}
                    </Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                      {createdKeyRaw}
                    </Typography>
                  </Alert>
                )}

                {apiKeysLoading ? (
                  // Loading state MUST be shown separately from the empty state
                  // (UI-NFR-004 R-020) — otherwise "No API keys yet." briefly
                  // flashes as a false statement while the list is still in flight.
                  <LoadingSkeleton variant="table" rows={3} />
                ) : apiKeysError ? (
                  <ErrorDisplay error={t('errors.loadFailed')} onRetry={loadApiKeys} />
                ) : (
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>{t('pages.auth.apiKeyLabel')}</TableCell>
                          <TableCell>{t('pages.auth.apiKeyColumnValue')}</TableCell>
                          <TableCell>{t('pages.auth.adminTenantStatus')}</TableCell>
                          {/* Least essential column — hidden below `sm` (UI-NFR-010
                              R-021) so the table stays usable without horizontal
                              scrolling on narrow/kiosk-style phone viewports. */}
                          <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                            {t('pages.auth.lastUsed')}
                          </TableCell>
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
                            <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                              <Typography variant="body2" color="text.secondary">
                                {k.last_used_at ? formatDate(k.last_used_at) : t('pages.auth.neverUsed')}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              {!k.revoked && (
                                <IconButton
                                  size="small"
                                  aria-label={t('pages.auth.revokeApiKey')}
                                  onClick={() => handleRevokeApiKey(k.key)}
                                >
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
                )}
              </CardContent>
            </Card>
        </SettingsSection>
      )}

      {connectSection && (
        <SettingsSection section={connectSection}>
            <Box sx={{ maxWidth: 600 }} data-testid="connect-app-tab">
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
                    <QrCode2Icon color="primary" />
                    <Typography variant="h6">
                      {t('pages.auth.devicePairing.discovery.tabTitle')}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {t('pages.auth.devicePairing.discovery.tabBlurb')}
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<QrCode2Icon />}
                    onClick={() => setConnectDeviceOpen(true)}
                    data-testid="connect-device-button"
                    // UI-NFR-001 R-011 — 48px minimum touch target on mobile.
                    sx={{ minHeight: 48 }}
                  >
                    {t('pages.auth.devicePairing.connectDevice')}
                  </Button>
                </CardContent>
              </Card>
              {/* The dialog reads `isLightMode` itself and renders its URL-only
                  instance-discovery variant here; no code, no backend call, so no
                  cleanup reload is needed on close (there are no sessions to refresh
                  in light mode). */}
              <ConnectDeviceDialog
                open={connectDeviceOpen}
                onClose={() => setConnectDeviceOpen(false)}
              />
            </Box>
        </SettingsSection>
      )}

      {/* Remove a sign-in method — step-up (#1847) */}
      <StepUpConfirmDialog
        open={unlinkTarget !== null}
        title={t('pages.auth.unlinkProviderStepUpTitle')}
        description={t('pages.auth.unlinkProviderStepUpDescription', {
          provider: unlinkTarget
            ? `${unlinkTarget.provider}${unlinkTarget.provider_email ? ` (${unlinkTarget.provider_email})` : ''}`
            : '',
        })}
        confirmLabel={t('pages.auth.unlinkProviderStepUpConfirm')}
        stepUpAction="provider_unlink"
        stepUpTarget={unlinkTarget?.key}
        testIdPrefix="unlink-provider"
        onConfirm={handleUnlinkProvider}
        onCancel={() => setUnlinkTarget(null)}
      />

      {/* Create API Key — step-up (#1847), full mode only */}
      {!isLightMode && (
        <StepUpConfirmDialog
          open={apiKeyStepUpOpen}
          title={t('pages.auth.apiKeyStepUpTitle')}
          description={t('pages.auth.apiKeyStepUpDescription', { label: newKeyLabel.trim() })}
          confirmLabel={t('pages.auth.apiKeyStepUpConfirm')}
          confirmColor="primary"
          stepUpAction="api_key_creation"
          testIdPrefix="create-api-key"
          onConfirm={handleConfirmApiKey}
          onCancel={() => setApiKeyStepUpOpen(false)}
        />
      )}

      {/* Create API Key Dialog */}
      <Dialog
        fullScreen={fullScreen}
        open={newKeyDialogOpen}
        onClose={() => setNewKeyDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        data-testid="api-key-label-dialog"
        aria-labelledby="api-key-label-dialog-title"
      >
        <DialogTitle id="api-key-label-dialog-title">{t('pages.auth.createApiKey')}</DialogTitle>
        <DialogContent>
          <TextField
            label={t('pages.auth.apiKeyLabel')}
            fullWidth
            value={newKeyLabel}
            onChange={(e) => setNewKeyLabel(e.target.value)}
            sx={{ mt: 1 }}
            autoFocus
            data-testid="api-key-label-field"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewKeyDialogOpen(false)}>{t('common.cancel')}</Button>
          <Button
            variant="contained"
            onClick={handleCreateApiKey}
            disabled={!newKeyLabel.trim()}
            data-testid="api-key-label-submit"
          >
            {t('common.create')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
