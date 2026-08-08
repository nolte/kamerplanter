import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Form from '@/components/form/Form';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormMonthField from '@/components/form/FormMonthField';
import FormRow from '@/components/form/FormRow';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import HelpTooltip from '@/components/common/HelpTooltip';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useFieldViolations } from '@/hooks/useFieldViolations';
import * as api from '@/api/endpoints/overwinteringProfiles';
import type {
  OverwinteringProfile,
  OverwinteringProfileCreate,
  OverwinteringProfileUpdate,
  PlantInstance,
} from '@/api/types';

const hardinessRatings = [
  'hardy',
  'needs_protection',
  'frost_free',
  'dig_and_store',
] as const;
const winterActions = [
  'none',
  'mulch',
  'fleece',
  'earth_up',
  'move_indoors',
  'dig_store',
  'wrap',
] as const;
const springActions = [
  'uncover',
  'move_outdoors',
  'replant',
  'prune',
  'harden_off',
] as const;
const tuberStatuses = [
  'planted',
  'growing',
  'dig_pending',
  'drying',
  'stored',
  'pre_sprouting',
] as const;
const winterLights = ['bright', 'semi_bright', 'dark'] as const;
const winterWaterings = ['none', 'minimal', 'reduced', 'normal'] as const;

type HardinessRating = (typeof hardinessRatings)[number];
type WinterAction = (typeof winterActions)[number];

// D5 winter-path invariant (server-enforced in winter_hardiness_engine): Path A
// (green/yellow ratings) keeps the plant in situ; Path B (red ratings) relocates
// it. The winter_action must match the path or the backend rejects with 422.
// These tables mirror _PATH_A_ACTIONS/_PATH_B_ACTIONS so the form only offers —
// and defaults to — actions valid for the selected hardiness rating.
const PATH_A_ACTIONS: readonly WinterAction[] = [
  'none',
  'mulch',
  'fleece',
  'earth_up',
  'wrap',
];
const PATH_B_ACTIONS: readonly WinterAction[] = ['move_indoors', 'dig_store'];

const RATING_VALID_ACTIONS: Record<HardinessRating, readonly WinterAction[]> = {
  hardy: PATH_A_ACTIONS,
  needs_protection: PATH_A_ACTIONS,
  frost_free: PATH_B_ACTIONS,
  dig_and_store: PATH_B_ACTIONS,
};

const RATING_DEFAULT_ACTION: Record<HardinessRating, WinterAction> = {
  hardy: 'none',
  needs_protection: 'mulch',
  frost_free: 'move_indoors',
  dig_and_store: 'dig_store',
};

// Optional numeric fields carry `number | ''` so the empty text input maps to a
// stable value; '' is converted to null on submit. Keeping input === output
// avoids the zodResolver input/output generic mismatch that z.preprocess causes.
const monthOptional = z.union([z.number().int().min(1).max(12), z.literal('')]).nullable();
const numberOptional = z.union([z.number(), z.literal('')]).nullable();
const intervalOptional = z.union([
  z.number().int().min(1).max(365),
  z.literal(''),
]);

const schema = z.object({
  plant_key: z.string(),
  hardiness_rating: z.enum(hardinessRatings),
  winter_action: z.enum(winterActions),
  winter_action_month: z.number().int().min(1).max(12),
  spring_action: z.enum(springActions).or(z.literal('')),
  spring_action_month: monthOptional,
  hardiness_zone_min: z.string().max(10),
  winter_quarter_temp_min: numberOptional,
  winter_quarter_temp_max: numberOptional,
  winter_quarter_light: z.enum(winterLights).or(z.literal('')),
  winter_watering: z.enum(winterWaterings).or(z.literal('')),
  storage_medium: z.string().max(200),
  storage_check_interval_days: intervalOptional,
  tuber_status: z.enum(tuberStatuses).or(z.literal('')),
  notes: z.string().max(2000),
});

type FormData = z.infer<typeof schema>;

// Accepts null as well as '' since #778 B2: FormNumberField/FormMonthField
// now emit null when cleared, and the schema's `.nullable()` lets it through.
const emptyToNull = (v: number | '' | null): number | null => (v === '' || v == null ? null : v);

const DEFAULTS: FormData = {
  plant_key: '',
  hardiness_rating: 'needs_protection',
  winter_action: 'fleece',
  winter_action_month: 10,
  spring_action: '',
  spring_action_month: '',
  hardiness_zone_min: '',
  winter_quarter_temp_min: '',
  winter_quarter_temp_max: '',
  winter_quarter_light: '',
  winter_watering: '',
  storage_medium: '',
  storage_check_interval_days: '',
  tuber_status: '',
  notes: '',
};

