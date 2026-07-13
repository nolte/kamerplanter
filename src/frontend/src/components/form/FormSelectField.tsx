import type { HTMLAttributes } from 'react';
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
          SelectProps={{
            // Dedicated testid on the clickable select display so tests can open
            // the dropdown without depending on the internal `.MuiSelect-select`
            // class (which changes across MUI versions / restyles). Options are
            // addressable by their stable `data-value` (set from `value` below).
            SelectDisplayProps: {
              'data-testid': `form-field-${name}-trigger`,
            } as HTMLAttributes<HTMLDivElement>,
          }}
        >
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
