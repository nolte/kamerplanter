import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormRow from '@/components/form/FormRow';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useAppDispatch } from '@/store/hooks';
import { overrideOverwintering } from '@/store/slices/seasonSlice';
import type {
  HardinessRating,
  OverwinteringOverride,
  OverwinteringProfile,
  WinterAction,
} from '@/api/types';

const hardinessRatings = [
  'hardy',
  'needs_protection',
  'frost_free',
  'dig_and_store',
] as const;
const springActions = [
  'uncover',
  'move_outdoors',
  'replant',
  'prune',
  'harden_off',
] as const;
const winterLights = ['bright', 'semi_bright', 'dark'] as const;
const winterWaterings = ['none', 'minimal', 'reduced', 'normal'] as const;
const tuberStatuses = [
  'planted',
  'growing',
  'dig_pending',
  'drying',
  'stored',
  'pre_sprouting',
] as const;

// D5 winter-path invariant (server-enforced): green/yellow ratings keep the
// plant in situ (path A actions), red ratings relocate it (path B actions). The
// backend rejects a winter_action that contradicts the rating with 422, so the
// form only offers valid actions for the selected rating.
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

const monthOptional = z.union([z.number().int().min(1).max(12), z.literal('')]);
const numberOptional = z.union([z.number(), z.literal('')]);
const intervalOptional = z.union([
  z.number().int().min(1).max(365),
  z.literal(''),
]);

const schema = z.object({
  hardiness_rating: z.enum(hardinessRatings),
  winter_action: z.enum([
    'none',
    'mulch',
    'fleece',
    'earth_up',
    'move_indoors',
    'dig_store',
    'wrap',
  ]),
  winter_action_month: z.number().int().min(1).max(12),
  spring_action: z.enum(springActions).or(z.literal('')),
  spring_action_month: monthOptional,
  winter_quarter_temp_min: numberOptional,
  winter_quarter_temp_max: numberOptional,
  winter_quarter_light: z.enum(winterLights).or(z.literal('')),
  winter_watering: z.enum(winterWaterings).or(z.literal('')),
  storage_check_interval_days: intervalOptional,
  tuber_status: z.enum(tuberStatuses).or(z.literal('')),
  notes: z.string().max(2000),
});

type FormData = z.infer<typeof schema>;

const emptyToNull = (v: number | ''): number | null => (v === '' ? null : v);

function profileToForm(p: OverwinteringProfile): FormData {
  return {
    hardiness_rating: p.hardiness_rating,
    winter_action: p.winter_action,
    winter_action_month: p.winter_action_month,
    spring_action: p.spring_action ?? '',
    spring_action_month: p.spring_action_month ?? '',
    winter_quarter_temp_min: p.winter_quarter_temp_min ?? '',
    winter_quarter_temp_max: p.winter_quarter_temp_max ?? '',
    winter_quarter_light: p.winter_quarter_light ?? '',
    winter_watering: p.winter_watering ?? '',
    storage_check_interval_days: p.storage_check_interval_days ?? '',
    tuber_status: p.tuber_status ?? '',
    notes: p.notes ?? '',
  };
}

interface Props {
  open: boolean;
  onClose: () => void;
  plantKey: string;
  profile: OverwinteringProfile;
}

/**
 * REQ-047 §4.3 — override dialog for the auto-materialised overwintering profile.
 * Sends a PATCH to the season-automation endpoint; the backend flips
 * `user_overridden` so the automation only fills remaining gaps afterwards and
 * never overwrites a user-set value.
 */
