/**
 * A numeric panel field (REQ-053 GP-FR-155, GP-UX-052/054): the typed text is a draft; blur or
 * Enter turns it into ONE change (one undo step), Escape puts the old value back. The decimal
 * keypad opens on touch (`inputmode="decimal"`), both separators are read. A draft the live
 * validation refuses is shown red and is not committed.
 */
import { useState } from 'react';
import InputAdornment from '@mui/material/InputAdornment';
import TextField from '@mui/material/TextField';
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
}

const format = (value: number): string => String(value);

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
}: NumberFieldProps) {
  const [text, setText] = useState(format(value));
  const [seen, setSeen] = useState(value);
  // The model changed under the field (undo, a drag): show the new value (derived state pattern).
  if (value !== seen) {
    setSeen(value);
    setText(format(value));
  }
  const parsed = parseDecimal(text);
  const range =
    parsed !== null && ((min !== undefined && parsed < min) || (max !== undefined && parsed > max));
  const code = parsed === null || range ? 'geometry.invalid' : (validate?.(parsed) ?? null);
  const dirty = parsed === null || parsed !== value;

  const revert = () => {
    setText(format(value));
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
