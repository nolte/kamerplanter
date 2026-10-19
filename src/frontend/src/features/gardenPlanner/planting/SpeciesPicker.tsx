/** Species choice of the planting dialog: favourites first (GP-FR §11.1 step 2), searchable by any name. */
import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Autocomplete, { createFilterOptions } from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import type { Species } from '@/api/types';

export function speciesLabel(species: Species): string {
  const common = species.common_names?.[0];
  return common ? `${common} (${species.scientific_name})` : species.scientific_name;
}

const filter = createFilterOptions<Species>({
  stringify: (species) =>
    [species.scientific_name, ...(species.common_names ?? []), species.genus, species.family_name ?? ''].join(' '),
  matchFrom: 'any',
  trim: true,
});

interface SpeciesPickerProps {
  species: readonly Species[];
  value: string | null;
  favorites: ReadonlySet<string>;
  label: string;
  error?: string;
  autoFocus?: boolean;
  testId: string;
  onChange: (key: string | null) => void;
}

export default function SpeciesPicker({
  species,
  value,
  favorites,
  label,
  error,
  autoFocus,
  testId,
  onChange,
}: SpeciesPickerProps) {
  const { t } = useTranslation();
  const options = useMemo(
    () =>
      [...species].sort((a, b) => {
        const fa = favorites.has(a.key) ? 0 : 1;
        const fb = favorites.has(b.key) ? 0 : 1;
        return fa - fb || speciesLabel(a).localeCompare(speciesLabel(b));
      }),
    [species, favorites],
  );
  const selected = options.find((option) => option.key === value) ?? null;

  return (
    <Autocomplete
      options={options}
      value={selected}
      onChange={(_, next) => onChange(next?.key ?? null)}
      getOptionLabel={speciesLabel}
      isOptionEqualToValue={(option, current) => option.key === current.key}
      filterOptions={filter}
      groupBy={(option) =>
        favorites.size === 0
          ? ''
          : favorites.has(option.key)
            ? t('pages.bed.planting.species.favorites')
            : t('pages.bed.planting.species.others')
      }
      noOptionsText={t('pages.bed.planting.species.none')}
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          required
          autoFocus={autoFocus}
          error={Boolean(error)}
          helperText={error}
          data-testid={testId}
        />
      )}
      sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
    />
  );
}
