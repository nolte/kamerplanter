import { useState, useEffect, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import InputAdornment from '@mui/material/InputAdornment';
import IconButton from '@mui/material/IconButton';
import Autocomplete from '@mui/material/Autocomplete';
import Divider from '@mui/material/Divider';
import Link from '@mui/material/Link';
import CircularProgress from '@mui/material/CircularProgress';
import PublicIcon from '@mui/icons-material/Public';
import HomeIcon from '@mui/icons-material/Home';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { Link as RouterLink } from 'react-router-dom';
import * as weatherApi from '@/api/endpoints/weatherSources';
import type {
  AvailableSourcesResponse,
  HaEntityItem,
  HaSensorMapping,
  HaWeatherMode,
  WeatherSourceEntryRequest,
  WeatherSourceKind,
} from '@/api/types';

const MASKED_PLACEHOLDER = '••••';

const HA_SOURCE_NAME = 'ha_weather';

/** The eight mappable `:WeatherForecast` fields (REQ-046 §2.2). */
const SENSOR_FIELDS: (keyof HaSensorMapping)[] = [
  'temp_min_entity',
  'temp_max_entity',
  'temp_current_entity',
  'humidity_entity',
  'precipitation_entity',
  'wind_speed_entity',
  'wind_gust_entity',
  'pressure_entity',
];

/**
 * Groups the eight sensor-mapping fields under short, scannable subheadings
 * instead of one flat list — reduces cognitive load and keeps the mobile
 * layout easy to stack (each group already renders as a single column).
 */
const SENSOR_FIELD_GROUPS: { titleKey: string; fields: (keyof HaSensorMapping)[] }[] = [
  { titleKey: 'pages.weatherSource.sensorGroupTemperature', fields: ['temp_min_entity', 'temp_max_entity', 'temp_current_entity'] },
  { titleKey: 'pages.weatherSource.sensorGroupPrecipitationWind', fields: ['precipitation_entity', 'wind_speed_entity', 'wind_gust_entity'] },
  { titleKey: 'pages.weatherSource.sensorGroupOther', fields: ['humidity_entity', 'pressure_entity'] },
];

interface Props {
  open: boolean;
  onClose: () => void;
  available: AvailableSourcesResponse | null;
  /** Pre-populated entry when editing an existing source (gear icon). */
  existing?: WeatherSourceEntryRequest;
  /** Whether the edited public source already has a stored OWM key (AC-8). */
  existingApiKeySet?: boolean;
  onSave: (entry: WeatherSourceEntryRequest) => void;
}

/**
 * REQ-046 §4.1 — "Add source" dialog with the confirmed two-way switch: a
 * public weather service (provider select; OWM adds a masked key field) versus
 * Home Assistant (mode A: one `weather.*` entity / mode B: per-field `sensor.*`
 * mapping). The HA branch is disabled with an explanatory hint whenever no HA
 * token is set (`available.ha_token_set === false`, AC-5).
 */
export default function WeatherSourceAddDialog({
  open,
  onClose,
  available,
  existing,
  existingApiKeySet = false,
  onSave,
}: Props) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const isEdit = !!existing;

  const haTokenSet = available?.ha_token_set ?? false;
  const publicSources = useMemo(
    () => (available?.sources ?? []).filter((s) => s.kind === 'public'),
    [available],
  );

  const [kind, setKind] = useState<WeatherSourceKind>('public');
  const [sourceName, setSourceName] = useState<string>('');
  const [apiKey, setApiKey] = useState<string>('');
  const [showKey, setShowKey] = useState(false);
  const [haMode, setHaMode] = useState<HaWeatherMode>('weather_entity');
  const [weatherEntityId, setWeatherEntityId] = useState<string | null>(null);
  const [sensorMapping, setSensorMapping] = useState<HaSensorMapping>({});

  const [weatherEntities, setWeatherEntities] = useState<HaEntityItem[]>([]);
  const [sensorEntities, setSensorEntities] = useState<HaEntityItem[]>([]);
  const [loadingEntities, setLoadingEntities] = useState(false);

  const requiresApiKey = useMemo(
    () => publicSources.find((s) => s.source_name === sourceName)?.requires_api_key ?? false,
    [publicSources, sourceName],
  );

  // Reset the form each time the dialog opens (add: defaults, edit: existing).
  useEffect(() => {
    if (!open) return;
    if (existing) {
      setKind(existing.kind);
      setSourceName(existing.source_name);
      setApiKey('');
      setShowKey(false);
      setHaMode(existing.ha_config?.mode ?? 'weather_entity');
      setWeatherEntityId(existing.ha_config?.weather_entity_id ?? null);
      setSensorMapping(existing.ha_config?.sensor_mapping ?? {});
    } else {
      setKind('public');
      setSourceName(publicSources[0]?.source_name ?? '');
      setApiKey('');
      setShowKey(false);
      setHaMode('weather_entity');
      setWeatherEntityId(null);
      setSensorMapping({});
    }
  }, [open, existing, publicSources]);

  // Lazily load HA entities the first time the HA branch is shown.
  useEffect(() => {
    if (!open || kind !== 'home_assistant' || !haTokenSet) return;
    if (weatherEntities.length > 0 || sensorEntities.length > 0) return;
    let cancelled = false;
    setLoadingEntities(true);
    Promise.all([weatherApi.listHaWeatherEntities(), weatherApi.listHaSensorEntities()])
      .then(([w, s]) => {
        if (cancelled) return;
        setWeatherEntities(w);
        setSensorEntities(s);
      })
      .catch(() => {
        if (!cancelled) {
          setWeatherEntities([]);
          setSensorEntities([]);
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingEntities(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, kind, haTokenSet, weatherEntities.length, sensorEntities.length]);

  const setMappingField = useCallback((field: keyof HaSensorMapping, value: string | null) => {
    setSensorMapping((prev) => ({ ...prev, [field]: value }));
  }, []);

  const canSave = useMemo(() => {
    if (kind === 'public') return !!sourceName;
    if (haMode === 'weather_entity') return !!weatherEntityId;
    // sensor_mapping: require at least one mapped field.
    return SENSOR_FIELDS.some((f) => !!sensorMapping[f]);
  }, [kind, sourceName, haMode, weatherEntityId, sensorMapping]);

  const handleSave = () => {
    if (kind === 'public') {
      const entry: WeatherSourceEntryRequest = {
        source_name: sourceName,
        kind: 'public',
        enabled: existing?.enabled ?? true,
        public_config: {
          // Empty string means "unchanged" (backend keeps stored ciphertext).
          api_key: requiresApiKey ? apiKey : null,
          units_hint: existing?.public_config?.units_hint ?? null,
        },
      };
      onSave(entry);
    } else {
      const entry: WeatherSourceEntryRequest = {
        source_name: HA_SOURCE_NAME,
        kind: 'home_assistant',
        enabled: existing?.enabled ?? true,
        ha_config: {
          mode: haMode,
          weather_entity_id: haMode === 'weather_entity' ? weatherEntityId : null,
          sensor_mapping: haMode === 'sensor_mapping' ? sensorMapping : null,
        },
      };
      onSave(entry);
    }
    onClose();
  };

  const entityLabel = (o: HaEntityItem) => `${o.friendly_name} (${o.entity_id})`;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      aria-labelledby="weather-source-add-title"
      data-testid="weather-source-add-dialog"
    >
      <DialogTitle id="weather-source-add-title">
        {isEdit ? t('pages.weatherSource.editSource') : t('pages.weatherSource.addSource')}
      </DialogTitle>
      <DialogContent dividers>
        <Stack spacing={2.5} sx={{ pt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {t('pages.weatherSource.addSourceIntro')}
          </Typography>

          {/* Two-way switch: public service vs. Home Assistant */}
          <ToggleButtonGroup
            exclusive
            fullWidth
            value={kind}
            onChange={(_e, v: WeatherSourceKind | null) => v && setKind(v)}
            aria-label={t('pages.weatherSource.kindSwitchAria')}
            disabled={isEdit}
          >
            <ToggleButton value="public" data-testid="weather-kind-public" autoFocus={!isEdit}>
              <PublicIcon fontSize="small" sx={{ mr: 1 }} />
              {t('enums.weatherSourceKind.public')}
            </ToggleButton>
            <ToggleButton
              value="home_assistant"
              data-testid="weather-kind-ha"
              disabled={!haTokenSet}
            >
              <HomeIcon fontSize="small" sx={{ mr: 1 }} />
              {t('enums.weatherSourceKind.home_assistant')}
            </ToggleButton>
          </ToggleButtonGroup>

          {isEdit && (
            <Typography variant="caption" color="text.secondary" data-testid="weather-edit-locked-hint">
              {t('pages.weatherSource.editLockedHint')}
            </Typography>
          )}

          {!haTokenSet && (
            <Alert severity="info" data-testid="ha-token-missing-hint">
              <AlertTitle>{t('pages.weatherSource.haDisabledTitle')}</AlertTitle>
              {t('pages.weatherSource.haDisabledHint')}{' '}
              <Link component={RouterLink} to="/account#ha">
                {t('pages.weatherSource.haSettingsLink')}
              </Link>
            </Alert>
          )}

          <Divider />

          {/* ── Public branch ── */}
          {kind === 'public' && (
            <Stack spacing={2}>
              <TextField
                select
                fullWidth
                label={t('pages.weatherSource.provider')}
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
                helperText={t('pages.weatherSource.providerHelper')}
                disabled={isEdit}
                data-testid="weather-provider-select"
              >
                {publicSources.map((s) => (
                  <MenuItem key={s.source_name} value={s.source_name}>
                    {t(`enums.weatherSource.${s.source_name}`, { defaultValue: s.source_name })}
                  </MenuItem>
                ))}
              </TextField>

              {sourceName && (
                <Typography variant="caption" color="text.secondary" data-testid="weather-provider-hint">
                  {t(`pages.weatherSource.providerHint.${sourceName}`, { defaultValue: '' })}
                </Typography>
              )}

              {requiresApiKey && (
                <TextField
                  fullWidth
                  type={showKey ? 'text' : 'password'}
                  label={t('pages.weatherSource.apiKey')}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={isEdit && existingApiKeySet ? MASKED_PLACEHOLDER : undefined}
                  helperText={
                    isEdit && existingApiKeySet
                      ? t('pages.weatherSource.apiKeyStoredHelper')
                      : t('pages.weatherSource.apiKeyHelper')
                  }
                  data-testid="weather-api-key-field"
                  slotProps={{
                    input: {
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            aria-label={t('pages.weatherSource.toggleKeyVisibility')}
                            onClick={() => setShowKey((v) => !v)}
                            edge="end"
                            data-testid="weather-api-key-visibility-toggle"
                          >
                            {showKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    },
                  }}
                />
              )}
            </Stack>
          )}

          {/* ── Home Assistant branch ── */}
          {kind === 'home_assistant' && haTokenSet && (
            <Stack spacing={2}>
              <ToggleButtonGroup
                exclusive
                fullWidth
                value={haMode}
                onChange={(_e, v: HaWeatherMode | null) => v && setHaMode(v)}
                aria-label={t('pages.weatherSource.haModeSwitchAria')}
                size="small"
              >
                <ToggleButton value="weather_entity" data-testid="ha-mode-weather-entity">
                  {t('enums.haWeatherMode.weather_entity')}
                </ToggleButton>
                <ToggleButton value="sensor_mapping" data-testid="ha-mode-sensor-mapping">
                  {t('enums.haWeatherMode.sensor_mapping')}
                </ToggleButton>
              </ToggleButtonGroup>

              {loadingEntities && (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                  <CircularProgress size={24} />
                </Box>
              )}

              {haMode === 'weather_entity' && (
                <>
                  <Typography variant="caption" color="text.secondary">
                    {t('pages.weatherSource.weatherEntityHelper')}
                  </Typography>
                  <Autocomplete
                    options={weatherEntities}
                    loading={loadingEntities}
                    value={weatherEntities.find((e) => e.entity_id === weatherEntityId) ?? null}
                    getOptionLabel={entityLabel}
                    isOptionEqualToValue={(o, v) => o.entity_id === v.entity_id}
                    onChange={(_e, v) => setWeatherEntityId(v?.entity_id ?? null)}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label={t('pages.weatherSource.weatherEntity')}
                        data-testid="ha-weather-entity-autocomplete"
                      />
                    )}
                  />
                  {!loadingEntities && weatherEntities.length === 0 && (
                    <Alert severity="info" data-testid="ha-no-weather-entities-hint">
                      {t('pages.weatherSource.noWeatherEntities')}
                    </Alert>
                  )}
                </>
              )}

              {haMode === 'sensor_mapping' && (
                <>
                  <Typography variant="caption" color="text.secondary">
                    {t('pages.weatherSource.sensorMappingHelper')}
                  </Typography>
                  {!loadingEntities && sensorEntities.length === 0 && (
                    <Alert severity="info" data-testid="ha-no-sensor-entities-hint">
                      {t('pages.weatherSource.noSensorEntities')}
                    </Alert>
                  )}
                  <Stack spacing={2.5}>
                    {SENSOR_FIELD_GROUPS.map((group) => (
                      <Stack key={group.titleKey} spacing={1.5}>
                        <Typography variant="overline" color="text.secondary" sx={{ lineHeight: 1 }}>
                          {t(group.titleKey)}
                        </Typography>
                        {group.fields.map((field) => (
                          <Autocomplete
                            key={field}
                            options={sensorEntities}
                            loading={loadingEntities}
                            value={sensorEntities.find((e) => e.entity_id === sensorMapping[field]) ?? null}
                            getOptionLabel={entityLabel}
                            isOptionEqualToValue={(o, v) => o.entity_id === v.entity_id}
                            onChange={(_e, v) => setMappingField(field, v?.entity_id ?? null)}
                            renderInput={(params) => (
                              <TextField
                                {...params}
                                label={t(`pages.weatherSource.sensorField.${field}`)}
                                data-testid={`ha-sensor-${field}`}
                              />
                            )}
                          />
                        ))}
                      </Stack>
                    ))}
                  </Stack>
                </>
              )}
            </Stack>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{t('common.cancel')}</Button>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={!canSave}
          data-testid="weather-source-add-confirm"
        >
          {isEdit ? t('common.save') : t('common.add')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
