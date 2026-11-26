import { useEffect, useId, useRef, useState, type MouseEvent, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { visuallyHidden } from '@mui/utils';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { KIOSK_LONG_PRESS_MS } from '@/kiosk/longPress';


interface LongPressButtonProps {
  onConfirm: () => void;
  children: ReactNode;
  holdMs?: number;
  color?: 'error' | 'primary' | 'inherit';
  variant?: 'contained' | 'outlined' | 'text';
  startIcon?: ReactNode;
  /** Visible hold instruction; defaults to "hold {{seconds}} s to confirm". */
  hint?: string;
  disabled?: boolean;
  loading?: boolean;
  'data-testid'?: string;
}

/**
 * UI-NFR-019 R-030 — a destructive action that a touch must HOLD for {@link KIOSK_LONG_PRESS_MS}.
 * A wet finger or a phantom touch on a greenhouse tablet taps; it does not hold for two seconds.
 * Used for destructive confirmations and for leaving kiosk mode (operator decision 2026-11-27).
 * A short tap does nothing but point at the hint below the button; the fill shows the progress
 * of the hold (R-053), and releasing or sliding off before the end cancels it.
 *
 * The hold is a pointer gesture only. Activation by keyboard (Enter/Space) or an assistive
 * technology's "activate" action reaches the button as a click without a pointer press
 * (`detail === 0`) and confirms at once: it is already the second, deliberate step of the
 * confirmation dialog this button sits in, which R-030 accepts on its own ("oder durch einen
 * zweistufigen Bestätigungsdialog"). A long-press-only action would lock out everyone who
 * cannot hold a pointer still (WCAG 2.5.1, 2.1.1).
 */
export default function LongPressButton({
  onConfirm,
  children,
  holdMs = KIOSK_LONG_PRESS_MS,
  color = 'error',
  variant = 'contained',
  startIcon,
  hint,
  disabled = false,
  loading = false,
  'data-testid': testId,
}: LongPressButtonProps) {
  const { t } = useTranslation();
  const hintId = useId();
  const [holding, setHolding] = useState(false);
  const [nudged, setNudged] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const fired = useRef(false);

  useEffect(() => () => clearTimeout(timer.current), []);

  const cancelHold = () => {
    if (timer.current === undefined) return;
    clearTimeout(timer.current);
    timer.current = undefined;
    setHolding(false);
    if (!fired.current) setNudged(true);
  };

  const startHold = (button: number) => {
    if (disabled || loading || button !== 0) return;
    fired.current = false;
    setHolding(true);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      timer.current = undefined;
      fired.current = true;
      setHolding(false);
      setNudged(false);
      onConfirm();
    }, holdMs);
  };

  const handleClick = (event: MouseEvent<HTMLButtonElement>) => {
    // A pointer click (detail >= 1) is the end of a press the hold timer already judged.
    if (event.detail === 0) onConfirm();
  };

  const seconds = Math.round(holdMs / 1000);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 0.5 }}>
      <Button
        variant={variant}
        color={color}
        startIcon={startIcon}
        disabled={disabled}
        loading={loading}
        aria-busy={loading}
        aria-describedby={hintId}
        onPointerDown={(e) => startHold(e.button)}
        onPointerUp={cancelHold}
        onPointerLeave={cancelHold}
        onPointerCancel={cancelHold}
        onClick={handleClick}
        // The browser's long-press menu and text selection would end the hold on a touch screen.
        onContextMenu={(e) => e.preventDefault()}
        data-testid={testId}
        data-holding={holding ? 'true' : 'false'}
        sx={{
          position: 'relative',
          overflow: 'hidden',
          userSelect: 'none',
          WebkitUserSelect: 'none',
          WebkitTouchCallout: 'none',
          touchAction: 'manipulation',
        }}
      >
        <Box
          aria-hidden="true"
          sx={{
            position: 'absolute',
            inset: 0,
            bgcolor: 'common.black',
            opacity: 0.35,
            transformOrigin: 'left',
            transform: holding ? 'scaleX(1)' : 'scaleX(0)',
            transition: holding ? `transform ${holdMs}ms linear` : 'none',
            pointerEvents: 'none',
          }}
        />
        <Box component="span" sx={{ position: 'relative' }}>
          {children}
        </Box>
      </Button>
      <Typography
        id={hintId}
        variant="body2"
        color={nudged ? 'error' : 'text.secondary'}
        sx={{ fontWeight: nudged ? 700 : 500 }}
        data-testid={testId ? `${testId}-hint` : undefined}
      >
        {hint ?? t('pages.kiosk.longPress.hint', { seconds })}
        <Box component="span" sx={visuallyHidden}>
          {` ${t('pages.kiosk.longPress.keyboardHint')}`}
        </Box>
      </Typography>
    </Box>
  );
}
