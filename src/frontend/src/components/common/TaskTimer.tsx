import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import ReplayIcon from '@mui/icons-material/Replay';
import { useTranslation } from 'react-i18next';
import { useCountdownTimer } from '@/hooks/useCountdownTimer';

interface Props {
  durationSeconds: number;
  label?: string | null;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export default function TaskTimer({ durationSeconds, label }: Props) {
  const { t } = useTranslation();
  const { remaining, running, expired, start, pause, reset } =
    useCountdownTimer(durationSeconds);

  const progress = (remaining / durationSeconds) * 100;

  return (
    <Box
      data-testid="task-timer"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 1,
        p: 2,
      }}
    >
      {label && (
        <Typography variant="subtitle2" color="text.secondary">
          {label}
        </Typography>
      )}

      <Box sx={{ position: 'relative', display: 'inline-flex' }}>
        <CircularProgress
          variant="determinate"
          value={progress}
          size={120}
          thickness={4}
          color={expired ? 'error' : 'primary'}
        />
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            bottom: 0,
            right: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography
            variant="h5"
            component="span"
            color={expired ? 'error' : 'text.primary'}
          >
            {formatTime(remaining)}
          </Typography>
        </Box>
      </Box>

      {expired && (
        <Typography variant="body2" color="error">
          {t('pages.tasks.timerExpired')}
        </Typography>
      )}

      <Box sx={{ display: 'flex', gap: 1 }}>
        {!running && !expired && (
          <IconButton
            onClick={start}
            color="primary"
            aria-label={t('pages.tasks.timerStart')}
            data-testid="timer-start"
          >
            <PlayArrowIcon />
          </IconButton>
        )}
        {running && (
          <IconButton
            onClick={pause}
            color="primary"
            aria-label={t('pages.tasks.timerPause')}
            data-testid="timer-pause"
          >
            <PauseIcon />
          </IconButton>
        )}
        <IconButton
          onClick={reset}
          color="default"
          aria-label={t('pages.tasks.timerReset')}
          data-testid="timer-reset"
        >
          <ReplayIcon />
        </IconButton>
      </Box>
    </Box>
  );
}
