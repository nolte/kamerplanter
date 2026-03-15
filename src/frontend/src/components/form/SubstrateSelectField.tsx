import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import FilterListIcon from '@mui/icons-material/FilterList';
import RecyclingIcon from '@mui/icons-material/Recycling';
import BlenderIcon from '@mui/icons-material/Blender';
import InputAdornment from '@mui/material/InputAdornment';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';
import type { Substrate, SubstrateType } from '@/api/types';
import { useLocalFavorites } from '@/hooks/useLocalFavorites';

const SUBSTRATE_TYPES: SubstrateType[] = [
  'soil', 'coco', 'clay_pebbles', 'perlite', 'living_soil', 'peat',
  'rockwool_slab', 'rockwool_plug', 'vermiculite', 'orchid_bark',
  'pon_mineral', 'sphagnum', 'hydro_solution', 'none',
];

/** Union type: either a full Substrate entity or a simple type-only fallback. */
interface TypeOnlyOption {
  key: string;
  type: SubstrateType;
  brand: null;
  name_de: string;
  name_en: string;
  is_mix: false;
  reusable: false;
  max_reuse_cycles: 0;
  _typeOnly: true;
}

type SubstrateOption = Substrate | TypeOnlyOption;

function isTypeOnly(opt: SubstrateOption): opt is TypeOnlyOption {
  return '_typeOnly' in opt && opt._typeOnly;
}

interface SubstrateSelectFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  substrates: Substrate[];
  helperText?: string;
  disabled?: boolean;
}

export default function SubstrateSelectField<T extends FieldValues>({
  name,
  control,
  label,
  substrates,
  helperText,
  disabled,
}: SubstrateSelectFieldProps<T>) {
  const { t, i18n } = useTranslation();
  const { isFavorite, toggleFavorite, hasFavorites } = useLocalFavorites('kamerplanter-substrate-favorites');
  const [favFilterActive, setFavFilterActive] = useState(false);
  const isDE = i18n.language?.startsWith('de');

  // If no substrate entities exist, generate fallback options from enum types
  const typeOnlyFallbacks = useMemo<TypeOnlyOption[]>(() =>
    SUBSTRATE_TYPES.map((st) => ({
      key: `_type_${st}`,
      type: st,
      brand: null,
      name_de: '',
      name_en: '',
      is_mix: false as const,
      reusable: false as const,
      max_reuse_cycles: 0,
      _typeOnly: true as const,
    })),
  []);

  const useEntities = substrates.length > 0;
  const allOptions: SubstrateOption[] = useEntities ? substrates : typeOnlyFallbacks;

  const displayName = (s: SubstrateOption) => {
    if (isTypeOnly(s)) return t(`enums.substrateType.${s.type}`);
    return (isDE ? s.name_de : s.name_en) || s.brand || t(`enums.substrateType.${s.type}`);
  };

  const sortedOptions = useMemo(() => {
    const filtered = favFilterActive && hasFavorites
      ? allOptions.filter((s) => isFavorite(s.key))
      : allOptions;
    return [...filtered].sort((a, b) => {
      const aFav = isFavorite(a.key) ? 0 : 1;
      const bFav = isFavorite(b.key) ? 0 : 1;
      if (aFav !== bFav) return aFav - bFav;
      return displayName(a).localeCompare(displayName(b));
    });
  }, [allOptions, favFilterActive, hasFavorites, isFavorite]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => {
        const selected = allOptions.find((s) => s.key === field.value) ?? null;
        return (
          <Autocomplete
            value={selected}
            onChange={(_e, newVal) => {
              field.onChange(newVal?.key ?? '');
            }}
            options={sortedOptions}
            getOptionLabel={(s) => displayName(s)}
            isOptionEqualToValue={(opt, val) => opt.key === val.key}
            disabled={disabled}
            fullWidth
            sx={{ mb: 2 }}
            renderOption={({ key: liKey, ...props }, option) => (
              <Box
                component="li"
                key={liKey}
                {...props}
                sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 1 }}
              >
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleFavorite(option.key);
                  }}
                  sx={{ p: 0.25, color: isFavorite(option.key) ? 'warning.main' : 'action.disabled' }}
                >
                  {isFavorite(option.key) ? <StarIcon fontSize="small" /> : <StarBorderIcon fontSize="small" />}
                </IconButton>
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="body2" noWrap>
                    {displayName(option)}
                    {!isTypeOnly(option) && option.brand && (
                      <Typography component="span" variant="body2" color="text.secondary">
                        {' '}({option.brand})
                      </Typography>
                    )}
                  </Typography>
                  {!isTypeOnly(option) && (
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.25 }}>
                      <Chip
                        label={t(`enums.substrateType.${option.type}`)}
                        size="small"
                        variant="outlined"
                        color="primary"
                      />
                      {option.is_mix && (
                        <Chip
                          icon={<BlenderIcon />}
                          label={t('pages.plantInstances.substrateMix')}
                          size="small"
                          variant="outlined"
                          color="secondary"
                        />
                      )}
                      {option.reusable && (
                        <Chip
                          icon={<RecyclingIcon />}
                          label={
                            option.max_reuse_cycles > 0
                              ? t('pages.plantInstances.substrateReusable', { cycles: option.max_reuse_cycles })
                              : t('pages.plantInstances.substrateReusableUnlimited')
                          }
                          size="small"
                          variant="outlined"
                          color="success"
                        />
                      )}
                    </Box>
                  )}
                </Box>
              </Box>
            )}
            renderInput={(params) => (
              <TextField
                {...params}
                label={label}
                error={!!error}
                helperText={error?.message ?? helperText}
                slotProps={{
                  input: {
                    ...params.InputProps,
                    endAdornment: (
                      <>
                        {hasFavorites && (
                          <InputAdornment position="end">
                            <Tooltip title={t('pages.plantInstances.substrateFavFilter')}>
                              <IconButton
                                size="small"
                                onClick={() => setFavFilterActive((p) => !p)}
                                color={favFilterActive ? 'warning' : 'default'}
                              >
                                <FilterListIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </InputAdornment>
                        )}
                        {params.InputProps.endAdornment}
                      </>
                    ),
                  },
                }}
                data-testid={`form-field-${name}`}
              />
            )}
          />
        );
      }}
    />
  );
}
