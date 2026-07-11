import { useTranslation } from 'react-i18next';
import Backdrop from '@mui/material/Backdrop';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import TimerIcon from '@mui/icons-material/Timer';

interface KioskTimeoutOverlayProps {
  open: boolean;
  remainingSeconds: number;
  onContinue: () => void;
}

/**
 * UI-NFR-019 §2.6 — full-area timeout warning (R-034). Covers ≥ 50% of the
 * screen, shows a large countdown and a ≥ 72px "Weiter arbeiten" button so it
 * is operable with gloves.
 */
export default function KioskTimeoutOverlay({
  open,
  remainingSeconds,
  onContinue,
}: KioskTimeoutOverlayProps) {
  const { t } = useTranslation();

  return (
    <Backdrop
      open={open}
      sx={{ zIndex: (theme) => theme.zIndex.modal + 1, bgcolor: 'rgba(0, 0, 0, 0.85)' }}
      data-testid="kiosk-timeout-overlay"
    >
      <Box
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="kiosk-timeout-title"
        aria-describedby="kiosk-timeout-desc"
        sx={{
          bgcolor: 'background.paper',
          color: 'text.primary',
          borderRadius: 2,
          border: '2px solid',
          borderColor: 'text.primary',
          p: { xs: 4, sm: 6 },
          textAlign: 'center',
          width: { xs: '90vw', sm: '70vw' },
          maxWidth: 640,
          minHeight: '50vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 3,
        }}
      >
        <TimerIcon aria-hidden="true" sx={{ fontSize: 96 }} />
        <Typography id="kiosk-timeout-title" variant="h3" component="h2" sx={{ fontWeight: 700 }}>
          {t('pages.kiosk.timeout.title')}
        </Typography>
        <Typography id="kiosk-timeout-desc" variant="h5" component="p" aria-live="assertive">
          {t('pages.kiosk.timeout.countdown', { seconds: remainingSeconds })}
        </Typography>
        <Button
          variant="contained"
          size="large"
          onClick={onContinue}
          data-testid="kiosk-timeout-continue"
          sx={{ minHeight: 72, minWidth: 240, fontSize: '1.25rem' }}
        >
          {t('pages.kiosk.timeout.continue')}
        </Button>
      </Box>
    </Backdrop>
  );
}
