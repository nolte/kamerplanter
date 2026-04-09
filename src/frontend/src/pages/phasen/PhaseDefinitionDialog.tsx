import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Typography from '@mui/material/Typography';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as phaseSequenceApi from '@/api/endpoints/phaseSequences';
import type { PhaseDefinition } from '@/api/types';

const stressLevels = ['none', 'low', 'medium', 'high'] as const;

const schema = z.object({
  name: z.string().min(1).max(200),
  display_name: z.string().max(200).optional().or(z.literal('')),
  description: z.string().optional().or(z.literal('')),
  typical_duration_days: z.number().min(1),
  stress_tolerance: z.enum(stressLevels),
  watering_interval_days: z.number().min(1).nullable(),
  tags: z.string().optional().or(z.literal('')),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  definition?: PhaseDefinition;
  onSaved: () => void;
}

export default function PhaseDefinitionDialog({
  open,
  onClose,
  definition,
  onSaved,
}: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const isEdit = !!definition;

  const defaultValues: FormData = {
    name: '',
    display_name: '',
    description: '',
    typical_duration_days: 7,
    stress_tolerance: 'none',
    watering_interval_days: null,
    tags: '',
  };

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues,
  });

  useEffect(() => {
    if (open && definition) {
      reset({
        name: definition.name,
        display_name: definition.display_name || '',
        description: definition.description || '',
        typical_duration_days: definition.typical_duration_days,
        stress_tolerance:
          (definition.stress_tolerance as FormData['stress_tolerance']) || 'none',
        watering_interval_days: definition.watering_interval_days,
        tags: definition.tags.join(', '),
      });
    } else if (open) {
      reset(defaultValues);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, definition, reset]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      const tagsArray = data.tags
        ? data.tags
            .split(',')
            .map((t) => t.trim())
            .filter(Boolean)
        : [];
      const payload = {
        name: data.name,
        display_name: data.display_name || undefined,
        description: data.description || undefined,
        typical_duration_days: data.typical_duration_days,
        stress_tolerance: data.stress_tolerance,
        watering_interval_days: data.watering_interval_days,
        tags: tagsArray.length > 0 ? tagsArray : undefined,
      };
      if (isEdit && definition) {
        await phaseSequenceApi.updatePhaseDefinition(definition.key, payload);
        notification.success(t('pages.phaseSequences.definitionUpdated'));
      } else {
        await phaseSequenceApi.createPhaseDefinition(payload);
        notification.success(t('pages.phaseSequences.definitionCreated'));
      }
      onSaved();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="phase-definition-dialog-title"
    >
      <DialogTitle id="phase-definition-dialog-title">
        {isEdit
          ? t('pages.phaseSequences.editDefinition')
          : t('pages.phaseSequences.createDefinition')}
      </DialogTitle>
      <DialogContent dividers>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {isEdit
            ? t('pages.phaseSequences.editDefinitionIntro')
            : t('pages.phaseSequences.createDefinitionIntro')}
        </Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          {/* Section: Identity */}
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.phaseSequences.sectionIdentity')}
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: { xs: 1, sm: 2 } }}>
            <FormTextField
              name="name"
              control={control}
              label={t('common.name')}
              required
              autoFocus={!isEdit}
              disabled={isEdit && definition?.is_system}
              helperText={isEdit && definition?.is_system ? t('pages.phaseSequences.systemFieldReadonly') : undefined}
            />
            <FormTextField
              name="display_name"
              control={control}
              label={t('pages.phaseSequences.displayName')}
              autoFocus={isEdit}
              helperText={t('pages.phaseSequences.displayNameHelper')}
            />
          </Box>

          <FormTextField
            name="description"
            control={control}
            label={t('common.description')}
            multiline
            minRows={2}
          />

          {/* Section: Timing & Parameters */}
          <Divider sx={{ my: 1.5 }} />
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.phaseSequences.sectionParameters')}
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: { xs: 1, sm: 2 } }}>
            <FormNumberField
              name="typical_duration_days"
              control={control}
              label={t('pages.phaseSequences.typicalDuration')}
              required
              min={1}
              step={1}
              suffix={t('common.days')}
              helperText={t('pages.phaseSequences.typicalDurationHelper')}
            />
            <FormNumberField
              name="watering_interval_days"
              control={control}
              label={t('pages.phaseSequences.wateringIntervalLabel')}
              min={1}
              step={1}
              suffix={t('common.days')}
              helperText={t('pages.phaseSequences.wateringIntervalHelper')}
            />
          </Box>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: { xs: 1, sm: 2 } }}>
            <FormSelectField
              name="stress_tolerance"
              control={control}
              label={t('pages.phaseSequences.stressTolerance')}
              options={stressLevels.map((v) => ({
                value: v,
                label: t(`enums.stressLevel.${v}`),
              }))}
            />
            <FormTextField
              name="tags"
              control={control}
              label={t('pages.phaseSequences.tags')}
              helperText={t('pages.phaseSequences.tagsHelper')}
            />
          </Box>

          <FormActions
            onCancel={onClose}
            loading={saving}
            saveLabel={isEdit ? t('common.save') : t('common.create')}
          />
        </form>
      </DialogContent>
    </Dialog>
  );
}
