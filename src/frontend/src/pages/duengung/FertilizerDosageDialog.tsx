import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as planApi from '@/api/endpoints/nutrient-plans';
import * as fertApi from '@/api/endpoints/fertilizers';
import type { Fertilizer, FertilizerDosage } from '@/api/types';

const schema = z.object({
  fertilizer_key: z.string().min(1),
  ml_per_liter: z.number().gt(0).max(50),
  optional: z.boolean(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  planKey: string;
  entryKey: string;
  existingDosages: FertilizerDosage[];
  onSaved: () => void;
}

export default function FertilizerDosageDialog({
  open,
  onClose,
  planKey,
  entryKey,
  existingDosages,
  onSaved,
}: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [fertilizers, setFertilizers] = useState<Fertilizer[]>([]);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      fertilizer_key: '',
      ml_per_liter: 1,
      optional: false,
    },
  });

  useEffect(() => {
    if (open) {
      fertApi.fetchFertilizers(0, 200).then(setFertilizers).catch(() => {});
      reset({ fertilizer_key: '', ml_per_liter: 1, optional: false });
    }
  }, [open, reset]);

  const existingKeys = new Set(existingDosages.map((d) => d.fertilizer_key));
  const availableFertilizers = fertilizers.filter((f) => !existingKeys.has(f.key));

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await planApi.addFertilizerToEntry(planKey, entryKey, {
        fertilizer_key: data.fertilizer_key,
        ml_per_liter: data.ml_per_liter,
        optional: data.optional,
      });
      notification.success(t('common.create'));
      onSaved();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t('pages.nutrientPlans.addFertilizer')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormSelectField
            name="fertilizer_key"
            control={control}
            label={t('entities.fertilizer')}
            options={availableFertilizers.map((f) => ({
              value: f.key,
              label: `${f.product_name} (${f.brand})`,
            }))}
            required
          />
          <FormNumberField
            name="ml_per_liter"
            control={control}
            label={t('pages.nutrientPlans.mlPerLiter')}
            min={0.01}
            max={50}
            required
          />
          <FormSwitchField
            name="optional"
            control={control}
            label={t('pages.nutrientPlans.optionalDosage')}
            helperText={t('pages.nutrientPlans.optionalDosageHelper')}
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
