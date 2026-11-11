/**
 * The field of a door (REQ-053 §9.8, GP-FR-180): its swing - what `DoorProps` carries. §9.8 names `swing` without a
 * value set, so the backend holds it as bounded free text (at most 50 characters); the field mirrors that and an
 * emptied field clears it (`null`).
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import TextField from '@mui/material/TextField';
import type { DoorProps } from '../../model/types';
import { MAX_SWING_LENGTH } from './limits';
import { OBJECT_PROPS_PREFIX, TARGET_PX, type ObjectFieldsProps } from './shared';
import { useCommitProps } from './useCommitProps';

const PREFIX = `${OBJECT_PROPS_PREFIX}.door`;

export function DoorFields(fields: ObjectFieldsProps<DoorProps>) {
  const { t } = useTranslation();
  const commit = useCommitProps(fields);
  const { props, disabled } = fields;
  const stored = props.swing ?? '';
  const [draft, setDraft] = useState(stored);
  const [seen, setSeen] = useState(stored);
  if (stored !== seen) {
    setSeen(stored);
    setDraft(stored);
  }
  const tooLong = draft.trim().length > MAX_SWING_LENGTH;
  const save = () => {
    const trimmed = draft.trim();
    if (tooLong || trimmed === stored) return;
    commit({ swing: trimmed === '' ? null : trimmed });
  };
  return (
    <TextField
      size="small"
      label={t(`${PREFIX}.swing`)}
      value={draft}
      disabled={disabled}
      error={tooLong}
      helperText={
        tooLong
          ? t(`${PREFIX}.swingTooLong`, { max: MAX_SWING_LENGTH })
          : t(`${PREFIX}.swingHelp`, { count: draft.trim().length, max: MAX_SWING_LENGTH })
      }
      onChange={(event) => setDraft(event.target.value)}
      onBlur={save}
      onKeyDown={(event) => {
        if (event.key === 'Enter') {
          event.preventDefault();
          save();
        } else if (event.key === 'Escape') {
          event.stopPropagation();
          setDraft(stored);
        }
      }}
      slotProps={{ htmlInput: { 'data-testid': 'garden-plan-panel-door-swing' } }}
      sx={{ '& .MuiInputBase-root': { minHeight: TARGET_PX } }}
    />
  );
}
