import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import LinearProgress from '@mui/material/LinearProgress';
import CircularProgress from '@mui/material/CircularProgress';
import Skeleton from '@mui/material/Skeleton';
import CloudDownloadIcon from '@mui/icons-material/CloudDownload';
import RefreshIcon from '@mui/icons-material/Refresh';
import {
  useWeatherFetch,
  type WeatherFetchRefusal,
  type WeatherFetchResultOrigin,
} from '@/hooks/useWeatherFetch';
import type { WeatherFetchRun } from '@/api/types';
import { formatDateTime } from '@/utils/formatting';
import type { Translate } from '@/i18n/translate';

const HELPER_ID = 'weather-fetch-now-helper';

function triggerLabel(run: WeatherFetchRun, t: Translate): string {
  return run.trigger === 'manual'
    ? t('pages.weatherProviders.fetchStatus.triggerManual')
    : t('pages.weatherProviders.fetchStatus.triggerScheduled');
}

/**
 * The result of the run that ended after this card's trigger.
 *
 * `role="none"`: the alert sits inside one of the panel's persistent live
 * regions, which announce it; an own `role="alert"` would announce it twice.
 */
function ResultAlert({ run, origin }: { run: WeatherFetchRun; origin: WeatherFetchResultOrigin | null }) {
  const { t } = useTranslation();
  let originNote: string | null = null;
  if (origin === 'scheduledInstead') originNote = t('pages.weatherProviders.fetchNow.originScheduledInstead');
  if (origin === 'alreadyRunning') originNote = t('pages.weatherProviders.fetchNow.originAlreadyRunning');
  const note = originNote && (
    <Typography variant="body2" sx={{ mb: 0.5 }} data-testid="weather-fetch-result-origin">
      {originNote}
    </Typography>
  );
  if (run.success) {
    return (
      <Alert severity="success" data-testid="weather-fetch-result" data-origin={origin ?? undefined} role="none">
        <AlertTitle>{t('pages.weatherProviders.fetchNow.successTitle')}</AlertTitle>
        {note}
        {run.sites === 0
          ? t('pages.weatherProviders.fetchNow.successNoSites')
          : t('pages.weatherProviders.fetchNow.successDetail', {
              written: run.sites_written,
              sites: run.sites,
              forecasts: run.forecasts_written,
            })}
        {run.sites_failed > 0 && (
          <Typography variant="body2" sx={{ mt: 0.5 }}>
            {t('pages.weatherProviders.fetchNow.successFailedSites', { failed: run.sites_failed })}
          </Typography>
        )}
      </Alert>
    );
  }
  return (
    <Alert severity="error" data-testid="weather-fetch-result" data-origin={origin ?? undefined} role="none">
      <AlertTitle>{t('pages.weatherProviders.fetchNow.failedTitle')}</AlertTitle>
      {note}
      {run.error_type
        ? t('pages.weatherProviders.fetchNow.failedAborted')
        : t('pages.weatherProviders.fetchNow.failedDetail', { failed: run.sites_failed, sites: run.sites })}
    </Alert>
  );
}

/** Whether a refusal is informational (announced politely) rather than a problem. */
function isInfoRefusal(refusal: WeatherFetchRefusal): boolean {
  return refusal.kind === 'disabled';
}

/** Why "fetch now" was refused — always with the way forward. Announced by its live region (`role="none"`). */
function RefusalAlert({ refusal }: { refusal: WeatherFetchRefusal }) {
  const { t } = useTranslation();
  let severity: 'warning' | 'info' | 'error' = 'warning';
  let text: string;
  switch (refusal.kind) {
    case 'cooldown':
      text =
        refusal.availableAt !== null
          ? t('pages.weatherProviders.fetchNow.cooldown', { time: formatDateTime(new Date(refusal.availableAt)) })
          : t('pages.weatherProviders.fetchNow.cooldownUnknown');
      break;
    case 'disabled':
      severity = 'info';
      text = t('pages.weatherProviders.fetchNow.disabled');
      break;
    case 'unavailable':
      text = t('pages.weatherProviders.fetchNow.unavailable');
      break;
    default:
      severity = 'error';
      text = t('pages.weatherProviders.fetchNow.error');
  }
  return (
    <Alert severity={severity} data-testid="weather-fetch-refusal" data-refusal={refusal.kind} role="none">
      <AlertTitle>{t('pages.weatherProviders.fetchNow.refusedTitle')}</AlertTitle>
      {text}
    </Alert>
  );
}

