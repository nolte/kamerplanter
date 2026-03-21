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
import FormDateField from '@/components/form/FormDateField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/substrates';
import type { Batch } from '@/api/types';
import { generateBatchId } from '@/utils/idGenerator';

const schema = z.object({
  batch_id: z.string().min(1),
  volume_liters: z.number().min(0),
  mixed_on: z.string().min(1),
});

type FormData = z.infer<typeof schema>;

interface Props {
  substrateKey: string;
  open: boolean;
  onClose: () => void;
  onCreated: (batch: Batch) => void;
}

export default function BatchCreateDialog({ substrateKey, open, onClose, onCreated }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      batch_id: '',
      volume_liters: 0,
      mixed_on: new Date().toISOString().split('T')[0],
    },
  });

  useEffect(() => {
    if (open) {
      reset({
        batch_id: generateBatchId(substrateKey),
        volume_liters: 0,
        mixed_on: new Date().toISOString().split('T')[0],
      });
    }
  }, [open, substrateKey, reset]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      const batch = await api.createBatch({ ...data, substrate_key: substrateKey });
      notification.success(t('common.create'));
      reset();
      onCreated(batch);
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog fullScreen={fullScreen} open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('pages.batches.create')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField name="batch_id" control={control} label={t('pages.batches.batchId')} helperText={t('pages.batches.batchIdHelper')} required />
          <FormNumberField name="volume_liters" control={control} label={t('pages.batches.volume')} helperText={t('pages.batches.volumeHelper')} min={0} step={0.5} />
          <FormDateField name="mixed_on" control={control} label={t('pages.batches.mixedOn')} required />
          <FormActions onCancel={onClose} loading={saving} saveLabel={t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
