/**
 * The properties panel (REQ-053 GP-FR-024/156, GP-UX-033/034/049/052/053/054, WP 2.6): the values of
 * the selection, editable, as a sidebar on desktop and as the content of a bottom sheet on phones.
 * Every edit is a `PlanOperation` handed to the editor; a number field commits on blur or Enter as
 * ONE undo step (GP-FR-155). Locked objects show their values but take no input (GP-FR-156). The
 * live validation (containment, simple polygon) marks the field red and explains it before anything
 * reaches the plan (GP-UX-053); the server stays the authority.
 */
import { lazy, Suspense, useMemo, useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Divider from '@mui/material/Divider';
import FormControlLabel from '@mui/material/FormControlLabel';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import Paper from '@mui/material/Paper';
import Stack from '@mui/material/Stack';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import CloseIcon from '@mui/icons-material/Close';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import FlipToBackIcon from '@mui/icons-material/FlipToBack';
import FlipToFrontIcon from '@mui/icons-material/FlipToFront';
import LockIcon from '@mui/icons-material/Lock';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import type { PlanModel } from '../model/planModel';
import type { Geometry, PlanEntity, PlanOperation, SunExposure } from '../model/types';
import type { RendererLabels } from '../renderer';
import type { SelectionRef, SelectionStack } from '../state/gardenPlanSlice';
import { EDITOR_ANCHORS } from './anchors';
import { PANEL_WIDTH_PX } from './layout';
import { NumberField } from './NumberField';
import { insertVertex, removeVertex } from './tools/geometryEdit';
import { isPlanEntity } from './tools/hierarchy';
import type { ActionLabel } from './tools/machineTypes';
import {
  geometryFields,
  pointList,
  sameGeometry,
  setField,
  setPoint,
  type FieldId,
} from './tools/panelFields';
import { stackRefs } from './tools/selection';
import type { ZMove } from './tools/zOrder';
import { firstViolation } from './tools/validation';

// The tiles load when a bed is selected: the panel is part of the editor chunk, the tiles are not (E-12 budget).
const SunTileSelector = lazy(() => import('../bed/SunTileSelector'));

const PREFIX = 'pages.gardenPlan.editor';
const SUN_PREFIX = 'pages.gardenPlan.sun';

/** A tile-sized placeholder while the lazy tiles load, so the panel does not jump. */
const SUN_FALLBACK = <Box sx={{ minHeight: 72 }} aria-hidden />;

/** Axis and turn symbols of GP-UX-054, in front of the field labels. */
const FIELD_SYMBOL: Record<FieldId, string> = {
  x: 'x →',
  y: 'y ↑',
  width: '↔',
  length: '↕',
  radius: 'r',
  rotation: '↺',
  strokeWidth: '↔',
};

export interface PropertiesPanelProps {
  plan: PlanModel;
  selection: SelectionRef[];
  stack: SelectionStack | null;
  labels: RendererLabels;
  /** Sidebar on desktop, content of the bottom sheet on phones. */
  layout: 'sidebar' | 'sheet';
  onCommit: (ops: PlanOperation[], label: ActionLabel) => void;
  onSelect: (selection: SelectionRef[]) => void;
  onStack: (stack: SelectionStack | null) => void;
  onClose?: () => void;
  /** Opens the item menu anchored at the "⋯" button (GP-UX-040). */
  onMore: (anchor: HTMLElement) => void;
  onDuplicate: () => void;
  onDelete: () => void;
  onZOrder: (move: ZMove) => void;
  /** The one action of the empty "nothing selected" state. */
  onDrawBed: () => void;
  /** Opens the detail page of a bed ("Details öffnen" / "Bepflanzen"); absent = no such page. */
  onOpenLocation?: (locationKey: string) => void;
  /** Opens the care tab of a bed (GP-FR-089); absent = no such tab (module switched off). */
  onOpenCare?: (locationKey: string) => void;
}

interface Described {
  title: string;
  subtitle: string;
}

function describe(plan: PlanModel, ref: SelectionRef, labels: RendererLabels): Described {
  if (ref.entity === 'location') {
    const location = plan.locations[ref.key];
    return { title: location?.name ?? ref.key, subtitle: location?.location_type_key ?? '' };
  }
  if (ref.entity === 'garden_object') {
    const garden = plan.gardenObjects[ref.key];
    const type = garden ? labels.objectType(garden.object_type) : '';
    return { title: garden?.label || type || ref.key, subtitle: type };
  }
  if (ref.entity === 'slot')
    return { title: plan.slots[ref.key]?.slot_id ?? ref.key, subtitle: '' };
  const plant = plan.plants[ref.key];
  return { title: plant?.instance_id ?? ref.key, subtitle: plant?.species_key ?? '' };
}

function sourceOf(plan: PlanModel, entity: PlanEntity, key: string) {
  return entity === 'location' ? plan.locations[key] : plan.gardenObjects[key];
}

function EntityForm({
  plan,
  entity,
  entityKey,
  labels,
  onCommit,
  onOpenLocation,
  onOpenCare,
  onDuplicate,
  onDelete,
  onZOrder,
}: Pick<
  PropertiesPanelProps,
  'plan' | 'labels' | 'onCommit' | 'onOpenLocation' | 'onOpenCare' | 'onDuplicate' | 'onDelete' | 'onZOrder'
> & { entity: PlanEntity; entityKey: string }) {
  const { t } = useTranslation();
  const source = sourceOf(plan, entity, entityKey);
  const geometry: Geometry | null = source?.geometry ?? null;
  const locked = source?.locked === true;
  const [error, setError] = useState<string | null>(null);
  const name =
    entity === 'location' ? plan.locations[entityKey]?.name : plan.gardenObjects[entityKey]?.label;
  const [nameDraft, setNameDraft] = useState(name ?? '');
  const [seenName, setSeenName] = useState(name ?? '');
  if ((name ?? '') !== seenName) {
    setSeenName(name ?? '');
    setNameDraft(name ?? '');
  }

  const violation = (next: Geometry): string | null =>
    firstViolation(plan, [{ entity, key: entityKey, geometry: next }]);

  const commitGeometry = (next: Geometry) => {
    if (geometry === null || sameGeometry(next, geometry)) return;
    onCommit([{ op: 'update_geometry', entity, key: entityKey, geometry: next }], 'edit');
  };
  const commitName = () => {
    const trimmed = nameDraft.trim();
    if (trimmed === (name ?? '').trim()) return;
    if (entity === 'location' && trimmed === '') {
      setNameDraft(name ?? ''); // a bed always has a name
      return;
    }
    const op: PlanOperation =
      entity === 'location'
        ? { op: 'update_fields', entity: 'location', key: entityKey, fields: { name: trimmed } }
        : {
            op: 'update_fields',
            entity: 'garden_object',
            key: entityKey,
            fields: { label: trimmed },
          };
    onCommit([op], 'edit');
  };

  const commitSun = (sun: SunExposure) => {
    if (entity !== 'location' || plan.locations[entityKey]?.sun_exposure === sun) return;
    onCommit(
      [{ op: 'update_fields', entity: 'location', key: entityKey, fields: { sun_exposure: sun } }],
      'edit',
    );
  };

  const fields = geometry ? geometryFields(geometry) : [];
  const points = geometry ? pointList(geometry) : [];
  const typeLabel =
    entity === 'garden_object'
      ? labels.objectType(plan.gardenObjects[entityKey]?.object_type ?? 'other')
      : (plan.locations[entityKey]?.location_type_key ?? '');
  const slotCount = Object.values(plan.slots).filter((s) => s.location_key === entityKey).length;
  const plantCount = Object.values(plan.plants).filter((p) => {
    const slot = p.slot_key ? plan.slots[p.slot_key] : undefined;
    return slot ? slot.location_key === entityKey : p.location_key === entityKey;
  }).length;
  const emptyBed = entity === 'location' && slotCount === 0 && plantCount === 0;
  const errorText = error
    ? t(`${PREFIX}.notice.${error}`, { defaultValue: t(`${PREFIX}.notice.generic`) })
    : null;

  return (
    <Stack spacing={1.5} data-testid="garden-plan-panel-form">
      {locked && (
        <Alert
          severity="info"
          icon={<LockIcon fontSize="small" />}
          data-testid="garden-plan-panel-locked"
        >
          {t(`${PREFIX}.panel.lockedHint`)}
        </Alert>
      )}
      <TextField
        size="small"
        label={t(entity === 'location' ? `${PREFIX}.panel.name` : `${PREFIX}.panel.label`)}
        value={nameDraft}
        disabled={locked}
        onChange={(event) => setNameDraft(event.target.value)}
        onBlur={commitName}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            event.preventDefault();
            commitName();
          }
        }}
        slotProps={{ htmlInput: { 'data-testid': 'garden-plan-panel-name' } }}
        sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
      />
      <Typography variant="body2" color="text.secondary" data-testid="garden-plan-panel-type">
        {t(`${PREFIX}.panel.type`, { type: typeLabel })}
      </Typography>

      {entity === 'location' && (
        <Box component="section" aria-labelledby="garden-plan-panel-sun-title" data-testid="garden-plan-panel-sun">
          <Typography variant="subtitle2" component="h4" id="garden-plan-panel-sun-title" sx={{ mb: 0.5 }}>
            {t(`${SUN_PREFIX}.title`)}
          </Typography>
          <Suspense fallback={SUN_FALLBACK}>
            <SunTileSelector
              value={plan.locations[entityKey]?.sun_exposure ?? 'unknown'}
              disabled={locked}
              onChange={commitSun}
            />
          </Suspense>
        </Box>
      )}

      {geometry === null && (
        <Typography variant="body2" color="text.secondary">
          {t(`${PREFIX}.panel.notPlaced`)}
        </Typography>
      )}

      {fields.length > 0 && (
        <Typography variant="subtitle2" component="h4" data-testid="garden-plan-panel-geometry-title">
          {t(`${PREFIX}.panel.geometryTitle`)}
        </Typography>
      )}
      {fields.length > 0 && (
        <Typography variant="body2" color="text.secondary">
          {t(`${PREFIX}.panel.geometryHint`)}
        </Typography>
      )}
      {fields.length > 0 && (
        <Box
          sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 1 }}
          data-testid="garden-plan-panel-geometry"
        >
          {fields.map((field) => (
            <NumberField
              key={field.id}
              label={`${FIELD_SYMBOL[field.id]} ${t(`${PREFIX}.panel.fields.${field.id}`)}`}
              value={field.value}
              unit={field.unit === 'deg' ? '°' : 'm'}
              min={field.min}
              max={field.max}
              disabled={locked}
              testId={`garden-plan-panel-field-${field.id}`}
              validate={(value) =>
                geometry ? violation(setField(geometry, field.id, value)) : null
              }
              onError={setError}
              errorText={t(`${PREFIX}.panel.fieldInvalid`)}
              onCommit={(value) => geometry && commitGeometry(setField(geometry, field.id, value))}
            />
          ))}
        </Box>
      )}

      {geometry !== null && points.length > 0 && (
        <Box data-testid="garden-plan-panel-points">
          <Typography variant="subtitle2" component="h4" sx={{ mb: 0.5 }}>
            {t(`${PREFIX}.panel.points`, { count: points.length })}
          </Typography>
          <Stack spacing={1}>
            {points.map(([px, py], index) => (
              // The index is the identity of a point: they have no key, and the list is rebuilt from the geometry.
              <Box key={index} sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                <NumberField
                  label={`${index + 1} · x →`}
                  value={px}
                  unit="m"
                  disabled={locked}
                  testId={`garden-plan-panel-point-${index}-x`}
                  validate={(value) => violation(setPoint(geometry, index, [value, py]))}
                  onError={setError}
                  errorText={t(`${PREFIX}.panel.fieldInvalid`)}
                  onCommit={(value) => commitGeometry(setPoint(geometry, index, [value, py]))}
                />
                <NumberField
                  label={`${index + 1} · y ↑`}
                  value={py}
                  unit="m"
                  disabled={locked}
                  testId={`garden-plan-panel-point-${index}-y`}
                  validate={(value) => violation(setPoint(geometry, index, [px, value]))}
                  onError={setError}
                  errorText={t(`${PREFIX}.panel.fieldInvalid`)}
                  onCommit={(value) => commitGeometry(setPoint(geometry, index, [px, value]))}
                />
                <Tooltip title={t(`${PREFIX}.vertex.delete`)}>
                  <span>
                    <IconButton
                      aria-label={t(`${PREFIX}.panel.deletePoint`, { n: index + 1 })}
                      disabled={locked || removeVertex(geometry, index) === null}
                      onClick={() => {
                        const next = removeVertex(geometry, index);
                        if (!next) return;
                        const code = violation(next);
                        if (code) setError(code);
                        else commitGeometry(next);
                      }}
                      sx={{ width: 48, height: 48 }}
                    >
                      <DeleteOutlinedIcon />
                    </IconButton>
                  </span>
                </Tooltip>
              </Box>
            ))}
          </Stack>
          <Button
            size="small"
            disabled={locked}
            onClick={() =>
              commitGeometry(
                insertVertex(geometry, points.length - (geometry.kind === 'polygon' ? 1 : 2)),
              )
            }
            sx={{ mt: 1, minHeight: 48 }}
            data-testid="garden-plan-panel-add-point"
          >
            {t(`${PREFIX}.vertex.insert`)}
          </Button>
        </Box>
      )}

      {errorText && (
        <Alert severity="error" data-testid="garden-plan-panel-error">
          {errorText}
        </Alert>
      )}

      {emptyBed && (
        <Box data-testid="garden-plan-panel-empty-bed">
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {t(`${PREFIX}.panel.emptyBed`)}
          </Typography>
          {onOpenLocation && (
            <Button
              variant="outlined"
              onClick={() => onOpenLocation(entityKey)}
              sx={{ minHeight: 48 }}
              data-testid="garden-plan-panel-plant"
            >
              {t(`${PREFIX}.panel.plant`)}
            </Button>
          )}
        </Box>
      )}

      <Divider />
      <FormControlLabel
        control={
          <Switch
            checked={locked}
            onChange={(_event, checked) =>
              onCommit(
                [{ op: 'set_locked', entity, key: entityKey, locked: checked }],
                checked ? 'lock' : 'unlock',
              )
            }
            slotProps={{ input: { 'data-testid': 'garden-plan-panel-locked-switch' } as never }}
          />
        }
        label={t(`${PREFIX}.panel.locked`)}
        sx={{ minHeight: 48, m: 0 }}
      />
      <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap' }}>
        <Button
          startIcon={<ContentCopyIcon />}
          onClick={onDuplicate}
          sx={{ minHeight: 48 }}
          data-testid="garden-plan-panel-duplicate"
        >
          {t(`${PREFIX}.contextMenu.duplicate`)}
        </Button>
        <Button
          startIcon={<FlipToFrontIcon />}
          onClick={() => onZOrder('front')}
          sx={{ minHeight: 48 }}
          data-testid="garden-plan-panel-front"
        >
          {t(`${PREFIX}.contextMenu.front`)}
        </Button>
        <Button
          startIcon={<FlipToBackIcon />}
          onClick={() => onZOrder('back')}
          sx={{ minHeight: 48 }}
          data-testid="garden-plan-panel-back"
        >
          {t(`${PREFIX}.contextMenu.back`)}
        </Button>
        <Button
          color="error"
          startIcon={<DeleteOutlinedIcon />}
          onClick={onDelete}
          disabled={locked}
          sx={{ minHeight: 48 }}
          data-testid="garden-plan-panel-delete"
        >
          {t(`${PREFIX}.delete.label`)}
        </Button>
      </Stack>
      {entity === 'location' && onOpenLocation && (
        <Button
          variant="text"
          onClick={() => onOpenLocation(entityKey)}
          sx={{ minHeight: 48, alignSelf: 'flex-start' }}
          data-testid="garden-plan-panel-details"
        >
          {t(`${PREFIX}.panel.openDetails`)}
        </Button>
      )}
      {entity === 'location' && onOpenCare && (plan.locations[entityKey]?.open_task_count ?? 0) > 0 && (
        <Button
          variant="text"
          color={(plan.locations[entityKey]?.overdue_task_count ?? 0) > 0 ? 'error' : 'primary'}
          onClick={() => onOpenCare(entityKey)}
          sx={{ minHeight: 48, alignSelf: 'flex-start' }}
          data-testid="garden-plan-panel-care"
        >
          {t(`${PREFIX}.panel.openCare`, {
            open: plan.locations[entityKey]?.open_task_count ?? 0,
            overdue: plan.locations[entityKey]?.overdue_task_count ?? 0,
          })}
        </Button>
      )}
    </Stack>
  );
}

