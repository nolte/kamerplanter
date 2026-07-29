import { useState, useCallback, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import CircularProgress from '@mui/material/CircularProgress';
import Stack from '@mui/material/Stack';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import PageTitle from '@/components/layout/PageTitle';
import client from '@/api/client';
import { parseApiError } from '@/api/errors';
import { listProviders } from '@/api/endpoints/auth';

interface ConsentItem {
  purpose: string;
  label: string;
  description: string;
  legal_basis: string;
  required: boolean;
  granted: boolean;
  granted_at: string | null;
  revoked_at: string | null;
}

interface ExportItem {
  key: string;
  status: string;
  requested_at: string | null;
  completed_at: string | null;
}

interface RestrictionItem {
  key: string;
  scope: string;
  reason: string;
  notes: string | null;
  created_at: string | null;
  lifted_at: string | null;
}

const RESTRICTION_REASONS = [
  'accuracy_contested',
  'unlawful_processing',
  'purpose_expired',
  'objection_pending',
] as const;

type RestrictionReason = (typeof RESTRICTION_REASONS)[number];

const TAB_KEYS = ['consents', 'export', 'erasure', 'restrict'] as const;

export default function PrivacySettingsPage() {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));

  const [tabIndex, setTabIndex] = useState(0);

  // ── Consents tab state ────────────────────────────────────────────
  const [consents, setConsents] = useState<ConsentItem[]>([]);
  const [consentsLoading, setConsentsLoading] = useState(false);
  const [consentsError, setConsentsError] = useState('');

  // ── Export tab state ──────────────────────────────────────────────
  const [exportRequest, setExportRequest] = useState<ExportItem | null>(null);
  const [exportPending, setExportPending] = useState(false);
  const [exportError, setExportError] = useState('');

  // ── Erasure tab state ─────────────────────────────────────────────
  const [erasureDialogOpen, setErasureDialogOpen] = useState(false);
  const [erasurePending, setErasurePending] = useState(false);
  const [erasureMessage, setErasureMessage] = useState('');
  const [erasureError, setErasureError] = useState('');
  const [erasurePassword, setErasurePassword] = useState('');
  // Tri-state: ``null`` = provider list not yet known (load pending or failed),
  // ``true``/``false`` = the account has / has not a local-password provider.
  const [hasLocalPassword, setHasLocalPassword] = useState<boolean | null>(null);

  // Local-password accounts must re-authenticate with their current password
  // before an erasure request is accepted (REQ-025, backend authorises via the
  // ``password`` field). We **fail closed**: require the password unless we
  // positively know the account is federated / password-less. Otherwise a
  // failed or still-pending provider load would hide the password field for a
  // local account, the backend would reject the request with 401, and the user
  // would have no field to supply the password — an unrecoverable dead end
  // (issue #394). Sending a password the backend ignores for a federated
  // account is harmless (``password_hash is None`` skips the check).
  const requiresPassword = hasLocalPassword !== false;

  // ── Restrict tab state ────────────────────────────────────────────
  const [restrictions, setRestrictions] = useState<RestrictionItem[]>([]);
  const [restrictScope, setRestrictScope] = useState('');
  const [restrictReason, setRestrictReason] = useState<RestrictionReason>('accuracy_contested');
  const [restrictNotes, setRestrictNotes] = useState('');
  const [restrictPending, setRestrictPending] = useState(false);
  const [restrictError, setRestrictError] = useState('');

  // ── Loaders ───────────────────────────────────────────────────────
  const loadConsents = useCallback(async () => {
    setConsentsLoading(true);
    setConsentsError('');
    try {
      const res = await client.get<ConsentItem[]>('/privacy/consents');
      setConsents(res.data);
    } catch (err) {
      setConsentsError(parseApiError(err));
    } finally {
      setConsentsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Determine the account's login providers once so the erasure dialog knows
    // whether a current-password confirmation is required. A failed load leaves
    // ``hasLocalPassword`` at ``null`` (unknown → fail closed, see
    // ``requiresPassword`` above), so the password field is still shown.
    listProviders()
      .then((list) => setHasLocalPassword(list.some((p) => p.provider === 'local')))
      .catch(() => setHasLocalPassword(null));
  }, []);

  useEffect(() => {
    // Load consents from the backend whenever the consents tab becomes active.
    // This synchronizes React state with the backend (external system), so the
    // setState-in-effect pattern is intentional and matches the loader pattern
    // used in AccountSettingsPage (loadHaSettings, loadAdminData).
    if (tabIndex === 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadConsents();
    }
  }, [tabIndex, loadConsents]);

  const handleRequestExport = async () => {
    setExportPending(true);
    setExportError('');
    try {
      const res = await client.post<ExportItem>('/privacy/export');
      setExportRequest(res.data);
    } catch (err) {
      setExportError(parseApiError(err));
    } finally {
      setExportPending(false);
    }
  };

  const resetErasureDialogState = () => {
    setErasureDialogOpen(false);
    setErasurePassword('');
    setErasureError('');
  };

  const closeErasureDialog = () => {
    // Ignore close attempts (backdrop click, Escape, Cancel button) while the
    // erasure request is in flight so a stray dismissal cannot mask the
    // eventual success/error outcome (UI-NFR-008 R-016 double-submit
    // protection extends to the whole in-flight interaction, not just the
    // confirm button). The success path below bypasses this guard via
    // ``resetErasureDialogState`` since it runs while ``erasurePending`` is
    // still true.
    if (erasurePending) return;
    resetErasureDialogState();
  };

  const handleRequestErasure = async () => {
    // Local-password accounts must supply their current password; the backend
    // rejects the request (401) otherwise. Guard client-side to avoid a
    // guaranteed round-trip failure and to keep the confirm button meaningful.
    if (requiresPassword && !erasurePassword.trim()) {
      setErasureError(t('pages.privacy.erasurePasswordRequired'));
      return;
    }
    setErasurePending(true);
    setErasureError('');
    setErasureMessage('');
    try {
      const payload = requiresPassword ? { password: erasurePassword } : {};
      await client.post('/privacy/erasure', payload);
      setErasureMessage(t('pages.privacy.erasureRequested'));
      resetErasureDialogState();
    } catch (err) {
      // Keep the dialog open so the user can correct the password; the error is
      // rendered inside the dialog (see erasure confirmation dialog below).
      setErasureError(parseApiError(err));
    } finally {
      setErasurePending(false);
    }
  };

  const handleCreateRestriction = async () => {
    if (!restrictScope.trim()) {
      setRestrictError(t('pages.privacy.restrictScopeRequired'));
      return;
    }
    setRestrictPending(true);
    setRestrictError('');
    try {
      const res = await client.post<RestrictionItem>('/privacy/restrict', {
        scope: restrictScope,
        reason: restrictReason,
        notes: restrictNotes || null,
      });
      setRestrictions((prev) => [res.data, ...prev]);
      setRestrictScope('');
      setRestrictNotes('');
    } catch (err) {
      setRestrictError(parseApiError(err));
    } finally {
      setRestrictPending(false);
    }
  };

  return (
    <Box data-testid="privacy-settings-page" sx={{ mt: 2 }}>
      <PageTitle title={t('pages.privacy.title')} />

      <Tabs
        value={tabIndex}
        onChange={(_, v: number) => setTabIndex(v)}
        sx={{ mb: 3 }}
        variant="scrollable"
        scrollButtons="auto"
        allowScrollButtonsMobile
        aria-label={t('pages.privacy.tabsAriaLabel')}
        data-testid="privacy-tabs"
      >
        <Tab label={t('pages.privacy.tabConsents')} data-testid="privacy-tab-consents" />
        <Tab label={t('pages.privacy.tabExport')} data-testid="privacy-tab-export" />
        <Tab label={t('pages.privacy.tabErasure')} data-testid="privacy-tab-erasure" />
        <Tab label={t('pages.privacy.tabRestrict')} data-testid="privacy-tab-restrict" />
      </Tabs>

      {/* ── Consents Tab ── */}
      {TAB_KEYS[tabIndex] === 'consents' && (
        <Card variant="outlined" data-testid="privacy-consents-panel">
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('pages.privacy.consentsHeading')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.privacy.consentsDescription')}
            </Typography>

            {consentsError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {consentsError}
              </Alert>
            )}

            {consentsLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
                <CircularProgress size={24} />
              </Box>
            ) : (
              <List disablePadding data-testid="privacy-consents-list">
                {consents.length === 0 && (
                  <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                    {t('pages.privacy.consentsEmpty')}
                  </Typography>
                )}
                {consents.map((c) => (
                  <ListItem
                    key={c.purpose}
                    disableGutters
                    secondaryAction={
                      <Chip
                        label={
                          c.granted
                            ? t('pages.privacy.consentGranted')
                            : t('pages.privacy.consentRevoked')
                        }
                        color={c.granted ? 'success' : 'default'}
                        size="small"
                      />
                    }
                  >
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                          {c.label || c.purpose}
                          {/* Clarifies why no revoke action is offered here: required
                              consents are tied to core functionality (REQ-025) and
                              cannot be revoked without deleting the account. */}
                          {c.required && (
                            <Chip
                              label={t('pages.privacy.consentRequired')}
                              size="small"
                              variant="outlined"
                              data-testid={`consent-required-${c.purpose}`}
                            />
                          )}
                        </Box>
                      }
                      secondary={c.description}
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Export Tab ── */}
      {TAB_KEYS[tabIndex] === 'export' && (
        <Card variant="outlined" data-testid="privacy-export-panel">
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('pages.privacy.exportHeading')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.privacy.exportDescription')}
            </Typography>

            {exportError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {exportError}
              </Alert>
            )}

            <Button
              variant="contained"
              onClick={handleRequestExport}
              disabled={exportPending}
              startIcon={exportPending ? <CircularProgress size={16} /> : undefined}
              data-testid="privacy-export-request-btn"
            >
              {t('pages.privacy.exportRequestButton')}
            </Button>

            {exportRequest && (
              <Alert severity="success" sx={{ mt: 2 }} data-testid="privacy-export-result">
                {t('pages.privacy.exportRequested', { status: exportRequest.status })}
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Erasure Tab ── */}
      {TAB_KEYS[tabIndex] === 'erasure' && (
        <Card variant="outlined" data-testid="privacy-erasure-panel">
          <CardContent>
            <Alert severity="warning" sx={{ mb: 2 }}>
              {t('pages.privacy.erasureWarning')}
            </Alert>

            <Typography variant="h6" gutterBottom color="error">
              {t('pages.privacy.erasureHeading')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.privacy.erasureDescription')}
            </Typography>

            {erasureMessage && (
              <Alert severity="info" sx={{ mb: 2 }}>
                {erasureMessage}
              </Alert>
            )}

            <Button
              variant="outlined"
              color="error"
              onClick={() => setErasureDialogOpen(true)}
              data-testid="privacy-erasure-request-btn"
            >
              {t('pages.privacy.erasureRequestButton')}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* ── Restrict Tab ── */}
      {TAB_KEYS[tabIndex] === 'restrict' && (
        <Card variant="outlined" data-testid="privacy-restrict-panel">
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('pages.privacy.restrictHeading')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.privacy.restrictDescription')}
            </Typography>

            {restrictError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {restrictError}
              </Alert>
            )}

            <Stack spacing={2} sx={{ maxWidth: 480, mb: 3 }}>
              <TextField
                label={t('pages.privacy.restrictScopeLabel')}
                helperText={t('pages.privacy.restrictScopeHelper')}
                value={restrictScope}
                onChange={(e) => setRestrictScope(e.target.value)}
                fullWidth
                data-testid="privacy-restrict-scope"
              />
              <TextField
                label={t('pages.privacy.restrictReasonLabel')}
                value={restrictReason}
                onChange={(e) => setRestrictReason(e.target.value as RestrictionReason)}
                select
                fullWidth
                data-testid="privacy-restrict-reason"
              >
                {RESTRICTION_REASONS.map((reason) => (
                  <MenuItem key={reason} value={reason}>
                    {t(`pages.privacy.restrictReason.${reason}`)}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                label={t('pages.privacy.restrictNotesLabel')}
                value={restrictNotes}
                onChange={(e) => setRestrictNotes(e.target.value)}
                fullWidth
                multiline
                rows={2}
                data-testid="privacy-restrict-notes"
              />
              <Button
                variant="contained"
                onClick={handleCreateRestriction}
                disabled={restrictPending || !restrictScope.trim()}
                startIcon={restrictPending ? <CircularProgress size={16} /> : undefined}
                sx={{ alignSelf: 'flex-start' }}
                data-testid="privacy-restrict-submit-btn"
              >
                {t('pages.privacy.restrictSubmitButton')}
              </Button>
            </Stack>

            <Typography variant="subtitle1" gutterBottom>
              {t('pages.privacy.restrictListHeading')}
            </Typography>
            <List disablePadding data-testid="privacy-restrict-list">
              {restrictions.length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                  {t('pages.privacy.restrictListEmpty')}
                </Typography>
              )}
              {restrictions.map((r) => (
                <ListItem
                  key={r.key}
                  disableGutters
                  secondaryAction={
                    <Chip
                      label={t(`pages.privacy.restrictReason.${r.reason}`)}
                      size="small"
                      variant="outlined"
                    />
                  }
                >
                  <ListItemText primary={r.scope} secondary={r.notes ?? ''} />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* ── Erasure Confirmation Dialog ── */}
      <Dialog
        open={erasureDialogOpen}
        onClose={closeErasureDialog}
        fullScreen={fullScreen}
        maxWidth="xs"
        fullWidth
        role="alertdialog"
        aria-labelledby="privacy-erasure-dialog-title"
        aria-describedby="privacy-erasure-dialog-description"
        data-testid="privacy-erasure-dialog"
      >
        <DialogTitle id="privacy-erasure-dialog-title">
          {t('pages.privacy.erasureDialogTitle')}
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="privacy-erasure-dialog-description">
            {t('pages.privacy.erasureDialogText')}
          </DialogContentText>

          {/* Local-password accounts confirm their identity with the current
              password before the erasure is authorised (REQ-025). Autofocus
              goes to the password field here because it is the next required
              action; federated accounts (no password field) instead autofocus
              the Cancel button below to keep the safe default for a
              destructive action. */}
          {requiresPassword && (
            <TextField
              type="password"
              label={t('pages.privacy.erasureDialogPasswordLabel')}
              helperText={t('pages.privacy.erasureDialogPasswordHelper')}
              value={erasurePassword}
              onChange={(e) => setErasurePassword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !erasurePending) {
                  handleRequestErasure();
                }
              }}
              autoComplete="current-password"
              fullWidth
              required
              autoFocus
              disabled={erasurePending}
              error={Boolean(erasureError)}
              sx={{ mt: 2 }}
              data-testid="privacy-erasure-password"
            />
          )}

          {erasureError && (
            <Alert severity="error" sx={{ mt: 2 }} data-testid="privacy-erasure-dialog-error">
              {erasureError}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            onClick={closeErasureDialog}
            disabled={erasurePending}
            autoFocus={!requiresPassword}
            data-testid="privacy-erasure-cancel-btn"
          >
            {t('common.cancel')}
          </Button>
          <Button
            onClick={handleRequestErasure}
            color="error"
            variant="contained"
            disabled={erasurePending || (requiresPassword && !erasurePassword.trim())}
            startIcon={erasurePending ? <CircularProgress size={16} color="inherit" /> : undefined}
            data-testid="privacy-erasure-confirm-btn"
          >
            {t('pages.privacy.erasureDialogConfirm')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
