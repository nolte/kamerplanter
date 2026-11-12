import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Autocomplete, { createFilterOptions } from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';
import type { Species } from '@/api/types';
import { getSpeciesOptionLabel, orderCommonNamesForLanguage } from '@/utils/plantDisplay';

interface SpeciesAutocompleteFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  species: Species[];
  helperText?: string;
  disabled?: boolean;
  required?: boolean;
  autoFocus?: boolean;
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

export default function SpeciesAutocompleteField<T extends FieldValues>({
  name,
  control,
  label,
  species,
  helperText,
  disabled,
  required,
  autoFocus,
}: SpeciesAutocompleteFieldProps<T>) {
  const { t, i18n } = useTranslation();
  const language = i18n.language;

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

    // Sorted by the label the user reads — the common name in the UI language (#2902).
    return mapped.sort((a, b) =>
      getSpeciesOptionLabel(a.species, language).localeCompare(
        getSpeciesOptionLabel(b.species, language),
        language,
      ),
    );
  }, [species, language]);

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
            getOptionLabel={(o) => getSpeciesOptionLabel(o.species, language)}
            isOptionEqualToValue={(opt, val) => opt.species.key === val.species.key}
            disabled={disabled}
            fullWidth
            sx={{ mb: 2 }}
            noOptionsText={t('pages.plantInstances.speciesNoResults')}
            renderOption={({ key: liKey, ...props }, option) => {
              const { species: sp } = option;
              const names = orderCommonNamesForLanguage(sp, language);
              const commonNames = names.length ? names.join(', ') : null;
              return (
                <Box
                  component="li"
                  key={liKey}
                  {...props}
                  sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', py: 1 }}
                >
                  <Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>
                    {commonNames ?? sp.scientific_name}
                  </Typography>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ fontStyle: 'italic' }}
                    noWrap
                  >
                    {sp.scientific_name}
                    {sp.family_name && ` · ${sp.family_name}`}
                  </Typography>
                </Box>
              );
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                label={label}
                required={required}
                autoFocus={autoFocus}
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
