import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import InputLabel from '@mui/material/InputLabel';
import FormControl from '@mui/material/FormControl';
import Divider from '@mui/material/Divider';
import SendIcon from '@mui/icons-material/Send';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutlined';
import { useSnackbar } from 'notistack';
import {
  getPreferences,
  updatePreferences,
  getChannelStatus,
  sendTest,
} from '@/api/endpoints/notifications';
import { parseApiError } from '@/api/errors';
import type {
  NotificationPreferencesResponse,
  ChannelStatusResponse,
  ChannelPreference,
  QuietHoursPreference,
  BatchingPreference,
  EscalationPreference,
  DailySummaryPreference,
} from '@/api/types';

const GRID_2COL = {
  display: 'grid',
  gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
  gap: 2,
} as const;

const CHANNEL_KEYS = ['home_assistant', 'email', 'pwa', 'apprise'] as const;

const CHANNEL_LABEL_KEYS: Record<string, string> = {
  home_assistant: 'pages.notifications.settings.channelHomeAssistant',
  email: 'pages.notifications.settings.channelEmail',
  pwa: 'pages.notifications.settings.channelPwa',
  apprise: 'pages.notifications.settings.channelApprise',
};

const DEFAULT_CHANNEL_PREF: ChannelPreference = {
  enabled: false,
  priority: 0,
  config: {},
};

function getChannelPref(
  prefs: NotificationPreferencesResponse | null,
  key: string,
): ChannelPreference {
  return prefs?.channels?.[key] ?? { ...DEFAULT_CHANNEL_PREF };
}

