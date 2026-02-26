import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
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
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/sites';
import type { Slot } from '@/api/types';

const schema = z.object({
  slot_id: z
    .string()
    .min(1)
    .transform((v) => v.toUpperCase())
    .pipe(z.string().regex(/^[A-Z0-9]+_[A-Z0-9]+$/, 'slot_id_format')),
  location_key: z.string(),
  capacity_plants: z.number().min(1).max(20),
});

type FormData = z.infer<typeof schema>;

export default function SlotDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [slot, setSlot] = useState<Slot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const { control, handleSubmit, reset, formState: { isDirty } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { slot_id: '', location_key: '', capacity_plants: 1 },
  });

  useEffect(() => {
    if (!key) return;
    setLoading(true);
    api.getSlot(key)
      .then((s) => {
        setSlot(s);
        reset({ slot_id: s.slot_id, location_key: s.location_key, capacity_plants: s.capacity_plants });
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [key, reset]);

  const onSubmit = async (data: FormData) => {
    if (!key) return;
    try {
      setSaving(true);
      await api.updateSlot(key, data);
      notification.success(t('common.save'));
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async () => {
    if (!key) return;
    try {
      await api.deleteSlot(key);
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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle title={slot?.slot_id ?? t('entities.slot')} />
        <Button color="error" startIcon={<DeleteIcon />} onClick={() => setDeleteOpen(true)}>
          {t('common.delete')}
        </Button>
      </Box>

      <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 600 }}>
        <FormTextField name="slot_id" control={control} label={t('pages.slots.slotId')} helperText={t('pages.slots.slotIdHelper')} required />
        <FormNumberField name="capacity_plants" control={control} label={t('pages.slots.capacity')} min={1} max={20} />
        <FormActions onCancel={() => navigate(-1)} loading={saving} />
      </Box>

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: slot?.slot_id })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />
    </>
  );
}
