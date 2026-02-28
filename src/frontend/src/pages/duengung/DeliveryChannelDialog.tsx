import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
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
import Autocomplete from '@mui/material/Autocomplete';
import type { DeliveryChannel, DeliveryChannelCreate, ApplicationMethod, Tank } from '@/api/types';

const APPLICATION_METHODS: ApplicationMethod[] = ['fertigation', 'drench', 'foliar', 'top_dress'];

interface Props {
  open: boolean;
  onClose: () => void;
  onSave: (channel: DeliveryChannelCreate) => void;
  existingChannel?: DeliveryChannel | null;
  existingIds?: string[];
  tanks?: Tank[];
}

export default function DeliveryChannelDialog({
  open,
  onClose,
  onSave,
  existingChannel,
  existingIds = [],
  tanks = [],
}: Props) {
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
  const [tankKey, setTankKey] = useState<string | null>(null);

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
            setTankKey(mp.tank_key ?? null);
          } else if (mp.method === 'drench') {
            setVolumePerFeeding(mp.volume_per_feeding_liters);
          } else if (mp.method === 'foliar') {
            setVolumePerSpray(mp.volume_per_spray_liters);
          } else if (mp.method === 'top_dress') {
            setGramsPerPlant(mp.grams_per_plant?.toString() ?? '');
            setGramsPerM2(mp.grams_per_m2?.toString() ?? '');
          }
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
        setTankKey(null);
      }
      setActiveStep(0);
    }
  }, [open, existingChannel]);

  const steps = [
    t('pages.deliveryChannels.stepMethod'),
    t('pages.deliveryChannels.stepParams'),
  ];

  const idError =
    !isEdit &&
    channelId.length > 0 &&
    existingIds.includes(channelId)
      ? 'Channel ID already exists'
      : '';

  const canSave = channelId.length > 0 && !idError;

  const handleSave = () => {
    const methodParams = (() => {
      switch (method) {
        case 'fertigation':
          return { method: 'fertigation' as const, runs_per_day: runsPerDay, duration_seconds: durationSeconds, flow_rate_ml_min: null, tank_key: tankKey };
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
    };
    onSave(channel);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
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
              inputProps={{ min: 0, max: 10, step: 0.1 }}
            />
            <TextField
              label={t('pages.deliveryChannels.targetPh')}
              type="number"
              value={targetPh}
              onChange={(e) => setTargetPh(e.target.value)}
              size="small"
              inputProps={{ min: 0, max: 14, step: 0.1 }}
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
                  inputProps={{ min: 1, max: 24 }}
                />
                <TextField
                  label={t('pages.deliveryChannels.fertigation.durationSeconds')}
                  type="number"
                  value={durationSeconds}
                  onChange={(e) => setDurationSeconds(parseInt(e.target.value) || 300)}
                  size="small"
                  inputProps={{ min: 1, max: 7200, step: 1 }}
                />
                <Autocomplete
                  options={tanks}
                  value={tanks.find((tk) => tk.key === tankKey) ?? null}
                  onChange={(_, value) => setTankKey(value?.key ?? null)}
                  getOptionLabel={(tk) => `${tk.name} (${tk.volume_liters} L)`}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={t('pages.deliveryChannels.fertigation.tankKey')}
                      size="small"
                      placeholder={t('pages.deliveryChannels.fertigation.noTank')}
                    />
                  )}
                  isOptionEqualToValue={(option, value) => option.key === value.key}
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
                inputProps={{ min: 0.1, max: 100, step: 0.1 }}
              />
            )}
            {method === 'foliar' && (
              <TextField
                label={t('pages.deliveryChannels.foliar.volumePerSpray')}
                type="number"
                value={volumePerSpray}
                onChange={(e) => setVolumePerSpray(parseFloat(e.target.value) || 0.5)}
                size="small"
                inputProps={{ min: 0.1, max: 10, step: 0.1 }}
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
                  inputProps={{ min: 0, step: 0.5 }}
                />
                <TextField
                  label={t('pages.deliveryChannels.topDress.gramsPerM2')}
                  type="number"
                  value={gramsPerM2}
                  onChange={(e) => setGramsPerM2(e.target.value)}
                  size="small"
                  inputProps={{ min: 0, step: 0.5 }}
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
