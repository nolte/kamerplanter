import TextField from '@mui/material/TextField';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';

interface FormDateFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  required?: boolean;
  disabled?: boolean;
  /** Extra helper/error text shown below the field, e.g. for cross-field validation
   *  (such as "end date before start date") that the Zod schema doesn't cover per-field. */
  helperText?: string;
  /** Marks the field as invalid even without a Zod fieldState error (cross-field validation). */
  error?: boolean;
}

export default function FormDateField<T extends FieldValues>({
  name,
  control,
  label,
  required,
  disabled,
  helperText,
  error,
}: FormDateFieldProps<T>) {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error: fieldError } }) => (
        <TextField
          {...field}
          type="date"
          label={label}
          required={required}
          disabled={disabled}
          error={!!fieldError || !!error}
          helperText={fieldError?.message ?? helperText}
          fullWidth
          sx={{ mb: 2 }}
          slotProps={{ inputLabel: { shrink: true } }}
          data-testid={`form-field-${name}`}
        />
      )}
    />
  );
}
