import TextField from '@mui/material/TextField';
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
}: FormNumberFieldProps<T>) {
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
          sx={{ mb: 2 }}
          inputProps={{ min, max, step: step ?? 'any' }}
        />
      )}
    />
  );
}
