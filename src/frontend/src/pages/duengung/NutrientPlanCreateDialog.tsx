import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormChipInput from '@/components/form/FormChipInput';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/nutrient-plans';
import type { NutrientPlanCreate, ScheduleMode } from '@/api/types';

const substrateTypes = [
  'soil',
  'coco',
  'clay_pebbles',
  'perlite',
  'living_soil',
  'peat',
  'rockwool_slab',
  'rockwool_plug',
  'vermiculite',
  'none',
  'orchid_bark',
  'pon_mineral',
  'sphagnum',
  'hydro_solution',
] as const;

const applicationMethods = ['drench', 'foliar', 'top_dress'] as const;

const WEEKDAY_KEYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] as const;

const schema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().max(2000),
  recommended_substrate_type: z.enum(substrateTypes).nullable(),
  author: z.string().max(200),
  is_template: z.boolean(),
  tags: z.array(z.string()),
  // Watering schedule fields
  schedule_mode: z.enum(['weekdays', 'interval']),
  weekday_schedule: z.array(z.number()),
  interval_days: z.number().min(1).max(90).nullable(),
  preferred_time: z.string().max(5),
  application_method: z.enum(applicationMethods),
  reminder_hours_before: z.number().min(0).max(24),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function NutrientPlanCreateDialog({ open, onClose, onCreated }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset, watch, setValue } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      description: '',
      recommended_substrate_type: null,
      author: '',
      is_template: false,
      tags: [],
      schedule_mode: 'weekdays',
      weekday_schedule: [],
      interval_days: null,
      preferred_time: '',
      application_method: 'drench',
      reminder_hours_before: 2,
    },
  });
  useEffect(() => {
    if (!open) {
      reset();
    }
  }, [open, reset]);


  const scheduleMode = watch('schedule_mode');
  const weekdaySchedule = watch('weekday_schedule');

  const handleWeekdayToggle = (dayIndex: number) => {
    const current = weekdaySchedule;
    if (current.includes(dayIndex)) {
      setValue('weekday_schedule', current.filter((d) => d !== dayIndex), { shouldDirty: true });
    } else {
      setValue('weekday_schedule', [...current, dayIndex].sort(), { shouldDirty: true });
    }
  };

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      const hasSchedule =
        (data.schedule_mode === 'weekdays' && data.weekday_schedule.length > 0) ||
        (data.schedule_mode === 'interval' && data.interval_days != null && data.interval_days > 0);

      const basePayload: NutrientPlanCreate = {
        name: data.name,
        description: data.description,
        recommended_substrate_type: data.recommended_substrate_type,
        author: data.author,
        is_template: data.is_template,
        tags: data.tags,
      };

      if (hasSchedule) {
        basePayload.watering_schedule = {
          schedule_mode: data.schedule_mode,
          weekday_schedule: data.weekday_schedule,
          interval_days: data.interval_days,
          preferred_time: data.preferred_time || null,
          application_method: data.application_method,
          reminder_hours_before: data.reminder_hours_before,
          times_per_day: 1,
        };
      }
      await api.createNutrientPlan(basePayload);
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

          {/* Watering Schedule Section */}
          <Accordion
            sx={{ mt: 2, mb: 2 }}
            data-testid="watering-schedule-section"
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>{t('pages.wateringSchedule.title')}</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {/* Schedule Mode Toggle */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {t('pages.wateringSchedule.mode')}
                </Typography>
                <Controller
                  name="schedule_mode"
                  control={control}
                  render={({ field }) => (
                    <ToggleButtonGroup
                      value={field.value}
                      exclusive
                      onChange={(_, value: ScheduleMode | null) => {
                        if (value) field.onChange(value);
                      }}
                      size="small"
                      fullWidth
                      data-testid="schedule-mode-toggle"
                    >
                      <ToggleButton value="weekdays">
                        {t('pages.wateringSchedule.weekdays')}
                      </ToggleButton>
                      <ToggleButton value="interval">
                        {t('pages.wateringSchedule.interval')}
                      </ToggleButton>
                    </ToggleButtonGroup>
                  )}
                />
              </Box>

              {/* Weekday Checkboxes */}
              {scheduleMode === 'weekdays' && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                    {t('pages.wateringSchedule.weekdays')}
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {WEEKDAY_KEYS.map((dayKey, index) => (
                      <FormControlLabel
                        key={dayKey}
                        control={
                          <Checkbox
                            checked={weekdaySchedule.includes(index)}
                            onChange={() => handleWeekdayToggle(index)}
                            size="small"
                            data-testid={`weekday-${dayKey}`}
                          />
                        }
                        label={t(`pages.wateringSchedule.${dayKey}`)}
                      />
                    ))}
                  </Box>
                </Box>
              )}

              {/* Interval Days */}
              {scheduleMode === 'interval' && (
                <FormNumberField
                  name="interval_days"
                  control={control}
                  label={t('pages.wateringSchedule.intervalDays')}
                  min={1}
                  max={90}
                  step={1}
                />
              )}

              {/* Preferred Time */}
              <Controller
                name="preferred_time"
                control={control}
                render={({ field, fieldState: { error } }) => (
                  <Box sx={{ mb: 2 }}>
                    <label htmlFor="preferred-time">
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                        {t('pages.wateringSchedule.preferredTime')}
                      </Typography>
                    </label>
                    <input
                      id="preferred-time"
                      type="time"
                      value={field.value}
                      onChange={field.onChange}
                      onBlur={field.onBlur}
                      data-testid="preferred-time-input"
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        fontSize: '1rem',
                        border: error ? '1px solid red' : '1px solid rgba(0,0,0,0.23)',
                        borderRadius: '4px',
                      }}
                    />
                    {error?.message && (
                      <Typography variant="caption" color="error">
                        {error.message}
                      </Typography>
                    )}
                  </Box>
                )}
              />

              {/* Application Method */}
              <FormSelectField
                name="application_method"
                control={control}
                label={t('pages.wateringSchedule.applicationMethod')}
                options={applicationMethods.map((v) => ({
                  value: v,
                  label: t(`enums.applicationMethod.${v}`),
                }))}
              />

              {/* Reminder Hours Before */}
              <FormNumberField
                name="reminder_hours_before"
                control={control}
                label={t('pages.wateringSchedule.reminderHoursBefore')}
                min={0}
                max={24}
                step={1}
              />
            </AccordionDetails>
          </Accordion>

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
