/**
 * Sun window, summer sun hours and leaf shade of a bed in the field-mode bed sheet (REQ-053 GP-FR-158/159,
 * GP-UX-057, WP 7.20): the chips of the bed view with 64 px touch targets. Every change is sent at once
 * (`PATCH /locations/{key}`, merged per key by the server) - there is no dirty state (GP-UX-003). The
 * stored value shown is updated at once and corrected by the list reload; a failed write puts it back.
 * While offline the controls are locked (no offline buffer before wave 9, D-23). Leaf shade is a note only.
 */
import { lazy, Suspense, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import { KIOSK_TOUCH_TARGET } from '@/kiosk/kioskTheme';
import { patchSun } from '../bed/bedApi';
import type { BedListItem, SunProfile, SunProfilePatch } from '../bed/types';

const SunWindowFields = lazy(() => import('../bed/SunWindowFields'));

interface FieldSunSectionProps {
  bed: BedListItem;
  /** A viewer sees the values but cannot change them. */
  canEdit: boolean;
  /** Offline: the controls are locked instead of losing the entry. */
  online: boolean;
  /** The sun profile was stored; the bed list reloads. */
  onChanged: () => void;
}

export default function FieldSunSection({ bed, canEdit, online, onChanged }: FieldSunSectionProps) {
  const { t } = useTranslation();
  const { handleError } = useApiError();
  const notification = useNotification();
  const stored: SunProfile | undefined = bed.site_conditions?.sun_profile;
  const [pending, setPending] = useState<{ base: SunProfile | undefined; patch: SunProfilePatch } | null>(null);
  const [saving, setSaving] = useState(false);
  // A reload brought a new stored value: it wins over the optimistic one.
  const patch = pending && pending.base === stored ? pending.patch : null;
  const shown: SunProfile = { ...stored, ...patch };

  const change = async (next: SunProfilePatch) => {
    if (saving) return;
    setPending({ base: stored, patch: { ...patch, ...next } });
    setSaving(true);
    try {
      await patchSun(bed.key, { sunProfile: next });
      notification.success(t('pages.gardenPlan.sun.window.saved'));
      onChanged();
    } catch (error) {
      setPending(null);
      handleError(error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box component="section" aria-labelledby={`field-sun-title-${bed.key}`} data-testid="field-mode-sun-section">
      <Typography id={`field-sun-title-${bed.key}`} variant="h6" component="h3" sx={{ mb: 1 }}>
        {t('pages.gardenPlan.sun.window.fieldTitle')}
      </Typography>
      <Suspense fallback={<Box sx={{ minHeight: KIOSK_TOUCH_TARGET }} aria-hidden />}>
        <SunWindowFields
          value={shown}
          onChange={(next) => void change(next)}
          disabled={!canEdit || !online || saving}
          touchTarget={KIOSK_TOUCH_TARGET}
          testId="field-mode-sun-profile"
        />
      </Suspense>
    </Box>
  );
}
