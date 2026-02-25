import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormDateField from '@/components/form/FormDateField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as plantApi from '@/api/endpoints/plantInstances';
import * as speciesApi from '@/api/endpoints/species';
import type { Species } from '@/api/types';

const schema = z.object({
  instance_id: z.string().min(1),
  species_key: z.string().min(1),
  plant_name: z.string().nullable(),
  planted_on: z.string().min(1),
  current_phase: z.string(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function PlantInstanceCreateDialog({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [speciesList, setSpeciesList] = useState<Species[]>([]);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      instance_id: '',
      species_key: '',
      plant_name: null,
      planted_on: new Date().toISOString().split('T')[0],
      current_phase: 'seedling',
    },
  });

  useEffect(() => {
    if (open) {
      speciesApi.listSpecies(0, 200).then((r) => setSpeciesList(r.items)).catch(() => {});
    }
  }, [open]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await plantApi.createPlantInstance(data);
      notification.success(t('common.create'));
      reset();
      onCreated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const phases = ['germination', 'seedling', 'vegetative', 'flowering', 'harvest'];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('pages.plantInstances.create')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField name="instance_id" control={control} label={t('pages.plantInstances.instanceId')} required />
          <FormSelectField
            name="species_key"
            control={control}
            label={t('entities.species')}
            required
            options={speciesList.map((s) => ({ value: s.key, label: s.scientific_name }))}
          />
          <FormTextField name="plant_name" control={control} label={t('pages.plantInstances.plantName')} />
          <FormDateField name="planted_on" control={control} label={t('pages.plantInstances.plantedOn')} required />
          <FormSelectField
            name="current_phase"
            control={control}
            label={t('pages.plantInstances.currentPhase')}
            options={phases.map((p) => ({ value: p, label: p }))}
          />
          <FormActions onCancel={onClose} loading={saving} saveLabel={t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
