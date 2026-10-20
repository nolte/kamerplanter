/**
 * Sun window, summer sun hours and leaf shade of a bed in the field-mode bed sheet (REQ-053 GP-FR-158/159,
 * GP-UX-057, WP 7.20): the chips of the bed view with 64 px touch targets. Every change is sent at once
 * (`PATCH /locations/{key}`, merged per key by the server) - there is no dirty state (GP-UX-003). The
 * stored value shown is updated at once and corrected by the list reload; a failed write puts it back.
 * While offline the controls are locked (no offline buffer before wave 9, D-23). Leaf shade is a note only.
 */
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import { KIOSK_TOUCH_TARGET } from '@/kiosk/kioskTheme';
import { patchSun } from '../bed/bedApi';
// A static import on purpose: the section is always rendered in the sheet, and a lazy chunk that fails to
// load offline in the garden would replace the whole field-mode page with the router error page.
import SunWindowFields from '../bed/SunWindowFields';
import type { BedListItem, SunProfile, SunProfilePatch } from '../bed/types';

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
  const [busy, setBusy] = useState(false);
  const running = useRef(false);
  const queued = useRef<SunProfilePatch | null>(null);
  // While a write runs the optimistic value stays; afterwards a reload with a new stored value wins.
  const patch = pending && (busy || pending.base === stored) ? pending.patch : null;
  const shown: SunProfile = { ...stored, ...patch };

  /** Sends one change; a change made meanwhile waits in `queued` and goes out next, so no tap is lost. */
  const send = async (first: SunProfilePatch) => {
    running.current = true;
    setBusy(true);
    let next: SunProfilePatch | null = first;
    while (next) {
      try {
        await patchSun(bed.key, { sunProfile: next });
        notification.success(t('pages.gardenPlan.sun.window.saved'));
        onChanged();
      } catch (error) {
        queued.current = null;
        setPending(null);
        handleError(error);
        break;
      }
      next = queued.current;
      queued.current = null;
    }
    running.current = false;
    setBusy(false);
  };

  const change = (next: SunProfilePatch) => {
    setPending((previous) => ({ base: previous?.base ?? stored, patch: { ...previous?.patch, ...next } }));
    if (running.current) {
      queued.current = { ...queued.current, ...next };
      return;
    }
    void send(next);
  };

  return (
    <Box component="section" aria-labelledby={`field-sun-title-${bed.key}`} data-testid="field-mode-sun-section">
      <Typography id={`field-sun-title-${bed.key}`} variant="h6" component="h3" sx={{ mb: 1 }}>
        {t('pages.gardenPlan.sun.window.fieldTitle')}
      </Typography>
      <SunWindowFields
        value={shown}
        onChange={change}
        disabled={!canEdit || !online}
        touchTarget={KIOSK_TOUCH_TARGET}
        testId="field-mode-sun-profile"
      />
    </Box>
  );
}
