import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormTextField from '@/components/form/FormTextField';
import FormChipInput from '@/components/form/FormChipInput';
import FormRow from '@/components/form/FormRow';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import SpeciesAutocompleteField from '@/components/form/SpeciesAutocompleteField';
import HelpTooltip from '@/components/common/HelpTooltip';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/propagation';
import * as speciesApi from '@/api/endpoints/species';
import type { PropagationEventMethod, Species } from '@/api/types';

const methods: PropagationEventMethod[] = [
  'seed',
  'cutting',
  'clone',
  'graft',
  'division',
  'layering',
  'offset',
  'other',
];

const schema = z.object({
  method: z.enum([
    'seed',
    'cutting',
    'clone',
    'graft',
    'division',
    'layering',
    'offset',
    'other',
  ]),
  quantity: z.number().int().min(1).max(1000),
  parent_plant_keys: z.array(z.string()),
  child_plant_keys: z.array(z.string()),
  species_key: z.string(),
  notes: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function PropagationEventDialog({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { handleError } = useApiError();

  const [speciesList, setSpeciesList] = useState<Species[]>([]);
  const [speciesLoading, setSpeciesLoading] = useState(false);

  const defaults: FormData = {
    method: 'cutting',
    quantity: 1,
    parent_plant_keys: [],
    child_plant_keys: [],
    species_key: '',
    notes: null,
  };

  const {
    control,
    handleSubmit,
    reset,
    setError,
    formState: { isDirty, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema), defaultValues: defaults });

  const method = useWatch({ control, name: 'method' });
  const isGraft = method === 'graft';
  const isCutting = method === 'cutting';

  // Species options are fetched once per dialog opening — small, global reference
  // data that changes rarely, so a single page is a pragmatic MVP fetch (mirrors
  // PlantInstanceCreateDialog's pattern). The async loader is declared *inside*
  // the effect body (mirroring `useAquaponicSystems`), so `setState` is never
  // called synchronously at the top level of the effect callback — this keeps
  // `react-hooks/set-state-in-effect` clean without adding an eslint-disable.
  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    const load = async () => {
      setSpeciesLoading(true);
      try {
        const r = await speciesApi.listSpecies(0, 200);
        if (!cancelled) setSpeciesList(r.items);
      } catch {
        if (!cancelled) setSpeciesList([]);
      } finally {
        if (!cancelled) setSpeciesLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [open]);

  const onSubmit = async (data: FormData) => {
    try {
      await api.createPropagationEvent({
        method: data.method,
        quantity: data.quantity,
        parent_plant_keys: data.parent_plant_keys,
        child_plant_keys: data.child_plant_keys,
        species_key: data.species_key.trim() || null,
        notes: data.notes,
      });
      reset(defaults);
      onCreated();
    } catch (error) {
      handleError(error, (name, message) => setError(name as keyof FormData, { message }));
    }
  };

  const handleClose = () => {
    reset(defaults);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} fullScreen={fullScreen} fullWidth maxWidth="sm">
      <DialogTitle>{t('pages.propagation.createEvent')}</DialogTitle>
      <DialogContent>
        <UnsavedChangesGuard dirty={isDirty} />
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
            <Typography variant="subtitle2">
              {t('pages.propagation.fields.sectionWhat')}
            </Typography>
            <HelpTooltip term="vermehrung" iconOnly />
            {isCutting && <HelpTooltip term="steckling" iconOnly />}
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
            {t('pages.propagation.fields.sectionWhatIntro')}
          </Typography>
          <FormRow>
            <FormSelectField
              name="method"
              control={control}
              label={t('pages.propagation.fields.method')}
              required
              autoFocus
              options={methods.map((v) => ({
                value: v,
                label: t(`enums.propagationEventMethod.${v}`),
              }))}
            />
            <FormNumberField
              name="quantity"
              control={control}
              label={t('pages.propagation.fields.quantity')}
              min={1}
              max={1000}
              step={1}
              required
            />
          </FormRow>
          <SpeciesAutocompleteField
            name="species_key"
            control={control}
            label={t('pages.propagation.fields.speciesKey')}
            species={speciesList}
            disabled={speciesLoading}
            helperText={
              speciesLoading
                ? t('pages.propagation.fields.speciesLoading')
                : t('pages.propagation.fields.speciesKeyHelper')
            }
          />

          <Divider sx={{ my: 2 }} />

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
            <Typography variant="subtitle2">
              {t('pages.propagation.fields.sectionPlants')}
            </Typography>
            {isGraft && <HelpTooltip term="veredelung" iconOnly />}
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
            {t('pages.propagation.fields.sectionPlantsIntro')}
          </Typography>
          <FormChipInput
            name="parent_plant_keys"
            control={control}
            label={
              isGraft
                ? t('pages.propagation.fields.parentKeysGraft')
                : t('pages.propagation.fields.parentKeys')
            }
            helperText={t('pages.propagation.fields.keysHelper')}
          />
          <FormChipInput
            name="child_plant_keys"
            control={control}
            label={
              isGraft
                ? t('pages.propagation.fields.childKeysGraft')
                : t('pages.propagation.fields.childKeys')
            }
            helperText={t('pages.propagation.fields.keysHelper')}
          />
          <FormTextField
            name="notes"
            control={control}
            label={t('pages.propagation.fields.notes')}
            multiline
            minRows={2}
          />
          <FormActions onCancel={handleClose} loading={isSubmitting} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
