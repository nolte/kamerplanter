import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Stepper from '@mui/material/Stepper';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import Box from '@mui/material/Box';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import Typography from '@mui/material/Typography';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Form from '@/components/form/Form';
import FormTextField from '@/components/form/FormTextField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSelectField from '@/components/form/FormSelectField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormTimeField from '@/components/form/FormTimeField';
import type {
  DeliveryChannel,
  DeliveryChannelCreate,
  ApplicationMethod,
  ScheduleMode,
  WateringSchedule,
  MethodParams,
} from '@/api/types';

const APPLICATION_METHODS: ApplicationMethod[] = [
  'fertigation',
  'drench',
  'foliar',
  'top_dress',
];

const SCHEDULE_MODES: ScheduleMode[] = ['weekdays', 'interval'];

const WEEKDAY_KEYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] as const;

// ── Zod schema ───────────────────────────────────────────────────
const schema = z.object({
  channel_id: z.string().min(1),
  label: z.string(),
  application_method: z.enum(['fertigation', 'drench', 'foliar', 'top_dress']),
  enabled: z.boolean(),
  notes: z.string(),
  target_ec_ms: z.number().min(0).max(10).nullable(),
  target_ph: z.number().min(0).max(14).nullable(),

  // Method params (all kept; only the active method's values are read on submit)
  runs_per_day: z.number().int().min(1).max(24),
  duration_seconds: z.number().int().min(1).max(7200),
  volume_per_feeding_liters: z.number().gt(0).max(100),
  volume_per_spray_liters: z.number().gt(0).max(10),
  grams_per_plant: z.number().min(0).nullable(),
  grams_per_m2: z.number().min(0).nullable(),

  // Schedule
  schedule_enabled: z.boolean(),
  schedule_mode: z.enum(['weekdays', 'interval']),
  weekday_schedule: z.array(z.number().int().min(0).max(6)),
  interval_days: z.number().int().min(1).max(90),
  preferred_time: z.string(),
  reminder_hours_before: z.number().int().min(0).max(24),
  times_per_day: z.number().int().min(1).max(6),
});

type FormData = z.infer<typeof schema>;

const DEFAULTS: FormData = {
  channel_id: '',
  label: '',
  application_method: 'drench',
  enabled: true,
  notes: '',
  target_ec_ms: null,
  target_ph: null,
  runs_per_day: 1,
  duration_seconds: 300,
  volume_per_feeding_liters: 1.0,
  volume_per_spray_liters: 0.5,
  grams_per_plant: null,
  grams_per_m2: null,
  schedule_enabled: false,
  schedule_mode: 'weekdays',
  weekday_schedule: [],
  interval_days: 3,
  preferred_time: '08:00',
  reminder_hours_before: 2,
  times_per_day: 1,
};

interface Props {
  open: boolean;
  onClose: () => void;
  onSave: (channel: DeliveryChannelCreate) => void;
  existingChannel?: DeliveryChannel | null;
  existingIds?: string[];
}

function buildDefaults(channel: DeliveryChannel | null | undefined): FormData {
  if (!channel) {
    return { ...DEFAULTS };
  }
  const mp = channel.method_params;
  const base: FormData = {
    ...DEFAULTS,
    channel_id: channel.channel_id,
    label: channel.label,
    application_method: channel.application_method as FormData['application_method'],
    enabled: channel.enabled,
    notes: channel.notes ?? '',
    target_ec_ms: channel.target_ec_ms,
    target_ph: channel.target_ph,
  };
  if (mp) {
    if (mp.method === 'fertigation') {
      base.runs_per_day = mp.runs_per_day;
      base.duration_seconds = mp.duration_seconds;
    } else if (mp.method === 'drench') {
      base.volume_per_feeding_liters = mp.volume_per_feeding_liters;
    } else if (mp.method === 'foliar') {
      base.volume_per_spray_liters = mp.volume_per_spray_liters;
    } else if (mp.method === 'top_dress') {
      base.grams_per_plant = mp.grams_per_plant;
      base.grams_per_m2 = mp.grams_per_m2;
    }
  }
  if (channel.schedule) {
    base.schedule_enabled = true;
    base.schedule_mode = channel.schedule.schedule_mode;
    base.weekday_schedule = channel.schedule.weekday_schedule;
    base.interval_days = channel.schedule.interval_days ?? 3;
    base.preferred_time = channel.schedule.preferred_time ?? '08:00';
    base.reminder_hours_before = channel.schedule.reminder_hours_before;
    base.times_per_day = channel.schedule.times_per_day ?? 1;
  }
  return base;
}

