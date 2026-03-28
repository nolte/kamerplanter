import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Alert from '@mui/material/Alert';
import Typography from '@mui/material/Typography';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormNumberField from '@/components/form/FormNumberField';
import FormSelectField from '@/components/form/FormSelectField';
import FormTextField from '@/components/form/FormTextField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/tanks';
import WaterMixRecommendationBox from '@/pages/duengung/WaterMixRecommendationBox';

const fillTypes = ['full_change', 'top_up', 'adjustment'] as const;
const waterSources = ['tap', 'osmose', 'mixed', 'rainwater', 'distilled', 'well'] as const;

const schema = z.object({
  fill_type: z.enum(fillTypes),
  volume_liters: z.number().gt(0),
  target_ec_ms: z.number().min(0).nullable(),
  target_ph: z.number().min(0).max(14).nullable(),
  measured_ec_ms: z.number().min(0).nullable(),
  measured_ph: z.number().min(0).max(14).nullable(),
  water_source: z.string().nullable(),
  water_mix_ratio_ro_percent: z.number().min(0).max(100).nullable(),
  is_organic_fertilizers: z.boolean(),
  notes: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  tankKey: string;
  onCreated: () => void;
  siteKey?: string | null;
  nutrientPlanKey?: string | null;
  currentSequenceOrder?: number;
}

export default function TankFillCreateDialog({ open, onClose, tankKey, onCreated, siteKey, nutrientPlanKey, currentSequenceOrder }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [warnings, setWarnings] = useState<string[]>([]);

  const { control, handleSubmit, reset, watch, setValue } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      fill_type: 'full_change',
      volume_liters: 0,
      target_ec_ms: null,
      target_ph: null,
      measured_ec_ms: null,
      measured_ph: null,
      water_source: null,
      water_mix_ratio_ro_percent: null,
      is_organic_fertilizers: false,
      notes: null,
    },
  });
  useEffect(() => {
    if (!open) {
      reset();
    }
  }, [open, reset]);


  const waterSource = watch('water_source');

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      setWarnings([]);
      const result = await api.recordFillEvent(tankKey, {
        fill_type: data.fill_type,
        volume_liters: data.volume_liters,
        target_ec_ms: data.target_ec_ms,
        target_ph: data.target_ph,
        measured_ec_ms: data.measured_ec_ms,
        measured_ph: data.measured_ph,
        water_source: data.water_source,
        water_mix_ratio_ro_percent: data.water_mix_ratio_ro_percent,
        is_organic_fertilizers: data.is_organic_fertilizers,
        notes: data.notes,
      });
      if (result.warnings.length > 0) {
        setWarnings(result.warnings);
      }
      notification.success(t('pages.tanks.fillRecorded'));
      reset();
      onCreated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog fullScreen={fullScreen} open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      data-testid="tank-fill-create-dialog">
      <DialogTitle>{t('pages.tanks.recordFill')}</DialogTitle>
      <DialogContent>
        {warnings.length > 0 && warnings.map((w, i) => (
          <Alert key={i} severity="warning" sx={{ mb: 1 }}>{w}</Alert>
        ))}
        <form onSubmit={handleSubmit(onSubmit)}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.tanks.sectionFillBasics')}
          </Typography>
          <FormSelectField
            name="fill_type"
            control={control}
            label={t('pages.tanks.fillType')}
            options={fillTypes.map((v) => ({
              value: v,
              label: t(`enums.fillType.${v}`),
            }))}
          />
          <FormRow>
            <FormNumberField
              name="volume_liters"
              control={control}
              label={t('pages.tanks.fillVolume')}
              helperText={t('pages.tanks.fillVolumeHelper')}
              suffix="L"
              inputMode="decimal"
              required
              min={0.1}
              autoFocus
            />
            <FormSelectField
              name="water_source"
              control={control}
              label={t('pages.tanks.waterSource')}
              options={[
                { value: '', label: '\u2014' },
                ...waterSources.map((v) => ({
                  value: v,
                  label: t(`enums.waterSource.${v}`),
                })),
              ]}
            />
          </FormRow>
          {waterSource === 'mixed' && (
            <>
              <FormNumberField
                name="water_mix_ratio_ro_percent"
                control={control}
                label={t('pages.tanks.roPercent')}
                helperText={t('pages.tanks.roPercentHelper')}
                suffix="%"
                inputMode="numeric"
                min={0}
                max={100}
              />
              {siteKey && nutrientPlanKey && currentSequenceOrder && (
                <WaterMixRecommendationBox
                  planKey={nutrientPlanKey}
                  sequenceOrder={currentSequenceOrder}
                  siteKey={siteKey}
                  onApply={(roPercent) => {
                    setValue('water_mix_ratio_ro_percent', roPercent, { shouldDirty: true });
                  }}
                />
              )}
            </>
          )}

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 1 }}>
            {t('pages.tanks.sectionTargetValues')}
          </Typography>
          <FormRow>
            <FormNumberField
              name="target_ec_ms"
              control={control}
              label={t('pages.tanks.targetEc')}
              helperText={t('pages.tanks.targetEcHelper')}
              suffix="mS/cm"
              inputMode="decimal"
              min={0}
            />
            <FormNumberField
              name="target_ph"
              control={control}
              label={t('pages.tanks.targetPh')}
              helperText={t('pages.tanks.targetPhHelper')}
              inputMode="decimal"
              min={0}
              max={14}
            />
          </FormRow>

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 1 }}>
            {t('pages.tanks.sectionMeasuredValues')}
          </Typography>
          <FormRow>
            <FormNumberField
              name="measured_ec_ms"
              control={control}
              label={t('pages.tanks.measuredEc')}
              helperText={t('pages.tanks.measuredEcHelper')}
              suffix="mS/cm"
              inputMode="decimal"
              min={0}
            />
            <FormNumberField
              name="measured_ph"
              control={control}
              label={t('pages.tanks.measuredPh')}
              helperText={t('pages.tanks.measuredPhHelper')}
              inputMode="decimal"
              min={0}
              max={14}
            />
          </FormRow>

          <FormSwitchField
            name="is_organic_fertilizers"
            control={control}
            label={t('pages.tanks.organicFertilizers')}
            helperText={t('pages.tanks.organicFertilizersHelper')}
          />
          <FormTextField
            name="notes"
            control={control}
            label={t('pages.tanks.notes')}
            multiline
            rows={2}
          />
          <FormActions
            onCancel={onClose}
            loading={saving}
            saveLabel={t('pages.tanks.recordFill')}
          />
        </form>
      </DialogContent>
    </Dialog>
  );
}
