import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import DialogContentText from '@mui/material/DialogContentText';
import Divider from '@mui/material/Divider';
import CircularProgress from '@mui/material/CircularProgress';
import Tooltip from '@mui/material/Tooltip';
import Link from '@mui/material/Link';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import ErrorIcon from '@mui/icons-material/Error';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import OptionsLoadError from '@/components/common/OptionsLoadError';
import { captureHandledError } from '@/observability/errorTracking';
import {
  getSystemSettings,
  updateHaSettings,
  testHaConnection,
  clearHaSettings,
  updatePlantIdentificationSettings,
  testPlantIdentificationKey,
  clearPlantIdentificationSettings,
} from '@/api/endpoints/adminSettings';
import type { HATestResponse, PlantIdentificationTestResponse } from '@/api/endpoints/adminSettings';
import { RecognitionStatusCard } from '@/components/admin/RecognitionStatusCard';
import { PestRecognitionAdminCard } from '@/components/admin/PestRecognitionAdminCard';
import StorageSettingsTab from '../StorageSettingsTab';
import WeatherProvidersSettingsTab from '../WeatherProvidersSettingsTab';
import SettingsSection from './SettingsSection';
import { findSettingsSection, type SettingsGroupProps } from '@/config/settingsGroups';

/**
 * Group "Installation" — the operator's group (F-11). Everything here applies to
 * the whole installation rather than to the signed-in user: storage, weather
 * providers, and the instance-wide cards of the former `ha` tab (the Home
 * Assistant connection, the Pl@ntNet key, plant and pest recognition). The
 * shell shows the group only when `canManageInstanceSettings`, and every
 * section repeats that gate in `settingsGroups.ts`, so a section is never
 * offered to a member whose request would answer 403 (#1385, #1401).
 */
