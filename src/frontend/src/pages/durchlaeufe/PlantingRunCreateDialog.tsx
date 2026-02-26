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
import type { Control, UseFormSetValue } from 'react-hook-form';
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
import * as sitesApi from '@/api/endpoints/sites';
import type { Species, Cultivar, Site, Location } from '@/api/types';

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
  site_key: z.string().nullable().optional(),
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

interface EntryRowProps {
  index: number;
  control: Control<FormData>;
  setValue: UseFormSetValue<FormData>;
  speciesList: Species[];
  roles: { value: string; label: string }[];
  onRemove: () => void;
  canRemove: boolean;
}

function EntryRow({ index, control, setValue, speciesList, roles, onRemove, canRemove }: EntryRowProps) {
  const { t } = useTranslation();
  const [cultivarList, setCultivarList] = useState<Cultivar[]>([]);
  const [cultivarsLoading, setCultivarsLoading] = useState(false);
  const speciesKey = useWatch({ control, name: `entries.${index}.species_key` });

  useEffect(() => {
    if (!speciesKey) {
      setCultivarList([]);
      return;
    }
    setCultivarsLoading(true);
    setValue(`entries.${index}.cultivar_key`, null);
    speciesApi
      .listCultivars(speciesKey)
      .then(setCultivarList)
      .catch(() => setCultivarList([]))
      .finally(() => setCultivarsLoading(false));
  }, [speciesKey, index, setValue]);

  return (
    <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start', mb: 1, flexWrap: 'wrap' }}>
      <Box sx={{ flex: 1, minWidth: 160 }}>
        <FormSelectField
          name={`entries.${index}.species_key`}
          control={control}
          label={t('entities.species')}
          required
          options={speciesList.map((s) => ({ value: s.key, label: s.scientific_name }))}
        />
      </Box>
      <Box sx={{ flex: 1, minWidth: 160 }}>
        <FormSelectField
          name={`entries.${index}.cultivar_key`}
          control={control}
          label={t('entities.cultivar')}
          disabled={!speciesKey || cultivarsLoading}
          options={[
            { value: '', label: '-' },
            ...cultivarList.map((c) => ({ value: c.key, label: c.name })),
          ]}
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
        onClick={onRemove}
        disabled={!canRemove}
        sx={{ mt: 1 }}
      >
        <DeleteIcon />
      </IconButton>
    </Box>
  );
}

export default function PlantingRunCreateDialog({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [speciesList, setSpeciesList] = useState<Species[]>([]);
  const [sitesList, setSitesList] = useState<Site[]>([]);
  const [locationsList, setLocationsList] = useState<Location[]>([]);
  const [locationsLoading, setLocationsLoading] = useState(false);

  const { control, handleSubmit, reset, setValue } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      run_type: 'monoculture',
      site_key: null,
      location_key: null,
      substrate_batch_key: null,
      planned_start_date: new Date().toISOString().split('T')[0],
      source_plant_key: null,
      notes: null,
      entries: [{ species_key: '', cultivar_key: null, quantity: 1, role: 'primary', id_prefix: '', spacing_cm: null, notes: null }],
    },
  });

  const { fields, append, remove } = useFieldArray({ control, name: 'entries' });
  const runType = useWatch({ control, name: 'run_type' });
  const siteKey = useWatch({ control, name: 'site_key' });

  useEffect(() => {
    if (open) {
      reset({
        name: '',
        run_type: 'monoculture',
        site_key: null,
        location_key: null,
        substrate_batch_key: null,
        planned_start_date: new Date().toISOString().split('T')[0],
        source_plant_key: null,
        notes: null,
        entries: [{ species_key: '', cultivar_key: null, quantity: 1, role: 'primary', id_prefix: '', spacing_cm: null, notes: null }],
      });
      setLocationsList([]);
      speciesApi.listSpecies(0, 200).then((r) => setSpeciesList(r.items)).catch(() => {});
      sitesApi.listSites(0, 200).then(setSitesList).catch(() => {});
    }
  }, [open, reset]);

  useEffect(() => {
    if (!siteKey) {
      setLocationsList([]);
      return;
    }
    setLocationsLoading(true);
    setValue('location_key', null);
    sitesApi
      .listLocations(siteKey)
      .then(setLocationsList)
      .catch(() => setLocationsList([]))
      .finally(() => setLocationsLoading(false));
  }, [siteKey, setValue]);

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
          <FormSelectField
            name="site_key"
            control={control}
            label={t('entities.site')}
            options={[
              { value: '', label: '-' },
              ...sitesList.map((s) => ({ value: s.key, label: s.name })),
            ]}
          />
          <FormSelectField
            name="location_key"
            control={control}
            label={t('pages.plantingRuns.location')}
            disabled={!siteKey || locationsLoading}
            options={[
              { value: '', label: '-' },
              ...locationsList.map((l) => ({ value: l.key, label: l.name })),
            ]}
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
            <EntryRow
              key={field.id}
              index={index}
              control={control}
              setValue={setValue}
              speciesList={speciesList}
              roles={roles}
              onRemove={() => remove(index)}
              canRemove={fields.length > 1}
            />
          ))}

          <Button
            startIcon={<AddIcon />}
            onClick={() =>
              append({ species_key: '', cultivar_key: null, quantity: 1, role: 'primary', id_prefix: '', spacing_cm: null, notes: null })
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
