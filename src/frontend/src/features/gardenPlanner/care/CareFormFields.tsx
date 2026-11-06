/**
 * The short, category-specific care form (REQ-053 GP-FR-084): watering asks for litres and source,
 * feeding for product, amount and unit, mulching for material and thickness, anything else for a
 * note. Every field is optional; the instant defaults to now and may be backdated by a year
 * (GP-FR-085). Shared by the completion dialog, the batch dialog and the log dialog.
 *
 * Area doses (GP-FR-123, WP 8.9): choosing a catalogue product pre-fills the rate from its data sheet
 * (`application_rate_g_per_m2` / `_l_per_m2`) — never from a soil analysis or a feeder class. A rate per
 * m² shows the live total for the bed; a bed without area disables the per-m² units of the dose forms.
 * A rate in g/m² with the product's N % shows "≈ kg N/ha", labelled as an approximation (no threshold).
 * Liming and pH-raising amendments show a text-only hint (review U-005); no lime amount is computed.
 */
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import FormHelperText from '@mui/material/FormHelperText';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { fetchAllFertilizers } from '@/api/endpoints/fertilizers';
import { formatNumber } from '@/utils/formatting';
import {
  areaDoseTotal,
  isAreaUnit,
  lPerM2ToMm,
  nitrogenApproximation,
  roundRate,
} from '../model/areaDose';
import {
  formKindOf,
  materialsFor,
  showsLimingHint,
  UNITS_BY_KIND,
  WATER_SOURCES,
} from './careCategories';
import {
  areaUnitsBlocked,
  defaultUnit,
  parseQuantity,
  performedAtBounds,
  type CareFormState,
  type FormErrors,
} from './careForm';
import type { CareUnit } from './careTypes';

const NOTE_MAX = 2000;
const TEXT_MAX = 200;
const DEFAULT_TOUCH_TARGET = 48;
/** Every control keeps the touch height (48 px, 64 px in field mode). */
const touchHeight = (height: number) => ({ '& .MuiInputBase-root': { minHeight: height } });

interface FertilizerOption {
  key: string;
  label: string;
  /** Data sheet rates (REQ-004 W-013); `null` when the product states none. */
  rateGPerM2: number | null;
  rateLPerM2: number | null;
  /** N % on the label (`npk_ratio[0]`); 0 is the catalogue's "not stated". */
  nPercent: number | null;
}

