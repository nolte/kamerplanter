import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Alert from '@mui/material/Alert';
import LinearProgress from '@mui/material/LinearProgress';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Form from '@/components/form/Form';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormChipInput from '@/components/form/FormChipInput';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import ExpertiseFieldWrapper from '@/components/common/ExpertiseFieldWrapper';
import ShowAllFieldsToggle from '@/components/common/ShowAllFieldsToggle';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { useAppDispatch } from '@/store/hooks';
import { resetShowAllFields } from '@/store/slices/uiSlice';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useNavigate } from 'react-router-dom';
import Button from '@mui/material/Button';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useCatalogue } from '@/hooks/useCatalogue';
import { useRetryFocus } from '@/hooks/useRetryFocus';
import LoadingStatus from '@/components/common/LoadingStatus';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import { speciesFieldConfig } from '@/config/fieldConfigs';
import * as speciesApi from '@/api/endpoints/species';
import type { GrowthHabit, PhotosynthesisType } from '@/api/types';

/** growth_habit enum values — mirrors GrowthHabit in api/types.ts (SSOT: backend GrowthHabit). */
const GROWTH_HABITS = [
  'herb',
  'shrub',
  'subshrub',
  'tree',
  'vine',
  'groundcover',
  'grass',
  'succulent',
  'bulb_geophyte',
  'fern',
  'aquatic',
  'epiphyte',
] as const satisfies readonly GrowthHabit[];

/** photosynthesis_type enum values — mirrors PhotosynthesisType in api/types.ts. */
const PHOTOSYNTHESIS_TYPES = ['c3', 'c4', 'cam'] as const satisfies readonly PhotosynthesisType[];

