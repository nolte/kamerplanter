import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

/**
 * Keeps an open option list from covering the field it belongs to (#833,
 * UI-NFR-001 R-011).
 *
 * Every claim below was measured on a real 393px viewport
 * (`TestSelectMenuGeometry`, TC-006-020), because reasoning about it was wrong
 * twice.
 *
 * **Not the anchor.** The issue proposed `anchorOrigin` / `transformOrigin` as the
 * fix. Setting them to bottom/top changes the menu top by *zero pixels* — MUI 9's
 * `SelectInput` already defaults to exactly that. They are still stated here, but
 * as a guard against a future default change, not as the fix. (Flipping them to
 * top/bottom moved the menu from 1650 to 1395, which is how we know the probe
 * responds at all rather than measuring something inert.)
 *
 * **It is the height.** `Popover` shifts a paper *up* until it fits the viewport,
 * and that shift is what walks over the trigger. Same field, same page:
 *
 *   45vh, 320px, 240px -> menu top 1650, trigger bottom 1691 (41px overlap)
 *   200px, 160px, 120px -> clears the trigger
 *
 * So the space below that field was between 200 and 240px.
 *
 * So `200` is the cap: the largest measured value that clears the trigger, chosen
 * over the roomier 45vh precisely because 45vh does not.
 *
 * **What was tried and does not work**, recorded so it is not retried: lifting the
 * trigger on `onOpen` (`scrollIntoView({block: 'start'})`) so there would be room
 * below. The probe reported an unchanged 41px overlap — `Popover` computes the
 * paper's position in the same tick, before the scroll's layout lands, so the
 * anchor it measures is the pre-scroll one. Two variants were measured (event
 * `currentTarget`, then a testid lookup, since `currentTarget` is already detached
 * inside MUI's handler chain); neither moved the number by a pixel.
 *
 * **Residual, stated rather than papered over:** a field with less than ~200px
 * below it can still be shifted over, and no static cap fixes that. `FormActions`
 * covers it from the other side by pinning the action row on `xs`, so
 * Abbrechen/Speichern stay reachable while a list is open.
 */
const MENU_PROPS = {
  anchorOrigin: { vertical: 'bottom', horizontal: 'left' },
  transformOrigin: { vertical: 'top', horizontal: 'left' },
  slotProps: { paper: { sx: { maxHeight: 200 } } },
} as const;

interface FormSelectFieldProps<T extends FieldValues> {
  name: Path<T>;
  control: Control<T>;
  label: string;
  options: SelectOption[];
  required?: boolean;
  disabled?: boolean;
  helperText?: string;
  autoFocus?: boolean;
}

export default function FormSelectField<T extends FieldValues>({
  name,
  control,
  label,
  options,
  required,
  disabled,
  helperText,
  autoFocus,
}: FormSelectFieldProps<T>) {
  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => (
        <TextField
          {...field}
          value={field.value ?? ''}
          select
          label={label}
          required={required}
          disabled={disabled}
          autoFocus={autoFocus}
          error={!!error}
          helperText={error?.message ?? helperText}
          fullWidth
          margin="dense"
          sx={{ mb: 1.5 }}
          data-testid={`form-field-${name}`}
          slotProps={{ select: { MenuProps: MENU_PROPS } }}
        >
          {/*
            Each option carries a dedicated testid `form-option-{name}-{value}` and
            a stable `data-value` (from `value`), so tests select by value rather
            than by i18n label text. The clickable trigger is addressed in tests via
            the ARIA `[data-testid='form-field-{name}'] [role='combobox']` (stable
            across MUI versions) instead of the internal `.MuiSelect-select` class.
          */}
          {options.map((opt) => (
            <MenuItem
              key={opt.value}
              value={opt.value}
              disabled={opt.disabled}
              data-testid={`form-option-${name}-${opt.value}`}
            >
              {opt.label}
            </MenuItem>
          ))}
        </TextField>
      )}
    />
  );
}
