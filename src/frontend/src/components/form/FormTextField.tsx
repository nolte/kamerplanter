import TextField from '@mui/material/TextField';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';

interface FormTextFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  required?: boolean;
  multiline?: boolean;
  rows?: number;
  /** Minimum visible rows for multiline fields (allows growing beyond). */
  minRows?: number;
  disabled?: boolean;
  type?: string;
  helperText?: string;
  autoFocus?: boolean;
  placeholder?: string;
}

export default function FormTextField<T extends FieldValues>({
  name,
  control,
  label,
  required,
  multiline,
  rows,
  minRows,
  disabled,
  type = 'text',
  helperText,
  autoFocus,
  placeholder,
}: FormTextFieldProps<T>) {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => (
        <TextField
          {...field}
          value={field.value ?? ''}
          label={label}
          required={required}
          multiline={multiline}
          rows={rows}
          minRows={minRows}
          disabled={disabled}
          type={type}
          autoFocus={autoFocus}
          placeholder={placeholder}
          error={!!error}
          helperText={error?.message ?? helperText}
          fullWidth
          margin="dense"
          sx={{ mb: 1.5 }}
          data-testid={`form-field-${name}`}
        />
      )}
    />
  );
}
