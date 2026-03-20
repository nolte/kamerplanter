import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormSelectField from '@/components/form/FormSelectField';
import FormTextField from '@/components/form/FormTextField';
import FormNumberField from '@/components/form/FormNumberField';
import FormRow from '@/components/form/FormRow';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/tanks';

const maintenanceTypes = [
  'water_change',
  'cleaning',
  'sanitization',
  'calibration',
  'filter_change',
  'pump_inspection',
] as const;

const schema = z.object({
  maintenance_type: z.enum(maintenanceTypes),
  performed_by: z.string(),
  duration_minutes: z.number().min(1).nullable(),
  products_used: z.string(),
  notes: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  tankKey: string;
  onCreated: () => void;
}

export default function MaintenanceLogDialog({ open, onClose, tankKey, onCreated }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      maintenance_type: 'water_change',
      performed_by: '',
      duration_minutes: null,
      products_used: '',
      notes: null,
    },
  });

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await api.logMaintenance(tankKey, {
        maintenance_type: data.maintenance_type,
        performed_by: data.performed_by || undefined,
        duration_minutes: data.duration_minutes,
        products_used: data.products_used
          ? data.products_used.split(',').map((s) => s.trim())
          : [],
        notes: data.notes,
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
      <DialogTitle>{t('pages.tanks.logMaintenance')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormSelectField
            name="maintenance_type"
            control={control}
            label={t('pages.tanks.maintenanceType')}
            options={maintenanceTypes.map((v) => ({
              value: v,
              label: t(`enums.maintenanceType.${v}`),
            }))}
          />
          <FormRow>
            <FormTextField
              name="performed_by"
              control={control}
              label={t('pages.tanks.performedBy')}
            />
            <FormNumberField
              name="duration_minutes"
              control={control}
              label={t('pages.tanks.durationMinutes')}
              helperText={t('pages.tanks.durationMinutesHelper')}
              min={1}
              inputMode="numeric"
            />
          </FormRow>
          <FormTextField
            name="products_used"
            control={control}
            label={t('pages.tanks.productsUsed')}
            helperText={t('pages.tanks.productsUsedHelper')}
          />
          <FormTextField
            name="notes"
            control={control}
            label={t('pages.tanks.notes')}
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
