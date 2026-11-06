import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Autocomplete, { createFilterOptions } from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutlineOutlined';
import { fetchAllFertilizers } from '@/api/endpoints/fertilizers';
import { listSites, listLocations } from '@/api/endpoints/sites';
import { listAllSpecies } from '@/api/endpoints/species';
import { useApiError } from '@/hooks/useApiError';
import type { Fertilizer, Location, Species } from '@/api/types';

/**
 * Shared master-data selectors for the Nutrient Calculations page (#610).
 *
 * The page previously asked users to hand-type comma-separated fertilizer keys
 * (and a `key:ml/L` micro-syntax for the EC budget). These components replace
 * that free text with `Autocomplete` selectors sourced from the fertilizer and
 * location catalogues, showing product name + brand and submitting `f.key` —
 * matching the existing pattern in `ChannelFertilizerDialog`/`DosageCalculatorTab`.
 *
 * The species selector of the area dosing replaces the former feeder-class
 * select (REQ-053 E-17 variant A): the N warning now reads the species'
 * own `nitrogen_fixing` flag on the server.
 *
 * The fertilizer/location/species lists are fetched once via the hooks below and shared
 * across every panel, so the selectors themselves are pure presentational
 * components that receive the option list as a prop.
 */

/** Human-readable option label: "Product (Brand)", falling back to the key. */
function fertilizerLabel(f: Fertilizer): string {
  if (!f.product_name) return f.key;
  return f.brand ? `${f.product_name} (${f.brand})` : f.product_name;
}

/**
 * Loads the complete fertilizer catalogue once and shares it across the page.
 * Returns a memoised object so consumers relying on referential stability
 * (FRONTEND.md useMemo obligation) don't re-render spuriously.
 */
export function useFertilizerOptions(): {
  fertilizers: Fertilizer[];
  loading: boolean;
} {
  const [fertilizers, setFertilizers] = useState<Fertilizer[]>([]);
  const [loading, setLoading] = useState(true);
  const { handleError } = useApiError();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await fetchAllFertilizers();
        if (!cancelled) setFertilizers(list);
      } catch (err) {
        if (!cancelled) handleError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [handleError]);

  return useMemo(() => ({ fertilizers, loading }), [fertilizers, loading]);
}

/**
 * Loads every location across all sites once (locations are scoped per site,
 * so we fan out over the site list). Returns a memoised object.
 */
export function useLocationOptions(): {
  locations: Location[];
  loading: boolean;
} {
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const { handleError } = useApiError();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const sites = await listSites(0, 200);
        const perSite = await Promise.all(
          sites.map((s) => listLocations(s.key)),
        );
        if (!cancelled) setLocations(perSite.flat());
      } catch (err) {
        if (!cancelled) handleError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [handleError]);

  return useMemo(() => ({ locations, loading }), [locations, loading]);
}

/**
 * Loads the species the tenant may read (own, global, granted) once.
 * Returns a memoised object (FRONTEND.md useMemo obligation).
 */
export function useSpeciesOptions(): {
  species: Species[];
  loading: boolean;
} {
  const [species, setSpecies] = useState<Species[]>([]);
  const [loading, setLoading] = useState(true);
  const { handleError } = useApiError();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const page = await listAllSpecies();
        if (!cancelled) setSpecies(page.items);
      } catch (err) {
        if (!cancelled) handleError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [handleError]);

  return useMemo(() => ({ species, loading }), [species, loading]);
}

interface FertilizerMultiSelectProps {
  options: Fertilizer[];
  /** Selected fertilizer keys. */
  value: string[];
  onChange: (keys: string[]) => void;
  label: string;
  helperText?: string;
  placeholder?: string;
  loading?: boolean;
}

/** Multi-select fertilizer picker submitting an array of `f.key`. */
export function FertilizerMultiSelect({
  options,
  value,
  onChange,
  label,
  helperText,
  placeholder,
  loading,
}: FertilizerMultiSelectProps) {
  const selected = useMemo(
    () =>
      value
        .map((k) => options.find((f) => f.key === k))
        .filter((f): f is Fertilizer => f != null),
    [value, options],
  );

  return (
    <Autocomplete
      multiple
      options={options}
      value={selected}
      onChange={(_, next) => onChange(next.map((f) => f.key))}
      getOptionLabel={fertilizerLabel}
      isOptionEqualToValue={(o, v) => o.key === v.key}
      loading={loading}
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          helperText={helperText}
          placeholder={selected.length === 0 ? placeholder : undefined}
        />
      )}
    />
  );
}

interface FertilizerSingleSelectProps {
  options: Fertilizer[];
  /** Selected fertilizer key, or empty string when none. */
  value: string;
  onChange: (key: string) => void;
  label: string;
  helperText?: string;
  loading?: boolean;
}

/** Single-select fertilizer picker submitting one `f.key` (clearable). */
export function FertilizerSingleSelect({
  options,
  value,
  onChange,
  label,
  helperText,
  loading,
}: FertilizerSingleSelectProps) {
  const selected = useMemo(
    () => options.find((f) => f.key === value) ?? null,
    [value, options],
  );

  return (
    <Autocomplete
      options={options}
      value={selected}
      onChange={(_, next) => onChange(next?.key ?? '')}
      getOptionLabel={fertilizerLabel}
      isOptionEqualToValue={(o, v) => o.key === v.key}
      loading={loading}
      fullWidth
      renderInput={(params) => (
        <TextField {...params} label={label} helperText={helperText} />
      )}
    />
  );
}

interface LocationSelectProps {
  options: Location[];
  /** Selected location key, or empty string when none. */
  value: string;
  onChange: (key: string) => void;
  label: string;
  helperText?: string;
  loading?: boolean;
}

