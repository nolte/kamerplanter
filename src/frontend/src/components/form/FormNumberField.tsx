import type { ReactNode } from 'react';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';

interface FormNumberFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  min?: number;
  max?: number;
  step?: number | 'any';
  required?: boolean;
  disabled?: boolean;
  helperText?: string;
  /** Short unit label rendered as end adornment (e.g. "L", "mS/cm", "°C"). */
  suffix?: string;
  /** Custom end adornment node. Takes precedence over suffix when both are provided. */
  endAdornment?: ReactNode;
  autoFocus?: boolean;
  inputMode?: 'numeric' | 'decimal';
}

export default function FormNumberField<T extends FieldValues>({
  name,
  control,
  label,
  min,
  max,
  step,
  required,
  disabled,
  helperText,
  suffix,
  endAdornment,
  autoFocus,
  inputMode,
}: FormNumberFieldProps<T>) {
  const adornment = endAdornment ?? (suffix ? (
    <InputAdornment position="end">{suffix}</InputAdornment>
  ) : undefined);

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => (
        <TextField
          {...field}
          value={field.value ?? ''}
          onChange={(e) => {
            const val = e.target.value;
            // Clearing the field emits `null`, not `''` (#778 B2). A numeric
            // field has no meaningful empty *string* value — the domain value
            // of "cleared" is absent, and `null` is what the API takes.
            //
            // Emitting `''` made `z.number().nullable()` reject a field the
            // user had emptied, so a filled duration could not be cleared
            // again: zod saw a string where it wanted a number or null. 112
            // schema lines across 38 files carry that plain nullable shape,
            // and only a handful had worked around it with
            // `z.union([z.number(), z.literal('')])`. Fixing the emitted value
            // once here is what makes the plain shape correct everywhere,
            // instead of teaching every schema about a quirk of this input.
            field.onChange(val === '' ? null : Number(val));
          }}
          type="number"
          label={label}
          required={required}
          disabled={disabled}
          error={!!error}
          helperText={error?.message ?? helperText}
          fullWidth
          autoFocus={autoFocus}
          margin="dense"
          sx={{ mb: 1.5 }}
          slotProps={{
            htmlInput: {
              // Only pass min/max when explicitly set — omitting them prevents
              // MUI from emitting aria-valuemin/aria-valuemax="0" as a fallback,
              // which would mislead screen readers into reporting a wrong range.
              ...(min !== undefined ? { min } : {}),
              ...(max !== undefined ? { max } : {}),
              step: step ?? 'any',
              inputMode: inputMode ?? 'decimal',
            },
            ...(adornment ? { input: { endAdornment: adornment } } : {}),
          }}
          data-testid={`form-field-${name}`}
        />
      )}
    />
  );
}
