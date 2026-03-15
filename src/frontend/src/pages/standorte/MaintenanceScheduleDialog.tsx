import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as tankApi from '@/api/endpoints/tanks';
import type { MaintenanceSchedule } from '@/api/types';

const maintenanceTypes = [
  'water_change', 'cleaning', 'sanitization',
  'calibration', 'filter_change', 'pump_inspection',
] as const;

const priorities = ['low', 'medium', 'high', 'critical'] as const;

const schema = z.object({
  maintenance_type: z.enum(maintenanceTypes),
  interval_days: z.number().int().min(1),
  reminder_days_before: z.number().int().min(0),
  is_active: z.boolean(),
  priority: z.enum(priorities),
  auto_create_task: z.boolean(),
  instructions: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  tankKey: string;
  schedule?: MaintenanceSchedule;
  onSaved: () => void;
}

export default function MaintenanceScheduleDialog({ open, onClose, tankKey, schedule, onSaved }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const isEdit = !!schedule;

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      maintenance_type: 'water_change',
      interval_days: 7,
      reminder_days_before: 1,
      is_active: true,
      priority: 'medium',
      auto_create_task: false,
      instructions: null,
    },
  });

  useEffect(() => {
    if (open && schedule) {
      reset({
        maintenance_type: schedule.maintenance_type as FormData['maintenance_type'],
        interval_days: schedule.interval_days,
        reminder_days_before: schedule.reminder_days_before,
        is_active: schedule.is_active,
        priority: schedule.priority as FormData['priority'],
        auto_create_task: schedule.auto_create_task,
        instructions: schedule.instructions,
      });
    } else if (open) {
      reset({
        maintenance_type: 'water_change',
        interval_days: 7,
        reminder_days_before: 1,
        is_active: true,
        priority: 'medium',
        auto_create_task: false,
        instructions: null,
      });
    }
  }, [open, schedule, reset]);

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      if (isEdit && schedule) {
        await tankApi.updateSchedule(tankKey, schedule.key, data);
        notification.success(t('pages.tanks.scheduleUpdated'));
      } else {
        await tankApi.createSchedule(tankKey, data);
        notification.success(t('pages.tanks.scheduleCreated'));
      }
      onSaved();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {isEdit ? t('pages.tanks.editSchedule') : t('pages.tanks.createSchedule')}
      </DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            {t('pages.tanks.sectionScheduleType')}
          </Typography>
          <FormSelectField
            name="maintenance_type"
            control={control}
            label={t('pages.tanks.maintenanceType')}
            options={maintenanceTypes.map((v) => ({
              value: v,
              label: t(`enums.maintenanceType.${v}`),
            }))}
          />
          <FormSelectField
            name="priority"
            control={control}
            label={t('pages.tanks.priority')}
            options={priorities.map((v) => ({
              value: v,
              label: t(`enums.maintenancePriority.${v}`),
            }))}
          />
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.tanks.sectionTiming')}
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormNumberField
              name="interval_days"
              control={control}
              label={t('pages.tanks.intervalDays')}
              helperText={t('pages.tanks.intervalDaysHelper')}
              min={1}
              step={1}
            />
            <FormNumberField
              name="reminder_days_before"
              control={control}
              label={t('pages.tanks.reminderDaysBefore')}
              helperText={t('pages.tanks.reminderDaysBeforeHelper')}
              min={0}
              step={1}
            />
          </Box>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.tanks.sectionAutomation')}
          </Typography>
          <FormSwitchField
            name="is_active"
            control={control}
            label={t('pages.tanks.active')}
          />
          <FormSwitchField
            name="auto_create_task"
            control={control}
            label={t('pages.tanks.autoCreateTask')}
          />
          <FormTextField
            name="instructions"
            control={control}
            label={t('pages.tanks.instructions')}
            multiline
            rows={3}
          />
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
