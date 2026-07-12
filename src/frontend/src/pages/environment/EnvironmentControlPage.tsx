import { useCallback, useMemo, useState } from 'react';
import type { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import type { TFunction } from 'i18next';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';
import AddIcon from '@mui/icons-material/Add';
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew';
import PowerOffIcon from '@mui/icons-material/PowerOff';
import WifiIcon from '@mui/icons-material/Wifi';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import PageTitle from '@/components/layout/PageTitle';
import EmptyState from '@/components/common/EmptyState';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import HelpTooltip from '@/components/common/HelpTooltip';
import { useNotification } from '@/hooks/useNotification';
import { useActuators } from '@/hooks/useActuators';
import * as api from '@/api/endpoints/environment';
import type { Actuator } from '@/api/types';
import ActuatorDialog from './ActuatorDialog';

// UI-NFR-002 R-018: state is never conveyed by color alone — the online chip
// carries a distinct icon so colorblind users can tell states apart.
const onlineIcon: Record<'online' | 'offline', ReactElement> = {
  online: <WifiIcon />,
  offline: <WifiOffIcon />,
};

function stateColor(state: string | null): ChipProps['color'] {
  if (state === null || state === 'off') return 'default';
  if (state === 'fault') return 'error';
  return 'success';
}

/** Icon for the current-state chip. Only `fault` gets a distinct icon (safety-relevant,
 * matches the ReportProblemIcon used elsewhere for destructive/critical states) — `on`/`off`
 * are already distinguished by their translated label text, so an icon there would be noise. */
function stateIcon(state: string | null): ReactElement | undefined {
  return state === 'fault' ? <ReportProblemIcon /> : undefined;
}

/** Known `current_state` values get a translated, human-readable label (UI-NFR-007).
 * Unknown/future values (e.g. a dimmer percentage from a not-yet-wired protocol) fall
 * back to the raw value instead of crashing or showing an untranslated i18n key. */
function stateLabel(t: TFunction, state: string | null): string {
  if (state === null) return t('pages.environmentControl.stateValues.unknown');
  const key = `pages.environmentControl.stateValues.${state}`;
  const translated = t(key);
  return translated === key ? state : translated;
}

export default function EnvironmentControlPage() {
  const { t } = useTranslation();
  const notification = useNotification();
  const { actuators, loading, reload } = useActuators();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [emergencyOpen, setEmergencyOpen] = useState(false);
  const [emergencyLoading, setEmergencyLoading] = useState(false);
  // Tracks the exact actuator+command in flight so only the clicked button shows a
  // spinner, while BOTH buttons on that card stay disabled to prevent a second command
  // racing the first (UI-NFR-008 double-submit protection extended to card actions).
  const [busy, setBusy] = useState<{ key: string; command: 'turn_on' | 'turn_off' } | null>(null);

  const handleCreated = useCallback(() => {
    setDialogOpen(false);
    notification.success(t('pages.environmentControl.actuatorCreated'));
    reload();
  }, [notification, t, reload]);

  const handleCommand = useCallback(
    async (actuator: Actuator, command: 'turn_on' | 'turn_off') => {
      setBusy({ key: actuator.key, command });
      try {
        const event = await api.sendCommand(actuator.key, command);
        // A failed dispatch (e.g. Home Assistant unreachable) still returns 201 —
        // the backend degrades gracefully to a manual fallback task (REQ-018 §6) rather
        // than throwing. Surface that distinction instead of a blanket "sent" message,
        // otherwise the user believes the device reacted when only a task was queued.
        if (event.success) {
          notification.success(t('pages.environmentControl.commandSent'));
        } else {
          notification.warning(t('pages.environmentControl.commandQueued'));
        }
        reload();
      } catch {
        notification.error(t('errors.generic'));
      } finally {
        setBusy(null);
      }
    },
    [notification, t, reload],
  );

  const handleEmergencyStop = useCallback(async () => {
    setEmergencyLoading(true);
    try {
      const result = await api.emergencyStop('fire_alarm');
      // The backend isolates each device (a bulkhead: one dispatch failure never
      // aborts the rest of the emergency stop) and reports the survivors in
      // `failed`. Reporting only `stopped` here would let the user believe every
      // device is safe even when one wasn't reached — always surface `failed`.
      if (result.failed.length > 0) {
        const failedNames = result.failed
          .map((key) => actuators.find((a) => a.key === key)?.name ?? key)
          .join(', ');
        notification.error(
          t('pages.environmentControl.emergencyPartialFailure', {
            stoppedCount: result.stopped.length,
            failedCount: result.failed.length,
            failedNames,
          }),
        );
      } else {
        notification.warning(
          t('pages.environmentControl.emergencyDone', { count: result.stopped.length }),
        );
      }
      reload();
    } catch {
      notification.error(t('errors.generic'));
    } finally {
      setEmergencyLoading(false);
    }
    // Close only after the request settles — while it's in flight the ConfirmDialog
    // stays open with its native `loading` state (spinner, no backdrop/Escape dismiss),
    // so the safety-critical action can't be accidentally re-triggered mid-request.
    setEmergencyOpen(false);
  }, [notification, t, reload, actuators]);

  const onlineCount = useMemo(
    () => actuators.filter((a) => a.is_online).length,
    [actuators],
  );

  return (
    <Box sx={{ p: 3 }} data-testid="environment-control-page">
      <PageTitle
        title={t('pages.environmentControl.title')}
        action={
          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', rowGap: 1 }}>
            <Button
              variant="outlined"
              color="error"
              startIcon={<ReportProblemIcon />}
              onClick={() => setEmergencyOpen(true)}
              disabled={actuators.length === 0 || emergencyLoading}
              sx={{ minHeight: 48 }}
              data-testid="emergency-stop-button"
            >
              {t('pages.environmentControl.emergencyStop')}
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setDialogOpen(true)}
              sx={{ minHeight: 48 }}
              data-testid="create-actuator-button"
            >
              {t('pages.environmentControl.createActuator')}
            </Button>
          </Stack>
        }
      />

      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5, mb: 3 }}>
        <Typography color="text.secondary">{t('pages.environmentControl.intro')}</Typography>
        <HelpTooltip term="aktor" iconOnly />
      </Box>

      {loading ? (
        <LoadingSkeleton variant="card" />
      ) : actuators.length === 0 ? (
        <EmptyState
          message={t('pages.environmentControl.emptyTitle')}
          description={t('pages.environmentControl.emptyDescription')}
          actionLabel={t('pages.environmentControl.createActuator')}
          onAction={() => setDialogOpen(true)}
        />
      ) : (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.environmentControl.summary', {
              total: actuators.length,
              online: onlineCount,
            })}
          </Typography>
          <Grid container spacing={2}>
            {actuators.map((actuator) => {
              const cardBusy = busy?.key === actuator.key;
              return (
              <Grid key={actuator.key} size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
                <Card variant="outlined" data-testid={`actuator-card-${actuator.key}`}>
                  <CardContent>
                    <Box
                      sx={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        gap: 1,
                        mb: 1,
                      }}
                    >
                      <Typography variant="h6" component="h2">
                        {actuator.name}
                      </Typography>
                      <Chip
                        size="small"
                        icon={onlineIcon[actuator.is_online ? 'online' : 'offline']}
                        label={t(
                          actuator.is_online
                            ? 'pages.environmentControl.online'
                            : 'pages.environmentControl.offline',
                        )}
                        color={actuator.is_online ? 'success' : 'default'}
                      />
                    </Box>

                    <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 0.5, mb: 1.5 }}>
                      <Chip
                        size="small"
                        variant="outlined"
                        label={t(`enums.actuatorType.${actuator.actuator_type}`)}
                      />
                      <Chip
                        size="small"
                        variant="outlined"
                        label={t(`enums.actuatorProtocol.${actuator.protocol}`)}
                      />
                      <Chip
                        size="small"
                        icon={stateIcon(actuator.current_state)}
                        color={stateColor(actuator.current_state)}
                        label={t('pages.environmentControl.stateLabel', {
                          state: stateLabel(t, actuator.current_state),
                        })}
                      />
                    </Stack>

                    {actuator.power_watts != null && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                        {t('pages.environmentControl.powerWattsValue', { watts: actuator.power_watts })}
                      </Typography>
                    )}

                    <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', rowGap: 1 }}>
                      <Button
                        size="small"
                        variant="contained"
                        startIcon={
                          cardBusy && busy?.command === 'turn_on' ? (
                            <CircularProgress size={16} color="inherit" />
                          ) : (
                            <PowerSettingsNewIcon />
                          )
                        }
                        disabled={cardBusy}
                        aria-busy={cardBusy && busy?.command === 'turn_on'}
                        onClick={() => handleCommand(actuator, 'turn_on')}
                        sx={{ minHeight: 48 }}
                        data-testid={`turn-on-${actuator.key}`}
                      >
                        {t('pages.environmentControl.turnOn')}
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={
                          cardBusy && busy?.command === 'turn_off' ? (
                            <CircularProgress size={16} color="inherit" />
                          ) : (
                            <PowerOffIcon />
                          )
                        }
                        disabled={cardBusy}
                        aria-busy={cardBusy && busy?.command === 'turn_off'}
                        onClick={() => handleCommand(actuator, 'turn_off')}
                        sx={{ minHeight: 48 }}
                        data-testid={`turn-off-${actuator.key}`}
                      >
                        {t('pages.environmentControl.turnOff')}
                      </Button>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
              );
            })}
          </Grid>
        </>
      )}

      <ActuatorDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onCreated={handleCreated}
      />
      <ConfirmDialog
        open={emergencyOpen}
        title={t('pages.environmentControl.emergencyStop')}
        message={t('pages.environmentControl.emergencyConfirm')}
        confirmLabel={t('pages.environmentControl.emergencyStop')}
        destructive
        loading={emergencyLoading}
        onConfirm={handleEmergencyStop}
        onCancel={() => setEmergencyOpen(false)}
      />
    </Box>
  );
}
