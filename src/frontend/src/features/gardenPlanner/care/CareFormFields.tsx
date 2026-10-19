/**
 * The short, category-specific care form (REQ-053 GP-FR-084): watering asks for litres and source,
 * feeding for product, amount and unit, mulching for material and thickness, anything else for a
 * note. Every field is optional; the instant defaults to now and may be backdated by a year
 * (GP-FR-085). Shared by the completion dialog, the batch dialog and the log dialog.
 */
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import { fetchAllFertilizers } from '@/api/endpoints/fertilizers';
import { formKindOf, MATERIALS_BY_KIND, UNITS_BY_KIND, WATER_SOURCES } from './careCategories';
import { defaultUnit, performedAtBounds, type CareFormState, type FormErrors } from './careForm';
import type { CareUnit } from './careTypes';

const NOTE_MAX = 2000;
const TEXT_MAX = 200;
/** Fields stack on a phone and pair up from `sm`; each control keeps the 48 px touch height. */
const TOUCH_HEIGHT = { '& .MuiInputBase-root': { minHeight: 48 } };

interface FertilizerOption {
  key: string;
  label: string;
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
              label: fertilizer.brand ? `${fertilizer.product_name} (${fertilizer.brand})` : fertilizer.product_name,
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
}

export default function CareFormFields({
  category,
  state,
  errors,
  onChange,
  now,
  testId,
  noteLabelKey = 'pages.bed.care.form.note',
}: CareFormFieldsProps) {
  const { t } = useTranslation();
  const kind = formKindOf(category);
  const units = UNITS_BY_KIND[kind];
  const fertilizers = useFertilizerOptions(kind === 'feeding');
  const bounds = useMemo(() => performedAtBounds(now), [now]);
  const unit: CareUnit | '' = state.unit !== '' ? state.unit : defaultUnit(kind);
  const materialOptions = MATERIALS_BY_KIND[kind] ?? [];
  const errorText = (field: keyof FormErrors) => {
    const code = errors[field];
    return code ? t(`pages.bed.care.errors.${code}`) : undefined;
  };
  const materialLabel = (code: string) =>
    materialOptions.includes(code) ? t(`enums.careMaterial.${code}`) : code;
  const product = fertilizers.find((option) => option.key === state.product?.key) ?? null;

  const quantityLabel = t(`pages.bed.care.form.quantity.${kind === 'note' ? 'amount' : kind}`);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }} data-testid={`${testId}-fields`}>
      {kind === 'feeding' && (
        <Autocomplete<FertilizerOption, false, false, true>
          freeSolo
          options={fertilizers}
          value={product ?? state.productLabel}
          getOptionLabel={(option) => (typeof option === 'string' ? option : option.label)}
          isOptionEqualToValue={(a, b) => (typeof a === 'string' || typeof b === 'string' ? a === b : a.key === b.key)}
          onChange={(_, value) => {
            if (value === null) onChange({ product: null, productLabel: '' });
            else if (typeof value === 'string') onChange({ product: null, productLabel: value });
            else onChange({ product: { kind: 'fertilizer', key: value.key }, productLabel: value.label });
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
                htmlInput: { ...params.slotProps.htmlInput, maxLength: TEXT_MAX, 'data-testid': `${testId}-product` },
              }}
            />
          )}
        />
      )}

      {units.length > 0 && (
        <Box sx={{ display: 'flex', gap: 1, flexDirection: { xs: 'column', sm: 'row' } }}>
          <TextField
            label={quantityLabel}
            value={state.quantity}
            onChange={(event) => onChange({ quantity: event.target.value })}
            error={Boolean(errors.quantity)}
            helperText={errorText('quantity')}
            sx={{ flex: 1, ...TOUCH_HEIGHT }}
            slotProps={{ htmlInput: { inputMode: 'decimal', 'data-testid': `${testId}-quantity` } }}
          />
          <TextField
            select
            label={t('pages.bed.care.form.unit')}
            value={unit}
            onChange={(event) => onChange({ unit: event.target.value as CareUnit })}
            disabled={units.length === 1}
            sx={{ minWidth: { sm: 160 }, ...TOUCH_HEIGHT }}
            slotProps={{ htmlInput: { 'data-testid': `${testId}-unit` } }}
          >
            {units.map((option) => (
              <MenuItem key={option} value={option}>
                {t(`enums.careUnit.${option}`)}
              </MenuItem>
            ))}
          </TextField>
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
              helperText={errorText('material')}
              sx={TOUCH_HEIGHT}
              slotProps={{
                ...params.slotProps,
                htmlInput: { ...params.slotProps.htmlInput, maxLength: TEXT_MAX, 'data-testid': `${testId}-material` },
              }}
            />
          )}
        />
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
        onChange={(event) => onChange({ performedAt: event.target.value, performedAtTouched: true })}
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
