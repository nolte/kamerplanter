/**
 * The type of what the next draw gesture creates (REQ-053 GP-UX-046, WP 2.6): the bed type for the
 * bed tool, the object type for the object tool. It replaces the placeholders of WP 2.4.
 */
import { useTranslation } from 'react-i18next';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import type { LocationType } from '@/api/types';
import type { GardenObjectType } from '../model/types';
import type { RendererLabels } from '../renderer';
import { OBJECT_TYPES } from './tools/objectTypes';

interface NewTypeSelectProps {
  target: 'bed' | 'garden_object';
  labels: RendererLabels;
  bedTypes: LocationType[];
  bedTypeKey: string;
  onBedTypeKey: (key: string) => void;
  objectType: GardenObjectType;
  onObjectType: (type: GardenObjectType) => void;
}

const sx = { minWidth: 200, '& .MuiInputBase-root': { minHeight: 44 } } as const;

export function NewTypeSelect(props: NewTypeSelectProps) {
  const { t } = useTranslation();
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
