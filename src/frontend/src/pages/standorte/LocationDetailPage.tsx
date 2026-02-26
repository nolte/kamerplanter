import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import DataTable, { type Column } from '@/components/common/DataTable';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormTimeField from '@/components/form/FormTimeField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import SlotCreateDialog from './SlotCreateDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/sites';
import type { Location, Slot } from '@/api/types';
import Chip from '@mui/material/Chip';

const timeRegex = /^\d{2}:\d{2}$/;

const schema = z.object({
  name: z.string().min(1),
  site_key: z.string(),
  area_m2: z.number().min(0),
  light_type: z.enum(['natural', 'led', 'hps', 'cmh', 'mixed']),
  irrigation_system: z.enum(['manual', 'drip', 'hydro', 'mist']),
  lights_on: z.string().regex(timeRegex).nullable().optional(),
  lights_off: z.string().regex(timeRegex).nullable().optional(),
  use_dynamic_sunrise: z.boolean(),
});

type FormData = z.infer<typeof schema>;

export default function LocationDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [location, setLocation] = useState<Location | null>(null);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [slotCreateOpen, setSlotCreateOpen] = useState(false);

  const { control, handleSubmit, reset, formState: { isDirty } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      site_key: '',
      area_m2: 0,
      light_type: 'natural',
      irrigation_system: 'manual',
      lights_on: null,
      lights_off: null,
      use_dynamic_sunrise: false,
    },
  });

  const lightType = useWatch({ control, name: 'light_type' });
  const isArtificial = lightType === 'led' || lightType === 'hps' || lightType === 'cmh';
  const isNaturalOrMixed = lightType === 'natural' || lightType === 'mixed';

  const load = async () => {
    if (!key) return;
    setLoading(true);
    try {
      const loc = await api.getLocation(key);
      setLocation(loc);
      reset({
        name: loc.name,
        site_key: loc.site_key,
        area_m2: loc.area_m2,
        light_type: loc.light_type,
        irrigation_system: loc.irrigation_system,
        lights_on: loc.lights_on,
        lights_off: loc.lights_off,
        use_dynamic_sunrise: loc.use_dynamic_sunrise,
      });
      const s = await api.listSlots(key);
      setSlots(s);
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
      await api.updateLocation(key, {
        ...data,
        lights_on: data.lights_on || undefined,
        lights_off: data.lights_off || undefined,
      });
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
      await api.deleteLocation(key);
      notification.success(t('common.delete'));
      navigate(-1);
    } catch (err) {
      handleError(err);
    }
    setDeleteOpen(false);
  };

  const slotColumns: Column<Slot>[] = [
    { id: 'slotId', label: t('pages.slots.slotId'), render: (r) => r.slot_id },
    { id: 'position', label: t('pages.slots.position'), render: (r) => `(${r.position[0]}, ${r.position[1]})` },
    { id: 'capacity', label: t('pages.slots.capacity'), render: (r) => r.capacity_plants },
    { id: 'occupied', label: t('pages.slots.occupied'), render: (r) => (
      <Chip label={r.currently_occupied ? t('common.yes') : t('common.no')} size="small" color={r.currently_occupied ? 'warning' : 'default'} />
    )},
  ];

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} onRetry={() => navigate(-1)} />;

  return (
    <>
      <UnsavedChangesGuard dirty={isDirty} />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle title={location?.name ?? t('entities.location')} />
        <Button color="error" startIcon={<DeleteIcon />} onClick={() => setDeleteOpen(true)}>
          {t('common.delete')}
        </Button>
      </Box>

      <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 600 }}>
        <FormTextField name="name" control={control} label={t('pages.locations.name')} required />
        <FormNumberField name="area_m2" control={control} label={t('pages.locations.area')} min={0} />
        <FormSelectField
          name="light_type"
          control={control}
          label={t('pages.locations.lightType')}
          options={['natural', 'led', 'hps', 'cmh', 'mixed'].map((v) => ({
            value: v, label: t(`enums.lightType.${v}`),
          }))}
        />
        <FormSelectField
          name="irrigation_system"
          control={control}
          label={t('pages.locations.irrigationSystem')}
          options={['manual', 'drip', 'hydro', 'mist'].map((v) => ({
            value: v, label: t(`enums.irrigationSystem.${v}`),
          }))}
        />

        {(isArtificial || isNaturalOrMixed) && (
          <>
            <FormTimeField
              name="lights_on"
              control={control}
              label={t('pages.locations.lightsOn')}
              helperText={t('pages.locations.lightsOnHelper')}
            />
            <FormTimeField
              name="lights_off"
              control={control}
              label={t('pages.locations.lightsOff')}
              helperText={t('pages.locations.lightsOffHelper')}
            />
          </>
        )}

        {isNaturalOrMixed && (
          <FormSwitchField
            name="use_dynamic_sunrise"
            control={control}
            label={t('pages.locations.useDynamicSunrise')}
          />
        )}

        <FormActions onCancel={() => navigate(-1)} loading={saving} />
      </Box>

      <Box sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">{t('pages.slots.title')}</Typography>
          <Button startIcon={<AddIcon />} onClick={() => setSlotCreateOpen(true)}>
            {t('pages.slots.create')}
          </Button>
        </Box>
        <DataTable columns={slotColumns} rows={slots} getRowKey={(r) => r.key} onRowClick={(r) => navigate(`/standorte/slots/${r.key}`)} />
      </Box>

      {key && (
        <SlotCreateDialog
          locationKey={key}
          open={slotCreateOpen}
          onClose={() => setSlotCreateOpen(false)}
          onCreated={() => { setSlotCreateOpen(false); load(); }}
        />
      )}

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: location?.name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />
    </>
  );
}
