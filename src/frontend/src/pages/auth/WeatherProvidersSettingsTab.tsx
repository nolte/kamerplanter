import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import InputAdornment from '@mui/material/InputAdornment';
import IconButton from '@mui/material/IconButton';
import CloudIcon from '@mui/icons-material/Cloud';
import ScienceIcon from '@mui/icons-material/Science';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutlined';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutlined';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import { useNotification } from '@/hooks/useNotification';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import {
  getWeatherProviders,
  putWeatherProviders,
  testWeatherProvider,
} from '@/api/endpoints/adminWeatherProviders';
import type {
  WeatherProvidersResponse,
  WeatherProvidersUpdate,
  WeatherProviderTestResponse,
} from '@/api/types';

/** The masked placeholder shown when a global key is stored (matches backend). */
const MASKED_PLACEHOLDER = '••••';

/** Per-provider payload keys, keyed by the provider `source_name`. */
const ENABLED_KEY: Record<string, keyof WeatherProvidersUpdate> = {
  'open-meteo': 'open_meteo_enabled',
  dwd: 'dwd_enabled',
  openweathermap: 'openweathermap_enabled',
};
const BASE_URL_KEY: Record<string, keyof WeatherProvidersUpdate> = {
  'open-meteo': 'open_meteo_base_url',
  dwd: 'dwd_base_url',
  openweathermap: 'openweathermap_base_url',
};

interface ProviderForm {
  sourceName: string;
  enabled: boolean;
  baseUrl: string;
  attribution: string;
}

interface WeatherForm {
  providers: ProviderForm[];
  /** New plaintext OWM key; empty = unchanged (keep stored ciphertext). */
  globalOwmKey: string;
  fetchTimeoutS: number | '';
  defaultPublicSource: string;
}

interface TestState {
  loading: boolean;
  result: WeatherProviderTestResponse | null;
}

function toForm(s: WeatherProvidersResponse): WeatherForm {
  return {
    providers: s.providers.map((p) => ({
      sourceName: p.source_name,
      enabled: p.enabled,
      baseUrl: p.base_url,
      attribution: p.attribution,
    })),
    globalOwmKey: '',
    fetchTimeoutS: s.fetch_timeout_s,
    defaultPublicSource: s.default_public_source,
  };
}

/**
 * REQ-046 follow-up — platform-admin "Weather services" settings tab.
 *
 * Instance-wide defaults for the public weather providers (Open-Meteo, DWD,
 * OpenWeatherMap): per-provider enable + base-URL override, a connection test,
 * the fetch timeout and the default public source, plus the global OpenWeatherMap
 * fallback key. Mirrors {@link StorageSettingsTab}: the secret is never returned
 * (only a presence flag), the field is masked, and an empty value keeps the
 * stored ciphertext unchanged.
 */
