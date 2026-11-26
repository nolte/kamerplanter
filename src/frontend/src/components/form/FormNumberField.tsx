import { lazy, Suspense, useContext, useRef, type ComponentProps, type ComponentType, type ReactNode } from 'react';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';
import FieldHelp from './FieldHelp';
import { KioskContext } from '@/kiosk/KioskProvider';
import { loadKioskQuickSelect } from '@/kiosk/kioskChunks';
import type { QuickSelectPreset } from '@/kiosk/quickSelectPresets';
// Type only: the tiles themselves stay in their lazy chunk.
import type QuickSelectTiles from '@/components/kiosk/KioskQuickSelect';

// UI-NFR-019 R-024 — only a kiosk session shows quick-select tiles; their own chunk.
// Offline before the shell's preload: the tiles stay away and the number field still works.
const KioskQuickSelect = lazy<ComponentType<ComponentProps<typeof QuickSelectTiles>>>(() =>
  loadKioskQuickSelect().catch(() => ({ default: () => null })),
);

interface FormNumberFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  min?: number;
  max?: number;
  step?: number | 'any';
  required?: boolean;
  disabled?: boolean;
  helperText?: string;
  /** Short unit label rendered as end adornment (e.g. "L", "mS/cm", "°C"). */
  suffix?: string;
  /** Custom end adornment node. Takes precedence over suffix when both are provided. */
  endAdornment?: ReactNode;
  autoFocus?: boolean;
  inputMode?: 'numeric' | 'decimal';
  /** Shown while the field is empty — use for what an empty value means, never as a label. */
  placeholder?: string;
  /**
   * Glossary key of the domain term this field asks for (e.g. "ec", "vpd") —
   * renders the shared `HelpTooltip` next to the field (#3020, UI-NFR-011 §6.1).
   */
  helpTerm?: string;
  /**
   * UI-NFR-019 R-024 — predefined values offered as large tiles while kiosk mode is on. The
   * number field itself stays as the "Manuell" entry (R-026); outside kiosk mode nothing changes.
   */
  quickSelect?: QuickSelectPreset;
}

export default function FormNumberField<T extends FieldValues>({
  name,
  control,
  label,
  min,
  max,
  step,
  required,
  disabled,
  helperText,
  suffix,
  endAdornment,
  autoFocus,
  inputMode,
  placeholder,
  helpTerm,
  quickSelect,
}: FormNumberFieldProps<T>) {
  const isKiosk = useContext(KioskContext)?.isKiosk ?? false;
  const inputRef = useRef<HTMLInputElement>(null);
  const adornment =
    endAdornment ?? (suffix ? <InputAdornment position="end">{suffix}</InputAdornment> : undefined);

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => {
        const input = (
          <FieldHelp helpTerm={helpTerm}>
            <TextField
              {...field}
              value={field.value ?? ''}
              onChange={(e) => {
                const val = e.target.value;
                // Clearing the field emits `null`, not `''` (#778 B2). A numeric
                // field has no meaningful empty *string* value — the domain value
                // of "cleared" is absent, and `null` is what the API takes.
                //
                // Emitting `''` made `z.number().nullable()` reject a field the
                // user had emptied, so a filled duration could not be cleared
                // again: zod saw a string where it wanted a number or null. 112
                // schema lines across 38 files carry that plain nullable shape,
                // and only a handful had worked around it with
                // `z.union([z.number(), z.literal('')])`. Fixing the emitted value
                // once here is what makes the plain shape correct everywhere,
                // instead of teaching every schema about a quirk of this input.
                field.onChange(val === '' ? null : Number(val));
              }}
              type="number"
              label={label}
              required={required}
              // `?? field.disabled` honours `useForm({ disabled })` / `<Controller disabled>`;
              // a bare `disabled={disabled}` overwrites RHF's value with `undefined` (#1402 C).
              disabled={disabled ?? field.disabled}
              error={!!error}
              helperText={error?.message ?? helperText}
              fullWidth
              autoFocus={autoFocus}
              margin="dense"
              sx={{ mb: 1.5 }}
              slotProps={{
                htmlInput: {
                  // Only pass min/max when explicitly set — omitting them prevents
                  // MUI from emitting aria-valuemin/aria-valuemax="0" as a fallback,
                  // which would mislead screen readers into reporting a wrong range.
                  ...(min !== undefined ? { min } : {}),
                  ...(max !== undefined ? { max } : {}),
                  step: step ?? 'any',
                  inputMode: inputMode ?? 'decimal',
                  ...(placeholder ? { placeholder } : {}),
                },
                ...(adornment ? { input: { endAdornment: adornment } } : {}),
              }}
              inputRef={inputRef}
              data-testid={`form-field-${name}`}
            />
          </FieldHelp>
        );
        // Without tiles the field renders exactly as before (the 700+ call sites keep their DOM).
        if (!isKiosk || !quickSelect) return input;
        // One grid item: the field and its kiosk tiles stay together in a two-column form, from the
        // first render on — not only once the tiles' chunk has arrived.
        return (
          <Box sx={{ minWidth: 0 }}>
            {input}
            <Suspense fallback={null}>
              <KioskQuickSelect
                preset={quickSelect}
                value={field.value as number | null | undefined}
                fieldLabel={label}
                onSelect={(v) => field.onChange(v)}
                onManual={() => inputRef.current?.focus()}
                testIdPrefix={`form-field-${name}`}
              />
            </Suspense>
          </Box>
        );
      }}
    />
  );
}
