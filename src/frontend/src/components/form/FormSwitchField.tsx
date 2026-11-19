import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import FormHelperText from '@mui/material/FormHelperText';
import Box from '@mui/material/Box';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';
import FieldHelp from './FieldHelp';

interface FormSwitchFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  disabled?: boolean;
  helperText?: string;
  /**
   * Glossary key of the domain term this field asks for (e.g. "ec", "vpd") —
   * renders the shared `HelpTooltip` next to the field (#3020, UI-NFR-011 §6.1).
   */
  helpTerm?: string;
}

export default function FormSwitchField<T extends FieldValues>({
  name,
  control,
  label,
  disabled,
  helperText,
  helpTerm,
}: FormSwitchFieldProps<T>) {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => (
        <Box sx={{ mb: 2 }} data-testid={`form-field-${name}`}>
          <FieldHelp helpTerm={helpTerm} variant="inline">
            <FormControlLabel
              control={
                <Switch
                  checked={!!field.value}
                  onChange={field.onChange}
                  // `?? field.disabled` honours `useForm({ disabled })` / `<Controller disabled>`;
                  // a bare `disabled={disabled}` overwrites RHF's value with `undefined` (#1402 C).
                  disabled={disabled ?? field.disabled}
                />
              }
              label={label}
            />
          </FieldHelp>
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
