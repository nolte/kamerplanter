import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Typography from '@mui/material/Typography';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as taskApi from '@/api/endpoints/tasks';

const categories = [
  'maintenance', 'watering', 'feeding', 'training', 'pest_control',
  'harvest', 'pruning', 'transplant', 'monitoring', 'cleaning',
] as const;

const difficultyLevels = ['beginner', 'intermediate', 'expert'] as const;

const schema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().nullable(),
  category: z.enum(categories),
  difficulty_level: z.enum(difficultyLevels),
  version: z.string(),
  tags: z.string(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function WorkflowCreateDialog({ open, onClose, onCreated }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      description: null,
      category: 'maintenance',
      difficulty_level: 'intermediate',
      version: '1.0',
      tags: '',
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
      await taskApi.createWorkflow({
        name: data.name,
        description: data.description,
        category: data.category,
        difficulty_level: data.difficulty_level,
        version: data.version,
        tags: data.tags ? data.tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
      });
      notification.success(t('pages.tasks.workflowCreated'));
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
      <DialogTitle>{t('pages.tasks.createWorkflow')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.tasks.createWorkflowIntro')}
        </Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField name="name" control={control} label={t('pages.tasks.workflowName')} required autoFocus />
          <FormTextField name="description" control={control} label={t('common.description')} multiline rows={3} />
          <FormSelectField
            name="category"
            control={control}
            label={t('pages.tasks.category')}
            options={categories.map((v) => ({ value: v, label: t(`enums.taskCategory.${v}`) }))}
          />
          <FormSelectField
            name="difficulty_level"
            control={control}
            label={t('pages.tasks.difficultyLevel')}
            options={difficultyLevels.map((v) => ({ value: v, label: t(`enums.difficultyLevel.${v}`) }))}
          />
          <FormTextField name="version" control={control} label={t('pages.tasks.version')} />
          <FormTextField name="tags" control={control} label={t('pages.tasks.tags')} helperText={t('pages.tasks.tagsHelper')} />
          <FormActions onCancel={onClose} loading={saving} saveLabel={t('common.create')} />
        </form>
      </DialogContent>
    </Dialog>
  );
}
