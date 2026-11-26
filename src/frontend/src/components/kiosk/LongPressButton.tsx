import {
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
  type MouseEvent,
  type PointerEvent,
  type ReactNode,
} from 'react';
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
  /**
   * Keep the hint out of the layout until a short tap asks for it (a compact app bar); it is then
   * shown under the button. Assistive technology reads it either way.
   */
  compactHint?: boolean;
  /** Accessible name when the visible content is only an icon on small screens. */
  'aria-label'?: string;
  disabled?: boolean;
  loading?: boolean;
  'data-testid'?: string;
}

/**
 * UI-NFR-019 R-030 — a destructive action that a touch must HOLD for {@link KIOSK_LONG_PRESS_MS}.
 * A wet finger or a phantom touch on a greenhouse tablet taps; it does not hold for two seconds.
 * Used for destructive confirmations and for leaving kiosk mode (operator decision 2026-11-27).
 * A short tap does nothing but point at the hint; the fill shows the progress of the hold (R-053).
 * Lifting the finger, sliding it off the button (also while the touch is captured, which is the
 * normal case on a touch screen), a cancelled pointer or the button becoming disabled (the dialog
 * starts closing) ends the hold without confirming.
 *
 * The hold is the gesture of a pointer that PRESSES the button. A click that no press on this
 * button preceded confirms at once: Enter/Space (`detail === 0`) and an assistive technology's
 * "activate" action, which dispatches a click without a press. It is the deliberate second step of
 * the dialog or control this button sits in, which R-030 accepts on its own ("oder durch einen
 * zweistufigen Bestätigungsdialog"); a phantom touch always presses, so it gains nothing from it.
 * A held Enter key confirms once, not once per key repeat.
 */
export default function LongPressButton({
  onConfirm,
  children,
  holdMs = KIOSK_LONG_PRESS_MS,
  color = 'error',
  variant = 'contained',
  startIcon,
  hint,
  compactHint = false,
  'aria-label': ariaLabel,
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
  // Whether the click about to arrive ends a press on this button (pointer path) or not (AT path).
  const pressed = useRef(false);
  const pressId = useRef(0);
  const pointerType = useRef<string>('');

  useEffect(() => () => clearTimeout(timer.current), []);

  // A dialog that starts closing disables the button: a hold still running must not fire into it.
  useEffect(() => {
    if (!disabled && !loading) return;
    clearTimeout(timer.current);
    timer.current = undefined;
  }, [disabled, loading]);

  const endHold = (nudge: boolean) => {
    if (timer.current === undefined) return;
    clearTimeout(timer.current);
    timer.current = undefined;
    setHolding(false);
    if (nudge && !fired.current) setNudged(true);
  };

  const handlePointerDown = (event: PointerEvent<HTMLButtonElement>) => {
    if (disabled || loading || event.button !== 0 || event.isPrimary === false) return;
    pressed.current = true;
    pressId.current += 1;
    pointerType.current = event.pointerType;
    // A touch pointer is captured implicitly, so `pointerleave` would only arrive on lift. Release
    // it: sliding off the button then ends the hold as the hint says.
    const target = event.currentTarget;
    if (typeof target.hasPointerCapture === 'function' && target.hasPointerCapture(event.pointerId)) {
      target.releasePointerCapture(event.pointerId);
    }
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

  // Belt and braces for engines that keep the capture: compare the point with the button itself.
  const handlePointerMove = (event: PointerEvent<HTMLButtonElement>) => {
    if (timer.current === undefined) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const inside =
      event.clientX >= rect.left &&
      event.clientX <= rect.right &&
      event.clientY >= rect.top &&
      event.clientY <= rect.bottom;
    if (!inside) endHold(true);
  };

  const handlePointerUp = () => {
    endHold(true);
    // The click of this press follows in the same task; after it, an unpressed click is AT again
    // (a press released off the button produces no click here and must not swallow the next one).
    const id = pressId.current;
    setTimeout(() => {
      if (pressId.current === id) pressed.current = false;
    }, 0);
  };

  const handlePointerCancel = () => {
    endHold(true);
    pressed.current = false;
  };

  const handleContextMenu = (event: MouseEvent<HTMLButtonElement>) => {
    // The browser's long-press menu and text selection would end the hold on a touch screen. A
    // touch long press raises `contextmenu` by design, so only a mouse's one ends the hold.
    event.preventDefault();
    if (pointerType.current === 'mouse') endHold(false);
  };

  const handleClick = () => {
    if (pressed.current) {
      // The end of a press the hold timer already judged.
      pressed.current = false;
      return;
    }
    onConfirm();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    pressed.current = false;
    // A held Enter repeats keydown, and each one would click the button again.
    if (event.repeat && (event.key === 'Enter' || event.key === ' ')) event.preventDefault();
  };

  const seconds = Math.round(holdMs / 1000);
  const hintText = hint ?? t('pages.kiosk.longPress.hint', { seconds });
  const hideHint = compactHint && !nudged;

  return (
    <Box
      sx={{
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
        gap: 0.5,
      }}
    >
      <Button
        variant={variant}
        color={color}
        startIcon={startIcon}
        disabled={disabled}
        loading={loading}
        aria-busy={loading}
        aria-label={ariaLabel}
        aria-describedby={hintId}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerLeave={() => endHold(true)}
        onPointerCancel={handlePointerCancel}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        onContextMenu={handleContextMenu}
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
        <Box component="span" sx={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
          {children}
        </Box>
      </Button>
      <Typography
        id={hintId}
        variant="body2"
        color={nudged ? 'error' : 'text.secondary'}
        sx={[
          { fontWeight: nudged ? 700 : 500 },
          hideHint && visuallyHidden,
          compactHint &&
            !hideHint && {
              position: 'absolute',
              top: '100%',
              right: 0,
              mt: 0.5,
              px: 1,
              py: 0.5,
              whiteSpace: 'nowrap',
              bgcolor: 'background.paper',
              border: 1,
              borderColor: 'error.main',
              borderRadius: 1,
              zIndex: 1,
            },
        ]}
        data-testid={testId ? `${testId}-hint` : undefined}
      >
        {hintText}
        <Box component="span" sx={visuallyHidden}>
          {` ${t('pages.kiosk.longPress.keyboardHint')}`}
        </Box>
      </Typography>
    </Box>
  );
}
