import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardActions from '@mui/material/CardActions';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import CircularProgress from '@mui/material/CircularProgress';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import EmptyState from '@/components/common/EmptyState';
import StepUpConfirmDialog from '@/components/common/StepUpConfirmDialog';
import type { StepUpConfirmation } from '@/components/common/StepUpConfirmDialog';
import OidcProviderFormDialog from '@/components/admin/OidcProviderFormDialog';
import type {
  OidcCreateFields,
  OidcFormSubmission,
  OidcUpdateFields,
} from '@/components/admin/OidcProviderFormDialog';
import OidcTestResultBody from '@/components/admin/OidcTestResultBody';
import {
  createOidcProvider,
  deleteOidcProvider,
  listOidcProviders,
  testOidcProvider,
  updateOidcProvider,
} from '@/api/endpoints/adminOidcProviders';
import { isApiError, parseApiError } from '@/api/errors';
import type { OidcProvider, OidcProviderTestResult } from '@/api/types';
import ErrorPage from '@/pages/ErrorPage';
import { useStepUpResume } from '@/hooks/useStepUpReauth';
import { toCredentialStepUpBody } from '@/utils/stepUp';
import { formatDateTime } from '@/utils/formatting';

/** A write waiting for the admin's step-up; the form stays open underneath. */
type PendingWrite =
  | { kind: 'create'; fields: OidcCreateFields }
  | { kind: 'update'; provider: OidcProvider; fields: OidcUpdateFields };

/**
 * Platform-admin page for the installation's OIDC / OAuth provider configurations (#1906).
 *
 * Reached from the platform tab of the settings page and guarded by `<RequirePlatformAdmin>`:
 * every request here is `require_platform_admin`, the list included, so a refused member has
 * nothing to read. Creating, deleting and every edit beyond `display_name` / `icon_url` go
 * through `StepUpConfirmDialog` for the act `oidc_provider_change` (#1883), bound to the
 * configuration's key — `new:<slug>` on create (#1884). A presentation-only edit saves
 * directly, as the API allows.
 *
 * The client secret is write-only: the list response has no such field and nothing on this
 * page renders it.
 *
 * Back from the identity provider after a fresh sign-in (#1815) the typed form values and the
 * chosen provider do not survive, so the three resume contexts are only consumed here; the
 * pending token is picked up when the admin repeats the act within its five minutes — for the
 * same target only (#1884).
 */