/** The fertilizer catalogue for the product field; a failed request leaves free text possible. */
function useFertilizerOptions(enabled: boolean): FertilizerOption[] {
  const [options, setOptions] = useState<FertilizerOption[]>([]);
  useEffect(() => {
    if (!enabled) return undefined;
    let cancelled = false;
    fetchAllFertilizers()
      .then((all) => {
        if (!cancelled) {
          setOptions(
            all.map((fertilizer) => ({
              key: fertilizer.key,
              label: fertilizer.brand
                ? `${fertilizer.product_name} (${fertilizer.brand})`
                : fertilizer.product_name,
              rateGPerM2: fertilizer.application_rate_g_per_m2 ?? null,
              rateLPerM2: fertilizer.application_rate_l_per_m2 ?? null,
              nPercent: fertilizer.npk_ratio?.[0] ?? null,
            })),
          );
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [enabled]);
  return options;
}

interface CareFormFieldsProps {
  category: string;
  state: CareFormState;
  errors: FormErrors;
  onChange: (patch: Partial<CareFormState>) => void;
  /** Reference instant for the bounds of the date field. */
  now: Date;
  /** Prefix of the test ids, so two forms on a page stay distinguishable. */
  testId: string;
  /** The note is stored with the line: "note" for a task, "what happened" for a log line. */
  noteLabelKey?: string;
  /**
   * `area_m2` of the bed (GP-FR-123): `null` or <= 0 disables g/m² and L/m² in the dose forms; absent
   * (several beds at once) disables nothing and shows no total.
   */
  areaM2?: number | null;
  /** Minimum touch height of the controls in px; the field mode passes `KIOSK_TOUCH_TARGET`. */
  touchTarget?: number;
}

export default function CareFormFields({
  category,
  state,
  errors,
  onChange,
  now,
  testId,
  noteLabelKey = 'pages.bed.care.form.note',
  areaM2,
  touchTarget = DEFAULT_TOUCH_TARGET,
}: CareFormFieldsProps) {
  const TOUCH_HEIGHT = touchHeight(touchTarget);
  const { t, i18n } = useTranslation();
  const kind = formKindOf(category);
  const units = UNITS_BY_KIND[kind];
  const fertilizers = useFertilizerOptions(kind === 'feeding');
  const bounds = useMemo(() => performedAtBounds(now), [now]);
  const unit: CareUnit | '' = state.unit !== '' ? state.unit : defaultUnit(kind, areaM2);
  const blocked = areaUnitsBlocked(kind, areaM2);
  const noAreaHintShown = blocked && units.some(isAreaUnit);
  const materialOptions = materialsFor(category);
  const errorText = (field: keyof FormErrors) => {
    const code = errors[field];
    return code ? t(`pages.bed.care.errors.${code}`) : undefined;
  };
  const materialLabel = (code: string) =>
    materialOptions.includes(code) ? t(`enums.careMaterial.${code}`) : code;
  const product = fertilizers.find((option) => option.key === state.product?.key) ?? null;
  const quantity = parseQuantity(state.quantity);
  // A total of 0 is never shown (GP-FR-123): only a positive rate has one; rainfall is a measurement, not a dose.
  const total =
    kind === 'rainfall' || quantity === null || quantity <= 0
      ? null
      : areaDoseTotal(quantity, unit, areaM2);
  const nitrogen =
    kind === 'feeding' && unit === 'g_per_m2'
      ? nitrogenApproximation(quantity, product?.nPercent)
      : null;
  const decimal = (value: number) => formatNumber(value, { maximumFractionDigits: 1 });
  /** The rate as the field takes it: 0.1, with the decimal comma in German (no grouping, so it parses back). */
  const rateText = (rate: number) => {
    const text = String(roundRate(rate));
    return i18n.language.startsWith('de') ? text.replace('.', ',') : text;
  };

  /**
   * GP-FR-123: the data sheet rate of the chosen product, as rate and unit. It replaces an empty quantity
   * or one pre-filled before, never what the user typed; a bed without area takes no per-m² rate.
   */
  const prefillFrom = (option: FertilizerOption): Partial<CareFormState> => {
    if (state.quantity.trim() !== '' && !state.quantityFromProduct) return {};
    const rate: [number, CareUnit] | null =
      option.rateGPerM2 != null && option.rateGPerM2 > 0
        ? [option.rateGPerM2, 'g_per_m2']
        : option.rateLPerM2 != null && option.rateLPerM2 > 0
          ? [option.rateLPerM2, 'l_per_m2']
          : null;
    if (rate === null || blocked || !units.includes(rate[1])) {
      return state.quantityFromProduct ? { quantity: '', quantityFromProduct: false } : {};
    }
    return { quantity: rateText(rate[0]), unit: rate[1], quantityFromProduct: true };
  };

  const quantityLabel = t(`pages.bed.care.form.quantity.${kind === 'note' ? 'amount' : kind}`);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }} data-testid={`${testId}-fields`}>
      {kind === 'feeding' && (
        <Autocomplete<FertilizerOption, false, false, true>
          freeSolo
          options={fertilizers}
          value={product ?? state.productLabel}
          getOptionLabel={(option) => (typeof option === 'string' ? option : option.label)}
          isOptionEqualToValue={(a, b) =>
            typeof a === 'string' || typeof b === 'string' ? a === b : a.key === b.key
          }
          onChange={(_, value) => {
            if (value === null) onChange({ product: null, productLabel: '' });
            else if (typeof value === 'string') onChange({ product: null, productLabel: value });
            else {
              onChange({
                product: { kind: 'fertilizer', key: value.key },
                productLabel: value.label,
                ...prefillFrom(value),
              });
            }
          }}
          onInputChange={(_, value, reason) => {
            if (reason === 'input') onChange({ product: null, productLabel: value });
          }}
          renderInput={(params) => (
            <TextField
              {...params}
              label={t('pages.bed.care.form.product')}
              helperText={errorText('productLabel') ?? t('pages.bed.care.form.productHint')}
              error={Boolean(errors.productLabel)}
              sx={TOUCH_HEIGHT}
              slotProps={{
                ...params.slotProps,
                htmlInput: {
                  ...params.slotProps.htmlInput,
                  maxLength: TEXT_MAX,
                  'data-testid': `${testId}-product`,
                },
              }}
            />
          )}
        />
      )}

      {units.length > 0 && (
        <Box>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
            <TextField
              label={quantityLabel}
              value={state.quantity}
              onChange={(event) =>
                onChange({ quantity: event.target.value, quantityFromProduct: false })
              }
              error={Boolean(errors.quantity)}
              helperText={errorText('quantity')}
              sx={{ flex: 1, ...TOUCH_HEIGHT }}
              slotProps={{
                htmlInput: { inputMode: 'decimal', 'data-testid': `${testId}-quantity` },
              }}
            />
            <TextField
              select
              label={t('pages.bed.care.form.unit')}
              value={unit}
              onChange={(event) => onChange({ unit: event.target.value as CareUnit })}
              disabled={units.length === 1}
              sx={{ width: { xs: 132, sm: 160 }, flexShrink: 0, ...TOUCH_HEIGHT }}
              slotProps={{
                htmlInput: {
                  'data-testid': `${testId}-unit`,
                  'aria-describedby': noAreaHintShown ? `${testId}-no-area-hint` : undefined,
                },
              }}
            >
              {units.map((option) => (
                <MenuItem
                  key={option}
                  value={option}
                  disabled={blocked && isAreaUnit(option)}
                  sx={{ minHeight: touchTarget }}
                  data-testid={`${testId}-unit-${option}`}
                >
                  {t(`enums.careUnit.${option}`)}
                </MenuItem>
              ))}
            </TextField>
          </Box>
          {noAreaHintShown && (
            <FormHelperText
              id={`${testId}-no-area-hint`}
              sx={{ mx: 1.75 }}
              data-testid={`${testId}-no-area-hint`}
            >
              {t('pages.bed.care.form.noAreaHint')}
            </FormHelperText>
          )}
        </Box>
      )}

      {(total || nitrogen || state.quantityFromProduct) && (
        <Box
          data-testid={`${testId}-dose-info`}
          sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}
        >
          {state.quantityFromProduct && (
            <Typography
              variant="caption"
              color="text.secondary"
              data-testid={`${testId}-rate-source`}
            >
              {t('pages.bed.care.form.rateFromDataSheet')}
            </Typography>
          )}
          {total && (
            <Typography
              variant="body2"
              role="status"
              aria-atomic="true"
              data-testid={`${testId}-total`}
            >
              {t('pages.bed.care.form.areaTotal', {
                total: formatNumber(total.displayTotal, {
                  maximumFractionDigits: total.quantityTotalUnit === 'l' ? 1 : 0,
                }),
                unit: t(`pages.bed.care.form.totalUnit.${total.quantityTotalUnit}`),
                area: decimal(areaM2 ?? 0),
              })}
              {unit === 'l_per_m2' &&
                quantity !== null &&
                ` ${t('pages.bed.care.form.layerMm', { mm: decimal(lPerM2ToMm(quantity)) })}`}
            </Typography>
          )}
          {nitrogen && (
            <Typography variant="body2" data-testid={`${testId}-nitrogen`}>
              {t('pages.bed.care.form.nitrogenApprox', {
                kgPerHa: formatNumber(nitrogen.kgNPerHa, { maximumFractionDigits: 0 }),
                gPerM2: decimal(nitrogen.gNPerM2),
              })}
              <Typography
                component="span"
                variant="caption"
                color="text.secondary"
                sx={{ display: 'block' }}
              >
                {t('pages.bed.care.form.nitrogenApproxHint')}
              </Typography>
            </Typography>
          )}
        </Box>
      )}

      {kind === 'watering' && (
        <TextField
          select
          label={t('pages.bed.care.form.source')}
          value={state.material}
          onChange={(event) => onChange({ material: event.target.value })}
          sx={TOUCH_HEIGHT}
          slotProps={{ htmlInput: { 'data-testid': `${testId}-source` } }}
        >
          <MenuItem value="">{t('pages.bed.care.form.sourceUnknown')}</MenuItem>
          {WATER_SOURCES.map((source) => (
            <MenuItem key={source} value={source}>
              {t(`enums.waterSource.${source}`)}
            </MenuItem>
          ))}
        </TextField>
      )}

      {materialOptions.length > 0 && (
        <Autocomplete<string, false, false, true>
          freeSolo
          options={[...materialOptions]}
          value={state.material}
          getOptionLabel={materialLabel}
          onChange={(_, value) => onChange({ material: value ?? '' })}
          onInputChange={(_, value, reason) => {
            if (reason === 'input') onChange({ material: value });
          }}
          renderInput={(params) => (
            <TextField
              {...params}
              label={t('pages.bed.care.form.material')}
              error={Boolean(errors.material)}
              helperText={errorText('material') ?? t('pages.bed.care.form.materialHint')}
              sx={TOUCH_HEIGHT}
              slotProps={{
                ...params.slotProps,
                htmlInput: {
                  ...params.slotProps.htmlInput,
                  maxLength: TEXT_MAX,
                  'data-testid': `${testId}-material`,
                },
              }}
            />
          )}
        />
      )}

      {showsLimingHint(category, state.material) && (
        <Alert severity="info" role="note" data-testid={`${testId}-liming-hint`}>
          {t('pages.bed.care.form.limingHint')}
        </Alert>
      )}

      <TextField
        label={t(noteLabelKey)}
        value={state.note}
        onChange={(event) => onChange({ note: event.target.value })}
        multiline
        minRows={2}
        error={Boolean(errors.note)}
        helperText={errorText('note')}
        slotProps={{ htmlInput: { maxLength: NOTE_MAX, 'data-testid': `${testId}-note` } }}
      />

      <TextField
        type="datetime-local"
        label={t('pages.bed.care.form.performedAt')}
        value={state.performedAt}
        onChange={(event) =>
          onChange({ performedAt: event.target.value, performedAtTouched: true })
        }
        error={Boolean(errors.performedAt)}
        helperText={errorText('performedAt') ?? t('pages.bed.care.form.performedAtHint')}
        sx={TOUCH_HEIGHT}
        slotProps={{
          inputLabel: { shrink: true },
          htmlInput: { min: bounds.min, max: bounds.max, 'data-testid': `${testId}-performed-at` },
        }}
      />
    </Box>
  );
}
