import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Switch from '@mui/material/Switch';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Alert from '@mui/material/Alert';
import Divider from '@mui/material/Divider';
import CircularProgress from '@mui/material/CircularProgress';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import SettingsIcon from '@mui/icons-material/Settings';
import ScienceIcon from '@mui/icons-material/Science';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import CloudIcon from '@mui/icons-material/Cloud';
import EmptyState from '@/components/common/EmptyState';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import WeatherProvenanceBadge from '@/components/weather/WeatherProvenanceBadge';
import WeatherSourceAddDialog from './WeatherSourceAddDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as weatherApi from '@/api/endpoints/weatherSources';
import type {
  AvailableSourcesResponse,
  WeatherSourceConfigResponse,
  WeatherSourceEntryRequest,
  WeatherSourceEntryResponse,
  WeatherTestResponse,
} from '@/api/types';

interface Props {
  siteKey: string;
}

interface WorkingEntry {
  entry: WeatherSourceEntryRequest;
  /** Whether this public source has a stored OWM key (server-side, AC-8). */
  apiKeySet: boolean;
}

interface TestState {
  loading: boolean;
  result: WeatherTestResponse | null;
}

/**
 * UI-NFR-001 R-011 — 48x48px touch targets on mobile/tablet; on `sm+` (mouse-
 * first) the reduced 32px size (R-013) keeps the crowded action row compact.
 */
const TOUCH_TARGET_SX = { minWidth: { xs: 48, sm: 32 }, minHeight: { xs: 48, sm: 32 } } as const;

function toWorkingEntry(r: WeatherSourceEntryResponse): WorkingEntry {
  if (r.kind === 'public') {
    return {
      entry: {
        source_name: r.source_name,
        kind: 'public',
        enabled: r.enabled,
        // Empty string = "unchanged" (server keeps the stored ciphertext).
        public_config: { api_key: '', units_hint: r.public_config?.units_hint ?? null },
      },
      apiKeySet: r.public_config?.api_key_set ?? false,
    };
  }
  return {
    entry: {
      source_name: r.source_name,
      kind: 'home_assistant',
      enabled: r.enabled,
      ha_config: r.ha_config ?? { mode: 'weather_entity' },
    },
    apiKeySet: false,
  };
}

/**
 * REQ-046 §4.1 — per-site weather-source configurator. Self-loading section
 * (like SiteRunsSection): given a `siteKey` it fetches the config + the
 * available sources and keeps its own local state (no Redux slice). Priority is
 * ordered via up/down icon buttons (D3, index 0 = highest priority); each entry
 * can be enabled, edited, connection-tested (AC-7) and removed.
 */
