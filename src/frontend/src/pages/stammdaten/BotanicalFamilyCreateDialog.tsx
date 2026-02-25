import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Typography from '@mui/material/Typography';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormMultiSelectField from '@/components/form/FormMultiSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormChipInput from '@/components/form/FormChipInput';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/botanicalFamilies';

const growthHabitValues = ['herb', 'shrub', 'tree', 'vine', 'groundcover'] as const;
const pollinationValues = ['insect', 'wind', 'self'] as const;

const schema = z.object({
  name: z.string().min(1).refine((v) => v.endsWith('aceae'), {
    message: "Muss auf '-aceae' enden",
  }),
  common_name_de: z.string(),
  common_name_en: z.string(),
  order: z.string(),
  description: z.string(),
  typical_nutrient_demand: z.enum(['light', 'medium', 'heavy']),
  nitrogen_fixing: z.boolean(),
  typical_root_depth: z.enum(['shallow', 'medium', 'deep']),
  soil_ph_min: z.union([z.number().min(3).max(9), z.literal('')]),
  soil_ph_max: z.union([z.number().min(3).max(9), z.literal('')]),
  frost_tolerance: z.enum(['sensitive', 'moderate', 'hardy', 'very_hardy']),
  typical_growth_forms: z.array(z.enum(growthHabitValues)).min(1),
  common_pests: z.array(z.string()),
  common_diseases: z.array(z.string()),
  pollination_type: z.array(z.enum(pollinationValues)).min(1),
  rotation_category: z.string(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function BotanicalFamilyCreateDialog({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      common_name_de: '',
      common_name_en: '',
      order: '',
      description: '',
      typical_nutrient_demand: 'medium',
      nitrogen_fixing: false,
      typical_root_depth: 'medium',
      soil_ph_min: '',
      soil_ph_max: '',
      frost_tolerance: 'moderate',
      typical_growth_forms: ['herb'],
      common_pests: [],
      common_diseases: [],
      pollination_type: ['insect'],
      rotation_category: '',
    },
  });

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      const { soil_ph_min, soil_ph_max, ...rest } = data;
      const payload = {
        ...rest,
        order: data.order || undefined,
        soil_ph_preference:
          typeof soil_ph_min === 'number' && typeof soil_ph_max === 'number'
            ? { min_ph: soil_ph_min, max_ph: soil_ph_max }
            : undefined,
      };
      await api.createBotanicalFamily(payload);
      notification.success(t('common.create'));
      reset();
      onCreated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const nutrientDemandOptions = [
    { value: 'light', label: t('enums.nutrientDemand.light') },
    { value: 'medium', label: t('enums.nutrientDemand.medium') },
    { value: 'heavy', label: t('enums.nutrientDemand.heavy') },
  ];

  const rootDepthOptions = [
    { value: 'shallow', label: t('enums.rootDepth.shallow') },
    { value: 'medium', label: t('enums.rootDepth.medium') },
    { value: 'deep', label: t('enums.rootDepth.deep') },
  ];

  const frostToleranceOptions = [
    { value: 'sensitive', label: t('enums.frostTolerance.sensitive') },
    { value: 'moderate', label: t('enums.frostTolerance.moderate') },
    { value: 'hardy', label: t('enums.frostTolerance.hardy') },
    { value: 'very_hardy', label: t('enums.frostTolerance.very_hardy') },
  ];

  const growthFormOptions = [
    { value: 'herb', label: t('enums.growthHabit.herb') },
    { value: 'shrub', label: t('enums.growthHabit.shrub') },
    { value: 'tree', label: t('enums.growthHabit.tree') },
    { value: 'vine', label: t('enums.growthHabit.vine') },
    { value: 'groundcover', label: t('enums.growthHabit.groundcover') },
  ];

  const pollinationOptions = [
    { value: 'insect', label: t('enums.pollinationType.insect') },
    { value: 'wind', label: t('enums.pollinationType.wind') },
    { value: 'self', label: t('enums.pollinationType.self') },
  ];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth data-testid="create-dialog">
      <DialogTitle>{t('pages.botanicalFamilies.create')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.botanicalFamilies.createIntro')}
        </Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField
            name="name"
            control={control}
            label={t('pages.botanicalFamilies.name')}
            required
            helperText={t('pages.botanicalFamilies.nameHelper')}
          />
          <FormTextField
            name="common_name_de"
            control={control}
            label={t('pages.botanicalFamilies.commonNameDe')}
            helperText={t('pages.botanicalFamilies.commonNameDeHelper')}
          />
          <FormTextField
            name="common_name_en"
            control={control}
            label={t('pages.botanicalFamilies.commonNameEn')}
            helperText={t('pages.botanicalFamilies.commonNameEnHelper')}
          />
          <FormTextField
            name="order"
            control={control}
            label={t('pages.botanicalFamilies.order')}
            helperText={t('pages.botanicalFamilies.orderHelper')}
          />
          <FormTextField
            name="description"
            control={control}
            label={t('pages.botanicalFamilies.description')}
            multiline
            rows={2}
            helperText={t('pages.botanicalFamilies.descriptionHelper')}
          />
          <FormSelectField
            name="typical_nutrient_demand"
            control={control}
            label={t('pages.botanicalFamilies.nutrientDemand')}
            options={nutrientDemandOptions}
            helperText={t('pages.botanicalFamilies.nutrientDemandHelper')}
          />
          <Controller
            name="nitrogen_fixing"
            control={control}
            render={({ field }) => (
              <FormControlLabel
                control={
                  <Switch
                    checked={field.value}
                    onChange={field.onChange}
                    data-testid="form-field-nitrogen_fixing"
                  />
                }
                label={t('pages.botanicalFamilies.nitrogenFixing')}
                sx={{ mb: 2, display: 'block' }}
              />
            )}
          />
          <FormSelectField
            name="typical_root_depth"
            control={control}
            label={t('pages.botanicalFamilies.rootDepth')}
            options={rootDepthOptions}
            helperText={t('pages.botanicalFamilies.rootDepthHelper')}
          />
          <FormNumberField
            name="soil_ph_min"
            control={control}
            label={t('pages.botanicalFamilies.soilPhMin')}
            min={3}
            max={9}
            step={0.1}
            helperText={t('pages.botanicalFamilies.soilPhHelper')}
          />
          <FormNumberField
            name="soil_ph_max"
            control={control}
            label={t('pages.botanicalFamilies.soilPhMax')}
            min={3}
            max={9}
            step={0.1}
          />
          <FormSelectField
            name="frost_tolerance"
            control={control}
            label={t('pages.botanicalFamilies.frostTolerance')}
            options={frostToleranceOptions}
            helperText={t('pages.botanicalFamilies.frostToleranceHelper')}
          />
          <FormMultiSelectField
            name="typical_growth_forms"
            control={control}
            label={t('pages.botanicalFamilies.growthForms')}
            options={growthFormOptions}
            required
            helperText={t('pages.botanicalFamilies.growthFormsHelper')}
          />
          <FormChipInput
            name="common_pests"
            control={control}
            label={t('pages.botanicalFamilies.commonPests')}
            helperText={t('pages.botanicalFamilies.commonPestsHelper')}
          />
          <FormChipInput
            name="common_diseases"
            control={control}
            label={t('pages.botanicalFamilies.commonDiseases')}
            helperText={t('pages.botanicalFamilies.commonDiseasesHelper')}
          />
          <FormMultiSelectField
            name="pollination_type"
            control={control}
            label={t('pages.botanicalFamilies.pollinationType')}
            options={pollinationOptions}
            required
            helperText={t('pages.botanicalFamilies.pollinationTypeHelper')}
          />
          <FormTextField
            name="rotation_category"
            control={control}
            label={t('pages.botanicalFamilies.rotationCategory')}
            helperText={t('pages.botanicalFamilies.rotationCategoryHelper')}
          />
          <FormActions onCancel={onClose} loading={saving} saveLabel={t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
