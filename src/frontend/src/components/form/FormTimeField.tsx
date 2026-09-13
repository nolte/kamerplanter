import TextField from '@mui/material/TextField';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';

interface FormTimeFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  required?: boolean;
  disabled?: boolean;
  helperText?: string;
}

export default function FormTimeField<T extends FieldValues>({
  name,
  control,
  label,
  required,
  disabled,
  helperText,
}: FormTimeFieldProps<T>) {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => (
        <TextField
          {...field}
          value={field.value ?? ''}
          type="time"
          label={label}
          required={required}
          // `?? field.disabled` honours `useForm({ disabled })` / `<Controller disabled>`;
          // a bare `disabled={disabled}` overwrites RHF's value with `undefined` (#1402 C).
          disabled={disabled ?? field.disabled}
          error={!!error}
          helperText={error?.message ?? helperText}
          fullWidth
          sx={{ mb: 2 }}
          slotProps={{ inputLabel: { shrink: true } }}
        />
      )}
    />
  );
}
