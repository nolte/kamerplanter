import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Box from '@mui/material/Box';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormNumberField from '@/components/form/FormNumberField';
import FormRow from '@/components/form/FormRow';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as phasesApi from '@/api/endpoints/phases';
import type { RequirementProfile, NutrientProfile } from '@/api/types';

const reqSchema = z.object({
  light_ppfd_target: z.number().min(0),
  photoperiod_hours: z.number().min(0).max(24),
  temperature_day_c: z.number(),
  temperature_night_c: z.number(),
  humidity_day_percent: z.number().min(0).max(100),
  humidity_night_percent: z.number().min(0).max(100),
  vpd_target_kpa: z.number().min(0),
  co2_ppm: z.number().min(0).nullable(),
  irrigation_frequency_days: z.number().min(0),
  irrigation_volume_ml_per_plant: z.number().min(0),
});

const nutSchema = z.object({
  npk_n: z.number().min(0),
  npk_p: z.number().min(0),
  npk_k: z.number().min(0),
  target_ec_ms: z.number().min(0),
  target_ph: z.number().min(0).max(14),
  calcium_ppm: z.number().min(0).nullable(),
  magnesium_ppm: z.number().min(0).nullable(),
});

const schema = z.object({
  req: reqSchema,
  nut: nutSchema,
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
  phaseKey: string;
  phaseName: string;
  reqProfile: RequirementProfile | null;
  nutProfile: NutrientProfile | null;
}

export default function ProfileEditDialog({
  open,
  onClose,
  onSaved,
  phaseKey,
  phaseName,
  reqProfile,
  nutProfile,
}: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: buildDefaults(reqProfile, nutProfile),
  });

  useEffect(() => {
    if (open) {
      reset(buildDefaults(reqProfile, nutProfile));
    }
  }, [open, reqProfile, nutProfile, reset]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);

      const reqPayload = {
        phase_key: phaseKey,
        light_ppfd_target: data.req.light_ppfd_target,
        photoperiod_hours: data.req.photoperiod_hours,
        temperature_day_c: data.req.temperature_day_c,
        temperature_night_c: data.req.temperature_night_c,
        humidity_day_percent: data.req.humidity_day_percent,
        humidity_night_percent: data.req.humidity_night_percent,
        vpd_target_kpa: data.req.vpd_target_kpa,
        co2_ppm: data.req.co2_ppm,
        irrigation_frequency_days: data.req.irrigation_frequency_days,
        irrigation_volume_ml_per_plant: data.req.irrigation_volume_ml_per_plant,
      };

      const nutPayload = {
        phase_key: phaseKey,
        npk_ratio: [data.nut.npk_n, data.nut.npk_p, data.nut.npk_k] as [number, number, number],
        target_ec_ms: data.nut.target_ec_ms,
        target_ph: data.nut.target_ph,
        calcium_ppm: data.nut.calcium_ppm,
        magnesium_ppm: data.nut.magnesium_ppm,
      };

      if (reqProfile) {
        await phasesApi.updateRequirementProfile(reqProfile.key, reqPayload);
      } else {
        await phasesApi.createRequirementProfile(reqPayload);
      }

      if (nutProfile) {
        await phasesApi.updateNutrientProfile(nutProfile.key, nutPayload);
      } else {
        await phasesApi.createNutrientProfile(nutPayload);
      }

      notification.success(t('common.save'));
      onSaved();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth data-testid="profile-edit-dialog">
      <DialogTitle>
        {phaseName} — {t('pages.profiles.editTitle')}
      </DialogTitle>
      <DialogContent>
        <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {t('pages.profiles.editDesc')}
          </Typography>

          {/* Environment section */}
          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.profiles.requirements')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.profiles.requirementsDesc')}
              </Typography>
              <FormRow>
                <FormNumberField name="req.light_ppfd_target" control={control} label={t('pages.profiles.lightPpfd')} min={0} suffix="PPFD" helperText="0–2000 \u03BCmol/m\u00B2/s" autoFocus />
                <FormNumberField name="req.photoperiod_hours" control={control} label={t('pages.profiles.photoperiodHours')} min={0} max={24} step={0.5} suffix="h" helperText="0–24 h" />
              </FormRow>
              <FormRow>
                <FormNumberField name="req.temperature_day_c" control={control} label={t('pages.profiles.tempDay')} step={0.5} suffix="°C" helperText="18–30 °C" />
                <FormNumberField name="req.temperature_night_c" control={control} label={t('pages.profiles.tempNight')} step={0.5} suffix="°C" helperText="15–25 °C" />
              </FormRow>
              <FormRow>
                <FormNumberField name="req.humidity_day_percent" control={control} label={t('pages.profiles.humidityDay')} min={0} max={100} suffix="%" helperText="40–70 %" />
                <FormNumberField name="req.humidity_night_percent" control={control} label={t('pages.profiles.humidityNight')} min={0} max={100} suffix="%" helperText="45–75 %" />
              </FormRow>
              <FormRow>
                <FormNumberField name="req.vpd_target_kpa" control={control} label={t('pages.profiles.vpdTarget')} min={0} step={0.1} suffix="kPa" helperText="0.8–1.5 kPa" />
                <FormNumberField name="req.co2_ppm" control={control} label="CO\u2082 (ppm)" min={0} suffix="ppm" helperText="400–1500 ppm" />
              </FormRow>
              <FormRow>
                <FormNumberField name="req.irrigation_frequency_days" control={control} label={t('pages.profiles.irrigationFrequency')} min={0} step={0.5} suffix={t('common.days')} />
                <FormNumberField name="req.irrigation_volume_ml_per_plant" control={control} label={t('pages.profiles.irrigationVolume')} min={0} suffix="ml" />
              </FormRow>
            </CardContent>
          </Card>

          {/* Nutrient section */}
          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.profiles.nutrients')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.profiles.nutrientsDesc')}
              </Typography>
              <FormRow>
                <FormNumberField name="nut.npk_n" control={control} label={`N (${t('pages.profiles.npkRatio')})`} min={0} helperText={t('pages.profiles.npkHelper')} />
                <FormNumberField name="nut.npk_p" control={control} label="P" min={0} />
              </FormRow>
              <FormRow>
                <FormNumberField name="nut.npk_k" control={control} label="K" min={0} />
                <span />
              </FormRow>
              <FormRow>
                <FormNumberField name="nut.target_ec_ms" control={control} label="EC" min={0} step={0.1} suffix="mS/cm" helperText="0.5–3.5 mS/cm" />
                <FormNumberField name="nut.target_ph" control={control} label="pH" min={0} max={14} step={0.1} helperText="5.5–7.0" />
              </FormRow>
              <FormRow>
                <FormNumberField name="nut.calcium_ppm" control={control} label="Ca (ppm)" min={0} suffix="ppm" />
                <FormNumberField name="nut.magnesium_ppm" control={control} label="Mg (ppm)" min={0} suffix="ppm" />
              </FormRow>
            </CardContent>
          </Card>

          <Typography variant="caption" color="text.secondary">* {t('common.required')}</Typography>
          <FormActions onCancel={onClose} loading={saving} saveLabel={t('common.save')} />
        </Box>
      </DialogContent>
    </Dialog>
  );
}