export default function AdminOidcProvidersPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();

  const [providers, setProviders] = useState<OidcProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<number | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useStepUpResume('oidc-provider-create');
  useStepUpResume('oidc-provider-update');
  useStepUpResume('oidc-provider-delete');

  // `undefined` = form closed, `null` = create, a provider = edit.
  const [formTarget, setFormTarget] = useState<OidcProvider | null | undefined>(undefined);
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);
  const [pendingWrite, setPendingWrite] = useState<PendingWrite | null>(null);
  const [toDelete, setToDelete] = useState<OidcProvider | null>(null);
  const [testing, setTesting] = useState<string | null>(null);
  const [testShown, setTestShown] = useState<{ provider: OidcProvider; result: OidcProviderTestResult } | null>(null);
  const [testError, setTestError] = useState<{ provider: OidcProvider; message: string } | null>(null);

  // Loading / error state is only ever set from the promise callbacks and the retry handler,
  // never synchronously in the effect body: a reload after a test must not flash the skeleton.
  useEffect(() => {
    let cancelled = false;
    listOidcProviders()
      .then((list) => {
        if (!cancelled) setProviders(list);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setLoadError(isApiError(err) ? err.statusCode : 0);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  const closeForm = useCallback(() => {
    setFormTarget(undefined);
    setFormError('');
    setPendingWrite(null);
  }, []);

  const handleFormSubmit = async (submission: OidcFormSubmission) => {
    setFormError('');
    if (submission.mode === 'create') {
      setPendingWrite({ kind: 'create', fields: submission.fields });
      return;
    }
    const provider = formTarget;
    if (!provider) return;
    if (submission.needsStepUp) {
      setPendingWrite({ kind: 'update', provider, fields: submission.fields });
      return;
    }
    // Presentation only (display name, icon): the API takes it without a step-up.
    setSaving(true);
    try {
      const updated = await updateOidcProvider(provider.key, submission.fields);
      setProviders((prev) => prev.map((p) => (p.key === updated.key ? updated : p)));
      closeForm();
      enqueueSnackbar(t('pages.admin.oidc.snack.saved'), { variant: 'success' });
    } catch (err) {
      setFormError(parseApiError(err));
    } finally {
      setSaving(false);
    }
  };

  // The admin's OWN step-up. A rejection propagates to the dialog, which shows it inside itself
  // and stays open.
  const handleConfirmWrite = async (credentials: StepUpConfirmation) => {
    if (!pendingWrite) return;
    const stepUp = toCredentialStepUpBody(credentials);
    if (pendingWrite.kind === 'create') {
      const created = await createOidcProvider({ ...pendingWrite.fields, ...stepUp });
      setProviders((prev) => [...prev, created]);
      closeForm();
      enqueueSnackbar(t('pages.admin.oidc.snack.created'), { variant: 'success' });
      return;
    }
    const updated = await updateOidcProvider(pendingWrite.provider.key, { ...pendingWrite.fields, ...stepUp });
    setProviders((prev) => prev.map((p) => (p.key === updated.key ? updated : p)));
    closeForm();
    enqueueSnackbar(t('pages.admin.oidc.snack.saved'), { variant: 'success' });
  };

  const handleConfirmDelete = async (credentials: StepUpConfirmation) => {
    if (!toDelete) return;
    const removed = toDelete;
    await deleteOidcProvider(removed.key, toCredentialStepUpBody(credentials));
    setProviders((prev) => prev.filter((p) => p.key !== removed.key));
    setToDelete(null);
    enqueueSnackbar(t('pages.admin.oidc.snack.deleted'), { variant: 'success' });
  };

  const handleTest = async (provider: OidcProvider) => {
    setTesting(provider.key);
    setTestError(null);
    try {
      const result = await testOidcProvider(provider.key);
      setTestShown({ provider, result });
      // A successful test stores the fetched discovery document: reflect the timestamp.
      setReloadToken((n) => n + 1);
    } catch (err) {
      setTestError({ provider, message: parseApiError(err) });
    } finally {
      setTesting(null);
    }
  };

  if (loading && loadError === null) return <LoadingSkeleton variant="form" />;
  if (loadError !== null) {
    return (
      <ErrorPage
        statusCode={loadError === 0 ? 503 : loadError}
        onRetry={() => {
          setLoading(true);
          setLoadError(null);
          setReloadToken((n) => n + 1);
        }}
        landmark={false}
      />
    );
  }

  const addButton = (
    <Button variant="contained" startIcon={<AddIcon />} onClick={() => setFormTarget(null)} data-testid="oidc-add">
      {t('pages.admin.oidc.add')}
    </Button>
  );

  return (
    <Box sx={{ mt: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <IconButton
          onClick={() => navigate('/settings#platform')}
          aria-label={t('pages.admin.oidc.back')}
          data-testid="oidc-back"
        >
          <ArrowBackIcon />
        </IconButton>
        <Box sx={{ flex: 1 }}>
          <PageTitle title={t('pages.admin.oidc.title')} action={addButton} sx={{ mb: 0 }} />
        </Box>
      </Box>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.admin.oidc.intro')}
      </Typography>
      <Alert severity="info" sx={{ mb: 3 }} data-testid="oidc-step-up-notice">
        {t('pages.admin.oidc.stepUpNotice')}
      </Alert>

      {providers.length === 0 ? (
        <EmptyState
          message={t('pages.admin.oidc.emptyTitle')}
          description={t('pages.admin.oidc.emptyDescription')}
          actionLabel={t('pages.admin.oidc.add')}
          onAction={() => setFormTarget(null)}
        />
      ) : (
        <Box
          component="ul"
          sx={{
            listStyle: 'none',
            m: 0,
            p: 0,
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' },
            gap: 2,
          }}
          data-testid="oidc-list"
        >
          {providers.map((p) => (
            <Box component="li" key={p.key} data-testid={`oidc-provider-${p.key}`}>
              <ProviderCard
                provider={p}
                testing={testing === p.key}
                onEdit={() => setFormTarget(p)}
                onDelete={() => setToDelete(p)}
                onTest={() => handleTest(p)}
              />
            </Box>
          ))}
        </Box>
      )}

      {formTarget !== undefined && (
        <OidcProviderFormDialog
          provider={formTarget}
          error={formError}
          pending={saving}
          onSubmit={handleFormSubmit}
          onCancel={closeForm}
        />
      )}

      {pendingWrite && (
        <StepUpConfirmDialog
          open
          title={t(pendingWrite.kind === 'create' ? 'pages.admin.oidc.stepUp.createTitle' : 'pages.admin.oidc.stepUp.updateTitle')}
          description={
            pendingWrite.kind === 'create'
              ? t('pages.admin.oidc.stepUp.createDescription', {
                  name: pendingWrite.fields.display_name,
                  slug: pendingWrite.fields.slug,
                })
              : t('pages.admin.oidc.stepUp.updateDescription', { name: pendingWrite.provider.display_name })
          }
          passwordLabel={t('pages.admin.oidc.stepUp.passwordLabel')}
          passwordHelper={t('pages.admin.oidc.stepUp.passwordHelper')}
          confirmLabel={t(pendingWrite.kind === 'create' ? 'pages.admin.oidc.stepUp.createConfirm' : 'pages.admin.oidc.stepUp.updateConfirm')}
          confirmColor="primary"
          stepUpAction="oidc_provider_change"
          stepUpTarget={pendingWrite.kind === 'create' ? `new:${pendingWrite.fields.slug}` : pendingWrite.provider.key}
          testIdPrefix={pendingWrite.kind === 'create' ? 'oidc-provider-create' : 'oidc-provider-update'}
          onConfirm={handleConfirmWrite}
          onCancel={() => setPendingWrite(null)}
        />
      )}

      {toDelete && (
        <StepUpConfirmDialog
          open
          title={t('pages.admin.oidc.stepUp.deleteTitle')}
          description={t('pages.admin.oidc.stepUp.deleteDescription', { name: toDelete.display_name })}
          echoLabel={t('pages.admin.oidc.stepUp.deleteEchoLabel')}
          echoHelper={t('pages.admin.oidc.stepUp.deleteEchoHelper', { slug: toDelete.slug })}
          expectedEcho={toDelete.slug}
          passwordLabel={t('pages.admin.oidc.stepUp.passwordLabel')}
          passwordHelper={t('pages.admin.oidc.stepUp.passwordHelper')}
          confirmLabel={t('pages.admin.oidc.stepUp.deleteConfirm')}
          stepUpAction="oidc_provider_change"
          stepUpTarget={toDelete.key}
          testIdPrefix="oidc-provider-delete"
          onConfirm={handleConfirmDelete}
          onCancel={() => setToDelete(null)}
        />
      )}

      {(testShown || testError) && (
        <Dialog
          open
          onClose={() => {
            setTestShown(null);
            setTestError(null);
          }}
          maxWidth="sm"
          fullWidth
          aria-labelledby="oidc-test-title"
          data-testid="oidc-test-dialog"
        >
          <DialogTitle id="oidc-test-title">
            {t('pages.admin.oidc.test.title', {
              name: (testShown ?? testError)!.provider.display_name,
            })}
          </DialogTitle>
          <DialogContent>
            {testShown && <OidcTestResultBody result={testShown.result} />}
            {testError && (
              <Alert severity="error" data-testid="oidc-test-error">
                {t('pages.admin.oidc.test.failedToRun')} {testError.message}
              </Alert>
            )}
          </DialogContent>
          <DialogActions>
            <Button
              onClick={() => {
                setTestShown(null);
                setTestError(null);
              }}
              data-testid="oidc-test-close"
            >
              {t('pages.admin.oidc.test.close')}
            </Button>
          </DialogActions>
        </Dialog>
      )}
    </Box>
  );
}

interface ProviderCardProps {
  provider: OidcProvider;
  testing: boolean;
  onEdit: () => void;
  onDelete: () => void;
  onTest: () => void;
}

function ProviderCard({ provider, testing, onEdit, onDelete, onTest }: ProviderCardProps) {
  const { t } = useTranslation();
  const fields: [string, string, string][] = [
    ['slug', t('pages.admin.oidc.list.slug'), provider.slug],
    [
      'type',
      t('pages.admin.oidc.list.type'),
      t(`pages.admin.oidc.types.${provider.provider_type}`, { defaultValue: provider.provider_type }),
    ],
    ['issuer', t('pages.admin.oidc.list.issuer'), provider.issuer_url],
    ['client-id', t('pages.admin.oidc.list.clientId'), provider.client_id],
    ['scopes', t('pages.admin.oidc.list.scopes'), provider.scopes.join(' ')],
    [
      'discovery',
      t('pages.admin.oidc.list.discovery'),
      !provider.auto_discover
        ? t('pages.admin.oidc.list.autoDiscoverOff')
        : provider.discovery_refreshed_at
          ? t('pages.admin.oidc.list.discoveryAt', { when: formatDateTime(provider.discovery_refreshed_at) })
          : t('pages.admin.oidc.list.discoveryNever'),
    ],
  ];

  return (
    <Card variant="outlined" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flex: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', mb: 1.5 }}>
          {provider.icon_url && (
            <Box
              component="img"
              src={provider.icon_url}
              alt=""
              referrerPolicy="no-referrer"
              sx={{ width: 24, height: 24, objectFit: 'contain' }}
            />
          )}
          <Typography variant="h6" component="h2" sx={{ wordBreak: 'break-word' }}>
            {provider.display_name}
          </Typography>
          <Chip
            size="small"
            color={provider.enabled ? 'success' : 'default'}
            label={provider.enabled ? t('pages.admin.oidc.list.enabled') : t('pages.admin.oidc.list.disabled')}
            data-testid={`oidc-status-${provider.key}`}
          />
        </Box>
        <Box component="dl" sx={{ m: 0, display: 'grid', gridTemplateColumns: 'max-content 1fr', columnGap: 2, rowGap: 0.75 }}>
          {fields.map(([id, label, value]) => (
            <Box key={id} sx={{ display: 'contents' }}>
              <Typography component="dt" variant="body2" color="text.secondary">
                {label}
              </Typography>
              <Typography
                component="dd"
                variant="body2"
                sx={{ m: 0, wordBreak: 'break-word', fontFamily: id === 'discovery' || id === 'type' ? undefined : 'monospace' }}
                data-testid={`oidc-field-${id}-${provider.key}`}
              >
                {value}
              </Typography>
            </Box>
          ))}
        </Box>
      </CardContent>
      <CardActions sx={{ justifyContent: 'flex-end', gap: 0.5, px: 2, pb: 1.5 }}>
        <Button
          size="medium"
          onClick={onTest}
          disabled={testing}
          startIcon={testing ? <CircularProgress size={16} /> : <FactCheckIcon />}
          aria-busy={testing}
          aria-label={
            testing
              ? `${t('pages.admin.oidc.actions.test', { name: provider.display_name })} – ${t('pages.admin.oidc.actions.testRunning')}`
              : t('pages.admin.oidc.actions.test', { name: provider.display_name })
          }
          data-testid={`oidc-test-${provider.key}`}
        >
          {testing ? t('pages.admin.oidc.actions.testRunning') : t('pages.admin.oidc.actions.testLabel')}
        </Button>
        <IconButton
          onClick={onEdit}
          aria-label={t('pages.admin.oidc.actions.edit', { name: provider.display_name })}
          data-testid={`oidc-edit-${provider.key}`}
        >
          <EditIcon />
        </IconButton>
        <IconButton
          color="error"
          onClick={onDelete}
          aria-label={t('pages.admin.oidc.actions.delete', { name: provider.display_name })}
          data-testid={`oidc-delete-${provider.key}`}
        >
          <DeleteIcon />
        </IconButton>
      </CardActions>
    </Card>
  );
}
