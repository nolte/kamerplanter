import { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Slider from '@mui/material/Slider';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import { useTheme } from '@mui/material/styles';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CalculateIcon from '@mui/icons-material/Calculate';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import ScienceIcon from '@mui/icons-material/Science';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import { useApiError } from '@/hooks/useApiError';
import * as planApi from '@/api/endpoints/nutrient-plans';
import * as siteApi from '@/api/endpoints/sites';
import type {
  CalculateDosagesResponse,
  EcBudgetSummary,
} from '@/api/endpoints/nutrient-plans';
import type {
  NutrientPlan,
  NutrientPlanPhaseEntry,
  Site,
} from '@/api/types';

interface Props {
  plan: NutrientPlan;
  entries: NutrientPlanPhaseEntry[];
}

interface PhaseCalcState {
  loading: boolean;
  result: CalculateDosagesResponse | null;
  volume: number;
  roOverride: number | null;
  roSliderActive: boolean;
  selectedChannelId: string | null;
}

// ── EC Budget Bar ────────────────────────────────────────────────────

function EcBudgetBar({ budget, targetEc }: { budget: EcBudgetSummary; targetEc: number }) {
  const { t } = useTranslation();
  const theme = useTheme();

  const segments = [
    { key: 'baseWater', value: budget.ec_base_water, color: theme.palette.info.main },
    { key: 'calmagCorrection', value: budget.ec_calmag, color: theme.palette.warning.main },
    { key: 'phReserve', value: budget.ec_ph_reserve, color: theme.palette.grey[400] },
    { key: 'fertilizers', value: budget.ec_fertilizers, color: theme.palette.success.main },
  ].filter((s) => s.value > 0);

  const total = segments.reduce((sum, s) => sum + s.value, 0);

  return (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
          {t('pages.nutrientPlans.dosageCalc.ecBudget')}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {budget.ec_final.toFixed(2)} / {targetEc.toFixed(2)} mS/cm
        </Typography>
      </Box>
      <Box
        sx={{
          display: 'flex',
          height: 24,
          borderRadius: 1,
          overflow: 'hidden',
          bgcolor: 'action.hover',
        }}
        role="img"
        aria-label={t('pages.nutrientPlans.dosageCalc.ecBudget')}
      >
        {segments.map((seg) => (
          <Tooltip
            key={seg.key}
            title={`${t(`pages.nutrientPlans.dosageCalc.${seg.key}`)}: ${seg.value.toFixed(2)} mS/cm`}
          >
            <Box
              sx={{
                width: total > 0 ? `${(seg.value / Math.max(total, targetEc)) * 100}%` : 0,
                bgcolor: seg.color,
                minWidth: seg.value > 0 ? 4 : 0,
                transition: 'width 0.3s ease',
              }}
            />
          </Tooltip>
        ))}
      </Box>
      <Box sx={{ display: 'flex', gap: 2, mt: 0.5, flexWrap: 'wrap' }}>
        {segments.map((seg) => (
          <Box key={seg.key} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: seg.color, flexShrink: 0 }} />
            <Typography variant="caption" color="text.secondary">
              {t(`pages.nutrientPlans.dosageCalc.${seg.key}`)} ({seg.value.toFixed(2)})
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}

// ── Phase Dosage Result ──────────────────────────────────────────────

function PhaseResult({ result }: { result: CalculateDosagesResponse }) {
  const { t } = useTranslation();
  const theme = useTheme();

  return (
    <Box sx={{ mt: 2 }}>
      {/* Channel info */}
      {result.channel_id && result.channel_id !== 'default' && (
        <Chip
          label={result.channel_id}
          size="small"
          variant="outlined"
          color="secondary"
          sx={{ mb: 1 }}
        />
      )}

      {/* Scaling factor info */}
      {result.scaling_factor !== 1.0 && (
        <Alert severity="info" variant="outlined" sx={{ mb: 2 }}>
          <Typography variant="body2">
            {t('pages.nutrientPlans.dosageCalc.scalingFactor')}: <strong>{result.scaling_factor.toFixed(3)}</strong>
            {' '}(RO: {result.ro_percent_used}%)
          </Typography>
        </Alert>
      )}

      {/* Substrate EC correction info */}
      {result.substrate_correction_applied && result.reference_ec_ms != null && (
        <Alert severity="info" variant="outlined" sx={{ mb: 2 }} icon={<ScienceIcon />}>
          <Typography variant="body2">
            {t('pages.nutrientPlans.substrateCorrection')}:{' '}
            {t('pages.nutrientPlans.referenceEc')} {result.reference_ec_ms.toFixed(2)} mS/cm
            {' → '}{t('pages.nutrientPlans.dosageCalc.targetEc')} {result.target_ec_ms.toFixed(2)} mS/cm
          </Typography>
        </Alert>
      )}

      {/* EC Budget visualization */}
      <EcBudgetBar budget={result.ec_budget} targetEc={result.target_ec_ms} />

      {/* CalMag correction info */}
      {result.calmag_correction && result.calmag_correction.needs_correction && (
        <Alert
          severity="warning"
          icon={<ScienceIcon />}
          sx={{ mb: 2 }}
          data-testid="calmag-correction-alert"
        >
          <AlertTitle>{t('pages.nutrientPlans.dosageCalc.calmagNeeded')}</AlertTitle>
          <Typography variant="body2">
            {t('pages.nutrientPlans.dosageCalc.caDeficit')}: {result.calmag_correction.calcium_deficit_ppm.toFixed(1)} ppm
            {' | '}
            {t('pages.nutrientPlans.dosageCalc.mgDeficit')}: {result.calmag_correction.magnesium_deficit_ppm.toFixed(1)} ppm
          </Typography>
          {result.calmag_correction.ca_mg_ratio_warning && (
            <Typography variant="caption" color="warning.dark" sx={{ mt: 0.5 }}>
              {result.calmag_correction.ca_mg_ratio_warning}
            </Typography>
          )}
          {result.calmag_dosage && (
            <Typography variant="body2" sx={{ mt: 0.5 }}>
              {result.calmag_dosage.product_name}: {result.calmag_dosage.ml_per_liter.toFixed(2)} ml/L ({result.calmag_dosage.total_ml.toFixed(1)} ml {t('pages.nutrientPlans.dosageCalc.total')})
            </Typography>
          )}
        </Alert>
      )}

      {result.calmag_correction && !result.calmag_correction.needs_correction && (
        <Alert severity="success" variant="outlined" sx={{ mb: 2 }}>
          {t('pages.nutrientPlans.dosageCalc.calmagNotNeeded')}
        </Alert>
      )}

      {/* Dosage table */}
      {result.dosages.length > 0 && (
        <TableContainer sx={{ mb: 2 }}>
          <Table size="small" aria-label={t('pages.nutrientPlans.dosageCalc.fertilizers')}>
            <TableHead>
              <TableRow>
                <TableCell>{t('pages.nutrientPlans.dosageCalc.fertilizers')}</TableCell>
                <TableCell align="right">
                  {t('pages.nutrientPlans.dosageCalc.reference')} (ml/L)
                </TableCell>
                <TableCell align="right">
                  {t('pages.nutrientPlans.dosageCalc.calculated')} (ml/L)
                </TableCell>
                <TableCell align="right">
                  {t('pages.nutrientPlans.dosageCalc.total')} (ml)
                </TableCell>
                <TableCell align="right">
                  {t('pages.nutrientPlans.dosageCalc.ecContribution')}
                </TableCell>
                <TableCell>
                  {t('pages.nutrientPlans.dosageCalc.source')}
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {result.dosages.map((d, i) => (
                <TableRow key={i}>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                      {d.product_name}
                    </Typography>
                  </TableCell>
                  <TableCell align="right" sx={{ color: 'text.secondary' }}>
                    {d.source === 'reference'
                      ? d.ml_per_liter.toFixed(2)
                      : (result.scaling_factor !== 0
                        ? (d.ml_per_liter / result.scaling_factor).toFixed(2)
                        : '-')}
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{ fontWeight: 'bold', color: theme.palette.primary.main }}
                  >
                    {d.ml_per_liter.toFixed(2)}
                  </TableCell>
                  <TableCell align="right">{d.total_ml.toFixed(1)}</TableCell>
                  <TableCell align="right">{d.ec_contribution.toFixed(2)}</TableCell>
                  <TableCell>
                    <Chip
                      label={t(`pages.nutrientPlans.dosageCalc.dosageSource${capitalize(d.source)}`)}
                      size="small"
                      variant="outlined"
                      color={d.source === 'scaled' ? 'primary' : d.source === 'auto_calmag' ? 'warning' : 'default'}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Effective water info */}
      {result.effective_water && (
        <Card variant="outlined" sx={{ mb: 2 }}>
          <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
            <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
              <WaterDropIcon fontSize="small" />
              {t('pages.nutrientPlans.dosageCalc.effectiveWater')}
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Chip label={`EC: ${result.effective_water.ec_ms.toFixed(2)} mS/cm`} size="small" variant="outlined" />
              <Chip label={`pH: ${result.effective_water.ph.toFixed(1)}`} size="small" variant="outlined" />
              <Chip label={`Ca: ${result.effective_water.calcium_ppm.toFixed(0)} ppm`} size="small" variant="outlined" />
              <Chip label={`Mg: ${result.effective_water.magnesium_ppm.toFixed(0)} ppm`} size="small" variant="outlined" />
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Mixing instructions */}
      {result.mixing_instructions.length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
            {t('pages.nutrientPlans.dosageCalc.mixingInstructions')}
          </Typography>
          <Box component="ol" sx={{ pl: 2.5, m: 0 }}>
            {result.mixing_instructions.map((instruction, i) => (
              <Typography component="li" variant="body2" key={i} sx={{ mb: 0.25 }}>
                {instruction}
              </Typography>
            ))}
          </Box>
        </Box>
      )}

      {/* Warnings */}
      {result.warnings.length > 0 && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          {result.warnings.map((warning, i) => (
            <Alert key={i} severity="warning" icon={<WarningAmberIcon />}>
              {warning}
            </Alert>
          ))}
        </Box>
      )}
    </Box>
  );
}

function capitalize(s: string): string {
  if (s === 'auto_calmag') return 'AutoCalmag';
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// ── Main Component ───────────────────────────────────────────────────

export default function DosageCalculatorTab({ plan, entries }: Props) {
  const { t } = useTranslation();
  const { handleError } = useApiError();

  const [sites, setSites] = useState<Site[]>([]);
  const [sitesLoading, setSitesLoading] = useState(true);
  const [selectedSite, setSelectedSite] = useState<Site | null>(null);
  const [expandedPhase, setExpandedPhase] = useState<string | false>(false);
  const [phaseStates, setPhaseStates] = useState<Record<string, PhaseCalcState>>({});

  const sorted = useMemo(
    () => [...entries].sort((a, b) => a.sequence_order - b.sequence_order),
    [entries],
  );

  // Load sites
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setSitesLoading(true);
        const data = await siteApi.listSites(0, 200);
        if (!cancelled) {
          setSites(data);
          if (data.length === 1) {
            setSelectedSite(data[0]);
          }
        }
      } catch (err) {
        if (!cancelled) handleError(err);
      } finally {
        if (!cancelled) setSitesLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [handleError]);

  // Init phase states
  useEffect(() => {
    setPhaseStates((prev) => {
      const next = { ...prev };
      for (const entry of sorted) {
        if (!next[entry.key]) {
          next[entry.key] = {
            loading: false,
            result: null,
            volume: 10,
            roOverride: null,
            roSliderActive: false,
            selectedChannelId: null,
          };
        }
      }
      return next;
    });
  }, [sorted]);

  // Auto-calculate when site changes (for expanded phase)
  useEffect(() => {
    if (!selectedSite || !expandedPhase) return;
    const entry = sorted.find((e) => e.key === expandedPhase);
    if (!entry) return;
    const state = phaseStates[entry.key];
    if (!state || state.result) return;
    calculateForPhase(entry.key, entry.sequence_order);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedSite, expandedPhase]);

  const calculateForPhase = useCallback(async (
    entryKey: string,
    sequenceOrder: number,
    overrides?: Partial<Pick<PhaseCalcState, 'volume' | 'roOverride' | 'selectedChannelId'>>,
  ) => {
    if (!selectedSite) return;

    setPhaseStates((prev) => {
      const state = prev[entryKey];
      if (!state) return prev;

      const volume = overrides?.volume ?? state.volume;
      const roOverride = overrides?.roOverride !== undefined ? overrides.roOverride : state.roOverride;
      const channelId = overrides?.selectedChannelId !== undefined ? overrides.selectedChannelId : state.selectedChannelId;

      // Fire API call with the resolved values
      planApi.calculateDosages(plan.key, {
        site_key: selectedSite.key,
        phase_sequence_order: sequenceOrder,
        channel_id: channelId,
        volume_liters: volume,
        ro_percent_override: roOverride,
      }).then((result) => {
        setPhaseStates((p) => ({
          ...p,
          [entryKey]: { ...p[entryKey], loading: false, result },
        }));
      }).catch((err) => {
        handleError(err);
        setPhaseStates((p) => ({
          ...p,
          [entryKey]: { ...p[entryKey], loading: false },
        }));
      });

      return { ...prev, [entryKey]: { ...state, loading: true } };
    });
  }, [selectedSite, plan.key, handleError]);

  const updatePhaseState = useCallback((entryKey: string, updates: Partial<PhaseCalcState>) => {
    setPhaseStates((prev) => ({
      ...prev,
      [entryKey]: { ...prev[entryKey], ...updates },
    }));
  }, []);

  const hasWaterProfile = selectedSite?.water_config?.tap_water_profile != null;

  return (
    <Box data-testid="dosage-calculator-tab">
      {/* Intro text */}
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t('pages.nutrientPlans.dosageCalc.intro')}
      </Typography>

      {/* Site selection */}
      <Card variant="outlined" sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="subtitle1" sx={{ fontWeight: 'medium', mb: 1 }}>
            {t('pages.nutrientPlans.dosageCalc.selectSite')}
          </Typography>
          <Autocomplete
            options={sites}
            getOptionLabel={(s) => s.name}
            value={selectedSite}
            onChange={(_, value) => {
              setSelectedSite(value);
              // Reset all results when site changes
              setPhaseStates((prev) => {
                const next = { ...prev };
                for (const key of Object.keys(next)) {
                  next[key] = { ...next[key], result: null };
                }
                return next;
              });
            }}
            loading={sitesLoading}
            renderInput={(params) => (
              <TextField
                {...params}
                placeholder={t('pages.nutrientPlans.dosageCalc.selectSite')}
                size="small"
                data-testid="dosage-site-select"
              />
            )}
            isOptionEqualToValue={(option, value) => option.key === value.key}
          />

          {/* Water profile info */}
          {selectedSite && !hasWaterProfile && (
            <Alert severity="info" variant="outlined" sx={{ mt: 2 }}>
              <InfoOutlinedIcon sx={{ fontSize: '1rem', verticalAlign: 'text-bottom', mr: 0.5 }} />
              {t('pages.nutrientPlans.dosageCalc.noWaterProfile')}
            </Alert>
          )}

          {selectedSite && hasWaterProfile && selectedSite.water_config?.tap_water_profile && (
            <Box sx={{ mt: 2, display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
              <Chip
                label={`Tap EC: ${selectedSite.water_config.tap_water_profile.ec_ms} mS/cm`}
                size="small"
                variant="outlined"
              />
              <Chip
                label={`pH: ${selectedSite.water_config.tap_water_profile.ph}`}
                size="small"
                variant="outlined"
              />
              <Chip
                label={`Ca: ${selectedSite.water_config.tap_water_profile.calcium_ppm} ppm`}
                size="small"
                variant="outlined"
              />
              <Chip
                label={`Mg: ${selectedSite.water_config.tap_water_profile.magnesium_ppm} ppm`}
                size="small"
                variant="outlined"
              />
              {selectedSite.water_config.has_ro_system && (
                <Chip
                  icon={<WaterDropIcon />}
                  label="RO"
                  size="small"
                  color="info"
                  variant="outlined"
                />
              )}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Phase accordion list */}
      {sorted.length === 0 ? (
        <Alert severity="info">{t('pages.nutrientPlans.noEntries')}</Alert>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {sorted.map((entry) => {
            const state = phaseStates[entry.key];
            const duration = entry.week_end - entry.week_start + 1;

            return (
              <Accordion
                key={entry.key}
                expanded={expandedPhase === entry.key}
                onChange={(_, isExpanded) => setExpandedPhase(isExpanded ? entry.key : false)}
                data-testid={`dosage-phase-${entry.sequence_order}`}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap', width: '100%' }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                      {t(`enums.phaseName.${entry.phase_name}`)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      W{entry.week_start}–{entry.week_end} ({duration} {t('pages.nutrientPlans.weeks')})
                    </Typography>
                    {entry.target_ec_ms != null && (
                      <Chip
                        label={`EC ${entry.target_ec_ms} mS/cm`}
                        size="small"
                        variant="outlined"
                        color="info"
                      />
                    )}
                    {state?.result && (
                      <Chip
                        label={`${t('pages.nutrientPlans.dosageCalc.scalingFactor')}: ${state.result.scaling_factor.toFixed(2)}`}
                        size="small"
                        color="primary"
                      />
                    )}
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  {!selectedSite ? (
                    <Alert severity="info" variant="outlined">
                      {t('pages.nutrientPlans.dosageCalc.selectSiteFirst')}
                    </Alert>
                  ) : (
                    <Box>
                      {/* Delivery channel selector */}
                      {entry.delivery_channels.length > 1 && (
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5, display: 'block' }}>
                            {t('pages.nutrientPlans.dosageCalc.deliveryChannel')}
                          </Typography>
                          <ToggleButtonGroup
                            value={state?.selectedChannelId ?? entry.delivery_channels[0]?.channel_id ?? null}
                            exclusive
                            onChange={(_, value) => {
                              if (value !== null) {
                                updatePhaseState(entry.key, { selectedChannelId: value });
                                calculateForPhase(entry.key, entry.sequence_order, { selectedChannelId: value });
                              }
                            }}
                            size="small"
                            sx={{ flexWrap: 'wrap' }}
                            data-testid={`dosage-channel-select-${entry.sequence_order}`}
                          >
                            {entry.delivery_channels.filter((ch) => ch.enabled).map((ch) => (
                              <ToggleButton key={ch.channel_id} value={ch.channel_id}>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  <Typography variant="body2">
                                    {ch.label || ch.channel_id}
                                  </Typography>
                                  <Chip
                                    label={t(`enums.applicationMethod.${ch.application_method}`)}
                                    size="small"
                                    variant="outlined"
                                    sx={{ ml: 0.5, pointerEvents: 'none' }}
                                  />
                                </Box>
                              </ToggleButton>
                            ))}
                          </ToggleButtonGroup>
                        </Box>
                      )}

                      {/* Volume + RO override inputs */}
                      <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start', mb: 2, flexWrap: 'wrap' }}>
                        <TextField
                          label={t('pages.nutrientPlans.dosageCalc.volumeLiters')}
                          type="number"
                          size="small"
                          value={state?.volume ?? 10}
                          onChange={(e) => {
                            const val = parseFloat(e.target.value);
                            if (!isNaN(val) && val > 0) {
                              updatePhaseState(entry.key, { volume: val });
                            }
                          }}
                          onBlur={() => {
                            if (state?.result) {
                              calculateForPhase(entry.key, entry.sequence_order);
                            }
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && state?.result) {
                              calculateForPhase(entry.key, entry.sequence_order);
                            }
                          }}
                          slotProps={{ htmlInput: { min: 0.1, max: 10000, step: 'any' } }}
                          sx={{ width: 160 }}
                          data-testid={`dosage-volume-${entry.sequence_order}`}
                        />

                        <Box sx={{ flex: '1 1 200px', maxWidth: 300 }}>
                          <Typography variant="caption" color="text.secondary">
                            {t('pages.nutrientPlans.dosageCalc.roPercentOverride')}
                          </Typography>
                          <Slider
                            value={state?.roOverride ?? 0}
                            onChange={(_, val) => {
                              updatePhaseState(entry.key, {
                                roOverride: val as number || null,
                                roSliderActive: true,
                              });
                            }}
                            onChangeCommitted={(_, val) => {
                              const roValue = val as number || null;
                              updatePhaseState(entry.key, { roOverride: roValue, roSliderActive: true });
                              if (state?.result) {
                                calculateForPhase(entry.key, entry.sequence_order, { roOverride: roValue });
                              }
                            }}
                            min={0}
                            max={100}
                            step={5}
                            valueLabelDisplay="auto"
                            valueLabelFormat={(v) => `${v}%`}
                            disabled={!selectedSite.water_config?.has_ro_system}
                            marks={[
                              { value: 0, label: '0%' },
                              { value: 50, label: '50%' },
                              { value: 100, label: '100%' },
                            ]}
                            data-testid={`dosage-ro-slider-${entry.sequence_order}`}
                          />
                        </Box>

                        <Button
                          variant="contained"
                          startIcon={state?.loading ? <CircularProgress size={16} /> : <CalculateIcon />}
                          onClick={() => calculateForPhase(entry.key, entry.sequence_order)}
                          disabled={state?.loading}
                          data-testid={`dosage-calculate-${entry.sequence_order}`}
                        >
                          {t('pages.nutrientPlans.dosageCalc.calculate')}
                        </Button>
                      </Box>

                      {/* Results */}
                      {state?.loading && !state.result && (
                        <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
                          <CircularProgress />
                        </Box>
                      )}

                      {state?.result && (
                        <Box sx={{ position: 'relative' }}>
                          {state.loading && (
                            <Box sx={{
                              position: 'absolute',
                              inset: 0,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              bgcolor: 'rgba(255,255,255,0.6)',
                              zIndex: 1,
                              borderRadius: 1,
                            }}>
                              <CircularProgress size={28} />
                            </Box>
                          )}
                          <PhaseResult result={state.result} />
                        </Box>
                      )}
                    </Box>
                  )}
                </AccordionDetails>
              </Accordion>
            );
          })}
        </Box>
      )}
    </Box>
  );
}
