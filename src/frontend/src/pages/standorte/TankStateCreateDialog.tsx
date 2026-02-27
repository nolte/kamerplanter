import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/tanks';

const schema = z.object({
  ph: z.number().min(0).max(14).nullable(),
  ec_ms: z.number().min(0).nullable(),
  water_temp_celsius: z.number().min(0).max(50).nullable(),
  fill_level_percent: z.number().min(0).max(100).nullable(),
  fill_level_liters: z.number().min(0).nullable(),
  tds_ppm: z.number().min(0).nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  tankKey: string;
  onCreated: () => void;
}

export default function TankStateCreateDialog({ open, onClose, tankKey, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      ph: null,
      ec_ms: null,
      water_temp_celsius: null,
      fill_level_percent: null,
      fill_level_liters: null,
      tds_ppm: null,
    },
  });

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await api.recordState(tankKey, {
        ph: data.ph,
        ec_ms: data.ec_ms,
        water_temp_celsius: data.water_temp_celsius,
        fill_level_percent: data.fill_level_percent,
        fill_level_liters: data.fill_level_liters,
        tds_ppm: data.tds_ppm,
        source: 'manual',
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
      <DialogTitle>{t('pages.tanks.recordState')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormNumberField
            name="ph"
            control={control}
            label="pH"
            min={0}
            max={14}
          />
          <FormNumberField
            name="ec_ms"
            control={control}
            label="EC (mS/cm)"
            min={0}
          />
          <FormNumberField
            name="water_temp_celsius"
            control={control}
            label={t('pages.tanks.waterTemp')}
            min={0}
            max={50}
          />
          <FormNumberField
            name="fill_level_percent"
            control={control}
            label={t('pages.tanks.fillLevelPercent')}
            min={0}
            max={100}
          />
          <FormNumberField
            name="fill_level_liters"
            control={control}
            label={t('pages.tanks.fillLevelLiters')}
            min={0}
          />
          <FormNumberField
            name="tds_ppm"
            control={control}
            label="TDS (ppm)"
            min={0}
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
