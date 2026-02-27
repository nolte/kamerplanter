import { useState } from 'react';
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
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/tanks';

const tankTypes = ['nutrient', 'irrigation', 'reservoir', 'recirculation'] as const;
const materials = ['plastic', 'stainless_steel', 'glass', 'ibc'] as const;

const schema = z.object({
  name: z.string().min(1).max(200),
  tank_type: z.enum(tankTypes),
  volume_liters: z.number().gt(0),
  material: z.enum(materials),
  has_lid: z.boolean(),
  has_air_pump: z.boolean(),
  has_circulation_pump: z.boolean(),
  has_heater: z.boolean(),
  notes: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function TankCreateDialog({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      tank_type: 'nutrient',
      volume_liters: 50,
      material: 'plastic',
      has_lid: false,
      has_air_pump: false,
      has_circulation_pump: false,
      has_heater: false,
      notes: null,
    },
  });

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await api.createTank(data);
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
      <DialogTitle>{t('pages.tanks.create')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField
            name="name"
            control={control}
            label={t('pages.tanks.name')}
            required
          />
          <FormSelectField
            name="tank_type"
            control={control}
            label={t('pages.tanks.tankType')}
            options={tankTypes.map((v) => ({
              value: v,
              label: t(`enums.tankType.${v}`),
            }))}
          />
          <FormNumberField
            name="volume_liters"
            control={control}
            label={t('pages.tanks.volumeLiters')}
            min={0.1}
          />
          <FormSelectField
            name="material"
            control={control}
            label={t('pages.tanks.material')}
            options={materials.map((v) => ({
              value: v,
              label: t(`enums.tankMaterial.${v}`),
            }))}
          />
          <FormSwitchField
            name="has_lid"
            control={control}
            label={t('pages.tanks.hasLid')}
          />
          <FormSwitchField
            name="has_air_pump"
            control={control}
            label={t('pages.tanks.hasAirPump')}
          />
          <FormSwitchField
            name="has_circulation_pump"
            control={control}
            label={t('pages.tanks.hasCirculationPump')}
          />
          <FormSwitchField
            name="has_heater"
            control={control}
            label={t('pages.tanks.hasHeater')}
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
