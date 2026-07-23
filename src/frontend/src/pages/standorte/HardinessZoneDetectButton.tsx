import { useCallback, useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import FormHelperText from '@mui/material/FormHelperText';
import Tooltip from '@mui/material/Tooltip';
import TravelExploreIcon from '@mui/icons-material/TravelExplore';
import { resolveSiteHardinessZone } from '@/api/endpoints/sites';
import { isApiError } from '@/api/errors';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';

interface Props {
  /** Key of the persisted site whose zone should be derived. */
  siteKey: string;
  /** Whether the *saved* site carries GPS coordinates (the resolver reads those). */
  gpsPresent: boolean;
  /** Called after a successful resolution so the parent can reload the site. */
  onResolved: () => void;
}

/**
 * "Derive climate zone from GPS" control for the site detail form (REQ-039/041).
 * Calls `POST /sites/{key}/resolve-hardiness-zone`, which fetches the site's
 * climate normals on demand and writes the derived USDA zone into both
 * `hardiness_zone` and the legacy `climate_zone` shown in the dropdown.
 *
 * Rendered only for members who may edit (admin/grower — the endpoint rejects
 * `viewer`). It reads the *saved* GPS coordinates, so it stays disabled — with a
 * hover tooltip and permanent, `aria-describedby`-linked helper text for
 * touch/kiosk users (UI-NFR-019) — until coordinates are stored.
 */
export default function HardinessZoneDetectButton({ siteKey, gpsPresent, onResolved }: Props) {
  const { t } = useTranslation();
  const { canEdit } = useTenantPermissions();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [resolving, setResolving] = useState(false);
  const reasonId = useId();

  const handleClick = useCallback(async () => {
    try {
      setResolving(true);
      const res = await resolveSiteHardinessZone(siteKey);
      if (res.hardiness_zone) {
        notification.success(t('pages.sites.hardinessResolved', { zone: res.hardiness_zone }));
      } else {
        notification.info(t('pages.sites.hardinessNotAvailable'));
      }
      onResolved();
    } catch (err) {
      // The resolver returns 422 when no usable climate normals could be
      // obtained for the coordinates (e.g. weather integration disabled).
      if (isApiError(err) && err.statusCode === 422) {
        notification.info(t('pages.sites.hardinessNotAvailable'));
      } else {
        handleError(err);
      }
    } finally {
      setResolving(false);
    }
  }, [siteKey, notification, handleError, onResolved, t]);

  // Viewers cannot trigger a derivation — hide the affordance entirely.
  if (!canEdit) return null;

  const label = t('pages.sites.hardinessDetect');

  if (!gpsPresent) {
    return (
      <Box sx={{ mt: 1, mb: 1.5 }}>
        <Tooltip title={t('pages.sites.hardinessNeedsGps')}>
          <span tabIndex={0}>
            <Button
              variant="outlined"
              startIcon={<TravelExploreIcon />}
              disabled
              aria-describedby={reasonId}
              data-testid="hardiness-detect-button"
              sx={{ alignSelf: 'flex-start' }}
            >
              {label}
            </Button>
          </span>
        </Tooltip>
        <FormHelperText id={reasonId} sx={{ mt: 0.5 }}>
          {t('pages.sites.hardinessNeedsGps')}
        </FormHelperText>
      </Box>
    );
  }

  return (
    <Button
      variant="outlined"
      startIcon={<TravelExploreIcon />}
      onClick={handleClick}
      loading={resolving}
      aria-busy={resolving}
      data-testid="hardiness-detect-button"
      sx={{ mt: 1, mb: 1.5, alignSelf: 'flex-start' }}
    >
      {label}
    </Button>
  );
}
