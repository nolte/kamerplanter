import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';
import { useMonthLabels } from '@/hooks/useMonthLabels';

interface FormMonthFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  required?: boolean;
  disabled?: boolean;
  helperText?: string;
  autoFocus?: boolean;
  /**
   * Prepends an empty "– none –" option so an optional month can be cleared.
   * When set, the field value becomes '' on that choice; leave off for required
   * month fields.
   */
  includeEmpty?: boolean;
  /** Overrides the empty option's label; defaults to `t('common.none')`. */
  emptyLabel?: string;
}

/**
 * Month picker rendered as a localised dropdown (January…December) that still
 * submits the selected month as an integer 1–12 — or '' when cleared via
 * {@link FormMonthFieldProps.includeEmpty}. This lets forms replace an unintuitive
 * numeric 1–12 input without any backend/Zod schema change: the internal
 * `<select>` works on strings, so the value is mapped number→string on the way in
 * and string→number on the way out.
 *
 * Labels follow the active app locale via the shared {@link useMonthLabels} hook.
 */
export default function FormMonthField<T extends FieldValues>({
  name,
  control,
  label,
  required,
  disabled,
  helperText,
  autoFocus,
  includeEmpty,
  emptyLabel,
}: FormMonthFieldProps<T>) {
  const { t } = useTranslation();
  const monthLabels = useMonthLabels('long');

  const options = useMemo(
    () =>
      monthLabels.map((monthLabel, idx) => ({
        value: String(idx + 1),
        label: monthLabel,
      })),
    [monthLabels],
  );

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => (
        <TextField
          {...field}
          value={
            field.value === '' || field.value == null ? '' : String(field.value)
          }
          onChange={(e) => {
            const val = e.target.value;
            // Selecting the empty option emits `null` (#778 B2) — matching the
            // "submits '' → null" contract described below, which the previous
            // `''` did not honour. The `value` binding above already maps null
            // back to the empty MenuItem, so the select stays controlled.
            field.onChange(val === '' ? null : Number(val));
          }}
          select
          label={label}
          required={required}
          disabled={disabled}
          autoFocus={autoFocus}
          error={!!error}
          helperText={error?.message ?? helperText}
          fullWidth
          margin="dense"
          sx={{ mb: 1.5 }}
          data-testid={`form-field-${name}`}
        >
          {/*
            Options mirror FormSelectField's testids (`form-option-{name}-{value}`)
            so tests can target a month by its integer value rather than the
            locale-dependent label. The empty option (optional fields) carries the
            `-empty` suffix and submits '' → null.
          */}
          {includeEmpty && (
            <MenuItem value="" data-testid={`form-option-${name}-empty`}>
              {emptyLabel ?? t('common.none')}
            </MenuItem>
          )}
          {options.map((opt) => (
            <MenuItem
              key={opt.value}
              value={opt.value}
              data-testid={`form-option-${name}-${opt.value}`}
            >
              {opt.label}
            </MenuItem>
          ))}
        </TextField>
      )}
    />
  );
}
