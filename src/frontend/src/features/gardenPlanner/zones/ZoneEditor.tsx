import { useMemo, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormGroup from '@mui/material/FormGroup';
import FormHelperText from '@mui/material/FormHelperText';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { isApiError } from '@/api/errors';
import { useNotification } from '@/hooks/useNotification';
import type { PlanModel } from '../model/planModel';
import { createZone, deleteZone, replaceZoneLocations, updateZone } from './zonesApi';
import {
  IRRIGATION_TYPES,
  type IrrigationZone,
  type IrrigationZoneType,
  type PlanZone,
  type ZoneCreate,
  type ZoneUpdate,
} from './zoneTypes';

const PREFIX = 'pages.gardenPlan.editor.zones';
const DEFAULT_COLOR = '#2E7D32';

interface Props {
  /** `null` creates a zone. */
  zone: IrrigationZone | PlanZone | null;
  siteKey: string;
  plan: PlanModel;
  /** All zones of the site: a bed names the zone it would be taken from. */
  zones: readonly PlanZone[];
  /** The beds selected on the plan, for "take over selection". */
  selectedBedKeys: readonly string[];
  canDelete: boolean;
  /** The `technical` admin scope: the flow rate is a technical value. */
  technical: boolean;
  /** Something was written: reload the zones and the layers. `key` = the zone to show next (null after a delete). */
  onChanged: (key: string | null) => void;
  onCancel: () => void;
}

function sameSet(a: readonly string[], b: readonly string[]): boolean {
  return a.length === b.length && a.every((key) => b.includes(key));
}

function errorKey(failure: unknown): string {
  if (!isApiError(failure)) return 'generic';
  if (failure.statusCode === 403) return 'forbidden';
  if (failure.statusCode === 404) return 'notFound';
  if (failure.errorCode === 'irrigation_zone.quota_exceeded') return 'quota';
  if (failure.statusCode === 422) return 'invalid';
  return 'generic';
}

/**
 * Create or change one zone and assign its beds (REQ-053 GP-FR-110). The beds are a checklist of the beds on the
 * plan; "take over selection" copies the multi-selection of the plan into it. Deleting is offered to the lead only
 * (the backend decides as well); the zone's beds are left alone by a delete.
 */
export function ZoneEditor({ zone, siteKey, plan, zones, selectedBedKeys, canDelete, technical, onChanged, onCancel }: Props) {
  const { t } = useTranslation();
  const notify = useNotification();
  const record = zone as Partial<IrrigationZone> | null;
  const [name, setName] = useState(zone?.name ?? '');
  const [type, setType] = useState<IrrigationZoneType>(zone?.irrigation_type ?? 'manual');
  const [color, setColor] = useState(zone?.color ?? DEFAULT_COLOR);
  const [hint, setHint] = useState(record?.schedule_hint ?? '');
  const [source, setSource] = useState(record?.water_source_key ?? '');
  const [flow, setFlow] = useState(record?.flow_rate_l_per_min != null ? String(record.flow_rate_l_per_min) : '');
  const [beds, setBeds] = useState<string[]>(zone?.location_keys ?? []);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const placedBeds = useMemo(
    () =>
      Object.values(plan.locations)
        .filter((location) => location.geometry != null)
        .sort((a, b) => a.name.localeCompare(b.name)),
    [plan.locations],
  );
  const waterSources = useMemo(
    () => Object.values(plan.gardenObjects).filter((object) => object.object_type === 'water_source'),
    [plan.gardenObjects],
  );
  const zoneOfBed = useMemo(() => {
    const map = new Map<string, PlanZone>();
    for (const other of zones) {
      if (other.key === zone?.key) continue;
      for (const key of other.location_keys) map.set(key, other);
    }
    return map;
  }, [zones, zone?.key]);

  const nameValid = name.trim() !== '';
  const flowNumber = flow.trim() === '' ? null : Number(flow.replace(',', '.'));
  const flowValid = flowNumber === null || (Number.isFinite(flowNumber) && flowNumber > 0);

  const toggleBed = (key: string, checked: boolean) =>
    setBeds((current) => (checked ? [...current, key] : current.filter((other) => other !== key)));
  const takeSelection = () => {
    const known = new Set(placedBeds.map((bed) => bed.key));
    const picked = selectedBedKeys.filter((key) => known.has(key));
    if (picked.length === 0) {
      setNotice(t(`${PREFIX}.form.bedsSelectionEmpty`));
      return;
    }
    setNotice(null);
    setBeds(Array.from(new Set([...beds, ...picked])));
  };

  const save = async (event: FormEvent) => {
    event.preventDefault();
    if (!nameValid || !flowValid || busy) return;
    setBusy(true);
    setError(null);
    let savedKey = zone?.key ?? null;
    let wrote = false;
    try {
      const fields: ZoneCreate = {
        name: name.trim(),
        irrigation_type: type,
        color,
        water_source_key: source === '' ? null : source,
        schedule_hint: hint.trim() === '' ? null : hint.trim(),
      };
      if (technical) fields.flow_rate_l_per_min = flowNumber;
      let moved: Record<string, string> = {};
      if (zone === null) {
        const created = await createZone(siteKey, fields);
        savedKey = created.key;
        wrote = true;
        if (beds.length > 0) moved = (await replaceZoneLocations(created.key, beds)).moved_from;
        notify.success(t(`${PREFIX}.form.created`, { name: created.name }));
      } else {
        const patch: ZoneUpdate = {};
        if (fields.name !== zone.name) patch.name = fields.name;
        if (type !== zone.irrigation_type) patch.irrigation_type = type;
        if (color !== zone.color) patch.color = color;
        if (fields.schedule_hint !== (record?.schedule_hint ?? null)) patch.schedule_hint = fields.schedule_hint;
        if (fields.water_source_key !== (record?.water_source_key ?? null)) patch.water_source_key = fields.water_source_key;
        if (technical && flowNumber !== (record?.flow_rate_l_per_min ?? null)) patch.flow_rate_l_per_min = flowNumber;
        if (Object.keys(patch).length > 0) {
          await updateZone(zone.key, patch);
          wrote = true;
        }
        if (!sameSet(beds, zone.location_keys)) {
          moved = (await replaceZoneLocations(zone.key, beds)).moved_from;
          wrote = true;
        }
        notify.success(t(`${PREFIX}.form.saved`, { name: fields.name }));
      }
      const movedBeds = Object.keys(moved).map((key) => plan.locations[key]?.name ?? key);
      if (movedBeds.length > 0) notify.info(t(`${PREFIX}.form.moved`, { beds: movedBeds.join(', ') }));
      onChanged(savedKey);
    } catch (failure) {
      setError(t(`${PREFIX}.errors.${errorKey(failure)}`));
      if (wrote) onChanged(savedKey);
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (zone === null) return;
    setBusy(true);
    try {
      await deleteZone(zone.key);
      notify.success(t(`${PREFIX}.form.deleted`, { name: zone.name }));
      setConfirmDelete(false);
      onChanged(null);
    } catch (failure) {
      setConfirmDelete(false);
      setError(t(`${PREFIX}.errors.${errorKey(failure)}`));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Box component="form" onSubmit={save} noValidate data-testid="garden-plan-zone-form" sx={{ display: 'grid', gap: 2 }}>
      <Typography variant="subtitle1" component="h3">
        {zone === null ? t(`${PREFIX}.panel.newTitle`) : t(`${PREFIX}.panel.editTitle`, { name: zone.name })}
      </Typography>
      <TextField
        label={t(`${PREFIX}.form.name`)}
        value={name}
        onChange={(event) => setName(event.target.value)}
        required
        error={name !== '' && !nameValid}
        slotProps={{ htmlInput: { maxLength: 200, 'data-testid': 'garden-plan-zone-name' } }}
        sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
      />
      <TextField
        select
        label={t(`${PREFIX}.form.type`)}
        value={type}
        onChange={(event) => setType(event.target.value as IrrigationZoneType)}
        slotProps={{ select: { native: true }, htmlInput: { 'data-testid': 'garden-plan-zone-type' } }}
        sx={{ '& select': { minHeight: 48, boxSizing: 'border-box', display: 'flex', alignItems: 'center' } }}
      >
        {IRRIGATION_TYPES.map((option) => (
          <option key={option} value={option}>
            {t(`enums.irrigationType.${option}`)}
          </option>
        ))}
      </TextField>
      <Box>
        <TextField
          label={t(`${PREFIX}.form.color`)}
          type="color"
          value={color}
          onChange={(event) => setColor(event.target.value.toUpperCase())}
          slotProps={{ htmlInput: { 'data-testid': 'garden-plan-zone-color', style: { minHeight: 48, padding: 4 } } }}
          sx={{ minWidth: 120 }}
        />
        <FormHelperText>{t(`${PREFIX}.form.colorHint`)}</FormHelperText>
      </Box>
      <TextField
        label={t(`${PREFIX}.form.scheduleHint`)}
        value={hint}
        onChange={(event) => setHint(event.target.value)}
        slotProps={{ htmlInput: { maxLength: 500, 'data-testid': 'garden-plan-zone-schedule' } }}
      />
      <TextField
        select
        label={t(`${PREFIX}.form.waterSource`)}
        value={source}
        onChange={(event) => setSource(event.target.value)}
        slotProps={{ select: { native: true }, htmlInput: { 'data-testid': 'garden-plan-zone-water-source' } }}
        sx={{ '& select': { minHeight: 48, boxSizing: 'border-box', display: 'flex', alignItems: 'center' } }}
      >
        <option value="">{t(`${PREFIX}.form.waterSourceNone`)}</option>
        {waterSources.map((object) => (
          <option key={object.key} value={object.key}>
            {object.label || object.key}
          </option>
        ))}
      </TextField>
      {technical && (
        <TextField
          label={t(`${PREFIX}.form.flowRate`)}
          value={flow}
          onChange={(event) => setFlow(event.target.value)}
          error={!flowValid}
          helperText={!flowValid ? t(`${PREFIX}.errors.invalid`) : undefined}
          slotProps={{ htmlInput: { inputMode: 'decimal', 'data-testid': 'garden-plan-zone-flow-rate-input' } }}
        />
      )}

      <Box component="fieldset" sx={{ border: 1, borderColor: 'divider', borderRadius: 1, m: 0, p: 1.5 }} data-testid="garden-plan-zone-beds">
        <Typography component="legend" variant="subtitle2" sx={{ px: 0.5 }}>
          {t(`${PREFIX}.form.beds`)}
        </Typography>
        <FormHelperText sx={{ mt: 0 }}>{t(`${PREFIX}.form.bedsHint`)}</FormHelperText>
        {placedBeds.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            {t(`${PREFIX}.form.bedsNone`)}
          </Typography>
        ) : (
          <FormGroup sx={{ maxHeight: 240, overflowY: 'auto', flexWrap: 'nowrap' }}>
            {placedBeds.map((bed) => {
              const other = zoneOfBed.get(bed.key);
              return (
                <FormControlLabel
                  key={bed.key}
                  sx={{ minHeight: 44 }}
                  control={
                    <Checkbox
                      checked={beds.includes(bed.key)}
                      onChange={(event) => toggleBed(bed.key, event.target.checked)}
                      slotProps={{ input: { 'data-testid': `garden-plan-zone-bed-${bed.key}` } as object }}
                    />
                  }
                  label={other ? `${bed.name} (${t(`${PREFIX}.form.bedInZone`, { zone: other.name })})` : bed.name}
                />
              );
            })}
          </FormGroup>
        )}
        <Button
          onClick={takeSelection}
          sx={{ minHeight: 44, mt: 1 }}
          disabled={placedBeds.length === 0}
          data-testid="garden-plan-zone-take-selection"
        >
          {t(`${PREFIX}.form.bedsUseSelection`)}
        </Button>
        {notice && (
          <Typography variant="body2" role="status" color="text.secondary">
            {notice}
          </Typography>
        )}
      </Box>

      {error && (
        <Alert severity="error" role="alert" data-testid="garden-plan-zone-error">
          {error}
        </Alert>
      )}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        <Button
          type="submit"
          variant="contained"
          disabled={!nameValid || !flowValid || busy}
          sx={{ minHeight: 44 }}
          data-testid="garden-plan-zone-save"
        >
          {t(`${PREFIX}.form.${busy ? 'saving' : 'save'}`)}
        </Button>
        <Button onClick={onCancel} disabled={busy} sx={{ minHeight: 44 }} data-testid="garden-plan-zone-cancel">
          {t(`${PREFIX}.form.cancel`)}
        </Button>
        {zone !== null && canDelete && (
          <Button
            color="error"
            onClick={() => setConfirmDelete(true)}
            disabled={busy}
            sx={{ minHeight: 44, ml: 'auto' }}
            data-testid="garden-plan-zone-delete"
          >
            {t(`${PREFIX}.form.delete`)}
          </Button>
        )}
      </Box>
      {zone !== null && (
        <ConfirmDialog
          open={confirmDelete}
          title={t(`${PREFIX}.form.deleteTitle`, { name: zone.name })}
          message={t(`${PREFIX}.form.deleteMessage`)}
          confirmLabel={t(`${PREFIX}.form.deleteConfirm`)}
          destructive
          loading={busy}
          onConfirm={() => void remove()}
          onCancel={() => setConfirmDelete(false)}
        />
      )}
    </Box>
  );
}
