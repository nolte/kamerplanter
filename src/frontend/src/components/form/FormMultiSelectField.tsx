import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';

interface SelectOption {
  value: string;
  label: string;
}

interface FormMultiSelectFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  options: SelectOption[];
  required?: boolean;
  disabled?: boolean;
  helperText?: string;
}

export default function FormMultiSelectField<T extends FieldValues>({
  name,
  control,
  label,
  options,
  required,
  disabled,
  helperText,
}: FormMultiSelectFieldProps<T>) {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => (
        <TextField
          {...field}
          select
          label={label}
          required={required}
          disabled={disabled}
          error={!!error}
          helperText={error?.message ?? helperText}
          fullWidth
          sx={{ mb: 2 }}
          data-testid={`form-field-${name}`}
          slotProps={{
            select: {
              multiple: true,
              renderValue: (selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {(selected as string[]).map((val) => {
                    const opt = options.find((o) => o.value === val);
                    return <Chip key={val} label={opt?.label ?? val} size="small" />;
                  })}
                </Box>
              ),
            },
          }}
        >
          {options.map((opt) => (
            <MenuItem key={opt.value} value={opt.value}>
              {opt.label}
            </MenuItem>
          ))}
        </TextField>
      )}
    />
  );
}