export default function NotificationSettingsTab() {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();

  const [prefs, setPrefs] = useState<NotificationPreferencesResponse | null>(null);
  const [channelStatuses, setChannelStatuses] = useState<ChannelStatusResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testingChannel, setTestingChannel] = useState<string | null>(null);

  // Editable state mirrors prefs for form fields
  const [channels, setChannels] = useState<Record<string, ChannelPreference>>({});
  const [quietHours, setQuietHours] = useState<QuietHoursPreference>({
    enabled: true,
    start: '22:00',
    end: '07:00',
    timezone: 'Europe/Berlin',
  });
  const [batching, setBatching] = useState<BatchingPreference>({
    enabled: true,
    window_minutes: 30,
    max_batch_size: 10,
  });
  const [escalation, setEscalation] = useState<EscalationPreference>({
    watering_enabled: true,
    escalation_days: [2, 4, 7],
  });
  const [dailySummary, setDailySummary] = useState<DailySummaryPreference>({
    enabled: false,
    time: '07:00',
    channel: 'home_assistant',
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [prefsData, statusData] = await Promise.all([
        getPreferences(),
        getChannelStatus(),
      ]);
      setPrefs(prefsData);
      setChannelStatuses(statusData);

      // Populate form state from loaded prefs
      setChannels(prefsData.channels ?? {});
      setQuietHours(prefsData.quiet_hours);
      setBatching(prefsData.batching);
      setEscalation(prefsData.escalation);
      setDailySummary(prefsData.daily_summary);
    } catch {
      // Keep defaults if loading fails
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await updatePreferences({
        channels,
        quiet_hours: quietHours,
        batching,
        escalation,
        type_overrides: prefs?.type_overrides ?? {},
        daily_summary: dailySummary,
      });
      setPrefs(updated);
      enqueueSnackbar(t('common.saved'), { variant: 'success' });
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const handleTestSend = async (channelKey: string) => {
    setTestingChannel(channelKey);
    try {
      const result = await sendTest(channelKey);
      if (result.success) {
        enqueueSnackbar(t('pages.notifications.settings.testSuccess'), {
          variant: 'success',
        });
      } else {
        enqueueSnackbar(
          `${t('pages.notifications.settings.testFailed')}: ${result.error ?? ''}`,
          { variant: 'error' },
        );
      }
    } catch (err) {
      enqueueSnackbar(parseApiError(err), { variant: 'error' });
    } finally {
      setTestingChannel(null);
    }
  };

  const updateChannelEnabled = (key: string, enabled: boolean) => {
    setChannels((prev) => ({
      ...prev,
      [key]: {
        ...(prev[key] ?? { ...DEFAULT_CHANNEL_PREF }),
        enabled,
      },
    }));
  };

  const updateChannelConfig = (
    channelKey: string,
    configKey: string,
    value: unknown,
  ) => {
    setChannels((prev) => ({
      ...prev,
      [channelKey]: {
        ...(prev[channelKey] ?? { ...DEFAULT_CHANNEL_PREF }),
        config: {
          ...(prev[channelKey]?.config ?? {}),
          [configKey]: value,
        },
      },
    }));
  };

  const getStatusForChannel = (key: string): ChannelStatusResponse | undefined => {
    return channelStatuses.find((s) => s.channel_key === key);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* ── Channels Section ── */}
      <Card variant="outlined">
        <CardContent
          component="fieldset"
          sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}
        >
          <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
            {t('pages.notifications.settings.channels')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.notifications.settings.channelsDesc')}
          </Typography>

          {CHANNEL_KEYS.map((channelKey) => {
            const pref = channels[channelKey] ?? getChannelPref(prefs, channelKey);
            const status = getStatusForChannel(channelKey);
            const channelLabelKey = CHANNEL_LABEL_KEYS[channelKey] ?? channelKey;

            return (
              <Box key={channelKey} sx={{ mb: 2 }}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    mb: 1,
                  }}
                >
                  <FormControlLabel
                    control={
                      <Switch
                        checked={pref.enabled}
                        onChange={(e) =>
                          updateChannelEnabled(channelKey, e.target.checked)
                        }
                        data-testid={`channel-toggle-${channelKey}`}
                      />
                    }
                    label={t(channelLabelKey)}
                  />
                  <Chip
                    size="small"
                    label={
                      status?.healthy
                        ? t('pages.notifications.settings.channelAvailable')
                        : t('pages.notifications.settings.channelNotConfigured')
                    }
                    color={status?.healthy ? 'success' : 'default'}
                    icon={
                      status?.healthy ? (
                        <CheckCircleIcon fontSize="small" />
                      ) : (
                        <ErrorOutlineIcon fontSize="small" />
                      )
                    }
                  />
                </Box>

                {/* Channel-specific config fields */}
                {pref.enabled && channelKey === 'home_assistant' && (
                  <Box sx={{ pl: 4, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={
                            (pref.config?.persistent_notification as boolean) ?? true
                          }
                          onChange={(e) =>
                            updateChannelConfig(
                              channelKey,
                              'persistent_notification',
                              e.target.checked,
                            )
                          }
                          data-testid="ha-persistent-notification-toggle"
                        />
                      }
                      label={t(
                        'pages.notifications.settings.persistentNotification',
                      )}
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={
                            (pref.config?.mobile_push as boolean) ?? true
                          }
                          onChange={(e) =>
                            updateChannelConfig(
                              channelKey,
                              'mobile_push',
                              e.target.checked,
                            )
                          }
                          data-testid="ha-mobile-push-toggle"
                        />
                      }
                      label={t('pages.notifications.settings.mobilePush')}
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={
                            (pref.config?.tts_enabled as boolean) ?? false
                          }
                          onChange={(e) =>
                            updateChannelConfig(
                              channelKey,
                              'tts_enabled',
                              e.target.checked,
                            )
                          }
                          data-testid="ha-tts-toggle"
                        />
                      }
                      label={t('pages.notifications.settings.ttsEnabled')}
                    />
                    {(pref.config?.tts_enabled as boolean) && (
                      <TextField
                        label={t('pages.notifications.settings.ttsEntityId')}
                        size="small"
                        value={(pref.config?.tts_entity_id as string) ?? ''}
                        onChange={(e) =>
                          updateChannelConfig(
                            channelKey,
                            'tts_entity_id',
                            e.target.value,
                          )
                        }
                        placeholder="media_player.kitchen"
                        data-testid="ha-tts-entity-id"
                        sx={{ maxWidth: 400 }}
                      />
                    )}
                  </Box>
                )}

                {pref.enabled && channelKey === 'email' && (
                  <Box sx={{ pl: 4, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                    <TextField
                      label={t('pages.notifications.settings.emailAddress')}
                      size="small"
                      type="email"
                      value={(pref.config?.address as string) ?? ''}
                      onChange={(e) =>
                        updateChannelConfig(
                          channelKey,
                          'address',
                          e.target.value,
                        )
                      }
                      data-testid="email-address"
                      sx={{ maxWidth: 400 }}
                    />
                    <FormControl size="small" sx={{ maxWidth: 250 }}>
                      <InputLabel id="email-digest-label">
                        {t('pages.notifications.settings.emailDigestMode')}
                      </InputLabel>
                      <Select
                        labelId="email-digest-label"
                        label={t('pages.notifications.settings.emailDigestMode')}
                        value={(pref.config?.digest_mode as string) ?? 'immediate'}
                        onChange={(e) =>
                          updateChannelConfig(
                            channelKey,
                            'digest_mode',
                            e.target.value,
                          )
                        }
                        data-testid="email-digest-mode"
                      >
                        <MenuItem value="immediate">
                          {t('pages.notifications.settings.emailImmediate')}
                        </MenuItem>
                        <MenuItem value="daily">
                          {t('pages.notifications.settings.emailDaily')}
                        </MenuItem>
                      </Select>
                    </FormControl>
                  </Box>
                )}

                {pref.enabled && channelKey === 'apprise' && (
                  <Box sx={{ pl: 4 }}>
                    <TextField
                      label={t('pages.notifications.settings.appriseUrls')}
                      size="small"
                      multiline
                      minRows={3}
                      maxRows={8}
                      value={
                        Array.isArray(pref.config?.urls)
                          ? (pref.config.urls as string[]).join('\n')
                          : ''
                      }
                      onChange={(e) =>
                        updateChannelConfig(
                          channelKey,
                          'urls',
                          e.target.value
                            .split('\n')
                            .filter((u: string) => u.trim().length > 0),
                        )
                      }
                      placeholder={
                        'tgram://bottoken/chatid\nslack://tokenA/tokenB/channel\ngotify://hostname/token'
                      }
                      data-testid="apprise-urls"
                      sx={{ maxWidth: 500, width: '100%' }}
                    />
                  </Box>
                )}

                {/* Test button */}
                {pref.enabled && (
                  <Box sx={{ pl: 4, mt: 1 }}>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={
                        testingChannel === channelKey ? (
                          <CircularProgress size={16} />
                        ) : (
                          <SendIcon />
                        )
                      }
                      disabled={testingChannel !== null}
                      onClick={() => handleTestSend(channelKey)}
                      data-testid={`test-send-${channelKey}`}
                    >
                      {t('pages.notifications.settings.testSend')}
                    </Button>
                  </Box>
                )}

                {channelKey !== CHANNEL_KEYS[CHANNEL_KEYS.length - 1] && (
                  <Divider sx={{ mt: 2 }} />
                )}
              </Box>
            );
          })}
        </CardContent>
      </Card>

      {/* ── Schedule Section (Quiet Hours + Daily Summary) ── */}
      <Box sx={GRID_2COL}>
        <Card variant="outlined">
          <CardContent
            component="fieldset"
            sx={{
              border: 'none',
              p: 0,
              m: 0,
              '&:last-child': { pb: 2 },
              px: 2,
              pt: 2,
            }}
          >
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.notifications.settings.quietHours')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.notifications.settings.quietHoursDesc')}
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={quietHours.enabled}
                  onChange={(e) =>
                    setQuietHours((prev) => ({
                      ...prev,
                      enabled: e.target.checked,
                    }))
                  }
                  data-testid="quiet-hours-toggle"
                />
              }
              label={t('pages.notifications.settings.quietHours')}
            />
            {quietHours.enabled && (
              <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                <TextField
                  label={t('pages.notifications.settings.quietHoursStart')}
                  type="time"
                  size="small"
                  value={quietHours.start}
                  onChange={(e) =>
                    setQuietHours((prev) => ({ ...prev, start: e.target.value }))
                  }
                  slotProps={{ inputLabel: { shrink: true } }}
                  data-testid="quiet-hours-start"
                />
                <TextField
                  label={t('pages.notifications.settings.quietHoursEnd')}
                  type="time"
                  size="small"
                  value={quietHours.end}
                  onChange={(e) =>
                    setQuietHours((prev) => ({ ...prev, end: e.target.value }))
                  }
                  slotProps={{ inputLabel: { shrink: true } }}
                  data-testid="quiet-hours-end"
                />
              </Box>
            )}
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent
            component="fieldset"
            sx={{
              border: 'none',
              p: 0,
              m: 0,
              '&:last-child': { pb: 2 },
              px: 2,
              pt: 2,
            }}
          >
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.notifications.settings.dailySummary')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.notifications.settings.dailySummaryDesc')}
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={dailySummary.enabled}
                  onChange={(e) =>
                    setDailySummary((prev) => ({
                      ...prev,
                      enabled: e.target.checked,
                    }))
                  }
                  data-testid="daily-summary-toggle"
                />
              }
              label={t('pages.notifications.settings.dailySummary')}
            />
            {dailySummary.enabled && (
              <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                <TextField
                  label={t('pages.notifications.settings.dailySummaryTime')}
                  type="time"
                  size="small"
                  value={dailySummary.time}
                  onChange={(e) =>
                    setDailySummary((prev) => ({
                      ...prev,
                      time: e.target.value,
                    }))
                  }
                  slotProps={{ inputLabel: { shrink: true } }}
                  data-testid="daily-summary-time"
                />
                <FormControl size="small" sx={{ minWidth: 180 }}>
                  <InputLabel id="daily-summary-channel-label">
                    {t('pages.notifications.settings.channels')}
                  </InputLabel>
                  <Select
                    labelId="daily-summary-channel-label"
                    label={t('pages.notifications.settings.channels')}
                    value={dailySummary.channel}
                    onChange={(e) =>
                      setDailySummary((prev) => ({
                        ...prev,
                        channel: e.target.value,
                      }))
                    }
                    data-testid="daily-summary-channel"
                  >
                    {CHANNEL_KEYS.map((ck) => (
                      <MenuItem key={ck} value={ck}>
                        {ck}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>

      {/* ── Batching + Escalation ── */}
      <Box sx={GRID_2COL}>
        <Card variant="outlined">
          <CardContent
            component="fieldset"
            sx={{
              border: 'none',
              p: 0,
              m: 0,
              '&:last-child': { pb: 2 },
              px: 2,
              pt: 2,
            }}
          >
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.notifications.settings.batching')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.notifications.settings.batchingDesc')}
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={batching.enabled}
                  onChange={(e) =>
                    setBatching((prev) => ({
                      ...prev,
                      enabled: e.target.checked,
                    }))
                  }
                  data-testid="batching-toggle"
                />
              }
              label={t('pages.notifications.settings.batching')}
            />
            {batching.enabled && (
              <Box sx={{ mt: 1 }}>
                <TextField
                  label={t('pages.notifications.settings.batchingWindow')}
                  type="number"
                  size="small"
                  value={batching.window_minutes}
                  onChange={(e) =>
                    setBatching((prev) => ({
                      ...prev,
                      window_minutes: Math.max(
                        1,
                        Math.min(120, Number(e.target.value) || 1),
                      ),
                    }))
                  }
                  slotProps={{
                    htmlInput: { min: 1, max: 120, step: 'any' },
                  }}
                  data-testid="batching-window"
                  sx={{ maxWidth: 200 }}
                />
              </Box>
            )}
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardContent
            component="fieldset"
            sx={{
              border: 'none',
              p: 0,
              m: 0,
              '&:last-child': { pb: 2 },
              px: 2,
              pt: 2,
            }}
          >
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.notifications.settings.escalation')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.notifications.settings.escalationDesc')}
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={escalation.watering_enabled}
                  onChange={(e) =>
                    setEscalation((prev) => ({
                      ...prev,
                      watering_enabled: e.target.checked,
                    }))
                  }
                  data-testid="escalation-toggle"
                />
              }
              label={t('pages.notifications.settings.escalationWatering')}
            />
            {escalation.watering_enabled && (
              <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                {escalation.escalation_days.map((day, index) => (
                  <Chip
                    key={index}
                    label={`${t('common.days')}: +${day}`}
                    size="small"
                    variant="outlined"
                    color="primary"
                  />
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>

      {/* ── Save Button ── */}
      <Box>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={saving}
          startIcon={saving ? <CircularProgress size={16} /> : undefined}
          data-testid="notification-settings-save"
        >
          {t('common.save')}
        </Button>
        {saving && (
          <Alert severity="info" sx={{ mt: 1, maxWidth: 400 }}>
            {t('common.loading')}
          </Alert>
        )}
      </Box>
    </Box>
  );
}
