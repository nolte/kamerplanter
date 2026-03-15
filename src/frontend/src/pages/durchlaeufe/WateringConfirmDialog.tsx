import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Alert from '@mui/material/Alert';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormNumberField from '@/components/form/FormNumberField';
import FormRow from '@/components/form/FormRow';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { confirmWatering } from '@/api/endpoints/wateringConfirm';
import type { WateringConfirmResponse } from '@/api/types';

const schema = z.object({
  measured_ec: z.number().min(0).max(20).nullable(),
  measured_ph: z.number().min(0).max(14).nullable(),
  volume_liters: z.number().min(0).max(10000).nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  runKey: string;
  taskKey: string;
  channelId?: string;
  onConfirmed: () => void;
  /** Pre-calculated suggested volume in liters. */
  suggestedVolumeLiters?: number;
  /** Human-readable explanation of how the volume was calculated. */
  volumeHint?: string;
}

export default function WateringConfirmDialog({
  open,
  onClose,
  runKey,
  taskKey,
  channelId,
  onConfirmed,
  suggestedVolumeLiters,
  volumeHint,
}: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<WateringConfirmResponse | null>(null);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      measured_ec: null,
      measured_ph: null,
      volume_liters: suggestedVolumeLiters ?? null,
    },
  });

  // Reset form with suggested volume when dialog opens
  useEffect(() => {
    if (open) {
      reset({
        measured_ec: null,
        measured_ph: null,
        volume_liters: suggestedVolumeLiters ?? null,
      });
      setResult(null);
    }
  }, [open, suggestedVolumeLiters, reset]);

  const handleClose = () => {
    reset();
    setResult(null);
    onClose();
  };

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      const response = await confirmWatering({
        run_key: runKey,
        task_key: taskKey,
        channel_id: channelId,
        measured_ec: data.measured_ec ?? undefined,
        measured_ph: data.measured_ph ?? undefined,
        volume_liters: data.volume_liters ?? undefined,
      });
      setResult(response);
      notification.success(t('pages.wateringSchedule.confirm'));
      onConfirmed();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      data-testid="watering-confirm-dialog"
    >
      <DialogTitle>{t('pages.wateringSchedule.confirm')}</DialogTitle>
      <DialogContent>
        {result ? (
          <Box sx={{ py: 2 }}>
            <Alert severity="success" sx={{ mb: 2 }}>
              {t('pages.wateringSchedule.feedingEventsCreated', {
                count: result.feeding_events_created,
              })}
            </Alert>
            <Typography variant="body2" color="text.secondary">
              {t('pages.wateringSchedule.wateringEventKey')}: {result.watering_event_key}
            </Typography>
            {result.warnings.length > 0 && (
              <Box sx={{ mt: 2 }}>
                {result.warnings.map((warning, index) => (
                  <Alert key={index} severity="warning" sx={{ mb: 0.5 }}>
                    {JSON.stringify(warning)}
                  </Alert>
                ))}
              </Box>
            )}
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <FormActions
                onCancel={handleClose}
                saveLabel={t('common.close')}
                loading={false}
              />
            </Box>
          </Box>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.wateringSchedule.confirmDescription')}
            </Typography>
            <FormRow>
              <FormNumberField
                name="measured_ec"
                control={control}
                label={t('pages.wateringSchedule.measuredEc')}
                min={0}
                max={20}
                helperText={t('pages.wateringSchedule.measuredEcHelper')}
                suffix="mS/cm"
              />
              <FormNumberField
                name="measured_ph"
                control={control}
                label={t('pages.wateringSchedule.measuredPh')}
                min={0}
                max={14}
                helperText={t('pages.wateringSchedule.measuredPhHelper')}
              />
            </FormRow>
            <FormNumberField
              name="volume_liters"
              control={control}
              label={t('pages.wateringSchedule.volumeLiters')}
              min={0}
              max={10000}
              helperText={volumeHint ?? t('common.optional')}
              suffix="L"
            />
            <FormActions
              onCancel={handleClose}
              loading={saving}
              saveLabel={t('pages.wateringSchedule.confirm')}
            />
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
