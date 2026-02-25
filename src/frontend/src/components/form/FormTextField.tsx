import TextField from '@mui/material/TextField';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';

interface FormTextFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  required?: boolean;
  multiline?: boolean;
  rows?: number;
  disabled?: boolean;
  type?: string;
  helperText?: string;
}

export default function FormTextField<T extends FieldValues>({
  name,
  control,
  label,
  required,
  multiline,
  rows,
  disabled,
  type = 'text',
  helperText,
}: FormTextFieldProps<T>) {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => (
        <TextField
          {...field}
          label={label}
          required={required}
          multiline={multiline}
          rows={rows}
          disabled={disabled}
          type={type}
          error={!!error}
          helperText={error?.message ?? helperText}
          fullWidth
          sx={{ mb: 2 }}
          data-testid={`form-field-${name}`}
        />
      )}
    />
  );
}