function buildDefaults(req: RequirementProfile | null, nut: NutrientProfile | null): FormData {
  return {
    req: {
      light_ppfd_target: req?.light_ppfd_target ?? 400,
      photoperiod_hours: req?.photoperiod_hours ?? 18,
      temperature_day_c: req?.temperature_day_c ?? 25,
      temperature_night_c: req?.temperature_night_c ?? 20,
      humidity_day_percent: req?.humidity_day_percent ?? 60,
      humidity_night_percent: req?.humidity_night_percent ?? 65,
      vpd_target_kpa: req?.vpd_target_kpa ?? 1.0,
      co2_ppm: req?.co2_ppm ?? null,
      irrigation_frequency_days: req?.irrigation_frequency_days ?? 1,
      irrigation_volume_ml_per_plant: req?.irrigation_volume_ml_per_plant ?? 250,
    },
    nut: {
      npk_n: nut?.npk_ratio?.[0] ?? 3,
      npk_p: nut?.npk_ratio?.[1] ?? 1,
      npk_k: nut?.npk_ratio?.[2] ?? 2,
      target_ec_ms: nut?.target_ec_ms ?? 1.5,
      target_ph: nut?.target_ph ?? 6.0,
      calcium_ppm: nut?.calcium_ppm ?? null,
      magnesium_ppm: nut?.magnesium_ppm ?? null,
    },
  };
}
