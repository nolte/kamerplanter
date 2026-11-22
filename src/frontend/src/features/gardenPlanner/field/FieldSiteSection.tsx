/**
 * Moisture and wind of a bed in the field-mode bed sheet (REQ-053 GP-FR-162/163, GP-UX-057, WP 8.22): the chips
 * "Moist / Normal / Dry" (-> `soil_profile.site_water_regime`: moist / fresh / dry) and the chip "Windy"
 * (-> `site_conditions.wind_exposure`: exposed; off -> back to the stored value, normal if that was exposed). 64 px targets (GP-UX-023). Every tap is sent at
 * once (no dirty state, GP-UX-003): the water regime through `PATCH /locations/{key}` with the stored soil
 * profile and the one key changed (the soil profile is written as a whole), the wind through the merged
 * `site_conditions`. The shown value is the tapped one until the list reload brings the stored one; a failed
 * write puts it back. Offline the controls are locked (no offline buffer before wave 9, D-23).
 *
 * On an indoor plan (GP-FR-182, WP 10.8) the "Windy" chip is not offered: wind is no feature of a windowsill.
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import { KIOSK_TOUCH_TARGET } from '@/kiosk/kioskTheme';
import { useAppSelector } from '@/store/hooks';
import { patchSiteConditions, patchSoilProfile } from '../bed/bedApi';
import ChipChoice from '../bed/ChipChoice';
import type { BedListItem, SiteWaterRegime, SoilProfile } from '../bed/types';
import { isIndoorPlanSite } from '../model/siteKind';
import { selectGardenPlanState } from '../state/gardenPlanSlice';

/** The three regimes the field offers; `fresh` is the plain "Normal". `wet` and `unknown` are set elsewhere. */
export const FIELD_WATER_REGIMES: readonly SiteWaterRegime[] = ['moist', 'fresh', 'dry'];

/** The stored profile with the regime set; a bed without a profile gets the unknown defaults for the rest. */
export function soilWithRegime(stored: SoilProfile | null | undefined, regime: SiteWaterRegime): SoilProfile {
  return (
    { ...(stored ?? { soil_texture: 'unknown', drainage: 'unknown', conditions: [] }), site_water_regime: regime } as SoilProfile
  );
}

interface FieldSiteSectionProps {
  bed: BedListItem;
  /** A viewer sees the values but cannot change them. */
  canEdit: boolean;
  /** Offline: the controls are locked instead of losing the entry. */
  online: boolean;
  /** The value was stored; the bed list reloads. */
  onChanged: () => void;
}

export default function FieldSiteSection({ bed, canEdit, online, onChanged }: FieldSiteSectionProps) {
  const { t } = useTranslation();
  const { handleError } = useApiError();
  const notification = useNotification();
  // Field mode loads the plan into the slice; its site type decides whether wind is a feature here.
  const indoor = useAppSelector((state) => isIndoorPlanSite(selectGardenPlanState(state).plan?.siteType));
  const storedRegime = bed.soil_profile?.site_water_regime ?? 'unknown';
  const storedWind = bed.site_conditions?.wind_exposure ?? 'unknown';
  const [tapped, setTapped] = useState<{ regime?: SiteWaterRegime; windy?: boolean; base: string } | null>(null);
  const [busy, setBusy] = useState(false);
  // A tapped value shows until the reload brings a different stored one.
  const base = `${storedRegime}|${storedWind}`;
  const live = tapped && (busy || tapped.base === base) ? tapped : null;
  const regime = live?.regime ?? storedRegime;
  const windy = live?.windy ?? storedWind === 'exposed';
  // Switching "Windy" off restores what was stored before (sheltered, unknown), "normal" if it was exposed.
  const windOff = storedWind === 'exposed' ? 'normal' : storedWind;

  const run = async (change: Partial<NonNullable<typeof tapped>>, write: () => Promise<unknown>) => {
    setTapped((previous) => ({ ...previous, ...change, base }));
    setBusy(true);
    try {
      await write();
      notification.success(t('pages.gardenPlan.siteConditions.field.saved'));
      onChanged();
    } catch (error) {
      setTapped(null);
      handleError(error);
    } finally {
      setBusy(false);
    }
  };

  const disabled = !canEdit || !online || busy;
  const titleId = `field-site-title-${bed.key}`;
  return (
    <Box component="section" aria-labelledby={titleId} data-testid="field-mode-site-section">
      <Typography id={titleId} variant="h6" component="h3" sx={{ mb: 1 }}>
        {t('pages.gardenPlan.siteConditions.field.title')}
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <ChipChoice
          title={t('pages.gardenPlan.siteConditions.field.moisture')}
          options={FIELD_WATER_REGIMES.map((value) => ({ value, label: t(`pages.gardenPlan.siteConditions.field.regime.${value}`) }))}
          value={[regime]}
          mode="single"
          onToggle={(option) =>
            void run({ regime: option }, () => patchSoilProfile(bed.key, soilWithRegime(bed.soil_profile, option)))
          }
          disabled={disabled}
          touchTarget={KIOSK_TOUCH_TARGET}
          testId="field-mode-site-moisture"
        />
        {!indoor && (
          <ChipChoice
            title={t('pages.gardenPlan.siteConditions.field.wind')}
            options={[{ value: 'windy', label: t('pages.gardenPlan.siteConditions.field.windy') }]}
            value={windy ? ['windy'] : []}
            mode="multiple"
            onToggle={() =>
              void run({ windy: !windy }, () =>
                patchSiteConditions(bed.key, { wind_exposure: windy ? windOff : 'exposed' }),
              )
            }
            disabled={disabled}
            touchTarget={KIOSK_TOUCH_TARGET}
            testId="field-mode-site-wind"
          />
        )}
      </Box>
    </Box>
  );
}
