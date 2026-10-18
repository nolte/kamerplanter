/**
 * The soil profile of a bed (REQ-053 GP-FR-120/121): filling, grain size (with the finger test),
 * drainage, site moisture, conditions and the last measurements; for filled beds a catalogue
 * substrate that pre-fills pH and EC. Everything is optional - an empty field stays "unknown", no
 * agronomic value is invented. A viewer sees the values read-only.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useTranslation } from 'react-i18next';
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Form from '@/components/form/Form';
import FormActions from '@/components/form/FormActions';
import FormMultiSelectField from '@/components/form/FormMultiSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormRow from '@/components/form/FormRow';
import FormSelectField from '@/components/form/FormSelectField';
import FormTextField from '@/components/form/FormTextField';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { listAllSubstrates } from '@/api/endpoints/substrates';
import type { Substrate } from '@/api/types';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import { patchSoilProfile } from './bedApi';
import {
  SUBSTRATE_MEDIA,
  formToSoil,
  soilFormSchema,
  soilToForm,
  substrateDefaults,
  type SoilFormData,
} from './soilForm';
import {
  GROWING_MEDIUM_KINDS,
  PH_METHODS,
  SITE_WATER_REGIMES,
  SOIL_CONDITIONS,
  SOIL_DRAINAGES,
  SOIL_TEXTURES,
  type GrowingMediumKind,
  type SoilProfile,
} from './types';

interface SoilProfileFormProps {
  bedKey: string;
  profile: SoilProfile | null | undefined;
  canEdit: boolean;
  /** The profile was stored; the page reloads its summary. */
  onSaved: () => void;
}

