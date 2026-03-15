import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogActions from '@mui/material/DialogActions';
import CircularProgress from '@mui/material/CircularProgress';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import {
  getSystemSettings,
  updateHaSettings,
  testHaConnection,
  clearHaSettings,
} from '@/api/endpoints/adminSettings';
import type { HASettingsResponse, HATestResponse } from '@/api/endpoints/adminSettings';

export default function AdminSettingsPage() {
  const { t } = useTranslation();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [resetOpen, setResetOpen] = useState(false);

  const [haUrl, setHaUrl] = useState('');
  const [haAccessToken, setHaAccessToken] = useState('');
  const [haTimeout, setHaTimeout] = useState('10');

  const [maskedToken, setMaskedToken] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [sourceToken, setSourceToken] = useState('');
  const [sourceTimeout, setSourceTimeout] = useState('');

  const [testResult, setTestResult] = useState<HATestResponse | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [resetDone, setResetDone] = useState(false);
  const [error, setError] = useState('');

  const loadSettings = useCallback(async () => {
    try {
      setLoading(true);
      const resp = await getSystemSettings();
      const ha: HASettingsResponse = resp.home_assistant;
      setHaUrl(ha.ha_url || '');
      setHaTimeout(String(ha.ha_timeout));
      setMaskedToken(ha.ha_access_token_masked);
      setSourceUrl(ha.source_ha_url);
      setSourceToken(ha.source_ha_access_token);
      setSourceTimeout(ha.source_ha_timeout);
      setHaAccessToken('');
    } catch {
      setError(t('errors.network'));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await testHaConnection({
        ha_url: haUrl || null,
        ha_access_token: haAccessToken || null,
        ha_timeout: haTimeout ? Number(haTimeout) : null,
      });
      setTestResult(result);
    } catch {
      setTestResult({ success: false, message: t('errors.network') });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveSuccess(false);
    setError('');
    try {
      await updateHaSettings({
        ha_url: haUrl || null,
        ha_access_token: haAccessToken || null,
        ha_timeout: haTimeout ? Number(haTimeout) : null,
      });
      setSaveSuccess(true);
      await loadSettings();
    } catch {
      setError(t('errors.server'));
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    setResetOpen(false);
    setResetDone(false);
    try {
      await clearHaSettings();
      setResetDone(true);
      await loadSettings();
    } catch {
      setError(t('errors.server'));
    }
  };

  const sourceLabel = (source: string) => {
    switch (source) {
      case 'db':
        return t('pages.admin.sourceDb');
      case 'env':
        return t('pages.admin.sourceEnv');
      default:
        return t('pages.admin.sourceDefault');
    }
  };

  const sourceColor = (source: string): 'primary' | 'default' | 'secondary' => {
    if (source === 'db') return 'primary';
    if (source === 'env') return 'secondary';
    return 'default';
  };

  if (loading) {
    return (
      <Box sx={{ maxWidth: 700, mx: 'auto', py: 3 }}>
        <LoadingSkeleton variant="card" />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 700, mx: 'auto', py: 3 }}>
      <PageTitle title={t('pages.admin.title')} />

      <Card>
        <CardContent>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
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
              <Chip
                size="small"
                label={sourceLabel(sourceUrl)}
                color={sourceColor(sourceUrl)}
                sx={{ mt: 0.5 }}
              />
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
              <Chip
                size="small"
                label={sourceLabel(sourceToken)}
                color={sourceColor(sourceToken)}
                sx={{ mt: 0.5 }}
              />
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
              <Chip
                size="small"
                label={sourceLabel(sourceTimeout)}
                color={sourceColor(sourceTimeout)}
                sx={{ mt: 0.5 }}
              />
            </Box>
          </Box>

          {testResult && (
            <Alert
              severity={testResult.success ? 'success' : 'error'}
              icon={testResult.success ? <CheckCircleIcon /> : <ErrorIcon />}
              sx={{ mt: 2 }}
              data-testid="test-result-alert"
            >
              {testResult.message}
              {testResult.ha_version && ` (v${testResult.ha_version})`}
            </Alert>
          )}

          {saveSuccess && (
            <Alert severity="success" sx={{ mt: 2 }} data-testid="save-success-alert">
              {t('pages.admin.saved')}
            </Alert>
          )}

          {resetDone && (
            <Alert severity="info" sx={{ mt: 2 }}>
              {t('pages.admin.resetDone')}
            </Alert>
          )}

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}

          <Box sx={{ display: 'flex', gap: 1, mt: 3, flexWrap: 'wrap', alignItems: 'center' }}>
            <Button
              variant="outlined"
              onClick={handleTest}
              disabled={testing || !haUrl}
              startIcon={testing ? <CircularProgress size={16} /> : undefined}
              data-testid="test-connection-btn"
            >
              {t('pages.admin.testConnection')}
            </Button>
            <Button
              variant="contained"
              onClick={handleSave}
              disabled={saving}
              startIcon={saving ? <CircularProgress size={16} /> : undefined}
              data-testid="save-settings-btn"
            >
              {t('common.save')}
            </Button>
            <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />
            <Button
              variant="text"
              color="warning"
              onClick={() => setResetOpen(true)}
              data-testid="reset-settings-btn"
            >
              {t('pages.admin.resetToDefaults')}
            </Button>
          </Box>
        </CardContent>
      </Card>

      <Dialog open={resetOpen} onClose={() => setResetOpen(false)}>
        <DialogTitle>{t('pages.admin.resetToDefaults')}</DialogTitle>
        <DialogContent>
          <DialogContentText>{t('pages.admin.resetConfirm')}</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetOpen(false)}>{t('common.cancel')}</Button>
          <Button onClick={handleReset} color="warning">
            {t('common.confirm')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
