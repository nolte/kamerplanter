import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Autocomplete, { createFilterOptions } from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';
import type { PlantInstance } from '@/api/types';

interface PlantInstanceAutocompleteFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  instances: PlantInstance[];
  /** When true the field stores an array of keys (multi-select); otherwise a single key string. */
  multiple?: boolean;
  helperText?: string;
  disabled?: boolean;
  required?: boolean;
  autoFocus?: boolean;
}

/** Flattened representation used by createFilterOptions to search across all relevant fields. */
export interface PlantInstanceOption {
  instance: PlantInstance;
  searchText: string;
}

const filterOptions = createFilterOptions<PlantInstanceOption>({
  stringify: (option) => option.searchText,
  matchFrom: 'any',
  trim: true,
});

/** Human-readable primary label for a plant instance — never the raw `_key`. */
export function getPlantInstanceLabel(instance: PlantInstance): string {
  return instance.plant_name?.trim() || instance.instance_id;
}

/** Species context line (scientific name) for a plant instance, if available. */
function getSpeciesContext(instance: PlantInstance): string | null {
  const scientific = instance.species?.scientific_name?.trim();
  return scientific || null;
}

export function buildPlantInstanceOptions(instances: PlantInstance[]): PlantInstanceOption[] {
  const mapped = instances.map((instance) => ({
    instance,
    searchText: [
      instance.plant_name ?? '',
      instance.instance_id,
      instance.species?.scientific_name ?? '',
      ...(instance.species?.common_names ?? []),
    ].join(' '),
  }));

  return mapped.sort((a, b) =>
    getPlantInstanceLabel(a.instance).localeCompare(getPlantInstanceLabel(b.instance)),
  );
}

/**
 * Name-based plant-instance picker (single or multi-select) for react-hook-form.
 *
 * Mirrors `SpeciesAutocompleteField`: the user only ever sees human-readable
 * names (`plant_name` / `instance_id`, with the species as secondary context)
 * while the form value stays the internal ArangoDB `_key`(s). The user never
 * types a raw key. Filtering is client-side over the pre-fetched `instances`
 * list (see `usePlantInstanceOptions`).
 */
export default function PlantInstanceAutocompleteField<T extends FieldValues>({
  name,
  control,
  label,
  instances,
  multiple = false,
  helperText,
  disabled,
  required,
  autoFocus,
}: PlantInstanceAutocompleteFieldProps<T>) {
  const { t } = useTranslation();

  const sortedOptions = useMemo<PlantInstanceOption[]>(
    () => buildPlantInstanceOptions(instances),
    [instances],
  );

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => {
        const value: PlantInstanceOption | PlantInstanceOption[] | null = multiple
          ? sortedOptions.filter(
              (o) => Array.isArray(field.value) && field.value.includes(o.instance.key),
            )
          : (sortedOptions.find((o) => o.instance.key === field.value) ?? null);

        return (
          <Autocomplete
            multiple={multiple}
            value={value}
            onChange={(_e, newVal) => {
              if (multiple) {
                const selected = (newVal as PlantInstanceOption[] | null) ?? [];
                field.onChange(selected.map((o) => o.instance.key));
              } else {
                const selected = newVal as PlantInstanceOption | null;
                field.onChange(selected?.instance.key ?? '');
              }
            }}
            options={sortedOptions}
            filterOptions={filterOptions}
            getOptionLabel={(o) => getPlantInstanceLabel(o.instance)}
            isOptionEqualToValue={(opt, val) => opt.instance.key === val.instance.key}
            disabled={disabled}
            fullWidth
            sx={{ mb: 2 }}
            noOptionsText={t('components.plantInstancePicker.noResults')}
            renderOption={({ key: liKey, ...props }, option) => {
              const { instance } = option;
              const context = getSpeciesContext(instance);
              return (
                <Box
                  component="li"
                  key={liKey}
                  {...props}
                  sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', py: 1 }}
                >
                  <Typography variant="body2" noWrap>
                    {getPlantInstanceLabel(instance)}
                  </Typography>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ fontStyle: 'italic' }}
                    noWrap
                  >
                    {instance.instance_id}
                    {context && ` · ${context}`}
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
                helperText={
                  error?.message ?? helperText ?? t('components.plantInstancePicker.searchHelper')
                }
                data-testid={`form-field-${name}`}
              />
            )}
          />
        );
      }}
    />
  );
}