/**
 * "Sonne für alle gewählten Beete setzen" (GP-FR-157, TC-053-036): one tile choice for every selected,
 * unlocked bed, as ONE undo step. A bed that already has the value is not touched; a lock guards the
 * structure only (GP-NFR-007) but the panel takes no input on a locked object (GP-FR-156), so locked
 * beds stay as they are.
 */
function SunBulk({
  plan,
  selection,
  onCommit,
}: Pick<PropertiesPanelProps, 'plan' | 'selection' | 'onCommit'>) {
  const { t } = useTranslation();
  const beds = selection
    .filter((ref) => ref.entity === 'location')
    .map((ref) => plan.locations[ref.key])
    .filter((location) => location !== undefined);
  const open = beds.filter((location) => !location.locked);
  if (beds.length === 0) return null;
  const values = new Set(open.map((location) => location.sun_exposure));
  const common: SunExposure | null = values.size === 1 ? [...values][0] : null;

  const apply = (sun: SunExposure) => {
    const ops: PlanOperation[] = open
      .filter((location) => location.sun_exposure !== sun)
      .map((location) => ({
        op: 'update_fields',
        entity: 'location',
        key: location.key,
        fields: { sun_exposure: sun },
      }));
    if (ops.length > 0) onCommit(ops, 'edit');
  };

  return (
    <Box component="section" aria-labelledby="garden-plan-panel-sun-bulk" data-testid="garden-plan-panel-sun-bulk">
      <Typography variant="subtitle2" component="h4" id="garden-plan-panel-sun-bulk">
        {t(`${SUN_PREFIX}.bulk.title`)}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {open.length === 0
          ? t(`${SUN_PREFIX}.bulk.locked`)
          : t(`${SUN_PREFIX}.bulk.hint`, { count: open.length })}
        {open.length > 1 && common === null ? ` ${t(`${SUN_PREFIX}.bulk.mixed`)}` : ''}
      </Typography>
      <Suspense fallback={SUN_FALLBACK}>
        <SunTileSelector
          value={common}
          disabled={open.length === 0}
          label={t(`${SUN_PREFIX}.bulk.title`)}
          testId="sun-tile-selector-bulk"
          onChange={apply}
        />
      </Suspense>
    </Box>
  );
}

