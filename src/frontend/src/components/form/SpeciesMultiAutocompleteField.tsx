import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Autocomplete, { createFilterOptions } from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';
import type { Species } from '@/api/types';

interface SpeciesMultiAutocompleteFieldProps<T extends FieldValues> {
  /** Form field holding a `string[]` of species keys. */
  name: Path<T>;
  control: Control<T>;
  label: string;
  species: Species[];
  helperText?: string;
  disabled?: boolean;
}

/** One selectable species, flattened so the filter can search every name at once. */
interface SpeciesOption {
  key: string;
  label: string;
  searchText: string;
}

const filterOptions = createFilterOptions<SpeciesOption>({
  stringify: (option) => option.searchText,
  matchFrom: 'any',
  trim: true,
});

function toOption(species: Species): SpeciesOption {
  const commonName = species.common_names?.[0];
  return {
    key: species.key,
    label: commonName ? `${commonName} (${species.scientific_name})` : species.scientific_name,
    searchText: [species.scientific_name, ...(species.common_names ?? []), species.genus, species.family_name ?? ''].join(
      ' ',
    ),
  };
}

/**
 * Multi-select counterpart of `SpeciesAutocompleteField`: picks several species
 * and stores their keys as a `string[]` (#1618, nutrient-plan species relation).
 *
 * A stored key the catalogue does not (yet) hold — the catalogue is still
 * loading, or the species is not visible — is kept as a chip showing the raw key
 * rather than dropped: removing it silently on the next change would rewrite the
 * relation behind the user's back.
 */
export default function SpeciesMultiAutocompleteField<T extends FieldValues>({
  name,
  control,
  label,
  species,
  helperText,
  disabled,
}: SpeciesMultiAutocompleteFieldProps<T>) {
  const { t } = useTranslation();

  const options = useMemo<SpeciesOption[]>(
    () => species.map(toOption).sort((a, b) => a.label.localeCompare(b.label)),
    [species],
  );
  const byKey = useMemo(() => new Map(options.map((o) => [o.key, o])), [options]);

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => {
        const keys: string[] = Array.isArray(field.value) ? (field.value as string[]) : [];
        const selected = keys.map(
          (key) => byKey.get(key) ?? { key, label: key, searchText: key },
        );
        return (
          <Autocomplete
            multiple
            value={selected}
            onChange={(_e, newVal) => field.onChange(newVal.map((o) => o.key))}
            onBlur={field.onBlur}
            options={options}
            filterOptions={filterOptions}
            filterSelectedOptions
            getOptionLabel={(o) => o.label}
            isOptionEqualToValue={(opt, val) => opt.key === val.key}
            // `?? field.disabled` honours `useForm({ disabled })` (#1402 C).
            disabled={disabled ?? field.disabled}
            fullWidth
            sx={{ mb: 2 }}
            noOptionsText={t('pages.plantInstances.speciesNoResults')}
            renderOption={({ key: liKey, ...props }, option) => (
              <Box
                component="li"
                key={liKey}
                {...props}
                sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', py: 1 }}
              >
                <Typography variant="body2">{option.label}</Typography>
              </Box>
            )}
            renderInput={(params) => (
              <TextField
                {...params}
                name={name}
                label={label}
                error={!!error}
                helperText={error?.message ?? helperText}
                data-testid={`form-field-${name}`}
              />
            )}
          />
        );
      }}
    />
  );
}
