/**
 * The fields of a water source in the properties panel (REQ-053 GP-FR-111, WP 9.14): its kind, the capacity of a
 * barrel or cistern and when it was last refilled - exactly what `WaterSourceProps` carries, nothing more. Each
 * change is ONE `update_fields` with the whole props object (the server replaces `props`), through the pending
 * model like every panel edit, so it is one undo step and part of the next save.
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import InputAdornment from '@mui/material/InputAdornment';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import type { PlanOperation, WaterSourceKind, WaterSourceProps } from '../model/types';
import { formatDecimal } from '../model/units';
import { parseDecimal } from './tools/panelFields';
import type { ActionLabel } from './tools/machineTypes';

const PREFIX = 'pages.gardenPlan.editor.panel.waterSource';

/** The kinds of §9.5, in the order of the spec. */
const WATER_SOURCE_KINDS: readonly WaterSourceKind[] = [
  'tap',
  'rain_barrel',
  'well',
  'pond',
  'cistern',
  'hose_reel',
];

/** The ceiling of the capacity field: a cistern of a large garden, not a reservoir (a typo guard only). */
const MAX_CAPACITY_LITERS = 1_000_000;

interface WaterSourceFieldsProps {
  objectKey: string;
  props: WaterSourceProps;
  disabled: boolean;
  onCommit: (ops: PlanOperation[], label: ActionLabel) => void;
}

/**
 * `YYYY-MM-DD` of a stored instant on the UTC calendar, or `''` (also for a value that is no instant). Read through
 * `Date`, not by cutting the string: an instant with an offset (`2026-11-02T23:30:00-02:00`) is the next UTC day.
 */
function dayOf(instant: string | null | undefined): string {
  if (!instant) return '';
  const parsed = new Date(instant);
  return Number.isNaN(parsed.getTime()) ? '' : parsed.toISOString().slice(0, 10);
}

/** Today on the UTC calendar: the latest day a source can have been refilled (the server refuses a later one). */
const todayUtc = (): string => new Date().toISOString().slice(0, 10);

export function WaterSourceFields({ objectKey, props, disabled, onCommit }: WaterSourceFieldsProps) {
  const { t, i18n } = useTranslation();
  const language = i18n.language;
  const storedCapacity = props.capacity_liters ?? null;
  const [capacityText, setCapacityText] = useState(() => formatDecimal(storedCapacity, language));
  const [seenCapacity, setSeenCapacity] = useState({ stored: storedCapacity, language });
  // The model changed under the field (undo, another edit) or the language did: show the stored value (derived state).
  if (storedCapacity !== seenCapacity.stored || language !== seenCapacity.language) {
    setSeenCapacity({ stored: storedCapacity, language });
    setCapacityText(formatDecimal(storedCapacity, language));
  }
  const storedDay = dayOf(props.last_refilled_at);
  const [dayDraft, setDayDraft] = useState(storedDay);
  const [seenDay, setSeenDay] = useState(storedDay);
  if (storedDay !== seenDay) {
    setSeenDay(storedDay);
    setDayDraft(storedDay);
  }
  const today = todayUtc();
  const dayInFuture = dayDraft !== '' && dayDraft > today;
  // A date input yields `''` while it is incomplete: only a whole day or an emptied field is committed.
  const commitDay = () => {
    if (dayDraft === storedDay || dayInFuture) return;
    if (dayDraft !== '' && !/^\d{4}-\d{2}-\d{2}$/.test(dayDraft)) return;
    commit({ last_refilled_at: dayDraft === '' ? null : `${dayDraft}T00:00:00Z` });
  };

  const parsed = capacityText.trim() === '' ? null : parseDecimal(capacityText);
  const capacityInvalid =
    capacityText.trim() !== '' && (parsed === null || parsed <= 0 || parsed > MAX_CAPACITY_LITERS);

  const commit = (patch: Partial<Omit<WaterSourceProps, 'object_type'>>) => {
    const next: WaterSourceProps = { ...props, ...patch, object_type: 'water_source' };
    if (JSON.stringify(next) === JSON.stringify({ ...props, object_type: 'water_source' })) return;
    onCommit(
      [
        {
          op: 'update_fields',
          entity: 'garden_object',
          key: objectKey,
          fields: { props: next as unknown as Record<string, unknown> },
        },
      ],
      'edit',
    );
  };

  const commitCapacity = () => {
    if (capacityInvalid) return;
    if (parsed === (props.capacity_liters ?? null)) return;
    commit({ capacity_liters: parsed });
  };

  return (
    <Box
      component="section"
      aria-labelledby="garden-plan-panel-water-source-title"
      data-testid="garden-plan-panel-water-source"
      sx={{ display: 'grid', gap: 1.5 }}
    >
      <Typography variant="subtitle2" component="h4" id="garden-plan-panel-water-source-title">
        {t(`${PREFIX}.title`)}
      </Typography>
      <TextField
        select
        size="small"
        label={t(`${PREFIX}.kind`)}
        value={props.water_source_kind}
        disabled={disabled}
        onChange={(event) => commit({ water_source_kind: event.target.value as WaterSourceKind })}
        slotProps={{ htmlInput: { 'data-testid': 'garden-plan-panel-water-source-kind' } }}
        sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
      >
        {WATER_SOURCE_KINDS.map((kind) => (
          <MenuItem key={kind} value={kind} sx={{ minHeight: 48 }}>
            {t(`enums.waterSourceKind.${kind}`)}
          </MenuItem>
        ))}
      </TextField>
      <TextField
        size="small"
        label={t(`${PREFIX}.capacity`)}
        value={capacityText}
        disabled={disabled}
        error={capacityInvalid}
        helperText={capacityInvalid ? t(`${PREFIX}.capacityInvalid`) : t(`${PREFIX}.capacityHelp`)}
        onChange={(event) => setCapacityText(event.target.value)}
        onBlur={commitCapacity}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            event.preventDefault();
            commitCapacity();
          } else if (event.key === 'Escape') {
            event.stopPropagation();
            setCapacityText(formatDecimal(storedCapacity, language));
          }
        }}
        slotProps={{
          htmlInput: { inputMode: 'decimal', 'data-testid': 'garden-plan-panel-water-source-capacity' },
          input: { endAdornment: <InputAdornment position="end">{t(`${PREFIX}.litres`)}</InputAdornment> },
        }}
        sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
      />
      <TextField
        size="small"
        type="date"
        label={t(`${PREFIX}.lastRefilled`)}
        value={dayDraft}
        disabled={disabled}
        error={dayInFuture}
        helperText={t(`${PREFIX}.${dayInFuture ? 'lastRefilledFuture' : 'lastRefilledHelp'}`)}
        onChange={(event) => setDayDraft(event.target.value)}
        onBlur={commitDay}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            event.preventDefault();
            commitDay();
          }
        }}
        slotProps={{
          inputLabel: { shrink: true },
          htmlInput: { max: today, 'data-testid': 'garden-plan-panel-water-source-refilled' },
        }}
        sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
      />
    </Box>
  );
}