/** "Objekte an dieser Stelle (n)" / "Pflanzen in der Nähe (n)" (GP-UX-033/034). */
function StackList({
  plan,
  stack,
  labels,
  onSelect,
  onStack,
}: Pick<PropertiesPanelProps, 'plan' | 'stack' | 'labels' | 'onSelect' | 'onStack'>) {
  const { t } = useTranslation();
  const refs = useMemo(() => (stack ? stackRefs(plan, stack.keys) : []), [plan, stack]);
  if (!stack || refs.length < 2) return null;
  const plants = refs.every((ref) => ref.entity === 'plant' || ref.entity === 'slot');
  return (
    <Box data-testid="garden-plan-panel-stack">
      <Typography variant="subtitle2" component="h4">
        {t(plants ? `${PREFIX}.panel.plantsNearby` : `${PREFIX}.panel.stack`, {
          count: refs.length,
        })}
      </Typography>
      <List dense={!plants} disablePadding>
        {refs.map((ref, index) => {
          const info = describe(plan, ref, labels);
          return (
            <ListItemButton
              key={`${ref.entity}:${ref.key}`}
              selected={index === stack.index}
              onClick={() => {
                onSelect([ref]);
                onStack({ ...stack, index });
              }}
              sx={{ minHeight: plants ? 64 : 48 }}
              data-testid={`garden-plan-panel-stack-item-${ref.key}`}
            >
              <ListItemText primary={info.title} secondary={info.subtitle || undefined} />
            </ListItemButton>
          );
        })}
      </List>
    </Box>
  );
}

