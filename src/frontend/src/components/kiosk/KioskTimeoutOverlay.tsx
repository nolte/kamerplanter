import { useTranslation } from 'react-i18next';
import Backdrop from '@mui/material/Backdrop';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Modal from '@mui/material/Modal';
import Typography from '@mui/material/Typography';
import TimerIcon from '@mui/icons-material/Timer';

interface KioskTimeoutOverlayProps {
  open: boolean;
  remainingSeconds: number;
  onContinue: () => void;
}

/**
 * UI-NFR-019 §2.6 — full-area timeout warning (R-034). Covers ≥ 50% of the
 * screen (width × height fraction, viewport-relative so it holds on both 7"
 * and 10" kiosk tablets), shows a large countdown and a ≥ 72px "Weiter
 * arbeiten" button so it is operable with gloves.
 *
 * Rendered as a MUI {@link Modal} (not a bare Backdrop) so focus is trapped
 * inside the warning and the rest of the app is `aria-hidden` while it is
 * open — a Tab press can no longer reach controls hidden behind the overlay.
 * `open` is fully controlled by the parent and no `onClose` is wired, so
 * neither a backdrop touch nor the Escape key can dismiss it — only the
 * explicit "Weiter arbeiten" button can (spec: "nicht wegklickbar").
 */
export default function KioskTimeoutOverlay({
  open,
  remainingSeconds,
  onContinue,
}: KioskTimeoutOverlayProps) {
  const { t } = useTranslation();

  return (
    <Modal
      open={open}
      data-testid="kiosk-timeout-overlay"
      sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}
      slots={{ backdrop: Backdrop }}
      slotProps={{
        backdrop: { sx: { bgcolor: 'rgba(0, 0, 0, 0.85)' } },
      }}
    >
      {/* role/aria-modal/aria-labelledby/aria-describedby all live on the
          same element that carries the dialog semantics, per WAI-ARIA. */}
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
          // ≥ 50% of the screen area on any kiosk tablet: 0.92 × 0.58 ≈ 0.53.
          // No pixel maxWidth cap — capping would shrink the area fraction
          // below 50% on wider 10" landscape tablets (R-034).
          width: '92vw',
          minHeight: '58vh',
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
          autoFocus
          data-testid="kiosk-timeout-continue"
          sx={{ minHeight: 72, minWidth: 240, fontSize: '1.25rem' }}
        >
          {t('pages.kiosk.timeout.continue')}
        </Button>
      </Box>
    </Modal>
  );
}
