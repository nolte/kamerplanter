import { useCallback, useMemo, useState } from 'react';
import type { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';
import AddIcon from '@mui/icons-material/Add';
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew';
import WifiIcon from '@mui/icons-material/Wifi';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import PageTitle from '@/components/layout/PageTitle';
import EmptyState from '@/components/common/EmptyState';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ConfirmDialog from '@/components/common/ConfirmDialog';
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

export default function EnvironmentControlPage() {
  const { t } = useTranslation();
  const notification = useNotification();
  const { actuators, loading, reload } = useActuators();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [emergencyOpen, setEmergencyOpen] = useState(false);
  const [busyKey, setBusyKey] = useState<string | null>(null);

  const handleCreated = useCallback(() => {
    setDialogOpen(false);
    notification.success(t('pages.environmentControl.actuatorCreated'));
    reload();
  }, [notification, t, reload]);

  const handleCommand = useCallback(
    async (actuator: Actuator, command: 'turn_on' | 'turn_off') => {
      setBusyKey(actuator.key);
      try {
        await api.sendCommand(actuator.key, command);
        notification.success(t('pages.environmentControl.commandSent'));
        reload();
      } catch {
        notification.error(t('errors.generic'));
      } finally {
        setBusyKey(null);
      }
    },
    [notification, t, reload],
  );

  const handleEmergencyStop = useCallback(async () => {
    setEmergencyOpen(false);
    try {
      const result = await api.emergencyStop('fire_alarm');
      notification.warning(
        t('pages.environmentControl.emergencyDone', { count: result.stopped.length }),
      );
      reload();
    } catch {
      notification.error(t('errors.generic'));
    }
  }, [notification, t, reload]);

  const onlineCount = useMemo(
    () => actuators.filter((a) => a.is_online).length,
    [actuators],
  );

  return (
    <Box sx={{ p: 3 }} data-testid="environment-control-page">
      <PageTitle
        title={t('pages.environmentControl.title')}
        action={
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              color="error"
              startIcon={<ReportProblemIcon />}
              onClick={() => setEmergencyOpen(true)}
              disabled={actuators.length === 0}
              data-testid="emergency-stop-button"
            >
              {t('pages.environmentControl.emergencyStop')}
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setDialogOpen(true)}
              data-testid="create-actuator-button"
            >
              {t('pages.environmentControl.createActuator')}
            </Button>
          </Stack>
        }
      />

      <Typography color="text.secondary" sx={{ mb: 3 }}>
        {t('pages.environmentControl.intro')}
      </Typography>

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
            {actuators.map((actuator) => (
              <Grid key={actuator.key} size={{ xs: 12, sm: 6, md: 4 }}>
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
                        color={stateColor(actuator.current_state)}
                        label={t('pages.environmentControl.stateLabel', {
                          state: actuator.current_state ?? '—',
                        })}
                      />
                    </Stack>

                    {actuator.power_watts != null && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                        {actuator.power_watts} W
                      </Typography>
                    )}

                    <Stack direction="row" spacing={1}>
                      <Button
                        size="small"
                        variant="contained"
                        startIcon={<PowerSettingsNewIcon />}
                        disabled={busyKey === actuator.key}
                        onClick={() => handleCommand(actuator, 'turn_on')}
                        data-testid={`turn-on-${actuator.key}`}
                      >
                        {t('pages.environmentControl.turnOn')}
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        disabled={busyKey === actuator.key}
                        onClick={() => handleCommand(actuator, 'turn_off')}
                        data-testid={`turn-off-${actuator.key}`}
                      >
                        {t('pages.environmentControl.turnOff')}
                      </Button>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
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
        onConfirm={handleEmergencyStop}
        onCancel={() => setEmergencyOpen(false)}
      />
    </Box>
  );
}
