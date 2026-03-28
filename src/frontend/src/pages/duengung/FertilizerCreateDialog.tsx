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
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormRow from '@/components/form/FormRow';
import FormActions from '@/components/form/FormActions';
import Typography from '@mui/material/Typography';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/fertilizers';

const fertilizerTypes = ['base', 'supplement', 'booster', 'biological', 'ph_adjuster', 'organic', 'silicate'] as const;
const phEffects = ['acidic', 'alkaline', 'neutral'] as const;
const applicationMethods = ['fertigation', 'drench', 'foliar', 'top_dress', 'any'] as const;

const schema = z.object({
  product_name: z.string().min(1).max(200),
  brand: z.string().max(200),
  fertilizer_type: z.enum(fertilizerTypes),
  is_organic: z.boolean(),
  tank_safe: z.boolean(),
  npk_n: z.number().min(0),
  npk_p: z.number().min(0),
  npk_k: z.number().min(0),
  ec_contribution_per_ml: z.number().min(0),
  mixing_priority: z.number().int().min(1),
  ph_effect: z.enum(phEffects),
  recommended_application: z.enum(applicationMethods),
  notes: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function FertilizerCreateDialog({ open, onClose, onCreated }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      product_name: '',
      brand: '',
      fertilizer_type: 'base',
      is_organic: false,
      tank_safe: true,
      npk_n: 0,
      npk_p: 0,
      npk_k: 0,
      ec_contribution_per_ml: 0,
      mixing_priority: 1,
      ph_effect: 'neutral',
      recommended_application: 'fertigation',
      notes: null,
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
      await api.createFertilizer({
        product_name: data.product_name,
        brand: data.brand,
        fertilizer_type: data.fertilizer_type,
        is_organic: data.is_organic,
        tank_safe: data.tank_safe,
        npk_ratio: [data.npk_n, data.npk_p, data.npk_k],
        ec_contribution_per_ml: data.ec_contribution_per_ml,
        mixing_priority: data.mixing_priority,
        ph_effect: data.ph_effect,
        recommended_application: data.recommended_application,
        notes: data.notes,
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
    <Dialog fullScreen={fullScreen} open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('pages.fertilizers.create')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 1 }}>
            {t('pages.fertilizers.sectionIdentification')}
          </Typography>
          <FormTextField
            name="product_name"
            control={control}
            label={t('pages.fertilizers.productName')}
            required
          />
          <FormTextField
            name="brand"
            control={control}
            label={t('pages.fertilizers.brand')}
          />
          <FormSelectField
            name="fertilizer_type"
            control={control}
            label={t('pages.fertilizers.fertilizerType')}
            options={fertilizerTypes.map((v) => ({
              value: v,
              label: t(`enums.fertilizerType.${v}`),
            }))}
          />

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.fertilizers.sectionNutrients')}
          </Typography>
          <FormRow>
            <FormNumberField
              name="npk_n"
              control={control}
              label={t('pages.fertilizers.npkN')}
              min={0}
              suffix="%"
              inputMode="decimal"
              helperText={t('pages.fertilizers.npkNHelper')}
            />
            <FormNumberField
              name="npk_p"
              control={control}
              label={t('pages.fertilizers.npkP')}
              min={0}
              suffix="%"
              inputMode="decimal"
            />
          </FormRow>
          <FormRow>
            <FormNumberField
              name="npk_k"
              control={control}
              label={t('pages.fertilizers.npkK')}
              min={0}
              suffix="%"
              inputMode="decimal"
            />
            <FormNumberField
              name="ec_contribution_per_ml"
              control={control}
              label={t('pages.fertilizers.ecContribution')}
              min={0}
              suffix="mS/ml"
              inputMode="decimal"
              helperText={t('pages.fertilizers.ecContributionHelper')}
            />
          </FormRow>

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.fertilizers.sectionMixing')}
          </Typography>
          <FormRow>
            <FormNumberField
              name="mixing_priority"
              control={control}
              label={t('pages.fertilizers.mixingPriority')}
              min={1}
              step={1}
              inputMode="numeric"
              helperText={t('pages.fertilizers.mixingPriorityHelper')}
            />
            <FormSelectField
              name="ph_effect"
              control={control}
              label={t('pages.fertilizers.phEffect')}
              options={phEffects.map((v) => ({
                value: v,
                label: t(`enums.phEffect.${v}`),
              }))}
            />
          </FormRow>
          <FormSelectField
            name="recommended_application"
            control={control}
            label={t('pages.fertilizers.recommendedApplication')}
            options={applicationMethods.map((v) => ({
              value: v,
              label: t(`enums.applicationMethod.${v}`),
            }))}
          />

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.fertilizers.sectionProperties')}
          </Typography>
          <FormRow>
            <FormSwitchField
              name="is_organic"
              control={control}
              label={t('pages.fertilizers.isOrganic')}
              helperText={t('pages.fertilizers.isOrganicHelper')}
            />
            <FormSwitchField
              name="tank_safe"
              control={control}
              label={t('pages.fertilizers.tankSafe')}
              helperText={t('pages.fertilizers.tankSafeHelper')}
            />
          </FormRow>
          <FormTextField
            name="notes"
            control={control}
            label={t('pages.fertilizers.notes')}
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