/** One label/value row of the status readout. */
function StatusRow({ label, value, testId }: { label: string; value: string; testId: string }) {
  return (
    <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: { xs: 0, sm: 1 } }}>
      <Typography component="dt" variant="body2" color="text.secondary" sx={{ minWidth: { sm: 220 } }}>
        {label}
      </Typography>
      <Typography component="dd" variant="body2" sx={{ m: 0 }} data-testid={testId}>
        {value}
      </Typography>
    </Box>
  );
}

/**
 * REQ-046 §3.6a (#2934, F-14) — the weather fetch status and the manual
 * "fetch now" inside the installation's "Abruf-Einstellungen" card.
 *
 * Shows the newest successful and the next scheduled fetch, starts a manual
 * fetch, follows it to its result and says when a refused fetch is possible
 * again. Rendered only inside the platform-admin-gated weather section.
 */
interface WeatherFetchPanelProps {
  /** Bump to re-read the status, e.g. after the interval was saved. */
  statusVersion?: number;
}

export default function WeatherFetchPanel({ statusVersion = 0 }: WeatherFetchPanelProps) {
  const { t } = useTranslation();
  const {
    status,
    statusLoading,
    statusError,
    reloadStatus,
    phase,
    result,
    resultOrigin,
    refusal,
    cooldownUntil,
    canTrigger,
    trigger,
  } = useWeatherFetch(statusVersion);

  const busy = phase === 'starting' || phase === 'running';
  const weatherDisabled = status !== null && !status.next_scheduled_at;

  // The reason under the button: what "fetch now" does, or why it cannot run now.
  let helper = t('pages.weatherProviders.fetchNow.helper');
  if (status === null) {
    helper = statusError
      ? t('pages.weatherProviders.fetchStatus.loadError')
      : t('pages.weatherProviders.fetchNow.reasonLoading');
  } else if (weatherDisabled) {
    helper = t('pages.weatherProviders.fetchNow.disabled');
  } else if (busy || status.running === true) {
    helper = t('pages.weatherProviders.fetchNow.reasonRunning');
  } else if (status.running == null) {
    helper = t('pages.weatherProviders.fetchNow.reasonUnknown');
  } else if (cooldownUntil !== null) {
    helper = t('pages.weatherProviders.fetchNow.cooldown', { time: formatDateTime(new Date(cooldownUntil)) });
  }

  const lastSuccess = status?.last_success ?? null;
  const lastRun = status?.last_run ?? null;
  const lastRunFailed = lastRun !== null && !lastRun.success && lastRun.started_at !== lastSuccess?.started_at;

  return (
    <Box data-testid="weather-fetch-panel" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1 }}>
        <Typography component="h4" variant="subtitle2" sx={{ fontWeight: 600 }}>
          {t('pages.weatherProviders.fetchStatus.title')}
        </Typography>
        <Tooltip title={t('pages.weatherProviders.fetchStatus.refresh')}>
          <span>
            <IconButton
              onClick={() => void reloadStatus()}
              disabled={statusLoading || busy}
              aria-label={t('pages.weatherProviders.fetchStatus.refresh')}
              sx={{ minWidth: 48, minHeight: 48 }}
              data-testid="weather-fetch-status-refresh"
            >
              <RefreshIcon />
            </IconButton>
          </span>
        </Tooltip>
      </Box>

      {status === null && statusLoading && (
        <Box data-testid="weather-fetch-status-loading">
          <Skeleton variant="text" width="70%" />
          <Skeleton variant="text" width="55%" />
        </Box>
      )}
      {status === null && !statusLoading && statusError && (
        <Alert
          severity="error"
          data-testid="weather-fetch-status-error"
          action={
            <Button color="inherit" onClick={() => void reloadStatus()} sx={{ minHeight: 48, minWidth: 48 }}>
              {t('common.retry')}
            </Button>
          }
        >
          {t('pages.weatherProviders.fetchStatus.loadError')}
        </Alert>
      )}
      {status !== null && (
        <Box component="dl" sx={{ m: 0, display: 'flex', flexDirection: 'column', gap: 1 }} data-testid="weather-fetch-status">
          <StatusRow
            label={t('pages.weatherProviders.fetchStatus.lastSuccess')}
            testId="weather-fetch-last-success"
            value={
              lastSuccess
                ? t('pages.weatherProviders.fetchStatus.lastSuccessDetail', {
                    time: formatDateTime(lastSuccess.finished_at),
                    trigger: triggerLabel(lastSuccess, t),
                    written: lastSuccess.sites_written,
                    sites: lastSuccess.sites,
                  })
                : t('pages.weatherProviders.fetchStatus.lastSuccessNone')
            }
          />
          <StatusRow
            label={t('pages.weatherProviders.fetchStatus.nextScheduled')}
            testId="weather-fetch-next-scheduled"
            value={
              status.next_scheduled_at
                ? formatDateTime(status.next_scheduled_at)
                : t('pages.weatherProviders.fetchStatus.nextScheduledDisabled')
            }
          />
          <StatusRow
            label={t('pages.weatherProviders.fetchStatus.interval')}
            testId="weather-fetch-interval-effective"
            value={t('pages.weatherProviders.fetchStatus.intervalValue', { hours: status.interval_hours })}
          />
          {lastRunFailed && lastRun && (
            <Typography variant="body2" color="error" data-testid="weather-fetch-last-failed">
              {t('pages.weatherProviders.fetchStatus.lastFailed', {
                time: formatDateTime(lastRun.finished_at),
                failed: lastRun.sites_failed,
                sites: lastRun.sites,
              })}
            </Typography>
          )}
        </Box>
      )}

      <Box>
        <Button
          variant="outlined"
          onClick={() => void trigger()}
          disabled={!canTrigger}
          aria-describedby={HELPER_ID}
          aria-busy={busy}
          startIcon={busy ? <CircularProgress size={16} color="inherit" /> : <CloudDownloadIcon />}
          sx={{ minHeight: 48, width: { xs: '100%', sm: 'auto' } }}
          data-testid="weather-fetch-now-button"
        >
          {t('pages.weatherProviders.fetchNow.button')}
        </Button>
        <Typography id={HELPER_ID} variant="caption" color="text.secondary" component="p" sx={{ mt: 0.75 }}>
          {helper}
        </Typography>

        {/* Two live regions that exist from the first render on, so a screen reader
            announces what is swapped into them — a region inserted together with its
            content is often not announced. Polite: progress, a successful result, the
            time-out note and the "weather is off" note. Assertive (role="alert"): a
            failed run and a refused fetch. */}
        <Box role="status" aria-live="polite" data-testid="weather-fetch-live">
          {busy && (
            <Box data-testid="weather-fetch-progress" sx={{ mt: 2 }}>
              <LinearProgress aria-label={t('pages.weatherProviders.fetchNow.progressLabel')} />
              <Typography variant="body2" sx={{ mt: 1 }}>
                {phase === 'starting'
                  ? t('pages.weatherProviders.fetchNow.starting')
                  : t('pages.weatherProviders.fetchNow.running')}
              </Typography>
            </Box>
          )}
          {phase === 'finished' && result?.success && (
            <Box sx={{ mt: 2 }}>
              <ResultAlert run={result} origin={resultOrigin} />
            </Box>
          )}
          {phase === 'timedOut' && (
            <Alert severity="info" data-testid="weather-fetch-timed-out" role="none" sx={{ mt: 2 }}>
              {t('pages.weatherProviders.fetchNow.timedOut')}
            </Alert>
          )}
          {refusal && isInfoRefusal(refusal) && (
            <Box sx={{ mt: 2 }}>
              <RefusalAlert refusal={refusal} />
            </Box>
          )}
        </Box>
        <Box role="alert" data-testid="weather-fetch-alerts">
          {phase === 'finished' && result && !result.success && (
            <Box sx={{ mt: 2 }}>
              <ResultAlert run={result} origin={resultOrigin} />
            </Box>
          )}
          {refusal && !isInfoRefusal(refusal) && (
            <Box sx={{ mt: 2 }}>
              <RefusalAlert refusal={refusal} />
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
}
