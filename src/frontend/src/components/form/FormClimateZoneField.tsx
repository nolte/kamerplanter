import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';
import HelpTooltip from '@/components/common/HelpTooltip';
import { USDA_HARDINESS_ZONES } from '@/pages/standorte/climateZones';

interface FormClimateZoneFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  helperText?: string;
  disabled?: boolean;
}

/**
 * USDA-hardiness-zone picker for the (optional) site `climate_zone` field. Offers
 * an empty "not specified" entry plus the structured 1a–13b zones. A pre-existing
 * legacy free-text value (e.g. "temperate") is kept as an extra option so editing
 * a site never silently drops it.
 */
export default function FormClimateZoneField<T extends FieldValues>({
  name,
  control,
  label,
  helperText,
  disabled,
}: FormClimateZoneFieldProps<T>) {
  const { t } = useTranslation();
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => {
        const value = (field.value as string) ?? '';
        const legacy = value && !USDA_HARDINESS_ZONES.includes(value) ? value : null;
        return (
          // UI-NFR-011 §2.1/§6.1 — "Hardiness Zones" is a mandatory-glossary
          // taxonomy term (the field itself only says "USDA", not what that
          // means). The icon sits next to the select rather than inside
          // `helperText`, matching the established `HelpTooltip` placement
          // convention (see OverwinteringProfileDialog's hardiness-zone field).
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5 }}>
            <TextField
              {...field}
              value={value}
              select
              label={label}
              disabled={disabled}
              error={!!error}
              helperText={error?.message ?? helperText}
              fullWidth
              margin="dense"
              sx={{ mb: 1.5, flexGrow: 1 }}
              data-testid={`form-field-${name}`}
            >
              <MenuItem value="" data-testid={`form-option-${name}-none`}>
                <em>{t('pages.sites.climateZoneNone')}</em>
              </MenuItem>
              {legacy && (
                <MenuItem value={legacy} data-testid={`form-option-${name}-${legacy}`}>
                  {legacy}
                </MenuItem>
              )}
              {USDA_HARDINESS_ZONES.map((zone) => (
                <MenuItem key={zone} value={zone} data-testid={`form-option-${name}-${zone}`}>
                  {zone}
                </MenuItem>
              ))}
            </TextField>
            <HelpTooltip term="hardiness_zones" iconOnly />
          </Box>
        );
      }}
    />
  );
}