export default function WeatherSourceSection({ siteKey }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [available, setAvailable] = useState<AvailableSourcesResponse | null>(null);
  const [entries, setEntries] = useState<WorkingEntry[]>([]);
  const [enabled, setEnabled] = useState(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editIndex, setEditIndex] = useState<number | null>(null);
  const [tests, setTests] = useState<Record<number, TestState>>({});

  const applyConfig = (config: WeatherSourceConfigResponse) => {
    setEnabled(config.enabled);
    setEntries(config.sources.map(toWorkingEntry));
    setTests({});
  };

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const [config, avail] = await Promise.all([
          weatherApi.getWeatherSource(siteKey),
          weatherApi.getAvailableSources(),
        ]);
        if (cancelled) return;
        setAvailable(avail);
        applyConfig(config);
      } catch (err) {
        if (!cancelled) handleError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [siteKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const move = (index: number, delta: number) => {
    const target = index + delta;
    if (target < 0 || target >= entries.length) return;
    setEntries((prev) => {
      const next = [...prev];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
    setTests({});
  };

  const toggleEnabled = (index: number) => {
    setEntries((prev) =>
      prev.map((w, i) =>
        i === index ? { ...w, entry: { ...w.entry, enabled: !w.entry.enabled } } : w,
      ),
    );
  };

  const remove = (index: number) => {
    setEntries((prev) => prev.filter((_, i) => i !== index));
    setTests({});
  };

  const handleDialogSave = (entry: WeatherSourceEntryRequest) => {
    const enteredKey = !!entry.public_config?.api_key;
    setEntries((prev) => {
      if (editIndex === null) {
        return [...prev, { entry, apiKeySet: enteredKey }];
      }
      return prev.map((w, i) =>
        i === editIndex
          ? { entry, apiKeySet: enteredKey || (entry.kind === 'public' && w.apiKeySet) }
          : w,
      );
    });
    setEditIndex(null);
  };

  const openAdd = () => {
    setEditIndex(null);
    setDialogOpen(true);
  };

  const openEdit = (index: number) => {
    setEditIndex(index);
    setDialogOpen(true);
  };

  const runTest = async (index: number) => {
    setTests((prev) => ({ ...prev, [index]: { loading: true, result: null } }));
    try {
      const result = await weatherApi.testSource(siteKey, entries[index].entry);
      setTests((prev) => ({ ...prev, [index]: { loading: false, result } }));
    } catch (err) {
      handleError(err);
      setTests((prev) => ({ ...prev, [index]: { loading: false, result: null } }));
    }
  };

  const save = async () => {
    setSaving(true);
    try {
      const saved = await weatherApi.putWeatherSource(siteKey, {
        enabled,
        sources: entries.map((w) => w.entry),
      });
      applyConfig(saved);
      notification.success(t('common.saved'));
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ mt: 4 }} data-testid="weather-source-section">
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <CloudIcon />
          {t('pages.weatherSource.title')}
        </Typography>
        <LoadingSkeleton variant="table" rows={2} />
      </Box>
    );
  }

  return (
    <Box sx={{ mt: 4 }} data-testid="weather-source-section">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1, flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CloudIcon />
          {t('pages.weatherSource.title')}
        </Typography>
        <Button startIcon={<AddIcon />} onClick={openAdd} data-testid="weather-add-source-button">
          {t('pages.weatherSource.addSource')}
        </Button>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.weatherSource.intro')}
      </Typography>

      {entries.length === 0 ? (
        <EmptyState
          message={t('pages.weatherSource.empty')}
          actionLabel={t('pages.weatherSource.addSource')}
          onAction={openAdd}
        />
      ) : (
        <Stack spacing={1.5}>
          {entries.map((w, index) => {
            const test = tests[index];
            return (
              <Card variant="outlined" key={`${w.entry.source_name}-${index}`} data-testid={`weather-entry-${index}`}>
                <CardContent sx={{ '&:last-child': { pb: 2 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                    <Stack sx={{ display: 'flex', flexShrink: 0 }}>
                      <Tooltip title={t('pages.weatherSource.moveUp')}>
                        <span>
                          <IconButton
                            size="small"
                            onClick={() => move(index, -1)}
                            disabled={index === 0}
                            aria-label={t('pages.weatherSource.moveUp')}
                            data-testid={`weather-move-up-${index}`}
                            sx={TOUCH_TARGET_SX}
                          >
                            <ArrowUpwardIcon fontSize="small" />
                          </IconButton>
                        </span>
                      </Tooltip>
                      <Tooltip title={t('pages.weatherSource.moveDown')}>
                        <span>
                          <IconButton
                            size="small"
                            onClick={() => move(index, 1)}
                            disabled={index === entries.length - 1}
                            aria-label={t('pages.weatherSource.moveDown')}
                            data-testid={`weather-move-down-${index}`}
                            sx={TOUCH_TARGET_SX}
                          >
                            <ArrowDownwardIcon fontSize="small" />
                          </IconButton>
                        </span>
                      </Tooltip>
                    </Stack>

                    <Tooltip title={t('pages.weatherSource.priorityHint', { position: index + 1 })}>
                      <Chip
                        size="small"
                        label={`#${index + 1}`}
                        color={index === 0 ? 'primary' : 'default'}
                        tabIndex={0}
                      />
                    </Tooltip>

                    <Box sx={{ flexGrow: 1, minWidth: 160 }}>
                      <Typography variant="subtitle2">
                        {t(`enums.weatherSource.${w.entry.source_name}`, { defaultValue: w.entry.source_name })}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
                        <Chip
                          size="small"
                          variant="outlined"
                          label={t(`enums.weatherSourceKind.${w.entry.kind}`)}
                        />
                        {w.entry.kind === 'home_assistant' && w.entry.ha_config && (
                          <Chip
                            size="small"
                            variant="outlined"
                            label={t(`enums.haWeatherMode.${w.entry.ha_config.mode}`)}
                          />
                        )}
                        {w.entry.kind === 'public' && w.apiKeySet && (
                          <Chip size="small" color="success" variant="outlined" label={t('pages.weatherSource.keyStored')} />
                        )}
                      </Box>
                    </Box>

                    <Tooltip title={t('pages.weatherSource.enableToggle')}>
                      <Switch
                        checked={w.entry.enabled}
                        onChange={() => toggleEnabled(index)}
                        slotProps={{ input: { 'aria-label': t('pages.weatherSource.enableToggle') } }}
                        data-testid={`weather-enable-${index}`}
                      />
                    </Tooltip>
                    <Tooltip title={t('pages.weatherSource.testSource')}>
                      <span>
                        <IconButton
                          size="small"
                          onClick={() => runTest(index)}
                          disabled={test?.loading}
                          aria-label={t('pages.weatherSource.testSource')}
                          data-testid={`weather-test-${index}`}
                          sx={TOUCH_TARGET_SX}
                        >
                          {test?.loading ? <CircularProgress size={18} /> : <ScienceIcon fontSize="small" />}
                        </IconButton>
                      </span>
                    </Tooltip>
                    <Tooltip title={t('pages.weatherSource.configure')}>
                      <IconButton
                        size="small"
                        onClick={() => openEdit(index)}
                        aria-label={t('pages.weatherSource.configure')}
                        data-testid={`weather-edit-${index}`}
                        sx={TOUCH_TARGET_SX}
                      >
                        <SettingsIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={t('common.delete')}>
                      <IconButton
                        size="small"
                        onClick={() => remove(index)}
                        aria-label={t('common.delete')}
                        data-testid={`weather-remove-${index}`}
                        sx={TOUCH_TARGET_SX}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>

                  {test?.result && (
                    <Box sx={{ mt: 1.5 }} data-testid={`weather-test-result-${index}`}>
                      <Divider sx={{ mb: 1.5 }} />
                      {test.result.reachable ? (
                        <>
                          <Alert severity="success" sx={{ mb: 1 }}>
                            {t('pages.weatherSource.testReachable')}
                          </Alert>
                          <Stack spacing={1}>
                            {test.result.preview.map((p) => (
                              <Box key={`${p.forecast_date}-${p.source}`} sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                                <Typography variant="body2" sx={{ minWidth: 96 }}>{p.forecast_date}</Typography>
                                <WeatherProvenanceBadge
                                  source={p.source}
                                  dataKind={p.data_kind}
                                  isCurrentConditions={p.is_current_conditions}
                                />
                                <Typography variant="caption" color="text.secondary">
                                  {t('pages.weatherSource.previewValues', {
                                    min: p.temp_min_c ?? '—',
                                    max: p.temp_max_c ?? '—',
                                    rain: p.precipitation_mm ?? '—',
                                  })}
                                </Typography>
                              </Box>
                            ))}
                          </Stack>
                        </>
                      ) : (
                        <Alert severity="error" data-testid={`weather-test-error-${index}`}>
                          {test.result.error || t('pages.weatherSource.testUnreachable')}
                        </Alert>
                      )}
                    </Box>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </Stack>
      )}

      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
        <Button variant="contained" onClick={save} disabled={saving} data-testid="weather-save-button">
          {t('common.save')}
        </Button>
      </Box>

      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
        {t('pages.weatherSource.attribution')}
      </Typography>

      <WeatherSourceAddDialog
        open={dialogOpen}
        onClose={() => { setDialogOpen(false); setEditIndex(null); }}
        available={available}
        existing={editIndex !== null ? entries[editIndex]?.entry : undefined}
        existingApiKeySet={editIndex !== null ? entries[editIndex]?.apiKeySet : false}
        onSave={handleDialogSave}
      />
    </Box>
  );
}
