/**
 * A group of chips on native inputs (radios for one choice, checkboxes for several), the look of the sun-window
 * chips (REQ-053 GP-UX-057): the arrow keys, the announcement and the checked state come from the browser, the
 * target is `touchTarget` px high (48 by default, 64 in field mode, GP-UX-023). Reports only the clicked option.
 */
import { useId } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

export interface ChipChoiceProps<T extends string> {
  /** Visible group title; also the accessible name of the group. */
  title: string;
  hint?: string;
  options: readonly { value: T; label: string }[];
  /** The checked options: one entry for `single`, any number for `multiple`. */
  value: readonly T[];
  mode: 'single' | 'multiple';
  onToggle: (option: T) => void;
  disabled?: boolean;
  touchTarget?: number;
  testId: string;
}

export default function ChipChoice<T extends string>({
  title,
  hint,
  options,
  value,
  mode,
  onToggle,
  disabled = false,
  touchTarget = 48,
  testId,
}: ChipChoiceProps<T>) {
  const name = useId();
  const titleId = `${name}-title`;
  const hintId = `${name}-hint`;
  return (
    <Box>
      <Typography id={titleId} variant="subtitle2" component="h4" sx={{ mb: 0.5 }}>
        {title}
      </Typography>
      {hint && (
        <Typography id={hintId} variant="caption" color="text.secondary" component="p" sx={{ mb: 1 }}>
          {hint}
        </Typography>
      )}
      <Box
        role={mode === 'single' ? 'radiogroup' : 'group'}
        aria-labelledby={titleId}
        aria-describedby={hint ? hintId : undefined}
        data-testid={testId}
        sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}
      >
        {options.map((option) => {
          const checked = value.includes(option.value);
          const labelId = `${name}-${option.value}`;
          return (
            <Box
              key={option.value}
              component="label"
              data-testid={`${testId}-${option.value}`}
              sx={(theme) => ({
                position: 'relative',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: touchTarget,
                minWidth: touchTarget,
                px: 2,
                borderRadius: touchTarget / 2,
                border: '2px solid',
                borderColor: checked ? 'primary.main' : 'divider',
                bgcolor: checked ? 'action.selected' : 'background.paper',
                cursor: disabled ? 'default' : 'pointer',
                opacity: disabled ? 0.6 : 1,
                '&:hover': disabled ? undefined : { bgcolor: 'action.hover' },
                '&:has(:focus-visible)': { outline: `3px solid ${theme.palette.primary.main}`, outlineOffset: 2 },
              })}
            >
              <input
                type={mode === 'single' ? 'radio' : 'checkbox'}
                name={name}
                value={option.value}
                checked={checked}
                disabled={disabled}
                onChange={() => {
                  if (mode === 'multiple' || !checked) onToggle(option.value);
                }}
                aria-labelledby={labelId}
                data-testid={`${testId}-${option.value}-input`}
                style={{
                  position: 'absolute',
                  inset: 0,
                  width: '100%',
                  height: '100%',
                  margin: 0,
                  opacity: 0,
                  cursor: 'inherit',
                }}
              />
              <Typography id={labelId} variant="body2" component="span" sx={{ fontWeight: checked ? 700 : 500 }}>
                {option.label}
              </Typography>
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}
