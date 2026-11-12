/**
 * "Thin out" (Vereinzeln) a sown row or zone (REQ-053 §11.3 "gesät", §12 `thinning`, Anhang A 60, W-015): the
 * seedlings left standing become plants of the run that reserved the slot, the slot is no longer "sown" and a
 * `thinning` care entry names the plants.
 *
 * The count follows from the slot's length or area and the spacing after thinning - the run's `thinning_to_cm`.
 * Without that value the dialog asks for it (no default, E-10); the grower may also type the count of seedlings
 * actually left standing. The server computes and stores the count; the number shown here is the same rule
 * (`thinningLogic.ts`).
 *
 * A zone also takes a row spacing (#2862): prefilled from the run, else from the species profile (its source shown),
 * else empty. With it the zone counts row spacing × in-row spacing; empty means broadcast sowing and the square-grid
 * estimate. The formula used is named under the result.
 */
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { parseApiError } from '@/api/errors';
import { useApiError } from '@/hooks/useApiError';
import { getThinningPlan, thinSlot } from './plantingApi';
import type { ThinningPlan, ThinningResult } from './plantingTypes';
import {
  MAX_THINNING_ROW_SPACING_CM,
  MAX_THINNING_SPACING_CM,
  MIN_THINNING_ROW_SPACING_CM,
  parseDecimal,
  spacingExceedsSlot,
  thinningCount,
  thinningFormula,
} from './thinningLogic';

interface ThinningDialogProps {
  slotKey: string;
  /** The slot's id as the list shows it (e.g. "BEET3_R01"). */
  slotLabel: string;
  /** The crop's display name. */
  speciesName: string;
  onClose: () => void;
  onThinned: (result: ThinningResult) => void;
}

type PlanState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; plan: ThinningPlan };

const FORMULA_KEYS = {
  along_row: 'pages.bed.planting.thinning.formulaAlongRow',
  rows: 'pages.bed.planting.thinning.formulaRows',
  square_grid: 'pages.bed.planting.thinning.formulaSquareGrid',
} as const;

