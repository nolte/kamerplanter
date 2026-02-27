import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Typography from '@mui/material/Typography';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import CircularProgress from '@mui/material/CircularProgress';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as taskApi from '@/api/endpoints/tasks';
import * as plantApi from '@/api/endpoints/plantInstances';
import type { PlantInstance } from '@/api/types';

const categories = [
  'maintenance', 'watering', 'feeding', 'training', 'pest_control',
  'harvest', 'pruning', 'transplant', 'monitoring', 'cleaning',
] as const;

const priorities = ['low', 'medium', 'high', 'critical'] as const;

const schema = z.object({
  name: z.string().min(1).max(200),
  instruction: z.string(),
  category: z.enum(categories),
  plant_key: z.string().nullable(),
  due_date: z.string().nullable(),
  priority: z.enum(priorities),
  estimated_duration_minutes: z.union([z.number().int().min(1), z.literal('')]).nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function TaskCreateDialog({ open, onClose, onCreated }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const [plants, setPlants] = useState<PlantInstance[]>([]);
  const [loadingPlants, setLoadingPlants] = useState(false);

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      instruction: '',
      category: 'maintenance',
      plant_key: null,
      due_date: null,
      priority: 'medium',
      estimated_duration_minutes: null,
    },
  });

  useEffect(() => {
    if (!open) return;
    const loadPlants = async () => {
      setLoadingPlants(true);
      try {
        const data = await plantApi.listPlantInstances(0, 200);
        setPlants(data);
      } catch (err) {
        handleError(err);
      } finally {
        setLoadingPlants(false);
      }
    };
    loadPlants();
  }, [open, handleError]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      await taskApi.createTask({
        name: data.name,
        instruction: data.instruction || undefined,
        category: data.category,
        plant_key: data.plant_key,
        due_date: data.due_date,
        priority: data.priority,
        estimated_duration_minutes:
          typeof data.estimated_duration_minutes === 'number'
            ? data.estimated_duration_minutes
            : undefined,
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
      <DialogTitle>{t('pages.tasks.createTask')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.tasks.createIntro')}
        </Typography>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField
            name="name"
            control={control}
            label={t('pages.tasks.name')}
            required
          />
          <FormTextField
            name="instruction"
            control={control}
            label={t('pages.tasks.instruction')}
            multiline
            rows={3}
          />
          <FormSelectField
            name="category"
            control={control}
            label={t('pages.tasks.category')}
            options={categories.map((v) => ({
              value: v,
              label: t(`enums.taskCategory.${v}`),
            }))}
          />
          <Controller
            name="plant_key"
            control={control}
            render={({ field }) => (
              <Autocomplete
                options={plants}
                getOptionLabel={(p) =>
                  p.plant_name
                    ? `${p.instance_id} - ${p.plant_name}`
                    : p.instance_id
                }
                loading={loadingPlants}
                value={plants.find((p) => p.key === field.value) ?? null}
                onChange={(_, value) => field.onChange(value?.key ?? null)}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label={t('pages.tasks.plant')}
                    sx={{ mb: 2 }}
                    slotProps={{
                      input: {
                        ...params.InputProps,
                        endAdornment: (
                          <>
                            {loadingPlants && <CircularProgress size={16} />}
                            {params.InputProps.endAdornment}
                          </>
                        ),
                      },
                    }}
                    data-testid="form-field-plant_key"
                  />
                )}
              />
            )}
          />
          <FormTextField
            name="due_date"
            control={control}
            label={t('pages.tasks.dueDate')}
            type="date"
          />
          <FormSelectField
            name="priority"
            control={control}
            label={t('pages.tasks.priority')}
            options={priorities.map((v) => ({
              value: v,
              label: t(`enums.taskPriority.${v}`),
            }))}
          />
          <FormNumberField
            name="estimated_duration_minutes"
            control={control}
            label={t('pages.tasks.estimatedDuration')}
            min={1}
            step={1}
            helperText={t('pages.tasks.estimatedDurationHelper')}
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
