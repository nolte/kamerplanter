import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
import MyLocationIcon from '@mui/icons-material/MyLocation';
import LocationSearchingIcon from '@mui/icons-material/LocationSearching';
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
 * explanatory tooltip outside a secure context (graceful degradation).
 */
export default function GpsDetectButton({ setValue }: Props) {
  const { t } = useTranslation();
  const { supported, available, unavailableReason, detecting, detect } = useGeolocation();

  const handleClick = useCallback(() => {
    detect(({ latitude, longitude }) => {
      setValue('gps_lat', roundCoordinate(latitude), { shouldValidate: true, shouldDirty: true });
      setValue('gps_lon', roundCoordinate(longitude), { shouldValidate: true, shouldDirty: true });
    });
  }, [detect, setValue]);

  // No Geolocation API at all: hide the affordance entirely (feature detect).
  if (!supported) return null;

  const label = t('pages.sites.gpsDetect');

  // Secure-context missing (no HTTPS/localhost): keep it visible but disabled
  // with a tooltip so the user understands why the shortcut is unavailable.
  if (!available) {
    return (
      <Tooltip title={unavailableReason ?? ''}>
        <span>
          <Button
            variant="outlined"
            startIcon={<LocationSearchingIcon />}
            disabled
            data-testid="gps-detect-button"
            sx={{ mt: 1, mb: 1.5, alignSelf: 'flex-start' }}
          >
            {label}
          </Button>
        </span>
      </Tooltip>
    );
  }

  return (
    <Button
      variant="outlined"
      startIcon={<MyLocationIcon />}
      onClick={handleClick}
      loading={detecting}
      data-testid="gps-detect-button"
      sx={{ mt: 1, mb: 1.5, alignSelf: 'flex-start' }}
    >
      {label}
    </Button>
  );
}
