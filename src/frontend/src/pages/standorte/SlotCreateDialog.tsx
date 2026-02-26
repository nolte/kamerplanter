import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/sites';

const schema = z.object({
  slot_id: z.string().min(1).transform((v) => v.toUpperCase()),
  capacity_plants: z.number().min(1).max(20),
});

type FormData = z.infer<typeof schema>;

interface Props {
  locationKey: string;
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function SlotCreateDialog({ locationKey, open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { slot_id: '', capacity_plants: 1 },
  });

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await api.createSlot({ ...data, location_key: locationKey });
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
      <DialogTitle>{t('pages.slots.create')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField name="slot_id" control={control} label={t('pages.slots.slotId')} required />
          <FormNumberField name="capacity_plants" control={control} label={t('pages.slots.capacity')} min={1} max={20} />
          <FormActions onCancel={onClose} loading={saving} saveLabel={t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
