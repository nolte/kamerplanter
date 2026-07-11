import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormTextField from '@/components/form/FormTextField';
import FormRow from '@/components/form/FormRow';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/propagation';
import type { PropagationEventMethod } from '@/api/types';

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

/** Comma-separated plant keys → trimmed, de-duplicated list. */
function parseKeys(raw: string): string[] {
  return Array.from(
    new Set(
      raw
        .split(',')
        .map((k) => k.trim())
        .filter(Boolean),
    ),
  );
}

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
  parent_plant_keys: z.string(),
  child_plant_keys: z.string(),
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

  const defaults: FormData = {
    method: 'cutting',
    quantity: 1,
    parent_plant_keys: '',
    child_plant_keys: '',
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

  const onSubmit = async (data: FormData) => {
    try {
      await api.createPropagationEvent({
        method: data.method,
        quantity: data.quantity,
        parent_plant_keys: parseKeys(data.parent_plant_keys),
        child_plant_keys: parseKeys(data.child_plant_keys),
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
          <FormRow>
            <FormSelectField
              name="method"
              control={control}
              label={t('pages.propagation.fields.method')}
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
          <FormTextField
            name="species_key"
            control={control}
            label={t('pages.propagation.fields.speciesKey')}
            helperText={t('pages.propagation.fields.speciesKeyHelper')}
          />
          <FormTextField
            name="parent_plant_keys"
            control={control}
            label={t('pages.propagation.fields.parentKeys')}
            helperText={t('pages.propagation.fields.keysHelper')}
          />
          <FormTextField
            name="child_plant_keys"
            control={control}
            label={t('pages.propagation.fields.childKeys')}
            helperText={t('pages.propagation.fields.keysHelper')}
          />
          <FormTextField
            name="notes"
            control={control}
            label={t('pages.propagation.fields.notes')}
            multiline
          />
          <FormActions onCancel={handleClose} loading={isSubmitting} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
