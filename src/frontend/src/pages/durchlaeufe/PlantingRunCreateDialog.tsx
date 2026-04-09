import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import Checkbox from '@mui/material/Checkbox';
import Chip from '@mui/material/Chip';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import Alert from '@mui/material/Alert';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import type { Control, UseFormSetValue } from 'react-hook-form';
import { useForm, useFieldArray, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormDateField from '@/components/form/FormDateField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import SpeciesAutocompleteField from '@/components/form/SpeciesAutocompleteField';
import ExpertiseFieldWrapper from '@/components/common/ExpertiseFieldWrapper';
import ShowAllFieldsToggle from '@/components/common/ShowAllFieldsToggle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import EmptyState from '@/components/common/EmptyState';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { useAppDispatch } from '@/store/hooks';
import { resetShowAllFields } from '@/store/slices/uiSlice';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { plantingRunFieldConfig } from '@/config/fieldConfigs';
import * as runApi from '@/api/endpoints/plantingRuns';
import * as speciesApi from '@/api/endpoints/species';
import * as sitesApi from '@/api/endpoints/sites';
import * as plantApi from '@/api/endpoints/plantInstances';
import LocationTreeSelect from '@/components/form/LocationTreeSelect';
import type { Species, Cultivar, Site, PlantInstance } from '@/api/types';

const entrySchema = z.object({
  species_key: z.string().min(1),
  cultivar_key: z.string().nullable().optional(),
  quantity: z.number().min(1),
  id_prefix: z.string().regex(/^[A-Z]{2,5}$/),
  spacing_cm: z.number().nullable().optional(),
  notes: z.string().nullable().optional(),
});

const schema = z.object({
  name: z.string().min(1).max(200),
  run_type: z.enum(['monoculture', 'clone']),
  site_key: z.string().nullable().optional(),
  location_key: z.string().nullable().optional(),
  substrate_batch_key: z.string().nullable().optional(),
  planned_start_date: z.string().nullable().optional(),
  source_plant_key: z.string().nullable().optional(),
  notes: z.string().nullable().optional(),
  entries: z.array(entrySchema),
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
  onRemove: () => void;
  canRemove: boolean;
}

function toPrefix(name: string): string {
  return name.replace(/[^a-zA-Z]/g, '').toUpperCase().slice(0, 3);
}

function EntryRow({ index, control, setValue, speciesList, onRemove, canRemove }: EntryRowProps) {
  const { t } = useTranslation();
  const [cultivarList, setCultivarList] = useState<Cultivar[]>([]);
  const [cultivarsLoading, setCultivarsLoading] = useState(false);
  const speciesKey = useWatch({ control, name: `entries.${index}.species_key` });
  const cultivarKey = useWatch({ control, name: `entries.${index}.cultivar_key` });
  const idPrefix = useWatch({ control, name: `entries.${index}.id_prefix` });
  const autoPrefix = useRef('');

  useEffect(() => {
    if (!speciesKey) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- reset state when species cleared
      setCultivarList([]);
      autoPrefix.current = '';
      return;
    }
    setCultivarsLoading(true);
    setValue(`entries.${index}.cultivar_key`, null);
    const species = speciesList.find((s) => s.key === speciesKey);
    if (species) {
      const prefix = toPrefix(species.genus);
      if (prefix.length >= 2 && (!idPrefix || idPrefix === autoPrefix.current)) {
        setValue(`entries.${index}.id_prefix`, prefix);
        autoPrefix.current = prefix;
      }
    }
    speciesApi
      .listCultivars(speciesKey)
      .then(setCultivarList)
      .catch(() => setCultivarList([]))
      .finally(() => setCultivarsLoading(false));
  }, [speciesKey, index, setValue]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!cultivarKey) return;
    const cultivar = cultivarList.find((c) => c.key === cultivarKey);
    if (cultivar) {
      const prefix = toPrefix(cultivar.name);
      if (prefix.length >= 2 && (!idPrefix || idPrefix === autoPrefix.current)) {
        setValue(`entries.${index}.id_prefix`, prefix);
        autoPrefix.current = prefix;
      }
    }
  }, [cultivarKey, cultivarList, index, setValue]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start', mb: 1, flexWrap: 'wrap' }}>
      <Box sx={{ flex: 1, minWidth: 160 }}>
        <SpeciesAutocompleteField
          name={`entries.${index}.species_key`}
          control={control}
          label={t('entities.species')}
          required
          species={speciesList}
        />
      </Box>
      <Box sx={{ flex: 1, minWidth: 160 }}>
        <FormSelectField
          name={`entries.${index}.cultivar_key`}
          control={control}
          label={t('entities.cultivar')}
          disabled={!speciesKey || cultivarsLoading}
          options={[
            { value: '', label: '\u2014' },
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
          helperText={t('pages.plantingRuns.idPrefixHelper')}
        />
      </Box>
      <Tooltip title={t('pages.plantingRuns.removeEntry')}>
        <span style={{ alignSelf: 'flex-start' }}>
          <IconButton
            onClick={onRemove}
            disabled={!canRemove}
            sx={{ mt: 1 }}
            aria-label={t('pages.plantingRuns.removeEntry')}
            data-testid={`remove-entry-${index}`}
          >
            <DeleteIcon />
          </IconButton>
        </span>
      </Tooltip>
    </Box>
  );
}

export default function PlantingRunCreateDialog({ open, onClose, onCreated }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [speciesList, setSpeciesList] = useState<Species[]>([]);
  const [sitesList, setSitesList] = useState<Site[]>([]);
  const [adoptMode, setAdoptMode] = useState(false);
  const [availablePlants, setAvailablePlants] = useState<PlantInstance[]>([]);
  const [plantsLoading, setPlantsLoading] = useState(false);
  const [plantsError, setPlantsError] = useState<string | null>(null);
  const [selectedPlants, setSelectedPlants] = useState<Set<string>>(new Set());
  const [plantSearch, setPlantSearch] = useState('');
  const dispatch = useAppDispatch();
  const { showAllOverride, toggleShowAll, level } = useExpertiseLevel();

  const handleClose = useCallback(() => {
    dispatch(resetShowAllFields());
    onClose();
  }, [dispatch, onClose]);

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
      entries: [{ species_key: '', cultivar_key: null, quantity: 1, id_prefix: '', spacing_cm: null, notes: null }],
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
        entries: [{ species_key: '', cultivar_key: null, quantity: 1, id_prefix: '', spacing_cm: null, notes: null }],
      });
      setAdoptMode(false);
      setSelectedPlants(new Set());
      setPlantSearch('');
      setPlantsError(null);
      speciesApi.listSpecies(0, 200).then((r) => setSpeciesList(r.items)).catch(() => {});
      sitesApi.listSites(0, 200).then(setSitesList).catch(() => {});
    }
  }, [open, reset]);

  useEffect(() => {
    if (!siteKey) {
      setValue('location_key', null);
    }
  }, [siteKey, setValue]);

  useEffect(() => {
    if (adoptMode) {
      // Clear entries so zod validation doesn't block on empty species_key/id_prefix
      setValue('entries', []);
      setPlantsLoading(true);
      setPlantsError(null);
      plantApi
        .listPlantInstances(0, 200)
        .then((allPlants) => {
          setAvailablePlants(allPlants.filter((p) => !p.removed_on));
        })
        .catch(() => {
          setAvailablePlants([]);
          setPlantsError(t('common.loadingError'));
        })
        .finally(() => setPlantsLoading(false));
    } else {
      // Restore default entry when switching back
      setValue('entries', [{ species_key: '', cultivar_key: null, quantity: 1, id_prefix: '', spacing_cm: null, notes: null }]);
    }
  }, [adoptMode, t, setValue]);

  const filteredPlants = useMemo(() => {
    if (!plantSearch.trim()) return availablePlants;
    const lower = plantSearch.toLowerCase();
    return availablePlants.filter(
      (p) =>
        p.instance_id.toLowerCase().includes(lower) ||
        (p.plant_name ?? '').toLowerCase().includes(lower) ||
        p.current_phase.toLowerCase().includes(lower),
    );
  }, [availablePlants, plantSearch]);

  const handleTogglePlant = (key: string) => {
    setSelectedPlants((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const handleSelectAllPlants = () => {
    if (selectedPlants.size === filteredPlants.length) {
      setSelectedPlants(new Set());
    } else {
      setSelectedPlants(new Set(filteredPlants.map((p) => p.key)));
    }
  };

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      const created = await runApi.createPlantingRun({
        name: data.name,
        run_type: data.run_type,
        location_key: data.location_key || undefined,
        substrate_batch_key: data.substrate_batch_key || undefined,
        planned_start_date: data.planned_start_date || undefined,
        source_plant_key: data.source_plant_key || undefined,
        notes: data.notes || undefined,
        entries: adoptMode
          ? undefined
          : data.entries.map((e) => ({
              species_key: e.species_key,
              cultivar_key: e.cultivar_key || undefined,
              quantity: e.quantity,
              id_prefix: e.id_prefix,
              spacing_cm: e.spacing_cm ?? undefined,
              notes: e.notes || undefined,
            })),
      });

      if (adoptMode && created.key && selectedPlants.size > 0) {
        const result = await runApi.adoptPlants(created.key, Array.from(selectedPlants));
        notification.success(
          t('pages.plantingRuns.plantsAdopted', { count: result.adopted_count }),
        );
      } else {
        notification.success(t('common.create'));
      }

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
  ];

  const fc = plantingRunFieldConfig;

  return (
    <Dialog fullScreen={fullScreen} open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>{t('pages.plantingRuns.create')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.plantingRuns.sectionBasics')}
          </Typography>
          <FormTextField name="name" control={control} label={t('pages.plantingRuns.name')} required />
          <FormDateField
            name="planned_start_date"
            control={control}
            label={t('pages.plantingRuns.plannedStartDate')}
          />

          <ExpertiseFieldWrapper minLevel={fc.run_type.level}>
            <FormSelectField
              name="run_type"
              control={control}
              label={t('pages.plantingRuns.runType')}
              required
              options={runTypes}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.site_key.level}>
            <FormSelectField
              name="site_key"
              control={control}
              label={t('entities.site')}
              options={[
                { value: '', label: '\u2014' },
                ...sitesList.map((s) => ({ value: s.key, label: s.name })),
              ]}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.location_key.level}>
            <LocationTreeSelect
              name="location_key"
              control={control}
              siteKey={siteKey}
              label={t('pages.plantingRuns.location')}
            />
          </ExpertiseFieldWrapper>
          <ExpertiseFieldWrapper minLevel={fc.notes.level}>
            <FormTextField name="notes" control={control} label={t('pages.plantingRuns.notes')} />
          </ExpertiseFieldWrapper>

          {/* expert */}
          {!adoptMode && (
            <ExpertiseFieldWrapper minLevel={fc.substrate_batch_key.level}>
              <FormTextField
                name="substrate_batch_key"
                control={control}
                label={t('pages.plantingRuns.substrateBatch')}
              />
            </ExpertiseFieldWrapper>
          )}
          {runType === 'clone' && (
            <ExpertiseFieldWrapper minLevel={fc.source_plant_key.level}>
              <FormTextField
                name="source_plant_key"
                control={control}
                label={t('pages.plantingRuns.sourcePlantKey')}
                required
              />
            </ExpertiseFieldWrapper>
          )}

          <Divider sx={{ my: 2 }} />
          <FormControlLabel
            control={
              <Switch
                checked={adoptMode}
                onChange={(e) => setAdoptMode(e.target.checked)}
                data-testid="adopt-mode-toggle"
              />
            }
            label={t('pages.plantingRuns.adoptAfterCreate')}
          />
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2, ml: 6 }}>
            {t('pages.plantingRuns.adoptAfterCreateDesc')}
          </Typography>

          {adoptMode ? (
            <>
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                {t('pages.plantingRuns.adoptPlants')}
              </Typography>

              {plantsError && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {plantsError}
                </Alert>
              )}

              {plantsLoading ? (
                <LoadingSkeleton variant="table" />
              ) : availablePlants.length === 0 ? (
                <EmptyState message={t('pages.plantingRuns.noAvailablePlants')} />
              ) : (
                <>
                  <TextField
                    size="small"
                    fullWidth
                    placeholder={t('common.search')}
                    value={plantSearch}
                    onChange={(e) => setPlantSearch(e.target.value)}
                    sx={{ mb: 1 }}
                    slotProps={{
                      input: {
                        startAdornment: (
                          <InputAdornment position="start">
                            <SearchIcon />
                          </InputAdornment>
                        ),
                      },
                    }}
                    data-testid="adopt-search"
                  />

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Button size="small" onClick={handleSelectAllPlants} data-testid="adopt-select-all">
                      {selectedPlants.size === filteredPlants.length
                        ? t('common.deselectAll')
                        : t('common.selectAll')}
                    </Button>
                    <Typography variant="caption" color="text.secondary">
                      {t('pages.plantingRuns.selectedCount', { count: selectedPlants.size })}
                    </Typography>
                  </Box>

                  <List
                    dense
                    sx={{
                      maxHeight: 300,
                      overflow: 'auto',
                      border: 1,
                      borderColor: 'divider',
                      borderRadius: 1,
                    }}
                    data-testid="adopt-plants-list"
                  >
                    {filteredPlants.map((plant) => (
                      <ListItem key={plant.key} disablePadding>
                        <ListItemButton onClick={() => handleTogglePlant(plant.key)} dense>
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            <Checkbox
                              edge="start"
                              checked={selectedPlants.has(plant.key)}
                              tabIndex={-1}
                              disableRipple
                              slotProps={{ input: { 'aria-label': plant.instance_id } }}
                            />
                          </ListItemIcon>
                          <ListItemText
                            primary={plant.plant_name ?? plant.instance_id}
                            secondary={plant.instance_id !== (plant.plant_name ?? plant.instance_id) ? plant.instance_id : undefined}
                          />
                          <Chip
                            label={plant.current_phase}
                            size="small"
                            color="primary"
                            variant="outlined"
                            sx={{ ml: 1 }}
                          />
                        </ListItemButton>
                      </ListItem>
                    ))}
                  </List>
                </>
              )}
            </>
          ) : (
            <>
              <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                {t('pages.plantingRuns.entries')}
              </Typography>

              {fields.map((field, index) => (
                <EntryRow
                  key={field.id}
                  index={index}
                  control={control}
                  setValue={setValue}
                  speciesList={speciesList}
                  onRemove={() => remove(index)}
                  canRemove={fields.length > 1}
                />
              ))}

              <Button
                startIcon={<AddIcon />}
                onClick={() =>
                  append({ species_key: '', cultivar_key: null, quantity: 1, id_prefix: '', spacing_cm: null, notes: null })
                }
                sx={{ mb: 2 }}
              >
                {t('pages.plantingRuns.addEntry')}
              </Button>
            </>
          )}

          {level !== 'expert' && (
            <ShowAllFieldsToggle showAll={showAllOverride} onToggle={toggleShowAll} />
          )}

          <FormActions
            onCancel={handleClose}
            loading={saving}
            saveLabel={t('common.create')}
            disabled={adoptMode && selectedPlants.size === 0}
          />
        </form>
      </DialogContent>
    </Dialog>
  );
}