/** Single-select location picker submitting one `location.key` (clearable). */
export function LocationSelect({
  options,
  value,
  onChange,
  label,
  helperText,
  loading,
}: LocationSelectProps) {
  const selected = useMemo(
    () => options.find((l) => l.key === value) ?? null,
    [value, options],
  );

  return (
    <Autocomplete
      options={options}
      value={selected}
      onChange={(_, next) => onChange(next?.key ?? '')}
      getOptionLabel={(l) =>
        l.area_m2 != null ? `${l.name} (${l.area_m2} m²)` : l.name
      }
      isOptionEqualToValue={(o, v) => o.key === v.key}
      loading={loading}
      fullWidth
      renderInput={(params) => (
        <TextField {...params} label={label} helperText={helperText} />
      )}
    />
  );
}

/** One row of the EC-budget fertilizer editor: a fertilizer key + ml/L dose. */
export interface EcBudgetFertilizerRow {
  key: string;
  mlPerLiter: number | '';
}

interface EcBudgetFertilizerRowsProps {
  options: Fertilizer[];
  rows: EcBudgetFertilizerRow[];
  onChange: (rows: EcBudgetFertilizerRow[]) => void;
  loading?: boolean;
}

/**
 * Repeatable rows editor replacing the `key:ml/L, key:ml/L` free-text
 * micro-syntax of the EC-budget panel. Each row pairs a fertilizer selector
 * with an optional numeric ml/L field, with add/remove controls.
 */
export function EcBudgetFertilizerRows({
  options,
  rows,
  onChange,
  loading,
}: EcBudgetFertilizerRowsProps) {
  const { t } = useTranslation();

  const updateRow = (index: number, patch: Partial<EcBudgetFertilizerRow>) => {
    onChange(rows.map((r, i) => (i === index ? { ...r, ...patch } : r)));
  };

  const addRow = () => {
    onChange([...rows, { key: '', mlPerLiter: '' }]);
  };

  const removeRow = (index: number) => {
    onChange(rows.filter((_, i) => i !== index));
  };

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        {t('pages.nutrientCalc.fertilizerRowsLabel')}
      </Typography>
      {rows.length === 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t('pages.nutrientCalc.fertilizerRowsEmpty')}
        </Typography>
      )}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        {rows.map((row, index) => (
          <Box
            key={index}
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              gap: 1,
              alignItems: { xs: 'stretch', sm: 'flex-start' },
            }}
          >
            <Box sx={{ flex: 2, minWidth: 0 }}>
              <FertilizerSingleSelect
                options={options}
                value={row.key}
                onChange={(key) => updateRow(index, { key })}
                label={t('pages.nutrientCalc.fertilizerRowProduct')}
                loading={loading}
              />
            </Box>
            <Box sx={{ flex: 1, minWidth: 0, display: 'flex', gap: 0.5 }}>
              <TextField
                type="number"
                label={t('pages.nutrientCalc.fertilizerRowDose')}
                value={row.mlPerLiter}
                onChange={(e) =>
                  updateRow(index, {
                    mlPerLiter:
                      e.target.value === '' ? '' : Number(e.target.value),
                  })
                }
                slotProps={{
                  htmlInput: { min: 0, step: 'any', inputMode: 'decimal' },
                }}
                fullWidth
              />
              <IconButton
                aria-label={t('pages.nutrientCalc.fertilizerRowRemove')}
                onClick={() => removeRow(index)}
                sx={{ alignSelf: 'center' }}
              >
                <DeleteOutlineIcon />
              </IconButton>
            </Box>
          </Box>
        ))}
      </Box>
      <Button
        startIcon={<AddIcon />}
        onClick={addRow}
        size="small"
        sx={{ mt: 1 }}
      >
        {t('pages.nutrientCalc.fertilizerRowAdd')}
      </Button>
    </Box>
  );
}

/** "Common name (Scientific name)", falling back to the scientific name. */
function speciesOptionLabel(species: Species): string {
  const common = species.common_names?.[0];
  return common ? `${common} (${species.scientific_name})` : species.scientific_name;
}

const speciesFilter = createFilterOptions<Species>({
  stringify: (species) =>
    [species.scientific_name, ...(species.common_names ?? []), species.genus, species.family_name ?? ''].join(' '),
  matchFrom: 'any',
  trim: true,
});

interface SpeciesSelectProps {
  options: Species[];
  /** Selected species key, or empty string when none. */
  value: string;
  onChange: (key: string) => void;
  label: string;
  helperText?: string;
  loading?: boolean;
}

/** Single-select species picker submitting one `species.key` (clearable), searchable by any name. */
export function SpeciesSelect({
  options,
  value,
  onChange,
  label,
  helperText,
  loading,
}: SpeciesSelectProps) {
  const { t } = useTranslation();
  const sorted = useMemo(
    () => [...options].sort((a, b) => speciesOptionLabel(a).localeCompare(speciesOptionLabel(b))),
    [options],
  );
  const selected = useMemo(
    () => sorted.find((s) => s.key === value) ?? null,
    [value, sorted],
  );

  return (
    <Autocomplete
      options={sorted}
      value={selected}
      onChange={(_, next) => onChange(next?.key ?? '')}
      getOptionLabel={speciesOptionLabel}
      isOptionEqualToValue={(o, v) => o.key === v.key}
      filterOptions={speciesFilter}
      loading={loading}
      noOptionsText={t('pages.nutrientCalc.speciesNoResults')}
      fullWidth
      renderInput={(params) => (
        <TextField {...params} label={label} helperText={helperText} />
      )}
    />
  );
}
