import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Typography from '@mui/material/Typography';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Form from '@/components/form/Form';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormTextField from '@/components/form/FormTextField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as harvestApi from '@/api/endpoints/harvest';
import { startDrying } from '@/api/endpoints/postHarvest';
import type { HarvestBatch } from '@/api/types';

const speciesTypes = ['flower', 'herb', 'root', 'fruit', 'mushroom'] as const;
const dryingMethods = ['hang_dry', 'rack_dry', 'dehydrator', 'air_cure'] as const;

const schema = z.object({
  harvest_batch_key: z.string().min(1),
  species_type: z.enum(speciesTypes),
  drying_method: z.enum(dryingMethods),
  start_weight_g: z.number().min(0).nullable(),
  target_moisture_percent: z.number().min(5).max(15),
  notes: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function StartDryingDialog({ open, onClose, onCreated }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [batches, setBatches] = useState<HarvestBatch[]>([]);
  const [loadingBatches, setLoadingBatches] = useState(false);

  const defaults: FormData = {
    harvest_batch_key: '',
    species_type: 'flower',
    drying_method: 'hang_dry',
    start_weight_g: null,
    target_moisture_percent: 10,
    notes: null,
  };

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: defaults,
  });

  useEffect(() => {
    if (open) {
      reset(defaults);
      setLoadingBatches(true);
      harvestApi
        .getBatches()
        .then(setBatches)
        .catch(() => setBatches([]))
        .finally(() => setLoadingBatches(false));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, reset]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await startDrying({
        harvest_batch_key: data.harvest_batch_key,
        species_type: data.species_type,
        drying_method: data.drying_method,
        start_weight_g: data.start_weight_g,
        target_moisture_percent: data.target_moisture_percent,
        notes: data.notes,
      });
      notification.success(t('pages.postHarvest.startDryingSuccess'));
      reset(defaults);
      onCreated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="start-drying-dialog-title"
      data-testid="start-drying-dialog"
    >
      <DialogTitle id="start-drying-dialog-title">
        {t('pages.postHarvest.startDrying')}
      </DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.postHarvest.startDryingIntro')}
        </Typography>
        <Form onSubmit={handleSubmit(onSubmit)}>
          <FormSelectField
            name="harvest_batch_key"
            control={control}
            label={t('pages.postHarvest.harvestBatch')}
            required
            disabled={loadingBatches || batches.length === 0}
            helperText={
              !loadingBatches && batches.length === 0
                ? t('pages.postHarvest.noHarvestBatches')
                : t('pages.postHarvest.harvestBatchHelper')
            }
            options={batches.map((b) => ({
              value: b.key,
              label: b.batch_id || b.key,
            }))}
          />
          <FormSelectField
            name="species_type"
            control={control}
            label={t('pages.postHarvest.speciesType')}
            required
            helperText={t('pages.postHarvest.speciesTypeHelper')}
            options={speciesTypes.map((v) => ({
              value: v,
              label: t(`enums.postHarvestSpeciesType.${v}`),
            }))}
          />
          <FormSelectField
            name="drying_method"
            control={control}
            label={t('pages.postHarvest.dryingMethod')}
            required
            helperText={t('pages.postHarvest.dryingMethodHelper')}
            options={dryingMethods.map((v) => ({
              value: v,
              label: t(`enums.dryingMethod.${v}`),
            }))}
          />
          <FormNumberField
            name="start_weight_g"
            control={control}
            label={t('pages.postHarvest.startWeightG')}
            min={0}
            inputMode="decimal"
            suffix="g"
            helperText={t('pages.postHarvest.startWeightHelper')}
          />
          <FormNumberField
            name="target_moisture_percent"
            control={control}
            label={t('pages.postHarvest.targetMoisturePercent')}
            min={5}
            max={15}
            suffix="%"
            helperText={t('pages.postHarvest.targetMoistureHelper')}
          />
          <FormTextField
            name="notes"
            control={control}
            label={t('pages.postHarvest.notes')}
            multiline
            rows={3}
          />
          <FormActions
            onCancel={onClose}
            loading={saving}
            saveLabel={t('pages.postHarvest.startDrying')}
          />
        </Form>
      </DialogContent>
    </Dialog>
  );
}
