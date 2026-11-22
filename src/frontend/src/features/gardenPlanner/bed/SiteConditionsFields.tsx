/**
 * Microclimate, wind, slope, aspect, access sides and competition flags of a bed (REQ-053 GP-FR-162/163/165/168,
 * GP-UX-057, WP 8.22, WP 9.11).
 *
 * Frost risk, stored heat and wind are chips (with "Unknown" last, the default), the cold-air pocket is a
 * switch, slope and aspect are optional numbers (degrees), the access sides are four toggles and the competition
 * flags (root competition, allelopathy) two more - a note only, no value is derived from them. All of it is
 * entered by hand; nothing is derived (§29). The component only reports what changed, per part; the caller
 * stores it with `PATCH /locations/{key}` (merged per key by the server). `touchTarget` is 48 px by default.
 *
 * On an indoor site (`indoor`, `windowsill`, `grow_tent` - GP-FR-182, WP 10.8) the weather, frost and wind features
 * are hidden: frost risk, cold-air pocket, stored heat and wind. Slope, aspect, access sides and the competition
 * flags stay. A stored value of a hidden feature is kept as it is - hiding never writes.
 */
import { useCallback, useEffect, useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import type { SiteType } from '@/api/types';
import { isIndoorPlanSite } from '../model/siteKind';
import type { FrostRisk, WindExposure } from '../model/types';
import ChipChoice from './ChipChoice';
import type { AccessSide, HeatRetention, SiteConditionsPatch, SiteConditionsSlice, SiteFlag } from './types';

export const FROST_RISK_VALUES: readonly FrostRisk[] = ['low', 'normal', 'high', 'unknown'];
export const HEAT_RETENTION_VALUES: readonly HeatRetention[] = ['none', 'wall', 'building', 'unknown'];
export const WIND_EXPOSURE_VALUES: readonly WindExposure[] = ['sheltered', 'normal', 'exposed', 'unknown'];
export const ACCESS_SIDE_VALUES: readonly AccessSide[] = ['N', 'E', 'S', 'W'];
export const SITE_FLAG_VALUES: readonly SiteFlag[] = ['root_competition', 'allelopathy_risk'];

const SLOPE_MAX = 90;
const ASPECT_MAX_EXCLUSIVE = 360;

/** `""` = cleared (`null`), a number in range, or `undefined` for text that is not a valid number. */
export function parseDegrees(text: string, max: number, maxInclusive: boolean): number | null | undefined {
  const trimmed = text.trim().replace(',', '.');
  if (trimmed === '') return null;
  if (!/^\d+(\.\d+)?$/.test(trimmed)) return undefined;
  const value = Number(trimmed);
  return value >= 0 && (maxInclusive ? value <= max : value < max) ? value : undefined;
}

function degreesText(value: number | null | undefined, language: string): string {
  return value === null || value === undefined
    ? ''
    : new Intl.NumberFormat(language, { maximumFractionDigits: 1, useGrouping: false }).format(value);
}

interface DegreesFieldProps {
  label: string;
  help: string;
  invalid: string;
  stored: number | null | undefined;
  max: number;
  maxInclusive: boolean;
  disabled: boolean;
  touchTarget: number;
  testId: string;
  onCommit: (value: number | null) => void;
  onValidityChange: (valid: boolean) => void;
}

/** One optional number with a draft: it is committed on blur or Enter, an unreadable entry is shown in red. */
function DegreesField({
  label,
  help,
  invalid,
  stored,
  max,
  maxInclusive,
  disabled,
  touchTarget,
  testId,
  onCommit,
  onValidityChange,
}: DegreesFieldProps) {
  const { i18n } = useTranslation();
  const [draft, setDraft] = useState(degreesText(stored, i18n.language));
  const [seen, setSeen] = useState(stored);
  const [bad, setBad] = useState(false);
  // The parent learns about the entry's validity after the render, never during it.
  useEffect(() => onValidityChange(!bad), [bad, onValidityChange]);
  // The stored value changed from outside (a reload): show it and drop a stale draft.
  if (stored !== seen) {
    setSeen(stored);
    setDraft(degreesText(stored, i18n.language));
    if (bad) setBad(false);
  }
  const commit = () => {
    // Merely focusing and leaving the field changes nothing: the shown text is a rounded form of the stored value.
    if (!bad && draft === degreesText(stored, i18n.language)) return;
    const parsed = parseDegrees(draft, max, maxInclusive);
    if (parsed === undefined) {
      setBad(true);
      return;
    }
    setBad(false);
    if (parsed !== (stored ?? null)) onCommit(parsed);
  };
  return (
    <TextField
      size="small"
      label={label}
      value={draft}
      disabled={disabled}
      error={bad}
      helperText={bad ? invalid : help}
      onChange={(event) => setDraft(event.target.value)}
      onBlur={commit}
      onKeyDown={(event) => {
        if (event.key === 'Enter') {
          event.preventDefault();
          commit();
        }
      }}
      slotProps={{ htmlInput: { inputMode: 'decimal', 'data-testid': testId } }}
      sx={{ maxWidth: 360, '& .MuiInputBase-root': { minHeight: touchTarget } }}
    />
  );
}

export interface SiteConditionsFieldsProps {
  value: SiteConditionsSlice;
  /** Only the changed part; the caller stores it. */
  onChange: (patch: SiteConditionsPatch) => void;
  disabled?: boolean;
  touchTarget?: number;
  testId?: string;
  /** A degrees field is invalid (or valid again); the caller may refuse to save meanwhile. */
  onValidityChange?: (valid: boolean) => void;
  /** The type of the bed's site; an indoor type hides weather, frost and wind (GP-FR-182). Unknown = shown. */
  siteType?: SiteType | null;
}

export default function SiteConditionsFields({
  value,
  onChange,
  disabled = false,
  touchTarget = 48,
  testId = 'bed-view-site-conditions',
  onValidityChange,
  siteType = null,
}: SiteConditionsFieldsProps) {
  const outdoor = !isIndoorPlanSite(siteType);
  const { t } = useTranslation();
  const name = useId();
  const [valid, setValid] = useState({ slope: true, aspect: true });
  const allValid = valid.slope && valid.aspect;
  useEffect(() => onValidityChange?.(allValid), [allValid, onValidityChange]);
  const onSlopeValidity = useCallback(
    (ok: boolean) => setValid((previous) => (previous.slope === ok ? previous : { ...previous, slope: ok })),
    [],
  );
  const onAspectValidity = useCallback(
    (ok: boolean) => setValid((previous) => (previous.aspect === ok ? previous : { ...previous, aspect: ok })),
    [],
  );
  const risk = value.microclimate?.frost_risk ?? 'unknown';
  const heat = value.microclimate?.heat_retention ?? 'unknown';
  const wind = value.wind_exposure ?? 'unknown';
  const sides = value.access_sides ?? [];
  const flags = value.flags ?? [];
  const labelled = <T extends string>(values: readonly T[], enumName: string) =>
    values.map((option) => {
      // Widened to `string`: i18next 27 rejects a key whose type still holds the generic `T`.
      const key: string = `enums.${enumName}.${option}`;
      return { value: option, label: t(key) };
    });
  const coldHelpId = `${name}-cold-help`;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }} data-testid={testId}>
      {outdoor && (
        <>
          <ChipChoice
            title={t('pages.gardenPlan.siteConditions.frost.title')}
            hint={t('pages.gardenPlan.siteConditions.frost.hint')}
            options={labelled(FROST_RISK_VALUES, 'frostRisk')}
            value={[risk]}
            mode="single"
            onToggle={(option) => onChange({ microclimate: { frost_risk: option } })}
            disabled={disabled}
            touchTarget={touchTarget}
            testId={`${testId}-frost`}
          />
          <Box>
            <FormControlLabel
              control={
                <Switch
                  checked={value.microclimate?.cold_air_pocket === true}
                  disabled={disabled}
                  onChange={(event) => onChange({ microclimate: { cold_air_pocket: event.target.checked } })}
                  slotProps={{ input: { 'aria-describedby': coldHelpId, 'data-testid': `${testId}-cold-air` } as object }}
                />
              }
              label={t('pages.gardenPlan.siteConditions.coldAirPocket.label')}
              sx={{ minHeight: touchTarget, ml: 0 }}
            />
            <Typography id={coldHelpId} variant="caption" color="text.secondary" component="p">
              {t('pages.gardenPlan.siteConditions.coldAirPocket.help')}
            </Typography>
          </Box>
          <ChipChoice
            title={t('pages.gardenPlan.siteConditions.heat.title')}
            hint={t('pages.gardenPlan.siteConditions.heat.hint')}
            options={labelled(HEAT_RETENTION_VALUES, 'heatRetention')}
            value={[heat]}
            mode="single"
            onToggle={(option) => onChange({ microclimate: { heat_retention: option } })}
            disabled={disabled}
            touchTarget={touchTarget}
            testId={`${testId}-heat`}
          />
          <ChipChoice
            title={t('pages.gardenPlan.siteConditions.wind.title')}
            hint={t('pages.gardenPlan.siteConditions.wind.hint')}
            options={labelled(WIND_EXPOSURE_VALUES, 'windExposure')}
            value={[wind]}
            mode="single"
            onToggle={(option) => onChange({ wind_exposure: option })}
            disabled={disabled}
            touchTarget={touchTarget}
            testId={`${testId}-wind`}
          />
        </>
      )}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
        <DegreesField
          label={t('pages.gardenPlan.siteConditions.slope.label')}
          help={t('pages.gardenPlan.siteConditions.slope.help')}
          invalid={t('pages.gardenPlan.siteConditions.slope.invalid')}
          stored={value.slope_deg}
          max={SLOPE_MAX}
          maxInclusive
          disabled={disabled}
          touchTarget={touchTarget}
          testId={`${testId}-slope`}
          onCommit={(slope) => onChange({ slope_deg: slope })}
          onValidityChange={onSlopeValidity}
        />
        <DegreesField
          label={t('pages.gardenPlan.siteConditions.aspect.label')}
          help={t('pages.gardenPlan.siteConditions.aspect.help')}
          invalid={t('pages.gardenPlan.siteConditions.aspect.invalid')}
          stored={value.aspect_deg}
          max={ASPECT_MAX_EXCLUSIVE}
          maxInclusive={false}
          disabled={disabled}
          touchTarget={touchTarget}
          testId={`${testId}-aspect`}
          onCommit={(aspect) => onChange({ aspect_deg: aspect })}
          onValidityChange={onAspectValidity}
        />
      </Box>
      <ChipChoice
        title={t('pages.gardenPlan.siteConditions.access.title')}
        hint={t('pages.gardenPlan.siteConditions.access.hint')}
        options={labelled(ACCESS_SIDE_VALUES, 'accessSide')}
        value={sides}
        mode="multiple"
        onToggle={(side) =>
          onChange({
            access_sides: sides.includes(side) ? sides.filter((entry) => entry !== side) : [...sides, side],
          })
        }
        disabled={disabled}
        touchTarget={touchTarget}
        testId={`${testId}-access`}
      />
      <ChipChoice
        title={t('pages.gardenPlan.siteConditions.flags.title')}
        hint={t('pages.gardenPlan.siteConditions.flags.hint')}
        options={labelled(SITE_FLAG_VALUES, 'siteFlag')}
        value={flags}
        mode="multiple"
        onToggle={(flag) =>
          onChange({ flags: flags.includes(flag) ? flags.filter((entry) => entry !== flag) : [...flags, flag] })
        }
        disabled={disabled}
        touchTarget={touchTarget}
        testId={`${testId}-flags`}
      />
    </Box>
  );
}
