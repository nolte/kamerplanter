import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Autocomplete, { createFilterOptions } from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';
import { getTimezoneOptions } from '@/pages/pflanzen/calculations/timezones';

interface FormTimezoneFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  helperText?: string;
  required?: boolean;
  disabled?: boolean;
}

// The runtime's IANA zone list runs to 400+ entries. Without a cap, opening
// the (unfiltered) dropdown on a phone renders hundreds of list items into
// the DOM at once — a real scroll/paint cost on low-end mobile hardware,
// which is the primary device class for this app (UI-NFR-001 mobile-first).
// `createFilterOptions` (MUI-native, no extra dependency) still searches the
// full list as the user types; only the *unfiltered* view is truncated, and
// the already-selected/legacy value (prepended in `options` below) always
// survives the cut because it sorts first.
const MAX_VISIBLE_OPTIONS = 50;
const filterOptions = createFilterOptions<string>({ limit: MAX_VISIBLE_OPTIONS });

/**
 * Searchable IANA time-zone picker for react-hook-form fields. Backs the free-text
 * timezone input on the site form with the runtime's full zone list (via
 * {@link getTimezoneOptions}), while keeping any already-stored value selectable —
 * e.g. the legacy `UTC` default, which `Intl.supportedValuesOf` may not list.
 */
export default function FormTimezoneField<T extends FieldValues>({
  name,
  control,
  label,
  helperText,
  required,
  disabled,
}: FormTimezoneFieldProps<T>) {
  const { t } = useTranslation();
  const baseOptions = useMemo(() => getTimezoneOptions(), []);
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => {
        const value = (field.value as string) ?? '';
        const options = value && !baseOptions.includes(value)
          ? [value, ...baseOptions]
          : baseOptions;
        return (
          <Autocomplete
            options={options}
            filterOptions={filterOptions}
            value={value || null}
            onChange={(_e, newVal) => field.onChange(newVal ?? '')}
            onBlur={field.onBlur}
            disabled={disabled}
            disableClearable={required}
            autoHighlight
            fullWidth
            noOptionsText={t('pages.sites.timezoneNoResults')}
            sx={{ mb: 1.5 }}
            renderInput={(params) => (
              <TextField
                {...params}
                inputRef={field.ref}
                label={label}
                required={required}
                error={!!error}
                helperText={error?.message ?? helperText}
                margin="dense"
                data-testid={`form-field-${name}`}
              />
            )}
          />
        );
      }}
    />
  );
}
