/**
 * The fields of a window (REQ-053 §9.8, GP-FR-180): sill height and glazing - what `WindowProps` carries. The
 * orientation is derived from the wall and the plan's north angle and never stored (§9.8, GP-FR-181, WP 10.7:
 * `model/windowOrientation.ts`); it is shown read-only ("Südost, 135°"), and as "not available" while none can be
 * derived (a window that is no line). When the plan has no outline that tells the outside, the caption says that the
 * outside was taken from the drawing direction.
 */
import { useTranslation } from 'react-i18next';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import type { WindowGlazing, WindowProps } from '../../model/types';
import { MAX_HEIGHT_M, MIN_SILL_HEIGHT_M } from './limits';
import { PropNumberField } from './PropNumberField';
import { formatBound, OBJECT_PROPS_PREFIX, TARGET_PX, type ObjectFieldsProps } from './shared';
import { useCommitProps } from './useCommitProps';

const PREFIX = `${OBJECT_PROPS_PREFIX}.window`;

/** `WindowGlazing` of the backend, in its order. */
export const WINDOW_GLAZINGS: readonly WindowGlazing[] = ['single', 'double', 'unknown'];

/** The select's value for "not given" (`glazing: null`). */
const NOT_GIVEN = '';

interface WindowFieldsProps extends ObjectFieldsProps<WindowProps> {
  /** The derived orientation as a text ("Südwest"), or `null` while none is derived. */
  orientation?: string | null;
  /** The outside was taken from the drawing direction (no outline to tell it). */
  orientationByConvention?: boolean;
}

export function WindowFields({ orientation = null, orientationByConvention = false, ...fields }: WindowFieldsProps) {
  const { t, i18n } = useTranslation();
  const commit = useCommitProps(fields);
  const { props, disabled } = fields;
  return (
    <>
      <PropNumberField
        label={t(`${PREFIX}.sillHeight`)}
        value={props.sill_height_m}
        unit="m"
        min={MIN_SILL_HEIGHT_M}
        max={MAX_HEIGHT_M}
        disabled={disabled}
        helperText={t(`${PREFIX}.sillHeightHelp`)}
        invalidText={t(`${PREFIX}.sillHeightInvalid`, { max: formatBound(MAX_HEIGHT_M, i18n.language) })}
        testId="garden-plan-panel-window-sill-height"
        onCommit={(value) => commit({ sill_height_m: value })}
      />
      <TextField
        select
        size="small"
        label={t(`${PREFIX}.glazing`)}
        value={props.glazing ?? NOT_GIVEN}
        disabled={disabled}
        helperText={t(`${PREFIX}.glazingHelp`)}
        onChange={(event) =>
          commit({ glazing: event.target.value === NOT_GIVEN ? null : (event.target.value as WindowGlazing) })
        }
        slotProps={{
          htmlInput: { 'data-testid': 'garden-plan-panel-window-glazing' },
          inputLabel: { shrink: true },
          select: { displayEmpty: true },
        }}
        sx={{ '& .MuiInputBase-root': { minHeight: TARGET_PX } }}
      >
        <MenuItem value={NOT_GIVEN} sx={{ minHeight: TARGET_PX }}>
          {t(`${OBJECT_PROPS_PREFIX}.notGiven`)}
        </MenuItem>
        {WINDOW_GLAZINGS.map((glazing) => (
          <MenuItem key={glazing} value={glazing} sx={{ minHeight: TARGET_PX }}>
            {t(`enums.windowGlazing.${glazing}`)}
          </MenuItem>
        ))}
      </TextField>
      <div data-testid="garden-plan-panel-window-orientation" data-available={orientation !== null}>
        <Typography variant="body2">
          {t(`${PREFIX}.orientation`, { value: orientation ?? t(`${PREFIX}.orientationNone`) })}
        </Typography>
        <Typography variant="caption" color="text.secondary" component="p">
          {t(`${PREFIX}.orientationHelp`)}
        </Typography>
        {orientation !== null && orientationByConvention && (
          <Typography
            variant="caption"
            color="text.secondary"
            component="p"
            data-testid="garden-plan-panel-window-orientation-convention"
          >
            {t(`${PREFIX}.orientationConvention`)}
          </Typography>
        )}
      </div>
    </>
  );
}
