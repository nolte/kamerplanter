import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as phasesApi from '@/api/endpoints/phases';
import type { GrowthPhase } from '@/api/types';

const schema = z.object({
  name: z.string().min(1),
  display_name: z.string(),
  typical_duration_days: z.number().min(1),
  sequence_order: z.number().min(0),
  is_terminal: z.boolean(),
  allows_harvest: z.boolean(),
  stress_tolerance: z.enum(['low', 'medium', 'high']),
});

type FormData = z.infer<typeof schema>;

interface Props {
  lifecycleKey: string;
  phase: GrowthPhase | null;
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
}

export default function GrowthPhaseDialog({ lifecycleKey, phase, open, onClose, onSaved }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const isEdit = !!phase;

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      display_name: '',
      typical_duration_days: 14,
      sequence_order: 0,
      is_terminal: false,
      allows_harvest: false,
      stress_tolerance: 'medium',
    },
  });

  useEffect(() => {
    if (phase) {
      reset({
        name: phase.name,
        display_name: phase.display_name,
        typical_duration_days: phase.typical_duration_days,
        sequence_order: phase.sequence_order,
        is_terminal: phase.is_terminal,
        allows_harvest: phase.allows_harvest,
        stress_tolerance: phase.stress_tolerance,
      });
    } else {
      reset({
        name: '',
        display_name: '',
        typical_duration_days: 14,
        sequence_order: 0,
        is_terminal: false,
        allows_harvest: false,
        stress_tolerance: 'medium',
      });
    }
  }, [phase, reset]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      const payload = { ...data, lifecycle_key: lifecycleKey };
      if (isEdit) {
        await phasesApi.updateGrowthPhase(phase.key, payload);
      } else {
        await phasesApi.createGrowthPhase(payload);
      }
      notification.success(isEdit ? t('common.save') : t('common.create'));
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
        {isEdit ? t('common.edit') : t('pages.growthPhases.create')}
      </DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField name="name" control={control} label={t('pages.growthPhases.name')} required />
          <FormTextField name="display_name" control={control} label={t('pages.growthPhases.displayName')} />
          <FormNumberField name="typical_duration_days" control={control} label={t('pages.growthPhases.duration')} min={1} />
          <FormNumberField name="sequence_order" control={control} label={t('pages.growthPhases.sequenceOrder')} min={0} />
          <FormSelectField
            name="stress_tolerance"
            control={control}
            label={t('pages.growthPhases.stressTolerance')}
            options={['low', 'medium', 'high'].map((v) => ({
              value: v,
              label: t(`enums.stressTolerance.${v}`),
            }))}
          />
          <Controller
            name="is_terminal"
            control={control}
            render={({ field }) => (
              <FormControlLabel
                control={<Switch checked={field.value} onChange={field.onChange} />}
                label={t('pages.growthPhases.isTerminal')}
                sx={{ display: 'block', mb: 1 }}
              />
            )}
          />
          <Controller
            name="allows_harvest"
            control={control}
            render={({ field }) => (
              <FormControlLabel
                control={<Switch checked={field.value} onChange={field.onChange} />}
                label={t('pages.growthPhases.allowsHarvest')}
                sx={{ display: 'block', mb: 1 }}
              />
            )}
          />
          <FormActions onCancel={onClose} loading={saving} saveLabel={isEdit ? t('common.save') : t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
