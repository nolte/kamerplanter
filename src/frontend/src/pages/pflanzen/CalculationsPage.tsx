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
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import PageTitle from '@/components/layout/PageTitle';
import { useApiError } from '@/hooks/useApiError';
import * as calcApi from '@/api/endpoints/calculations';
import type { VPDResponse, GDDResponse, PhotoperiodScheduleEntry, SlotCapacityResponse } from '@/api/types';

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
  const [ppSchedule, setPpSchedule] = useState<PhotoperiodScheduleEntry[]>([]);

  // Slot Capacity
  const [scArea, setScArea] = useState(10);
  const [scSpacing, setScSpacing] = useState(30);
  const [scResult, setScResult] = useState<SlotCapacityResponse | null>(null);

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
              <Button variant="contained" onClick={calcPhotoperiod} fullWidth>
                {t('pages.calculations.calculate')}
              </Button>
              {ppSchedule.length > 0 && (
                <Table size="small" sx={{ mt: 2 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell>Day</TableCell>
                      <TableCell>Hours</TableCell>
                      <TableCell>DLI</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {ppSchedule.map((s) => (
                      <TableRow key={s.day}>
                        <TableCell>{s.day}</TableCell>
                        <TableCell>{s.photoperiod_hours.toFixed(1)}</TableCell>
                        <TableCell>{s.dli.toFixed(2)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
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
      </Grid>
    </>
  );
}
