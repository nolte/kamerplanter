import { useState, useCallback, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
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
import type { CareProfile, CareStyleType, WateringMethod } from '@/api/types';
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

interface CareProfileEditDialogProps {
  open: boolean;
  onClose: () => void;
  profile: CareProfile;
  onUpdated: (profile: CareProfile) => void;
}

export default function CareProfileEditDialog({
  open,
  onClose,
  profile,
  onUpdated,
}: CareProfileEditDialogProps) {
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
  const [humidityCheckEnabled, setHumidityCheckEnabled] = useState(
    profile.humidity_check_enabled,
  );
  const [humidityCheckInterval, setHumidityCheckInterval] = useState(
    profile.humidity_check_interval_days,
  );
  const [notes, setNotes] = useState(profile.notes ?? '');

  useEffect(() => {
    if (open) {
      setCareStyle(profile.care_style);
      setWateringInterval(profile.watering_interval_days);
      setWateringMethod(profile.watering_method);
      setFertilizingInterval(profile.fertilizing_interval_days);
      setRepottingInterval(profile.repotting_interval_months);
      setPestCheckInterval(profile.pest_check_interval_days);
      setAdaptiveLearning(profile.adaptive_learning_enabled);
      setHumidityCheckEnabled(profile.humidity_check_enabled);
      setHumidityCheckInterval(profile.humidity_check_interval_days);
      setNotes(profile.notes ?? '');
    }
  }, [open, profile]);

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
        humidity_check_enabled: humidityCheckEnabled,
        humidity_check_interval_days: humidityCheckInterval,
        notes: notes || null,
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
    humidityCheckEnabled,
    humidityCheckInterval,
    notes,
    profile.plant_key,
    notification,
    handleError,
    onUpdated,
    onClose,
    t,
  ]);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      data-testid="care-profile-edit-dialog"
    >
      <DialogTitle>{t('pages.pflege.editProfile')}</DialogTitle>
      <DialogContent sx={{ pt: 2 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
          <FormControl fullWidth>
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

          <FormControl fullWidth>
            <InputLabel id="watering-method-label">
              {t('enums.reminderType.watering')}
            </InputLabel>
            <Select
              labelId="watering-method-label"
              value={wateringMethod}
              label={t('enums.reminderType.watering')}
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

          <Box>
            <Typography gutterBottom>
              {t('pages.pflege.wateringInterval')}: {wateringInterval}
            </Typography>
            <Slider
              value={wateringInterval}
              onChange={(_, val) => setWateringInterval(val as number)}
              min={1}
              max={30}
              step={1}
              marks={[
                { value: 1, label: '1' },
                { value: 7, label: '7' },
                { value: 14, label: '14' },
                { value: 30, label: '30' },
              ]}
              data-testid="watering-interval-slider"
            />
          </Box>

          <Box>
            <Typography gutterBottom>
              {t('pages.pflege.fertilizingInterval')}: {fertilizingInterval}
            </Typography>
            <Slider
              value={fertilizingInterval}
              onChange={(_, val) => setFertilizingInterval(val as number)}
              min={7}
              max={90}
              step={1}
              marks={[
                { value: 7, label: '7' },
                { value: 14, label: '14' },
                { value: 30, label: '30' },
                { value: 90, label: '90' },
              ]}
              data-testid="fertilizing-interval-slider"
            />
          </Box>

          <Box>
            <Typography gutterBottom>
              {t('pages.pflege.repottingInterval')}: {repottingInterval}
            </Typography>
            <Slider
              value={repottingInterval}
              onChange={(_, val) => setRepottingInterval(val as number)}
              min={3}
              max={36}
              step={1}
              marks={[
                { value: 3, label: '3' },
                { value: 12, label: '12' },
                { value: 24, label: '24' },
                { value: 36, label: '36' },
              ]}
              data-testid="repotting-interval-slider"
            />
          </Box>

          <Box>
            <Typography gutterBottom>
              {t('pages.pflege.pestCheckInterval')}: {pestCheckInterval}
            </Typography>
            <Slider
              value={pestCheckInterval}
              onChange={(_, val) => setPestCheckInterval(val as number)}
              min={3}
              max={30}
              step={1}
              data-testid="pest-check-interval-slider"
            />
          </Box>

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

          <FormControlLabel
            control={
              <Switch
                checked={humidityCheckEnabled}
                onChange={(e) => setHumidityCheckEnabled(e.target.checked)}
                data-testid="humidity-check-switch"
              />
            }
            label={t('pages.pflege.humidityCheck')}
          />

          {humidityCheckEnabled && (
            <Box>
              <Typography gutterBottom>
                {t('pages.pflege.humidityCheck')}: {humidityCheckInterval}
              </Typography>
              <Slider
                value={humidityCheckInterval}
                onChange={(_, val) => setHumidityCheckInterval(val as number)}
                min={1}
                max={14}
                step={1}
                data-testid="humidity-interval-slider"
              />
            </Box>
          )}

          <TextField
            label={t('common.optional')}
            multiline
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            data-testid="care-notes-field"
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={submitting} data-testid="cancel-button">
          {t('common.cancel')}
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
