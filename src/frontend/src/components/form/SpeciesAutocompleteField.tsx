import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Autocomplete, { createFilterOptions } from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';
import type { Species } from '@/api/types';

interface SpeciesAutocompleteFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  species: Species[];
  helperText?: string;
  disabled?: boolean;
  required?: boolean;
}

/** Flattened representation used by createFilterOptions to search across all relevant fields. */
interface SpeciesFilterOption {
  species: Species;
  searchText: string;
}

const filterOptions = createFilterOptions<SpeciesFilterOption>({
  stringify: (option) => option.searchText,
  matchFrom: 'any',
  trim: true,
});

function getDisplayLabel(species: Species): string {
  const commonName = species.common_names?.[0];
  if (commonName) {
    return `${commonName} (${species.scientific_name})`;
  }
  return species.scientific_name;
}

export default function SpeciesAutocompleteField<T extends FieldValues>({
  name,
  control,
  label,
  species,
  helperText,
  disabled,
  required,
}: SpeciesAutocompleteFieldProps<T>) {
  const { t } = useTranslation();

  const sortedOptions = useMemo<SpeciesFilterOption[]>(() => {
    const mapped = species.map((s) => ({
      species: s,
      searchText: [
        s.scientific_name,
        ...(s.common_names ?? []),
        s.genus,
        s.family_name ?? '',
      ].join(' '),
    }));

    return mapped.sort((a, b) => {
      const aLabel = a.species.common_names?.[0] ?? a.species.scientific_name;
      const bLabel = b.species.common_names?.[0] ?? b.species.scientific_name;
      return aLabel.localeCompare(bLabel);
    });
  }, [species]);

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => {
        const selected = sortedOptions.find((o) => o.species.key === field.value) ?? null;
        return (
          <Autocomplete
            value={selected}
            onChange={(_e, newVal) => {
              field.onChange(newVal?.species.key ?? '');
            }}
            options={sortedOptions}
            filterOptions={filterOptions}
            getOptionLabel={(o) => getDisplayLabel(o.species)}
            isOptionEqualToValue={(opt, val) => opt.species.key === val.species.key}
            disabled={disabled}
            fullWidth
            sx={{ mb: 2 }}
            noOptionsText={t('pages.plantInstances.speciesNoResults')}
            renderOption={({ key: liKey, ...props }, option) => {
              const { species: sp } = option;
              const commonNames = sp.common_names?.length
                ? sp.common_names.join(', ')
                : null;
              return (
                <Box
                  component="li"
                  key={liKey}
                  {...props}
                  sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', py: 1 }}
                >
                  <Typography variant="body2" noWrap>
                    {commonNames ?? sp.scientific_name}
                  </Typography>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ fontStyle: 'italic' }}
                    noWrap
                  >
                    {sp.scientific_name}
                    {sp.family_name && ` \u00B7 ${sp.family_name}`}
                  </Typography>
                </Box>
              );
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                label={label}
                required={required}
                error={!!error}
                helperText={error?.message ?? helperText ?? t('pages.plantInstances.speciesSearchHelper')}
                data-testid={`form-field-${name}`}
              />
            )}
          />
        );
      }}
    />
  );
}
