import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Alert from '@mui/material/Alert';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormRow from '@/components/form/FormRow';
import Typography from '@mui/material/Typography';
import Collapse from '@mui/material/Collapse';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as planApi from '@/api/endpoints/nutrient-plans';
import type { NutrientPlanPhaseEntry } from '@/api/types';
import WaterMixRecommendationBox from './WaterMixRecommendationBox';

const phaseNames = ['germination', 'seedling', 'vegetative', 'flowering', 'flushing', 'dormancy', 'harvest'] as const;

const schema = z.object({
  phase_name: z.enum(phaseNames),
  sequence_order: z.number().min(1),
  week_start: z.number().min(1),
  week_end: z.number().min(1),
  is_recurring: z.boolean(),
  npk_n: z.number().min(0),
  npk_p: z.number().min(0),
  npk_k: z.number().min(0),
  calcium_ppm: z.number().min(0).nullable(),
  magnesium_ppm: z.number().min(0).nullable(),
  notes: z.string().nullable(),
  override_enabled: z.boolean(),
  override_interval_days: z.number().min(1).max(90).nullable(),
  water_mix_ratio_ro_percent: z.number().min(0).max(100).nullable(),
}).refine((data) => data.week_end >= data.week_start, {
  message: 'week_end_before_start',
  path: ['week_end'],
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  planKey: string;
  entry?: NutrientPlanPhaseEntry | null;
  onSaved: () => void;
  siteKey?: string | null;
  substrateType?: string;
}

export default function PhaseEntryDialog({ open, onClose, planKey, entry, onSaved, siteKey, substrateType }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const isEdit = !!entry;

  const { control, handleSubmit, reset, watch, setValue } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      phase_name: 'germination',
      sequence_order: 1,
      week_start: 1,
      week_end: 2,
      is_recurring: false,
      npk_n: 0,
      npk_p: 0,
      npk_k: 0,
      calcium_ppm: null,
      magnesium_ppm: null,
      notes: null,
      override_enabled: false,
      override_interval_days: null,
      water_mix_ratio_ro_percent: null,
    },
  });

  const overrideEnabled = watch('override_enabled');

  useEffect(() => {
    if (open) {
      if (entry) {
        reset({
          phase_name: entry.phase_name,
          sequence_order: entry.sequence_order,
          week_start: entry.week_start,
          week_end: entry.week_end,
          is_recurring: entry.is_recurring ?? false,
          npk_n: entry.npk_ratio[0],
          npk_p: entry.npk_ratio[1],
          npk_k: entry.npk_ratio[2],
          calcium_ppm: entry.calcium_ppm,
          magnesium_ppm: entry.magnesium_ppm,
          notes: entry.notes,
          override_enabled: entry.watering_schedule_override != null,
          override_interval_days: entry.watering_schedule_override?.interval_days ?? null,
          water_mix_ratio_ro_percent: entry.water_mix_ratio_ro_percent,
        });
      } else {
        reset({
          phase_name: 'germination',
          sequence_order: 1,
          week_start: 1,
          week_end: 2,
          is_recurring: false,
          npk_n: 0,
          npk_p: 0,
          npk_k: 0,
          calcium_ppm: null,
          magnesium_ppm: null,
          notes: null,
          override_enabled: false,
          override_interval_days: null,
          water_mix_ratio_ro_percent: null,
        });
      }
    }
  }, [open, entry, reset]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      const payload = {
        phase_name: data.phase_name,
        sequence_order: data.sequence_order,
        week_start: data.week_start,
        week_end: data.week_end,
        is_recurring: data.is_recurring,
        npk_ratio: [data.npk_n, data.npk_p, data.npk_k] as [number, number, number],
        calcium_ppm: data.calcium_ppm,
        magnesium_ppm: data.magnesium_ppm,
        notes: data.notes,
        water_mix_ratio_ro_percent: data.water_mix_ratio_ro_percent,
        watering_schedule_override: data.override_enabled && data.override_interval_days
          ? {
              schedule_mode: 'interval' as const,
              weekday_schedule: [],
              interval_days: data.override_interval_days,
              preferred_time: '09:00',
              application_method: 'drench' as const,
              reminder_hours_before: 2,
              times_per_day: 1,
            }
          : null,
      };
      if (isEdit && entry) {
        await planApi.updatePhaseEntry(planKey, entry.key, payload);
      } else {
        await planApi.createPhaseEntry(planKey, payload);
      }
      notification.success(t(isEdit ? 'common.save' : 'common.create'));
      onSaved();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog fullScreen={fullScreen} open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {isEdit
          ? t('pages.nutrientPlans.editEntry')
          : t('pages.nutrientPlans.addEntry')}
      </DialogTitle>
      <DialogContent>
        {isEdit && entry && entry.delivery_channels && entry.delivery_channels.length > 0 && (
          <Alert severity="info" sx={{ mb: 2 }}>
            {t('pages.deliveryChannels.multiChannelActive')}
          </Alert>
        )}
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormSelectField
            name="phase_name"
            control={control}
            label={t('pages.nutrientPlans.phaseName')}
            options={phaseNames.map((v) => ({
              value: v,
              label: t(`enums.phaseName.${v}`),
            }))}
            required
          />
          <FormNumberField
            name="sequence_order"
            control={control}
            label={t('pages.nutrientPlans.sequenceOrder')}
            min={1}
            required
          />
          <FormRow>
            <FormNumberField
              name="week_start"
              control={control}
              label={t('pages.nutrientPlans.weekStart')}
              min={1}
              step={1}
              inputMode="numeric"
              required
            />
            <FormNumberField
              name="week_end"
              control={control}
              label={t('pages.nutrientPlans.weekEnd')}
              min={1}
              step={1}
              inputMode="numeric"
              required
            />
          </FormRow>

          <FormSwitchField
            name="is_recurring"
            control={control}
            label={t('pages.nutrientPlans.isRecurring')}
            helperText={t('pages.nutrientPlans.isRecurringHelper')}
          />

          <FormSwitchField
            name="override_enabled"
            control={control}
            label={t('pages.nutrientPlans.wateringScheduleOverride')}
          />
          <Collapse in={overrideEnabled}>
            <FormNumberField
              name="override_interval_days"
              control={control}
              label={t('pages.nutrientPlans.overrideIntervalDays')}
              min={1}
              max={90}
              step={1}
            />
          </Collapse>

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.fertilizers.sectionNutrients')}
          </Typography>
          <FormRow>
            <FormNumberField
              name="npk_n"
              control={control}
              label={t('pages.fertilizers.npkN')}
              min={0}
              suffix="%"
              inputMode="decimal"
            />
            <FormNumberField
              name="npk_p"
              control={control}
              label={t('pages.fertilizers.npkP')}
              min={0}
              suffix="%"
              inputMode="decimal"
            />
          </FormRow>
          <FormRow>
            <FormNumberField
              name="npk_k"
              control={control}
              label={t('pages.fertilizers.npkK')}
              min={0}
              suffix="%"
              inputMode="decimal"
            />
            <FormNumberField
              name="water_mix_ratio_ro_percent"
              control={control}
              label={t('pages.nutrientPlans.roPercent')}
              min={0}
              max={100}
              step={5}
              suffix="%"
              inputMode="numeric"
              helperText={t('pages.nutrientPlans.roPercentHelper')}
            />
          </FormRow>
          {siteKey && (
            <WaterMixRecommendationBox
              planKey={planKey}
              sequenceOrder={entry?.sequence_order ?? watch('sequence_order')}
              siteKey={siteKey}
              substrateType={substrateType}
              onApply={(roPercent) => {
                setValue('water_mix_ratio_ro_percent', roPercent, { shouldDirty: true });
              }}
            />
          )}

          <FormRow>
            <FormNumberField
              name="calcium_ppm"
              control={control}
              label={t('pages.nutrientPlans.calciumPpm')}
              min={0}
              suffix="ppm"
              inputMode="decimal"
              helperText={t('pages.nutrientPlans.ppmHelper')}
            />
            <FormNumberField
              name="magnesium_ppm"
              control={control}
              label={t('pages.nutrientPlans.magnesiumPpm')}
              min={0}
              suffix="ppm"
              inputMode="decimal"
            />
          </FormRow>
          <FormTextField
            name="notes"
            control={control}
            label={t('pages.nutrientPlans.notes')}
            multiline
            rows={2}
          />
          <FormActions
            onCancel={onClose}
            loading={saving}
            saveLabel={t(isEdit ? 'common.save' : 'common.create')}
          />
        </form>
      </DialogContent>
    </Dialog>
  );
}
