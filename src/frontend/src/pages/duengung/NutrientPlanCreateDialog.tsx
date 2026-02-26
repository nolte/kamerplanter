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
import FormSwitchField from '@/components/form/FormSwitchField';
import FormChipInput from '@/components/form/FormChipInput';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/nutrient-plans';

const substrateTypes = [
  'soil',
  'coco',
  'rockwool',
  'clay_pebbles',
  'perlite',
  'living_soil',
  'hydro_solution',
] as const;

const schema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().max(2000),
  recommended_substrate_type: z.enum(substrateTypes).nullable(),
  author: z.string().max(200),
  is_template: z.boolean(),
  tags: z.array(z.string()),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function NutrientPlanCreateDialog({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      description: '',
      recommended_substrate_type: null,
      author: '',
      is_template: false,
      tags: [],
    },
  });

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await api.createNutrientPlan({
        name: data.name,
        description: data.description,
        recommended_substrate_type: data.recommended_substrate_type,
        author: data.author,
        is_template: data.is_template,
        tags: data.tags,
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
      <DialogTitle>{t('pages.nutrientPlans.create')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField
            name="name"
            control={control}
            label={t('pages.nutrientPlans.name')}
            required
          />
          <FormTextField
            name="description"
            control={control}
            label={t('pages.nutrientPlans.description')}
            multiline
            rows={3}
          />
          <FormSelectField
            name="recommended_substrate_type"
            control={control}
            label={t('pages.nutrientPlans.substrateType')}
            options={substrateTypes.map((v) => ({
              value: v,
              label: t(`enums.substrateType.${v}`),
            }))}
          />
          <FormTextField
            name="author"
            control={control}
            label={t('pages.nutrientPlans.author')}
          />
          <FormSwitchField
            name="is_template"
            control={control}
            label={t('pages.nutrientPlans.isTemplate')}
          />
          <FormChipInput
            name="tags"
            control={control}
            label={t('pages.nutrientPlans.tags')}
            placeholder={t('pages.nutrientPlans.tagsPlaceholder')}
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
