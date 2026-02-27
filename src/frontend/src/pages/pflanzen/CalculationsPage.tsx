import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Grid from '@mui/material/Grid';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useApiError } from '@/hooks/useApiError';
import * as calcApi from '@/api/endpoints/calculations';
import type { VPDResponse, GDDResponse, PhotoperiodScheduleEntry, SlotCapacityResponse, SunTimesResponse } from '@/api/types';

export default function CalculationsPage() {
  const { t } = useTranslation();
  const { handleError } = useApiError();

  // VPD
  const [vpdTemp, setVpdTemp] = useState(25);
  const [vpdHumidity, setVpdHumidity] = useState(60);
  const [vpdResult, setVpdResult] = useState<VPDResponse | null>(null);

  // GDD
  const [gddBaseTemp, setGddBaseTemp] = useState(10);
  const [gddTemps, setGddTemps] = useState('15,25\n14,24\n16,28');
  const [gddResult, setGddResult] = useState<GDDResponse | null>(null);

  // Photoperiod
  const [ppCurrent, setPpCurrent] = useState(18);
  const [ppTarget, setPpTarget] = useState(12);
  const [ppDays, setPpDays] = useState(7);
  const [ppLightsOn, setPpLightsOn] = useState('06:00');
  const [ppSchedule, setPpSchedule] = useState<PhotoperiodScheduleEntry[]>([]);

  // Slot Capacity
  const [scArea, setScArea] = useState(10);
  const [scSpacing, setScSpacing] = useState(30);
  const [scResult, setScResult] = useState<SlotCapacityResponse | null>(null);

  // Sun Times
  const [sunLat, setSunLat] = useState(52.52);
  const [sunLon, setSunLon] = useState(13.405);
  const [sunDate, setSunDate] = useState(new Date().toISOString().split('T')[0]);
  const [sunTz, setSunTz] = useState('Europe/Berlin');
  const [sunResult, setSunResult] = useState<SunTimesResponse | null>(null);

  const calcVpd = async () => {
    try {
      const result = await calcApi.calculateVPD({ temp_c: vpdTemp, humidity_percent: vpdHumidity });
      setVpdResult(result);
    } catch (err) { handleError(err); }
  };

  const calcGdd = async () => {
    try {
      const daily_temps = gddTemps.split('\n').filter(Boolean).map((line) => {
        const [min, max] = line.split(',').map(Number);
        return [min, max] as [number, number];
      });
      const result = await calcApi.calculateGDD({ daily_temps, base_temp_c: gddBaseTemp });
      setGddResult(result);
    } catch (err) { handleError(err); }
  };

  const calcPhotoperiod = async () => {
    try {
      const result = await calcApi.calculatePhotoperiodTransition({
        current_hours: ppCurrent,
        target_hours: ppTarget,
        transition_days: ppDays,
        lights_on_time: ppLightsOn,
      });
      setPpSchedule(result);
    } catch (err) { handleError(err); }
  };

  const calcCapacity = async () => {
    try {
      const result = await calcApi.calculateSlotCapacity({
        area_m2: scArea,
        plant_spacing_cm: scSpacing,
      });
      setScResult(result);
    } catch (err) { handleError(err); }
  };

  const calcSunTimes = async () => {
    try {
      const result = await calcApi.calculateSunTimes({
        latitude: sunLat,
        longitude: sunLon,
        date: sunDate,
        timezone: sunTz,
      });
      setSunResult(result);
    } catch (err) { handleError(err); }
  };

  const ppColumns: Column<PhotoperiodScheduleEntry>[] = [
    { id: 'day', label: 'Day', render: (s) => s.day, align: 'right' },
    { id: 'hours', label: 'Hours', render: (s) => s.photoperiod_hours.toFixed(1), align: 'right' },
    { id: 'on', label: 'On', render: (s) => s.lights_on },
    { id: 'off', label: 'Off', render: (s) => s.lights_off },
    { id: 'dli', label: 'DLI', render: (s) => s.dli.toFixed(2), align: 'right' },
  ];

  return (
    <>
      <PageTitle title={t('pages.calculations.title')} />

      <Grid container spacing={3}>
        {/* VPD */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>{t('pages.calculations.vpd')}</Typography>
              <TextField
                type="number"
                label={t('pages.calculations.vpdTemp')}
                value={vpdTemp}
                onChange={(e) => setVpdTemp(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
              />
              <TextField
                type="number"
                label={t('pages.calculations.vpdHumidity')}
                value={vpdHumidity}
                onChange={(e) => setVpdHumidity(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
                inputProps={{ min: 0, max: 100 }}
              />
              <Button variant="contained" onClick={calcVpd} fullWidth>
                {t('pages.calculations.calculate')}
              </Button>
              {vpdResult && (
                <Alert severity={vpdResult.status === 'optimal' ? 'success' : 'warning'} sx={{ mt: 2 }}>
                  {t('pages.calculations.vpdResult')}: {vpdResult.vpd_kpa} kPa — {vpdResult.status}
                  <br />
                  {vpdResult.recommendation}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* GDD */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>{t('pages.calculations.gdd')}</Typography>
              <TextField
                type="number"
                label={t('pages.calculations.gddBaseTemp')}
                value={gddBaseTemp}
                onChange={(e) => setGddBaseTemp(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
              />
              <TextField
                label="Min,Max (pro Zeile)"
                value={gddTemps}
                onChange={(e) => setGddTemps(e.target.value)}
                multiline
                rows={3}
                fullWidth
                sx={{ mb: 2 }}
              />
              <Button variant="contained" onClick={calcGdd} fullWidth>
                {t('pages.calculations.calculate')}
              </Button>
              {gddResult && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  {t('pages.calculations.gddResult')}: {gddResult.accumulated_gdd} ({gddResult.days_counted} days)
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Photoperiod */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>{t('pages.calculations.photoperiod')}</Typography>
              <TextField type="number" label={t('pages.calculations.currentHours')} value={ppCurrent} onChange={(e) => setPpCurrent(Number(e.target.value))} fullWidth sx={{ mb: 2 }} inputProps={{ min: 0, max: 24 }} />
              <TextField type="number" label={t('pages.calculations.targetHours')} value={ppTarget} onChange={(e) => setPpTarget(Number(e.target.value))} fullWidth sx={{ mb: 2 }} inputProps={{ min: 0, max: 24 }} />
              <TextField type="number" label={t('pages.calculations.transitionDays')} value={ppDays} onChange={(e) => setPpDays(Number(e.target.value))} fullWidth sx={{ mb: 2 }} inputProps={{ min: 1 }} />
              <TextField
                type="time"
                label={t('pages.calculations.lightsOnTime')}
                value={ppLightsOn}
                onChange={(e) => setPpLightsOn(e.target.value)}
                fullWidth
                sx={{ mb: 2 }}
                InputLabelProps={{ shrink: true }}
              />
              <Button variant="contained" onClick={calcPhotoperiod} fullWidth>
                {t('pages.calculations.calculate')}
              </Button>
              {ppSchedule.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <DataTable
                    columns={ppColumns}
                    rows={ppSchedule}
                    getRowKey={(s) => String(s.day)}
                    variant="simple"
                    ariaLabel={t('pages.calculations.photoperiod')}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Slot Capacity */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>{t('pages.calculations.slotCapacity')}</Typography>
              <TextField type="number" label={t('pages.calculations.areaMsq')} value={scArea} onChange={(e) => setScArea(Number(e.target.value))} fullWidth sx={{ mb: 2 }} inputProps={{ min: 0.1 }} />
              <TextField type="number" label={t('pages.calculations.plantSpacing')} value={scSpacing} onChange={(e) => setScSpacing(Number(e.target.value))} fullWidth sx={{ mb: 2 }} inputProps={{ min: 1 }} />
              <Button variant="contained" onClick={calcCapacity} fullWidth>
                {t('pages.calculations.calculate')}
              </Button>
              {scResult && (
                <Box sx={{ mt: 2 }}>
                  <Alert severity="info">
                    Max: {scResult.max_capacity} | Optimal: {scResult.optimal_range[0]}-{scResult.optimal_range[1]} | {scResult.plants_per_m2}/m²
                  </Alert>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Sun Times */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>{t('pages.calculations.sunTimes')}</Typography>
              <TextField
                type="number"
                label={t('pages.calculations.latitude')}
                value={sunLat}
                onChange={(e) => setSunLat(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
                inputProps={{ min: -90, max: 90, step: 0.01 }}
              />
              <TextField
                type="number"
                label={t('pages.calculations.longitude')}
                value={sunLon}
                onChange={(e) => setSunLon(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
                inputProps={{ min: -180, max: 180, step: 0.01 }}
              />
              <TextField
                type="date"
                label={t('common.createdAt').split(' ')[0]}
                value={sunDate}
                onChange={(e) => setSunDate(e.target.value)}
                fullWidth
                sx={{ mb: 2 }}
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                label={t('pages.sites.timezone')}
                value={sunTz}
                onChange={(e) => setSunTz(e.target.value)}
                fullWidth
                sx={{ mb: 2 }}
              />
              <Button variant="contained" onClick={calcSunTimes} fullWidth>
                {t('pages.calculations.calculate')}
              </Button>
              {sunResult && (
                <Box sx={{ mt: 2 }}>
                  <Alert severity="info">
                    {t('pages.calculations.sunrise')}: {sunResult.sunrise} | {t('pages.calculations.sunset')}: {sunResult.sunset}
                    <br />
                    {t('pages.calculations.dawn')}: {sunResult.dawn} | {t('pages.calculations.dusk')}: {sunResult.dusk}
                    <br />
                    {t('pages.calculations.dayLength')}: {sunResult.day_length_hours.toFixed(2)} h
                  </Alert>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </>
  );
}
