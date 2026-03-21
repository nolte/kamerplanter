import { useState, useEffect } from 'react';
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
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';

import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Checkbox from '@mui/material/Checkbox';
import Typography from '@mui/material/Typography';
import type { DeliveryChannel, DeliveryChannelCreate, ApplicationMethod, ScheduleMode, WateringSchedule } from '@/api/types';

const APPLICATION_METHODS: ApplicationMethod[] = ['fertigation', 'drench', 'foliar', 'top_dress'];

const WEEKDAY_KEYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] as const;

interface Props {
  open: boolean;
  onClose: () => void;
  onSave: (channel: DeliveryChannelCreate) => void;
  existingChannel?: DeliveryChannel | null;
  existingIds?: string[];
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

  const [channelId, setChannelId] = useState('');
  const [label, setLabel] = useState('');
  const [method, setMethod] = useState<ApplicationMethod>('drench');
  const [enabled, setEnabled] = useState(true);
  const [notes, setNotes] = useState('');
  const [targetEc, setTargetEc] = useState<string>('');
  const [targetPh, setTargetPh] = useState<string>('');

  // Method params
  const [runsPerDay, setRunsPerDay] = useState(1);
  const [durationSeconds, setDurationSeconds] = useState(300);
  const [volumePerFeeding, setVolumePerFeeding] = useState(1.0);
  const [volumePerSpray, setVolumePerSpray] = useState(0.5);
  const [gramsPerPlant, setGramsPerPlant] = useState<string>('');
  const [gramsPerM2, setGramsPerM2] = useState<string>('');


  // Schedule state
  const [scheduleEnabled, setScheduleEnabled] = useState(false);
  const [scheduleMode, setScheduleMode] = useState<ScheduleMode>('weekdays');
  const [weekdaySchedule, setWeekdaySchedule] = useState<number[]>([]);
  const [intervalDays, setIntervalDays] = useState<number>(3);
  const [preferredTime, setPreferredTime] = useState<string>('08:00');
  const [reminderHoursBefore, setReminderHoursBefore] = useState<number>(2);
  const [timesPerDay, setTimesPerDay] = useState<number>(1);

  useEffect(() => {
    if (open) {
      if (existingChannel) {
        setChannelId(existingChannel.channel_id);
        setLabel(existingChannel.label);
        setMethod(existingChannel.application_method);
        setEnabled(existingChannel.enabled);
        setNotes(existingChannel.notes || '');
        setTargetEc(existingChannel.target_ec_ms?.toString() ?? '');
        setTargetPh(existingChannel.target_ph?.toString() ?? '');
        if (existingChannel.method_params) {
          const mp = existingChannel.method_params;
          if (mp.method === 'fertigation') {
            setRunsPerDay(mp.runs_per_day);
            setDurationSeconds(mp.duration_seconds);
          } else if (mp.method === 'drench') {
            setVolumePerFeeding(mp.volume_per_feeding_liters);
          } else if (mp.method === 'foliar') {
            setVolumePerSpray(mp.volume_per_spray_liters);
          } else if (mp.method === 'top_dress') {
            setGramsPerPlant(mp.grams_per_plant?.toString() ?? '');
            setGramsPerM2(mp.grams_per_m2?.toString() ?? '');
          }
        }
        // Initialize schedule state from existing channel
        if (existingChannel.schedule) {
          setScheduleEnabled(true);
          setScheduleMode(existingChannel.schedule.schedule_mode);
          setWeekdaySchedule(existingChannel.schedule.weekday_schedule);
          setIntervalDays(existingChannel.schedule.interval_days ?? 3);
          setPreferredTime(existingChannel.schedule.preferred_time ?? '08:00');
          setReminderHoursBefore(existingChannel.schedule.reminder_hours_before);
          setTimesPerDay(existingChannel.schedule.times_per_day ?? 1);
        } else {
          setScheduleEnabled(false);
          setScheduleMode('weekdays');
          setWeekdaySchedule([]);
          setIntervalDays(3);
          setPreferredTime('08:00');
          setReminderHoursBefore(2);
          setTimesPerDay(1);
        }
      } else {
        setChannelId('');
        setLabel('');
        setMethod('drench');
        setEnabled(true);
        setNotes('');
        setTargetEc('');
        setTargetPh('');
        setRunsPerDay(1);
        setDurationSeconds(300);
        setVolumePerFeeding(1.0);
        setVolumePerSpray(0.5);
        setGramsPerPlant('');
        setGramsPerM2('');
        setScheduleEnabled(false);
        setScheduleMode('weekdays');
        setWeekdaySchedule([]);
        setIntervalDays(3);
        setPreferredTime('08:00');
        setReminderHoursBefore(2);
        setTimesPerDay(1);
      }
      setActiveStep(0);
    }
  }, [open, existingChannel]);

  const steps = [
    t('pages.deliveryChannels.stepMethod'),
    t('pages.deliveryChannels.stepParams'),
    t('pages.deliveryChannels.stepSchedule'),
  ];

  const idError =
    !isEdit &&
    channelId.length > 0 &&
    existingIds.includes(channelId)
      ? t('pages.deliveryChannels.channelIdExists')
      : '';

