import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
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
import { generateSlotId } from '@/utils/idGenerator';

const schema = z.object({
  slot_id: z
    .string()
    .min(1)
    .transform((v) => v.toUpperCase())
    .pipe(z.string().regex(/^[A-Z0-9]+_[A-Z0-9]+$/, 'slot_id_format')),
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
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { slot_id: '', capacity_plants: 1 },
  });

  useEffect(() => {
    if (open) {
      reset({ slot_id: generateSlotId(locationKey), capacity_plants: 1 });
    }
  }, [open, locationKey, reset]);

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
    <Dialog fullScreen={fullScreen} open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('pages.slots.create')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField name="slot_id" control={control} label={t('pages.slots.slotId')} helperText={t('pages.slots.slotIdHelper')} required />
          <FormNumberField name="capacity_plants" control={control} label={t('pages.slots.capacity')} helperText={t('pages.slots.capacityHelper')} min={1} max={20} />
          <FormActions onCancel={onClose} loading={saving} saveLabel={t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
