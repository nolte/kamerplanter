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
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as harvestApi from '@/api/endpoints/harvest';
import type { HarvestIndicator } from '@/api/types';

const ripenessStages = [
  'immature',
  'approaching',
  'peak',
  'overripe',
] as const;

const schema = z.object({
  indicator_key: z.string().min(1),
  observer: z.string().max(200),
  ripeness_assessment: z.enum(ripenessStages),
  days_to_harvest_estimate: z.number().min(0).nullable(),
  notes: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  plantKey: string;
  onCreated: () => void;
}

export default function ObservationCreateDialog({
  open,
  onClose,
  plantKey,
  onCreated,
}: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [indicators, setIndicators] = useState<HarvestIndicator[]>([]);
  const [loadingIndicators, setLoadingIndicators] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      indicator_key: '',
      observer: '',
      ripeness_assessment: 'immature',
      days_to_harvest_estimate: null,
      notes: null,
    },
  });

  useEffect(() => {
    if (open) {
      setLoadingIndicators(true);
      harvestApi
        .getIndicators()
        .then(setIndicators)
        .catch(() => setIndicators([]))
        .finally(() => setLoadingIndicators(false));

      reset({
        indicator_key: '',
        observer: '',
        ripeness_assessment: 'immature',
        days_to_harvest_estimate: null,
        notes: null,
      });
    }
  }, [open, reset]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await harvestApi.createObservation(plantKey, {
        indicator_key: data.indicator_key,
        observer: data.observer || undefined,
        ripeness_assessment: data.ripeness_assessment,
        days_to_harvest_estimate: data.days_to_harvest_estimate,
        notes: data.notes,
      });
      notification.success(t('pages.harvest.observationCreated'));
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
      <DialogTitle>{t('pages.harvest.createObservation')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.harvest.createObservationIntro')}
        </Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormSelectField
            name="indicator_key"
            control={control}
            label={t('pages.harvest.indicator')}
            required
            autoFocus
            disabled={loadingIndicators}
            options={indicators.map((i) => ({
              value: i.key,
              label: `${t(`enums.harvestIndicatorType.${i.indicator_type}`)} (${i.measurement_unit || '\u2014'})`,
            }))}
          />
          <FormTextField
            name="observer"
            control={control}
            label={t('pages.harvest.observer')}
          />
          <FormSelectField
            name="ripeness_assessment"
            control={control}
            label={t('pages.harvest.ripenessAssessment')}
            options={ripenessStages.map((v) => ({
              value: v,
              label: t(`enums.ripenessStage.${v}`),
            }))}
          />
          <FormNumberField
            name="days_to_harvest_estimate"
            control={control}
            label={t('pages.harvest.daysToHarvestEstimate')}
            min={0}
            inputMode="numeric"
            suffix={t('pages.harvest.days')}
            helperText={t('pages.harvest.daysToHarvestHelper')}
          />
          <FormTextField
            name="notes"
            control={control}
            label={t('pages.harvest.notes')}
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
