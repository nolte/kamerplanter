import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import { useForm, useFieldArray, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormDateField from '@/components/form/FormDateField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as runApi from '@/api/endpoints/plantingRuns';
import * as speciesApi from '@/api/endpoints/species';
import type { Species } from '@/api/types';

const entrySchema = z.object({
  species_key: z.string().min(1),
  cultivar_key: z.string().nullable().optional(),
  quantity: z.number().min(1),
  role: z.string(),
  id_prefix: z.string().regex(/^[A-Z]{2,5}$/),
  spacing_cm: z.number().nullable().optional(),
  notes: z.string().nullable().optional(),
});

const schema = z.object({
  name: z.string().min(1).max(200),
  run_type: z.enum(['monoculture', 'clone', 'mixed_culture']),
  location_key: z.string().nullable().optional(),
  substrate_batch_key: z.string().nullable().optional(),
  planned_start_date: z.string().nullable().optional(),
  source_plant_key: z.string().nullable().optional(),
  notes: z.string().nullable().optional(),
  entries: z.array(entrySchema).min(1),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function PlantingRunCreateDialog({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [speciesList, setSpeciesList] = useState<Species[]>([]);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      run_type: 'monoculture',
      location_key: null,
      substrate_batch_key: null,
      planned_start_date: new Date().toISOString().split('T')[0],
      source_plant_key: null,
      notes: null,
      entries: [{ species_key: '', quantity: 1, role: 'primary', id_prefix: '', spacing_cm: null, notes: null }],
    },
  });

  const { fields, append, remove } = useFieldArray({ control, name: 'entries' });
  const runType = useWatch({ control, name: 'run_type' });

  useEffect(() => {
    if (open) {
      reset({
        name: '',
        run_type: 'monoculture',
        location_key: null,
        substrate_batch_key: null,
        planned_start_date: new Date().toISOString().split('T')[0],
        source_plant_key: null,
        notes: null,
        entries: [{ species_key: '', quantity: 1, role: 'primary', id_prefix: '', spacing_cm: null, notes: null }],
      });
      speciesApi.listSpecies(0, 200).then((r) => setSpeciesList(r.items)).catch(() => {});
    }
  }, [open, reset]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await runApi.createPlantingRun({
        name: data.name,
        run_type: data.run_type,
        location_key: data.location_key || undefined,
        substrate_batch_key: data.substrate_batch_key || undefined,
        planned_start_date: data.planned_start_date || undefined,
        source_plant_key: data.source_plant_key || undefined,
        notes: data.notes || undefined,
        entries: data.entries.map((e) => ({
          species_key: e.species_key,
          cultivar_key: e.cultivar_key || undefined,
          quantity: e.quantity,
          role: e.role as 'primary' | 'companion' | 'trap_crop',
          id_prefix: e.id_prefix,
          spacing_cm: e.spacing_cm ?? undefined,
          notes: e.notes || undefined,
        })),
      });
      notification.success(t('common.create'));
      reset();
      onCreated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const runTypes = [
    { value: 'monoculture', label: t('enums.plantingRunType.monoculture') },
    { value: 'clone', label: t('enums.plantingRunType.clone') },
    { value: 'mixed_culture', label: t('enums.plantingRunType.mixed_culture') },
  ];

  const roles = [
    { value: 'primary', label: t('enums.entryRole.primary') },
    { value: 'companion', label: t('enums.entryRole.companion') },
    { value: 'trap_crop', label: t('enums.entryRole.trap_crop') },
  ];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{t('pages.plantingRuns.create')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField name="name" control={control} label={t('pages.plantingRuns.name')} required />
          <FormSelectField
            name="run_type"
            control={control}
            label={t('pages.plantingRuns.runType')}
            required
            options={runTypes}
          />
          <FormTextField
            name="location_key"
            control={control}
            label={t('pages.plantingRuns.location')}
          />
          <FormDateField
            name="planned_start_date"
            control={control}
            label={t('pages.plantingRuns.plannedStartDate')}
          />
          {runType === 'clone' && (
            <FormTextField
              name="source_plant_key"
              control={control}
              label={t('pages.plantingRuns.sourcePlantKey')}
              required
            />
          )}
          <FormTextField name="notes" control={control} label={t('pages.plantingRuns.notes')} />

          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle1" sx={{ mb: 1 }}>
            {t('pages.plantingRuns.entries')}
          </Typography>

          {fields.map((field, index) => (
            <Box key={field.id} sx={{ display: 'flex', gap: 1, alignItems: 'flex-start', mb: 1 }}>
              <Box sx={{ flex: 1 }}>
                <FormSelectField
                  name={`entries.${index}.species_key`}
                  control={control}
                  label={t('entities.species')}
                  required
                  options={speciesList.map((s) => ({ value: s.key, label: s.scientific_name }))}
                />
              </Box>
              <Box sx={{ width: 100 }}>
                <FormNumberField
                  name={`entries.${index}.quantity`}
                  control={control}
                  label={t('pages.plantingRuns.quantity')}
                  required
                  min={1}
                />
              </Box>
              <Box sx={{ width: 100 }}>
                <FormTextField
                  name={`entries.${index}.id_prefix`}
                  control={control}
                  label={t('pages.plantingRuns.idPrefix')}
                  required
                  helperText="A-Z, 2-5"
                />
              </Box>
              <Box sx={{ width: 140 }}>
                <FormSelectField
                  name={`entries.${index}.role`}
                  control={control}
                  label={t('pages.plantingRuns.role')}
                  options={roles}
                />
              </Box>
              <IconButton
                onClick={() => remove(index)}
                disabled={fields.length <= 1}
                sx={{ mt: 1 }}
              >
                <DeleteIcon />
              </IconButton>
            </Box>
          ))}

          <Button
            startIcon={<AddIcon />}
            onClick={() =>
              append({ species_key: '', quantity: 1, role: 'primary', id_prefix: '', spacing_cm: null, notes: null })
            }
            sx={{ mb: 2 }}
          >
            {t('pages.plantingRuns.addEntry')}
          </Button>

          <FormActions onCancel={onClose} loading={saving} saveLabel={t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