export default function DeliveryChannelDialog({
  open,
  onClose,
  onSave,
  existingChannel,
  existingIds = [],
}: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const [activeStep, setActiveStep] = useState(0);
  const isEdit = !!existingChannel;

  const { control, handleSubmit, reset, watch, formState } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: buildDefaults(existingChannel),
    mode: 'onChange',
  });

  useEffect(() => {
    if (open) {
      reset(buildDefaults(existingChannel));
      setActiveStep(0);
    }
  }, [open, existingChannel, reset]);

  const channelIdValue = watch('channel_id');
  const methodValue = watch('application_method');
  const scheduleEnabled = watch('schedule_enabled');
  const scheduleModeValue = watch('schedule_mode');

  const idCollisionError =
    !isEdit &&
    channelIdValue.length > 0 &&
    existingIds.includes(channelIdValue)
      ? t('pages.deliveryChannels.channelIdExists')
      : '';

  const canProceed = channelIdValue.length > 0 && !idCollisionError;

  const steps = [
    t('pages.deliveryChannels.stepMethod'),
    t('pages.deliveryChannels.stepParams'),
    t('pages.deliveryChannels.stepSchedule'),
  ];

  const buildSchedule = (data: FormData): WateringSchedule | null => {
    if (!data.schedule_enabled) return null;
    return {
      schedule_mode: data.schedule_mode,
      weekday_schedule:
        data.schedule_mode === 'weekdays' ? data.weekday_schedule : [],
      interval_days:
        data.schedule_mode === 'interval' ? data.interval_days : null,
      preferred_time: data.preferred_time || null,
      application_method: data.application_method,
      reminder_hours_before: data.reminder_hours_before,
      times_per_day: data.times_per_day,
    };
  };

  const buildMethodParams = (data: FormData): MethodParams | null => {
    switch (data.application_method) {
      case 'fertigation':
        return {
          method: 'fertigation',
          runs_per_day: data.runs_per_day,
          duration_seconds: data.duration_seconds,
          flow_rate_ml_min: null,
        };
      case 'drench':
        return {
          method: 'drench',
          volume_per_feeding_liters: data.volume_per_feeding_liters,
        };
      case 'foliar':
        return {
          method: 'foliar',
          volume_per_spray_liters: data.volume_per_spray_liters,
        };
      case 'top_dress':
        return {
          method: 'top_dress',
          grams_per_plant: data.grams_per_plant,
          grams_per_m2: data.grams_per_m2,
        };
      default:
        return null;
    }
  };

  const onSubmit = (data: FormData) => {
    if (idCollisionError) return;
    const channel: DeliveryChannelCreate = {
      channel_id: data.channel_id,
      label: data.label,
      application_method: data.application_method,
      enabled: data.enabled,
      notes: data.notes || null,
      target_ec_ms: data.target_ec_ms,
      target_ph: data.target_ph,
      method_params: buildMethodParams(data),
      schedule: buildSchedule(data),
    };
    onSave(channel);
  };

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="delivery-channel-dialog-title"
      data-testid="delivery-channel-dialog"
    >
      <DialogTitle id="delivery-channel-dialog-title">
        {isEdit
          ? t('pages.deliveryChannels.editChannel')
          : t('pages.deliveryChannels.addChannel')}
      </DialogTitle>
      <Form onSubmit={handleSubmit(onSubmit)}>
        <DialogContent>
          <Stepper activeStep={activeStep} sx={{ mb: 3, mt: 1 }}>
            {steps.map((s) => (
              <Step key={s}>
                <StepLabel>{s}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {activeStep === 0 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <FormTextField
                name="channel_id"
                control={control}
                label={t('pages.deliveryChannels.channelId')}
                required
                disabled={isEdit}
                helperText={idCollisionError || undefined}
                autoFocus
              />
              <FormTextField
                name="label"
                control={control}
                label={t('pages.deliveryChannels.label')}
              />
              <FormSelectField
                name="application_method"
                control={control}
                label={t('pages.deliveryChannels.applicationMethod')}
                options={APPLICATION_METHODS.map((m) => ({
                  value: m,
                  label: t(`enums.applicationMethod.${m}`),
                }))}
              />
              <FormSwitchField
                name="enabled"
                control={control}
                label={t('pages.deliveryChannels.enabled')}
              />
              <FormNumberField
                name="target_ec_ms"
                control={control}
                label={t('pages.deliveryChannels.targetEc')}
                min={0}
                max={10}
                step={0.1}
                inputMode="decimal"
                suffix="mS/cm"
                helperText={t('pages.deliveryChannels.targetEcHelper')}
              />
              <FormNumberField
                name="target_ph"
                control={control}
                label={t('pages.deliveryChannels.targetPh')}
                min={0}
                max={14}
                step={0.1}
                inputMode="decimal"
                helperText={t('pages.deliveryChannels.targetPhHelper')}
              />
              <FormTextField
                name="notes"
                control={control}
                label={t('pages.deliveryChannels.notes')}
                multiline
                rows={2}
              />
            </Box>
          )}

          {activeStep === 1 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {methodValue === 'fertigation' && (
                <>
                  <FormNumberField
                    name="runs_per_day"
                    control={control}
                    label={t('pages.deliveryChannels.fertigation.runsPerDay')}
                    min={1}
                    max={24}
                    step={1}
                    inputMode="numeric"
                    helperText={t('pages.deliveryChannels.runsPerDayHelper')}
                  />
                  <FormNumberField
                    name="duration_seconds"
                    control={control}
                    label={t(
                      'pages.deliveryChannels.fertigation.durationSeconds',
                    )}
                    min={1}
                    max={7200}
                    step={1}
                    inputMode="numeric"
                    helperText={t(
                      'pages.deliveryChannels.durationSecondsHelper',
                    )}
                  />
                </>
              )}
              {methodValue === 'drench' && (
                <FormNumberField
                  name="volume_per_feeding_liters"
                  control={control}
                  label={t('pages.deliveryChannels.drench.volumePerFeeding')}
                  min={0.1}
                  max={100}
                  step={0.1}
                  inputMode="decimal"
                  suffix="L"
                />
              )}
              {methodValue === 'foliar' && (
                <FormNumberField
                  name="volume_per_spray_liters"
                  control={control}
                  label={t('pages.deliveryChannels.foliar.volumePerSpray')}
                  min={0.1}
                  max={10}
                  step={0.1}
                  inputMode="decimal"
                  suffix="L"
                />
              )}
              {methodValue === 'top_dress' && (
                <>
                  <FormNumberField
                    name="grams_per_plant"
                    control={control}
                    label={t('pages.deliveryChannels.topDress.gramsPerPlant')}
                    min={0}
                    step={0.5}
                    inputMode="decimal"
                    suffix="g"
                  />
                  <FormNumberField
                    name="grams_per_m2"
                    control={control}
                    label={t('pages.deliveryChannels.topDress.gramsPerM2')}
                    min={0}
                    step={0.5}
                    inputMode="decimal"
                    suffix="g/m²"
                  />
                </>
              )}
            </Box>
          )}

          {activeStep === 2 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <FormSwitchField
                name="schedule_enabled"
                control={control}
                label={t('pages.deliveryChannels.scheduleEnabled')}
              />
              <Typography variant="body2" color="text.secondary">
                {t('pages.deliveryChannels.scheduleHint')}
              </Typography>

              {scheduleEnabled && (
                <>
                  <Box>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 1 }}
                    >
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
                        >
                          {SCHEDULE_MODES.map((mode) => (
                            <ToggleButton key={mode} value={mode}>
                              {t(`pages.wateringSchedule.${mode}`)}
                            </ToggleButton>
                          ))}
                        </ToggleButtonGroup>
                      )}
                    />
                  </Box>

                  {scheduleModeValue === 'weekdays' && (
                    <Box>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ mb: 0.5 }}
                      >
                        {t('pages.wateringSchedule.weekdays')}
                      </Typography>
                      <Controller
                        name="weekday_schedule"
                        control={control}
                        render={({ field }) => (
                          <Box
                            sx={{
                              display: 'flex',
                              flexWrap: 'wrap',
                              gap: 0.5,
                            }}
                          >
                            {WEEKDAY_KEYS.map((dayKey, index) => {
                              const checked = field.value.includes(index);
                              return (
                                <FormControlLabel
                                  key={dayKey}
                                  control={
                                    <Checkbox
                                      checked={checked}
                                      onChange={() => {
                                        const next = checked
                                          ? field.value.filter(
                                              (d: number) => d !== index,
                                            )
                                          : [...field.value, index].sort(
                                              (a: number, b: number) => a - b,
                                            );
                                        field.onChange(next);
                                      }}
                                      size="small"
                                    />
                                  }
                                  label={t(
                                    `pages.wateringSchedule.${dayKey}`,
                                  )}
                                />
                              );
                            })}
                          </Box>
                        )}
                      />
                    </Box>
                  )}

                  {scheduleModeValue === 'interval' && (
                    <FormNumberField
                      name="interval_days"
                      control={control}
                      label={t('pages.wateringSchedule.intervalDays')}
                      min={1}
                      max={90}
                      step={1}
                      inputMode="numeric"
                    />
                  )}

                  <FormTimeField
                    name="preferred_time"
                    control={control}
                    label={t('pages.wateringSchedule.preferredTime')}
                  />

                  <FormNumberField
                    name="reminder_hours_before"
                    control={control}
                    label={t('pages.wateringSchedule.reminderHoursBefore')}
                    min={0}
                    max={24}
                    step={1}
                    inputMode="numeric"
                  />

                  <FormNumberField
                    name="times_per_day"
                    control={control}
                    label={t('pages.wateringSchedule.timesPerDay')}
                    min={1}
                    max={6}
                    step={1}
                    inputMode="numeric"
                  />
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>{t('common.cancel')}</Button>
          {activeStep > 0 && (
            <Button onClick={() => setActiveStep((s) => s - 1)}>
              {t('common.back')}
            </Button>
          )}
          {activeStep < steps.length - 1 ? (
            <Button
              variant="contained"
              onClick={() => setActiveStep((s) => s + 1)}
              disabled={!canProceed}
            >
              {t('common.next')}
            </Button>
          ) : (
            <Button
              type="submit"
              variant="contained"
              disabled={!canProceed || formState.isSubmitting}
            >
              {t(isEdit ? 'common.save' : 'common.create')}
            </Button>
          )}
        </DialogActions>
      </Form>
    </Dialog>
  );
}
