import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/substrates';

const schema = z.object({
  type: z.enum(['soil', 'coco', 'clay_pebbles', 'perlite', 'living_soil', 'peat', 'rockwool_slab', 'rockwool_plug', 'vermiculite', 'none', 'orchid_bark', 'pon_mineral', 'sphagnum', 'hydro_solution']),
  brand: z.string().nullable(),
  ph_base: z.number().min(0).max(14),
  ec_base_ms: z.number().min(0),
  water_retention: z.enum(['low', 'medium', 'high']),
  air_porosity_percent: z.number().min(0).max(100),
  buffer_capacity: z.enum(['low', 'medium', 'high']),
  reusable: z.boolean(),
  max_reuse_cycles: z.number().min(1),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function SubstrateCreateDialog({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      type: 'soil',
      brand: null,
      ph_base: 6.5,
      ec_base_ms: 0.5,
      water_retention: 'medium',
      air_porosity_percent: 25.0,
      buffer_capacity: 'medium',
      reusable: false,
      max_reuse_cycles: 3,
    },
  });

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await api.createSubstrate(data);
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
      <DialogTitle>{t('pages.substrates.create')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormSelectField
            name="type"
            control={control}
            label={t('pages.substrates.type')}
            options={['soil', 'coco', 'clay_pebbles', 'perlite', 'living_soil', 'peat', 'rockwool_slab', 'rockwool_plug', 'vermiculite', 'none', 'orchid_bark', 'pon_mineral', 'sphagnum', 'hydro_solution'].map((v) => ({
              value: v, label: t(`enums.substrateType.${v}`),
            }))}
          />
          <FormTextField name="brand" control={control} label={t('pages.substrates.brand')} />
          <FormNumberField name="ph_base" control={control} label={t('pages.substrates.phBase')} min={0} max={14} step={0.1} />
          <FormNumberField name="ec_base_ms" control={control} label={t('pages.substrates.ecBase')} min={0} step={0.1} />
          <FormSelectField
            name="water_retention"
            control={control}
            label={t('pages.substrates.waterRetention')}
            options={['low', 'medium', 'high'].map((v) => ({
              value: v, label: t(`enums.waterRetention.${v}`),
            }))}
          />
          <FormNumberField name="air_porosity_percent" control={control} label={t('pages.substrates.airPorosity')} min={0} max={100} step={1} />
          <FormSelectField
            name="buffer_capacity"
            control={control}
            label={t('pages.substrates.bufferCapacity')}
            options={['low', 'medium', 'high'].map((v) => ({
              value: v, label: t(`enums.bufferCapacity.${v}`),
            }))}
          />
          <FormSwitchField name="reusable" control={control} label={t('pages.substrates.reusable')} />
          <FormNumberField name="max_reuse_cycles" control={control} label={t('pages.substrates.maxReuseCycles')} min={1} />
          <FormActions onCancel={onClose} loading={saving} saveLabel={t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
