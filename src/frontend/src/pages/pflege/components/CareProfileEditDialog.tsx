import { useState, useCallback, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Slider from '@mui/material/Slider';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Chip from '@mui/material/Chip';
import Collapse from '@mui/material/Collapse';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import OpacityIcon from '@mui/icons-material/Opacity';
import YardIcon from '@mui/icons-material/Yard';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import BugReportIcon from '@mui/icons-material/BugReport';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import PlaceIcon from '@mui/icons-material/Place';
import type { CareProfile, CareConfirmation, CareStyleType, WateringMethod } from '@/api/types';
import * as careApi from '@/api/endpoints/careReminders';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';

const CARE_STYLES: CareStyleType[] = [
  'tropical',
  'succulent',
  'orchid',
  'calathea',
  'herb_tropical',
  'mediterranean',
  'fern',
  'cactus',
  'custom',
];

const WATERING_METHODS: WateringMethod[] = [
  'soak',
  'drench_and_drain',
  'top_water',
  'bottom_water',
];

const MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

interface CareProfileEditDialogProps {
  open: boolean;
  onClose: () => void;
  profile: CareProfile;
  onUpdated: (profile: CareProfile) => void;
}

/**
 * A single task-type row: toggle + icon + label + interval control.
 * When the toggle is off, the interval control is hidden.
 */
function TaskTypeRow({
  icon,
  label,
  enabled,
  onToggle,
  children,
  testId,
}: {
  icon: React.ReactNode;
  label: string;
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  children?: React.ReactNode;
  testId: string;
}) {
  return (
    <Box
      sx={{
        border: 1,
        borderColor: enabled ? 'primary.main' : 'divider',
        borderRadius: 1,
        p: 1.5,
        bgcolor: enabled ? 'action.hover' : 'transparent',
        transition: 'all 0.15s',
      }}
    >
      <FormControlLabel
        control={
          <Switch
            checked={enabled}
            onChange={(e) => onToggle(e.target.checked)}
            data-testid={testId}
          />
        }
        label={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {icon}
            <Typography variant="body2" sx={{ fontWeight: enabled ? 600 : 400 }}>
              {label}
            </Typography>
          </Box>
        }
        sx={{ m: 0, width: '100%' }}
      />
      <Collapse in={enabled}>
        {children && <Box sx={{ pl: 6, pt: 1 }}>{children}</Box>}
      </Collapse>
    </Box>
  );
}

export default function CareProfileEditDialog({
  open,
  onClose,
  profile,
  onUpdated,
}: CareProfileEditDialogProps) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [submitting, setSubmitting] = useState(false);

  const [careStyle, setCareStyle] = useState<CareStyleType>(profile.care_style);
  const [wateringInterval, setWateringInterval] = useState(profile.watering_interval_days);
  const [wateringMethod, setWateringMethod] = useState<WateringMethod>(
    profile.watering_method,
  );
  const [fertilizingInterval, setFertilizingInterval] = useState(
    profile.fertilizing_interval_days,
  );
  const [repottingInterval, setRepottingInterval] = useState(
    profile.repotting_interval_months,
  );
  const [pestCheckInterval, setPestCheckInterval] = useState(
    profile.pest_check_interval_days,
  );
  const [adaptiveLearning, setAdaptiveLearning] = useState(
    profile.adaptive_learning_enabled,
  );
  const [autoCreateWateringTask, setAutoCreateWateringTask] = useState(
    profile.auto_create_watering_task,
  );
  const [autoCreateFertilizingTask, setAutoCreateFertilizingTask] = useState(
    profile.auto_create_fertilizing_task,
  );
  const [autoCreateRepottingTask, setAutoCreateRepottingTask] = useState(
    profile.auto_create_repotting_task,
  );
  const [autoCreatePestCheckTask, setAutoCreatePestCheckTask] = useState(
    profile.auto_create_pest_check_task,
  );
  const [humidityCheckEnabled, setHumidityCheckEnabled] = useState(
    profile.humidity_check_enabled,
  );
  const [humidityCheckInterval, setHumidityCheckInterval] = useState(
    profile.humidity_check_interval_days,
  );
  const [notes, setNotes] = useState(profile.notes ?? '');

  const [winterWateringMultiplier, setWinterWateringMultiplier] = useState(
    profile.winter_watering_multiplier ?? 1.0,
  );
  const [waterQualityHint, setWaterQualityHint] = useState(
    profile.water_quality_hint ?? '',
  );
  const [fertilizingActiveMonths, setFertilizingActiveMonths] = useState<number[]>(
    profile.fertilizing_active_months ?? [3, 4, 5, 6, 7, 8, 9],
  );
  const [locationCheckEnabled, setLocationCheckEnabled] = useState(
    profile.location_check_enabled ?? false,
  );
  const [locationCheckMonths, setLocationCheckMonths] = useState<number[]>(
    profile.location_check_months ?? [],
  );

  // Confirmation history
  const [history, setHistory] = useState<CareConfirmation[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  useEffect(() => {
    if (open) {
      setCareStyle(profile.care_style);
      setWateringInterval(profile.watering_interval_days);
      setWateringMethod(profile.watering_method);
      setFertilizingInterval(profile.fertilizing_interval_days);
      setRepottingInterval(profile.repotting_interval_months);
      setPestCheckInterval(profile.pest_check_interval_days);
      setAdaptiveLearning(profile.adaptive_learning_enabled);
      setAutoCreateWateringTask(profile.auto_create_watering_task);
      setAutoCreateFertilizingTask(profile.auto_create_fertilizing_task);
      setAutoCreateRepottingTask(profile.auto_create_repotting_task);
      setAutoCreatePestCheckTask(profile.auto_create_pest_check_task);
      setHumidityCheckEnabled(profile.humidity_check_enabled);
      setHumidityCheckInterval(profile.humidity_check_interval_days);
      setNotes(profile.notes ?? '');
      setWinterWateringMultiplier(profile.winter_watering_multiplier ?? 1.0);
      setWaterQualityHint(profile.water_quality_hint ?? '');
      setFertilizingActiveMonths(profile.fertilizing_active_months ?? [3, 4, 5, 6, 7, 8, 9]);
      setLocationCheckEnabled(profile.location_check_enabled ?? false);
      setLocationCheckMonths(profile.location_check_months ?? []);
      setHistory([]);
    }
  }, [open, profile]);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const data = await careApi.getHistory(profile.plant_key);
      setHistory(data);
    } catch (err) {
      handleError(err);
    } finally {
      setHistoryLoading(false);
    }
  }, [profile.plant_key, handleError]);

  const handleSave = useCallback(async () => {
    try {
      setSubmitting(true);
      const updated = await careApi.updateProfile(profile.plant_key, {
        care_style: careStyle,
        watering_interval_days: wateringInterval,
        watering_method: wateringMethod,
        fertilizing_interval_days: fertilizingInterval,
        repotting_interval_months: repottingInterval,
        pest_check_interval_days: pestCheckInterval,
        adaptive_learning_enabled: adaptiveLearning,
        auto_create_watering_task: autoCreateWateringTask,
        auto_create_fertilizing_task: autoCreateFertilizingTask,
        auto_create_repotting_task: autoCreateRepottingTask,
        auto_create_pest_check_task: autoCreatePestCheckTask,
        humidity_check_enabled: humidityCheckEnabled,
        humidity_check_interval_days: humidityCheckInterval,
        notes: notes || null,
        winter_watering_multiplier: winterWateringMultiplier,
        water_quality_hint: waterQualityHint || null,
        fertilizing_active_months: fertilizingActiveMonths,
        location_check_enabled: locationCheckEnabled,
        location_check_months: locationCheckMonths,
      });
      notification.success(t('common.save'));
      onUpdated(updated);
      onClose();
    } catch (err) {
      handleError(err);
    } finally {
      setSubmitting(false);
    }
  }, [
    careStyle,
    wateringInterval,
    wateringMethod,
    fertilizingInterval,
    repottingInterval,
    pestCheckInterval,
    adaptiveLearning,
    autoCreateWateringTask,
    autoCreateFertilizingTask,
    autoCreateRepottingTask,
    autoCreatePestCheckTask,
    humidityCheckEnabled,
    humidityCheckInterval,
    notes,
    winterWateringMultiplier,
    waterQualityHint,
    fertilizingActiveMonths,
    locationCheckEnabled,
    locationCheckMonths,
    profile.plant_key,
    notification,
    handleError,
    onUpdated,
    onClose,
    t,
  ]);

  const handleReset = useCallback(async () => {
    try {
      setSubmitting(true);
      await careApi.resetProfile(profile.plant_key);
      notification.success(t('pages.pflege.profileReset'));
      onClose();
    } catch (err) {
      handleError(err);
    } finally {
      setSubmitting(false);
    }
  }, [profile.plant_key, notification, handleError, onClose, t]);

  const isCustom = careStyle === 'custom';

  const handleMonthToggle = (
    _: React.MouseEvent<HTMLElement>,
    newMonths: number[],
    setter: (months: number[]) => void,
  ) => {
    setter(newMonths);
  };

  const intervalSlider = (
    value: number,
    onChange: (v: number) => void,
    min: number,
    max: number,
    marks: { value: number; label: string }[],
    unit: string,
    testId: string,
    customValue?: number,
    onCustomChange?: (v: number) => void,
  ) =>
    isCustom ? (
      <TextField
        type="number"
        size="small"
        value={customValue ?? value}
        onChange={(e) => (onCustomChange ?? onChange)(Math.max(min, Number(e.target.value)))}
        slotProps={{ htmlInput: { min, max } }}
        sx={{ width: 100 }}
        data-testid={testId}
      />
    ) : (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
        <Slider
          value={value}
          onChange={(_, val) => onChange(val as number)}
          min={min}
          max={max}
          step={1}
          marks={marks}
          valueLabelDisplay="auto"
          data-testid={testId}
          sx={{ flex: 1 }}
        />
        <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'nowrap', minWidth: 50, textAlign: 'right' }}>
          {value} {unit}
        </Typography>
      </Box>
    );

  return (
    <Dialog fullScreen={fullScreen} open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      data-testid="care-profile-edit-dialog">
      <DialogTitle>{t('pages.pflege.editProfile')}</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>

          {/* ── Section 1: Care style base ── */}
          <FormControl fullWidth size="small">
            <InputLabel id="care-style-label">{t('pages.pflege.careStyle')}</InputLabel>
            <Select
              labelId="care-style-label"
              value={careStyle}
              label={t('pages.pflege.careStyle')}
              onChange={(e) => setCareStyle(e.target.value as CareStyleType)}
              data-testid="care-style-select"
            >
              {CARE_STYLES.map((style) => (
                <MenuItem key={style} value={style}>
                  {t(`enums.careStyle.${style}`)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* ── Section 2: Task types — each as a card with toggle + inline interval ── */}
          <Typography variant="subtitle2" color="text.secondary">
            {t('pages.pflege.sectionTaskGeneration')}
          </Typography>

          {/* Watering */}
          <TaskTypeRow
            icon={<OpacityIcon fontSize="small" color="primary" />}
            label={t('enums.reminderType.watering')}
            enabled={autoCreateWateringTask}
            onToggle={setAutoCreateWateringTask}
            testId="auto-create-watering-task-switch"
          >
            <FormControl size="small" sx={{ minWidth: 160, mb: 1 }}>
              <InputLabel id="watering-method-label">
                {t('pages.pflege.wateringMethodLabel')}
              </InputLabel>
              <Select
                labelId="watering-method-label"
                value={wateringMethod}
                label={t('pages.pflege.wateringMethodLabel')}
                onChange={(e) => setWateringMethod(e.target.value as WateringMethod)}
                data-testid="watering-method-select"
              >
                {WATERING_METHODS.map((method) => (
                  <MenuItem key={method} value={method}>
                    {t(`enums.wateringMethod.${method}`)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {intervalSlider(
              wateringInterval, setWateringInterval, 1, 30,
              [{ value: 1, label: '1' }, { value: 7, label: '7' }, { value: 14, label: '14' }, { value: 30, label: '30' }],
              t('common.days'), 'watering-interval-slider',
            )}
          </TaskTypeRow>

          {/* Fertilizing */}
          <TaskTypeRow
            icon={<YardIcon fontSize="small" color="success" />}
            label={t('enums.reminderType.fertilizing')}
            enabled={autoCreateFertilizingTask}
            onToggle={setAutoCreateFertilizingTask}
            testId="auto-create-fertilizing-task-switch"
          >
            {intervalSlider(
              fertilizingInterval, setFertilizingInterval, 7, 90,
              [{ value: 7, label: '7' }, { value: 14, label: '14' }, { value: 30, label: '30' }, { value: 90, label: '90' }],
              t('common.days'), 'fertilizing-interval-slider',
            )}
            <Box sx={{ mt: 1 }}>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                {t('pages.pflege.fertilizingActiveMonths')}
              </Typography>
              <ToggleButtonGroup
                value={fertilizingActiveMonths}
                onChange={(e, newMonths: number[]) =>
                  handleMonthToggle(e, newMonths, setFertilizingActiveMonths)
                }
                size="small"
                sx={{ flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}
                data-testid="fertilizing-active-months"
              >
                {MONTHS.map((month) => (
                  <ToggleButton
                    key={month}
                    value={month}
                    sx={{ px: 1, py: 0.25, minWidth: 32 }}
                    data-testid={`fertilizing-month-${month}`}
                  >
                    {month}
                  </ToggleButton>
                ))}
              </ToggleButtonGroup>
            </Box>
          </TaskTypeRow>

          {/* Repotting */}
          <TaskTypeRow
            icon={<SwapHorizIcon fontSize="small" color="warning" />}
            label={t('enums.reminderType.repotting')}
            enabled={autoCreateRepottingTask}
            onToggle={setAutoCreateRepottingTask}
            testId="auto-create-repotting-task-switch"
          >
            {intervalSlider(
              repottingInterval, setRepottingInterval, 3, 36,
              [{ value: 3, label: '3' }, { value: 12, label: '12' }, { value: 24, label: '24' }, { value: 36, label: '36' }],
              t('common.months_unit'), 'repotting-interval-slider',
            )}
          </TaskTypeRow>

          {/* Pest check */}
          <TaskTypeRow
            icon={<BugReportIcon fontSize="small" color="error" />}
            label={t('enums.reminderType.pest_check')}
            enabled={autoCreatePestCheckTask}
            onToggle={setAutoCreatePestCheckTask}
            testId="auto-create-pest-check-task-switch"
          >
            {intervalSlider(
              pestCheckInterval, setPestCheckInterval, 3, 30,
              [{ value: 3, label: '3' }, { value: 7, label: '7' }, { value: 14, label: '14' }, { value: 30, label: '30' }],
              t('common.days'), 'pest-check-interval-slider',
            )}
          </TaskTypeRow>

          {/* Humidity check */}
          <TaskTypeRow
            icon={<WaterDropIcon fontSize="small" sx={{ color: 'info.main' }} />}
            label={t('pages.pflege.humidityCheck')}
            enabled={humidityCheckEnabled}
            onToggle={setHumidityCheckEnabled}
            testId="humidity-check-switch"
          >
            {intervalSlider(
              humidityCheckInterval, setHumidityCheckInterval, 1, 14,
              [{ value: 1, label: '1' }, { value: 7, label: '7' }, { value: 14, label: '14' }],
              t('common.days'), 'humidity-interval-slider',
            )}
          </TaskTypeRow>

          {/* Location check */}
          <TaskTypeRow
            icon={<PlaceIcon fontSize="small" sx={{ color: 'secondary.main' }} />}
            label={t('pages.pflege.locationCheck')}
            enabled={locationCheckEnabled}
            onToggle={setLocationCheckEnabled}
            testId="location-check-switch"
          >
            <Typography variant="caption" color="text.secondary">
              {t('pages.pflege.locationCheckMonths')}
            </Typography>
            <ToggleButtonGroup
              value={locationCheckMonths}
              onChange={(e, newMonths: number[]) =>
                handleMonthToggle(e, newMonths, setLocationCheckMonths)
              }
              size="small"
              sx={{ flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}
              data-testid="location-check-months"
            >
              {MONTHS.map((month) => (
                <ToggleButton
                  key={month}
                  value={month}
                  sx={{ px: 1, py: 0.25, minWidth: 32 }}
                  data-testid={`location-month-${month}`}
                >
                  {month}
                </ToggleButton>
              ))}
            </ToggleButtonGroup>
          </TaskTypeRow>

          {/* ── Section 3: Advanced (collapsed by default) ── */}
          <Accordion disableGutters elevation={0} sx={{ border: 1, borderColor: 'divider', borderRadius: 1, '&::before': { display: 'none' } }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle2" color="text.secondary">
                {t('pages.pflege.sectionAdvanced')}
              </Typography>
            </AccordionSummary>
            <AccordionDetails sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <TextField
                label={t('pages.pflege.winterWateringMultiplier')}
                type="number"
                size="small"
                value={winterWateringMultiplier}
                onChange={(e) => setWinterWateringMultiplier(Number(e.target.value))}
                slotProps={{ htmlInput: { min: 0.1, max: 3.0, step: 0.1 } }}
                fullWidth
                helperText={t('pages.pflege.winterWateringMultiplierHelper')}
                data-testid="winter-watering-multiplier-field"
              />
              <TextField
                label={t('pages.pflege.waterQualityHint')}
                size="small"
                value={waterQualityHint}
                onChange={(e) => setWaterQualityHint(e.target.value)}
                fullWidth
                data-testid="water-quality-hint-field"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={adaptiveLearning}
                    onChange={(e) => setAdaptiveLearning(e.target.checked)}
                    data-testid="adaptive-learning-switch"
                  />
                }
                label={t('pages.pflege.adaptiveLearning')}
              />
              {/* Learned intervals (read-only) */}
              {(profile.watering_interval_learned != null || profile.fertilizing_interval_learned != null) && (
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  {profile.watering_interval_learned != null && (
                    <Chip
                      size="small"
                      variant="outlined"
                      label={`${t('pages.pflege.wateringIntervalLearned')}: ${profile.watering_interval_learned} ${t('common.days')}`}
                      data-testid="watering-learned"
                    />
                  )}
                  {profile.fertilizing_interval_learned != null && (
                    <Chip
                      size="small"
                      variant="outlined"
                      label={`${t('pages.pflege.fertilizingIntervalLearned')}: ${profile.fertilizing_interval_learned} ${t('common.days')}`}
                      data-testid="fertilizing-learned"
                    />
                  )}
                </Box>
              )}
              <TextField
                label={t('pages.pflege.notes')}
                multiline
                rows={3}
                size="small"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                helperText={t('common.optional')}
                data-testid="care-notes-field"
              />
            </AccordionDetails>
          </Accordion>

          {/* ── Section 4: Confirmation history ── */}
          <Accordion disableGutters elevation={0} sx={{ border: 1, borderColor: 'divider', borderRadius: 1, '&::before': { display: 'none' } }} onChange={(_, expanded) => { if (expanded && history.length === 0) loadHistory(); }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle2" color="text.secondary">
                {t('pages.pflege.confirmationHistory')}
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              {historyLoading ? (
                <CircularProgress size={24} />
              ) : history.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  {t('common.noData')}
                </Typography>
              ) : (
                history.map((h, i) => (
                  <Box
                    key={i}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      py: 0.5,
                      borderBottom: '1px solid',
                      borderColor: 'divider',
                      gap: 1,
                    }}
                  >
                    <Typography variant="body2">
                      {t(`enums.reminderType.${h.reminder_type}`)}
                    </Typography>
                    <Typography variant="body2">
                      {new Date(h.confirmed_at).toLocaleDateString()}
                    </Typography>
                    <Chip label={h.action} size="small" />
                    {h.snooze_days && (
                      <Typography variant="body2">+{h.snooze_days}d</Typography>
                    )}
                  </Box>
                ))
              )}
            </AccordionDetails>
          </Accordion>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={submitting} data-testid="cancel-button">
          {t('common.cancel')}
        </Button>
        <Button
          color="warning"
          onClick={handleReset}
          disabled={submitting}
          data-testid="reset-profile-button"
        >
          {t('pages.pflege.profileReset')}
        </Button>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={submitting}
          startIcon={submitting ? <CircularProgress size={16} /> : undefined}
          data-testid="save-profile-button"
        >
          {t('common.save')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
