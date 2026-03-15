import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormDateField from '@/components/form/FormDateField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import SubstrateSelectField from '@/components/form/SubstrateSelectField';
import LocationTreeSelect from '@/components/form/LocationTreeSelect';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as plantApi from '@/api/endpoints/plantInstances';
import * as speciesApi from '@/api/endpoints/species';
import * as phaseApi from '@/api/endpoints/phases';
import * as substrateApi from '@/api/endpoints/substrates';
import * as sitesApi from '@/api/endpoints/sites';
import type { Species, Cultivar, Substrate, SubstrateType, GrowthPhase, Site, Slot } from '@/api/types';
import { generateInstanceId } from '@/utils/idGenerator';

const schema = z.object({
  instance_id: z.string().min(1),
  species_key: z.string().min(1),
  cultivar_key: z.string().nullable(),
  plant_name: z.string().nullable(),
  planted_on: z.string().min(1),
  current_phase_key: z.string().nullable(),
  substrate_key: z.string().nullable(),
  site_key: z.string().nullable(),
  location_key: z.string().nullable(),
  slot_key: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

export interface PlantInstanceDuplicateData {
  species_key: string;
  cultivar_key: string | null;
  plant_name: string | null;
  substrate_key: string | null;
  substrate_type_override: SubstrateType | null;
  current_phase_key: string | null;
  slot_key: string | null;
}

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: (key: string) => void;
  initialSpeciesKey?: string;
  duplicateFrom?: PlantInstanceDuplicateData;
}

export default function PlantInstanceCreateDialog({ open, onClose, onCreated, initialSpeciesKey, duplicateFrom }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [speciesList, setSpeciesList] = useState<Species[]>([]);
  const [cultivarList, setCultivarList] = useState<Cultivar[]>([]);
  const [cultivarsLoading, setCultivarsLoading] = useState(false);
  const [substratesList, setSubstratesList] = useState<Substrate[]>([]);
  const [growthPhases, setGrowthPhases] = useState<GrowthPhase[]>([]);
  const [sitesList, setSitesList] = useState<Site[]>([]);
  const [slotsList, setSlotsList] = useState<Slot[]>([]);

  const { control, handleSubmit, reset, setValue, getValues } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      instance_id: '',
      species_key: '',
      cultivar_key: null,
      plant_name: null,
      planted_on: new Date().toISOString().split('T')[0],
      current_phase_key: null,
      substrate_key: null,
      site_key: null,
      location_key: null,
      slot_key: null,
    },
  });

  const speciesKey = useWatch({ control, name: 'species_key' });
  const siteKey = useWatch({ control, name: 'site_key' });
  const locationKey = useWatch({ control, name: 'location_key' });

  const effectiveSpeciesKey = duplicateFrom?.species_key ?? initialSpeciesKey ?? '';

  useEffect(() => {
    if (open) {
      const substrateVal = duplicateFrom?.substrate_key
        ? duplicateFrom.substrate_key
        : duplicateFrom?.substrate_type_override
          ? `_type_${duplicateFrom.substrate_type_override}`
          : null;
      reset({
        instance_id: generateInstanceId(''),
        species_key: effectiveSpeciesKey,
        cultivar_key: duplicateFrom?.cultivar_key ?? null,
        plant_name: duplicateFrom?.plant_name ? `${duplicateFrom.plant_name} (Kopie)` : null,
        planted_on: new Date().toISOString().split('T')[0],
        current_phase_key: duplicateFrom?.current_phase_key ?? null,
        substrate_key: substrateVal,
        site_key: null,
        location_key: null,
        slot_key: null,
      });
      substrateApi.listSubstrates(0, 200).then(setSubstratesList).catch(() => setSubstratesList([]));
      sitesApi.listSites(0, 200).then(setSitesList).catch(() => setSitesList([]));
      speciesApi.listSpecies(0, 200).then((r) => {
        setSpeciesList(r.items);
        if (effectiveSpeciesKey) {
          const species = r.items.find((s) => s.key === effectiveSpeciesKey);
          if (species) {
            setValue('instance_id', generateInstanceId(species.scientific_name));
          }
        }
      }).catch(() => {});
      // Resolve slot → location → site for duplicate
      if (duplicateFrom?.slot_key) {
        sitesApi.getSlot(duplicateFrom.slot_key).then(async (slot) => {
          const loc = await sitesApi.getLocation(slot.location_key);
          // Load slots for the location so the dropdown is populated
          const slots = await sitesApi.listSlots(loc.key).catch(() => [] as Slot[]);
          setSlotsList(slots);
          // Set values without triggering cascade resets
          skipLocationReset.current = true;
          skipSlotReset.current = true;
          setValue('site_key', loc.site_key);
          setValue('location_key', loc.key);
          setValue('slot_key', slot.key);
        }).catch(() => {});
      }
    }
  }, [open, reset, effectiveSpeciesKey, setValue, duplicateFrom]);

  useEffect(() => {
    if (speciesKey) {
      const currentId = getValues('instance_id');
      if (currentId.startsWith('PLANT-')) {
        const species = speciesList.find((s) => s.key === speciesKey);
        if (species) {
          setValue('instance_id', generateInstanceId(species.scientific_name));
        }
      }
    }
  }, [speciesKey, speciesList, getValues, setValue]);

  const [initialLoadDone, setInitialLoadDone] = useState(false);

  useEffect(() => {
    if (!open) {
      setInitialLoadDone(false);
    }
  }, [open]);

  useEffect(() => {
    if (!speciesKey) {
      setCultivarList([]);
      setGrowthPhases([]);
      return;
    }
    const isInitialDuplicate = duplicateFrom && !initialLoadDone;
    setCultivarsLoading(true);
    if (!isInitialDuplicate) {
      setValue('cultivar_key', null);
      setValue('current_phase_key', null);
    }
    speciesApi
      .listCultivars(speciesKey)
      .then((cultivars) => setCultivarList(cultivars))
      .catch(() => setCultivarList([]))
      .finally(() => setCultivarsLoading(false));

    // Load growth phases for species
    phaseApi.getLifecycleConfig(speciesKey)
      .then((lc) => phaseApi.listGrowthPhases(lc.key))
      .then((phases) => {
        setGrowthPhases(phases);
        if (!isInitialDuplicate) {
          // Auto-select first phase
          if (phases.length > 0) {
            const sorted = [...phases].sort((a, b) => a.sequence_order - b.sequence_order);
            setValue('current_phase_key', sorted[0].key);
          }
        }
        setInitialLoadDone(true);
      })
      .catch(() => { setGrowthPhases([]); setInitialLoadDone(true); });
  }, [speciesKey, setValue, duplicateFrom, initialLoadDone, open]);

  // Cascade: site → load locations (via LocationTreeSelect), location → load slots
  const skipLocationReset = useRef(false);
  const skipSlotReset = useRef(false);

  useEffect(() => {
    if (skipLocationReset.current) {
      skipLocationReset.current = false;
      return;
    }
    setValue('location_key', null);
    setSlotsList([]);
    setValue('slot_key', null);
  }, [siteKey, setValue]);

  useEffect(() => {
    if (skipSlotReset.current) {
      skipSlotReset.current = false;
      return;
    }
    setSlotsList([]);
    setValue('slot_key', null);
    if (locationKey) {
      sitesApi.listSlots(locationKey).then(setSlotsList).catch(() => setSlotsList([]));
    }
  }, [locationKey, setValue]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { substrate_key: rawSubstrateKey, site_key: _siteKey, ...rest } = data;
      // Type-only fallback keys start with '_type_' — don't send as substrate_key
      const isTypeOnly = rawSubstrateKey?.startsWith('_type_');
      const substrateKey = isTypeOnly ? null : (rawSubstrateKey || null);
      const selectedSubstrate = substrateKey ? substratesList.find((s) => s.key === substrateKey) : null;
      const typeOverride = isTypeOnly
        ? rawSubstrateKey!.replace('_type_', '') as SubstrateType
        : (selectedSubstrate?.type ?? null);
      const result = await plantApi.createPlantInstance({
        ...rest,
        location_key: rest.location_key || null,
        slot_key: rest.slot_key || null,
        substrate_key: substrateKey,
        substrate_type_override: typeOverride,
      });
      notification.success(t('common.create'));
      reset();
      onCreated(result.key);
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{duplicateFrom ? t('pages.plantInstances.duplicateTitle') : t('pages.plantInstances.create')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          {/* Identification */}
          <FormSelectField
            name="species_key"
            control={control}
            label={t('entities.species')}
            required
            disabled={!!initialSpeciesKey || !!duplicateFrom}
            options={speciesList.map((s) => ({ value: s.key, label: s.scientific_name }))}
          />
          <FormRow>
            <FormSelectField
              name="cultivar_key"
              control={control}
              label={t('pages.plantInstances.cultivarKey')}
              helperText={t('pages.plantInstances.cultivarKeyHelper')}
              disabled={!speciesKey || cultivarsLoading}
              options={[
                { value: '', label: '\u2014' },
                ...cultivarList.map((c) => ({ value: c.key, label: c.name })),
              ]}
            />
            <FormTextField
              name="plant_name"
              control={control}
              label={t('pages.plantInstances.plantName')}
              helperText={t('pages.plantInstances.plantNameHelper')}
            />
          </FormRow>

          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.plantInstances.sectionSetup')}
          </Typography>

          <FormRow>
            <FormDateField name="planted_on" control={control} label={t('pages.plantInstances.plantedOn')} required />
            <FormSelectField
              name="current_phase_key"
              control={control}
              label={t('pages.plantInstances.currentPhase')}
              disabled={growthPhases.length === 0}
              options={growthPhases
                .sort((a, b) => a.sequence_order - b.sequence_order)
                .map((gp) => ({
                  value: gp.key,
                  label: gp.display_name || t(`enums.phaseName.${gp.name}`, { defaultValue: gp.name }),
                }))}
            />
          </FormRow>
          <FormTextField name="instance_id" control={control} label={t('pages.plantInstances.instanceId')} required helperText={t('pages.plantInstances.instanceIdHelper')} />
          <SubstrateSelectField
            name="substrate_key"
            control={control}
            label={t('pages.plantInstances.substrate')}
            helperText={t('pages.plantInstances.substrateHelper')}
            substrates={substratesList}
          />

          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.plantInstances.sectionLocation')}
          </Typography>
          <FormRow>
            <FormSelectField
              name="site_key"
              control={control}
              label={t('entities.site')}
              helperText={t('pages.plantInstances.siteHelper')}
              options={[
                { value: '', label: '\u2014' },
                ...sitesList.map((s) => ({ value: s.key, label: s.name })),
              ]}
            />
            <LocationTreeSelect
              name="location_key"
              control={control}
              siteKey={siteKey}
              label={t('entities.location')}
            />
          </FormRow>
          <FormSelectField
            name="slot_key"
            control={control}
            label={t('entities.slot')}
            helperText={t('pages.plantInstances.slotHelper')}
            disabled={slotsList.length === 0}
            options={[
              { value: '', label: '\u2014' },
              ...slotsList.map((s) => ({
                value: s.key,
                label: s.currently_occupied
                  ? `${s.slot_id} (${t('pages.plantInstances.slotOccupied')})`
                  : s.slot_id,
              })),
            ]}
          />
          <FormActions onCancel={onClose} loading={saving} saveLabel={t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
