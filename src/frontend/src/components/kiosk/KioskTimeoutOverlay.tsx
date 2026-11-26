import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { visuallyHidden } from '@mui/utils';
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
  /** A form on the page holds unsaved input: say that the reset discards it (R-038). */
  unsavedInput?: boolean;
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
  unsavedInput = false,
}: KioskTimeoutOverlayProps) {
  const { t } = useTranslation();

  // The visible countdown ticks every second; announcing every tick (the former `aria-live="assertive"` on
  // it) made a screen reader talk without pause and drowned out the button (#3017, W-07). The opening of
  // the alertdialog already reads the countdown through `aria-describedby`; after that only every tenth
  // second and the final five are spoken, politely.
  const [spokenSeconds, setSpokenSeconds] = useState<number | null>(null);
  const isMilestone = remainingSeconds % 10 === 0 || remainingSeconds === 5;
  if (open && isMilestone && spokenSeconds !== remainingSeconds) {
    setSpokenSeconds(remainingSeconds);
  }

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
        aria-describedby={unsavedInput ? 'kiosk-timeout-desc kiosk-timeout-unsaved' : 'kiosk-timeout-desc'}
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
        <Typography id="kiosk-timeout-desc" variant="h5" component="p">
          {t('pages.kiosk.timeout.countdown', { seconds: remainingSeconds })}
        </Typography>
        {unsavedInput && (
          <Typography
            id="kiosk-timeout-unsaved"
            variant="h6"
            component="p"
            color="error"
            sx={{ fontWeight: 700 }}
            data-testid="kiosk-timeout-unsaved"
          >
            {t('pages.kiosk.timeout.unsavedWarning')}
          </Typography>
        )}
        <Box role="status" aria-live="polite" sx={visuallyHidden} data-testid="kiosk-timeout-announcement">
          {spokenSeconds !== null ? t('pages.kiosk.timeout.countdown', { seconds: spokenSeconds }) : ''}
        </Box>
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