const schema = z.object({
  scientific_name: z.string().min(1),
  common_names: z.array(z.string()),
  family_key: z.string().nullable(),
  genus: z.string(),
  growth_habit: z.enum(GROWTH_HABITS),
  // Empty string = "no selection" from the MUI select; normalised to null on submit.
  photosynthesis_type: z.enum(PHOTOSYNTHESIS_TYPES).or(z.literal('')).nullable(),
  root_type: z.enum(['fibrous', 'taproot', 'tuberous', 'bulbous']),
  hardiness_zones: z.array(z.string()),
  native_habitat: z.string(),
  allelopathy_score: z.number().min(-1).max(1),
  base_temp: z.number(),
  description: z.string(),
  synonyms: z.array(z.string()),
  taxonomic_authority: z.string(),
  taxonomic_status: z.string(),
  container_suitable: z.enum(['yes', 'limited', 'no', '']).nullable(),
  recommended_container_volume_l: z.string(),
  min_container_depth_cm: z.number().min(1).max(200).nullable(),
  mature_height_cm: z.string(),
  mature_width_cm: z.string(),
  spacing_cm: z.string(),
  indoor_suitable: z.enum(['yes', 'limited', 'no', '']).nullable(),
  balcony_suitable: z.enum(['yes', 'limited', 'no', '']).nullable(),
  greenhouse_recommended: z.boolean(),
  support_required: z.boolean(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function SpeciesCreateDialog({ open, onClose, onCreated }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const dispatch = useAppDispatch();
  const [saving, setSaving] = useState(false);
  // The botanical-family catalogue comes from the shared reader (#1568). What it
  // replaced was `listAllBotanicalFamilies().then(setFamilies).catch(() => {})`:
  // on a failed load the mandatory "Familie" field showed nothing but its
  // placeholder — no message, no retry — and the user created a species without
  // a family, believing none applied. There was no in-flight state either, and
  // no ignore guard, so closing and reopening the dialog started a second
  // sequence whose late answer could overwrite the live one.
  const families = useCatalogue('botanicalFamilies', { enabled: open });
  // After a retry succeeds, focus the control the user was trying to reach.
  // `FormSelectField` documents `[role='combobox']` as the stable trigger
  // selector, which is also what its own tests address.
  const { attachRegion: attachFamilyRegion, beginRetry: beginFamilyRetry } = useRetryFocus(
    families.status,
    "[data-testid='form-field-family_key'] [role='combobox']",
    { enabled: open },
  );
  const { showAllOverride, toggleShowAll, level } = useExpertiseLevel();

  const handleClose = useCallback(() => {
    dispatch(resetShowAllFields());
    onClose();
  }, [dispatch, onClose]);

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      scientific_name: '',
      common_names: [],
      family_key: null,
      genus: '',
      growth_habit: 'herb',
      photosynthesis_type: null,
      root_type: 'fibrous',
      hardiness_zones: [],
      native_habitat: '',
      allelopathy_score: 0,
      base_temp: 10,
      description: '',
      synonyms: [],
      taxonomic_authority: '',
      taxonomic_status: '',
      container_suitable: null,
      recommended_container_volume_l: '',
      min_container_depth_cm: null,
      mature_height_cm: '',
      mature_width_cm: '',
      spacing_cm: '',
      indoor_suitable: null,
      balcony_suitable: null,
      greenhouse_recommended: false,
      support_required: false,
    },
  });


  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      const payload = {
        ...data,
        photosynthesis_type: data.photosynthesis_type || null,
        container_suitable: data.container_suitable || null,
        indoor_suitable: data.indoor_suitable || null,
        balcony_suitable: data.balcony_suitable || null,
      };
      await speciesApi.createSpecies(payload);
      notification.success(t('common.create'));
      reset();
      onCreated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const fc = speciesFieldConfig;

  return (
    <>
    {/*
      The warning that makes the CTA above acceptable. Hung on the form's real
      dirty state — `isDirty` — because a loss warning shown over an untouched
      form is noise, and a warning users have learned to click through is not
      there for the one time it matters. `&& open` mirrors the established usage
      in `OverwinteringProfileDialog` and `DiaryEntryDialog`: a closed dialog has
      nothing to lose.

      This is the project's existing mechanism (30+ call sites), not a second one
      placed beside it: `useBlocker` intercepts the route change and
      `ConfirmDialog` — `role="alertdialog"`, cancel `autoFocus` — offers both
      ways with "stay" as the lighter one.
    */}
    <UnsavedChangesGuard dirty={isDirty && open} />
    <Dialog fullScreen={fullScreen} open={open} onClose={handleClose} maxWidth="sm" fullWidth data-testid="species-create-dialog"
      aria-labelledby="species-create-dialog-title">
      <DialogTitle id="species-create-dialog-title">{t('pages.species.create')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.species.createIntro')}
        </Typography>
        <Form onSubmit={handleSubmit(onSubmit)}>
          {/* --- Taxonomy section --- */}
          <Typography variant="subtitle2" sx={{ mb: 1, mt: 2 }}>
            {t('pages.species.sectionTaxonomy')}
          </Typography>
          <ExpertiseFieldWrapper minLevel={fc.scientific_name.level}>
            <FormTextField
              name="scientific_name"
              control={control}
              label={t('pages.species.scientificName')}
              helperText={t('pages.species.scientificNameHelper')}
              required
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.common_names.level}>
            <FormChipInput
              name="common_names"
              control={control}
              label={t('pages.species.commonNames')}
              helperText={t('pages.species.commonNamesHelper')}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.family_key.level}>
            {/*
              A failed family load is now its own state with its own retry, not
              an empty dropdown (#1568), and the field is not operable while the
              catalogue is in flight or unreachable.

              What that does **not** do, stated because an earlier version of
              this comment claimed it: it does not stop the species being created
              without a family. `family_key` is nullable in the schema (see the
              zod object above), defaults to `null`, and `FormActions` is not
              coupled to `families.status` — so on a failed load the user still
              submits, the field is merely unusable rather than merely silent.
              Making the claim true means either blocking submit or making
              `family_key` required, which is a behaviour change for the operator
              to decide, not a review fix.
            */}
            <Box ref={attachFamilyRegion}>
              <FormSelectField
                name="family_key"
                control={control}
                label={t('pages.species.family')}
                helperText={
                  families.status === 'loading'
                    ? t('pages.species.familyLoading')
                    : t('pages.species.familyHelper')
                }
                disabled={families.status !== 'ready'}
                options={[
                  { value: '', label: '—' },
                  ...families.items.map((f) => ({ value: f.key, label: f.name })),
                ]}
              />
              {/*
                The announcement half, and it is mounted unconditionally on
                purpose (UI-NFR-002 §2.3 R-011, WCAG 2.2 AA 4.1.3). A live region
                has to exist *before* its content changes for the change to be
                announced — see property 4 in `LoadingStatus`. Rendering it only
                while loading would insert region and content together on the
                first load and, worse, announce nothing at all on the
                `failed → loading → ready` path a retry takes.

                `active` carries the content, so the region is empty and unnamed
                once the catalogue is there and says nothing to a user who
                navigates onto it later.
              */}
              <LoadingStatus
                label={t('pages.species.familyLoading')}
                active={families.status === 'loading'}
                data-testid="family-catalogue-loading-status"
              />
              {/*
                The *visual* half (UI-NFR-004 §2.5 R-020, which asks for a
                spinner, progress bar or skeleton — a helper text is none of the
                three). Without it a sighted first-time user reads the greyed-out
                dropdown as broken rather than as loading.

                A bar rather than the activity dialog's centred spinner: same
                vocabulary (an MUI progress indicator), applied at the scale of
                the surface — one form field here, a whole list region there.
              */}
              {families.status === 'loading' && (
                <LinearProgress
                  aria-hidden
                  sx={{ mt: -1, mb: 1.5 }}
                  data-testid="family-catalogue-loading"
                />
              )}
              {families.status === 'failed' && (
                <Box data-testid="family-catalogue-error">
                  <ErrorDisplay
                    error={families.error ?? 'errors.loadFailed'}
                    onRetry={() => {
                      // Arm the focus restore before the state flips, because the
                      // button this click landed on is about to unmount.
                      beginFamilyRetry();
                      families.reload();
                    }}
                  />
                </Box>
              )}
            </Box>
            {families.isEmpty && (
              <Alert
                severity="info"
                sx={{ mb: 1.5 }}
                data-testid="family-catalogue-empty"
                action={
                  /*
                    R-014: an empty state carries a way out, not only a
                    description (UI-NFR-004 §3.2). Operator decision, taken
                    against the UI reviewer's advice — the reviewer objected that
                    navigating away pulls the user out of the task they are in
                    the middle of. The objection is answered rather than
                    overruled: `UnsavedChangesGuard` below blocks the navigation
                    whenever this form actually holds input, and its
                    `ConfirmDialog` autofocuses "cancel", so staying is the
                    default and leaving is the deliberate act.
                  */
                  <Button
                    color="inherit"
                    size="small"
                    onClick={() => navigate('/stammdaten/botanical-families')}
                    data-testid="family-catalogue-empty-cta"
                  >
                    {t('pages.species.familyCatalogueEmptyCta')}
                  </Button>
                }
              >
                {t('pages.species.familyCatalogueEmpty')}
              </Alert>
            )}
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.genus.level}>
            <FormTextField
              name="genus"
              control={control}
              label={t('pages.species.genus')}
              helperText={t('pages.species.genusHelper')}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.description.level}>
            <FormTextField
              name="description"
              control={control}
              label={t('pages.species.description')}
              helperText={t('pages.species.descriptionHelper')}
              multiline
              rows={3}
            />
          </ExpertiseFieldWrapper>

          {/* --- Growth section --- */}
          <Typography variant="subtitle2" sx={{ mb: 1, mt: 2 }}>
            {t('pages.species.sectionGrowth')}
          </Typography>
          <ExpertiseFieldWrapper minLevel={fc.growth_habit.level}>
            <FormSelectField
              name="growth_habit"
              control={control}
              label={t('pages.species.growthHabit')}
              helperText={t('pages.species.growthHabitHelper')}
              options={GROWTH_HABITS.map((v) => ({
                value: v,
                label: t(`enums.growthHabit.${v}`),
              }))}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.photosynthesis_type.level}>
            <FormSelectField
              name="photosynthesis_type"
              control={control}
              label={t('pages.species.photosynthesisType')}
              helperText={t('pages.species.photosynthesisTypeHelper')}
              options={[
                { value: '', label: '—' },
                ...PHOTOSYNTHESIS_TYPES.map((v) => ({
                  value: v,
                  label: t(`enums.photosynthesisType.${v}`),
                })),
              ]}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.root_type.level}>
            <FormSelectField
              name="root_type"
              control={control}
              label={t('pages.species.rootType')}
              helperText={t('pages.species.rootTypeHelper')}
              options={['fibrous', 'taproot', 'tuberous', 'bulbous'].map((v) => ({
                value: v,
                label: t(`enums.rootType.${v}`),
              }))}
            />
          </ExpertiseFieldWrapper>

          {/* --- Environment section --- */}
          <Typography variant="subtitle2" sx={{ mb: 1, mt: 2 }}>
            {t('pages.species.sectionEnvironment')}
          </Typography>
          <ExpertiseFieldWrapper minLevel={fc.hardiness_zones.level}>
            <FormChipInput
              name="hardiness_zones"
              control={control}
              label={t('pages.species.hardinessZones')}
              helperText={t('pages.species.hardinessZonesHelper')}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.native_habitat.level}>
            <FormTextField
              name="native_habitat"
              control={control}
              label={t('pages.species.nativeHabitat')}
              helperText={t('pages.species.nativeHabitatHelper')}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.allelopathy_score.level}>
            <FormNumberField
              name="allelopathy_score"
              control={control}
              label={t('pages.species.allelopathyScore')}
              helperText={t('pages.species.allelopathyScoreHelper')}
              min={-1}
              max={1}
              step={0.1}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.base_temp.level}>
            <FormNumberField
              name="base_temp"
              control={control}
              label={t('pages.species.baseTemp')}
              helperText={t('pages.species.baseTempHelper')}
            />
          </ExpertiseFieldWrapper>

          {/* --- Classification section --- */}
          <Typography variant="subtitle2" sx={{ mb: 1, mt: 2 }}>
            {t('pages.species.sectionClassification')}
          </Typography>
          <ExpertiseFieldWrapper minLevel={fc.synonyms.level}>
            <FormChipInput
              name="synonyms"
              control={control}
              label={t('pages.species.synonyms')}
              helperText={t('pages.species.synonymsHelper')}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.taxonomic_authority.level}>
            <FormTextField
              name="taxonomic_authority"
              control={control}
              label={t('pages.species.taxonomicAuthority')}
              helperText={t('pages.species.taxonomicAuthorityHelper')}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.taxonomic_status.level}>
            <FormTextField
              name="taxonomic_status"
              control={control}
              label={t('pages.species.taxonomicStatus')}
              helperText={t('pages.species.taxonomicStatusHelper')}
            />
          </ExpertiseFieldWrapper>

          {/* --- Cultivation conditions section --- */}
          <Typography variant="subtitle2" sx={{ mb: 1, mt: 2 }}>
            {t('pages.species.sectionCultivation')}
          </Typography>
          <ExpertiseFieldWrapper minLevel={fc.container_suitable.level}>
            <FormRow>
              <FormSelectField
                name="container_suitable"
                control={control}
                label={t('pages.species.containerSuitable')}
                helperText={t('pages.species.containerSuitableHelper')}
                options={[
                  { value: '', label: '—' },
                  ...['yes', 'limited', 'no'].map((v) => ({
                    value: v,
                    label: t(`enums.suitability.${v}`),
                  })),
                ]}
              />
              <FormSelectField
                name="indoor_suitable"
                control={control}
                label={t('pages.species.indoorSuitable')}
                helperText={t('pages.species.indoorSuitableHelper')}
                options={[
                  { value: '', label: '—' },
                  ...['yes', 'limited', 'no'].map((v) => ({
                    value: v,
                    label: t(`enums.suitability.${v}`),
                  })),
                ]}
              />
            </FormRow>
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.balcony_suitable.level}>
            <FormSelectField
              name="balcony_suitable"
              control={control}
              label={t('pages.species.balconySuitable')}
              helperText={t('pages.species.balconySuitableHelper')}
              options={[
                { value: '', label: '—' },
                ...['yes', 'limited', 'no'].map((v) => ({
                  value: v,
                  label: t(`enums.suitability.${v}`),
                })),
              ]}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.recommended_container_volume_l.level}>
            <FormRow>
              <FormTextField
                name="recommended_container_volume_l"
                control={control}
                label={t('pages.species.recommendedContainerVolumeL')}
                helperText={t('pages.species.recommendedContainerVolumeLHelper')}
              />
              <FormNumberField
                name="min_container_depth_cm"
                control={control}
                label={t('pages.species.minContainerDepthCm')}
                helperText={t('pages.species.minContainerDepthCmHelper')}
                min={1}
                max={200}
              />
            </FormRow>
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.mature_height_cm.level}>
            <FormRow>
              <FormTextField
                name="mature_height_cm"
                control={control}
                label={t('pages.species.matureHeightCm')}
                helperText={t('pages.species.matureHeightCmHelper')}
              />
              <FormTextField
                name="mature_width_cm"
                control={control}
                label={t('pages.species.matureWidthCm')}
                helperText={t('pages.species.matureWidthCmHelper')}
              />
            </FormRow>
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.spacing_cm.level}>
            <FormTextField
              name="spacing_cm"
              control={control}
              label={t('pages.species.spacingCm')}
              helperText={t('pages.species.spacingCmHelper')}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.greenhouse_recommended.level}>
            <FormRow>
              <FormSwitchField
                name="greenhouse_recommended"
                control={control}
                label={t('pages.species.greenhouseRecommended')}
                helperText={t('pages.species.greenhouseRecommendedHelper')}
              />
              <FormSwitchField
                name="support_required"
                control={control}
                label={t('pages.species.supportRequired')}
                helperText={t('pages.species.supportRequiredHelper')}
              />
            </FormRow>
          </ExpertiseFieldWrapper>

          {level !== 'expert' && (
            <ShowAllFieldsToggle showAll={showAllOverride} onToggle={toggleShowAll} />
          )}
          <FormActions onCancel={handleClose} loading={saving} saveLabel={t('common.create')} />
        </Form>
      </DialogContent>
    </Dialog>
    </>
  );
}
