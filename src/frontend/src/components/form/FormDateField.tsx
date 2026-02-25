import TextField from '@mui/material/TextField';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';

interface FormDateFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  required?: boolean;
  disabled?: boolean;
}

export default function FormDateField<T extends FieldValues>({
  name,
  control,
  label,
  required,
  disabled,
}: FormDateFieldProps<T>) {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => (
        <TextField
          {...field}
          type="date"
          label={label}
          required={required}
          disabled={disabled}
          error={!!error}
          helperText={error?.message}
          fullWidth
          sx={{ mb: 2 }}
          InputLabelProps={{ shrink: true }}
        />
      )}
    />
  );
}