function profileToForm(p: OverwinteringProfile): FormData {
  return {
    plant_key: p.plant_key ?? '',
    hardiness_rating: p.hardiness_rating,
    winter_action: p.winter_action,
    winter_action_month: p.winter_action_month,
    spring_action: p.spring_action ?? '',
    spring_action_month: p.spring_action_month ?? '',
    hardiness_zone_min: p.hardiness_zone_min ?? '',
    winter_quarter_temp_min: p.winter_quarter_temp_min ?? '',
    winter_quarter_temp_max: p.winter_quarter_temp_max ?? '',
    winter_quarter_light: p.winter_quarter_light ?? '',
    winter_watering: p.winter_watering ?? '',
    storage_medium: p.storage_medium ?? '',
    storage_check_interval_days: p.storage_check_interval_days ?? '',
    tuber_status: p.tuber_status ?? '',
    notes: p.notes ?? '',
  };
}

/**
 * Backend violation `code` (stable) → i18n key. Keyed on `code`, not on the
 * field, and translated here because the backend `reason` is English (#1015).
 * A code absent here is left to the generic toast rather than rendered raw.
 *
 * - `WINTER_PATH_VIOLATION` — D5: `winter_action` contradicts the rating's
 *   winter path (`validate_d5_invariant`), lands on `winter_action`.
 * - `SITE_NOT_FROST_EXPOSED` / `INVALID_SUBJECT` — create-time subject checks,
 *   land on `plant_key`.
 */
const VIOLATION_MESSAGE_KEYS: Record<string, string> = {
  WINTER_PATH_VIOLATION: 'pages.overwintering.errors.winterPathViolation',
  SITE_NOT_FROST_EXPOSED: 'pages.overwintering.errors.siteNotFrostExposed',
  INVALID_SUBJECT: 'pages.overwintering.errors.invalidSubject',
};

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  /** When set the dialog edits this profile; otherwise it creates a new one. */
  profile?: OverwinteringProfile | null;
  /** Plant instances offered as the (optional) subject in create mode. */
  plants: PlantInstance[];
}

