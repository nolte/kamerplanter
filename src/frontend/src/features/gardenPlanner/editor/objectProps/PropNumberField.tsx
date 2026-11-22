/**
 * A numeric object property in the properties panel (REQ-053 GP-FR-180, GP-UX-052/053): the typed text is a draft;
 * blur or Enter commits it as ONE change, Escape puts the stored value back. Both decimal separators are read, the
 * decimal keypad opens on touch. The stored value is written with the separator of the UI language (UI-NFR-007 R-014). A draft outside the bounds of the backend model is shown red with a text that says
 * what to enter, and is not committed. An optional field may be emptied (`null`); a required one may not.
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import InputAdornment from '@mui/material/InputAdornment';
import TextField from '@mui/material/TextField';
import { formatDecimal } from '../../model/units';
import { parseDecimal } from '../tools/panelFields';

interface PropNumberFieldProps {
  label: string;
  value: number | null | undefined;
  /** The unit after the value ("m", "µmol/m²/s"). */
  unit: string;
  /** Inclusive bounds of the backend model; `undefined` = unbounded on that side. */
  min?: number;
  max?: number;
  /** A required field refuses the empty draft (the model has no `None` there). */
  required?: boolean;
  disabled?: boolean;
  /** The help under the field while the draft is valid. */
  helperText: string;
  /** The text under the field while the draft is refused: what to enter instead. */
  invalidText: string;
  testId: string;
  /** Called once with the new value on blur/Enter; never with an invalid or unchanged one. */
  onCommit: (value: number | null) => void;
}

export function PropNumberField({
  label,
  value,
  unit,
  min,
  max,
  required = false,
  disabled,
  helperText,
  invalidText,
  testId,
  onCommit,
}: PropNumberFieldProps) {
  const { i18n } = useTranslation();
  const language = i18n.language;
  const stored = value ?? null;
  const [text, setText] = useState(() => formatDecimal(stored, language));
  const [seen, setSeen] = useState({ stored, language });
  // The model changed under the field (undo, another edit) or the language did: show the stored value (derived state).
  if (stored !== seen.stored || language !== seen.language) {
    setSeen({ stored, language });
    setText(formatDecimal(stored, language));
  }
  const empty = text.trim() === '';
  const parsed = empty ? null : parseDecimal(text);
  const invalid = empty
    ? required
    : parsed === null || (min !== undefined && parsed < min) || (max !== undefined && parsed > max);

  const commit = () => {
    if (invalid || parsed === stored) return;
    onCommit(parsed);
  };

  return (
    <TextField
      size="small"
      label={label}
      value={text}
      disabled={disabled}
      required={required}
      error={invalid}
      helperText={invalid ? invalidText : helperText}
      onChange={(event) => setText(event.target.value)}
      onBlur={commit}
      onKeyDown={(event) => {
        if (event.key === 'Enter') {
          event.preventDefault();
          commit();
        } else if (event.key === 'Escape') {
          event.stopPropagation();
          setText(formatDecimal(stored, language));
        }
      }}
      slotProps={{
        htmlInput: { inputMode: 'decimal', 'data-testid': testId },
        input: { endAdornment: <InputAdornment position="end">{unit}</InputAdornment> },
      }}
      sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
    />
  );
}
