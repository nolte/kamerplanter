import { useCallback, useMemo, type ReactNode } from 'react';
import Box from '@mui/material/Box';
import Slider from '@mui/material/Slider';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import HelpTooltip from '@/components/common/HelpTooltip';

export interface SliderMark {
  value: number;
  label?: string;
}

interface SliderNumberFieldProps {
  /** Accessible label — used both on the numeric field and the slider. */
  label: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step?: number;
  /** Unit rendered as a trailing `InputAdornment` (e.g. `°C`, `%`, `h`). */
  unit?: string;
  marks?: SliderMark[];
  helperText?: ReactNode;
  /** Optional glossary term rendered as a `HelpTooltip` next to the field. */
  glossaryTerm?: string;
  /** Validation error text; also flags the numeric field. */
  error?: string;
  disabled?: boolean;
  testId?: string;
}

/**
 * A bounded numeric input paired with a slider for quick adjustment. Both
 * controls share one value so the accessible, labelled `TextField` stays the
 * primary (keyboard- and test-friendly) affordance while the slider offers a
 * mobile-friendly coarse adjustment. Values are clamped to `[min, max]`.
 *
 * Mobile-first: the slider thumb and the input satisfy the ≥48 px touch target
 * (UI-NFR-001); the numeric field carries the unit as an `InputAdornment` rather
 * than only in label text.
 */
export default function SliderNumberField({
  label,
  value,
  onChange,
  min,
  max,
  step = 1,
  unit,
  marks,
  helperText,
  glossaryTerm,
  error,
  disabled,
  testId,
}: SliderNumberFieldProps) {
  const clamp = useCallback(
    (raw: number): number => {
      if (Number.isNaN(raw)) return min;
      return Math.min(max, Math.max(min, raw));
    },
    [min, max],
  );

  const handleSlider = useCallback(
    (_event: Event, next: number | number[]) => {
      onChange(clamp(Array.isArray(next) ? next[0] : next));
    },
    [clamp, onChange],
  );

  const inputProps = useMemo(
    () => ({
      htmlInput: { min, max, step },
      input: unit
        ? { endAdornment: <InputAdornment position="end">{unit}</InputAdornment> }
        : undefined,
    }),
    [min, max, step, unit],
  );

  return (
    <Box sx={{ mb: 2 }}>
      <TextField
        type="number"
        label={label}
        value={value}
        onChange={(e) => onChange(clamp(Number(e.target.value)))}
        fullWidth
        error={Boolean(error)}
        helperText={error ?? helperText}
        disabled={disabled}
        slotProps={inputProps}
        data-testid={testId}
      />
      <Box sx={{ px: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
        <Slider
          value={value}
          onChange={handleSlider}
          min={min}
          max={max}
          step={step}
          marks={marks}
          disabled={disabled}
          valueLabelDisplay="auto"
          aria-label={label}
          sx={{ flexGrow: 1 }}
        />
        {glossaryTerm && <HelpTooltip term={glossaryTerm} iconOnly />}
      </Box>
    </Box>
  );
}
