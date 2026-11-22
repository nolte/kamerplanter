/**
 * The parcel label of a bed in the properties panel (REQ-053 GP-FR-176, #2759): a stable identifier such as an
 * allotment number, the parcel list's identifier where set. Commits on blur or Enter as ONE `update_fields` (one
 * undo step, GP-FR-155); a blank field clears the label. The rules are checked before anything is committed.
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import TextField from '@mui/material/TextField';
import {
  PARCEL_LABEL_MAX_CHARS,
  parcelLabelProblem,
  parcelLabelValue,
  type ParcelLabelProblem,
} from '../model/parcelLabel';

const PREFIX = 'pages.gardenPlan.editor.panel';

const PROBLEM_KEY: Record<ParcelLabelProblem, string> = {
  too_long: `${PREFIX}.parcelLabelTooLong`,
  control: `${PREFIX}.parcelLabelControl`,
};

export interface ParcelLabelFieldProps {
  /** The stored label; `null`/absent = none. */
  value: string | null | undefined;
  disabled: boolean;
  /** Called with the new label (`null` clears it) only when it changed and passes the rules. */
  onCommit: (next: string | null) => void;
}

export function ParcelLabelField({ value, disabled, onCommit }: ParcelLabelFieldProps) {
  const { t } = useTranslation();
  const stored = value ?? '';
  const [draft, setDraft] = useState(stored);
  const [seen, setSeen] = useState(stored);
  const [problem, setProblem] = useState<ParcelLabelProblem | null>(null);
  // An undo, a reload or another selection changes the stored value: the field follows it.
  if (stored !== seen) {
    setSeen(stored);
    setDraft(stored);
    setProblem(null);
  }

  const commit = () => {
    const found = parcelLabelProblem(draft);
    setProblem(found);
    if (found !== null) return;
    const next = parcelLabelValue(draft);
    if (next === (value ?? null)) {
      setDraft(stored);
      return;
    }
    onCommit(next);
  };

  return (
    <TextField
      size="small"
      label={t(`${PREFIX}.parcelLabel`)}
      value={draft}
      disabled={disabled}
      error={problem !== null}
      helperText={
        problem !== null
          ? t(PROBLEM_KEY[problem], { max: PARCEL_LABEL_MAX_CHARS })
          : t(`${PREFIX}.parcelLabelHelp`)
      }
      onChange={(event) => setDraft(event.target.value)}
      onBlur={commit}
      onKeyDown={(event) => {
        if (event.key === 'Enter') {
          event.preventDefault();
          commit();
        }
      }}
      slotProps={{ htmlInput: { 'data-testid': 'garden-plan-panel-parcel-label' } }}
      sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
    />
  );
}
