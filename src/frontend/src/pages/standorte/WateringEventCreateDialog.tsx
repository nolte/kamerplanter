import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormRow from '@/components/form/FormRow';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/watering-events';
import { useWateringVolumeSuggestion } from '@/hooks/useWateringVolumeSuggestion';

const applicationMethods = ['fertigation', 'drench', 'foliar', 'top_dress'] as const;
const waterSources = ['tank', 'tap', 'osmose', 'rainwater', 'distilled', 'well'] as const;

const fertilizerLineSchema = z.object({
  product_name: z.string().min(1),
  ml_per_liter: z.number().gt(0),
});

const schema = z.object({
  application_method: z.enum(applicationMethods),
  is_supplemental: z.boolean(),
  volume_liters: z.number().gt(0),
  plant_keys_input: z.string().min(1),
  water_source: z.string().nullable(),
  target_ec: z.number().min(0).nullable(),
  target_ph: z.number().min(0).max(14).nullable(),
  measured_ec: z.number().min(0).nullable(),
  measured_ph: z.number().min(0).max(14).nullable(),
  runoff_ec: z.number().min(0).nullable(),
  runoff_ph: z.number().min(0).max(14).nullable(),
  performed_by: z.string().nullable(),
  fertilizers_used: z.array(fertilizerLineSchema),
  notes: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
  plantKeys?: string[];
}

export default function WateringEventCreateDialog({
  open,
  onClose,
  onCreated,
  plantKeys,
}: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [warnings, setWarnings] = useState<Array<{ type: string; message: string }>>([]);

  // Fetch volume suggestion for the first plant
  const firstPlantKey = plantKeys?.[0];
  const { suggestion: volumeSuggestion } = useWateringVolumeSuggestion(firstPlantKey);

  const { control, handleSubmit, reset, setValue } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      application_method: 'drench',
      is_supplemental: false,
      volume_liters: 1,
      plant_keys_input: plantKeys?.join(', ') ?? '',
      water_source: null,
      target_ec: null,
      target_ph: null,
      measured_ec: null,
      measured_ph: null,
      runoff_ec: null,
      runoff_ph: null,
      performed_by: null,
      fertilizers_used: [],
      notes: null,
    },
  });

  // Pre-fill suggested volume when it becomes available
  useEffect(() => {
    if (volumeSuggestion) {
      setValue('volume_liters', volumeSuggestion.liters);
    }
  }, [volumeSuggestion, setValue]);

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'fertilizers_used',
  });

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      setWarnings([]);
      const plantKeysArray = data.plant_keys_input
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      const result = await api.createWateringEvent({
        application_method: data.application_method,
        is_supplemental: data.is_supplemental,
        volume_liters: data.volume_liters,
        plant_keys: plantKeysArray,
        water_source: data.water_source as 'tank' | 'tap' | 'osmose' | 'rainwater' | 'distilled' | 'well' | null | undefined,
        target_ec: data.target_ec,
        target_ph: data.target_ph,
        measured_ec: data.measured_ec,
        measured_ph: data.measured_ph,
        runoff_ec: data.runoff_ec,
        runoff_ph: data.runoff_ph,
        performed_by: data.performed_by,
        fertilizers_used: data.fertilizers_used.map((f) => ({
          ...f,
          product_key: null,
        })),
        notes: data.notes,
      });
      if (result.warnings.length > 0) {
        setWarnings(result.warnings);
      }
      notification.success(t('common.create'));
      reset();
      onCreated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog fullScreen={fullScreen} open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('pages.wateringEvents.create')}</DialogTitle>
      <DialogContent>
        {warnings.map((w, i) => (
          <Alert key={i} severity="warning" sx={{ mb: 1 }}>
            {w.message}
          </Alert>
        ))}
        <form onSubmit={handleSubmit(onSubmit)}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.wateringEvents.sectionBasics')}
          </Typography>
          <FormTextField
            name="plant_keys_input"
            control={control}
            label={t('pages.wateringEvents.plantKeys')}
            helperText={t('pages.wateringEvents.plantKeysHelper')}
            required
            disabled={!!plantKeys}
          />
          <FormSelectField
            name="application_method"
            control={control}
            label={t('pages.wateringEvents.applicationMethod')}
            options={applicationMethods.map((v) => ({
              value: v,
              label: t(`enums.applicationMethod.${v}`),
            }))}
          />
          <FormSwitchField
            name="is_supplemental"
            control={control}
            label={t('pages.wateringEvents.isSupplemental')}
          />
          <FormNumberField
            name="volume_liters"
            control={control}
            label={t('pages.wateringEvents.volumeLiters')}
            helperText={volumeSuggestion?.hint ?? t('pages.wateringEvents.volumeLitersHelper')}
            min={0.01}
          />
          <FormSelectField
            name="water_source"
            control={control}
            label={t('pages.wateringEvents.waterSource')}
            options={waterSources.map((v) => ({
              value: v,
              label: t(`enums.waterSource.${v}`),
            }))}
          />
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.wateringEvents.sectionTarget')}
          </Typography>
          <FormRow>
            <FormNumberField
              name="target_ec"
              control={control}
              label={t('pages.wateringEvents.targetEc')}
              helperText={t('pages.wateringEvents.targetEcHelper')}
              min={0}
              inputMode="decimal"
            />
            <FormNumberField
              name="target_ph"
              control={control}
              label={t('pages.wateringEvents.targetPh')}
              helperText={t('pages.wateringEvents.targetPhHelper')}
              min={0}
              max={14}
              inputMode="decimal"
            />
          </FormRow>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.wateringEvents.sectionMeasured')}
          </Typography>
          <FormRow>
            <FormNumberField
              name="measured_ec"
              control={control}
              label={t('pages.wateringEvents.measuredEc')}
              min={0}
              inputMode="decimal"
            />
            <FormNumberField
              name="measured_ph"
              control={control}
              label={t('pages.wateringEvents.measuredPh')}
              min={0}
              max={14}
              inputMode="decimal"
            />
          </FormRow>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.wateringEvents.sectionRunoff')}
          </Typography>
          <FormRow>
            <FormNumberField
              name="runoff_ec"
              control={control}
              label={t('pages.wateringEvents.runoffEc')}
              helperText={t('pages.wateringEvents.runoffEcHelper')}
              min={0}
              inputMode="decimal"
            />
            <FormNumberField
              name="runoff_ph"
              control={control}
              label={t('pages.wateringEvents.runoffPh')}
              min={0}
              max={14}
              inputMode="decimal"
            />
          </FormRow>
          <FormTextField
            name="performed_by"
            control={control}
            label={t('pages.wateringEvents.performedBy')}
          />

          <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2, mb: 1 }}>
            {t('pages.wateringEvents.fertilizersUsed')}
          </Typography>
          {fields.map((field, index) => (
            <Box
              key={field.id}
              sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}
            >
              <FormTextField
                name={`fertilizers_used.${index}.product_name`}
                control={control}
                label={t('pages.wateringEvents.productName')}
                required
              />
              <FormNumberField
                name={`fertilizers_used.${index}.ml_per_liter`}
                control={control}
                label={t('pages.wateringEvents.mlPerLiter')}
                min={0.01}
              />
              <IconButton onClick={() => remove(index)} sx={{ mt: 1 }}>
                <DeleteIcon />
              </IconButton>
            </Box>
          ))}
          <Button
            size="small"
            startIcon={<AddIcon />}
            onClick={() => append({ product_name: '', ml_per_liter: 1 })}
            sx={{ mb: 2 }}
          >
            {t('pages.feedingEvents.addFertilizer')}
          </Button>

          <FormTextField
            name="notes"
            control={control}
            label={t('pages.wateringEvents.notes')}
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
