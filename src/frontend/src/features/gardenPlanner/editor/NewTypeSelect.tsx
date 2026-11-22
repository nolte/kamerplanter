/**
 * The type of what the next draw gesture creates (REQ-053 GP-UX-046, WP 2.6): the bed type for the
 * bed tool, the object type for the object tool, the area type for the area tool (GP-UX-071, #2913). It replaces the
 * placeholders of WP 2.4.
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import type { LocationType } from '@/api/types';
import type { GardenObjectType } from '../model/types';
import type { RendererLabels } from '../renderer';
import { OBJECT_TYPES } from './tools/objectTypes';

interface NewTypeSelectProps {
  target: 'area' | 'bed' | 'garden_object';
  labels: RendererLabels;
  bedTypes: LocationType[];
  bedTypeKey: string;
  onBedTypeKey: (key: string) => void;
  objectType: GardenObjectType;
  onObjectType: (type: GardenObjectType) => void;
  /** The offered area types (`useAreaTypes`) and the chosen one; only read for the area tool. */
  areaTypes?: LocationType[];
  areaTypeKey?: string;
  onAreaTypeKey?: (key: string) => void;
}

const sx = { minWidth: 200, '& .MuiInputBase-root': { minHeight: 44 } } as const;

/** A location type's name in the UI language: the English name where there is one (the seed carries both). */
export function locationTypeName(type: Pick<LocationType, 'name' | 'name_en'>, language: string): string {
  return language.startsWith('en') && type.name_en ? type.name_en : type.name;
}

export function NewTypeSelect(props: NewTypeSelectProps) {
  const { t, i18n } = useTranslation();
  if (props.target === 'area') {
    const types = props.areaTypes ?? [];
    // Without a loaded list there is nothing to choose: the tool keeps the fallback type.
    if (types.length === 0) return null;
    return (
      // The parent rule stands beside the choice, not under it: the row keeps the height of the bed's type choice, so
      // the canvas below keeps its room (GP-UX-067); on a narrow screen it wraps below.
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
        <TextField
          select
          size="small"
          label={t('pages.gardenPlan.editor.area.type')}
          value={types.some((type) => type.key === props.areaTypeKey) ? props.areaTypeKey : ''}
          onChange={(event) => props.onAreaTypeKey?.(event.target.value)}
          slotProps={{ htmlInput: { 'data-testid': 'garden-plan-new-area-type' } }}
          sx={sx}
        >
          {types.map((type) => (
            <MenuItem key={type.key} value={type.key} sx={{ minHeight: 48 }}>
              {locationTypeName(type, i18n.language)}
            </MenuItem>
          ))}
        </TextField>
        {/* What the area holds and what it does not, before the first click (GP-UX-071). */}
        <Typography
          variant="caption"
          color="text.secondary"
          data-testid="garden-plan-new-area-type-rule"
          sx={{ flex: '1 1 240px', maxWidth: 640 }}
        >
          {t('pages.gardenPlan.editor.area.parentRule')}
        </Typography>
      </Box>
    );
  }
  if (props.target === 'bed') {
    // Without a loaded list there is nothing to choose: the tool keeps the plan's usual bed type.
    if (props.bedTypes.length === 0) return null;
    return (
      <TextField
        select
        size="small"
        label={t('pages.gardenPlan.editor.addWithDimensions.bedType')}
        value={props.bedTypes.some((type) => type.key === props.bedTypeKey) ? props.bedTypeKey : ''}
        onChange={(event) => props.onBedTypeKey(event.target.value)}
        slotProps={{ htmlInput: { 'data-testid': 'garden-plan-new-bed-type' } }}
        sx={sx}
      >
        {props.bedTypes.map((type) => (
          <MenuItem key={type.key} value={type.key} sx={{ minHeight: 48 }}>
            {type.name}
          </MenuItem>
        ))}
      </TextField>
    );
  }
  return (
    <TextField
      select
      size="small"
      label={t('pages.gardenPlan.editor.addWithDimensions.objectType')}
      value={props.objectType}
      onChange={(event) => props.onObjectType(event.target.value as GardenObjectType)}
      slotProps={{ htmlInput: { 'data-testid': 'garden-plan-new-object-type' } }}
      sx={sx}
    >
      {OBJECT_TYPES.map((type) => (
        <MenuItem key={type} value={type} sx={{ minHeight: 48 }}>
          {props.labels.objectType(type)}
        </MenuItem>
      ))}
    </TextField>
  );
}
