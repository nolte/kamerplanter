import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
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

const treatmentTypes = ['cultural', 'biological', 'chemical', 'mechanical'] as const;
const applicationMethods = ['spray', 'drench', 'granular', 'release', 'cultural'] as const;

const schema = z.object({
  name: z.string().min(1).max(200),
  treatment_type: z.enum(treatmentTypes),
  active_ingredient: z.string().nullable(),
  application_method: z.enum(applicationMethods),
  safety_interval_days: z.number().int().min(0),
  dosage_per_liter: z.number().positive().nullable(),
  protective_equipment: z.array(z.string()),
  description: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function TreatmentCreateDialog({ open, onClose, onCreated }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      treatment_type: 'cultural',
      active_ingredient: null,
      application_method: 'spray',
      safety_interval_days: 0,
      dosage_per_liter: null,
      protective_equipment: [],
      description: null,
    },
  });
  useEffect(() => {
    if (!open) {
      reset();
    }
  }, [open, reset]);


  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await api.createTreatment({
        name: data.name,
        treatment_type: data.treatment_type,
        active_ingredient: data.active_ingredient,
        application_method: data.application_method,
        safety_interval_days: data.safety_interval_days,
        dosage_per_liter: data.dosage_per_liter,
        protective_equipment: data.protective_equipment,
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
    <Dialog fullScreen={fullScreen} open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('pages.ipm.createTreatment')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.ipm.treatmentCreateIntro')}
        </Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField
            name="name"
            control={control}
            label={t('pages.ipm.treatmentName')}
            required
            autoFocus
            helperText={t('pages.ipm.treatmentNameHelper')}
          />
          <FormSelectField
            name="treatment_type"
            control={control}
            label={t('pages.ipm.treatmentType')}
            options={treatmentTypes.map((v) => ({
              value: v,
              label: t(`enums.treatmentType.${v}`),
            }))}
          />
          <FormTextField
            name="active_ingredient"
            control={control}
            label={t('pages.ipm.activeIngredient')}
            helperText={t('pages.ipm.activeIngredientHelper')}
          />
          <FormSelectField
            name="application_method"
            control={control}
            label={t('pages.ipm.applicationMethod')}
            options={applicationMethods.map((v) => ({
              value: v,
              label: t(`enums.ipmApplicationMethod.${v}`),
            }))}
          />
          <FormNumberField
            name="safety_interval_days"
            control={control}
            label={t('pages.ipm.safetyIntervalDays')}
            min={0}
            step={1}
            helperText={t('pages.ipm.safetyIntervalDaysHelper')}
          />
          <FormNumberField
            name="dosage_per_liter"
            control={control}
            label={t('pages.ipm.dosagePerLiter')}
            min={0}
            helperText={t('pages.ipm.dosagePerLiterHelper')}
          />
          <FormChipInput
            name="protective_equipment"
            control={control}
            label={t('pages.ipm.protectiveEquipment')}
            helperText={t('pages.ipm.protectiveEquipmentHelper')}
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