export default function WeatherProvidersSettingsTab() {
  const { t } = useTranslation();
  const notify = useNotification();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [settings, setSettings] = useState<WeatherProvidersResponse | null>(null);
  const [form, setForm] = useState<WeatherForm | null>(null);
  const [saving, setSaving] = useState(false);
  const [keyVisible, setKeyVisible] = useState(false);
  const [tests, setTests] = useState<Record<string, TestState>>({});

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(false);
    try {
      const s = await getWeatherProviders();
      setSettings(s);
      setForm(toForm(s));
      setTests({});
    } catch {
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const setProviderField = useCallback(
    <K extends keyof ProviderForm>(sourceName: string, key: K, value: ProviderForm[K]) => {
      setForm((prev) =>
        prev
          ? {
              ...prev,
              providers: prev.providers.map((p) =>
                p.sourceName === sourceName ? { ...p, [key]: value } : p,
              ),
            }
          : prev,
      );
    },
    [],
  );

  const setFormField = useCallback(<K extends keyof WeatherForm>(key: K, value: WeatherForm[K]) => {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
  }, []);

  const buildPayload = useCallback((): WeatherProvidersUpdate => {
    const payload: WeatherProvidersUpdate = {
      // Empty string = "unchanged" — the backend keeps the stored ciphertext.
      openweathermap_global_api_key: form?.globalOwmKey ?? '',
      fetch_timeout_s: form && form.fetchTimeoutS !== '' ? Number(form.fetchTimeoutS) : null,
      default_public_source:
        (form?.defaultPublicSource as WeatherProvidersUpdate['default_public_source']) ?? null,
    };
    form?.providers.forEach((p) => {
      const enabledKey = ENABLED_KEY[p.sourceName];
      const baseUrlKey = BASE_URL_KEY[p.sourceName];
      if (enabledKey) (payload[enabledKey] as boolean) = p.enabled;
      // Empty base URL clears the override → the env default applies again.
      if (baseUrlKey) (payload[baseUrlKey] as string) = p.baseUrl;
    });
    return payload;
  }, [form]);

  const handleSave = useCallback(async () => {
    if (!form) return;
    setSaving(true);
    try {
      const resp = await putWeatherProviders(buildPayload());
      setSettings(resp);
      setForm(toForm(resp));
      setTests({});
      setKeyVisible(false);
      notify.success(t('pages.weatherProviders.saveSuccess'));
    } catch {
      notify.error(t('pages.weatherProviders.saveError'));
    } finally {
      setSaving(false);
    }
  }, [form, buildPayload, notify, t]);

  const handleTest = useCallback(
    async (sourceName: string) => {
      setTests((prev) => ({ ...prev, [sourceName]: { loading: true, result: null } }));
      try {
        const result = await testWeatherProvider(sourceName);
        setTests((prev) => ({ ...prev, [sourceName]: { loading: false, result } }));
      } catch {
        notify.error(t('pages.weatherProviders.testError'));
        setTests((prev) => ({ ...prev, [sourceName]: { loading: false, result: null } }));
      }
    },
    [notify, t],
  );

  const providerName = useCallback(
    (sourceName: string) => t(`enums.weatherSource.${sourceName}`, { defaultValue: sourceName }),
    [t],
  );

  const sourceOptions = useMemo(
    () => form?.providers.map((p) => p.sourceName) ?? [],
    [form],
  );

  if (loading) {
    return <LoadingSkeleton variant="form" rows={6} />;
  }
  if (loadError || !form || !settings) {
    return (
      <Alert severity="error" action={<Button onClick={() => void load()}>{t('common.retry')}</Button>}>
        {t('pages.weatherProviders.loadError')}
      </Alert>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }} data-testid="weather-providers-tab">
      {/* ── Header / intro ── */}
      <Card variant="outlined">
        <CardContent sx={{ p: { xs: 2, md: 3 } }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
            <CloudIcon fontSize="small" aria-hidden="true" />
            {t('pages.weatherProviders.title')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('pages.weatherProviders.intro')}
          </Typography>
        </CardContent>
      </Card>

      {/* ── Per-provider cards ── */}
      {form.providers.map((p) => {
        const test = tests[p.sourceName];
        return (
          <Card variant="outlined" key={p.sourceName} data-testid={`weather-provider-${p.sourceName}`}>
            <CardContent component="fieldset" sx={{ border: 'none', p: { xs: 2, md: 3 }, m: 0 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1 }}>
                <Typography component="legend" variant="subtitle1" sx={{ fontWeight: 600 }}>
                  {providerName(p.sourceName)}
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={p.enabled}
                      onChange={(e) => setProviderField(p.sourceName, 'enabled', e.target.checked)}
                      slotProps={{ input: { 'aria-label': t('pages.weatherProviders.enableToggle') } }}
                      data-testid={`weather-provider-enabled-${p.sourceName}`}
                    />
                  }
                  label={t('pages.weatherProviders.enableToggle')}
                  sx={{ m: 0 }}
                />
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                {t('pages.weatherProviders.enableToggleHelper')}
              </Typography>

              <Box sx={{ mt: 2 }}>
                <TextField
                  fullWidth
                  label={t('pages.weatherProviders.baseUrl')}
                  value={p.baseUrl}
                  onChange={(e) => setProviderField(p.sourceName, 'baseUrl', e.target.value)}
                  helperText={t('pages.weatherProviders.baseUrlHelper')}
                  data-testid={`weather-provider-base-url-${p.sourceName}`}
                />
              </Box>

              {p.attribution && (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                  <strong>{t('pages.weatherProviders.attributionLabel')}:</strong> {p.attribution}
                </Typography>
              )}

              <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => void handleTest(p.sourceName)}
                  disabled={test?.loading}
                  startIcon={test?.loading ? <CircularProgress size={16} color="inherit" /> : <ScienceIcon />}
                  data-testid={`weather-provider-test-${p.sourceName}`}
                >
                  {t('pages.weatherProviders.testButton')}
                </Button>
              </Box>

              {test?.result && (
                <Box sx={{ mt: 1.5 }} data-testid={`weather-provider-test-result-${p.sourceName}`}>
                  {test.result.reachable ? (
                    <Alert severity="success" icon={<CheckCircleOutlineIcon fontSize="inherit" />}>
                      <AlertTitle>{t('pages.weatherProviders.testReachable')}</AlertTitle>
                      {test.result.preview.map((row) => (
                        <Typography variant="caption" component="div" key={`${row.forecast_date}-${row.source}`}>
                          {t('pages.weatherProviders.previewRow', {
                            date: row.forecast_date,
                            min: row.temp_min_c ?? '—',
                            max: row.temp_max_c ?? '—',
                            rain: row.precipitation_mm ?? '—',
                          })}
                        </Typography>
                      ))}
                    </Alert>
                  ) : (
                    <Alert severity="error" icon={<ErrorOutlineIcon fontSize="inherit" />}>
                      {test.result.error || t('pages.weatherProviders.testUnreachable')}
                    </Alert>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        );
      })}

      {/* ── Global OpenWeatherMap fallback key ── */}
      <Card variant="outlined">
        <CardContent component="fieldset" sx={{ border: 'none', p: { xs: 2, md: 3 }, m: 0 }}>
          <Typography component="legend" variant="subtitle1" sx={{ mb: 0.5, fontWeight: 600 }}>
            {t('pages.weatherProviders.globalKeyTitle')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.weatherProviders.globalKeyDesc')}
          </Typography>
          <TextField
            fullWidth
            type={keyVisible ? 'text' : 'password'}
            label={t('pages.weatherProviders.globalKeyLabel')}
            value={form.globalOwmKey}
            onChange={(e) => setFormField('globalOwmKey', e.target.value)}
            placeholder={settings.openweathermap_global_api_key_set ? MASKED_PLACEHOLDER : ''}
            autoComplete="new-password"
            helperText={
              settings.openweathermap_global_api_key_set
                ? t('pages.weatherProviders.globalKeyStoredHelper')
                : t('pages.weatherProviders.globalKeyEmptyHelper')
            }
            slotProps={{
              input: {
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label={t('pages.weatherProviders.toggleKeyVisibility')}
                      onClick={() => setKeyVisible((v) => !v)}
                      edge="end"
                      size="small"
                      data-testid="weather-global-owm-key-toggle"
                    >
                      {keyVisible ? <VisibilityOffIcon fontSize="small" /> : <VisibilityIcon fontSize="small" />}
                    </IconButton>
                  </InputAdornment>
                ),
              },
            }}
            data-testid="weather-global-owm-key"
          />
          <Box sx={{ mt: 1 }}>
            <Chip
              size="small"
              color={settings.openweathermap_global_api_key_set ? 'success' : 'default'}
              label={
                settings.openweathermap_global_api_key_set
                  ? t('pages.weatherProviders.globalKeySet')
                  : t('pages.weatherProviders.globalKeyUnset')
              }
              data-testid="weather-global-owm-key-status"
            />
          </Box>
        </CardContent>
      </Card>

      {/* ── Fetch settings ── */}
      <Card variant="outlined">
        <CardContent component="fieldset" sx={{ border: 'none', p: { xs: 2, md: 3 }, m: 0 }}>
          <Typography component="legend" variant="subtitle1" sx={{ mb: 0.5, fontWeight: 600 }}>
            {t('pages.weatherProviders.fetchTitle')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.weatherProviders.fetchDesc')}
          </Typography>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
              gap: 2,
            }}
          >
            <TextField
              type="number"
              label={t('pages.weatherProviders.fetchTimeout')}
              value={form.fetchTimeoutS}
              onChange={(e) =>
                setFormField('fetchTimeoutS', e.target.value === '' ? '' : Number(e.target.value))
              }
              helperText={t('pages.weatherProviders.fetchTimeoutHelper')}
              slotProps={{
                htmlInput: { min: 1, max: 120, step: 1, inputMode: 'numeric' },
                input: { endAdornment: <InputAdornment position="end">s</InputAdornment> },
              }}
              data-testid="weather-fetch-timeout"
            />
            <TextField
              select
              label={t('pages.weatherProviders.defaultSource')}
              value={form.defaultPublicSource}
              onChange={(e) => setFormField('defaultPublicSource', e.target.value)}
              helperText={t('pages.weatherProviders.defaultSourceHelper')}
              data-testid="weather-default-source"
            >
              {sourceOptions.map((name) => (
                <MenuItem key={name} value={name}>
                  {providerName(name)}
                </MenuItem>
              ))}
            </TextField>
          </Box>
        </CardContent>
      </Card>

      <Divider />

      {/* ── Actions ── */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          onClick={() => void handleSave()}
          disabled={saving}
          aria-busy={saving}
          startIcon={saving ? <CircularProgress size={16} color="inherit" /> : undefined}
          data-testid="weather-providers-save-button"
        >
          {t('common.save')}
        </Button>
      </Box>
    </Box>
  );
}
