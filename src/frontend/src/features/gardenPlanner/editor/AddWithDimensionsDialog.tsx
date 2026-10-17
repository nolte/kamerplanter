/**
 * "Add with dimensions" (REQ-053 GP-UX-046, WP 2.6): type, shape, size, position and rotation typed
 * in - the keyboard and touch alternative to drawing, and the place where a new bed or object gets
 * its type. The result goes through the same live validation as a drawn shape; a refusal is
 * explained inside the dialog and nothing is created. A reference-object distance ("2 m from the
 * fence") is not part of this version.
 */
import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import IconButton from '@mui/material/IconButton';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import type { LocationType } from '@/api/types';
import type { PlanModel } from '../model/planModel';
import type { GardenObjectType, PlanOperation, Point } from '../model/types';
import type { RendererLabels } from '../renderer';
import type { SelectionRef } from '../state/gardenPlanSlice';
import {
  addWithDimensions,
  SHAPE_FIELDS,
  type DimensionTarget,
  type DimensionValues,
} from './tools/addDimensions';
import type { DrawShape } from './tools/drawMachine';
import { OBJECT_TYPES } from './tools/objectTypes';
import { parseDecimal } from './tools/panelFields';

const PREFIX = 'pages.gardenPlan.editor';

interface AddWithDimensionsDialogProps {
  open: boolean;
  plan: PlanModel;
  labels: RendererLabels;
  bedTypes: LocationType[];
  /** Bed type used while the list is not loaded: the plan's most common one. */
  fallbackBedTypeKey: string;
  /** The middle of the visible plan: where the new shape starts. */
  defaultPosition: Point;
  /** "Beet 4" for a blank name. */
  suggestedName: string;
  onAdd: (ops: PlanOperation[], selection: SelectionRef) => void;
  onClose: () => void;
}

interface Draft {
  target: DimensionTarget;
  bedTypeKey: string;
  objectType: GardenObjectType;
  shape: DrawShape;
  name: string;
  x: string;
  y: string;
  width: string;
  length: string;
  radius: string;
  rotation: string;
  strokeWidth: string;
  points: { x: string; y: string }[];
}

const num = (text: string): number | null => parseDecimal(text);

function initialDraft(defaultPosition: Point, bedTypeKey: string): Draft {
  return {
    target: 'bed',
    bedTypeKey,
    objectType: 'other',
    shape: 'rect',
    name: '',
    x: String(Math.round(defaultPosition[0] * 100) / 100),
    y: String(Math.round(defaultPosition[1] * 100) / 100),
    width: '2',
    length: '1',
    radius: '1',
    rotation: '0',
    strokeWidth: '0.3',
    points: [
      { x: '', y: '' },
      { x: '', y: '' },
      { x: '', y: '' },
    ],
  };
}

function valuesOf(draft: Draft): DimensionValues {
  return {
    target: draft.target,
    bedTypeKey: draft.bedTypeKey,
    objectType: draft.objectType,
    name: draft.name,
    shape: draft.shape,
    x: num(draft.x),
    y: num(draft.y),
    width: num(draft.width),
    length: num(draft.length),
    radius: num(draft.radius),
    rotation: num(draft.rotation),
    strokeWidth: num(draft.strokeWidth),
    points: draft.points.map((p): Point | null => {
      const x = num(p.x);
      const y = num(p.y);
      return x === null || y === null ? null : [x, y];
    }),
  };
}

