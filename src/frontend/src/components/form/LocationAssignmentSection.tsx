import { useMemo, useState } from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import {
  useWatch,
  type Control,
  type FieldValues,
  type Path,
} from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import FormRow from './FormRow';
import FormSelectField from './FormSelectField';
import LocationTreeSelect from './LocationTreeSelect';
import type { Site, Slot } from '@/api/types';

/**
 * Field names the cascade relies on. Both the create dialog and the detail edit
 * tab use these exact names, so they are fixed here to keep the persisted
 * contract stable (issue #543).
 */
const SITE_FIELD = 'site_key';
const LOCATION_FIELD = 'location_key';
const SLOT_FIELD = 'slot_key';

interface LocationAssignmentSectionProps<T extends FieldValues> {
  control: Control<T>;
  /** Sites available for the current tenant, already loaded by the parent. */
  sites: Site[];
  /**
   * Slots of the currently selected area, loaded and reset by the parent's
   * cascade effect. The section only presents them and derives disabled state.
   */
  slots: Slot[];
  /**
   * Visual wrapper. `card` matches the detail edit tab (outlined fieldset),
   * `inline` matches the create dialog (divider + subtitle).
   */
  variant?: 'card' | 'inline';
}

/**
 * Shared Standort → Bereich → Stellplatz (site → area → slot) cascade used by
 * both the plant-instance create dialog and the detail edit tab.
 *
 * It owns the *user-facing* explanation of empty / disabled states so the two
 * call sites stay consistent (issue #543): a site without areas, an area
 * without slots, and "pick a site/area first" are each spelled out instead of
 * silently greying a field. The parent still owns loading + cascade resets so
 * the persisted field wiring (`site_key`/`location_key`/`slot_key`) is
 * unchanged.
 */
export default function LocationAssignmentSection<T extends FieldValues>({
  control,
  sites,
  slots,
  variant = 'card',
}: LocationAssignmentSectionProps<T>) {
  const { t } = useTranslation();

  const siteKey = useWatch({ control, name: SITE_FIELD as Path<T> }) as
    | string
    | null
    | undefined;
  const locationKey = useWatch({ control, name: LOCATION_FIELD as Path<T> }) as
    | string
    | null
    | undefined;
  const slotKey = useWatch({ control, name: SLOT_FIELD as Path<T> }) as
    | string
    | null
    | undefined;

  // Number of areas the currently selected site exposes. `null` = not yet known
  // (no site chosen or tree still loading), `0` = site has no areas.
  const [areaCount, setAreaCount] = useState<number | null>(null);

  const siteHasNoAreas = !!siteKey && areaCount === 0;

  const areaHelperText = useMemo(() => {
    if (!siteKey) return t('pages.plantInstances.locationSelectSiteFirst');
    if (siteHasNoAreas) return t('pages.plantInstances.locationEmptyForSite');
    return t('pages.plantInstances.locationHelperOptional');
  }, [siteKey, siteHasNoAreas, t]);

  const slotDisabled = !locationKey || slots.length === 0;

  const slotHelperText = useMemo(() => {
    if (!siteKey) return t('pages.plantInstances.slotSelectSiteFirst');
    if (!locationKey) return t('pages.plantInstances.slotSelectAreaFirst');
    if (slots.length === 0) return t('pages.plantInstances.slotEmptyForArea');
    return t('pages.plantInstances.slotHelperOptional');
  }, [siteKey, locationKey, slots.length, t]);

  const slotOptions = useMemo(
    () => [
      { value: '', label: '—' },
      ...slots.map((s) => {
        // Occupied slots are blocked, except the one this plant already sits in
        // (edit case) so the current assignment stays selectable.
        const isCurrent = s.key === slotKey;
        const occupied = s.currently_occupied && !isCurrent;
        return {
          value: s.key,
          label: s.currently_occupied
            ? `${s.slot_id} (${t('pages.plantInstances.slotOccupied')})`
            : s.slot_id,
          disabled: occupied,
        };
      }),
    ],
    [slots, slotKey, t],
  );

  const siteOptions = useMemo(
    () => [
      { value: '', label: '—' },
      ...sites.map((s) => ({ value: s.key, label: s.name })),
    ],
    [sites],
  );

  const fields = (
    <>
      <FormRow>
        <FormSelectField
          name={SITE_FIELD as Path<T>}
          control={control}
          label={t('entities.site')}
          helperText={t('pages.plantInstances.siteHelper')}
          options={siteOptions}
        />
        <LocationTreeSelect
          name={LOCATION_FIELD as Path<T>}
          control={control}
          siteKey={siteKey}
          label={t('entities.location')}
          helperText={areaHelperText}
          emptyHelperText={t('pages.plantInstances.locationEmptyForSite')}
          onTreeLoaded={setAreaCount}
        />
      </FormRow>
      <FormSelectField
        name={SLOT_FIELD as Path<T>}
        control={control}
        label={t('entities.slot')}
        helperText={slotHelperText}
        disabled={slotDisabled}
        options={slotOptions}
      />
    </>
  );

  if (variant === 'inline') {
    return (
      <div data-testid="location-assignment-section">
        <Divider sx={{ my: 2 }} />
        <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 0.5 }}>
          {t('pages.plantInstances.sectionLocation')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          {t('pages.plantInstances.sectionLocationOptionalDesc')}
        </Typography>
        {fields}
      </div>
    );
  }

  return (
    <Card variant="outlined" data-testid="location-assignment-section">
      <CardContent
        component="fieldset"
        sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}
      >
        <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
          {t('pages.plantInstances.sectionLocation')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.plantInstances.sectionLocationOptionalDesc')}
        </Typography>
        {fields}
      </CardContent>
    </Card>
  );
}
