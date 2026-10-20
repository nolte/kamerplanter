/**
 * Change the sun and shade of one bed from the bed view (REQ-053 GP-FR-157/158/159, GP-API-010): the
 * tiles of the plan editor plus the sun window chips, the summer sun hours and the leaf-shade switch in a
 * dialog, stored with ONE `PATCH /locations/{key}`. The editor stores the class through the plan batch;
 * here a bed that is not on the plan can be classified too. Nothing is computed (§29); leaf shade is a
 * note only and does not change the site-fit hint.
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import type { SunExposure } from '../model/types';
import { patchSun } from './bedApi';
import SunTileSelector from './SunTileSelector';
import SunWindowFields from './SunWindowFields';
import type { SunProfile, SunProfilePatch } from './types';

interface SunDialogProps {
  bedKey: string;
  bedName: string;
  current: SunExposure;
  /** The stored `site_conditions.sun_profile`; absent = nothing recorded. */
  currentProfile?: SunProfile | null;
  onClose: () => void;
  /** The class was stored; the page reloads its summary. */
  onChanged: () => void;
}

export default function SunDialog({ bedKey, bedName, current, currentProfile, onClose, onChanged }: SunDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { handleError } = useApiError();
  const notification = useNotification();
  const [chosen, setChosen] = useState<SunExposure>(current);
  const [profilePatch, setProfilePatch] = useState<SunProfilePatch>({});
  const [saving, setSaving] = useState(false);
  const [hoursValid, setHoursValid] = useState(true);
  const stored: SunProfile = currentProfile ?? {};
  const shown: SunProfile = { ...stored, ...profilePatch };

  /** Only the keys that differ from what is stored go out; a key set back to its stored value drops out. */
  const changedProfile = (): SunProfilePatch => {
    const out: SunProfilePatch = {};
    if (profilePatch.sun_window !== undefined && profilePatch.sun_window !== (stored.sun_window ?? 'unknown')) {
      out.sun_window = profilePatch.sun_window;
    }
    if (
      profilePatch.direct_sun_hours_summer !== undefined &&
      profilePatch.direct_sun_hours_summer !== (stored.direct_sun_hours_summer ?? null)
    ) {
      out.direct_sun_hours_summer = profilePatch.direct_sun_hours_summer;
    }
    if (
      profilePatch.foliage_shade_in_summer !== undefined &&
      profilePatch.foliage_shade_in_summer !== (stored.foliage_shade_in_summer ?? false)
    ) {
      out.foliage_shade_in_summer = profilePatch.foliage_shade_in_summer;
    }
    return out;
  };

  const submit = async () => {
    // An unreadable hours entry is shown in red under the field; saving waits until it is fixed or cleared.
    if (!hoursValid) return;
    const profile = changedProfile();
    const profileChanged = Object.keys(profile).length > 0;
    if (chosen === current && !profileChanged) {
      onClose();
      return;
    }
    setSaving(true);
    try {
      await patchSun(bedKey, {
        ...(chosen !== current ? { sunExposure: chosen } : {}),
        ...(profileChanged ? { sunProfile: profile } : {}),
      });
      notification.success(t('pages.gardenPlan.sun.dialog.saved'));
      onChanged();
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open
      onClose={saving ? undefined : onClose}
      fullScreen={fullScreen}
      maxWidth="md"
      fullWidth
      aria-labelledby="bed-sun-title"
      data-testid="bed-sun-dialog"
    >
      <DialogTitle id="bed-sun-title">{t('pages.gardenPlan.sun.dialog.title', { bed: bedName })}</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {t('pages.gardenPlan.sun.hint')}
        </Typography>
        <SunTileSelector value={chosen} onChange={setChosen} disabled={saving} />
        <SunWindowFields
          value={shown}
          onChange={(patch) => setProfilePatch((previous) => ({ ...previous, ...patch }))}
          disabled={saving}
          onValidityChange={setHoursValid}
          testId="bed-view-sun-profile"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          {t('pages.gardenPlan.sun.dialog.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={() => void submit()}
          loading={saving}
          data-testid="bed-sun-submit"
        >
          {t('pages.gardenPlan.sun.dialog.save')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
