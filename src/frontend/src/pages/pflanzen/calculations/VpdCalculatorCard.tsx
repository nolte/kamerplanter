import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import HelpTooltip from '@/components/common/HelpTooltip';
import { useApiError } from '@/hooks/useApiError';
import * as calcApi from '@/api/endpoints/calculations';
import type { VPDResponse } from '@/api/types';
import { PHASE_KEYS, PHASE_PROFILES, type PhaseKey } from './phasePresets';
import SliderNumberField from './SliderNumberField';

/**
 * VPD calculator. Exposes the growth-phase select (so the request carries the
 * optional `phase` the backend classifier already reads) and temperature/
 * humidity sliders bounded to sensible ranges. The computation itself is
 * server-side (`POST /calculations/vpd`); the payload is unchanged apart from
 * adding the already-supported `phase` field.
 */
export default function VpdCalculatorCard() {
  const { t } = useTranslation();
  const { handleError } = useApiError();

  const [phase, setPhase] = useState<PhaseKey>('vegetative');
  const [temp, setTemp] = useState(25);
  const [humidity, setHumidity] = useState(60);
  const [result, setResult] = useState<VPDResponse | null>(null);

  const band = useMemo(() => PHASE_PROFILES[phase], [phase]);

  const humidityMarks = useMemo(
    () => [
      { value: 0 },
      { value: 40, label: '40' },
      { value: 60, label: '60' },
      { value: 100 },
    ],
    [],
  );

  const calculate = async () => {
    try {
      const res = await calcApi.calculateVPD({
        temp_c: temp,
        humidity_percent: humidity,
        phase,
      });
      setResult(res);
    } catch (err) {
      handleError(err);
    }
  };

  return (
    <Card>
      <CardContent>
        <HelpTooltip term="vpd">
          <Typography variant="h6" component="h2">
            {t('pages.calculations.vpd')}
          </Typography>
        </HelpTooltip>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
          {t('pages.calculations.vpdIntro')}
        </Typography>

        <TextField
          select
          label={t('pages.calculations.phase')}
          value={phase}
          onChange={(e) => setPhase(e.target.value as PhaseKey)}
          fullWidth
          sx={{ mb: 2 }}
          helperText={t('pages.calculations.vpdTargetBand', {
            min: band.vpdMin,
            max: band.vpdMax,
          })}
        >
          {PHASE_KEYS.map((key) => (
            <MenuItem key={key} value={key}>
              {t(`pages.calculations.phases.${key}`)}
            </MenuItem>
          ))}
        </TextField>

        <SliderNumberField
          label={t('pages.calculations.vpdTemp')}
          value={temp}
          onChange={setTemp}
          min={5}
          max={40}
          step={0.5}
          unit="°C"
        />
        <SliderNumberField
          label={t('pages.calculations.vpdHumidity')}
          value={humidity}
          onChange={setHumidity}
          min={0}
          max={100}
          step={1}
          unit="%"
          marks={humidityMarks}
        />

        <Button variant="contained" onClick={calculate} fullWidth>
          {t('pages.calculations.calculate')}
        </Button>

        {result && (
          <Alert
            severity={result.status === 'optimal' ? 'success' : 'warning'}
            sx={{ mt: 2 }}
          >
            <Box sx={{ fontWeight: 600 }}>
              {t('pages.calculations.vpdResult')}: {result.vpd_kpa} kPa
              {' — '}
              {t(`pages.calculations.vpdStatusValues.${result.status}`, {
                defaultValue: result.status,
              })}
            </Box>
            <Box sx={{ mt: 0.5 }}>
              {t('pages.calculations.vpdTargetBand', {
                min: band.vpdMin,
                max: band.vpdMax,
              })}
            </Box>
            {result.recommendation && (
              <Box sx={{ mt: 0.5 }}>{result.recommendation}</Box>
            )}
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
