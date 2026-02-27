import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Typography from '@mui/material/Typography';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/ipm';

const pestTypes = ['insect', 'mite', 'nematode', 'mollusk'] as const;
const difficulties = ['easy', 'medium', 'hard'] as const;

const schema = z.object({
  scientific_name: z.string().min(1).max(200),
  common_name: z.string().min(1).max(200),
  pest_type: z.enum(pestTypes),
  lifecycle_days: z.number().int().positive().nullable(),
  optimal_temp_min: z.number().nullable(),
  optimal_temp_max: z.number().nullable(),
  detection_difficulty: z.enum(difficulties),
  description: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function PestCreateDialog({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      scientific_name: '',
      common_name: '',
      pest_type: 'insect',
      lifecycle_days: null,
      optimal_temp_min: null,
      optimal_temp_max: null,
      detection_difficulty: 'medium',
      description: null,
    },
  });

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await api.createPest({
        scientific_name: data.scientific_name,
        common_name: data.common_name,
        pest_type: data.pest_type,
        lifecycle_days: data.lifecycle_days,
        optimal_temp_min: data.optimal_temp_min,
        optimal_temp_max: data.optimal_temp_max,
        detection_difficulty: data.detection_difficulty,
        description: data.description,
      });
      notification.success(t('common.create'));
      reset();
      onCreated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('pages.ipm.createPest')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.ipm.pestCreateIntro')}
        </Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField
            name="scientific_name"
            control={control}
            label={t('pages.ipm.scientificName')}
            required
            helperText={t('pages.ipm.scientificNameHelper')}
          />
          <FormTextField
            name="common_name"
            control={control}
            label={t('pages.ipm.commonName')}
            required
            helperText={t('pages.ipm.commonNameHelper')}
          />
          <FormSelectField
            name="pest_type"
            control={control}
            label={t('pages.ipm.pestType')}
            options={pestTypes.map((v) => ({
              value: v,
              label: t(`enums.pestType.${v}`),
            }))}
          />
          <FormNumberField
            name="lifecycle_days"
            control={control}
            label={t('pages.ipm.lifecycleDays')}
            min={1}
            step={1}
            helperText={t('pages.ipm.lifecycleDaysHelper')}
          />
          <FormNumberField
            name="optimal_temp_min"
            control={control}
            label={t('pages.ipm.optimalTempMin')}
            helperText={t('pages.ipm.optimalTempHelper')}
          />
          <FormNumberField
            name="optimal_temp_max"
            control={control}
            label={t('pages.ipm.optimalTempMax')}
          />
          <FormSelectField
            name="detection_difficulty"
            control={control}
            label={t('pages.ipm.detectionDifficulty')}
            options={difficulties.map((v) => ({
              value: v,
              label: t(`enums.detectionDifficulty.${v}`),
            }))}
          />
          <FormTextField
            name="description"
            control={control}
            label={t('pages.ipm.description')}
            multiline
            rows={3}
          />
          <FormActions
            onCancel={onClose}
            loading={saving}
            saveLabel={t('common.create')}
          />
        </form>
      </DialogContent>
    </Dialog>
  );
}
