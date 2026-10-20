/**
 * The underlay dialog (REQ-053 GP-FR-033, WP 7.15): choose a picture (photo, sketch, aerial view), mark two points of
 * it and state the real distance between them (the scale), place it on the plan (move, turn) and set its opacity.
 * The picture is background to trace over - presentation only, never exported, printed only on request.
 *
 * This module is its own `lazy()` chunk (UI-NFR-003): the route chunk carries only the switch that mounts it.
 * Marking points is a click on the picture; the same four numbers are fields, so the whole calibration works
 * without a pointer too (WCAG 2.1.1, 2.5.1).
 */
import {
  memo,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type MouseEvent,
} from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Slider from '@mui/material/Slider';
import TextField from '@mui/material/TextField';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Typography from '@mui/material/Typography';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { isApiError } from '@/api/errors';
import { useNotification } from '@/hooks/useNotification';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import type { PlanUnderlay } from '../model/types';
import {
  MAX_DISTANCE_M,
  MIN_OPACITY,
  clampOpacity,
  pixelsPerMetre,
  toImagePoint,
  type Point,
} from './calibration';
import { deleteUnderlay, fetchUnderlayBlob, putUnderlay, uploadUnderlayImage } from './underlayApi';

const PREFIX = 'pages.gardenPlan.editor.underlay';
const MARK_PX = 8;
const TARGET_PX = 44;

export interface UnderlayDialogProps {
  open: boolean;
  siteKey: string;
  /** The stored underlay of the site, or `null` for none yet. */
  underlay: PlanUnderlay | null;
  /** The server accepted a change: the new underlay, or `null` after a removal. */
  onSaved: (next: PlanUnderlay | null) => void;
  onClose: () => void;
}

type Which = 'p1' | 'p2';

function numberOf(text: string): number {
  return text.trim() === '' ? Number.NaN : Number(text.replace(',', '.'));
}

function errorKey(failure: unknown): string {
  if (!isApiError(failure)) return 'generic';
  if (failure.statusCode === 403) return 'forbidden';
  if (failure.statusCode === 413) return 'tooLarge';
  if (failure.statusCode === 415 || failure.errorCode === 'INVALID_FILE_TYPE') return 'wrongType';
  if (failure.statusCode === 429) return 'rateLimited';
  if (failure.errorCode === 'plan.required') return 'planRequired';
  if (failure.statusCode === 422) return 'invalid';
  return 'generic';
}

interface NumberFieldProps {
  id: string;
  value: string;
  onChange: (next: string) => void;
  label: string;
  unit: string;
  disabled: boolean;
  error?: boolean;
}

/**
 * One numeric field of the dialog. Memoised on primitives only, so a keystroke re-renders the one field it
 * belongs to and not the eleven of the dialog (the dialog's tests under coverage instrumentation were the first
 * to show what that costs; the user pays it on a phone as well).
 */
const NumberField = memo(function NumberField({
  id,
  value,
  onChange,
  label,
  unit,
  disabled,
  error,
}: NumberFieldProps) {
  return (
    <TextField
      id={`underlay-${id}`}
      label={label}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      size="small"
      disabled={disabled}
      error={error}
      slotProps={{
        htmlInput: { inputMode: 'decimal', 'data-testid': `underlay-${id}` },
        input: { endAdornment: <Typography variant="caption">{unit}</Typography> },
      }}
      sx={{ minWidth: 110 }}
    />
  );
});

const text = (value: number): string => (Number.isFinite(value) ? String(value) : '');

