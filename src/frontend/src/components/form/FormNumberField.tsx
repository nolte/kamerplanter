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
          onChange={(e) => {
            const val = e.target.value;
            field.onChange(val === '' ? '' : Number(val));
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
          inputProps={{ min, max, step: step ?? 'any', inputMode: inputMode ?? 'decimal' }}
          InputProps={adornment ? { endAdornment: adornment } : undefined}
          data-testid={`form-field-${name}`}
        />
      )}
    />
  );
}