function DimensionsForm({
  plan,
  labels,
  bedTypes,
  fallbackBedTypeKey,
  defaultPosition,
  suggestedName,
  onAdd,
  onClose,
}: Omit<AddWithDimensionsDialogProps, 'open'>) {
  const { t } = useTranslation();
  const [draft, setDraft] = useState<Draft>(() =>
    initialDraft(defaultPosition, bedTypes[0]?.key ?? fallbackBedTypeKey),
  );
  const [error, setError] = useState<string | null>(null);
  const set = <K extends keyof Draft>(key: K, value: Draft[K]) => {
    setDraft((previous) => ({ ...previous, [key]: value }));
    setError(null);
  };
  const fields = SHAPE_FIELDS[draft.shape];
  const shapes: DrawShape[] =
    draft.target === 'garden_object'
      ? ['rect', 'circle', 'polygon', 'polyline']
      : ['rect', 'circle', 'polygon'];
  // The type list of a bed arrives with the request; until then the draft keeps the first known key.
  const bedKey = bedTypes.some((type) => type.key === draft.bedTypeKey)
    ? draft.bedTypeKey
    : (bedTypes[0]?.key ?? draft.bedTypeKey);

  const numberField = (
    id: 'x' | 'y' | 'width' | 'length' | 'radius' | 'rotation' | 'strokeWidth',
    unit: string,
  ) =>
    fields.includes(id) ? (
      <TextField
        key={id}
        size="small"
        label={t(`${PREFIX}.addWithDimensions.fields.${id}`)}
        value={draft[id]}
        onChange={(event) => set(id, event.target.value)}
        required={id !== 'rotation' && id !== 'strokeWidth'}
        error={draft[id] !== '' && num(draft[id]) === null}
        helperText={
          draft[id] !== '' && num(draft[id]) === null
            ? t(`${PREFIX}.addWithDimensions.fieldInvalid`)
            : undefined
        }
        slotProps={{
          htmlInput: { inputMode: 'decimal', 'data-testid': `garden-plan-add-${id}` },
          input: { endAdornment: unit },
        }}
        sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
      />
    ) : null;

  const submit = () => {
    const outcome = addWithDimensions(
      plan,
      { ...valuesOf(draft), bedTypeKey: bedKey },
      suggestedName,
    );
    if (!outcome.ok) {
      setError(outcome.code);
      return;
    }
    onAdd(outcome.ops, outcome.selection);
  };

  return (
    <Box
      component="form"
      noValidate
      onSubmit={(event: FormEvent) => {
        event.preventDefault(); // Enter in a field adds the shape, like the button
        submit();
      }}
      sx={{ display: 'flex', flexDirection: 'column', flex: '1 1 auto', minHeight: 0 }}
    >
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {t(`${PREFIX}.addWithDimensions.intro`)}
          </Typography>
          <ToggleButtonGroup
            exclusive
            fullWidth
            size="small"
            value={draft.target}
            aria-label={t(`${PREFIX}.addWithDimensions.kind`)}
            onChange={(_event, next: DimensionTarget | null) => {
              if (!next) return;
              setDraft((previous) => ({
                ...previous,
                target: next,
                shape: next === 'bed' && previous.shape === 'polyline' ? 'rect' : previous.shape,
              }));
              setError(null);
            }}
          >
            <ToggleButton value="bed" sx={{ minHeight: 48 }} data-testid="garden-plan-add-kind-bed">
              {t(`${PREFIX}.addWithDimensions.bed`)}
            </ToggleButton>
            <ToggleButton
              value="garden_object"
              sx={{ minHeight: 48 }}
              data-testid="garden-plan-add-kind-object"
            >
              {t(`${PREFIX}.addWithDimensions.object`)}
            </ToggleButton>
          </ToggleButtonGroup>

          {draft.target === 'bed' ? (
            <TextField
              select
              size="small"
              label={t(`${PREFIX}.addWithDimensions.bedType`)}
              value={bedKey}
              onChange={(event) => set('bedTypeKey', event.target.value)}
              slotProps={{ htmlInput: { 'data-testid': 'garden-plan-add-bed-type' } }}
              sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
            >
              {(bedTypes.length > 0
                ? bedTypes
                : [{ key: bedKey, name: bedKey } as LocationType]
              ).map((type) => (
                <MenuItem key={type.key} value={type.key} sx={{ minHeight: 48 }}>
                  {type.name}
                </MenuItem>
              ))}
            </TextField>
          ) : (
            <TextField
              select
              size="small"
              label={t(`${PREFIX}.addWithDimensions.objectType`)}
              value={draft.objectType}
              onChange={(event) => set('objectType', event.target.value as GardenObjectType)}
              slotProps={{ htmlInput: { 'data-testid': 'garden-plan-add-object-type' } }}
              sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
            >
              {OBJECT_TYPES.map((type) => (
                <MenuItem key={type} value={type} sx={{ minHeight: 48 }}>
                  {labels.objectType(type)}
                </MenuItem>
              ))}
            </TextField>
          )}

          <TextField
            size="small"
            label={t(`${PREFIX}.addWithDimensions.name`)}
            value={draft.name}
            onChange={(event) => set('name', event.target.value)}
            placeholder={suggestedName}
            helperText={t(`${PREFIX}.addWithDimensions.nameHelper`)}
            slotProps={{ htmlInput: { 'data-testid': 'garden-plan-add-name' } }}
            sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
          />

          <ToggleButtonGroup
            exclusive
            size="small"
            value={draft.shape}
            aria-label={t(`${PREFIX}.toolbar.shapes`)}
            onChange={(_event, next: DrawShape | null) => next && set('shape', next)}
          >
            {shapes.map((shape) => (
              <ToggleButton
                key={shape}
                value={shape}
                sx={{ minHeight: 48, px: 1.5 }}
                data-testid={`garden-plan-add-shape-${shape}`}
              >
                {t(`${PREFIX}.shapes.${shape}.label`)}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>

          {fields.includes('points') ? (
            <Typography variant="body2" color="text.secondary">
              {t(`${PREFIX}.addWithDimensions.pointsHint`)}
            </Typography>
          ) : (
            <Typography variant="body2" color="text.secondary">
              {t(`${PREFIX}.addWithDimensions.positionHint`)}
            </Typography>
          )}
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 1.5 }}>
            {numberField('x', 'm')}
            {numberField('y', 'm')}
            {numberField('width', 'm')}
            {numberField('length', 'm')}
            {numberField('radius', 'm')}
            {numberField('rotation', '°')}
            {numberField('strokeWidth', 'm')}
          </Box>

          {fields.includes('points') && (
            <Stack spacing={1} data-testid="garden-plan-add-points">
              {draft.points.map((point, index) => (
                <Box key={index} sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
                  {(['x', 'y'] as const).map((axis) => (
                    <TextField
                      key={axis}
                      size="small"
                      label={`${index + 1} · ${axis === 'x' ? 'x →' : 'y ↑'}`}
                      value={point[axis]}
                      onChange={(event) =>
                        set(
                          'points',
                          draft.points.map((p, i) =>
                            i === index ? { ...p, [axis]: event.target.value } : p,
                          ),
                        )
                      }
                      error={point[axis] !== '' && num(point[axis]) === null}
                      slotProps={{
                        htmlInput: {
                          inputMode: 'decimal',
                          'data-testid': `garden-plan-add-point-${index}-${axis}`,
                        },
                        input: { endAdornment: 'm' },
                      }}
                      sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
                    />
                  ))}
                  <IconButton
                    aria-label={t(`${PREFIX}.panel.deletePoint`, { n: index + 1 })}
                    disabled={draft.points.length <= (draft.shape === 'polygon' ? 3 : 2)}
                    onClick={() =>
                      set(
                        'points',
                        draft.points.filter((_, i) => i !== index),
                      )
                    }
                    sx={{ width: 48, height: 48 }}
                  >
                    <DeleteOutlinedIcon />
                  </IconButton>
                </Box>
              ))}
              <Button
                size="small"
                onClick={() => set('points', [...draft.points, { x: '', y: '' }])}
                disabled={draft.points.length >= 200}
                sx={{ minHeight: 48, alignSelf: 'flex-start' }}
                data-testid="garden-plan-add-point"
              >
                {t(`${PREFIX}.addWithDimensions.addPoint`)}
              </Button>
            </Stack>
          )}

          {error && (
            <Alert severity="error" data-testid="garden-plan-add-error">
              {t(`${PREFIX}.notice.${error}`, { defaultValue: t(`${PREFIX}.notice.generic`) })}
            </Alert>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} sx={{ minHeight: 48 }} data-testid="garden-plan-add-cancel">
          {t(`${PREFIX}.draw.cancel`)}
        </Button>
        <Button
          variant="contained"
          type="submit"
          sx={{ minHeight: 48 }}
          data-testid="garden-plan-add-submit"
        >
          {t(`${PREFIX}.addWithDimensions.submit`)}
        </Button>
      </DialogActions>
    </Box>
  );
}

export function AddWithDimensionsDialog(props: AddWithDimensionsDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { open, ...rest } = props;
  return (
    <Dialog
      open={open}
      onClose={props.onClose}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      aria-labelledby="garden-plan-add-title"
      data-testid="garden-plan-add-dialog"
    >
      <DialogTitle id="garden-plan-add-title">{t(`${PREFIX}.addWithDimensions.title`)}</DialogTitle>
      {/* Mounted only while open: every opening starts from a fresh draft at the current view. */}
      {open && <DimensionsForm {...rest} />}
    </Dialog>
  );
}
