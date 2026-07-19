import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import TextField, { type TextFieldProps } from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import MenuItem from '@mui/material/MenuItem';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Grid from '@mui/material/Grid';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import PageTitle from '@/components/layout/PageTitle';
import MobileCard from '@/components/common/MobileCard';
import DataTable, { type Column } from '@/components/common/DataTable';
import ExpertiseFieldWrapper from '@/components/common/ExpertiseFieldWrapper';
import HelpTooltip from '@/components/common/HelpTooltip';
import {
  useFertilizerOptions,
  useLocationOptions,
  FertilizerMultiSelect,
  FertilizerSingleSelect,
  LocationSelect,
  EcBudgetFertilizerRows,
  type EcBudgetFertilizerRow,
} from './NutrientCalcFertilizerFields';
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
  AreaDosingResponse,
  AreaDosingItem,
  SubstrateType,
  PhaseName,
  NutrientDemandLevel,
} from '@/api/types';

/**
 * A calculation input field. Renders a full-width MUI TextField and, when a
 * glossary `helpTerm` is given, embeds the contextual HelpTooltip as an
 * end-adornment *inside* the field rather than as a sibling icon. This keeps the
 * field at full width (labels no longer truncate) and lets fields sit in a
 * responsive Grid without a competing icon column.
 *
 * Accessibility/tab-order note: the embedded HelpTooltip renders its own
 * focusable trigger (`tabIndex=0`) as a DOM sibling *after* the native
 * `<input>` inside the field's root, so keyboard/tab order is
 * input -> help-icon -> next field, matching the visual left-to-right
 * reading order. The Tooltip component wires `aria-describedby` to the
 * trigger automatically, so it doesn't clash with the input's own
 * label/helperText association (UI-NFR-002 / UI-NFR-008).
 */
type CalcFieldProps = Omit<TextFieldProps, 'slotProps'> & {
  /** Glossary term for the embedded HelpTooltip (UI-NFR-011). */
  helpTerm?: string;
  /** Constraints forwarded to the underlying <input> (min/max/step). */
  htmlInputProps?: Record<string, unknown>;
};

function CalcField({ helpTerm, htmlInputProps, ...props }: CalcFieldProps) {
  // Numeric fields default to a decimal-friendly mobile keypad (UI-NFR-008
  // "Eingabetypen & Input-Modes"). Callers can still override via
  // htmlInputProps.inputMode if a field ever needs integer-only input.
  const resolvedHtmlInputProps =
    props.type === 'number' ? { inputMode: 'decimal' as const, ...htmlInputProps } : htmlInputProps;

  return (
    <TextField
      fullWidth
      {...props}
      slotProps={{
        htmlInput: resolvedHtmlInputProps,
        input: helpTerm
          ? {
              endAdornment: (
                <InputAdornment position="end">
                  <HelpTooltip term={helpTerm} iconOnly />
                </InputAdornment>
              ),
            }
          : undefined,
      }}
    />
  );
}

