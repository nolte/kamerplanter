import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import GrowthPhaseListSection from './GrowthPhaseListSection';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as phasesApi from '@/api/endpoints/phases';
import type { LifecycleConfig } from '@/api/types';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import { Controller } from 'react-hook-form';

const schema = z.object({
  cycle_type: z.enum(['annual', 'biennial', 'perennial']),
  typical_lifespan_years: z.number().nullable(),
  dormancy_required: z.boolean(),
  vernalization_required: z.boolean(),
  vernalization_min_days: z.number().nullable(),
  photoperiod_type: z.enum(['short_day', 'long_day', 'day_neutral']),
  critical_day_length_hours: z.number().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  speciesKey: string;
}

export default function LifecycleConfigSection({ speciesKey }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [lifecycle, setLifecycle] = useState<LifecycleConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [exists, setExists] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      cycle_type: 'annual',
      typical_lifespan_years: null,
      dormancy_required: false,
      vernalization_required: false,
      vernalization_min_days: null,
      photoperiod_type: 'day_neutral',
      critical_day_length_hours: null,
    },
  });

  useEffect(() => {
    setLoading(true);
    phasesApi
      .getLifecycleConfig(speciesKey)
      .then((lc) => {
        setLifecycle(lc);
        setExists(true);
        reset({
          cycle_type: lc.cycle_type,
          typical_lifespan_years: lc.typical_lifespan_years,
          dormancy_required: lc.dormancy_required,
          vernalization_required: lc.vernalization_required,
          vernalization_min_days: lc.vernalization_min_days,
          photoperiod_type: lc.photoperiod_type,
          critical_day_length_hours: lc.critical_day_length_hours,
        });
      })
      .catch(() => setExists(false))
      .finally(() => setLoading(false));
  }, [speciesKey, reset]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      let result: LifecycleConfig;
      if (exists && lifecycle) {
        result = await phasesApi.updateLifecycleConfig(speciesKey, lifecycle.key, data);
      } else {
        result = await phasesApi.createLifecycleConfig(speciesKey, data);
        setExists(true);
      }
      setLifecycle(result);
      notification.success(t('common.save'));
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSkeleton variant="form" />;

  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        {t('pages.lifecycle.title')}
      </Typography>
      <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 600 }}>
        <FormSelectField
          name="cycle_type"
          control={control}
          label={t('pages.lifecycle.cycleType')}
          options={['annual', 'biennial', 'perennial'].map((v) => ({
            value: v,
            label: t(`enums.cycleType.${v}`),
          }))}
        />
        <FormNumberField
          name="typical_lifespan_years"
          control={control}
          label={t('pages.lifecycle.lifespanYears')}
          min={1}
        />
        <FormSelectField
          name="photoperiod_type"
          control={control}
          label={t('pages.lifecycle.photoperiodType')}
          options={['short_day', 'long_day', 'day_neutral'].map((v) => ({
            value: v,
            label: t(`enums.photoperiodType.${v}`),
          }))}
        />
        <FormNumberField
          name="critical_day_length_hours"
          control={control}
          label={t('pages.lifecycle.criticalDayLength')}
          min={0}
          max={24}
          step={0.5}
        />
        <Controller
          name="dormancy_required"
          control={control}
          render={({ field }) => (
            <FormControlLabel
              control={<Switch checked={field.value} onChange={field.onChange} />}
              label={t('pages.lifecycle.dormancy')}
              sx={{ mb: 1, display: 'block' }}
            />
          )}
        />
        <Controller
          name="vernalization_required"
          control={control}
          render={({ field }) => (
            <FormControlLabel
              control={<Switch checked={field.value} onChange={field.onChange} />}
              label={t('pages.lifecycle.vernalization')}
              sx={{ mb: 1, display: 'block' }}
            />
          )}
        />
        <FormNumberField
          name="vernalization_min_days"
          control={control}
          label={t('pages.lifecycle.vernalizationDays')}
          min={1}
        />
        <FormActions
          onCancel={() => {}}
          loading={saving}
          saveLabel={exists ? t('common.save') : t('common.create')}
        />
      </Box>

      {lifecycle && (
        <GrowthPhaseListSection lifecycleKey={lifecycle.key} />
      )}
    </Box>
  );
}
