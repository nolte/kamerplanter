import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Grid from '@mui/material/Grid';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import ExpertiseFieldWrapper from '@/components/common/ExpertiseFieldWrapper';
import { useApiError } from '@/hooks/useApiError';
import * as calcApi from '@/api/endpoints/nutrient-calculations';
import type {
  MixingProtocolResponse,
  MixingDosage,
  FlushingResponse,
  FlushingScheduleDay,
  RunoffResponse,
  MixingSafetyResponse,
  WaterMixReverseResponse,
  EcBudgetResponse,
  SubstrateType,
  PhaseName,
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

  // ── Water Mixer (reverse) ──────────────────────────────────────────
  const [wmTapEc, setWmTapEc] = useState(0.5);
  const [wmAlkalinity, setWmAlkalinity] = useState(80);
  const [wmTargetBaseEc, setWmTargetBaseEc] = useState(0.15);
  const [wmResult, setWmResult] = useState<WaterMixReverseResponse | null>(null);

  // ── EC Budget ──────────────────────────────────────────────────────
  const [ebTargetEc, setEbTargetEc] = useState(1.8);
  const [ebSubstrate, setEbSubstrate] = useState<SubstrateType>('coco');
  const [ebPhase, setEbPhase] = useState<PhaseName>('vegetative');
  const [ebVolume, setEbVolume] = useState(10);
  const [ebFertKeys, setEbFertKeys] = useState('');
  const [ebCalmagKey, setEbCalmagKey] = useState('');
  const [ebCalmagDose, setEbCalmagDose] = useState(1.0);
  const [ebSilicateKey, setEbSilicateKey] = useState('');
  const [ebSilicateDose, setEbSilicateDose] = useState(0.5);
  const [ebSubstrateCycles, setEbSubstrateCycles] = useState<number | ''>('');
  const [ebMeasuredEc, setEbMeasuredEc] = useState<number | ''>('');
  const [ebMeasuredTemp, setEbMeasuredTemp] = useState<number | ''>('');
  const [ebResult, setEbResult] = useState<EcBudgetResponse | null>(null);

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

  const calcWaterMixReverse = async () => {
    try {
      const result = await calcApi.calculateWaterMixReverse({
        tap_profile: { ec_ms: wmTapEc, ph: 7.5, alkalinity_ppm: wmAlkalinity },
        target_base_ec_ms: wmTargetBaseEc,
      });
      setWmResult(result);
    } catch (err) {
      handleError(err);
    }
  };

  const calcEcBudget = async () => {
    try {
      const fertEntries = ebFertKeys
        .split(',')
        .map((entry) => entry.trim())
        .filter(Boolean)
        .map((entry) => {
          const [key, dose] = entry.split(':');
          return {
            key: key.trim(),
            recipe_ml_per_liter: dose ? Number(dose.trim()) : undefined,
          };
        });

      const baseEc = wmResult ? wmResult.effective_profile.ec_ms : wmTargetBaseEc;

      const result = await calcApi.calculateEcBudget({
        base_water_ec: baseEc,
        alkalinity_ppm: wmAlkalinity,
        target_ec: ebTargetEc,
        substrate: ebSubstrate,
        phase: ebPhase,
        volume_liters: ebVolume,
        fertilizer_keys: fertEntries,
        calmag_key: ebCalmagKey || undefined,
        calmag_dose_ml_per_liter: ebCalmagKey ? ebCalmagDose : undefined,
        silicate_key: ebSilicateKey || undefined,
        silicate_dose_ml_per_liter: ebSilicateKey ? ebSilicateDose : undefined,
        substrate_cycles_used: ebSubstrateCycles !== '' ? ebSubstrateCycles : undefined,
        measured_ec: ebMeasuredEc !== '' ? ebMeasuredEc : undefined,
        measured_temp_celsius: ebMeasuredTemp !== '' ? ebMeasuredTemp : undefined,
      });
      setEbResult(result);
    } catch (err) {
      handleError(err);
    }
  };

  const SEGMENT_COLORS: Record<string, string> = {
    bluegrey: 'info.main',
    teal: 'success.light',
    orange: 'warning.main',
    green: 'success.main',
    grey: 'text.disabled',
  };

  const SUBSTRATE_OPTIONS: { value: SubstrateType; label: string }[] = [
    { value: 'hydro_solution', label: t('enums.substrateType.hydro_solution') },
    { value: 'coco', label: t('enums.substrateType.coco') },
    { value: 'soil', label: t('enums.substrateType.soil') },
    { value: 'living_soil', label: t('enums.substrateType.living_soil') },
  ];

  const PHASE_OPTIONS: { value: PhaseName; label: string }[] = [
    { value: 'seedling', label: t('enums.phaseName.seedling') },
    { value: 'vegetative', label: t('enums.phaseName.vegetative') },
    { value: 'flowering', label: t('enums.phaseName.flowering') },
    { value: 'flushing', label: t('enums.phaseName.flushing') },
  ];

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
                helperText={t('pages.nutrientCalc.targetVolumeHelper')}
              />
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  type="number"
                  label={t('pages.nutrientCalc.targetEc')}
                  value={mpTargetEc}
                  onChange={(e) => setMpTargetEc(Number(e.target.value))}
                  fullWidth
                  sx={{ mb: 2 }}
                  inputProps={{ min: 0, step: 0.1 }}
                  helperText={t('pages.nutrientCalc.ecUnitHelper')}
                />
                <TextField
                  type="number"
                  label={t('pages.nutrientCalc.targetPh')}
                  value={mpTargetPh}
                  onChange={(e) => setMpTargetPh(Number(e.target.value))}
                  fullWidth
                  sx={{ mb: 2 }}
                  inputProps={{ min: 0, max: 14, step: 0.1 }}
                  helperText={t('pages.nutrientCalc.phUnitHelper')}
                />
              </Box>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  type="number"
                  label={t('pages.nutrientCalc.baseWaterEc')}
                  value={mpBaseEc}
                  onChange={(e) => setMpBaseEc(Number(e.target.value))}
                  fullWidth
                  sx={{ mb: 2 }}
                  inputProps={{ min: 0, step: 0.1 }}
                  helperText={t('pages.nutrientCalc.ecUnitHelper')}
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
              </Box>
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
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  type="number"
                  label={t('pages.nutrientCalc.inputEc')}
                  value={roInputEc}
                  onChange={(e) => setRoInputEc(Number(e.target.value))}
                  fullWidth
                  sx={{ mb: 2 }}
                  inputProps={{ min: 0, step: 0.1 }}
                  helperText={t('pages.nutrientCalc.ecUnitHelper')}
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
              </Box>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  type="number"
                  label={t('pages.nutrientCalc.inputPh')}
                  value={roInputPh}
                  onChange={(e) => setRoInputPh(Number(e.target.value))}
                  fullWidth
                  sx={{ mb: 2 }}
                  inputProps={{ min: 0, max: 14, step: 0.1 }}
                  helperText={t('pages.nutrientCalc.phUnitHelper')}
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
              </Box>
              <Box sx={{ display: 'flex', gap: 2 }}>
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
              </Box>
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

        {/* EC Budget (full width) */}
        <Grid size={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                {t('pages.nutrientCalc.ecBudgetTitle')}
              </Typography>

              {/* Water Mixer Section (intermediate+) */}
              <ExpertiseFieldWrapper minLevel="intermediate">
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  {t('pages.nutrientCalc.waterMixer')}
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <TextField
                    type="number"
                    label={t('pages.nutrientCalc.baseWaterEc')}
                    value={wmTapEc}
                    onChange={(e) => setWmTapEc(Number(e.target.value))}
                    fullWidth
                    inputProps={{ min: 0, max: 2, step: 0.01 }}
                    helperText={t('pages.nutrientCalc.ecUnitHelper')}
                  />
                  <TextField
                    type="number"
                    label={t('pages.nutrientCalc.alkalinity')}
                    value={wmAlkalinity}
                    onChange={(e) => setWmAlkalinity(Number(e.target.value))}
                    fullWidth
                    inputProps={{ min: 0, max: 500, step: 10 }}
                  />
                  <TextField
                    type="number"
                    label={t('pages.nutrientCalc.targetBaseEc')}
                    value={wmTargetBaseEc}
                    onChange={(e) => setWmTargetBaseEc(Number(e.target.value))}
                    fullWidth
                    inputProps={{ min: 0, max: 2, step: 0.01 }}
                    helperText={t('pages.nutrientCalc.ecUnitHelper')}
                  />
                </Box>
                <Button variant="outlined" onClick={calcWaterMixReverse} sx={{ mb: 2 }}>
                  {t('pages.nutrientCalc.calculate')}
                </Button>
                {wmResult && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    {t('pages.nutrientCalc.suggestedRoPercent')}: {wmResult.ro_percent}% |{' '}
                    {t('pages.nutrientCalc.ecMix')}: {wmResult.effective_profile.ec_ms.toFixed(3)} mS/cm
                  </Alert>
                )}
              </ExpertiseFieldWrapper>

              {/* EC Budget Section (expert) */}
              <ExpertiseFieldWrapper minLevel="expert">
                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                  {t('pages.nutrientCalc.ecBudget')}
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <TextField
                    type="number"
                    label={t('pages.nutrientCalc.targetEc')}
                    value={ebTargetEc}
                    onChange={(e) => setEbTargetEc(Number(e.target.value))}
                    fullWidth
                    inputProps={{ min: 0, max: 10, step: 0.1 }}
                  />
                  <TextField
                    select
                    label={t('pages.nutrientCalc.substrate')}
                    value={ebSubstrate}
                    onChange={(e) => setEbSubstrate(e.target.value as SubstrateType)}
                    fullWidth
                  >
                    {SUBSTRATE_OPTIONS.map((o) => (
                      <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
                    ))}
                  </TextField>
                  <TextField
                    select
                    label={t('pages.nutrientCalc.phase')}
                    value={ebPhase}
                    onChange={(e) => setEbPhase(e.target.value as PhaseName)}
                    fullWidth
                  >
                    {PHASE_OPTIONS.map((o) => (
                      <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
                    ))}
                  </TextField>
                  <TextField
                    type="number"
                    label={t('pages.nutrientCalc.targetVolume')}
                    value={ebVolume}
                    onChange={(e) => setEbVolume(Number(e.target.value))}
                    fullWidth
                    inputProps={{ min: 0.1, step: 1 }}
                  />
                </Box>
                <TextField
                  label={t('pages.nutrientCalc.fertilizerKeys')}
                  value={ebFertKeys}
                  onChange={(e) => setEbFertKeys(e.target.value)}
                  fullWidth
                  sx={{ mb: 2 }}
                  helperText={t('pages.nutrientCalc.fertilizerKeysEcBudgetHelp')}
                />
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <TextField
                    label={t('pages.nutrientCalc.calmagKey')}
                    value={ebCalmagKey}
                    onChange={(e) => setEbCalmagKey(e.target.value)}
                    fullWidth
                  />
                  <TextField
                    type="number"
                    label={t('pages.nutrientCalc.calmagDose')}
                    value={ebCalmagDose}
                    onChange={(e) => setEbCalmagDose(Number(e.target.value))}
                    fullWidth
                    inputProps={{ min: 0, step: 0.1 }}
                  />
                  <TextField
                    label={t('pages.nutrientCalc.silicateKey')}
                    value={ebSilicateKey}
                    onChange={(e) => setEbSilicateKey(e.target.value)}
                    fullWidth
                  />
                  <TextField
                    type="number"
                    label={t('pages.nutrientCalc.silicateDose')}
                    value={ebSilicateDose}
                    onChange={(e) => setEbSilicateDose(Number(e.target.value))}
                    fullWidth
                    inputProps={{ min: 0, step: 0.1 }}
                  />
                </Box>
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <TextField
                    type="number"
                    label={t('pages.nutrientCalc.substrateCycles')}
                    value={ebSubstrateCycles}
                    onChange={(e) => setEbSubstrateCycles(e.target.value === '' ? '' : Number(e.target.value))}
                    fullWidth
                    inputProps={{ min: 0, step: 1 }}
                  />
                  <TextField
                    type="number"
                    label={t('pages.nutrientCalc.measuredEcAtTemp')}
                    value={ebMeasuredEc}
                    onChange={(e) => setEbMeasuredEc(e.target.value === '' ? '' : Number(e.target.value))}
                    fullWidth
                    inputProps={{ min: 0, step: 0.01 }}
                  />
                  <TextField
                    type="number"
                    label={t('pages.nutrientCalc.measuredTemp')}
                    value={ebMeasuredTemp}
                    onChange={(e) => setEbMeasuredTemp(e.target.value === '' ? '' : Number(e.target.value))}
                    fullWidth
                    inputProps={{ step: 0.5 }}
                  />
                </Box>
                <Button variant="contained" onClick={calcEcBudget} fullWidth sx={{ mb: 2 }}>
                  {t('pages.nutrientCalc.calculate')}
                </Button>

                {ebResult && (
                  <Box>
                    {/* Living Soil bypass */}
                    {ebResult.living_soil_bypass && (
                      <Alert severity="info" sx={{ mb: 2 }}>
                        {t('pages.nutrientCalc.livingsoilBypass')}
                      </Alert>
                    )}

                    {/* Validation status */}
                    {!ebResult.living_soil_bypass && (
                      <Alert severity={ebResult.valid ? 'success' : 'error'} sx={{ mb: 2 }}>
                        <Chip
                          label={ebResult.valid ? t('pages.nutrientCalc.ecBudgetValid') : t('pages.nutrientCalc.ecBudgetInvalid')}
                          size="small"
                          color={ebResult.valid ? 'success' : 'error'}
                          sx={{ mr: 1 }}
                        />
                        {t('pages.nutrientCalc.ecFinal')}: {ebResult.ec_final.toFixed(2)} mS |{' '}
                        {t('pages.nutrientCalc.ecTarget')}: {ebResult.ec_target.toFixed(2)} mS |{' '}
                        {t('pages.nutrientCalc.ecMax')}: {ebResult.ec_max.toFixed(1)} mS
                      </Alert>
                    )}

                    {/* Temperature correction */}
                    {ebResult.ec_at_25_corrected != null && (
                      <Alert severity="info" sx={{ mb: 2 }}>
                        {t('pages.nutrientCalc.ecAt25')}: {ebResult.ec_at_25_corrected.toFixed(3)} mS/cm
                      </Alert>
                    )}

                    {/* EC Budget Bar */}
                    {!ebResult.living_soil_bypass && ebResult.segments.length > 0 && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
                          {t('pages.nutrientCalc.ecBudget')} ({ebResult.ec_final.toFixed(2)} / {ebResult.ec_max.toFixed(1)} mS)
                        </Typography>
                        <Box sx={{
                          display: 'flex',
                          height: 32,
                          borderRadius: 1,
                          overflow: 'hidden',
                          border: 1,
                          borderColor: 'divider',
                        }}>
                          {ebResult.segments.map((seg, i) => {
                            const widthPct = ebResult.ec_max > 0
                              ? Math.max(1, (seg.ec_contribution / ebResult.ec_max) * 100)
                              : 0;
                            return (
                              <Tooltip
                                key={i}
                                title={`${seg.label}: ${seg.ec_contribution.toFixed(3)} mS${seg.ml_per_liter ? ` (${seg.ml_per_liter} ml/L)` : ''}`}
                              >
                                <Box sx={{
                                  width: `${widthPct}%`,
                                  bgcolor: SEGMENT_COLORS[seg.color_hint] ?? 'action.disabled',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  overflow: 'hidden',
                                  px: 0.5,
                                }}>
                                  <Typography
                                    variant="caption"
                                    sx={{ color: 'common.white', whiteSpace: 'nowrap', fontSize: '0.65rem' }}
                                  >
                                    {seg.ec_contribution > 0.05 ? seg.label : ''}
                                  </Typography>
                                </Box>
                              </Tooltip>
                            );
                          })}
                        </Box>
                      </Box>
                    )}

                    {/* Warnings */}
                    {ebResult.warnings.map((w, i) => (
                      <Alert key={i} severity="warning" sx={{ mb: 0.5 }}>
                        {w}
                      </Alert>
                    ))}

                    {/* Dosage table */}
                    {ebResult.dosage_table.length > 0 && (
                      <Box sx={{ mt: 2 }}>
                        <DataTable
                          columns={[
                            { id: 'product', label: t('pages.nutrientCalc.product'), render: (r: Record<string, unknown>) => String(r.product_name) },
                            { id: 'mlPerLiter', label: t('pages.nutrientCalc.mlPerLiter'), render: (r: Record<string, unknown>) => Number(r.ml_per_liter).toFixed(2), align: 'right' as const },
                            { id: 'totalMl', label: t('pages.nutrientCalc.totalMl'), render: (r: Record<string, unknown>) => Number(r.total_ml).toFixed(1), align: 'right' as const },
                            { id: 'ecContrib', label: t('pages.nutrientCalc.ecContribution'), render: (r: Record<string, unknown>) => Number(r.ec_contribution).toFixed(3), align: 'right' as const },
                          ]}
                          rows={ebResult.dosage_table}
                          getRowKey={(r: Record<string, unknown>) => String(r.key)}
                          variant="simple"
                          ariaLabel={t('pages.nutrientCalc.ecBudget')}
                        />
                      </Box>
                    )}

                    {/* Mixing instructions */}
                    {ebResult.dosage_instructions.length > 0 && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" sx={{ mb: 1 }}>
                          {t('pages.nutrientCalc.dosageInstructions')}
                        </Typography>
                        {ebResult.dosage_instructions.map((inst, i) => (
                          <Typography key={i} variant="body2" sx={{ mb: 0.5 }}>
                            {inst}
                          </Typography>
                        ))}
                      </Box>
                    )}
                  </Box>
                )}
              </ExpertiseFieldWrapper>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </>
  );
}
