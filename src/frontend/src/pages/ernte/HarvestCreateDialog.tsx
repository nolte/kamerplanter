import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Typography from '@mui/material/Typography';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as harvestApi from '@/api/endpoints/harvest';
import * as plantApi from '@/api/endpoints/plantInstances';
import type { PlantInstance } from '@/api/types';

const harvestTypes = ['partial', 'final', 'continuous'] as const;

const schema = z.object({
  plant_key: z.string().min(1),
  batch_id: z.string().max(100).optional(),
  harvest_type: z.enum(harvestTypes),
  wet_weight_g: z.number().min(0).nullable(),
  harvester: z.string().max(200),
  notes: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
  plantKey?: string;
}

export default function HarvestCreateDialog({
  open,
  onClose,
  onCreated,
  plantKey,
}: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [plants, setPlants] = useState<PlantInstance[]>([]);
  const [loadingPlants, setLoadingPlants] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      plant_key: plantKey ?? '',
      batch_id: '',
      harvest_type: 'final',
      wet_weight_g: null,
      harvester: '',
      notes: null,
    },
  });

  useEffect(() => {
    if (open && !plantKey) {
      setLoadingPlants(true);
      plantApi
        .listPlantInstances()
        .then(setPlants)
        .catch(() => setPlants([]))
        .finally(() => setLoadingPlants(false));
    }
  }, [open, plantKey]);

  useEffect(() => {
    if (open) {
      reset({
        plant_key: plantKey ?? '',
        batch_id: '',
        harvest_type: 'final',
        wet_weight_g: null,
        harvester: '',
        notes: null,
      });
    }
  }, [open, plantKey, reset]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      const { plant_key, ...payload } = data;
      await harvestApi.createBatch(plant_key, {
        batch_id: payload.batch_id || undefined,
        harvest_type: payload.harvest_type,
        wet_weight_g: payload.wet_weight_g,
        harvester: payload.harvester || undefined,
        notes: payload.notes,
      });
      notification.success(t('pages.harvest.created'));
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
      <DialogTitle>{t('pages.harvest.create')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.harvest.createIntro')}
        </Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          {plantKey ? (
            <FormTextField
              name="plant_key"
              control={control}
              label={t('pages.harvest.plantKey')}
              disabled
              required
            />
          ) : (
            <FormSelectField
              name="plant_key"
              control={control}
              label={t('pages.harvest.plantKey')}
              required
              disabled={loadingPlants}
              options={plants.map((p) => ({
                value: p.key,
                label: p.plant_name || p.instance_id,
              }))}
            />
          )}
          <FormTextField
            name="batch_id"
            control={control}
            label={t('pages.harvest.batchId')}
            helperText={t('pages.harvest.batchIdHelper')}
          />
          <FormSelectField
            name="harvest_type"
            control={control}
            label={t('pages.harvest.harvestType')}
            options={harvestTypes.map((v) => ({
              value: v,
              label: t(`enums.harvestType.${v}`),
            }))}
          />
          <FormNumberField
            name="wet_weight_g"
            control={control}
            label={t('pages.harvest.wetWeightG')}
            min={0}
            inputMode="decimal"
            suffix="g"
            helperText={t('pages.harvest.weightHelper')}
          />
          <FormTextField
            name="harvester"
            control={control}
            label={t('pages.harvest.harvester')}
          />
          <FormTextField
            name="notes"
            control={control}
            label={t('pages.harvest.notes')}
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