export default function SoilProfileForm({ bedKey, profile, canEdit, onSaved }: SoilProfileFormProps) {
  const { t, i18n } = useTranslation();
  const { handleError } = useApiError();
  const notification = useNotification();
  const [saving, setSaving] = useState(false);
  const [substrates, setSubstrates] = useState<Substrate[]>([]);

  const initial = useMemo(() => soilToForm(profile), [profile]);
  const { control, handleSubmit, reset, setValue, getValues, formState } = useForm<SoilFormData>({
    resolver: zodResolver(soilFormSchema),
    defaultValues: initial,
    disabled: !canEdit,
  });

  // A reload of the summary (after a status change, say) hands in a new profile object. It replaces
  // the form only when its content changed and the user has no edits of their own to lose.
  const initialKey = useMemo(() => JSON.stringify(initial), [initial]);
  const dirtyRef = useRef(false);
  useEffect(() => {
    dirtyRef.current = formState.isDirty;
  });
  useEffect(() => {
    if (!dirtyRef.current) reset(initial);
    // `initial` is derived from `initialKey`; only a change of content may reset the form.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialKey, reset]);

  const medium = useWatch({ control, name: 'growing_medium_kind' });
  const substrateKey = useWatch({ control, name: 'substrate_key' });
  const showSubstrate = SUBSTRATE_MEDIA.includes(medium as GrowingMediumKind);

  // The catalogue is only needed once a substrate-filled bed asks for it.
  useEffect(() => {
    if (!showSubstrate || substrates.length > 0) return undefined;
    let cancelled = false;
    listAllSubstrates()
      .then((all) => {
        if (!cancelled) setSubstrates(all);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [showSubstrate, substrates.length]);

  const substrateOptions = useMemo(
    () => [
      { value: '', label: t('pages.bed.soil.notSet') },
      ...substrates.map((substrate) => ({
        value: substrate.key,
        label: (i18n.language.startsWith('de') ? substrate.name_de : substrate.name_en) || substrate.name_de,
      })),
    ],
    [substrates, t, i18n.language],
  );

  // GP-FR-121: a substrate the user picks here (not one loaded with the bed) pre-fills pH and EC
  // where the bed has no measurement yet.
  const substrateTouched = Boolean(formState.dirtyFields.substrate_key);
  useEffect(() => {
    if (!substrateTouched || substrateKey === '') return;
    const chosen = substrates.find((substrate) => substrate.key === substrateKey);
    const next = substrateDefaults(chosen, getValues());
    setValue('ph', next.ph, { shouldDirty: true });
    setValue('ec_ms_cm', next.ec_ms_cm, { shouldDirty: true });
  }, [substrateTouched, substrateKey, substrates, getValues, setValue]);

  const onSubmit = async (data: SoilFormData) => {
    setSaving(true);
    try {
      await patchSoilProfile(bedKey, formToSoil(data));
      notification.success(t('pages.bed.soil.saved'));
      reset(data);
      onSaved();
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  };

  const label = (group: string, value: string) => t(`enums.${group}.${value}`);

  return (
    <Box data-testid="bed-soil-tab">
      <UnsavedChangesGuard dirty={formState.isDirty} />
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {canEdit ? t('pages.bed.soil.intro') : t('pages.bed.soil.introReadOnly')}
      </Typography>
      <Form onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 720 }} aria-label={t('pages.bed.soil.title')}>
        <FormRow>
          <FormSelectField
            name="growing_medium_kind"
            control={control}
            label={t('pages.bed.soil.medium')}
            helperText={t('pages.bed.soil.mediumHelper')}
            options={[
              { value: '', label: t('pages.bed.soil.notSet') },
              ...GROWING_MEDIUM_KINDS.map((value) => ({ value, label: label('growingMediumKind', value) })),
            ]}
          />
          {showSubstrate && (
            <FormSelectField
              name="substrate_key"
              control={control}
              label={t('pages.bed.soil.substrate')}
              helperText={t('pages.bed.soil.substrateHelper')}
              options={substrateOptions}
            />
          )}
        </FormRow>

        <FormSelectField
          name="soil_texture"
          control={control}
          label={t('pages.bed.soil.texture')}
          helperText={t('pages.bed.soil.textureHelper')}
          options={SOIL_TEXTURES.map((value) => ({ value, label: label('soilTexture', value) }))}
        />
        <Accordion disableGutters variant="outlined" sx={{ mb: 2 }} data-testid="bed-soil-finger-test">
          <AccordionSummary expandIcon={<ExpandMoreIcon />} aria-controls="bed-soil-finger-body" id="bed-soil-finger-head">
            <Typography>{t('pages.bed.soil.fingerTest.title')}</Typography>
          </AccordionSummary>
          <AccordionDetails id="bed-soil-finger-body">
            <Typography variant="body2" sx={{ mb: 1 }}>
              {t('pages.bed.soil.fingerTest.intro')}
            </Typography>
            <Box component="dl" sx={{ m: 0 }}>
              {SOIL_TEXTURES.filter((value) => value !== 'unknown').map((value) => (
                <Box key={value} sx={{ mb: 1 }}>
                  <Typography component="dt" variant="subtitle2">
                    {label('soilTexture', value)}
                  </Typography>
                  <Typography component="dd" variant="body2" color="text.secondary" sx={{ m: 0 }}>
                    {t(`pages.bed.soil.fingerTest.${value}`)}
                  </Typography>
                </Box>
              ))}
            </Box>
          </AccordionDetails>
        </Accordion>

        <FormRow>
          <FormSelectField
            name="drainage"
            control={control}
            label={t('pages.bed.soil.drainage')}
            helperText={t('pages.bed.soil.drainageHelper')}
            options={SOIL_DRAINAGES.map((value) => ({ value, label: label('soilDrainage', value) }))}
          />
          <FormSelectField
            name="site_water_regime"
            control={control}
            label={t('pages.bed.soil.waterRegime')}
            helperText={t('pages.bed.soil.waterRegimeHelper')}
            options={SITE_WATER_REGIMES.map((value) => ({ value, label: label('siteWaterRegime', value) }))}
          />
        </FormRow>
        <FormMultiSelectField
          name="conditions"
          control={control}
          label={t('pages.bed.soil.conditions')}
          helperText={t('pages.bed.soil.conditionsHelper')}
          options={SOIL_CONDITIONS.map((value) => ({ value, label: label('soilCondition', value) }))}
        />

        <Typography variant="subtitle2" component="h3" sx={{ mt: 1 }}>
          {t('pages.bed.soil.measurements')}
        </Typography>
        <FormRow>
          <FormNumberField
            name="ph"
            control={control}
            label={t('pages.bed.soil.ph')}
            helperText={t('pages.bed.soil.phHelper')}
            min={0}
            max={14}
            step={0.1}
            inputMode="decimal"
          />
          <FormSelectField
            name="ph_method"
            control={control}
            label={t('pages.bed.soil.phMethod')}
            options={[
              { value: '', label: t('pages.bed.soil.notSet') },
              ...PH_METHODS.map((value) => ({ value, label: label('phMethod', value) })),
            ]}
          />
        </FormRow>
        <FormRow>
          <FormNumberField
            name="ec_ms_cm"
            control={control}
            label={t('pages.bed.soil.ec')}
            helperText={t('pages.bed.soil.ecHelper')}
            min={0}
            step="any"
            inputMode="decimal"
            suffix="mS/cm"
          />
          <FormNumberField
            name="humus_percent"
            control={control}
            label={t('pages.bed.soil.humus')}
            helperText={t('pages.bed.soil.humusHelper')}
            inputMode="decimal"
            min={0}
            max={100}
            suffix="%"
          />
        </FormRow>
        <FormTextField name="notes" control={control} label={t('pages.bed.soil.notes')} multiline minRows={2} />

        {canEdit && (
          <FormActions
            onCancel={() => reset(initial)}
            loading={saving}
            disabled={!formState.isDirty}
          />
        )}
      </Form>
    </Box>
  );
}
