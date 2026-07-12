import { useMemo } from 'react';
import type { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import Autocomplete, { createFilterOptions } from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import type { PlantInstance } from '@/api/types';
import {
  buildPlantInstanceOptions,
  getPlantInstanceLabel,
  type PlantInstanceOption,
} from './PlantInstanceAutocompleteField';

interface PlantInstancePickerProps {
  label: string;
  instances: PlantInstance[];
  /** Currently selected plant instance `_key` (empty string = none). */
  value: string;
  onChange: (key: string) => void;
  helperText?: string;
  disabled?: boolean;
  loading?: boolean;
  size?: 'small' | 'medium';
  fullWidth?: boolean;
  /** Applied to the TextField root for test targeting. */
  testId?: string;
}

const filterOptions = createFilterOptions<PlantInstanceOption>({
  stringify: (option) => option.searchText,
  matchFrom: 'any',
  trim: true,
});

/**
 * Controlled (non-RHF) single-select plant-instance picker for the read-only
 * lineage explorer. Shares option building + labelling with
 * {@link PlantInstanceAutocompleteField}; the user picks by name and the
 * component emits the internal `_key`, never requiring a raw key to be typed.
 */
export default function PlantInstancePicker({
  label,
  instances,
  value,
  onChange,
  helperText,
  disabled,
  loading,
  size = 'small',
  fullWidth = true,
  testId,
}: PlantInstancePickerProps): ReactElement {
  const { t } = useTranslation();

  const sortedOptions = useMemo<PlantInstanceOption[]>(
    () => buildPlantInstanceOptions(instances),
    [instances],
  );

  const selected = useMemo(
    () => sortedOptions.find((o) => o.instance.key === value) ?? null,
    [sortedOptions, value],
  );

  return (
    <Autocomplete
      value={selected}
      onChange={(_e, newVal) => onChange(newVal?.instance.key ?? '')}
      options={sortedOptions}
      filterOptions={filterOptions}
      getOptionLabel={(o) => getPlantInstanceLabel(o.instance)}
      isOptionEqualToValue={(opt, val) => opt.instance.key === val.instance.key}
      disabled={disabled || loading}
      fullWidth={fullWidth}
      size={size}
      noOptionsText={t('components.plantInstancePicker.noResults')}
      renderOption={({ key: liKey, ...props }, option) => {
        const { instance } = option;
        const context = instance.species?.scientific_name?.trim() || null;
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
          helperText={loading ? t('components.plantInstancePicker.loading') : helperText}
          data-testid={testId}
        />
      )}
    />
  );
}
