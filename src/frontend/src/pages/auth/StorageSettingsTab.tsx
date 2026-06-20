import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import FormControl from '@mui/material/FormControl';
import FormLabel from '@mui/material/FormLabel';
import RadioGroup from '@mui/material/RadioGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Radio from '@mui/material/Radio';
import Switch from '@mui/material/Switch';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Collapse from '@mui/material/Collapse';
import Divider from '@mui/material/Divider';
import Tooltip from '@mui/material/Tooltip';
import StorageIcon from '@mui/icons-material/Storage';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutlined';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutlined';
import HelpOutlineIcon from '@mui/icons-material/HelpOutlined';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { useNotification } from '@/hooks/useNotification';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import {
  getStorageSettings,
  updateStorageSettings,
  testStorageConnection,
  type StorageSettingsResponse,
  type StorageTestResponse,
} from '@/api/endpoints/adminSettings';

type Backend = 'local-fs' | 's3';

/** Editable, non-secret form state mirrored from the storage settings. */
interface StorageForm {
  backend: Backend;
  localFsRoot: string;
  localFsPublicBaseUrl: string;
  s3EndpointUrl: string;
  s3Region: string;
  s3Bucket: string;
  s3UsePathStyle: boolean;
  s3KmsKeyId: string;
  s3ForceTls: boolean;
}

function toForm(s: StorageSettingsResponse): StorageForm {
  return {
    backend: s.backend === 's3' ? 's3' : 'local-fs',
    localFsRoot: s.local_fs_root,
    localFsPublicBaseUrl: s.local_fs_public_base_url,
    s3EndpointUrl: s.s3_endpoint_url,
    s3Region: s.s3_region,
    s3Bucket: s.s3_bucket,
    s3UsePathStyle: s.s3_use_path_style,
    s3KmsKeyId: s.s3_kms_key_id,
    s3ForceTls: s.s3_force_tls,
  };
}

/** Responsive 2-column grid, collapses to 1 column on xs/sm. */
const GRID_2COL = {
  display: 'grid',
  gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
  gap: 2,
} as const;

/**
 * NFR-013 §4.1 — admin-only "Storage" settings section.
 *
 * Lets the operator choose the active object-storage backend (local filesystem
 * or S3-compatible) and edit its non-secret configuration. The S3 access key /
 * secret are NOT editable here: per NFR-013 §4.1 they come exclusively from the
 * environment / External Secrets Operator. The UI only reports their presence
 * and offers a non-destructive connection test (§4.2 health_check).
 *
 * Per AC-04 the rest of the app references no bucket/backend; this admin surface
 * is the single, deliberate exception where the backend is configured.
 */
