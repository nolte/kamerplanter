import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Typography from '@mui/material/Typography';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/tanks';

const schema = z.object({
  ph: z.number().min(0).max(14).nullable(),
  ec_ms: z.number().min(0).nullable(),
  water_temp_celsius: z.number().min(0).max(50).nullable(),
  fill_level_percent: z.number().min(0).max(100).nullable(),
  fill_level_liters: z.number().min(0).nullable(),
  tds_ppm: z.number().min(0).nullable(),
  dissolved_oxygen_mgl: z.number().min(0).max(20).nullable(),
  orp_mv: z.number().min(-500).max(1000).nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  tankKey: string;
  onCreated: () => void;
}

export default function TankStateCreateDialog({ open, onClose, tankKey, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      ph: null,
      ec_ms: null,
      water_temp_celsius: null,
      fill_level_percent: null,
      fill_level_liters: null,
      tds_ppm: null,
      dissolved_oxygen_mgl: null,
      orp_mv: null,
    },
  });

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await api.recordState(tankKey, {
        ph: data.ph,
        ec_ms: data.ec_ms,
        water_temp_celsius: data.water_temp_celsius,
        fill_level_percent: data.fill_level_percent,
        fill_level_liters: data.fill_level_liters,
        tds_ppm: data.tds_ppm,
        dissolved_oxygen_mgl: data.dissolved_oxygen_mgl,
        orp_mv: data.orp_mv != null ? Math.round(data.orp_mv) : null,
        source: 'manual',
      });
      notification.success(t('pages.tanks.stateRecorded'));
      reset();
      onCreated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      data-testid="tank-state-create-dialog"
    >
      <DialogTitle>{t('pages.tanks.recordState')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.tanks.sectionWaterQuality')}
          </Typography>
          <FormRow>
            <FormNumberField
              name="ph"
              control={control}
              label="pH"
              helperText={t('pages.tanks.phHelper')}
              min={0}
              max={14}
              inputMode="decimal"
              autoFocus
            />
            <FormNumberField
              name="ec_ms"
              control={control}
              label="EC"
              helperText={t('pages.tanks.ecHelper')}
              suffix="mS/cm"
              inputMode="decimal"
              min={0}
            />
          </FormRow>
          <FormRow>
            <FormNumberField
              name="tds_ppm"
              control={control}
              label="TDS"
              helperText={t('pages.tanks.tdsHelper')}
              suffix="ppm"
              inputMode="numeric"
              min={0}
            />
            <FormNumberField
              name="water_temp_celsius"
              control={control}
              label={t('pages.tanks.waterTempShort')}
              helperText={t('pages.tanks.waterTempHelper')}
              suffix="°C"
              inputMode="decimal"
              min={0}
              max={50}
            />
          </FormRow>

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 1 }}>
            {t('pages.tanks.sectionFillLevel')}
          </Typography>
          <FormRow>
            <FormNumberField
              name="fill_level_percent"
              control={control}
              label={t('pages.tanks.fillLevelPercent')}
              helperText={t('pages.tanks.fillLevelPercentHelper')}
              suffix="%"
              inputMode="numeric"
              min={0}
              max={100}
            />
            <FormNumberField
              name="fill_level_liters"
              control={control}
              label={t('pages.tanks.fillLevelLiters')}
              suffix="L"
              inputMode="decimal"
              min={0}
            />
          </FormRow>

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 1 }}>
            {t('pages.tanks.sectionAdvanced')}
          </Typography>
          <FormRow>
            <FormNumberField
              name="dissolved_oxygen_mgl"
              control={control}
              label={t('pages.tanks.dissolvedOxygenShort')}
              helperText={t('pages.tanks.dissolvedOxygenHelper')}
              suffix="mg/L"
              inputMode="decimal"
              min={0}
              max={20}
            />
            <FormNumberField
              name="orp_mv"
              control={control}
              label="ORP"
              helperText={t('pages.tanks.orpHelper')}
              suffix="mV"
              inputMode="numeric"
              min={-500}
              max={1000}
            />
          </FormRow>
          <FormActions
            onCancel={onClose}
            loading={saving}
            saveLabel={t('pages.tanks.recordState')}
          />
        </form>
      </DialogContent>
    </Dialog>
  );
}
