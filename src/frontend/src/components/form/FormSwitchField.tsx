import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import FormHelperText from '@mui/material/FormHelperText';
import Box from '@mui/material/Box';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';

interface FormSwitchFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  disabled?: boolean;
  helperText?: string;
}

export default function FormSwitchField<T extends FieldValues>({
  name,
  control,
  label,
  disabled,
  helperText,
}: FormSwitchFieldProps<T>) {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => (
        <Box sx={{ mb: 2 }} data-testid={`form-field-${name}`}>
          <FormControlLabel
            control={
              <Switch
                checked={!!field.value}
                onChange={field.onChange}
                disabled={disabled}
              />
            }
            label={label}
          />
          {(error?.message ?? helperText) && (
            <FormHelperText error={!!error}>
              {error?.message ?? helperText}
            </FormHelperText>
          )}
        </Box>
      )}
    />
  );
}
