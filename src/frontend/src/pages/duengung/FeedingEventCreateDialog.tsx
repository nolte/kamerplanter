import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/feeding-events';

const applicationMethods = ['fertigation', 'drench', 'foliar', 'top_dress'] as const;

const fertilizerLineSchema = z.object({
  fertilizer_key: z.string().min(1),
  ml_applied: z.number().gt(0),
});

const schema = z.object({
  plant_key: z.string().min(1),
  application_method: z.enum(applicationMethods),
  is_supplemental: z.boolean(),
  volume_applied_liters: z.number().gt(0),
  measured_ec_before: z.number().min(0).nullable(),
  measured_ec_after: z.number().min(0).nullable(),
  measured_ph_before: z.number().min(0).max(14).nullable(),
  measured_ph_after: z.number().min(0).max(14).nullable(),
  runoff_ec: z.number().min(0).nullable(),
  runoff_ph: z.number().min(0).max(14).nullable(),
  runoff_volume_liters: z.number().min(0).nullable(),
  fertilizers_used: z.array(fertilizerLineSchema),
  notes: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
  plantKey?: string;
}

export default function FeedingEventCreateDialog({
  open,
  onClose,
  onCreated,
  plantKey,
}: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      plant_key: plantKey ?? '',
      application_method: 'fertigation',
      is_supplemental: false,
      volume_applied_liters: 1,
      measured_ec_before: null,
      measured_ec_after: null,
      measured_ph_before: null,
      measured_ph_after: null,
      runoff_ec: null,
      runoff_ph: null,
      runoff_volume_liters: null,
      fertilizers_used: [],
      notes: null,
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'fertilizers_used',
  });

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await api.createFeedingEvent(data);
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
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('pages.feedingEvents.create')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField
            name="plant_key"
            control={control}
            label={t('pages.feedingEvents.plantKey')}
            required
            disabled={!!plantKey}
          />
          <FormSelectField
            name="application_method"
            control={control}
            label={t('pages.feedingEvents.applicationMethod')}
            options={applicationMethods.map((v) => ({
              value: v,
              label: t(`enums.applicationMethod.${v}`),
            }))}
          />
          <FormSwitchField
            name="is_supplemental"
            control={control}
            label={t('pages.feedingEvents.isSupplemental')}
          />
          <FormNumberField
            name="volume_applied_liters"
            control={control}
            label={t('pages.feedingEvents.volumeApplied')}
            min={0.01}
          />
          <FormNumberField
            name="measured_ec_before"
            control={control}
            label={t('pages.feedingEvents.ecBefore')}
            min={0}
          />
          <FormNumberField
            name="measured_ec_after"
            control={control}
            label={t('pages.feedingEvents.ecAfter')}
            min={0}
          />
          <FormNumberField
            name="measured_ph_before"
            control={control}
            label={t('pages.feedingEvents.phBefore')}
            min={0}
            max={14}
          />
          <FormNumberField
            name="measured_ph_after"
            control={control}
            label={t('pages.feedingEvents.phAfter')}
            min={0}
            max={14}
          />
          <FormNumberField
            name="runoff_ec"
            control={control}
            label={t('pages.feedingEvents.runoffEc')}
            min={0}
          />
          <FormNumberField
            name="runoff_ph"
            control={control}
            label={t('pages.feedingEvents.runoffPh')}
            min={0}
            max={14}
          />
          <FormNumberField
            name="runoff_volume_liters"
            control={control}
            label={t('pages.feedingEvents.runoffVolume')}
            min={0}
          />

          <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
            {t('pages.feedingEvents.fertilizersUsed')}
          </Typography>
          {fields.map((field, index) => (
            <Box
              key={field.id}
              sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}
            >
              <FormTextField
                name={`fertilizers_used.${index}.fertilizer_key`}
                control={control}
                label={t('pages.feedingEvents.fertilizerKey')}
                required
              />
              <FormNumberField
                name={`fertilizers_used.${index}.ml_applied`}
                control={control}
                label={t('pages.feedingEvents.mlApplied')}
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
            onClick={() => append({ fertilizer_key: '', ml_applied: 1 })}
            sx={{ mb: 2 }}
          >
            {t('pages.feedingEvents.addFertilizer')}
          </Button>

          <FormTextField
            name="notes"
            control={control}
            label={t('pages.feedingEvents.notes')}
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