export default function OverwinteringProfileDialog({
  open,
  onClose,
  onSaved,
  profile,
  plants,
}: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const isEdit = !!profile;

  // In create mode a subject is mandatory: the backend `_require_single_subject`
  // rejects a profile without exactly one of plant_key/planting_run_key (422).
  // Guard it client-side so the obvious first save no longer fails. Edit mode
  // keeps the base schema because the plant field is not rendered there and the
  // subject may legitimately be a planting run (empty plant_key).
  const resolver = useMemo(
    () =>
      zodResolver(
        isEdit
          ? schema
          : schema.superRefine((data, ctx) => {
              if (!data.plant_key) {
                ctx.addIssue({
                  code: z.ZodIssueCode.custom,
                  path: ['plant_key'],
                  message: t('pages.overwintering.plantRequired'),
                });
              }
            }),
      ),
    [isEdit, t],
  );

  const {
    control,
    handleSubmit,
    reset,
    watch,
    setValue,
    setError,
    formState: { isDirty },
  } = useForm<FormData>({
    resolver,
    defaultValues: DEFAULTS,
  });

  const applyFieldViolation = useFieldViolations(setError, {
    messageKeys: VIOLATION_MESSAGE_KEYS,
  });

  useEffect(() => {
    if (open) {
      reset(profile ? profileToForm(profile) : DEFAULTS);
    }
  }, [open, profile, reset]);

  const hardinessRating = watch('hardiness_rating');
  const winterAction = watch('winter_action');
  const showTuberSection = hardinessRating === 'dig_and_store';

  // D5 constraint (server-enforced): tuber storage data is only meaningful for
  // the dig-and-store rating. Clear it when leaving that rating so a hidden
  // field can never carry a stale value into the request.
  useEffect(() => {
    if (hardinessRating !== 'dig_and_store') {
      setValue('storage_medium', '');
      setValue('storage_check_interval_days', '');
      setValue('tuber_status', '');
    }
  }, [hardinessRating, setValue]);

  // D5 UX guidance: keep winter_action valid for the selected rating's path.
  // When the current action no longer matches the path (e.g. rating switched to
  // dig_and_store while the default fleece is still selected) reset it to the
  // path's default so the first save does not hit a guaranteed 422. A still-valid
  // action (e.g. an edited profile's stored value) is preserved.
  useEffect(() => {
    if (!RATING_VALID_ACTIONS[hardinessRating].includes(winterAction)) {
      setValue('winter_action', RATING_DEFAULT_ACTION[hardinessRating], {
        shouldValidate: true,
      });
    }
  }, [hardinessRating, winterAction, setValue]);

  // Only offer actions valid for the selected rating's winter path (D5).
  const winterActionOptions = useMemo(
    () =>
      RATING_VALID_ACTIONS[hardinessRating].map((v) => ({
        value: v,
        label: t(`enums.winterAction.${v}`),
      })),
    [hardinessRating, t],
  );

  const onSubmit = async (data: FormData) => {
    const base: OverwinteringProfileUpdate = {
      hardiness_rating: data.hardiness_rating,
      winter_action: data.winter_action,
      winter_action_month: data.winter_action_month,
      spring_action: data.spring_action || null,
      spring_action_month: emptyToNull(data.spring_action_month),
      hardiness_zone_min: data.hardiness_zone_min || null,
      winter_quarter_temp_min: emptyToNull(data.winter_quarter_temp_min),
      winter_quarter_temp_max: emptyToNull(data.winter_quarter_temp_max),
      winter_quarter_light: data.winter_quarter_light || null,
      winter_watering: data.winter_watering || null,
      storage_medium: data.storage_medium || null,
      storage_check_interval_days: emptyToNull(data.storage_check_interval_days),
      tuber_status: data.tuber_status || null,
      notes: data.notes || null,
    };
    try {
      setSaving(true);
      if (profile) {
        await api.updateOverwinteringProfile(profile.key, base);
        notification.success(t('common.save'));
      } else {
        const createPayload: OverwinteringProfileCreate = {
          ...base,
          hardiness_rating: data.hardiness_rating,
          winter_action: data.winter_action,
          winter_action_month: data.winter_action_month,
          plant_key: data.plant_key || null,
        };
        await api.createOverwinteringProfile(createPayload);
        notification.success(t('common.create'));
      }
      reset(DEFAULTS);
      onSaved();
    } catch (err) {
      // Surfaces the server-side D5 winter-path 422 (and the create-time subject
      // checks) on the field, translated on the violation `code`; an untranslated
      // code degrades to the generic toast rather than to the English reason
      // (#1015). The previous raw `setError` cast also passed the reason string
      // where react-hook-form expects `{ message }`, so the field went red with
      // no text at all — the helper sets the correct `{ type, message }` shape.
      handleError(err, applyFieldViolation);
    } finally {
      setSaving(false);
    }
  };

  const plantOptions = [
    { value: '', label: t('common.none') },
    ...plants.map((p) => ({
      value: p.key,
      label: p.plant_name ? `${p.plant_name} (${p.instance_id})` : p.instance_id,
    })),
  ];

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="overwintering-dialog-title"
      data-testid="overwintering-dialog"
    >
      <UnsavedChangesGuard dirty={isDirty && open} />
      <DialogTitle id="overwintering-dialog-title">
        {isEdit
          ? t('pages.overwintering.edit')
          : t('pages.overwintering.create')}
      </DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.overwintering.formIntro')}
        </Typography>
        <Form onSubmit={handleSubmit(onSubmit)}>
          {!isEdit && (
            <FormSelectField
              name="plant_key"
              control={control}
              label={t('pages.overwintering.plant')}
              options={plantOptions}
              helperText={t('pages.overwintering.plantHelp')}
              autoFocus
            />
          )}

          <Typography variant="subtitle2" sx={{ mb: 0.25 }}>
            {t('pages.overwintering.hardinessSection')}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
            {t('pages.overwintering.hardinessSectionDesc')}
          </Typography>
          <FormRow>
            <FormSelectField
              name="hardiness_rating"
              control={control}
              label={t('pages.overwintering.hardinessRating')}
              required
              autoFocus={isEdit}
              helperText={t('pages.overwintering.hardinessRatingHelper')}
              options={hardinessRatings.map((v) => ({
                value: v,
                label: t(`enums.hardinessRating.${v}`),
              }))}
            />
            <FormSelectField
              name="winter_action"
              control={control}
              label={t('pages.overwintering.winterAction')}
              required
              helperText={`${t('pages.overwintering.winterActionHelper')} ${t('pages.overwintering.winterActionRatingNote')}`}
              options={winterActionOptions}
            />
          </FormRow>
          <FormRow>
            <FormMonthField
              name="winter_action_month"
              control={control}
              label={t('pages.overwintering.winterActionMonth')}
              required
              helperText={t('pages.overwintering.winterActionMonthHelper')}
            />
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5 }}>
              <FormTextField
                name="hardiness_zone_min"
                control={control}
                label={t('pages.overwintering.hardinessZoneMin')}
                helperText={t('pages.overwintering.hardinessZoneMinHelper')}
              />
              <HelpTooltip term="hardiness_zones" iconOnly />
            </Box>
          </FormRow>

          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle2" sx={{ mb: 0.25 }}>
            {t('pages.overwintering.springSection')}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
            {t('pages.overwintering.springSectionDesc')}
          </Typography>
          <FormRow>
            <FormSelectField
              name="spring_action"
              control={control}
              label={t('pages.overwintering.springAction')}
              helperText={t('pages.overwintering.springActionHelper')}
              options={[
                { value: '', label: t('common.none') },
                ...springActions.map((v) => ({
                  value: v,
                  label: t(`enums.springAction.${v}`),
                })),
              ]}
            />
            <FormMonthField
              name="spring_action_month"
              control={control}
              label={t('pages.overwintering.springActionMonth')}
              includeEmpty
              helperText={t('pages.overwintering.springActionMonthHelper')}
            />
          </FormRow>

          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle2" sx={{ mb: 0.25 }}>
            {t('pages.overwintering.winterQuarterSection')}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
            {t('pages.overwintering.winterQuarterSectionDesc')}
          </Typography>
          <FormRow>
            <FormNumberField
              name="winter_quarter_temp_min"
              control={control}
              label={t('pages.overwintering.winterQuarterTempMin')}
              suffix="°C"
              helperText={t('pages.overwintering.winterQuarterTempMinHelper')}
            />
            <FormNumberField
              name="winter_quarter_temp_max"
              control={control}
              label={t('pages.overwintering.winterQuarterTempMax')}
              suffix="°C"
              helperText={t('pages.overwintering.winterQuarterTempMaxHelper')}
            />
          </FormRow>
          <FormRow>
            <FormSelectField
              name="winter_quarter_light"
              control={control}
              label={t('pages.overwintering.winterQuarterLight')}
              helperText={t('pages.overwintering.winterQuarterLightHelper')}
              options={[
                { value: '', label: t('common.none') },
                ...winterLights.map((v) => ({
                  value: v,
                  label: t(`enums.winterQuarterLight.${v}`),
                })),
              ]}
            />
            <FormSelectField
              name="winter_watering"
              control={control}
              label={t('pages.overwintering.winterWatering')}
              helperText={t('pages.overwintering.winterWateringHelper')}
              options={[
                { value: '', label: t('common.none') },
                ...winterWaterings.map((v) => ({
                  value: v,
                  label: t(`enums.winterWatering.${v}`),
                })),
              ]}
            />
          </FormRow>

          {showTuberSection && (
            <>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2" sx={{ mb: 0.25 }}>
                {t('pages.overwintering.tuberSection')}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                {t('pages.overwintering.tuberSectionDesc')}
              </Typography>
              <FormRow>
                <FormTextField
                  name="storage_medium"
                  control={control}
                  label={t('pages.overwintering.storageMedium')}
                  helperText={t('pages.overwintering.storageMediumHelper')}
                />
                <FormNumberField
                  name="storage_check_interval_days"
                  control={control}
                  label={t('pages.overwintering.storageCheckIntervalDays')}
                  min={1}
                  max={365}
                  step={1}
                  inputMode="numeric"
                  suffix={t('pages.overwintering.daysUnit')}
                  helperText={t('pages.overwintering.storageCheckIntervalDaysHelper')}
                />
              </FormRow>
              <FormSelectField
                name="tuber_status"
                control={control}
                label={t('pages.overwintering.tuberStatus')}
                helperText={t('pages.overwintering.tuberStatusHelper')}
                options={[
                  { value: '', label: t('common.none') },
                  ...tuberStatuses.map((v) => ({
                    value: v,
                    label: t(`enums.tuberStatus.${v}`),
                  })),
                ]}
              />
            </>
          )}

          <Divider sx={{ my: 2 }} />
          <FormTextField
            name="notes"
            control={control}
            label={t('pages.overwintering.notes')}
            multiline
            minRows={3}
          />

          <FormActions
            onCancel={onClose}
            loading={saving}
            saveLabel={isEdit ? t('common.save') : t('common.create')}
          />
        </Form>
      </DialogContent>
    </Dialog>
  );
}
