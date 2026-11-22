/**
 * A numeric panel field (REQ-053 GP-FR-155, GP-UX-052/054): the typed text is a draft; blur or
 * Enter turns it into ONE change (one undo step), Escape puts the old value back. The decimal
 * keypad opens on touch (`inputmode="decimal"`), both separators are read. A draft the live
 * validation refuses is shown red and is not committed. The value is written with the separator of the UI language
 * (UI-NFR-007 R-014).
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import InputAdornment from '@mui/material/InputAdornment';
import TextField from '@mui/material/TextField';
import { formatDecimal } from '../model/units';
import { parseDecimal } from './tools/panelFields';

interface NumberFieldProps {
  label: string;
  value: number;
  unit?: string;
  min?: number;
  max?: number;
  disabled?: boolean;
  /** An error code for the typed number, or `null`; shown red while typing (GP-UX-053). */
  validate?: (value: number) => string | null;
  /** Called once with the new value on blur/Enter; never with an invalid or unchanged one. */
  onCommit: (value: number, previous: number) => void;
  /** Reports the live error code (or `null`) so the panel can explain it. */
  onError?: (code: string | null) => void;
  testId?: string;
  /** Short text under the field while its draft is invalid (the panel explains the cause). */
  errorText?: string;
}

export function NumberField({
  label,
  value,
  unit,
  min,
  max,
  disabled,
  validate,
  onCommit,
  onError,
  testId,
  errorText,
}: NumberFieldProps) {
  const { i18n } = useTranslation();
  const language = i18n.language;
  const [text, setText] = useState(() => formatDecimal(value, language));
  const [seen, setSeen] = useState({ value, language });
  // The model changed under the field (undo, a drag) or the language did: show the new value (derived state pattern).
  if (value !== seen.value || language !== seen.language) {
    setSeen({ value, language });
    setText(formatDecimal(value, language));
  }
  const parsed = parseDecimal(text);
  const range =
    parsed !== null && ((min !== undefined && parsed < min) || (max !== undefined && parsed > max));
  const code = parsed === null || range ? 'geometry.invalid' : (validate?.(parsed) ?? null);
  const dirty = parsed === null || parsed !== value;

  const revert = () => {
    setText(formatDecimal(value, language));
    onError?.(null);
  };
  const commit = () => {
    if (!dirty) return;
    if (code !== null || parsed === null) {
      onError?.(code);
      return;
    }
    onError?.(null);
    onCommit(parsed, value);
  };

  return (
    <TextField
      size="small"
      label={label}
      value={text}
      disabled={disabled}
      error={dirty && code !== null}
      helperText={dirty && code !== null ? errorText : undefined}
      onChange={(event) => {
        setText(event.target.value);
        const next = parseDecimal(event.target.value);
        const outside =
          next !== null && ((min !== undefined && next < min) || (max !== undefined && next > max));
        onError?.(next === null || outside ? 'geometry.invalid' : (validate?.(next) ?? null));
      }}
      onBlur={commit}
      onKeyDown={(event) => {
        if (event.key === 'Enter') {
          event.preventDefault();
          commit();
        } else if (event.key === 'Escape' && dirty) {
          event.stopPropagation();
          revert();
        }
      }}
      slotProps={{
        htmlInput: { inputMode: 'decimal', 'data-testid': testId },
        input: {
          endAdornment: unit ? <InputAdornment position="end">{unit}</InputAdornment> : undefined,
        },
      }}
      sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
    />
  );
}
