import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as planApi from '@/api/endpoints/nutrient-plans';
import type { NutrientPlanPhaseEntry } from '@/api/types';

const phaseNames = ['germination', 'seedling', 'vegetative', 'flowering', 'harvest'] as const;

const schema = z.object({
  phase_name: z.enum(phaseNames),
  sequence_order: z.number().min(1),
  week_start: z.number().min(1),
  week_end: z.number().min(1),
  npk_n: z.number().min(0),
  npk_p: z.number().min(0),
  npk_k: z.number().min(0),
  target_ec_ms: z.number().min(0).max(10),
  target_ph: z.number().min(0).max(14),
  calcium_ppm: z.number().min(0).nullable(),
  magnesium_ppm: z.number().min(0).nullable(),
  feeding_frequency_per_week: z.number().min(1).max(14),
  volume_per_feeding_liters: z.number().min(0).nullable(),
  notes: z.string().nullable(),
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
}

export default function PhaseEntryDialog({ open, onClose, planKey, entry, onSaved }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const isEdit = !!entry;

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      phase_name: 'germination',
      sequence_order: 1,
      week_start: 1,
      week_end: 2,
      npk_n: 0,
      npk_p: 0,
      npk_k: 0,
      target_ec_ms: 1.0,
      target_ph: 6.0,
      calcium_ppm: null,
      magnesium_ppm: null,
      feeding_frequency_per_week: 1,
      volume_per_feeding_liters: null,
      notes: null,
    },
  });

  useEffect(() => {
    if (open) {
      if (entry) {
        reset({
          phase_name: entry.phase_name,
          sequence_order: entry.sequence_order,
          week_start: entry.week_start,
          week_end: entry.week_end,
          npk_n: entry.npk_ratio[0],
          npk_p: entry.npk_ratio[1],
          npk_k: entry.npk_ratio[2],
          target_ec_ms: entry.target_ec_ms,
          target_ph: entry.target_ph,
          calcium_ppm: entry.calcium_ppm,
          magnesium_ppm: entry.magnesium_ppm,
          feeding_frequency_per_week: entry.feeding_frequency_per_week,
          volume_per_feeding_liters: entry.volume_per_feeding_liters,
          notes: entry.notes,
        });
      } else {
        reset({
          phase_name: 'germination',
          sequence_order: 1,
          week_start: 1,
          week_end: 2,
          npk_n: 0,
          npk_p: 0,
          npk_k: 0,
          target_ec_ms: 1.0,
          target_ph: 6.0,
          calcium_ppm: null,
          magnesium_ppm: null,
          feeding_frequency_per_week: 1,
          volume_per_feeding_liters: null,
          notes: null,
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
        npk_ratio: [data.npk_n, data.npk_p, data.npk_k] as [number, number, number],
        target_ec_ms: data.target_ec_ms,
        target_ph: data.target_ph,
        calcium_ppm: data.calcium_ppm,
        magnesium_ppm: data.magnesium_ppm,
        feeding_frequency_per_week: data.feeding_frequency_per_week,
        volume_per_feeding_liters: data.volume_per_feeding_liters,
        notes: data.notes,
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
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {isEdit
          ? t('pages.nutrientPlans.editEntry')
          : t('pages.nutrientPlans.addEntry')}
      </DialogTitle>
      <DialogContent>
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
          <FormNumberField
            name="week_start"
            control={control}
            label={t('pages.nutrientPlans.weekStart')}
            min={1}
            required
          />
          <FormNumberField
            name="week_end"
            control={control}
            label={t('pages.nutrientPlans.weekEnd')}
            min={1}
            required
          />
          <FormNumberField
            name="npk_n"
            control={control}
            label={t('pages.fertilizers.npkN')}
            min={0}

          />
          <FormNumberField
            name="npk_p"
            control={control}
            label={t('pages.fertilizers.npkP')}
            min={0}

          />
          <FormNumberField
            name="npk_k"
            control={control}
            label={t('pages.fertilizers.npkK')}
            min={0}

          />
          <FormNumberField
            name="target_ec_ms"
            control={control}
            label={t('pages.nutrientPlans.targetEc')}
            min={0}
            max={10}

            required
          />
          <FormNumberField
            name="target_ph"
            control={control}
            label={t('pages.nutrientPlans.targetPh')}
            min={0}
            max={14}

            required
          />
          <FormNumberField
            name="calcium_ppm"
            control={control}
            label={t('pages.nutrientPlans.calciumPpm')}
            min={0}
          />
          <FormNumberField
            name="magnesium_ppm"
            control={control}
            label={t('pages.nutrientPlans.magnesiumPpm')}
            min={0}
          />
          <FormNumberField
            name="feeding_frequency_per_week"
            control={control}
            label={t('pages.nutrientPlans.feedingFrequency')}
            min={1}
            max={14}
            required
          />
          <FormNumberField
            name="volume_per_feeding_liters"
            control={control}
            label={t('pages.nutrientPlans.volumePerFeeding')}
            min={0}

          />
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