export default function InstallationSettingsGroup({ sections }: SettingsGroupProps) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();

  const storageSection = findSettingsSection(sections, 'storage');
  const weatherSection = findSettingsSection(sections, 'weather-providers');
  const haConnectionSection = findSettingsSection(sections, 'ha-connection');
  const plantIdentificationSection = findSettingsSection(sections, 'plant-identification');
  const recognitionSection = findSettingsSection(sections, 'recognition');
  // `GET /admin/settings` carries both the HA connection and the Pl@ntNet key; read it
  // only when one of the two cards is shown (the server answers 403 to anyone but an operator).
  const needsSystemSettings = Boolean(haConnectionSection || plantIdentificationSection);

  const [error, setError] = useState('');

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
  // A failed settings read is shown with a retry: empty fields would read as "not configured" (#3037).
  const [haLoadError, setHaLoadError] = useState(false);
  // Pl@ntNet (plant identification) settings state
  const [plantnetKey, setPlantnetKey] = useState('');
  const [plantnetMaskedKey, setPlantnetMaskedKey] = useState('');
  const [plantnetSource, setPlantnetSource] = useState('');
  const [plantnetTestResult, setPlantnetTestResult] = useState<PlantIdentificationTestResponse | null>(null);
  const [plantnetSaving, setPlantnetSaving] = useState(false);
  const [plantnetTesting, setPlantnetTesting] = useState(false);
  const [plantnetResetOpen, setPlantnetResetOpen] = useState(false);
  const [plantnetSaveSuccess, setPlantnetSaveSuccess] = useState(false);
  const [plantnetResetDone, setPlantnetResetDone] = useState(false);
  const [plantnetKeyVisible, setPlantnetKeyVisible] = useState(false);

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
      const pi = resp.plant_identification;
      setPlantnetMaskedKey(pi.plantnet_api_key_masked);
      setPlantnetSource(pi.source_plantnet_api_key);
      setPlantnetKey('');
      setHaLoaded(true);
      setHaLoadError(false);
    } catch (err) {
      captureHandledError(err, { source: 'InstallationSettingsGroup.systemSettings' });
      setHaLoadError(true);
    }
  }, []);

  useEffect(() => {
    if (needsSystemSettings && !haLoaded && !haLoadError) {
      loadHaSettings();
    }
  }, [needsSystemSettings, haLoaded, haLoadError, loadHaSettings]);

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

  const handlePlantnetSave = async () => {
    setPlantnetSaving(true);
    setPlantnetSaveSuccess(false);
    setPlantnetTestResult(null);
    try {
      await updatePlantIdentificationSettings({ plantnet_api_key: plantnetKey });
      setPlantnetSaveSuccess(true);
      await loadHaSettings();
    } catch {
      setError(t('errors.server'));
    } finally {
      setPlantnetSaving(false);
    }
  };

  const handlePlantnetTest = async () => {
    setPlantnetTesting(true);
    setPlantnetTestResult(null);
    try {
      const result = await testPlantIdentificationKey({
        plantnet_api_key: plantnetKey || null,
      });
      setPlantnetTestResult(result);
    } catch {
      setPlantnetTestResult({ success: false, message: t('errors.network') });
    } finally {
      setPlantnetTesting(false);
    }
  };

  const handlePlantnetReset = async () => {
    setPlantnetResetOpen(false);
    setPlantnetResetDone(false);
    try {
      await clearPlantIdentificationSettings();
      setPlantnetResetDone(true);
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

  const plantnetSourceLabel = (source: string) => {
    switch (source) {
      case 'db': return t('pages.admin.sourceDb');
      case 'env': return t('pages.admin.sourceEnv');
      default: return t('pages.admin.plantnetSourceNone');
    }
  };

  const plantnetSourceColor = (source: string): 'primary' | 'default' | 'secondary' => {
    if (source === 'db') return 'primary';
    if (source === 'env') return 'secondary';
    return 'default';
  };

  const haSourceColor = (source: string): 'primary' | 'default' | 'secondary' => {
    if (source === 'db') return 'primary';
    if (source === 'env') return 'secondary';
    return 'default';
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      {error && <Alert severity="error">{error}</Alert>}
      {haLoadError && needsSystemSettings && (
        <OptionsLoadError
          messageKey="errors.loadFailed"
          onRetry={() => void loadHaSettings()}
          data-testid="system-settings-load-error"
        />
      )}

      {/* NFR-013 */}
      {storageSection && (
        <SettingsSection section={storageSection}>
          <StorageSettingsTab />
        </SettingsSection>
      )}

      {/* REQ-046 — providers, fetch interval, fetch status and "fetch now" (F-14, #2934). */}
      {weatherSection && (
        <SettingsSection section={weatherSection}>
          <WeatherProvidersSettingsTab />
        </SettingsSection>
      )}

      {/* Home Assistant connection — installation-wide (one HA per instance). */}
      {haConnectionSection && (
        <SettingsSection section={haConnectionSection}>
            <Card variant="outlined">
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
        </SettingsSection>
      )}

      {/* Plant identification (Pl@ntNet) — instance-wide, REQ-029 Phase 1. Clearing
          the key removes identification for every user. */}
      {plantIdentificationSection && (
        <SettingsSection section={plantIdentificationSection}>
            <Card variant="outlined">
              <CardContent
                component="fieldset"
                sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}
              >
                <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                  {t('pages.admin.plantnetSection')}
                </Typography>

                {/* Intro text with clickable link to registration page */}
                <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                  {t('pages.admin.plantnetSectionHelperPre')}{' '}
                  <Link
                    href="https://my.plantnet.org"
                    target="_blank"
                    rel="noopener noreferrer"
                    underline="always"
                    sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.25 }}
                  >
                    my.plantnet.org
                    <OpenInNewIcon sx={{ fontSize: 13 }} aria-hidden="true" />
                  </Link>
                  {', '}
                  {t('pages.admin.plantnetSectionHelperPost')}
                </Typography>
                <Alert severity="info" icon={false} sx={{ mb: 2.5, py: 0.5 }}>
                  <Typography variant="body2">
                    {t('pages.admin.plantnetSectionEffect')}
                  </Typography>
                </Alert>

                <Box>
                  <TextField
                    fullWidth
                    type={plantnetKeyVisible ? 'text' : 'password'}
                    label={t('pages.admin.plantnetApiKey')}
                    value={plantnetKey}
                    onChange={(e) => {
                      setPlantnetKey(e.target.value);
                      setPlantnetSaveSuccess(false);
                      setPlantnetTestResult(null);
                    }}
                    placeholder={t('pages.admin.plantnetApiKeyPlaceholder')}
                    autoComplete="new-password"
                    helperText={
                      plantnetMaskedKey
                        ? `${t('pages.admin.plantnetApiKeyHelper')}: ${plantnetMaskedKey}`
                        : t('pages.admin.notConfigured')
                    }
                    slotProps={{
                      input: {
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton
                              aria-label={
                                plantnetKeyVisible
                                  ? t('pages.admin.plantnetHideKey')
                                  : t('pages.admin.plantnetShowKey')
                              }
                              onClick={() => setPlantnetKeyVisible((v) => !v)}
                              edge="end"
                              size="small"
                              data-testid="plantnet-key-visibility-toggle"
                            >
                              {plantnetKeyVisible ? (
                                <VisibilityOffIcon fontSize="small" />
                              ) : (
                                <VisibilityIcon fontSize="small" />
                              )}
                            </IconButton>
                          </InputAdornment>
                        ),
                      },
                    }}
                    data-testid="plantnet-key-field"
                  />
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, mt: 0.75 }}>
                    <Tooltip
                      title={t(`pages.admin.plantnetSourceTooltip.${plantnetSource || 'none'}`)}
                      arrow
                    >
                      <Chip
                        size="small"
                        label={plantnetSourceLabel(plantnetSource)}
                        color={plantnetSourceColor(plantnetSource)}
                        icon={<InfoOutlinedIcon />}
                        aria-label={`${t('pages.admin.plantnetSourceAriaPrefix')}: ${plantnetSourceLabel(plantnetSource)}`}
                        data-testid="plantnet-source-chip"
                      />
                    </Tooltip>
                  </Box>
                </Box>

                {plantnetTestResult && (
                  <Alert
                    severity={plantnetTestResult.success ? 'success' : 'error'}
                    icon={plantnetTestResult.success ? <CheckCircleIcon /> : <ErrorIcon />}
                    sx={{ mt: 2 }}
                    data-testid="plantnet-test-result-alert"
                  >
                    {plantnetTestResult.message}
                  </Alert>
                )}
                {plantnetSaveSuccess && (
                  <Alert severity="success" sx={{ mt: 2 }} data-testid="plantnet-save-success-alert">
                    {t('pages.admin.plantnetSaved')}
                  </Alert>
                )}
                {plantnetResetDone && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    {t('pages.admin.plantnetResetDone')}
                  </Alert>
                )}

                <Box sx={{ display: 'flex', gap: 1, mt: 3, flexWrap: 'wrap', alignItems: 'center' }}>
                  <Tooltip
                    title={
                      !plantnetKey && !plantnetMaskedKey
                        ? t('pages.admin.plantnetTestDisabledHint')
                        : ''
                    }
                    disableHoverListener={!!(plantnetKey || plantnetMaskedKey)}
                  >
                    <span>
                      <Button
                        variant="outlined"
                        onClick={handlePlantnetTest}
                        disabled={plantnetTesting || (!plantnetKey && !plantnetMaskedKey)}
                        startIcon={plantnetTesting ? <CircularProgress size={16} /> : undefined}
                        data-testid="plantnet-test-btn"
                      >
                        {t('pages.admin.plantnetTest')}
                      </Button>
                    </span>
                  </Tooltip>
                  <Button
                    variant="contained"
                    onClick={handlePlantnetSave}
                    disabled={plantnetSaving || !plantnetKey.trim()}
                    startIcon={plantnetSaving ? <CircularProgress size={16} /> : undefined}
                    data-testid="plantnet-save-btn"
                  >
                    {t('common.save')}
                  </Button>
                  <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />
                  <Button
                    variant="text"
                    color="warning"
                    onClick={() => setPlantnetResetOpen(true)}
                    disabled={plantnetSource !== 'db'}
                    data-testid="plantnet-reset-btn"
                  >
                    {t('pages.admin.plantnetReset')}
                  </Button>
                </Box>
              </CardContent>
            </Card>
        </SettingsSection>
      )}

            {/* Self-hosted DINOv2 recognition (REQ-029-A) and the pest few-shot index
                (REQ-044). Both are installation-wide admin surfaces, so both are gated
                (#1401).

                An earlier version of this comment called the recognition card
                "read-only, discloses no endpoint or credential" and left it visible to
                everyone. Both halves were wrong: it renders an acquire button that
                POSTs /admin/recognition/acquire, and GET /admin/recognition/status
                returns the inference service's internal URL. Those two routes now carry
                require_platform_admin, matching the admin/pests sibling that had it all
                along.

                The pest card's routes were already gated server-side; it was rendered to
                every member regardless, so its button looked live and answered 403 — the
                #1339 class. Gated here for the same reason, not because anything about
                it changed. */}
      {recognitionSection && (
        <SettingsSection section={recognitionSection}>
          <Box sx={{ display: 'grid', gap: 2 }}>
            <RecognitionStatusCard gridColumn="1 / -1" />
            <PestRecognitionAdminCard gridColumn="1 / -1" />
          </Box>
        </SettingsSection>
      )}

    {/* HA Reset Dialog */}
    <Dialog fullScreen={fullScreen} open={haResetOpen} onClose={() => setHaResetOpen(false)} data-testid="ha-reset-dialog" aria-labelledby="ha-reset-dialog-title">
      <DialogTitle id="ha-reset-dialog-title">{t('pages.admin.resetToDefaults')}</DialogTitle>
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

    {/* Pl@ntNet Reset Dialog */}
    <Dialog
      fullScreen={fullScreen}
      open={plantnetResetOpen}
      onClose={() => setPlantnetResetOpen(false)}
      aria-labelledby="plantnet-reset-dialog-title"
      aria-describedby="plantnet-reset-dialog-desc"
      data-testid="plantnet-reset-dialog"
    >
      <DialogTitle id="plantnet-reset-dialog-title">
        {t('pages.admin.plantnetResetDialogTitle')}
      </DialogTitle>
      <DialogContent>
        <DialogContentText id="plantnet-reset-dialog-desc">
          {t('pages.admin.plantnetResetConfirm')}
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        {/* Abbrechen hat Fokus-Priorität bei destruktiven Dialogen */}
        <Button onClick={() => setPlantnetResetOpen(false)} autoFocus data-testid="plantnet-reset-cancel-btn">
          {t('common.cancel')}
        </Button>
        <Button onClick={handlePlantnetReset} color="warning" data-testid="plantnet-reset-confirm-btn">
          {t('common.confirm')}
        </Button>
      </DialogActions>
    </Dialog>
    </Box>
  );
}
