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
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import CircularProgress from '@mui/material/CircularProgress';
import Stack from '@mui/material/Stack';
import PageTitle from '@/components/layout/PageTitle';
import client from '@/api/client';
import { parseApiError } from '@/api/errors';
import type { AccountErasureRequest } from '@/api/types';
import StepUpConfirmDialog from '@/components/common/StepUpConfirmDialog';
import type { StepUpConfirmation } from '@/components/common/StepUpConfirmDialog';
import { useAppSelector } from '@/store/hooks';

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
  file_size_bytes?: number | null;
  /** #1645 - why a failed run delivered nothing. */
  error_message?: string | null;
}

/**
 * Export states from which the request no longer moves on its own.
 *
 * #1645 - the run used to stop at `processing` for ever, so the UI had nothing
 * to wait for and said "success" regardless. Naming the terminal set is what
 * lets the panel distinguish "still working" from "finished" from "failed".
 */
const TERMINAL_EXPORT_STATES = ['completed', 'failed', 'expired'];

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
  // The step-up itself — own e-mail echo, fail-closed password, lockout — lives
  // in `StepUpConfirmDialog` (#1813, #1816); the page only keeps the outcome.
  const ownEmail = useAppSelector((s) => s.auth.user?.email ?? '');
  const [erasureDialogOpen, setErasureDialogOpen] = useState(false);
  const [erasureMessage, setErasureMessage] = useState('');

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

  const handleRefreshExport = async () => {
    if (!exportRequest) return;
    setExportPending(true);
    setExportError('');
    try {
      const res = await client.get<ExportItem>(`/privacy/export/${exportRequest.key}`);
      setExportRequest(res.data);
    } catch (err) {
      setExportError(parseApiError(err));
    } finally {
      setExportPending(false);
    }
  };

  const handleDownloadExport = async () => {
    if (!exportRequest) return;
    setExportPending(true);
    setExportError('');
    try {
      // The endpoint is JWT-protected, so a plain anchor href cannot fetch it;
      // the bytes come through the authenticated client and are handed to the
      // browser as an object URL (same shape as the print endpoints).
      const res = await client.get<Blob>(`/privacy/export/${exportRequest.key}/download`, {
        responseType: 'blob',
      });
      const url = URL.createObjectURL(res.data);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `kamerplanter-export-${exportRequest.key}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setExportError(parseApiError(err));
    } finally {
      setExportPending(false);
    }
  };

  // A rejection propagates to the dialog, which shows it (the lockout included)
  // and stays open so the echo or the password can be corrected.
  const handleRequestErasure = async ({ echo, password }: StepUpConfirmation) => {
    setErasureMessage('');
    const payload: AccountErasureRequest =
      password === undefined ? { confirm_email: echo } : { confirm_email: echo, password };
    await client.post('/privacy/erasure', payload);
    setErasureDialogOpen(false);
    setErasureMessage(t('pages.privacy.erasureRequested'));
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

            {exportRequest && exportRequest.status === 'completed' && (
              <Alert severity="success" sx={{ mt: 2 }} data-testid="privacy-export-result">
                {t('pages.privacy.exportReady')}
              </Alert>
            )}

            {exportRequest && exportRequest.status === 'failed' && (
              <Alert severity="error" sx={{ mt: 2 }} data-testid="privacy-export-result">
                {exportRequest.error_message
                  ? t('pages.privacy.exportFailed', { reason: exportRequest.error_message })
                  : t('pages.privacy.exportFailedUnknown')}
              </Alert>
            )}

            {exportRequest && exportRequest.status === 'expired' && (
              // #1662 SCR-009 — a terminal state that showed nothing at all: the
              // panel went blank, which is the opposite of what this page is for.
              <Alert severity="info" sx={{ mt: 2 }} data-testid="privacy-export-result">
                {t('pages.privacy.exportExpired')}
              </Alert>
            )}

            {exportRequest && !TERMINAL_EXPORT_STATES.includes(exportRequest.status) && (
              <Alert severity="info" sx={{ mt: 2 }} data-testid="privacy-export-result">
                {t('pages.privacy.exportRequested', { status: exportRequest.status })}
              </Alert>
            )}

            {exportRequest && exportRequest.status === 'completed' && (
              <Button
                variant="outlined"
                sx={{ mt: 2 }}
                onClick={handleDownloadExport}
                disabled={exportPending}
                data-testid="privacy-export-download-btn"
              >
                {t('pages.privacy.exportDownload')}
              </Button>
            )}

            {exportRequest && !TERMINAL_EXPORT_STATES.includes(exportRequest.status) && (
              <Button
                variant="outlined"
                sx={{ mt: 2 }}
                onClick={handleRefreshExport}
                disabled={exportPending}
                data-testid="privacy-export-refresh-btn"
              >
                {t('pages.privacy.exportStatusRefresh')}
              </Button>
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

      {/* ── Erasure Confirmation Dialog (step-up, #1813) ── */}
      <StepUpConfirmDialog
        open={erasureDialogOpen}
        title={t('pages.privacy.erasureDialogTitle')}
        description={t('pages.privacy.erasureDialogText')}
        echoLabel={t('pages.privacy.erasureDialogEmailLabel')}
        echoHelper={t('pages.privacy.erasureDialogEmailHelper', { email: ownEmail })}
        expectedEcho={ownEmail}
        echoMatch="caseInsensitive"
        echoInputType="email"
        passwordLabel={t('pages.privacy.erasureDialogPasswordLabel')}
        passwordHelper={t('pages.privacy.erasureDialogPasswordHelper')}
        passwordRequiredMessage={t('pages.privacy.erasurePasswordRequired')}
        confirmLabel={t('pages.privacy.erasureDialogConfirm')}
        testIdPrefix="privacy-erasure"
        testIds={{
          echo: 'privacy-erasure-email',
          error: 'privacy-erasure-dialog-error',
          cancel: 'privacy-erasure-cancel-btn',
          confirm: 'privacy-erasure-confirm-btn',
        }}
        onConfirm={handleRequestErasure}
        onCancel={() => setErasureDialogOpen(false)}
      />
    </Box>
  );
}