/** The UTC calendar day: the server refuses a day after its own today (UTC). */
function todayUtcText(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function ThinningDialog({ slotKey, slotLabel, speciesName, onClose, onThinned }: ThinningDialogProps) {
  const { t, i18n } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { handleError } = useApiError();
  const [state, setState] = useState<PlanState>({ status: 'loading' });
  const [attempt, setAttempt] = useState(0);
  const [spacing, setSpacing] = useState('');
  const [rowSpacing, setRowSpacing] = useState('');
  const [count, setCount] = useState('');
  const [plantedOn, setPlantedOn] = useState(todayUtcText);
  const [showErrors, setShowErrors] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getThinningPlan(slotKey)
      .then((plan) => {
        if (cancelled) return;
        setState({ status: 'ready', plan });
        setSpacing(plan.thinning_to_cm != null ? String(plan.thinning_to_cm) : '');
        setRowSpacing(plan.row_spacing_cm != null ? String(plan.row_spacing_cm) : '');
      })
      .catch((error: unknown) => {
        if (!cancelled) setState({ status: 'error', message: parseApiError(error) });
      });
    return () => {
      cancelled = true;
    };
  }, [slotKey, attempt]);

  const plan = state.status === 'ready' ? state.plan : null;
  const number = useMemo(() => new Intl.NumberFormat(i18n.language, { maximumFractionDigits: 2 }), [i18n.language]);
  const dateFormat = useMemo(() => new Intl.DateTimeFormat(i18n.language, { dateStyle: 'medium' }), [i18n.language]);

  const isZone = plan?.measure_kind === 'area';
  const spacingValue = parseDecimal(spacing);
  const countValue = parseDecimal(count);
  const rowSpacingParsed = parseDecimal(rowSpacing);
  const rowSpacingInvalid =
    isZone &&
    rowSpacing.trim() !== '' &&
    (rowSpacingParsed === null ||
      rowSpacingParsed < MIN_THINNING_ROW_SPACING_CM ||
      rowSpacingParsed > MAX_THINNING_ROW_SPACING_CM);
  // A row spacing counts only for a zone, and only a valid one: an invalid entry yields no count rather than a guess.
  const rowSpacingValue = isZone && !rowSpacingInvalid ? rowSpacingParsed : null;
  const computed =
    plan?.measure_kind && plan.measure_value != null && spacingValue !== null && !rowSpacingInvalid
      ? thinningCount(plan.measure_kind, plan.measure_value, spacingValue, rowSpacingValue)
      : null;
  const formula = plan?.measure_kind ? thinningFormula(plan.measure_kind, rowSpacingValue) : null;
  // The prefill's source is named only while the field still holds the prefilled value.
  const rowSpacingPrefilled = plan?.row_spacing_cm != null && rowSpacingParsed === plan.row_spacing_cm;
  const maxCount = plan?.max_count ?? 0;
  // One spacing longer than the row (wider than the zone): one seedling stays - allowed, but said (A4).
  const singleSeedling =
    plan?.measure_kind != null &&
    plan.measure_value != null &&
    spacingValue !== null &&
    spacingValue > 0 &&
    countValue === null &&
    spacingExceedsSlot(plan.measure_kind, plan.measure_value, spacingValue, rowSpacingValue);
  // A zone without a row spacing assumes a square grid of the spacing: a guide value, not a measurement (A5).
  const zoneEstimate = formula === 'square_grid' && countValue === null;
  const spacingInvalid =
    spacing.trim() !== '' && (spacingValue === null || spacingValue <= 0 || spacingValue > MAX_THINNING_SPACING_CM);
  const countInvalid =
    count.trim() !== '' &&
    (countValue === null || !Number.isInteger(countValue) || countValue < 1 || countValue > maxCount);
  const effectiveCount = countValue !== null && !countInvalid ? countValue : computed;
  const missing = effectiveCount === null && !spacingInvalid && !rowSpacingInvalid && !countInvalid;
  const tooMany = effectiveCount !== null && effectiveCount > maxCount;
  const dateInvalid = plantedOn === '' || (plan !== null && plantedOn < plan.sown_at) || plantedOn > todayUtcText();
  const invalid = spacingInvalid || rowSpacingInvalid || countInvalid || missing || tooMany || dateInvalid;

  const submit = async () => {
    if (!plan) return;
    setShowErrors(true);
    if (invalid) return;
    setSaving(true);
    try {
      const result = await thinSlot(slotKey, {
        ...(countValue !== null
          ? { count: countValue }
          : { thinning_to_cm: spacingValue, ...(isZone ? { row_spacing_cm: rowSpacingValue } : {}) }),
        planted_on: plantedOn,
      });
      onThinned(result);
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  };

  const rowSpacingHelper = rowSpacingInvalid
    ? t('pages.bed.planting.thinning.rowSpacingInvalid', {
        min: MIN_THINNING_ROW_SPACING_CM,
        max: MAX_THINNING_ROW_SPACING_CM,
      })
    : rowSpacingPrefilled && plan?.row_spacing_source === 'run'
      ? t('pages.bed.planting.thinning.rowSpacingFromRun')
      : rowSpacingPrefilled && plan?.row_spacing_source === 'species'
        ? t('pages.bed.planting.thinning.rowSpacingFromSpecies', { range: plan.species_row_spacing_cm ?? '' })
        : t('pages.bed.planting.thinning.rowSpacingHelper');

  const measureText =
    plan?.measure_kind === 'length' && plan.measure_value != null
      ? t('pages.bed.planting.thinning.measureLength', { length: number.format(plan.measure_value) })
      : plan?.measure_kind === 'area' && plan.measure_value != null
        ? t('pages.bed.planting.thinning.measureArea', { area: number.format(plan.measure_value) })
        : null;

  return (
    <Dialog
      open
      onClose={saving ? undefined : onClose}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      aria-labelledby="thinning-dialog-title"
      data-testid="thinning-dialog"
    >
      <DialogTitle id="thinning-dialog-title">
        {t('pages.bed.planting.thinning.title', { species: speciesName, slot: slotLabel })}
      </DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {t('pages.bed.planting.thinning.help')}
        </Typography>
        {state.status === 'loading' ? <LoadingSkeleton variant="card" /> : null}
        {state.status === 'error' ? (
          <ErrorDisplay error={state.message} onRetry={() => {
            setState({ status: 'loading' });
            setAttempt((value) => value + 1);
          }} />
        ) : null}
        {plan ? (
          <>
            <Box data-testid="thinning-facts">
              <Typography variant="body2">
                {t('pages.bed.planting.thinning.sownOn', { date: dateFormat.format(new Date(plan.sown_at)) })}
              </Typography>
              {measureText ? <Typography variant="body2">{measureText}</Typography> : null}
            </Box>
            {plan.thinning_to_cm == null ? (
              <Alert severity="info" data-testid="thinning-no-spacing">
                {t('pages.bed.planting.thinning.noSpacing')}
              </Alert>
            ) : null}
            <TextField
              label={t('pages.bed.planting.thinning.spacing')}
              value={spacing}
              onChange={(event) => setSpacing(event.target.value)}
              type="number"
              error={(showErrors || spacing.trim() !== '') && spacingInvalid}
              helperText={
                spacingInvalid
                  ? t('pages.bed.planting.thinning.spacingInvalid', { max: MAX_THINNING_SPACING_CM })
                  : t(
                      plan.thinning_to_cm != null
                        ? 'pages.bed.planting.thinning.spacingFromRun'
                        : 'pages.bed.planting.thinning.spacingHelper',
                    )
              }
              slotProps={{
                htmlInput: { step: 'any', min: 0, inputMode: 'decimal', 'data-testid': 'thinning-spacing' },
              }}
              sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
            />
            {isZone ? (
              <TextField
                label={t('pages.bed.planting.thinning.rowSpacing')}
                value={rowSpacing}
                onChange={(event) => setRowSpacing(event.target.value)}
                type="number"
                error={rowSpacingInvalid}
                helperText={rowSpacingHelper}
                slotProps={{
                  htmlInput: {
                    step: 'any',
                    min: MIN_THINNING_ROW_SPACING_CM,
                    max: MAX_THINNING_ROW_SPACING_CM,
                    inputMode: 'decimal',
                    'data-testid': 'thinning-row-spacing',
                  },
                }}
                sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
              />
            ) : null}
            <TextField
              label={t('pages.bed.planting.thinning.count')}
              value={count}
              onChange={(event) => setCount(event.target.value)}
              type="number"
              error={(showErrors || count.trim() !== '') && countInvalid}
              helperText={
                countInvalid
                  ? t('pages.bed.planting.thinning.countInvalid', { max: maxCount })
                  : computed !== null
                    ? t('pages.bed.planting.thinning.countComputed', { count: computed })
                    : t('pages.bed.planting.thinning.countHelper')
              }
              slotProps={{ htmlInput: { step: 1, min: 1, inputMode: 'numeric', 'data-testid': 'thinning-count' } }}
              sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
            />
            <TextField
              label={t('pages.bed.planting.thinning.plantedOn')}
              value={plantedOn}
              onChange={(event) => setPlantedOn(event.target.value)}
              type="date"
              error={showErrors && dateInvalid}
              helperText={
                showErrors && dateInvalid
                  ? t('pages.bed.planting.thinning.plantedOnInvalid')
                  : t('pages.bed.planting.thinning.plantedOnHelper')
              }
              slotProps={{
                inputLabel: { shrink: true },
                htmlInput: { min: plan.sown_at, max: todayUtcText(), 'data-testid': 'thinning-planted-on' },
              }}
              sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
            />
            {showErrors && missing ? (
              <Alert severity="warning" data-testid="thinning-missing">
                {t('pages.bed.planting.thinning.missing')}
              </Alert>
            ) : null}
            {tooMany ? (
              <Alert severity="warning" data-testid="thinning-too-many">
                {t('pages.bed.planting.thinning.tooMany', { count: effectiveCount ?? 0, max: maxCount })}
              </Alert>
            ) : null}
            {singleSeedling && !spacingInvalid ? (
              <Alert severity="info" data-testid="thinning-single-seedling">
                {t(
                  plan.measure_kind === 'area'
                    ? 'pages.bed.planting.thinning.singleSeedlingZone'
                    : 'pages.bed.planting.thinning.singleSeedlingRow',
                )}
              </Alert>
            ) : null}
            {effectiveCount !== null && !tooMany ? (
              <Box aria-live="polite">
                <Typography variant="subtitle2" data-testid="thinning-result">
                  {t(zoneEstimate ? 'pages.bed.planting.thinning.resultEstimate' : 'pages.bed.planting.thinning.result', {
                    count: effectiveCount,
                  })}
                </Typography>
                {countValue === null && formula ? (
                  <Typography variant="body2" color="text.secondary" data-testid="thinning-formula">
                    {t(FORMULA_KEYS[formula])}
                  </Typography>
                ) : null}
                {zoneEstimate ? (
                  <Typography variant="body2" color="text.secondary" data-testid="thinning-estimate-note">
                    {t('pages.bed.planting.thinning.estimateNote')}
                  </Typography>
                ) : null}
              </Box>
            ) : null}
          </>
        ) : null}
      </DialogContent>
      <DialogActions sx={{ px: { xs: 2, sm: 3 }, pb: 2 }}>
        <Button onClick={onClose} disabled={saving} sx={{ minHeight: 48 }}>
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={() => void submit()}
          disabled={saving || plan === null}
          sx={{ minHeight: 48 }}
          data-testid="thinning-submit"
        >
          {t('pages.bed.planting.thinning.submit')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