export function PropertiesPanel(props: PropertiesPanelProps) {
  const { plan, selection, labels, layout, onClose, onMore, onSelect, onStack, onDrawBed } = props;
  const { t } = useTranslation();
  const entities = selection.filter(isPlanEntity);
  const single = selection.length === 1 ? selection[0] : null;

  let body: ReactNode;
  let title = t(`${PREFIX}.panel.title`);
  // A selection can be ahead of the plan by one render (a deleted object): it shows nothing then.
  if (single !== null && isPlanEntity(single) && sourceOf(plan, single.entity, single.key)) {
    title = describe(plan, single, labels).title;
    body = (
      <EntityForm
        // A new selection starts with fresh drafts and no stale error.
        key={`${single.entity}:${single.key}`}
        plan={plan}
        entity={single.entity}
        entityKey={single.key}
        labels={labels}
        onCommit={props.onCommit}
        onOpenLocation={props.onOpenLocation}
        onOpenCare={props.onOpenCare}
        onDuplicate={props.onDuplicate}
        onDelete={props.onDelete}
        onZOrder={props.onZOrder}
      />
    );
  } else if (single !== null && !isPlanEntity(single)) {
    const info = describe(plan, single, labels);
    title = info.title;
    body = (
      <Typography variant="body2" color="text.secondary" data-testid="garden-plan-panel-readonly">
        {t(`${PREFIX}.panel.${single.entity === 'slot' ? 'slotInfo' : 'plantInfo'}`, {
          name: info.title,
          species: info.subtitle,
        })}
      </Typography>
    );
  } else if (selection.length > 1) {
    title = t(`${PREFIX}.panel.multiTitle`, { count: selection.length });
    body = (
      <Stack spacing={1.5} data-testid="garden-plan-panel-multi">
        <Typography variant="body2" color="text.secondary">
          {t(`${PREFIX}.panel.multiHint`)}
        </Typography>
        <SunBulk plan={plan} selection={selection} onCommit={props.onCommit} />
        <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: 'wrap' }}>
          <Button
            startIcon={<ContentCopyIcon />}
            onClick={props.onDuplicate}
            disabled={entities.length === 0}
            sx={{ minHeight: 48 }}
            data-testid="garden-plan-panel-duplicate"
          >
            {t(`${PREFIX}.contextMenu.duplicate`)}
          </Button>
          <Button
            startIcon={<FlipToFrontIcon />}
            onClick={() => props.onZOrder('front')}
            disabled={entities.length === 0}
            sx={{ minHeight: 48 }}
          >
            {t(`${PREFIX}.contextMenu.front`)}
          </Button>
          <Button
            startIcon={<FlipToBackIcon />}
            onClick={() => props.onZOrder('back')}
            disabled={entities.length === 0}
            sx={{ minHeight: 48 }}
          >
            {t(`${PREFIX}.contextMenu.back`)}
          </Button>
          <Button
            color="error"
            startIcon={<DeleteOutlinedIcon />}
            onClick={props.onDelete}
            disabled={entities.length === 0}
            sx={{ minHeight: 48 }}
            data-testid="garden-plan-panel-delete"
          >
            {t(`${PREFIX}.delete.label`)}
          </Button>
        </Stack>
      </Stack>
    );
  } else if (props.stack && stackRefs(plan, props.stack.keys).length >= 2) {
    // The list below is the whole point of the sheet: plants nearby a tap (GP-UX-034).
    title = t(`${PREFIX}.panel.title`);
    body = null;
  } else {
    body = (
      <Box data-testid="garden-plan-panel-empty">
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          {t(`${PREFIX}.panel.nothingSelected`)}
        </Typography>
        <Button
          variant="outlined"
          onClick={onDrawBed}
          sx={{ minHeight: 48 }}
          data-testid="garden-plan-panel-draw-bed"
        >
          {t(`${PREFIX}.panel.drawBed`)}
        </Button>
      </Box>
    );
  }

  return (
    <Paper
      variant="outlined"
      component="section"
      id={EDITOR_ANCHORS.panel}
      tabIndex={-1} // the skip link "To the properties panel" focuses the region itself
      aria-label={t(`${PREFIX}.panel.region`)}
      data-testid="garden-plan-panel"
      data-layout={layout}
      sx={{
        p: 1.5,
        display: 'flex',
        flexDirection: 'column',
        gap: 1.5,
        overflowY: 'auto',
        ...(layout === 'sidebar'
          ? { width: PANEL_WIDTH_PX, flexShrink: 0, alignSelf: 'flex-start', maxHeight: '80vh' }
          : {}),
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <Typography
          variant="h6"
          component="h3"
          sx={{ flexGrow: 1, minWidth: 0, overflowWrap: 'anywhere' }}
          data-testid="garden-plan-panel-title"
        >
          {title}
        </Typography>
        {entities.length > 0 && (
          <Tooltip title={t(`${PREFIX}.contextMenu.more`)}>
            <IconButton
              aria-label={t(`${PREFIX}.contextMenu.more`)}
              aria-haspopup="menu"
              onClick={(event) => onMore(event.currentTarget)}
              sx={{ width: 48, height: 48 }}
              data-testid="garden-plan-panel-more"
            >
              <MoreVertIcon />
            </IconButton>
          </Tooltip>
        )}
        {layout === 'sheet' && onClose && (
          <Tooltip title={t(`${PREFIX}.panel.close`)}>
            <IconButton
              aria-label={t(`${PREFIX}.panel.close`)}
              onClick={onClose}
              sx={{ width: 48, height: 48 }}
              data-testid="garden-plan-panel-close"
            >
              <CloseIcon />
            </IconButton>
          </Tooltip>
        )}
      </Box>
      {body}
      <StackList
        plan={plan}
        stack={props.stack}
        labels={labels}
        onSelect={onSelect}
        onStack={onStack}
      />
    </Paper>
  );
}
