/**
 * The fields of a lamp (REQ-053 §9.8, GP-FR-180): kind, mounting height and a reference PPFD - what `LampProps`
 * carries, as preparation for a light distribution; nothing is calculated from them. Kind and height are required in
 * the model; the reference PPFD is optional and has no default: a value the grower does not know stays empty
 * (`null`) rather than an invented one (G-W10 d).
 */
import { useTranslation } from 'react-i18next';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import type { LampKind, LampProps } from '../../model/types';
import { MAX_HEIGHT_M, MIN_HEIGHT_M, MIN_PPFD } from './limits';
import { PropNumberField } from './PropNumberField';
import { formatBound, OBJECT_PROPS_PREFIX, TARGET_PX, type ObjectFieldsProps } from './shared';
import { useCommitProps } from './useCommitProps';

const PREFIX = `${OBJECT_PROPS_PREFIX}.lamp`;

/** `LampKind` of the backend, in its order. */
export const LAMP_KINDS: readonly LampKind[] = ['grow_light', 'ceiling', 'floor'];

/** The PPFD unit; the same in every language. */
const PPFD_UNIT = 'µmol/m²/s';

export function LampFields(fields: ObjectFieldsProps<LampProps>) {
  const { t, i18n } = useTranslation();
  const commit = useCommitProps(fields);
  const { props, disabled } = fields;
  return (
    <>
      <TextField
        select
        size="small"
        label={t(`${PREFIX}.kind`)}
        value={props.kind}
        disabled={disabled}
        helperText={t(`${PREFIX}.kindHelp`)}
        onChange={(event) => commit({ kind: event.target.value as LampKind })}
        slotProps={{ htmlInput: { 'data-testid': 'garden-plan-panel-lamp-kind' } }}
        sx={{ '& .MuiInputBase-root': { minHeight: TARGET_PX } }}
      >
        {LAMP_KINDS.map((kind) => (
          <MenuItem key={kind} value={kind} sx={{ minHeight: TARGET_PX }}>
            {t(`enums.lampKind.${kind}`)}
          </MenuItem>
        ))}
      </TextField>
      <PropNumberField
        label={t(`${PREFIX}.height`)}
        value={props.height_m}
        unit="m"
        min={MIN_HEIGHT_M}
        max={MAX_HEIGHT_M}
        required
        disabled={disabled}
        helperText={t(`${PREFIX}.heightHelp`)}
        invalidText={t(`${OBJECT_PROPS_PREFIX}.heightRequiredInvalid`, {
          min: formatBound(MIN_HEIGHT_M, i18n.language),
          max: formatBound(MAX_HEIGHT_M, i18n.language),
        })}
        testId="garden-plan-panel-lamp-height"
        onCommit={(value) => {
          if (value !== null) commit({ height_m: value });
        }}
      />
      <PropNumberField
        label={t(`${PREFIX}.ppfd`)}
        value={props.ppfd_ref}
        unit={PPFD_UNIT}
        min={MIN_PPFD}
        disabled={disabled}
        helperText={t(`${PREFIX}.${props.ppfd_ref == null ? 'ppfdNone' : 'ppfdHelp'}`)}
        invalidText={t(`${PREFIX}.ppfdInvalid`)}
        testId="garden-plan-panel-lamp-ppfd"
        onCommit={(value) => commit({ ppfd_ref: value })}
      />
    </>
  );
}
