import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface FormSelectFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  options: SelectOption[];
  required?: boolean;
  disabled?: boolean;
  helperText?: string;
  autoFocus?: boolean;
}

export default function FormSelectField<T extends FieldValues>({
  name,
  control,
  label,
  options,
  required,
  disabled,
  helperText,
  autoFocus,
}: FormSelectFieldProps<T>) {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => (
        <TextField
          {...field}
          value={field.value ?? ''}
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
            Each option carries a dedicated testid `form-option-{name}-{value}` and
            a stable `data-value` (from `value`), so tests select by value rather
            than by i18n label text. The clickable trigger is addressed in tests via
            the ARIA `[data-testid='form-field-{name}'] [role='combobox']` (stable
            across MUI versions) instead of the internal `.MuiSelect-select` class.
          */}
          {options.map((opt) => (
            <MenuItem
              key={opt.value}
              value={opt.value}
              disabled={opt.disabled}
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