export default function UnderlayDialog({
  open,
  siteKey,
  underlay,
  onSaved,
  onClose,
}: UnderlayDialogProps) {
  const { t } = useTranslation();
  // Grower and above write; a viewer sees the calibration read-only (the backend decides as well).
  const { canEdit } = useTenantPermissions();
  const notify = useNotification();
  const stored = underlay;
  const [file, setFile] = useState<File | null>(null);
  const [href, setHref] = useState<string | null>(null);
  const [natural, setNatural] = useState<{ width: number; height: number } | null>(null);
  const [p1x, setP1x] = useState(text(stored?.calibration.p1_px[0] ?? Number.NaN));
  const [p1y, setP1y] = useState(text(stored?.calibration.p1_px[1] ?? Number.NaN));
  const [p2x, setP2x] = useState(text(stored?.calibration.p2_px[0] ?? Number.NaN));
  const [p2y, setP2y] = useState(text(stored?.calibration.p2_px[1] ?? Number.NaN));
  const [distance, setDistance] = useState(text(stored?.calibration.distance_m ?? Number.NaN));
  const [originX, setOriginX] = useState(text(stored?.origin[0] ?? 0));
  const [originY, setOriginY] = useState(text(stored?.origin[1] ?? 0));
  const [rotation, setRotation] = useState(text(stored?.rotation_deg ?? 0));
  const [opacity, setOpacity] = useState(stored?.opacity ?? 0.5);
  const [marking, setMarking] = useState<Which>('p1');
  const [busy, setBusy] = useState(false);
  const [confirmRemove, setConfirmRemove] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);

  // The stored picture, read through the authenticated client; a picked file replaces it (local object URL).
  const attachmentKey = stored?.attachment_key ?? null;
  useEffect(() => {
    if (!open || file !== null || attachmentKey === null) return undefined;
    const abort = new AbortController();
    let url: string | null = null;
    fetchUnderlayBlob(attachmentKey, abort.signal)
      .then((blob) => {
        if (abort.signal.aborted) return;
        url = URL.createObjectURL(blob);
        setHref(url);
      })
      .catch(() => {
        if (!abort.signal.aborted) setError('loadFailed');
      });
    return () => {
      abort.abort();
      if (url !== null) URL.revokeObjectURL(url);
    };
  }, [open, file, attachmentKey]);

  useEffect(() => {
    if (file === null) return undefined;
    const url = URL.createObjectURL(file);
    // eslint-disable-next-line react-hooks/set-state-in-effect -- the object URL is an external resource tied to the file
    setHref(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const calibration = useMemo(() => {
    const p1: Point = [numberOf(p1x), numberOf(p1y)];
    const p2: Point = [numberOf(p2x), numberOf(p2y)];
    return { p1, p2, distance: numberOf(distance) };
  }, [p1x, p1y, p2x, p2y, distance]);
  const perMetre = pixelsPerMetre({
    p1_px: calibration.p1,
    p2_px: calibration.p2,
    distance_m: calibration.distance,
  });
  const originNumbers: [number, number] = [numberOf(originX), numberOf(originY)];
  const rotationNumber = numberOf(rotation);
  const pointsInside =
    natural === null ||
    ([...calibration.p1, ...calibration.p2].every(
      (value) => Number.isFinite(value) && value >= 0,
    ) &&
      calibration.p1[0] <= natural.width &&
      calibration.p2[0] <= natural.width &&
      calibration.p1[1] <= natural.height &&
      calibration.p2[1] <= natural.height);
  const placementValid =
    originNumbers.every((value) => Number.isFinite(value) && Math.abs(value) <= 1000) &&
    Number.isFinite(rotationNumber) &&
    Math.abs(rotationNumber) <= 360;
  const hasPicture = file !== null || attachmentKey !== null;
  const fieldsOff = !canEdit || busy;
  const valid = hasPicture && perMetre !== null && pointsInside && placementValid;

  const pick = (event: ChangeEvent<HTMLInputElement>) => {
    const picked = event.target.files?.[0] ?? null;
    if (picked === null) return;
    setError(null);
    setNatural(null);
    setFile(picked);
    // A new picture has no calibration of its own: the old points would be pixels of another image.
    for (const reset of [setP1x, setP1y, setP2x, setP2y, setDistance]) reset('');
    setMarking('p1');
  };

  const mark = (event: MouseEvent<HTMLDivElement>) => {
    if (!canEdit || natural === null || imageRef.current === null) return;
    const point = toImagePoint(
      [event.clientX, event.clientY],
      imageRef.current.getBoundingClientRect(),
      natural,
    );
    if (point === null) return;
    if (marking === 'p1') {
      setP1x(String(point[0]));
      setP1y(String(point[1]));
      setMarking('p2');
    } else {
      setP2x(String(point[0]));
      setP2y(String(point[1]));
    }
  };

  const save = async () => {
    if (!valid || busy || !canEdit) return;
    setBusy(true);
    setError(null);
    try {
      const key = file !== null ? await uploadUnderlayImage(file) : attachmentKey;
      if (key === null) return;
      const saved = await putUnderlay(siteKey, {
        attachment_key: key,
        calibration: {
          p1_px: [calibration.p1[0], calibration.p1[1]],
          p2_px: [calibration.p2[0], calibration.p2[1]],
          distance_m: calibration.distance,
        },
        origin: originNumbers,
        rotation_deg: rotationNumber,
        opacity,
      });
      notify.success(t(`${PREFIX}.saved`));
      onSaved(saved);
      onClose();
    } catch (failure) {
      setError(errorKey(failure));
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (busy || !canEdit) return;
    setConfirmRemove(false);
    setBusy(true);
    setError(null);
    try {
      await deleteUnderlay(siteKey);
      notify.success(t(`${PREFIX}.removed`));
      onSaved(null);
      onClose();
    } catch (failure) {
      setError(errorKey(failure));
    } finally {
      setBusy(false);
    }
  };

  const markers: { which: Which; point: Point }[] = [
    { which: 'p1', point: calibration.p1 },
    { which: 'p2', point: calibration.p2 },
  ];
  return (
    <>
      <Dialog
        open={open}
        onClose={busy ? undefined : onClose}
        maxWidth="md"
        fullWidth
        aria-labelledby="underlay-title"
        data-testid="garden-plan-underlay-dialog"
      >
        <DialogTitle id="underlay-title">{t(`${PREFIX}.title`)}</DialogTitle>
        <DialogContent dividers sx={{ display: 'grid', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {t(`${PREFIX}.intro`)}
          </Typography>
          {error !== null && (
            <Alert severity="error" role="alert" data-testid="underlay-error">
              {t(`${PREFIX}.error.${error}`)}
            </Alert>
          )}
          {canEdit && (
            <Box>
              <Button
                component="label"
                variant="outlined"
                sx={{ minHeight: TARGET_PX }}
                disabled={busy}
              >
                {t(`${PREFIX}.choose`)}
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  hidden
                  onChange={pick}
                  data-testid="underlay-file"
                />
              </Button>
              {file !== null && (
                <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                  {file.name}
                </Typography>
              )}
            </Box>
          )}
          {href !== null && (
            <>
              {canEdit && (
                <ToggleButtonGroup
                  exclusive
                  size="small"
                  value={marking}
                  aria-label={t(`${PREFIX}.marking.label`)}
                  onChange={(_event, next: Which | null) => {
                    if (next) setMarking(next);
                  }}
                >
                  <ToggleButton
                    value="p1"
                    sx={{ minHeight: TARGET_PX }}
                    data-testid="underlay-mark-p1"
                  >
                    {t(`${PREFIX}.marking.p1`)}
                  </ToggleButton>
                  <ToggleButton
                    value="p2"
                    sx={{ minHeight: TARGET_PX }}
                    data-testid="underlay-mark-p2"
                  >
                    {t(`${PREFIX}.marking.p2`)}
                  </ToggleButton>
                </ToggleButtonGroup>
              )}
              <Box
                onClick={mark}
                data-testid="underlay-picture"
                sx={{
                  position: 'relative',
                  maxHeight: 420,
                  overflow: 'auto',
                  cursor: canEdit ? 'crosshair' : 'default',
                }}
              >
                <img
                  ref={imageRef}
                  src={href}
                  alt={t(`${PREFIX}.pictureAlt`)}
                  onLoad={(event) =>
                    setNatural({
                      width: event.currentTarget.naturalWidth,
                      height: event.currentTarget.naturalHeight,
                    })
                  }
                  style={{ display: 'block', width: '100%', height: 'auto' }}
                />
                {natural !== null && (
                  <svg
                    viewBox={`0 0 ${natural.width} ${natural.height}`}
                    aria-hidden="true"
                    style={{
                      position: 'absolute',
                      inset: 0,
                      width: '100%',
                      height: '100%',
                      pointerEvents: 'none',
                    }}
                  >
                    {markers.map(({ which, point }) =>
                      Number.isFinite(point[0]) && Number.isFinite(point[1]) ? (
                        <circle
                          key={which}
                          cx={point[0]}
                          cy={point[1]}
                          r={(MARK_PX * natural.width) / 800}
                          fill={which === 'p1' ? '#d32f2f' : '#1565c0'}
                          stroke="#fff"
                          strokeWidth={(2 * natural.width) / 800}
                        />
                      ) : null,
                    )}
                  </svg>
                )}
              </Box>
            </>
          )}
          <Box
            component="fieldset"
            sx={{ border: 0, p: 0, m: 0, display: 'flex', flexWrap: 'wrap', gap: 1 }}
          >
            <Typography component="legend" variant="subtitle2" sx={{ width: '100%', mb: 1 }}>
              {t(`${PREFIX}.calibration.title`)}
            </Typography>
            <NumberField
              id="p1x"
              value={p1x}
              onChange={setP1x}
              label={t(`${PREFIX}.calibration.p1x`)}
              unit="px"
              disabled={fieldsOff}
            />
            <NumberField
              id="p1y"
              value={p1y}
              onChange={setP1y}
              label={t(`${PREFIX}.calibration.p1y`)}
              unit="px"
              disabled={fieldsOff}
            />
            <NumberField
              id="p2x"
              value={p2x}
              onChange={setP2x}
              label={t(`${PREFIX}.calibration.p2x`)}
              unit="px"
              disabled={fieldsOff}
            />
            <NumberField
              id="p2y"
              value={p2y}
              onChange={setP2y}
              label={t(`${PREFIX}.calibration.p2y`)}
              unit="px"
              disabled={fieldsOff}
            />
            <NumberField
              id="distance"
              value={distance}
              onChange={setDistance}
              label={t(`${PREFIX}.calibration.distance`)}
              unit="m"
              disabled={fieldsOff}
              error={
                distance.trim() !== '' &&
                (!Number.isFinite(calibration.distance) ||
                  calibration.distance <= 0 ||
                  calibration.distance > MAX_DISTANCE_M)
              }
            />
          </Box>
          <Typography variant="body2" role="status" data-testid="underlay-scale">
            {perMetre !== null
              ? t(`${PREFIX}.calibration.scale`, { pxPerM: Number(perMetre.toFixed(2)) })
              : t(`${PREFIX}.calibration.scaleMissing`)}
          </Typography>
          {!pointsInside && (
            <Alert severity="warning" role="status">
              {t(`${PREFIX}.calibration.outside`)}
            </Alert>
          )}
          <Box
            component="fieldset"
            sx={{ border: 0, p: 0, m: 0, display: 'flex', flexWrap: 'wrap', gap: 1 }}
          >
            <Typography component="legend" variant="subtitle2" sx={{ width: '100%', mb: 1 }}>
              {t(`${PREFIX}.placement.title`)}
            </Typography>
            <NumberField
              id="originX"
              value={originX}
              onChange={setOriginX}
              label={t(`${PREFIX}.placement.originX`)}
              unit="m"
              disabled={fieldsOff}
            />
            <NumberField
              id="originY"
              value={originY}
              onChange={setOriginY}
              label={t(`${PREFIX}.placement.originY`)}
              unit="m"
              disabled={fieldsOff}
            />
            <NumberField
              id="rotation"
              value={rotation}
              onChange={setRotation}
              label={t(`${PREFIX}.placement.rotation`)}
              unit="°"
              disabled={fieldsOff}
            />
          </Box>
          <Box sx={{ maxWidth: 360 }}>
            <Typography id="underlay-opacity-label" variant="body2">
              {t(`${PREFIX}.opacity`)}
            </Typography>
            <Slider
              value={opacity}
              min={MIN_OPACITY}
              max={1}
              step={0.05}
              onChange={(_event, next) =>
                setOpacity(clampOpacity(Array.isArray(next) ? next[0] : next))
              }
              aria-labelledby="underlay-opacity-label"
              valueLabelDisplay="auto"
              valueLabelFormat={(value) => `${Math.round(value * 100)} %`}
              disabled={!canEdit || busy}
              data-testid="underlay-opacity"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          {canEdit && stored !== null && (
            <Button
              color="error"
              onClick={() => setConfirmRemove(true)}
              disabled={busy}
              sx={{ minHeight: TARGET_PX, mr: 'auto' }}
              data-testid="underlay-remove"
            >
              {t(`${PREFIX}.remove`)}
            </Button>
          )}
          <Button onClick={onClose} disabled={busy} sx={{ minHeight: TARGET_PX }}>
            {t(`${PREFIX}.close`)}
          </Button>
          {canEdit && (
            <Button
              variant="contained"
              onClick={() => void save()}
              disabled={!valid || busy}
              sx={{ minHeight: TARGET_PX }}
              data-testid="underlay-save"
            >
              {t(`${PREFIX}.save`)}
            </Button>
          )}
        </DialogActions>
      </Dialog>
      <ConfirmDialog
        open={confirmRemove}
        title={t(`${PREFIX}.removeConfirm.title`)}
        message={t(`${PREFIX}.removeConfirm.message`)}
        confirmLabel={t(`${PREFIX}.remove`)}
        destructive
        loading={busy}
        onConfirm={() => void remove()}
        onCancel={() => setConfirmRemove(false)}
      />
    </>
  );
}