  const canSave = channelId.length > 0 && !idError;

  const handleWeekdayToggle = (dayIndex: number) => {
    setWeekdaySchedule((prev) =>
      prev.includes(dayIndex)
        ? prev.filter((d) => d !== dayIndex)
        : [...prev, dayIndex].sort(),
    );
  };

  const buildSchedule = (): WateringSchedule | null => {
    if (!scheduleEnabled) return null;
    return {
      schedule_mode: scheduleMode,
      weekday_schedule: scheduleMode === 'weekdays' ? weekdaySchedule : [],
      interval_days: scheduleMode === 'interval' ? intervalDays : null,
      preferred_time: preferredTime || null,
      application_method: method,
      reminder_hours_before: reminderHoursBefore,
      times_per_day: timesPerDay,
    };
  };

  const handleSave = () => {
    const methodParams = (() => {
      switch (method) {
        case 'fertigation':
          return { method: 'fertigation' as const, runs_per_day: runsPerDay, duration_seconds: durationSeconds, flow_rate_ml_min: null };
        case 'drench':
          return { method: 'drench' as const, volume_per_feeding_liters: volumePerFeeding };
        case 'foliar':
          return { method: 'foliar' as const, volume_per_spray_liters: volumePerSpray };
        case 'top_dress':
          return {
            method: 'top_dress' as const,
            grams_per_plant: gramsPerPlant ? parseFloat(gramsPerPlant) : null,
            grams_per_m2: gramsPerM2 ? parseFloat(gramsPerM2) : null,
          };
        default:
          return null;
      }
    })();

    const channel: DeliveryChannelCreate = {
      channel_id: channelId,
      label,
      application_method: method,
      enabled,
      notes: notes || null,
      target_ec_ms: targetEc ? parseFloat(targetEc) : null,
      target_ph: targetPh ? parseFloat(targetPh) : null,
      method_params: methodParams,
      schedule: buildSchedule(),
    };
    onSave(channel);
  };

