/**
 * "My position" on the field map (REQ-053 GP-UX-026): the opt-in switch with its hints, and the dot with its
 * accuracy circle drawn over the plan.
 *
 * The switch follows the REQ-002 opt-in pattern of the site form's "Detect via browser" (`GpsDetectButton`): the
 * browser is asked only after the user's own action, an unsupported browser shows nothing, an insecure context shows
 * the switch disabled with the reason as permanent helper text, and every refusal or failure is said in words. The
 * choice is not remembered: field mode starts with the switch off on every visit.
 *
 * The position never leaves the device (SR-019): it lives in `useOwnPosition`'s state, is drawn here and is gone
 * when the switch, the map or field mode is left. The dot does not take pointer events (a tap goes to the bed below
 * it, and no click on it can end up in an error-tracking breadcrumb), and the map never pans to it - the map view is
 * remembered on the device, and a view centred on the user would store the position after all.
 */
import { useId } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormHelperText from '@mui/material/FormHelperText';
import Switch from '@mui/material/Switch';
import { alpha, useTheme } from '@mui/material/styles';
import { KIOSK_TOUCH_TARGET } from '@/kiosk/kioskTheme';
import type { Point } from '../model/types';
import type { OwnPositionHint, PlainHintReason } from './ownPositionView';

const PREFIX = 'pages.gardenPlan.field.position';

/** The i18n key of each hint without a number in it. */
const PLAIN_HINT_KEYS: Record<PlainHintReason, string> = {
  locating: 'locating',
  denied: 'denied',
  unavailable: 'unavailable',
  timeout: 'timeout',
  site_loading: 'siteLoading',
  site_error: 'siteError',
  no_gps: 'noGps',
};

/** Metres as the hints print them: whole metres below 1 km, else kilometres with one decimal. */
export function formatDistance(distanceM: number, language: string): string {
  if (distanceM < 1000) {
    return `${new Intl.NumberFormat(language, { maximumFractionDigits: 0 }).format(Math.round(distanceM))} m`;
  }
  return `${new Intl.NumberFormat(language, { maximumFractionDigits: 1 }).format(distanceM / 1000)} km`;
}

/** The accuracy as the dot's text names it: whole metres, rounded up (never claims more precision than there is). */
export function accuracyText(radiusM: number): number {
  return Math.ceil(radiusM);
}

interface OwnPositionSwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  /** The browser has a Geolocation API; without one the switch is not shown at all. */
  supported: boolean;
  /** Supported and in a secure context; otherwise the switch is disabled with the reason. */
  available: boolean;
  hint: OwnPositionHint | null;
}

export function OwnPositionSwitch({ checked, onChange, supported, available, hint }: OwnPositionSwitchProps) {
  const { t, i18n } = useTranslation();
  const descriptionId = useId();
  if (!supported) return null;

  const hintText = (() => {
    if (!hint) return null;
    switch (hint.reason) {
      case 'far':
        return t(`${PREFIX}.far`, { distance: formatDistance(hint.distanceM, i18n.language) });
      case 'outside_view':
        return hint.distanceM > 0
          ? t(`${PREFIX}.outsideViewNear`, { distance: formatDistance(hint.distanceM, i18n.language) })
          : t(`${PREFIX}.outsideView`);
      case 'coarse':
        return t(`${PREFIX}.coarse`, { accuracy: accuracyText(hint.accuracyM) });
      default:
        return t(`${PREFIX}.${PLAIN_HINT_KEYS[hint.reason]}`);
    }
  })();
  const severity = hint?.reason === 'denied' || hint?.reason === 'site_error' ? 'warning' : 'info';

  return (
    <Box sx={{ mb: 1 }} data-testid="field-mode-position">
      <FormControlLabel
        control={
          <Switch
            checked={checked && available}
            onChange={(event) => onChange(event.target.checked)}
            disabled={!available}
            slotProps={{
              input: { 'aria-describedby': descriptionId, 'data-testid': 'field-mode-position-switch' } as Record<string, string>,
            }}
          />
        }
        label={t(`${PREFIX}.label`)}
        sx={{ minHeight: KIOSK_TOUCH_TARGET, ml: 0, mr: 0 }}
      />
      <FormHelperText id={descriptionId} sx={{ mt: 0, fontSize: '1rem' }} data-testid="field-mode-position-description">
        {available ? t(`${PREFIX}.description`) : t(`${PREFIX}.insecure`)}
      </FormHelperText>
      {available && checked && hintText && (
        <Alert
          severity={severity}
          role="status"
          sx={{ mt: 1 }}
          data-testid="field-mode-position-hint"
          data-reason={hint?.reason}
        >
          {hintText}
        </Alert>
      )}
    </Box>
  );
}

interface OwnPositionDotProps {
  /** The dot's centre in screen pixels of the drawing. */
  centerPx: Point;
  /** The accuracy circle's radius in screen pixels. */
  radiusPx: number;
  /** The accuracy circle's radius in metres (≥ 3 m), for the accessible text. */
  radiusM: number;
  widthPx: number;
  heightPx: number;
}

/** The dot and its accuracy circle, as an overlay of the drawing's size. Draws nothing but itself. */
export function OwnPositionDot({ centerPx, radiusPx, radiusM, widthPx, heightPx }: OwnPositionDotProps) {
  const { t } = useTranslation();
  const { palette } = useTheme();
  const [cx, cy] = centerPx;
  const color = palette.info.main;
  return (
    <svg
      width={widthPx}
      height={heightPx}
      viewBox={`0 0 ${widthPx} ${heightPx}`}
      role="img"
      aria-label={t(`${PREFIX}.dot`, { accuracy: accuracyText(radiusM) })}
      data-testid="field-mode-position-dot"
      data-accuracy-m={accuracyText(radiusM)}
      style={{ position: 'absolute', left: 0, top: 0, pointerEvents: 'none', overflow: 'hidden' }}
    >
      <circle
        cx={cx}
        cy={cy}
        r={radiusPx}
        fill={alpha(color, 0.15)}
        stroke={color}
        strokeWidth={2}
        data-testid="field-mode-position-accuracy"
      />
      <circle cx={cx} cy={cy} r={9} fill={color} stroke={palette.background.paper} strokeWidth={3} />
      <circle cx={cx} cy={cy} r={10.5} fill="none" stroke={palette.text.primary} strokeWidth={1} />
    </svg>
  );
}
