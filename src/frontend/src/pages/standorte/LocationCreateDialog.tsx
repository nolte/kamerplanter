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
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/sites';

const schema = z.object({
  name: z.string().min(1),
  area_m2: z.number().min(0),
  light_type: z.enum(['natural', 'led', 'hps', 'cmh', 'mixed']),
  irrigation_system: z.enum(['manual', 'drip', 'hydro', 'mist']),
});

type FormData = z.infer<typeof schema>;

interface Props {
  siteKey: string;
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function LocationCreateDialog({ siteKey, open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { name: '', area_m2: 0, light_type: 'natural', irrigation_system: 'manual' },
  });

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await api.createLocation({ ...data, site_key: siteKey });
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
      <DialogTitle>{t('pages.locations.create')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField name="name" control={control} label={t('pages.locations.name')} required />
          <FormNumberField name="area_m2" control={control} label={t('pages.locations.area')} min={0} />
          <FormSelectField
            name="light_type"
            control={control}
            label={t('pages.locations.lightType')}
            options={['natural', 'led', 'hps', 'cmh', 'mixed'].map((v) => ({
              value: v,
              label: t(`enums.lightType.${v}`),
            }))}
          />
          <FormSelectField
            name="irrigation_system"
            control={control}
            label={t('pages.locations.irrigationSystem')}
            options={['manual', 'drip', 'hydro', 'mist'].map((v) => ({
              value: v,
              label: t(`enums.irrigationSystem.${v}`),
            }))}
          />
          <FormActions onCancel={onClose} loading={saving} saveLabel={t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