export default function StorageSettingsTab() {
  const { t } = useTranslation();
  const notify = useNotification();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [settings, setSettings] = useState<StorageSettingsResponse | null>(null);
  const [form, setForm] = useState<StorageForm | null>(null);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<StorageTestResponse | null>(null);
  const [credentialsExpanded, setCredentialsExpanded] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(false);
    try {
      const s = await getStorageSettings();
      setSettings(s);
      setForm(toForm(s));
    } catch {
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const sourceChip = useCallback(
    (source: string | undefined) => {
      if (source === 'db') {
        return <Chip size="small" color="primary" label={t('storageSettings.sourceDb')} sx={{ mt: 0.5 }} />;
      }
      return <Chip size="small" label={t('storageSettings.sourceEnv')} sx={{ mt: 0.5 }} />;
    },
    [t],
  );

  const buildPayload = useCallback(() => {
    if (!form) return {};
    return {
      backend: form.backend,
      local_fs_root: form.localFsRoot,
      local_fs_public_base_url: form.localFsPublicBaseUrl,
      s3_endpoint_url: form.s3EndpointUrl,
      s3_region: form.s3Region,
      s3_bucket: form.s3Bucket,
      s3_use_path_style: form.s3UsePathStyle,
      s3_kms_key_id: form.s3KmsKeyId,
      s3_force_tls: form.s3ForceTls,
    };
  }, [form]);

  const handleSave = useCallback(async () => {
    if (!form) return;
    setSaving(true);
    try {
      const resp = await updateStorageSettings(buildPayload());
      setSettings(resp);
      setForm(toForm(resp));
      setTestResult(null);
      notify.success(t('storageSettings.saveSuccess'));
    } catch {
      notify.error(t('storageSettings.saveError'));
    } finally {
      setSaving(false);
    }
  }, [form, buildPayload, notify, t]);

  const handleTest = useCallback(async () => {
    if (!form) return;
    setTesting(true);
    setTestResult(null);
    try {
      const result = await testStorageConnection(buildPayload());
      setTestResult(result);
    } catch {
      notify.error(t('storageSettings.testError'));
    } finally {
      setTesting(false);
    }
  }, [form, buildPayload, notify, t]);

  const setField = useCallback(<K extends keyof StorageForm>(key: K, value: StorageForm[K]) => {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
    setTestResult(null);
  }, []);

  // The configured target region is surfaced for the DSGVO §6.5 hint.
  const targetRegionLabel = useMemo(() => {
    if (!form) return '';
    if (form.backend === 's3') {
      return form.s3Region || t('storageSettings.regionUnknown');
    }
    return t('storageSettings.regionLocal');
  }, [form, t]);

  // Whether both S3 credentials are present in the environment.
  const credentialsOk = useMemo(
    () =>
      settings !== null &&
      settings.s3_access_key_id_configured &&
      settings.s3_secret_access_key_configured,
    [settings],
  );

  if (loading) {
    return <LoadingSkeleton variant="form" rows={6} />;
  }
  if (loadError || !form || !settings) {
    return (
      <Alert severity="error" action={<Button onClick={() => void load()}>{t('common.retry')}</Button>}>
        {t('storageSettings.loadError')}
      </Alert>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* ── Panel 1: Header + DSGVO region info ── */}
      <Card variant="outlined">
        <CardContent sx={{ p: { xs: 2, md: 3 } }}>
          <Typography
            variant="h6"
            sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}
          >
            <StorageIcon fontSize="small" aria-hidden="true" />
            {t('storageSettings.title')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2.5 }}>
            {t('storageSettings.intro')}
          </Typography>

          {/* DSGVO §6.5 — surface the configured target region with context. */}
          <Alert
            severity="info"
            sx={{ mb: 0 }}
            icon={<InfoOutlinedIcon fontSize="inherit" />}
          >
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5 }}>
              <span>{t('storageSettings.targetRegion', { region: targetRegionLabel })}</span>
              <Tooltip
                title={t('storageSettings.targetRegionHelp')}
                placement="top"
                arrow
                enterDelay={300}
              >
                <Box
                  component="span"
                  tabIndex={0}
                  sx={{ display: 'inline-flex', alignItems: 'center', cursor: 'help', ml: 0.5 }}
                  aria-label={t('storageSettings.targetRegionHelp')}
                >
                  <HelpOutlineIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
                </Box>
              </Tooltip>
            </Box>
          </Alert>
        </CardContent>
      </Card>

      {/* ── Panel 2: Backend selection ── */}
      <Card variant="outlined">
        <CardContent component="fieldset" sx={{ border: 'none', p: { xs: 2, md: 3 }, m: 0 }}>
          <Typography component="legend" variant="subtitle1" sx={{ mb: 0.5, fontWeight: 600 }}>
            {t('storageSettings.backendLabel')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('storageSettings.backendDesc')}
          </Typography>

          <FormControl sx={{ width: '100%' }}>
            <FormLabel id="storage-backend-label" sx={{ display: 'none' }}>
              {t('storageSettings.backendLabel')}
            </FormLabel>
            <RadioGroup
              aria-labelledby="storage-backend-label"
              value={form.backend}
              onChange={(e) => setField('backend', e.target.value as Backend)}
              sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}
            >
              {/* Local-FS option with description */}
              <Box
                sx={{
                  border: 1,
                  borderColor: form.backend === 'local-fs' ? 'primary.main' : 'divider',
                  borderRadius: 1,
                  p: 1.5,
                  bgcolor: form.backend === 'local-fs' ? 'action.selected' : 'transparent',
                  cursor: 'pointer',
                }}
                onClick={() => setField('backend', 'local-fs')}
              >
                <FormControlLabel
                  value="local-fs"
                  control={<Radio data-testid="storage-backend-local-fs" />}
                  label={
                    <Box>
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        {t('storageSettings.backendLocalFs')}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {t('storageSettings.backendLocalFsDesc')}
                      </Typography>
                    </Box>
                  }
                  sx={{ m: 0, width: '100%' }}
                />
              </Box>

              {/* S3 option with description */}
              <Box
                sx={{
                  border: 1,
                  borderColor: form.backend === 's3' ? 'primary.main' : 'divider',
                  borderRadius: 1,
                  p: 1.5,
                  bgcolor: form.backend === 's3' ? 'action.selected' : 'transparent',
                  cursor: 'pointer',
                }}
                onClick={() => setField('backend', 's3')}
              >
                <FormControlLabel
                  value="s3"
                  control={<Radio data-testid="storage-backend-s3" />}
                  label={
                    <Box>
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        {t('storageSettings.backendS3')}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {t('storageSettings.backendS3Desc')}
                      </Typography>
                    </Box>
                  }
                  sx={{ m: 0, width: '100%' }}
                />
              </Box>
            </RadioGroup>
            <Box sx={{ mt: 1 }}>{sourceChip(settings.source_backend)}</Box>
          </FormControl>
        </CardContent>
      </Card>

      {/* ── Panel 3a: Local-FS fields ── */}
      {form.backend === 'local-fs' && (
        <Card variant="outlined">
          <CardContent
            component="fieldset"
            sx={{ border: 'none', p: { xs: 2, md: 3 }, m: 0 }}
            data-testid="storage-local-fs-fields"
          >
            <Typography component="legend" variant="subtitle1" sx={{ mb: 0.5, fontWeight: 600 }}>
              {t('storageSettings.backendLocalFs')}
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 1.5 }}>
              <Box>
                <TextField
                  fullWidth
                  label={t('storageSettings.localFsRoot')}
                  value={form.localFsRoot}
                  onChange={(e) => setField('localFsRoot', e.target.value)}
                  placeholder="/data/attachments"
                  helperText={t('storageSettings.localFsRootHelper')}
                  slotProps={{ htmlInput: { 'aria-describedby': 'local-fs-root-help' } }}
                  data-testid="storage-local-fs-root"
                />
                {sourceChip(settings.source_local_fs_root)}
              </Box>
              <Box>
                <TextField
                  fullWidth
                  label={t('storageSettings.localFsPublicBaseUrl')}
                  value={form.localFsPublicBaseUrl}
                  onChange={(e) => setField('localFsPublicBaseUrl', e.target.value)}
                  placeholder="https://media.meine-domain.de"
                  helperText={t('storageSettings.localFsPublicBaseUrlHelper')}
                  data-testid="storage-local-fs-public-base-url"
                />
                {sourceChip(settings.source_local_fs_public_base_url)}
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* ── Panel 3b: S3 fields ── */}
      {form.backend === 's3' && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }} data-testid="storage-s3-fields">

          {/* S3 connection basics */}
          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: { xs: 2, md: 3 }, m: 0 }}>
              <Typography component="legend" variant="subtitle1" sx={{ mb: 0.5, fontWeight: 600 }}>
                {t('storageSettings.s3SectionBasic')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('storageSettings.s3SectionBasicDesc')}
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                <Box>
                  <TextField
                    fullWidth
                    label={t('storageSettings.s3EndpointUrl')}
                    value={form.s3EndpointUrl}
                    onChange={(e) => setField('s3EndpointUrl', e.target.value)}
                    placeholder="https://s3.eu-central-1.amazonaws.com"
                    helperText={t('storageSettings.s3EndpointUrlHelper')}
                    data-testid="storage-s3-endpoint-url"
                  />
                  {sourceChip(settings.source_s3_endpoint_url)}
                </Box>

                <Box sx={GRID_2COL}>
                  <Box>
                    <TextField
                      fullWidth
                      label={t('storageSettings.s3Region')}
                      value={form.s3Region}
                      onChange={(e) => setField('s3Region', e.target.value)}
                      placeholder="eu-central-1"
                      helperText={t('storageSettings.s3RegionHelper')}
                      data-testid="storage-s3-region"
                    />
                    {sourceChip(settings.source_s3_region)}
                  </Box>
                  <Box>
                    <TextField
                      fullWidth
                      label={t('storageSettings.s3Bucket')}
                      value={form.s3Bucket}
                      onChange={(e) => setField('s3Bucket', e.target.value)}
                      helperText={t('storageSettings.s3BucketHelper')}
                      data-testid="storage-s3-bucket"
                    />
                    {sourceChip(settings.source_s3_bucket)}
                  </Box>
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* S3 advanced options */}
          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: { xs: 2, md: 3 }, m: 0 }}>
              <Typography component="legend" variant="subtitle1" sx={{ mb: 0.5, fontWeight: 600 }}>
                {t('storageSettings.s3SectionAdvanced')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('storageSettings.s3SectionAdvancedDesc')}
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {/* Path-style toggle with inline help */}
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={form.s3UsePathStyle}
                          onChange={(e) => setField('s3UsePathStyle', e.target.checked)}
                          data-testid="storage-s3-use-path-style"
                        />
                      }
                      label={t('storageSettings.s3UsePathStyleLabel')}
                      sx={{ m: 0 }}
                    />
                    <Tooltip
                      title={t('storageSettings.s3UsePathStyleHelper')}
                      placement="top"
                      arrow
                      enterDelay={300}
                    >
                      <Box
                        component="span"
                        tabIndex={0}
                        sx={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          cursor: 'help',
                          color: 'text.secondary',
                        }}
                        aria-label={t('storageSettings.s3UsePathStyleHelper')}
                      >
                        <HelpOutlineIcon sx={{ fontSize: 16 }} />
                      </Box>
                    </Tooltip>
                  </Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', ml: 5.5, mt: 0.25 }}>
                    {t('storageSettings.s3UsePathStyleHelper')}
                  </Typography>
                </Box>

                <Divider />

                {/* Force-TLS toggle with inline help */}
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={form.s3ForceTls}
                          onChange={(e) => setField('s3ForceTls', e.target.checked)}
                          data-testid="storage-s3-force-tls"
                        />
                      }
                      label={t('storageSettings.s3ForceTlsLabel')}
                      sx={{ m: 0 }}
                    />
                    <Tooltip
                      title={t('storageSettings.s3ForceTlsHelper')}
                      placement="top"
                      arrow
                      enterDelay={300}
                    >
                      <Box
                        component="span"
                        tabIndex={0}
                        sx={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          cursor: 'help',
                          color: 'text.secondary',
                        }}
                        aria-label={t('storageSettings.s3ForceTlsHelper')}
                      >
                        <HelpOutlineIcon sx={{ fontSize: 16 }} />
                      </Box>
                    </Tooltip>
                  </Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', ml: 5.5, mt: 0.25 }}>
                    {t('storageSettings.s3ForceTlsHelper')}
                  </Typography>
                </Box>

                <Divider />

                {/* KMS Key — optional, last */}
                <Box>
                  <TextField
                    fullWidth
                    label={t('storageSettings.s3KmsKeyId')}
                    value={form.s3KmsKeyId}
                    onChange={(e) => setField('s3KmsKeyId', e.target.value)}
                    placeholder="arn:aws:kms:eu-central-1:123456789:key/..."
                    helperText={t('storageSettings.s3KmsKeyIdHelper')}
                    data-testid="storage-s3-kms-key-id"
                  />
                  {sourceChip(settings.source_s3_kms_key_id)}
                </Box>
              </Box>
            </CardContent>
          </Card>

          {/* S3 Credentials — prominent, clearly explains no input field */}
          <Card
            variant="outlined"
            sx={{ borderColor: credentialsOk ? 'success.light' : 'warning.light' }}
          >
            <CardContent sx={{ p: { xs: 2, md: 3 } }}>
              <Typography variant="subtitle1" sx={{ mb: 0.5, fontWeight: 600 }}>
                {t('storageSettings.credentialsSectionTitle')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('storageSettings.credentialsSectionDesc')}
              </Typography>

              {/* Status indicator */}
              <Alert
                severity={credentialsOk ? 'success' : 'warning'}
                icon={credentialsOk ? <CheckCircleOutlineIcon fontSize="inherit" /> : <ErrorOutlineIcon fontSize="inherit" />}
                data-testid="storage-s3-credentials-hint"
                sx={{ mb: 1.5 }}
              >
                <AlertTitle>
                  {credentialsOk
                    ? t('storageSettings.credentialsConfigured')
                    : t('storageSettings.credentialsMissing')}
                </AlertTitle>
              </Alert>

              {/* Expandable "why no password field?" explanation */}
              <Button
                variant="text"
                size="small"
                startIcon={<HelpOutlineIcon fontSize="small" />}
                onClick={() => setCredentialsExpanded((v) => !v)}
                aria-expanded={credentialsExpanded}
                sx={{ textTransform: 'none', px: 0, color: 'text.secondary' }}
              >
                {t('storageSettings.credentialsWhyNotHere')}
              </Button>
              <Collapse in={credentialsExpanded}>
                <Alert severity="info" icon={false} sx={{ mt: 1, py: 1 }}>
                  <Typography variant="body2">
                    {t('storageSettings.credentialsWhyNotHereExplain')}
                  </Typography>
                </Alert>
              </Collapse>
            </CardContent>
          </Card>
        </Box>
      )}

      {/* ── Test result ── */}
      {testResult && (
        <Alert
          severity={testResult.success ? 'success' : 'error'}
          icon={
            testResult.success ? (
              <CheckCircleOutlineIcon fontSize="inherit" />
            ) : (
              <ErrorOutlineIcon fontSize="inherit" />
            )
          }
          data-testid="storage-test-result"
        >
          <AlertTitle>
            {testResult.success
              ? t('storageSettings.testResultSuccess')
              : t('storageSettings.testResultFailed')}
          </AlertTitle>
          {testResult.message}
        </Alert>
      )}

      {/* ── Actions ── */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
        <Button
          variant="outlined"
          onClick={() => void handleTest()}
          disabled={testing || saving}
          aria-busy={testing}
          startIcon={testing ? <CircularProgress size={16} color="inherit" /> : undefined}
          data-testid="storage-test-button"
        >
          {testing ? t('storageSettings.testingButton') : t('storageSettings.testButton')}
        </Button>
        <Button
          variant="contained"
          onClick={() => void handleSave()}
          disabled={saving || testing}
          aria-busy={saving}
          startIcon={saving ? <CircularProgress size={16} color="inherit" /> : undefined}
          data-testid="storage-save-button"
        >
          {t('storageSettings.saveButton')}
        </Button>
      </Box>
    </Box>
  );
}
