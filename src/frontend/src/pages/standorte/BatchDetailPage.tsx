import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import FormTextField from '@/components/form/FormTextField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/substrates';
import type { Batch } from '@/api/types';

const schema = z.object({
  batch_id: z.string().min(1),
  substrate_key: z.string(),
  volume_liters: z.number().min(0),
  mixed_on: z.string().min(1),
});

type FormData = z.infer<typeof schema>;

export default function BatchDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [batch, setBatch] = useState<Batch | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { batch_id: '', substrate_key: '', volume_liters: 0, mixed_on: '' },
  });

  const load = async () => {
    if (!key) return;
    setLoading(true);
    try {
      const b = await api.getBatch(key);
      setBatch(b);
      reset({
        batch_id: b.batch_id,
        substrate_key: b.substrate_key,
        volume_liters: b.volume_liters,
        mixed_on: b.mixed_on,
      });
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  const onSubmit = async (data: FormData) => {
    if (!key) return;
    try {
      setSaving(true);
      await api.updateBatch(key, data);
      notification.success(t('common.save'));
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async () => {
    if (!key) return;
    try {
      await api.deleteBatch(key);
      notification.success(t('common.delete'));
      navigate(-1);
    } catch (err) {
      handleError(err);
    }
    setDeleteOpen(false);
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} onRetry={() => navigate(-1)} />;

  return (
    <>
      <UnsavedChangesGuard dirty={isDirty} />
      <PageTitle
        title={batch?.batch_id ?? t('entities.batch')}
        action={
          <Button color="error" startIcon={<DeleteIcon />} onClick={() => setDeleteOpen(true)}>
            {t('common.delete')}
          </Button>
        }
      />

      <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 900 }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.batches.editIntro')}
        </Typography>
        <FormRow>
          <FormTextField name="batch_id" control={control} label={t('pages.batches.batchId')} helperText={t('pages.batches.batchIdHelper')} required />
          <FormNumberField name="volume_liters" control={control} label={t('pages.batches.volume')} helperText={t('pages.batches.volumeHelper')} min={0} step={0.1} />
        </FormRow>
        <FormTextField name="mixed_on" control={control} label={t('pages.batches.mixedOn')} helperText={t('pages.batches.mixedOnHelper')} type="date" required />

        {batch && (
          <Box sx={{ mt: 2, mb: 2, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
            <Typography variant="subtitle2" color="text.secondary">{t('pages.batches.cyclesUsed')}</Typography>
            <Typography>{batch.cycles_used}</Typography>
            {batch.ph_current != null && (
              <>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>{t('pages.batches.phCurrent')}</Typography>
                <Typography>{batch.ph_current}</Typography>
              </>
            )}
            {batch.ec_current_ms != null && (
              <>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>{t('pages.batches.ecCurrent')}</Typography>
                <Typography>{batch.ec_current_ms} mS/cm</Typography>
              </>
            )}
          </Box>
        )}

        <FormActions onCancel={() => navigate(-1)} loading={saving} />
      </Box>

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: batch?.batch_id })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />
    </>
  );
}
