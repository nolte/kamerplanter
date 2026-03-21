import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Alert from '@mui/material/Alert';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormChipInput from '@/components/form/FormChipInput';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/activities';

const schema = z.object({
  name: z.string().min(1).max(200),
  name_de: z.string(),
  description: z.string(),
  description_de: z.string(),
  category: z.enum(['training_hst', 'training_lst', 'pruning', 'ausgeizen', 'transplant', 'harvest_prep', 'propagation', 'general']),
  stress_level: z.enum(['none', 'low', 'medium', 'high']),
  skill_level: z.enum(['beginner', 'intermediate', 'advanced', 'expert']),
  recovery_days_default: z.number().min(0),
  estimated_duration_minutes: z.number().min(1).nullable(),
  requires_photo: z.boolean(),
  species_compatible: z.array(z.string()),
  forbidden_phases: z.array(z.string()),
  tools_required: z.array(z.string()),
  tags: z.array(z.string()),
  sort_order: z.number().min(0),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function ActivityCreateDialog({ open, onClose, onCreated }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset, watch } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      name_de: '',
      description: '',
      description_de: '',
      category: 'general',
      stress_level: 'none',
      skill_level: 'beginner',
      recovery_days_default: 0,
      estimated_duration_minutes: null,
      requires_photo: false,
      species_compatible: [],
      forbidden_phases: [],
      tools_required: [],
      tags: [],
      sort_order: 0,
    },
  });

  const speciesCompatible = watch('species_compatible');

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await api.createActivity({
        ...data,
        estimated_duration_minutes: data.estimated_duration_minutes ?? undefined,
      });
      notification.success(t('common.created'));
      reset();
      onCreated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const categoryOptions = [
    'training_hst', 'training_lst', 'pruning', 'ausgeizen',
    'transplant', 'harvest_prep', 'propagation', 'general',
  ].map((v) => ({ value: v, label: t(`enums.activityCategory.${v}`) }));

  const stressOptions = ['none', 'low', 'medium', 'high'].map((v) => ({
    value: v, label: t(`enums.stressLevel.${v}`),
  }));

  const skillOptions = ['beginner', 'intermediate', 'advanced', 'expert'].map((v) => ({
    value: v, label: t(`enums.skillLevel.${v}`),
  }));

  return (
    <Dialog fullScreen={fullScreen} open={open} onClose={onClose} maxWidth="md" fullWidth data-testid="create-dialog">
      <DialogTitle>{t('pages.activities.create')}</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)} noValidate>

          {/* --- Section: Bezeichnung --- */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 1 }}>
            {t('pages.activities.sectionIdentification')}
          </Typography>
          <FormRow>
            <FormTextField name="name" control={control} label={t('pages.activities.nameEn')} required autoFocus />
            <FormTextField name="name_de" control={control} label={t('pages.activities.nameDe')} />
          </FormRow>
          <FormRow>
            <FormTextField name="description" control={control} label={t('pages.activities.descriptionEn')} multiline rows={2} />
            <FormTextField name="description_de" control={control} label={t('pages.activities.descriptionDe')} multiline rows={2} />
          </FormRow>

          {/* --- Section: Klassifizierung --- */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.activities.sectionClassification')}
          </Typography>
          <FormRow>
            <FormSelectField name="category" control={control} label={t('pages.activities.category')} options={categoryOptions} />
            <FormSelectField name="skill_level" control={control} label={t('pages.activities.skillLevel')} options={skillOptions} />
          </FormRow>
          <FormRow>
            <FormSelectField name="stress_level" control={control} label={t('pages.activities.stressLevel')} options={stressOptions} />
            <FormNumberField name="recovery_days_default" control={control} label={t('pages.activities.recoveryDays')} min={0} suffix="d" />
          </FormRow>

          {/* --- Section: Ausführung --- */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.activities.sectionExecution')}
          </Typography>
          <FormRow>
            <FormNumberField name="estimated_duration_minutes" control={control} label={t('pages.activities.estimatedDuration')} min={1} suffix="min" />
            <FormSwitchField name="requires_photo" control={control} label={t('pages.activities.requiresPhoto')} helperText={t('pages.activities.requiresPhotoHint')} />
          </FormRow>
          <FormChipInput name="tools_required" control={control} label={t('pages.activities.toolsRequired')} helperText={t('pages.activities.toolsRequiredHint')} />

          {/* --- Section: Geltungsbereich --- */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.activities.sectionScope')}
          </Typography>
          <Alert
            severity={speciesCompatible.length === 0 ? 'success' : 'info'}
            sx={{ mb: 2 }}
            icon={false}
          >
            {speciesCompatible.length === 0
              ? t('pages.activities.scopeUniversalInfo')
              : t('pages.activities.scopeRestrictedInfo', { count: speciesCompatible.length })}
          </Alert>
          <Controller
            name="species_compatible"
            control={control}
            render={({ field }) => (
              <Autocomplete
                multiple
                freeSolo
                options={[]}
                value={field.value}
                onChange={(_, newValue) => field.onChange(newValue)}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => {
                    const { key, ...tagProps } = getTagProps({ index });
                    return <Chip key={key} label={option} size="small" color="primary" variant="outlined" {...tagProps} />;
                  })
                }
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label={t('pages.activities.speciesCompatible')}
                    helperText={t('pages.activities.speciesCompatibleHint')}
                  />
                )}
              />
            )}
          />

          {/* --- Section: Phasenbeschränkungen --- */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.activities.sectionPhaseRestrictions')}
          </Typography>
          <FormChipInput name="forbidden_phases" control={control} label={t('pages.activities.forbiddenPhases')} helperText={t('pages.activities.forbiddenPhasesHint')} />

          {/* --- Section: Tags & Sortierung --- */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.activities.sectionMeta')}
          </Typography>
          <FormChipInput name="tags" control={control} label={t('pages.activities.tags')} helperText={t('pages.activities.tagsHint')} />
          <FormNumberField name="sort_order" control={control} label={t('pages.activities.sortOrder')} min={0} step={1} />

          <FormActions
            onCancel={() => { reset(); onClose(); }}
            saveLabel={t('common.create')}
            loading={saving}
          />
        </form>
      </DialogContent>
    </Dialog>
  );
}
