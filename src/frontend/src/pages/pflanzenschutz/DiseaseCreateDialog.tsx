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
import FormChipInput from '@/components/form/FormChipInput';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/ipm';

const pathogenTypes = ['fungal', 'bacterial', 'viral', 'physiological'] as const;

const schema = z.object({
  scientific_name: z.string().min(1).max(200),
  common_name: z.string().min(1).max(200),
  pathogen_type: z.enum(pathogenTypes),
  incubation_period_days: z.number().int().positive().nullable(),
  environmental_triggers: z.array(z.string()),
  affected_plant_parts: z.array(z.string()),
  description: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function DiseaseCreateDialog({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      scientific_name: '',
      common_name: '',
      pathogen_type: 'fungal',
      incubation_period_days: null,
      environmental_triggers: [],
      affected_plant_parts: [],
      description: null,
    },
  });

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await api.createDisease({
        scientific_name: data.scientific_name,
        common_name: data.common_name,
        pathogen_type: data.pathogen_type,
        incubation_period_days: data.incubation_period_days,
        environmental_triggers: data.environmental_triggers,
        affected_plant_parts: data.affected_plant_parts,
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
      <DialogTitle>{t('pages.ipm.createDisease')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.ipm.diseaseCreateIntro')}
        </Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField
            name="scientific_name"
            control={control}
            label={t('pages.ipm.scientificName')}
            required
            helperText={t('pages.ipm.diseaseScientificNameHelper')}
          />
          <FormTextField
            name="common_name"
            control={control}
            label={t('pages.ipm.commonName')}
            required
            helperText={t('pages.ipm.commonNameHelper')}
          />
          <FormSelectField
            name="pathogen_type"
            control={control}
            label={t('pages.ipm.pathogenType')}
            options={pathogenTypes.map((v) => ({
              value: v,
              label: t(`enums.pathogenType.${v}`),
            }))}
          />
          <FormNumberField
            name="incubation_period_days"
            control={control}
            label={t('pages.ipm.incubationPeriodDays')}
            min={1}
            step={1}
            helperText={t('pages.ipm.incubationPeriodDaysHelper')}
          />
          <FormChipInput
            name="environmental_triggers"
            control={control}
            label={t('pages.ipm.environmentalTriggers')}
            helperText={t('pages.ipm.environmentalTriggersHelper')}
          />
          <FormChipInput
            name="affected_plant_parts"
            control={control}
            label={t('pages.ipm.affectedPlantParts')}
            helperText={t('pages.ipm.affectedPlantPartsHelper')}
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
