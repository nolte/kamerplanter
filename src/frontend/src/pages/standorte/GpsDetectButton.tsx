import { useCallback, useId } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import FormHelperText from '@mui/material/FormHelperText';
import Tooltip from '@mui/material/Tooltip';
import MyLocationIcon from '@mui/icons-material/MyLocation';
import LocationDisabledIcon from '@mui/icons-material/LocationDisabled';
import type { UseFormSetValue } from 'react-hook-form';
import { useGeolocation } from '@/hooks/useGeolocation';
import type { SiteFormData } from './siteForm';

interface Props {
  /** `setValue` from the shared site `useForm`, used to fill the GPS fields. */
  setValue: UseFormSetValue<SiteFormData>;
}

// GPS coordinates are stored with ~6 decimals (~0.1 m), well beyond consumer
// GPS accuracy — trimming the browser's long floats keeps the form tidy.
const GPS_DECIMALS = 6;
const roundCoordinate = (value: number): number => Number(value.toFixed(GPS_DECIMALS));

/**
 * Opt-in "detect via browser" control for the site coordinate fields (REQ-002).
 * On success it fills `gps_lat`/`gps_lon` through the shared form's `setValue`
 * (triggering the existing both-or-neither + range validation); on failure the
 * hook shows a localised toast and the fields stay untouched. Renders nothing
 * when the browser has no Geolocation API, and stays disabled with an
 * explanatory tooltip *and* persistent helper text outside a secure context
 * (graceful degradation) — the helper text keeps the reason readable for
 * touch/kiosk users who have no hover state (UI-NFR-019).
 */
export default function GpsDetectButton({ setValue }: Props) {
  const { t } = useTranslation();
  const { supported, available, unavailableReason, detecting, detect } = useGeolocation();
  const reasonId = useId();

  const handleClick = useCallback(() => {
    detect(({ latitude, longitude }) => {
      setValue('gps_lat', roundCoordinate(latitude), { shouldValidate: true, shouldDirty: true });
      setValue('gps_lon', roundCoordinate(longitude), { shouldValidate: true, shouldDirty: true });
    });
  }, [detect, setValue]);

  // No Geolocation API at all: hide the affordance entirely (feature detect).
  if (!supported) return null;

  const label = t('pages.sites.gpsDetect');

  // Secure-context missing (no HTTPS/localhost): keep it visible but disabled.
  // The reason is shown both as a hover/focus tooltip (mouse + keyboard, via
  // `tabIndex` on the wrapping span since a disabled <button> cannot receive
  // focus itself) and as permanent helper text linked via `aria-describedby` —
  // touch/kiosk screens have no hover state, so the tooltip alone would leave
  // those users without an explanation.
  if (!available) {
    return (
      <Box sx={{ mt: 1, mb: 1.5 }}>
        <Tooltip title={unavailableReason ?? ''}>
          <span tabIndex={0}>
            <Button
              variant="outlined"
              startIcon={<LocationDisabledIcon />}
              disabled
              aria-describedby={reasonId}
              data-testid="gps-detect-button"
              sx={{ alignSelf: 'flex-start' }}
            >
              {label}
            </Button>
          </span>
        </Tooltip>
        <FormHelperText id={reasonId} sx={{ mt: 0.5 }}>
          {unavailableReason}
        </FormHelperText>
      </Box>
    );
  }

  return (
    <Button
      variant="outlined"
      startIcon={<MyLocationIcon />}
      onClick={handleClick}
      loading={detecting}
      aria-busy={detecting}
      data-testid="gps-detect-button"
      sx={{ mt: 1, mb: 1.5, alignSelf: 'flex-start' }}
    >
      {label}
    </Button>
  );
}