  return (
    <Dialog fullScreen={fullScreen} open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {isEdit
          ? t('pages.deliveryChannels.editChannel')
          : t('pages.deliveryChannels.addChannel')}
      </DialogTitle>
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
            <TextField
              label={t('pages.deliveryChannels.channelId')}
              value={channelId}
              onChange={(e) => setChannelId(e.target.value)}
              error={!!idError}
              helperText={idError}
              disabled={isEdit}
              required
              size="small"
            />
            <TextField
              label={t('pages.deliveryChannels.label')}
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              size="small"
            />
            <TextField
              select
              label={t('pages.deliveryChannels.applicationMethod')}
              value={method}
              onChange={(e) => setMethod(e.target.value as ApplicationMethod)}
              size="small"
            >
              {APPLICATION_METHODS.map((m) => (
                <MenuItem key={m} value={m}>
                  {t(`enums.applicationMethod.${m}`)}
                </MenuItem>
              ))}
            </TextField>
            <FormControlLabel
              control={<Switch checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />}
              label={t('pages.deliveryChannels.enabled')}
            />
            <TextField
              label={t('pages.deliveryChannels.targetEc')}
              type="number"
              value={targetEc}
              onChange={(e) => setTargetEc(e.target.value)}
              size="small"
              inputProps={{ min: 0, max: 10, step: 0.1, inputMode: 'decimal' }}
              slotProps={{
                input: {
                  endAdornment: <Typography variant="caption" sx={{ whiteSpace: 'nowrap', ml: 0.5 }}>mS/cm</Typography>,
                },
              }}
              helperText={t('pages.deliveryChannels.targetEcHelper')}
            />
            <TextField
              label={t('pages.deliveryChannels.targetPh')}
              type="number"
              value={targetPh}
              onChange={(e) => setTargetPh(e.target.value)}
              size="small"
              inputProps={{ min: 0, max: 14, step: 0.1, inputMode: 'decimal' }}
              helperText={t('pages.deliveryChannels.targetPhHelper')}
            />
            <TextField
              label={t('pages.deliveryChannels.notes')}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              multiline
              rows={2}
              size="small"
            />
          </Box>
        )}

        {activeStep === 1 && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {method === 'fertigation' && (
              <>
                <TextField
                  label={t('pages.deliveryChannels.fertigation.runsPerDay')}
                  type="number"
                  value={runsPerDay}
                  onChange={(e) => setRunsPerDay(parseInt(e.target.value) || 1)}
                  size="small"
                  inputProps={{ min: 1, max: 24, inputMode: 'numeric' }}
                  helperText={t('pages.deliveryChannels.runsPerDayHelper')}
                />
                <TextField
                  label={t('pages.deliveryChannels.fertigation.durationSeconds')}
                  type="number"
                  value={durationSeconds}
                  onChange={(e) => setDurationSeconds(parseInt(e.target.value) || 300)}
                  size="small"
                  inputProps={{ min: 1, max: 7200, step: 1, inputMode: 'numeric' }}
                  helperText={t('pages.deliveryChannels.durationSecondsHelper')}
                />
              </>
            )}
            {method === 'drench' && (
              <TextField
                label={t('pages.deliveryChannels.drench.volumePerFeeding')}
                type="number"
                value={volumePerFeeding}
                onChange={(e) => setVolumePerFeeding(parseFloat(e.target.value) || 1)}
                size="small"
                inputProps={{ min: 0.1, max: 100, step: 0.1, inputMode: 'decimal' }}
                slotProps={{
                  input: {
                    endAdornment: <Typography variant="caption" sx={{ ml: 0.5 }}>L</Typography>,
                  },
                }}
              />
            )}
            {method === 'foliar' && (
              <TextField
                label={t('pages.deliveryChannels.foliar.volumePerSpray')}
                type="number"
                value={volumePerSpray}
                onChange={(e) => setVolumePerSpray(parseFloat(e.target.value) || 0.5)}
                size="small"
                inputProps={{ min: 0.1, max: 10, step: 0.1, inputMode: 'decimal' }}
                slotProps={{
                  input: {
                    endAdornment: <Typography variant="caption" sx={{ ml: 0.5 }}>L</Typography>,
                  },
                }}
              />
            )}
            {method === 'top_dress' && (
              <>
                <TextField
                  label={t('pages.deliveryChannels.topDress.gramsPerPlant')}
                  type="number"
                  value={gramsPerPlant}
                  onChange={(e) => setGramsPerPlant(e.target.value)}
                  size="small"
                  inputProps={{ min: 0, step: 0.5, inputMode: 'decimal' }}
                  slotProps={{
                    input: {
                      endAdornment: <Typography variant="caption" sx={{ ml: 0.5 }}>g</Typography>,
                    },
                  }}
                />
                <TextField
                  label={t('pages.deliveryChannels.topDress.gramsPerM2')}
                  type="number"
                  value={gramsPerM2}
                  onChange={(e) => setGramsPerM2(e.target.value)}
                  size="small"
                  inputProps={{ min: 0, step: 0.5, inputMode: 'decimal' }}
                  slotProps={{
                    input: {
                      endAdornment: <Typography variant="caption" sx={{ ml: 0.5 }}>g/m\u00B2</Typography>,
                    },
                  }}
                />
              </>
            )}
          </Box>
        )}

        {activeStep === 2 && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={scheduleEnabled}
                  onChange={(e) => setScheduleEnabled(e.target.checked)}
                />
              }
              label={t('pages.deliveryChannels.scheduleEnabled')}
            />
            <Typography variant="body2" color="text.secondary">
              {t('pages.deliveryChannels.scheduleHint')}
            </Typography>

            {scheduleEnabled && (
              <>
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {t('pages.wateringSchedule.mode')}
                  </Typography>
                  <ToggleButtonGroup
                    value={scheduleMode}
                    exclusive
                    onChange={(_, value: ScheduleMode | null) => {
                      if (value) setScheduleMode(value);
                    }}
                    size="small"
                    fullWidth
                  >
                    <ToggleButton value="weekdays">
                      {t('pages.wateringSchedule.weekdays')}
                    </ToggleButton>
                    <ToggleButton value="interval">
                      {t('pages.wateringSchedule.interval')}
                    </ToggleButton>
                  </ToggleButtonGroup>
                </Box>

                {scheduleMode === 'weekdays' && (
                  <Box>
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
                            />
                          }
                          label={t(`pages.wateringSchedule.${dayKey}`)}
                        />
                      ))}
                    </Box>
                  </Box>
                )}

                {scheduleMode === 'interval' && (
                  <TextField
                    label={t('pages.wateringSchedule.intervalDays')}
                    type="number"
                    value={intervalDays}
                    onChange={(e) => setIntervalDays(parseInt(e.target.value) || 3)}
                    size="small"
                    inputProps={{ min: 1, max: 90, step: 1 }}
                  />
                )}

                <TextField
                  label={t('pages.wateringSchedule.preferredTime')}
                  type="time"
                  value={preferredTime}
                  onChange={(e) => setPreferredTime(e.target.value)}
                  size="small"
                  fullWidth
                  slotProps={{ inputLabel: { shrink: true } }}
                />

                <TextField
                  label={t('pages.wateringSchedule.reminderHoursBefore')}
                  type="number"
                  value={reminderHoursBefore}
                  onChange={(e) => setReminderHoursBefore(parseInt(e.target.value) || 0)}
                  size="small"
                  inputProps={{ min: 0, max: 24, step: 1 }}
                />

                <TextField
                  label={t('pages.wateringSchedule.timesPerDay')}
                  type="number"
                  value={timesPerDay}
                  onChange={(e) => setTimesPerDay(Math.max(1, Math.min(6, parseInt(e.target.value) || 1)))}
                  size="small"
                  inputProps={{ min: 1, max: 6, step: 1 }}
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
            disabled={!canSave}
          >
            {t('common.next')}
          </Button>
        ) : (
          <Button variant="contained" onClick={handleSave} disabled={!canSave}>
            {t(isEdit ? 'common.save' : 'common.create')}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