export default function OverwinteringOverrideDialog({
  open,
  onClose,
  plantKey,
  profile,
}: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const dispatch = useAppDispatch();
  const [saving, setSaving] = useState(false);

  const {
    control,
    handleSubmit,
    reset,
    watch,
    setValue,
    setError,
    formState: { isDirty },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: profileToForm(profile),
  });

  useEffect(() => {
    if (open) reset(profileToForm(profile));
  }, [open, profile, reset]);

  const hardinessRating = watch('hardiness_rating');
  const winterAction = watch('winter_action');
  const showTuberSection = hardinessRating === 'dig_and_store';

  // Keep winter_action valid for the selected rating's path (D5) so the first
  // save never hits a guaranteed 422.
  useEffect(() => {
    if (!RATING_VALID_ACTIONS[hardinessRating].includes(winterAction)) {
      setValue('winter_action', RATING_DEFAULT_ACTION[hardinessRating], {
        shouldValidate: true,
      });
    }
  }, [hardinessRating, winterAction, setValue]);

  useEffect(() => {
    if (hardinessRating !== 'dig_and_store') {
      setValue('storage_check_interval_days', '');
      setValue('tuber_status', '');
    }
  }, [hardinessRating, setValue]);

  const winterActionOptions = useMemo(
    () =>
      RATING_VALID_ACTIONS[hardinessRating].map((v) => ({
        value: v,
        label: t(`enums.winterAction.${v}`),
      })),
    [hardinessRating, t],
  );

  const onSubmit = async (data: FormData) => {
    const patch: OverwinteringOverride = {
      hardiness_rating: data.hardiness_rating,
      winter_action: data.winter_action,
      winter_action_month: data.winter_action_month,
      spring_action: data.spring_action || null,
      spring_action_month: emptyToNull(data.spring_action_month),
      winter_quarter_temp_min: emptyToNull(data.winter_quarter_temp_min),
      winter_quarter_temp_max: emptyToNull(data.winter_quarter_temp_max),
      winter_quarter_light: data.winter_quarter_light || null,
      winter_watering: data.winter_watering || null,
      storage_check_interval_days: emptyToNull(data.storage_check_interval_days),
      tuber_status: data.tuber_status || null,
      notes: data.notes || null,
    };
    try {
      setSaving(true);
      await dispatch(overrideOverwintering({ plantKey, patch })).unwrap();
      notification.success(t('pages.season.override.saved'));
      onClose();
    } catch (err) {
      handleError(err, setError as (name: string, message: string) => void);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="overwintering-override-title"
      data-testid="overwintering-override-dialog"
    >
      <UnsavedChangesGuard dirty={isDirty && open} />
      <DialogTitle id="overwintering-override-title">
        {t('pages.season.override.dialogTitle')}
      </DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.season.override.dialogIntro')}
        </Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormRow>
            <FormSelectField
              name="hardiness_rating"
              control={control}
              label={t('pages.overwintering.hardinessRating')}
              required
              autoFocus
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
              helperText={t('pages.overwintering.winterActionRatingNote')}
              options={winterActionOptions}
            />
          </FormRow>
          <FormRow>
            <FormNumberField
              name="winter_action_month"
              control={control}
              label={t('pages.overwintering.winterActionMonth')}
              required
              min={1}
              max={12}
              step={1}
              inputMode="numeric"
              helperText={t('pages.overwintering.winterActionMonthHelper')}
            />
            <FormSelectField
              name="winter_watering"
              control={control}
              label={t('pages.overwintering.winterWatering')}
              helperText={t('pages.season.override.winterWateringHelper')}
              options={[
                { value: '', label: t('common.none') },
                ...winterWaterings.map((v) => ({
                  value: v,
                  label: t(`enums.winterWatering.${v}`),
                })),
              ]}
            />
          </FormRow>

          <Divider sx={{ my: 2 }} />
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
            <FormNumberField
              name="spring_action_month"
              control={control}
              label={t('pages.overwintering.springActionMonth')}
              min={1}
              max={12}
              step={1}
              inputMode="numeric"
              helperText={t('pages.overwintering.springActionMonthHelper')}
            />
          </FormRow>

          <Divider sx={{ my: 2 }} />
          <FormRow>
            <FormNumberField
              name="winter_quarter_temp_min"
              control={control}
              label={t('pages.overwintering.winterQuarterTempMin')}
              suffix="°C"
              step="any"
              helperText={t('pages.overwintering.winterQuarterTempMinHelper')}
            />
            <FormNumberField
              name="winter_quarter_temp_max"
              control={control}
              label={t('pages.overwintering.winterQuarterTempMax')}
              suffix="°C"
              step="any"
              helperText={t('pages.overwintering.winterQuarterTempMaxHelper')}
            />
          </FormRow>
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

          {showTuberSection && (
            <>
              <Divider sx={{ my: 2 }} />
              <FormRow>
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
              </FormRow>
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
            saveLabel={t('common.save')}
          />
        </form>
      </DialogContent>
    </Dialog>
  );
}