export default function NutrientCalculationsPage() {
  const { t } = useTranslation();
  const { handleError } = useApiError();

  // Shared master-data catalogues, fetched once and reused by every panel (#610).
  const { fertilizers, loading: fertilizersLoading } = useFertilizerOptions();
  const { locations, loading: locationsLoading } = useLocationOptions();

  // ── Mixing Protocol ──────────────────────────────────────────────────
  const [mpVolume, setMpVolume] = useState(10);
  const [mpTargetEc, setMpTargetEc] = useState(1.8);
  const [mpTargetPh, setMpTargetPh] = useState(6.0);
  const [mpBaseEc, setMpBaseEc] = useState(0.3);
  const [mpBasePh, setMpBasePh] = useState(7.2);
  const [mpAlkalinity, setMpAlkalinity] = useState(0);
  const [mpPhase, setMpPhase] = useState<PhaseName>('vegetative');
  const [mpFertKeys, setMpFertKeys] = useState<string[]>([]);
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
  const [msKeys, setMsKeys] = useState<string[]>([]);
  const [msResult, setMsResult] = useState<MixingSafetyResponse | null>(null);

  // ── Water Mixer (reverse) ──────────────────────────────────────────
  const [wmTapEc, setWmTapEc] = useState(0.5);
  const [wmAlkalinity, setWmAlkalinity] = useState(80);
  const [wmTargetBaseEc, setWmTargetBaseEc] = useState(0.15);
  const [wmResult, setWmResult] = useState<WaterMixReverseResponse | null>(null);

  // ── Area-based Dosing (REQ-004 W-013) ────────────────────────────────
  const [adFertKeys, setAdFertKeys] = useState<string[]>([]);
  const [adAreaM2, setAdAreaM2] = useState<number | ''>('');
  const [adLocationKey, setAdLocationKey] = useState('');
  const [adDemandLevel, setAdDemandLevel] = useState<NutrientDemandLevel | ''>('');
  const [adResult, setAdResult] = useState<AreaDosingResponse | null>(null);

  // ── EC Budget ──────────────────────────────────────────────────────
  const [ebTargetEc, setEbTargetEc] = useState(1.8);
  const [ebSubstrate, setEbSubstrate] = useState<SubstrateType>('coco');
  const [ebPhase, setEbPhase] = useState<PhaseName>('vegetative');
  const [ebVolume, setEbVolume] = useState(10);
  const [ebFertRows, setEbFertRows] = useState<EcBudgetFertilizerRow[]>([]);
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
      const result = await calcApi.calculateMixingProtocol({
        target_volume_liters: mpVolume,
        target_ec_ms: mpTargetEc,
        target_ph: mpTargetPh,
        base_water_ec: mpBaseEc,
        base_water_ph: mpBasePh,
        alkalinity_ppm: mpAlkalinity,
        phase: mpPhase,
        fertilizer_keys: mpFertKeys,
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
      const result = await calcApi.validateMixingSafety({
        fertilizer_keys: msKeys,
      });
      setMsResult(result);
    } catch (err) {
      handleError(err);
    }
  };

  const calcAreaDosing = async () => {
    try {
      const result = await calcApi.calculateAreaDosing({
        fertilizer_keys: adFertKeys,
        area_m2: adAreaM2 !== '' ? adAreaM2 : undefined,
        location_key: adLocationKey.trim() || undefined,
        demand_level: adDemandLevel || undefined,
      });
      setAdResult(result);
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
      const fertEntries = ebFertRows
        .filter((row) => row.key)
        .map((row) => ({
          key: row.key,
          recipe_ml_per_liter:
            row.mlPerLiter !== '' ? row.mlPerLiter : undefined,
        }));

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

  const DEMAND_LEVEL_OPTIONS: { value: NutrientDemandLevel; label: string }[] = [
    { value: 'heavy_feeder', label: t('enums.nutrientDemandLevel.heavy_feeder') },
    { value: 'medium_feeder', label: t('enums.nutrientDemandLevel.medium_feeder') },
    { value: 'light_feeder', label: t('enums.nutrientDemandLevel.light_feeder') },
    { value: 'nitrogen_fixer', label: t('enums.nutrientDemandLevel.nitrogen_fixer') },
  ];

  const areaDosingColumns: Column<AreaDosingItem>[] = [
    { id: 'product', label: t('pages.nutrientCalc.product'), render: (r) => r.product_name },
    {
      id: 'totalGrams',
      label: t('pages.nutrientCalc.areaTotalGrams'),
      render: (r) => (r.total_grams != null ? r.total_grams.toFixed(1) : '—'),
      align: 'right',
    },
    {
      id: 'totalLiters',
      label: t('pages.nutrientCalc.areaTotalLiters'),
      render: (r) => (r.total_liters != null ? r.total_liters.toFixed(1) : '—'),
      align: 'right',
    },
    {
      id: 'releaseSpeed',
      label: t('pages.nutrientCalc.areaReleaseSpeed'),
      render: (r) =>
        r.nutrient_release_speed != null
          ? t(`enums.nutrientReleaseSpeed.${r.nutrient_release_speed}`)
          : '—',
    },
    {
      id: 'note',
      label: t('pages.nutrientCalc.areaNote'),
      render: (r) => r.note ?? '—',
    },
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
              <Typography variant="h6" sx={{ mb: 1 }}>
                {t('pages.nutrientCalc.mixingProtocol')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.nutrientCalc.mixingProtocolIntro')}
              </Typography>
              <Grid container spacing={2}>
                <Grid size={12}>
                  <CalcField
                    type="number"
                    label={t('pages.nutrientCalc.targetVolume')}
                    value={mpVolume}
                    onChange={(e) => setMpVolume(Number(e.target.value))}
                    htmlInputProps={{ min: 0.1, step: 0.1 }}
                    helperText={t('pages.nutrientCalc.targetVolumeHelper')}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <CalcField
                    type="number"
                    helpTerm="ec"
                    label={t('pages.nutrientCalc.targetEc')}
                    value={mpTargetEc}
                    onChange={(e) => setMpTargetEc(Number(e.target.value))}
                    htmlInputProps={{ min: 0, step: 0.1 }}
                    helperText={t('pages.nutrientCalc.ecUnitHelper')}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <CalcField
                    type="number"
                    helpTerm="ph"
                    label={t('pages.nutrientCalc.targetPh')}
                    value={mpTargetPh}
                    onChange={(e) => setMpTargetPh(Number(e.target.value))}
                    htmlInputProps={{ min: 0, max: 14, step: 0.1 }}
                    helperText={t('pages.nutrientCalc.phUnitHelper')}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <CalcField
                    type="number"
                    helpTerm="ec"
                    label={t('pages.nutrientCalc.baseWaterEc')}
                    value={mpBaseEc}
                    onChange={(e) => setMpBaseEc(Number(e.target.value))}
                    htmlInputProps={{ min: 0, step: 0.1 }}
                    helperText={t('pages.nutrientCalc.ecUnitHelper')}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <CalcField
                    type="number"
                    helpTerm="ph"
                    label={t('pages.nutrientCalc.baseWaterPh')}
                    value={mpBasePh}
                    onChange={(e) => setMpBasePh(Number(e.target.value))}
                    htmlInputProps={{ min: 0, max: 14, step: 0.1 }}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <CalcField
                    type="number"
                    helpTerm="alkalinity"
                    label={t('pages.nutrientCalc.mixingAlkalinity')}
                    value={mpAlkalinity}
                    onChange={(e) => setMpAlkalinity(Number(e.target.value))}
                    htmlInputProps={{ min: 0, max: 500, step: 'any' }}
                    helperText={t('pages.nutrientCalc.mixingAlkalinityHelper')}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    select
                    label={t('pages.nutrientCalc.mixingPhase')}
                    value={mpPhase}
                    onChange={(e) => setMpPhase(e.target.value as PhaseName)}
                    fullWidth
                    helperText={t('pages.nutrientCalc.mixingPhaseHelper')}
                  >
                    {PHASE_OPTIONS.map((o) => (
                      <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
                    ))}
                  </TextField>
                </Grid>
                <Grid size={12}>
                  <FertilizerMultiSelect
                    options={fertilizers}
                    loading={fertilizersLoading}
                    value={mpFertKeys}
                    onChange={setMpFertKeys}
                    label={t('pages.nutrientCalc.fertilizers')}
                    helperText={t('pages.nutrientCalc.fertilizersHelp')}
                    placeholder={t('pages.nutrientCalc.fertilizersPlaceholder')}
                  />
                </Grid>
              </Grid>
              <Button variant="contained" onClick={calcMixingProtocol} fullWidth sx={{ mt: 2 }}>
                {t('pages.nutrientCalc.calculate')}
              </Button>
              {mpResult && (
                <Box sx={{ mt: 2 }}>
                  <Alert severity={mpResult.valid ? 'success' : 'error'} sx={{ mb: 1 }}>
                    <Chip
                      label={mpResult.valid ? t('pages.nutrientCalc.mixingValid') : t('pages.nutrientCalc.mixingInvalid')}
                      size="small"
                      color={mpResult.valid ? 'success' : 'error'}
                      sx={{ mr: 1 }}
                    />
                    {t('pages.nutrientCalc.calculatedEc')}: {mpResult.calculated_ec.toFixed(2)} mS/cm
                    {mpResult.ph_adjustment.needed && (
                      <>
                        {' | '}pH {mpResult.ph_adjustment.direction}: {mpResult.ph_adjustment.delta.toFixed(2)}
                      </>
                    )}
                  </Alert>
                  <Alert severity="info" icon={false} sx={{ mb: 1 }}>
                    <Tooltip title={t('pages.nutrientCalc.ecNetHelper')} arrow enterTouchDelay={0}>
                      <span tabIndex={0} style={{ cursor: 'help', textDecoration: 'underline dotted' }}>
                        {t('pages.nutrientCalc.ecNetLabel')}: {mpResult.ec_net.toFixed(3)} mS/cm
                      </span>
                    </Tooltip>
                    {' | '}
                    <Tooltip title={t('pages.nutrientCalc.ecPhReserveHelper')} arrow enterTouchDelay={0}>
                      <span tabIndex={0} style={{ cursor: 'help', textDecoration: 'underline dotted' }}>
                        {t('pages.nutrientCalc.ecPhReserveLabel')}: {mpResult.ec_ph_reserve.toFixed(3)} mS/cm
                      </span>
                    </Tooltip>
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
                        mobileCardRenderer={(r) => (
                          <MobileCard
                            title={r.product_name}
                            fields={[
                              { label: t('pages.nutrientCalc.mlPerLiter'), value: r.ml_per_liter.toFixed(2) },
                              { label: t('pages.nutrientCalc.totalMl'), value: r.total_ml.toFixed(1) },
                              { label: t('pages.nutrientCalc.ecContribution'), value: r.ec_contribution.toFixed(3) },
                            ]}
                          />
                        )}
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
              <Typography variant="h6" sx={{ mb: 1 }}>
                {t('pages.nutrientCalc.flushing')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.nutrientCalc.flushingIntro')}
              </Typography>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <CalcField
                    type="number"
                    helpTerm="ec"
                    label={t('pages.nutrientCalc.currentEc')}
                    value={flCurrentEc}
                    onChange={(e) => setFlCurrentEc(Number(e.target.value))}
                    htmlInputProps={{ min: 0, step: 0.1 }}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <CalcField
                    type="number"
                    label={t('pages.nutrientCalc.daysUntilHarvest')}
                    value={flDaysUntilHarvest}
                    onChange={(e) => setFlDaysUntilHarvest(Number(e.target.value))}
                    htmlInputProps={{ min: 1 }}
                  />
                </Grid>
              </Grid>
              <Button variant="contained" onClick={calcFlushing} fullWidth sx={{ mt: 2 }}>
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
                      mobileCardRenderer={(r) => (
                        <MobileCard
                          title={`${t('pages.nutrientCalc.day')} ${r.day}`}
                          subtitle={r.action}
                          fields={[
                            { label: t('pages.nutrientCalc.targetEc'), value: r.target_ec_ms.toFixed(2) },
                            { label: t('pages.nutrientCalc.dosagePercent'), value: `${r.dosage_percent}%` },
                          ]}
                        />
                      )}
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
              <Typography variant="h6" sx={{ mb: 1 }}>
                {t('pages.nutrientCalc.runoffAnalysis')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.nutrientCalc.runoffAnalysisIntro')}
              </Typography>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <CalcField
                    type="number"
                    helpTerm="ec"
                    label={t('pages.nutrientCalc.inputEc')}
                    value={roInputEc}
                    onChange={(e) => setRoInputEc(Number(e.target.value))}
                    htmlInputProps={{ min: 0, step: 0.1 }}
                    helperText={t('pages.nutrientCalc.ecUnitHelper')}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <CalcField
                    type="number"
                    helpTerm="ec"
                    label={t('pages.nutrientCalc.runoffEc')}
                    value={roRunoffEc}
                    onChange={(e) => setRoRunoffEc(Number(e.target.value))}
                    htmlInputProps={{ min: 0, step: 0.1 }}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <CalcField
                    type="number"
                    helpTerm="ph"
                    label={t('pages.nutrientCalc.inputPh')}
                    value={roInputPh}
                    onChange={(e) => setRoInputPh(Number(e.target.value))}
                    htmlInputProps={{ min: 0, max: 14, step: 0.1 }}
                    helperText={t('pages.nutrientCalc.phUnitHelper')}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <CalcField
                    type="number"
                    helpTerm="ph"
                    label={t('pages.nutrientCalc.runoffPh')}
                    value={roRunoffPh}
                    onChange={(e) => setRoRunoffPh(Number(e.target.value))}
                    htmlInputProps={{ min: 0, max: 14, step: 0.1 }}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <CalcField
                    type="number"
                    label={t('pages.nutrientCalc.inputVolume')}
                    value={roInputVol}
                    onChange={(e) => setRoInputVol(Number(e.target.value))}
                    htmlInputProps={{ min: 0, step: 0.1 }}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <CalcField
                    type="number"
                    label={t('pages.nutrientCalc.runoffVolume')}
                    value={roRunoffVol}
                    onChange={(e) => setRoRunoffVol(Number(e.target.value))}
                    htmlInputProps={{ min: 0, step: 0.1 }}
                  />
                </Grid>
              </Grid>
              <Button variant="contained" onClick={calcRunoff} fullWidth sx={{ mt: 2 }}>
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
              <Typography variant="h6" sx={{ mb: 1 }}>
                {t('pages.nutrientCalc.mixingSafety')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.nutrientCalc.mixingSafetyIntro')}
              </Typography>
              <Box sx={{ mb: 2 }}>
                <FertilizerMultiSelect
                  options={fertilizers}
                  loading={fertilizersLoading}
                  value={msKeys}
                  onChange={setMsKeys}
                  label={t('pages.nutrientCalc.fertilizers')}
                  helperText={t('pages.nutrientCalc.fertilizersSafetyHelp')}
                  placeholder={t('pages.nutrientCalc.fertilizersPlaceholder')}
                />
              </Box>
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

        {/* Area-based Dosing (REQ-004 W-013) */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 1 }}>
                {t('pages.nutrientCalc.areaDosing')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.nutrientCalc.areaDosingIntro')}
              </Typography>
              <Grid container spacing={2} sx={{ alignItems: 'flex-start' }}>
                <Grid size={12}>
                  <FertilizerMultiSelect
                    options={fertilizers}
                    loading={fertilizersLoading}
                    value={adFertKeys}
                    onChange={setAdFertKeys}
                    label={t('pages.nutrientCalc.fertilizers')}
                    helperText={t('pages.nutrientCalc.fertilizersAreaHelp')}
                    placeholder={t('pages.nutrientCalc.fertilizersPlaceholder')}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <CalcField
                    type="number"
                    label={t('pages.nutrientCalc.areaM2')}
                    value={adAreaM2}
                    onChange={(e) => setAdAreaM2(e.target.value === '' ? '' : Number(e.target.value))}
                    placeholder="10"
                    htmlInputProps={{ min: 0, step: 'any' }}
                    helperText={t('pages.nutrientCalc.areaM2Helper')}
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <LocationSelect
                    options={locations}
                    loading={locationsLoading}
                    value={adLocationKey}
                    onChange={setAdLocationKey}
                    label={t('pages.nutrientCalc.location')}
                    helperText={t('pages.nutrientCalc.locationHelper')}
                  />
                </Grid>
                <Grid size={12}>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: -1 }}>
                    {t('pages.nutrientCalc.areaOrLocation')}
                  </Typography>
                </Grid>
                {adAreaM2 !== '' && adLocationKey.trim() !== '' && (
                  <Grid size={12}>
                    <Alert severity="info">
                      {t('pages.nutrientCalc.areaOverridesLocationHint')}
                    </Alert>
                  </Grid>
                )}
                <Grid size={12}>
                  <TextField
                    select
                    label={t('pages.nutrientCalc.demandLevel')}
                    value={adDemandLevel}
                    onChange={(e) => setAdDemandLevel(e.target.value as NutrientDemandLevel | '')}
                    fullWidth
                    helperText={t('pages.nutrientCalc.demandLevelHelper')}
                  >
                    <MenuItem value="">{t('pages.nutrientCalc.demandLevelNone')}</MenuItem>
                    {DEMAND_LEVEL_OPTIONS.map((o) => (
                      <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
                    ))}
                  </TextField>
                </Grid>
              </Grid>
              <Button variant="contained" onClick={calcAreaDosing} fullWidth sx={{ mt: 2 }}>
                {t('pages.nutrientCalc.calculate')}
              </Button>
              {adResult && (
                <Box sx={{ mt: 2 }}>
                  <Alert severity="info" sx={{ mb: 1 }}>
                    {t('pages.nutrientCalc.areaM2')}: {adResult.area_m2} m²
                  </Alert>
                  {adResult.warnings.map((w, i) => (
                    <Alert key={i} severity="warning" sx={{ mb: 0.5 }}>
                      {w}
                    </Alert>
                  ))}
                  {adResult.items.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                      <DataTable
                        columns={areaDosingColumns}
                        rows={adResult.items}
                        getRowKey={(r) => r.fertilizer_key ?? r.product_name}
                        variant="simple"
                        ariaLabel={t('pages.nutrientCalc.areaDosing')}
                        mobileCardRenderer={(r) => (
                          <MobileCard
                            title={r.product_name}
                            subtitle={r.note ?? undefined}
                            fields={[
                              { label: t('pages.nutrientCalc.areaTotalGrams'), value: r.total_grams != null ? r.total_grams.toFixed(1) : '—' },
                              { label: t('pages.nutrientCalc.areaTotalLiters'), value: r.total_liters != null ? r.total_liters.toFixed(1) : '—' },
                              {
                                label: t('pages.nutrientCalc.areaReleaseSpeed'),
                                value: r.nutrient_release_speed != null ? t(`enums.nutrientReleaseSpeed.${r.nutrient_release_speed}`) : '—',
                              },
                            ]}
                          />
                        )}
                      />
                    </Box>
                  )}
                  {adResult.instructions.map((inst, i) => (
                    <Typography key={i} variant="body2" sx={{ mt: 0.5 }}>
                      {inst}
                    </Typography>
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
              <Typography variant="h6" sx={{ mb: 1 }}>
                {t('pages.nutrientCalc.ecBudgetTitle')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.nutrientCalc.ecBudgetIntro')}
              </Typography>

              {/* Water Mixer Section (intermediate+) */}
              <ExpertiseFieldWrapper minLevel="intermediate">
                <Typography variant="subtitle1" sx={{ mb: 0.5 }}>
                  {t('pages.nutrientCalc.waterMixer')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                  {t('pages.nutrientCalc.waterMixerIntro')}
                </Typography>
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <CalcField
                      type="number"
                      helpTerm="ec"
                      label={t('pages.nutrientCalc.baseWaterEc')}
                      value={wmTapEc}
                      onChange={(e) => setWmTapEc(Number(e.target.value))}
                      htmlInputProps={{ min: 0, max: 2, step: 0.01 }}
                      helperText={t('pages.nutrientCalc.ecUnitHelper')}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <CalcField
                      type="number"
                      helpTerm="alkalinity"
                      label={t('pages.nutrientCalc.alkalinity')}
                      value={wmAlkalinity}
                      onChange={(e) => setWmAlkalinity(Number(e.target.value))}
                      htmlInputProps={{ min: 0, max: 500, step: 10 }}
                      helperText={t('pages.nutrientCalc.mixingAlkalinityHelper')}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <CalcField
                      type="number"
                      helpTerm="ec"
                      label={t('pages.nutrientCalc.targetBaseEc')}
                      value={wmTargetBaseEc}
                      onChange={(e) => setWmTargetBaseEc(Number(e.target.value))}
                      htmlInputProps={{ min: 0, max: 2, step: 0.01 }}
                      helperText={t('pages.nutrientCalc.ecUnitHelper')}
                    />
                  </Grid>
                </Grid>
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
                <Typography variant="subtitle1" sx={{ mb: 0.5 }}>
                  {t('pages.nutrientCalc.ecBudget')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                  {t('pages.nutrientCalc.ecBudgetSectionIntro')}
                </Typography>
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                    <CalcField
                      type="number"
                      helpTerm="ec"
                      label={t('pages.nutrientCalc.targetEc')}
                      value={ebTargetEc}
                      onChange={(e) => setEbTargetEc(Number(e.target.value))}
                      htmlInputProps={{ min: 0, max: 10, step: 0.1 }}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 3 }}>
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
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 3 }}>
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
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                    <CalcField
                      type="number"
                      label={t('pages.nutrientCalc.targetVolume')}
                      value={ebVolume}
                      onChange={(e) => setEbVolume(Number(e.target.value))}
                      htmlInputProps={{ min: 0.1, step: 1 }}
                    />
                  </Grid>
                  <Grid size={12}>
                    <EcBudgetFertilizerRows
                      options={fertilizers}
                      loading={fertilizersLoading}
                      rows={ebFertRows}
                      onChange={setEbFertRows}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                    <FertilizerSingleSelect
                      options={fertilizers}
                      loading={fertilizersLoading}
                      value={ebCalmagKey}
                      onChange={setEbCalmagKey}
                      label={t('pages.nutrientCalc.calmagKey')}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                    <CalcField
                      type="number"
                      helpTerm="calmag"
                      label={t('pages.nutrientCalc.calmagDose')}
                      value={ebCalmagDose}
                      onChange={(e) => setEbCalmagDose(Number(e.target.value))}
                      htmlInputProps={{ min: 0, step: 0.1 }}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                    <FertilizerSingleSelect
                      options={fertilizers}
                      loading={fertilizersLoading}
                      value={ebSilicateKey}
                      onChange={setEbSilicateKey}
                      label={t('pages.nutrientCalc.silicateKey')}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                    <CalcField
                      type="number"
                      label={t('pages.nutrientCalc.silicateDose')}
                      value={ebSilicateDose}
                      onChange={(e) => setEbSilicateDose(Number(e.target.value))}
                      htmlInputProps={{ min: 0, step: 0.1 }}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <CalcField
                      type="number"
                      label={t('pages.nutrientCalc.substrateCycles')}
                      value={ebSubstrateCycles}
                      onChange={(e) => setEbSubstrateCycles(e.target.value === '' ? '' : Number(e.target.value))}
                      htmlInputProps={{ min: 0, step: 1 }}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <CalcField
                      type="number"
                      helpTerm="ec"
                      label={t('pages.nutrientCalc.measuredEcAtTemp')}
                      value={ebMeasuredEc}
                      onChange={(e) => setEbMeasuredEc(e.target.value === '' ? '' : Number(e.target.value))}
                      htmlInputProps={{ min: 0, step: 0.01 }}
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6, md: 4 }}>
                    <CalcField
                      type="number"
                      label={t('pages.nutrientCalc.measuredTemp')}
                      value={ebMeasuredTemp}
                      onChange={(e) => setEbMeasuredTemp(e.target.value === '' ? '' : Number(e.target.value))}
                      htmlInputProps={{ step: 0.5 }}
                    />
                  </Grid>
                </Grid>
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
                          mobileCardRenderer={(r: Record<string, unknown>) => (
                            <MobileCard
                              title={String(r.product_name)}
                              fields={[
                                { label: t('pages.nutrientCalc.mlPerLiter'), value: Number(r.ml_per_liter).toFixed(2) },
                                { label: t('pages.nutrientCalc.totalMl'), value: Number(r.total_ml).toFixed(1) },
                                { label: t('pages.nutrientCalc.ecContribution'), value: Number(r.ec_contribution).toFixed(3) },
                              ]}
                            />
                          )}
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
