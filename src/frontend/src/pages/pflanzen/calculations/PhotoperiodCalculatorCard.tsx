import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import Button from '@mui/material/Button';
import ButtonGroup from '@mui/material/ButtonGroup';
import Box from '@mui/material/Box';
import HelpTooltip from '@/components/common/HelpTooltip';
import DataTable, { type Column } from '@/components/common/DataTable';
import MobileCard from '@/components/common/MobileCard';
import { useApiError } from '@/hooks/useApiError';
import * as calcApi from '@/api/endpoints/calculations';
import type { PhotoperiodScheduleEntry } from '@/api/types';
import { PPFD_PRESETS } from './phasePresets';
import SliderNumberField from './SliderNumberField';

/**
 * Photoperiod-transition calculator (incl. DLI). Current/target photoperiods use
 * sliders bounded to 0–24 h; PPFD is now captured explicitly (previously the
 * backend default of 400 was applied silently) with phase quick-presets. The
 * `ppfd` field is part of the existing request schema, so the server contract is
 * unchanged — `POST /calculations/photoperiod-transition`.
 */
export default function PhotoperiodCalculatorCard() {
  const { t } = useTranslation();
  const { handleError } = useApiError();

  const [currentHours, setCurrentHours] = useState(18);
  const [targetHours, setTargetHours] = useState(12);
  const [days, setDays] = useState(7);
  const [ppfd, setPpfd] = useState(400);
  const [lightsOn, setLightsOn] = useState('06:00');
  const [schedule, setSchedule] = useState<PhotoperiodScheduleEntry[]>([]);

  const calculate = async () => {
    try {
      const result = await calcApi.calculatePhotoperiodTransition({
        current_hours: currentHours,
        target_hours: targetHours,
        transition_days: days,
        ppfd,
        lights_on_time: lightsOn,
      });
      setSchedule(result);
    } catch (err) {
      handleError(err);
    }
  };

  const columns: Column<PhotoperiodScheduleEntry>[] = useMemo(
    () => [
      {
        id: 'day',
        label: t('pages.calculations.ppDay'),
        render: (s) => s.day,
        align: 'right',
      },
      {
        id: 'hours',
        label: t('pages.calculations.ppHours'),
        render: (s) => s.photoperiod_hours.toFixed(1),
        align: 'right',
      },
      { id: 'on', label: t('pages.calculations.ppOn'), render: (s) => s.lights_on },
      { id: 'off', label: t('pages.calculations.ppOff'), render: (s) => s.lights_off },
      {
        id: 'dli',
        label: t('pages.calculations.ppDli'),
        render: (s) => s.dli.toFixed(2),
        align: 'right',
      },
    ],
    [t],
  );

  return (
    <Card>
      <CardContent>
        <HelpTooltip term="dli">
          <Typography variant="h6" component="h2">
            {t('pages.calculations.photoperiod')}
          </Typography>
        </HelpTooltip>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
          {t('pages.calculations.photoperiodIntro')}
        </Typography>

        <SliderNumberField
          label={t('pages.calculations.currentHours')}
          value={currentHours}
          onChange={setCurrentHours}
          min={0}
          max={24}
          step={0.5}
          unit="h"
        />
        <SliderNumberField
          label={t('pages.calculations.targetHours')}
          value={targetHours}
          onChange={setTargetHours}
          min={0}
          max={24}
          step={0.5}
          unit="h"
        />
        <TextField
          type="number"
          label={t('pages.calculations.transitionDays')}
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          fullWidth
          sx={{ mb: 2 }}
          slotProps={{
            htmlInput: { min: 1, step: 1 },
            input: { endAdornment: <InputAdornment position="end">d</InputAdornment> },
          }}
        />

        <TextField
          type="number"
          label={t('pages.calculations.ppfd')}
          value={ppfd}
          onChange={(e) => setPpfd(Number(e.target.value))}
          fullWidth
          sx={{ mb: 1 }}
          slotProps={{
            htmlInput: { min: 0, step: 10 },
            input: {
              endAdornment: <InputAdornment position="end">µmol/m²/s</InputAdornment>,
            },
          }}
        />
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <ButtonGroup size="small" variant="outlined" sx={{ flexWrap: 'wrap' }}>
            {PPFD_PRESETS.map((preset) => (
              <Button
                key={preset}
                onClick={() => setPpfd(preset)}
                variant={ppfd === preset ? 'contained' : 'outlined'}
              >
                {preset}
              </Button>
            ))}
          </ButtonGroup>
          <HelpTooltip term="ppfd" iconOnly />
        </Box>

        <TextField
          type="time"
          label={t('pages.calculations.lightsOnTime')}
          value={lightsOn}
          onChange={(e) => setLightsOn(e.target.value)}
          fullWidth
          sx={{ mb: 2 }}
          slotProps={{ inputLabel: { shrink: true } }}
        />

        <Button variant="contained" onClick={calculate} fullWidth>
          {t('pages.calculations.calculate')}
        </Button>

        {schedule.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <DataTable
              columns={columns}
              rows={schedule}
              getRowKey={(s) => String(s.day)}
              variant="simple"
              ariaLabel={t('pages.calculations.photoperiod')}
              mobileCardRenderer={(s) => (
                <MobileCard
                  title={t('pages.calculations.gddDay', { day: s.day })}
                  subtitle={`${s.photoperiod_hours.toFixed(1)} h`}
                  fields={[
                    { label: t('pages.calculations.ppOn'), value: s.lights_on },
                    { label: t('pages.calculations.ppOff'), value: s.lights_off },
                    { label: t('pages.calculations.ppDli'), value: s.dli.toFixed(2) },
                  ]}
                />
              )}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
