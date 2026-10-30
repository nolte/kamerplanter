/**
 * Sun window, summer sun hours and leaf shade of a bed (REQ-053 GP-FR-158/159, GP-UX-057, WP 7.20).
 *
 * The sun window is a group of chips ("Morning / Midday / Afternoon / All day / Changing / Unknown") on
 * native radios, so the arrow keys and the announcement come from the browser; the hours are optional and
 * need no counting. The leaf-shade switch is a hint only: nothing is computed (§29) and the site-fit hint
 * stays as it is (operator decision #2466 item 10), which the helper text says.
 *
 * The component only reports what changed; the caller decides how it is stored: the bed dialog and the
 * field-mode bed sheet send `PATCH /locations/{key}` with `site_conditions.sun_profile` (merged per key by
 * the server); the editor's properties panel commits an `update_fields` operation into the plan save instead
 * (#2538). `touchTarget` is 48 px by default and 64 px in field mode (GP-UX-023).
 */
import { useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import type { SunWindow } from '../model/types';
import type { SunProfile, SunProfilePatch } from './types';

/** The chips in the order of the day; `unknown` (the default) last. */
export const SUN_WINDOW_VALUES: readonly SunWindow[] = [
  'morning',
  'midday',
  'afternoon',
  'all_day',
  'mixed',
  'unknown',
];

const MAX_HOURS = 24;

/** `""` = cleared (`null`), a number in 0..24, or `undefined` for text that is not a valid number. */
export function parseSunHours(text: string): number | null | undefined {
  const trimmed = text.trim().replace(',', '.');
  if (trimmed === '') return null;
  if (!/^\d+(\.\d+)?$/.test(trimmed)) return undefined;
  const value = Number(trimmed);
  return value >= 0 && value <= MAX_HOURS ? value : undefined;
}

/** The stored hours in the language of the page ("6,5" in German), without grouping. */
function hoursText(hours: number | null | undefined, language: string): string {
  return hours === null || hours === undefined
    ? ''
    : new Intl.NumberFormat(language, { maximumFractionDigits: 2, useGrouping: false }).format(hours);
}

export interface SunWindowFieldsProps {
  value: SunProfile;
  /** Only the changed key; the caller stores it. */
  onChange: (patch: SunProfilePatch) => void;
  disabled?: boolean;
  /** Minimum height of every control in px; 64 in field mode. */
  touchTarget?: number;
  testId?: string;
  /** The hours field is invalid (or valid again); the caller may refuse to save meanwhile. */
  onValidityChange?: (valid: boolean) => void;
}

export default function SunWindowFields({
  value,
  onChange,
  disabled = false,
  touchTarget = 48,
  testId = 'bed-view-sun-profile',
  onValidityChange,
}: SunWindowFieldsProps) {
  const { t, i18n } = useTranslation();
  const name = useId();
  const helpId = `${name}-foliage-help`;
  const current = value.sun_window ?? 'unknown';
  const [draft, setDraft] = useState(hoursText(value.direct_sun_hours_summer, i18n.language));
  const [seen, setSeen] = useState(value.direct_sun_hours_summer);
  const [invalid, setInvalidState] = useState(false);
  const setInvalid = (next: boolean) => {
    setInvalidState(next);
    onValidityChange?.(!next);
  };
  // The stored value changed from outside (a reload): show it, drop a stale draft.
  if (value.direct_sun_hours_summer !== seen) {
    setSeen(value.direct_sun_hours_summer);
    setDraft(hoursText(value.direct_sun_hours_summer, i18n.language));
    if (invalid) setInvalid(false);
  }

  const commitHours = () => {
    const parsed = parseSunHours(draft);
    if (parsed === undefined) {
      setInvalid(true);
      return;
    }
    setInvalid(false);
    if (parsed !== (value.direct_sun_hours_summer ?? null)) onChange({ direct_sun_hours_summer: parsed });
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }} data-testid={testId}>
      <Box component="section" aria-labelledby={`${name}-window-title`}>
        <Typography id={`${name}-window-title`} variant="subtitle2" component="h4" sx={{ mb: 0.5 }}>
          {t('pages.gardenPlan.sun.window.title')}
        </Typography>
        <Typography variant="caption" color="text.secondary" component="p" sx={{ mb: 1 }}>
          {t('pages.gardenPlan.sun.window.hint')}
        </Typography>
        <Box
          role="radiogroup"
          aria-labelledby={`${name}-window-title`}
          data-testid={`${testId}-window`}
          sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}
        >
          {SUN_WINDOW_VALUES.map((option) => {
            const checked = current === option;
            const labelId = `${name}-${option}`;
            return (
              <Box
                key={option}
                component="label"
                data-testid={`${testId}-window-${option}`}
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
                  type="radio"
                  name={name}
                  value={option}
                  checked={checked}
                  disabled={disabled}
                  onChange={() => {
                    if (!checked) onChange({ sun_window: option });
                  }}
                  aria-labelledby={labelId}
                  data-testid={`${testId}-window-${option}-input`}
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
                <Typography
                  id={labelId}
                  variant="body2"
                  component="span"
                  sx={{ fontWeight: checked ? 700 : 500 }}
                >
                  {t(`pages.gardenPlan.sun.window.options.${option}`)}
                </Typography>
              </Box>
            );
          })}
        </Box>
      </Box>

      <TextField
        size="small"
        label={t('pages.gardenPlan.sun.hours.label')}
        value={draft}
        disabled={disabled}
        error={invalid}
        helperText={invalid ? t('pages.gardenPlan.sun.hours.invalid') : t('pages.gardenPlan.sun.hours.help')}
        onChange={(event) => setDraft(event.target.value)}
        onBlur={commitHours}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            event.preventDefault();
            commitHours();
          }
        }}
        slotProps={{
          htmlInput: { inputMode: 'decimal', 'data-testid': `${testId}-hours` },
        }}
        sx={{ maxWidth: 360, '& .MuiInputBase-root': { minHeight: touchTarget } }}
      />

      <Box>
        <FormControlLabel
          control={
            <Switch
              checked={value.foliage_shade_in_summer === true}
              disabled={disabled}
              onChange={(event) => onChange({ foliage_shade_in_summer: event.target.checked })}
              slotProps={{ input: { 'aria-describedby': helpId, 'data-testid': `${testId}-foliage` } as object }}
            />
          }
          label={t('pages.gardenPlan.sun.foliage.label')}
          sx={{ minHeight: touchTarget, ml: 0 }}
        />
        <Typography id={helpId} variant="caption" color="text.secondary" component="p">
          {t('pages.gardenPlan.sun.foliage.help')}
        </Typography>
      </Box>
    </Box>
  );
}
