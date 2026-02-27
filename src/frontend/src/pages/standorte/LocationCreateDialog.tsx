import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormTimeField from '@/components/form/FormTimeField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/sites';

const timeRegex = /^\d{2}:\d{2}$/;

const schema = z.object({
  name: z.string().min(1),
  area_m2: z.number().min(0),
  light_type: z.enum(['natural', 'led', 'hps', 'cmh', 'mixed']),
  irrigation_system: z.enum(['manual', 'drip', 'hydro', 'mist', 'nft', 'ebb_flow']),
  lights_on: z.string().regex(timeRegex).nullable().optional(),
  lights_off: z.string().regex(timeRegex).nullable().optional(),
  use_dynamic_sunrise: z.boolean(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  siteKey: string;
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function LocationCreateDialog({ siteKey, open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      area_m2: 0,
      light_type: 'natural',
      irrigation_system: 'manual',
      lights_on: null,
      lights_off: null,
      use_dynamic_sunrise: false,
    },
  });

  const lightType = useWatch({ control, name: 'light_type' });
  const isArtificial = lightType === 'led' || lightType === 'hps' || lightType === 'cmh';
  const isNaturalOrMixed = lightType === 'natural' || lightType === 'mixed';

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await api.createLocation({
        ...data,
        site_key: siteKey,
        lights_on: data.lights_on || undefined,
        lights_off: data.lights_off || undefined,
      });
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
      <DialogTitle>{t('pages.locations.create')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField name="name" control={control} label={t('pages.locations.name')} required />
          <FormNumberField name="area_m2" control={control} label={t('pages.locations.area')} min={0} />
          <FormSelectField
            name="light_type"
            control={control}
            label={t('pages.locations.lightType')}
            options={['natural', 'led', 'hps', 'cmh', 'mixed'].map((v) => ({
              value: v,
              label: t(`enums.lightType.${v}`),
            }))}
          />
          <FormSelectField
            name="irrigation_system"
            control={control}
            label={t('pages.locations.irrigationSystem')}
            options={['manual', 'drip', 'hydro', 'mist', 'nft', 'ebb_flow'].map((v) => ({
              value: v,
              label: t(`enums.irrigationSystem.${v}`),
            }))}
          />

          {(isArtificial || isNaturalOrMixed) && (
            <>
              <FormTimeField
                name="lights_on"
                control={control}
                label={t('pages.locations.lightsOn')}
                helperText={t('pages.locations.lightsOnHelper')}
              />
              <FormTimeField
                name="lights_off"
                control={control}
                label={t('pages.locations.lightsOff')}
                helperText={t('pages.locations.lightsOffHelper')}
              />
            </>
          )}

          {isNaturalOrMixed && (
            <FormSwitchField
              name="use_dynamic_sunrise"
              control={control}
              label={t('pages.locations.useDynamicSunrise')}
            />
          )}

          <FormActions onCancel={onClose} loading={saving} saveLabel={t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
