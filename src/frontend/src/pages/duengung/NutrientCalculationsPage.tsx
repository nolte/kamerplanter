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
import Chip from '@mui/material/Chip';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useApiError } from '@/hooks/useApiError';
import * as calcApi from '@/api/endpoints/nutrient-calculations';
import type {
  MixingProtocolResponse,
  MixingDosage,
  FlushingResponse,
  FlushingScheduleDay,
  RunoffResponse,
  MixingSafetyResponse,
} from '@/api/types';

export default function NutrientCalculationsPage() {
  const { t } = useTranslation();
  const { handleError } = useApiError();

  // ── Mixing Protocol ──────────────────────────────────────────────────
  const [mpVolume, setMpVolume] = useState(10);
  const [mpTargetEc, setMpTargetEc] = useState(1.8);
  const [mpTargetPh, setMpTargetPh] = useState(6.0);
  const [mpBaseEc, setMpBaseEc] = useState(0.3);
  const [mpBasePh, setMpBasePh] = useState(7.2);
  const [mpFertKeys, setMpFertKeys] = useState('');
  const [mpResult, setMpResult] = useState<MixingProtocolResponse | null>(null);

  // ── Flushing ─────────────────────────────────────────────────────────
  const [flCurrentEc, setFlCurrentEc] = useState(1.5);
  const [flDaysUntilHarvest, setFlDaysUntilHarvest] = useState(14);
  const [flResult, setFlResult] = useState<FlushingResponse | null>(null);

  // ── Runoff Analysis ──────────────────────────────────────────────────
  const [roInputEc, setRoInputEc] = useState(1.8);
  const [roRunoffEc, setRoRunoffEc] = useState(2.5);
  const [roInputPh, setRoInputPh] = useState(6.0);
  const [roRunoffPh, setRoRunoffPh] = useState(5.5);
  const [roInputVol, setRoInputVol] = useState(1.0);
  const [roRunoffVol, setRoRunoffVol] = useState(0.2);
  const [roResult, setRoResult] = useState<RunoffResponse | null>(null);

  // ── Mixing Safety ────────────────────────────────────────────────────
  const [msKeys, setMsKeys] = useState('');
  const [msResult, setMsResult] = useState<MixingSafetyResponse | null>(null);

  const calcMixingProtocol = async () => {
    try {
      const keys = mpFertKeys.split(',').map((k) => k.trim()).filter(Boolean);
      const result = await calcApi.calculateMixingProtocol({
        target_volume_liters: mpVolume,
        target_ec_ms: mpTargetEc,
        target_ph: mpTargetPh,
        base_water_ec: mpBaseEc,
        base_water_ph: mpBasePh,
        fertilizer_keys: keys,
      });
      setMpResult(result);
    } catch (err) {
      handleError(err);
    }
  };

  const calcFlushing = async () => {
    try {
      const result = await calcApi.calculateFlushing({
        current_ec_ms: flCurrentEc,
        days_until_harvest: flDaysUntilHarvest,
      });
      setFlResult(result);
    } catch (err) {
      handleError(err);
    }
  };

  const calcRunoff = async () => {
    try {
      const result = await calcApi.calculateRunoff({
        input_ec_ms: roInputEc,
        runoff_ec_ms: roRunoffEc,
        input_ph: roInputPh,
        runoff_ph: roRunoffPh,
        input_volume_liters: roInputVol,
        runoff_volume_liters: roRunoffVol,
      });
      setRoResult(result);
    } catch (err) {
      handleError(err);
    }
  };

  const calcMixingSafety = async () => {
    try {
      const keys = msKeys.split(',').map((k) => k.trim()).filter(Boolean);
      const result = await calcApi.validateMixingSafety({
        fertilizer_keys: keys,
      });
      setMsResult(result);
    } catch (err) {
      handleError(err);
    }
  };

  const dosageColumns: Column<MixingDosage>[] = [
    { id: 'product', label: t('pages.nutrientCalc.product'), render: (r) => r.product_name },
    { id: 'mlPerLiter', label: t('pages.nutrientCalc.mlPerLiter'), render: (r) => r.ml_per_liter.toFixed(2), align: 'right' },
    { id: 'totalMl', label: t('pages.nutrientCalc.totalMl'), render: (r) => r.total_ml.toFixed(1), align: 'right' },
    { id: 'ecContrib', label: t('pages.nutrientCalc.ecContribution'), render: (r) => r.ec_contribution.toFixed(3), align: 'right' },
  ];

  const flushColumns: Column<FlushingScheduleDay>[] = [
    { id: 'day', label: t('pages.nutrientCalc.day'), render: (r) => r.day, align: 'right' },
    { id: 'targetEc', label: t('pages.nutrientCalc.targetEc'), render: (r) => r.target_ec_ms.toFixed(2), align: 'right' },
    { id: 'action', label: t('pages.nutrientCalc.action'), render: (r) => r.action },
    { id: 'dosage', label: t('pages.nutrientCalc.dosagePercent'), render: (r) => `${r.dosage_percent}%`, align: 'right' },
  ];

  return (
    <>
      <PageTitle title={t('pages.nutrientCalc.title')} />

      <Grid container spacing={3}>
        {/* Mixing Protocol */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                {t('pages.nutrientCalc.mixingProtocol')}
              </Typography>
              <TextField
                type="number"
                label={t('pages.nutrientCalc.targetVolume')}
                value={mpVolume}
                onChange={(e) => setMpVolume(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
                inputProps={{ min: 0.1, step: 0.1 }}
              />
              <TextField
                type="number"
                label={t('pages.nutrientCalc.targetEc')}
                value={mpTargetEc}
                onChange={(e) => setMpTargetEc(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
                inputProps={{ min: 0, step: 0.1 }}
              />
              <TextField
                type="number"
                label={t('pages.nutrientCalc.targetPh')}
                value={mpTargetPh}
                onChange={(e) => setMpTargetPh(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
                inputProps={{ min: 0, max: 14, step: 0.1 }}
              />
              <TextField
                type="number"
                label={t('pages.nutrientCalc.baseWaterEc')}
                value={mpBaseEc}
                onChange={(e) => setMpBaseEc(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
                inputProps={{ min: 0, step: 0.1 }}
              />
              <TextField
                type="number"
                label={t('pages.nutrientCalc.baseWaterPh')}
                value={mpBasePh}
                onChange={(e) => setMpBasePh(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
                inputProps={{ min: 0, max: 14, step: 0.1 }}
              />
              <TextField
                label={t('pages.nutrientCalc.fertilizerKeys')}
                value={mpFertKeys}
                onChange={(e) => setMpFertKeys(e.target.value)}
                fullWidth
                sx={{ mb: 2 }}
                helperText={t('pages.nutrientCalc.fertilizerKeysHelp')}
              />
              <Button variant="contained" onClick={calcMixingProtocol} fullWidth>
                {t('pages.nutrientCalc.calculate')}
              </Button>
              {mpResult && (
                <Box sx={{ mt: 2 }}>
                  <Alert severity="info" sx={{ mb: 1 }}>
                    {t('pages.nutrientCalc.calculatedEc')}: {mpResult.calculated_ec.toFixed(2)} mS/cm
                    {mpResult.ph_adjustment.needed && (
                      <>
                        {' | '}pH {mpResult.ph_adjustment.direction}: {mpResult.ph_adjustment.delta.toFixed(2)}
                      </>
                    )}
                  </Alert>
                  {mpResult.warnings.map((w, i) => (
                    <Alert key={i} severity="warning" sx={{ mb: 0.5 }}>
                      {w}
                    </Alert>
                  ))}
                  {mpResult.instructions.map((inst, i) => (
                    <Typography key={i} variant="body2" sx={{ mb: 0.5 }}>
                      {i + 1}. {inst}
                    </Typography>
                  ))}
                  {mpResult.dosages.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                      <DataTable
                        columns={dosageColumns}
                        rows={mpResult.dosages}
                        getRowKey={(r) => r.fertilizer_key}
                        variant="simple"
                        ariaLabel={t('pages.nutrientCalc.mixingProtocol')}
                      />
                    </Box>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Flushing */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                {t('pages.nutrientCalc.flushing')}
              </Typography>
              <TextField
                type="number"
                label={t('pages.nutrientCalc.currentEc')}
                value={flCurrentEc}
                onChange={(e) => setFlCurrentEc(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
                inputProps={{ min: 0, step: 0.1 }}
              />
              <TextField
                type="number"
                label={t('pages.nutrientCalc.daysUntilHarvest')}
                value={flDaysUntilHarvest}
                onChange={(e) => setFlDaysUntilHarvest(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
                inputProps={{ min: 1 }}
              />
              <Button variant="contained" onClick={calcFlushing} fullWidth>
                {t('pages.nutrientCalc.calculate')}
              </Button>
              {flResult && (
                <Box sx={{ mt: 2 }}>
                  <Alert severity="info" sx={{ mb: 1 }}>
                    {t('pages.nutrientCalc.recommendedFlushDays')}: {flResult.recommended_flush_days} |{' '}
                    {t('pages.nutrientCalc.flushStartDay')}: {flResult.flush_start_day}
                  </Alert>
                  {flResult.schedule.length > 0 && (
                    <DataTable
                      columns={flushColumns}
                      rows={flResult.schedule}
                      getRowKey={(r) => String(r.day)}
                      variant="simple"
                      ariaLabel={t('pages.nutrientCalc.flushing')}
                    />
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Runoff Analysis */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                {t('pages.nutrientCalc.runoffAnalysis')}
              </Typography>
              <TextField
                type="number"
                label={t('pages.nutrientCalc.inputEc')}
                value={roInputEc}
                onChange={(e) => setRoInputEc(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
                inputProps={{ min: 0, step: 0.1 }}
              />
              <TextField
                type="number"
                label={t('pages.nutrientCalc.runoffEc')}
                value={roRunoffEc}
                onChange={(e) => setRoRunoffEc(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
                inputProps={{ min: 0, step: 0.1 }}
              />
              <TextField
                type="number"
                label={t('pages.nutrientCalc.inputPh')}
                value={roInputPh}
                onChange={(e) => setRoInputPh(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
                inputProps={{ min: 0, max: 14, step: 0.1 }}
              />
              <TextField
                type="number"
                label={t('pages.nutrientCalc.runoffPh')}
                value={roRunoffPh}
                onChange={(e) => setRoRunoffPh(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
                inputProps={{ min: 0, max: 14, step: 0.1 }}
              />
              <TextField
                type="number"
                label={t('pages.nutrientCalc.inputVolume')}
                value={roInputVol}
                onChange={(e) => setRoInputVol(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
                inputProps={{ min: 0, step: 0.1 }}
              />
              <TextField
                type="number"
                label={t('pages.nutrientCalc.runoffVolume')}
                value={roRunoffVol}
                onChange={(e) => setRoRunoffVol(Number(e.target.value))}
                fullWidth
                sx={{ mb: 2 }}
                inputProps={{ min: 0, step: 0.1 }}
              />
              <Button variant="contained" onClick={calcRunoff} fullWidth>
                {t('pages.nutrientCalc.calculate')}
              </Button>
              {roResult && (
                <Box sx={{ mt: 2 }}>
                  <Alert
                    severity={roResult.overall_health === 'healthy' ? 'success' : roResult.overall_health === 'warning' ? 'warning' : 'error'}
                    sx={{ mb: 1 }}
                  >
                    {t('pages.nutrientCalc.overallHealth')}: {roResult.overall_health}
                  </Alert>
                  <Alert severity={roResult.ec_status === 'ok' ? 'success' : 'warning'} sx={{ mb: 0.5 }}>
                    EC: {roResult.ec_message} (delta: {roResult.ec_delta.toFixed(2)})
                  </Alert>
                  <Alert severity={roResult.ph_status === 'ok' ? 'success' : 'warning'} sx={{ mb: 0.5 }}>
                    pH: {roResult.ph_message} (delta: {roResult.ph_delta.toFixed(2)})
                  </Alert>
                  <Alert severity={roResult.volume_status === 'ok' ? 'success' : 'warning'}>
                    {t('pages.nutrientCalc.volume')}: {roResult.volume_message} ({roResult.runoff_percent.toFixed(1)}%)
                  </Alert>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Mixing Safety */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                {t('pages.nutrientCalc.mixingSafety')}
              </Typography>
              <TextField
                label={t('pages.nutrientCalc.fertilizerKeys')}
                value={msKeys}
                onChange={(e) => setMsKeys(e.target.value)}
                fullWidth
                sx={{ mb: 2 }}
                helperText={t('pages.nutrientCalc.fertilizerKeysHelp')}
              />
              <Button variant="contained" onClick={calcMixingSafety} fullWidth>
                {t('pages.nutrientCalc.validate')}
              </Button>
              {msResult && (
                <Box sx={{ mt: 2 }}>
                  <Alert severity={msResult.safe ? 'success' : 'error'} sx={{ mb: 1 }}>
                    <Chip
                      label={msResult.safe ? t('pages.nutrientCalc.safe') : t('pages.nutrientCalc.unsafe')}
                      size="small"
                      color={msResult.safe ? 'success' : 'error'}
                      sx={{ mr: 1 }}
                    />
                    {msResult.safe
                      ? t('pages.nutrientCalc.safeMessage')
                      : t('pages.nutrientCalc.unsafeMessage')}
                  </Alert>
                  {msResult.warnings.map((w, i) => (
                    <Alert key={i} severity="warning" sx={{ mb: 0.5 }}>
                      {w}
                    </Alert>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </>
  );
}
