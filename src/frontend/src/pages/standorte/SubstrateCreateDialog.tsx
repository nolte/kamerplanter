import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Typography from '@mui/material/Typography';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormRow from '@/components/form/FormRow';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/substrates';

const schema = z.object({
  type: z.enum(['soil', 'coco', 'clay_pebbles', 'perlite', 'living_soil', 'peat', 'rockwool_slab', 'rockwool_plug', 'vermiculite', 'none', 'orchid_bark', 'pon_mineral', 'sphagnum', 'hydro_solution']),
  brand: z.string().nullable(),
  name_de: z.string(),
  name_en: z.string(),
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
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      type: 'soil',
      brand: null,
      name_de: '',
      name_en: '',
      ph_base: 6.5,
      ec_base_ms: 0.5,
      water_retention: 'medium',
      air_porosity_percent: 25.0,
      buffer_capacity: 'medium',
      reusable: false,
      max_reuse_cycles: 3,
    },
  });
  useEffect(() => {
    if (!open) {
      reset();
    }
  }, [open, reset]);


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
    <Dialog fullScreen={fullScreen} open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('pages.substrates.create')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.substrates.createIntro')}
        </Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.substrates.sectionIdentification')}
          </Typography>
          <FormSelectField
            name="type"
            control={control}
            label={t('pages.substrates.type')}
            helperText={t('pages.substrates.typeHelper')}
            options={['soil', 'coco', 'clay_pebbles', 'perlite', 'living_soil', 'peat', 'rockwool_slab', 'rockwool_plug', 'vermiculite', 'none', 'orchid_bark', 'pon_mineral', 'sphagnum', 'hydro_solution'].map((v) => ({
              value: v, label: t(`enums.substrateType.${v}`),
            }))}
          />
          <FormTextField name="brand" control={control} label={t('pages.substrates.brand')} helperText={t('pages.substrates.brandHelper')} autoFocus />
          <FormTextField name="name_de" control={control} label={`${t('pages.substrates.name')} (${t('common.langDE')})`} helperText={t('pages.substrates.nameHelper')} />
          <FormTextField name="name_en" control={control} label={`${t('pages.substrates.name')} (${t('common.langEN')})`} helperText={t('pages.substrates.nameHelper')} />
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.substrates.sectionChemistry')}
          </Typography>
          <FormRow>
            <FormNumberField name="ph_base" control={control} label={t('pages.substrates.phBase')} helperText={t('pages.substrates.phBaseHelper')} min={0} max={14} step={0.1} inputMode="decimal" />
            <FormNumberField name="ec_base_ms" control={control} label={t('pages.substrates.ecBase')} helperText={t('pages.substrates.ecBaseHelper')} min={0} step={0.1} inputMode="decimal" />
          </FormRow>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.substrates.sectionPhysical')}
          </Typography>
          <FormSelectField
            name="water_retention"
            control={control}
            label={t('pages.substrates.waterRetention')}
            helperText={t('pages.substrates.waterRetentionHelper')}
            options={['low', 'medium', 'high'].map((v) => ({
              value: v, label: t(`enums.waterRetention.${v}`),
            }))}
          />
          <FormNumberField name="air_porosity_percent" control={control} label={t('pages.substrates.airPorosity')} helperText={t('pages.substrates.airPorosityHelper')} min={0} max={100} step={1} />
          <FormSelectField
            name="buffer_capacity"
            control={control}
            label={t('pages.substrates.bufferCapacity')}
            helperText={t('pages.substrates.bufferCapacityHelper')}
            options={['low', 'medium', 'high'].map((v) => ({
              value: v, label: t(`enums.bufferCapacity.${v}`),
            }))}
          />
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.substrates.sectionReuse')}
          </Typography>
          <FormSwitchField name="reusable" control={control} label={t('pages.substrates.reusable')} helperText={t('pages.substrates.reusableHelper')} />
          <FormNumberField name="max_reuse_cycles" control={control} label={t('pages.substrates.maxReuseCycles')} helperText={t('pages.substrates.maxReuseCyclesHelper')} min={1} />
          <FormActions onCancel={onClose} loading={saving} saveLabel={t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
