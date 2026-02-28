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
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import LocationListSection from './LocationListSection';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchSite, clearCurrent } from '@/store/slices/sitesSlice';
import * as api from '@/api/endpoints/sites';

const schema = z.object({
  name: z.string().min(1),
  type: z.enum(['outdoor', 'greenhouse', 'indoor', 'windowsill', 'balcony', 'grow_tent']),
  climate_zone: z.string(),
  total_area_m2: z.number().min(0),
  timezone: z.string(),
});

type FormData = z.infer<typeof schema>;

export default function SiteDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { currentSite: current, loading, error } = useAppSelector((s) => s.sites);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const { control, handleSubmit, reset, formState: { isDirty } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { name: '', type: 'indoor', climate_zone: '', total_area_m2: 0, timezone: 'UTC' },
  });

  useEffect(() => {
    if (key) dispatch(fetchSite(key));
    return () => { dispatch(clearCurrent()); };
  }, [key, dispatch]);

  useEffect(() => {
    if (current) {
      reset({ name: current.name, type: current.type, climate_zone: current.climate_zone, total_area_m2: current.total_area_m2, timezone: current.timezone ?? 'UTC' });
    }
  }, [current, reset]);

  const onSubmit = async (data: FormData) => {
    if (!key) return;
    try {
      setSaving(true);
      await api.updateSite(key, data);
      notification.success(t('common.save'));
      dispatch(fetchSite(key));
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async () => {
    if (!key) return;
    try {
      await api.deleteSite(key);
      notification.success(t('common.delete'));
      navigate('/standorte/sites');
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
        <PageTitle title={current?.name ?? t('entities.site')} />
        <Button color="error" startIcon={<DeleteIcon />} onClick={() => setDeleteOpen(true)}>
          {t('common.delete')}
        </Button>
      </Box>

      <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 600 }}>
        <FormTextField name="name" control={control} label={t('pages.sites.name')} required />
        <FormSelectField
          name="type"
          control={control}
          label={t('pages.sites.type')}
          options={['outdoor', 'greenhouse', 'indoor', 'windowsill', 'balcony', 'grow_tent'].map((v) => ({
            value: v,
            label: t(`enums.siteType.${v}`),
          }))}
        />
        <FormTextField name="climate_zone" control={control} label={t('pages.sites.climateZone')} />
        <FormNumberField name="total_area_m2" control={control} label={t('pages.sites.totalArea')} min={0} />
        <FormTextField name="timezone" control={control} label={t('pages.sites.timezone')} helperText={t('pages.sites.timezoneHelper')} />
        <FormActions onCancel={() => navigate(-1)} loading={saving} />
      </Box>

      {key && <LocationListSection siteKey={key} />}

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: current?.name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />
    </>
  );
}
