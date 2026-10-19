/**
 * "Correct position" (REQ-053 GP-FR-068, GP-ACC-022): one plant's slot gets a new geometry. Drag the
 * marker on the bed or - the default in the field (F-13) - move it with the stepper buttons or type the
 * coordinates. The server logs `care_event(position_corrected)` with the plant; nothing here writes it.
 * A plant in a zone has no single position and cannot be moved (the panel says so).
 */
import { useCallback, useEffect, useMemo, useState, type ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { useApiError } from '@/hooks/useApiError';
import type { Geometry, Point } from '../model/types';
import LayoutCanvas from './LayoutCanvas';
import { correctSlotPosition, getSlot, listBedSlots } from './plantingApi';
import { insideBed } from './plantingLogic';

/** Stepper step in centimetres; the long press of the field uses the larger one. */
export const STEP_CM = 1;
export const BIG_STEP_CM = 5;
const CM = 100;

interface PositionCorrectionDialogProps {
  bedName: string;
  bedGeometry: Geometry;
  bedKey: string;
  slotKey: string;
  /** Instance id of the plant, for the title. */
  plantLabel: string;
  onClose: () => void;
  onCorrected: () => void;
  /** Stepper step in cm; field mode moves by 10 cm (§18.1 step 9, F-16). */
  stepCm?: number;
  /** Edge of the stepper and action buttons in px; field mode passes the kiosk target (64 px, GP-UX-020). */
  touchTarget?: number;
  /** Hold time before the marker can be dragged; field mode needs a 500 ms long press (GP-UX-023). */
  dragHoldMs?: number;
  /**
   * Offer the ±{@link BIG_STEP_CM} cm buttons next to the stepper. Field mode turns them off: its 10 cm
   * step is already coarser (§18.1 step 9).
   */
  showBigSteps?: boolean;
}

type Loaded =
  | { status: 'loading' }
  | { status: 'zone' }
  | { status: 'error' }
  | { status: 'ready'; origin: Point };

function cmText(value: number): string {
  return String(Math.round(value * CM * 10) / 10);
}

export default function PositionCorrectionDialog({
  bedName,
  bedGeometry,
  bedKey,
  slotKey,
  plantLabel,
  onClose,
  onCorrected,
  stepCm = STEP_CM,
  touchTarget = 48,
  dragHoldMs,
  showBigSteps = true,
}: PositionCorrectionDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { handleError } = useApiError();
  const [loaded, setLoaded] = useState<Loaded>({ status: 'loading' });
  const [others, setOthers] = useState<Point[]>([]);
  const [xText, setXText] = useState('');
  const [yText, setYText] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getSlot(slotKey), listBedSlots(bedKey).catch(() => [])])
      .then(([slot, slots]) => {
        if (cancelled) return;
        if (slot.geometry?.kind === 'point') {
          setLoaded({ status: 'ready', origin: slot.geometry.origin });
          setXText(cmText(slot.geometry.origin[0]));
          setYText(cmText(slot.geometry.origin[1]));
          setOthers(
            slots.flatMap((other) =>
              other.key !== slotKey && !other.archived_at && other.geometry?.kind === 'point'
                ? [other.geometry.origin]
                : [],
            ),
          );
        } else {
          setLoaded({ status: 'zone' });
        }
      })
      .catch(() => {
        if (!cancelled) setLoaded({ status: 'error' });
      });
    return () => {
      cancelled = true;
    };
  }, [slotKey, bedKey]);

  // The two fields are the truth: what they say is what is saved. A text that is not a number has no position.
  const parsed = useMemo<Point | null>(() => {
    const x = Number(xText.trim().replace(',', '.'));
    const y = Number(yText.trim().replace(',', '.'));
    return xText.trim() !== '' && yText.trim() !== '' && Number.isFinite(x) && Number.isFinite(y)
      ? [x / CM, y / CM]
      : null;
  }, [xText, yText]);
  const inside = parsed !== null && insideBed(bedGeometry, parsed);
  const shown: Point | null = parsed ?? (loaded.status === 'ready' ? loaded.origin : null);

  const moveTo = useCallback((next: Point) => {
    setXText(cmText(next[0]));
    setYText(cmText(next[1]));
  }, []);

  const step = (dxCm: number, dyCm: number) => {
    if (!shown) return;
    moveTo([Math.round((shown[0] + dxCm / CM) * CM) / CM, Math.round((shown[1] + dyCm / CM) * CM) / CM]);
  };

  const changed =
    loaded.status === 'ready' &&
    parsed !== null &&
    inside &&
    (Math.abs(parsed[0] - loaded.origin[0]) > 1e-9 || Math.abs(parsed[1] - loaded.origin[1]) > 1e-9);
  const layers = useMemo(
    () => (shown ? [{ id: 'plant', shape: 'circle' as const, color: theme.palette.success.dark, positions: [shown] }] : []),
    [shown, theme],
  );

  const save = async () => {
    if (!parsed || !changed) return;
    setSaving(true);
    try {
      await correctSlotPosition(slotKey, { kind: 'point', origin: [Math.round(parsed[0] * CM) / CM, Math.round(parsed[1] * CM) / CM] });
      onCorrected();
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  };

  const stepButton = (label: string, dx: number, dy: number, icon: ReactElement, testId: string) => (
    <IconButton
      aria-label={label}
      onClick={() => step(dx, dy)}
      sx={{ width: touchTarget, height: touchTarget, border: 1, borderColor: 'divider' }}
      data-testid={testId}
    >
      {icon}
    </IconButton>
  );

  return (
    <Dialog
      open
      onClose={saving ? undefined : onClose}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      aria-labelledby="position-dialog-title"
      data-testid="position-dialog"
    >
      <DialogTitle id="position-dialog-title">{t('pages.bed.planting.position.title', { plant: plantLabel })}</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        {loaded.status === 'loading' ? <LoadingSkeleton variant="card" /> : null}
        {loaded.status === 'zone' ? (
          <Alert severity="info" data-testid="position-zone-note">
            {t('pages.bed.planting.position.zone')}
          </Alert>
        ) : null}
        {loaded.status === 'error' ? <Alert severity="error">{t('pages.bed.planting.position.failed')}</Alert> : null}
        {loaded.status === 'ready' && shown ? (
          <>
            <Typography variant="body2" color="text.secondary">
              {t('pages.bed.planting.position.help')}
            </Typography>
            <LayoutCanvas
              bed={bedGeometry}
              layers={layers}
              existing={others}
              label={t('pages.bed.planting.position.canvasLabel', { bed: bedName })}
              interactiveLayerId="plant"
              selected={{ layerId: 'plant', index: 0 }}
              onMove={(_, __, next) => moveTo(next)}
              dragHoldMs={dragHoldMs}
              testId="position-canvas"
            />
            <Box
              sx={{ display: 'grid', gridTemplateColumns: `repeat(3, ${touchTarget}px)`, gap: 1, justifyContent: 'center' }}
              role="group"
              aria-label={t('pages.bed.planting.position.stepper')}
            >
              <span />
              {stepButton(t('pages.bed.planting.position.up'), 0, stepCm, <ArrowUpwardIcon />, 'position-up')}
              <span />
              {stepButton(t('pages.bed.planting.position.left'), -stepCm, 0, <ArrowBackIcon />, 'position-left')}
              <Typography variant="caption" color="text.secondary" sx={{ alignSelf: 'center', textAlign: 'center' }} aria-hidden="true">
                {stepCm} cm
              </Typography>
              {stepButton(t('pages.bed.planting.position.right'), stepCm, 0, <ArrowForwardIcon />, 'position-right')}
              <span />
              {stepButton(t('pages.bed.planting.position.down'), 0, -stepCm, <ArrowDownwardIcon />, 'position-down')}
              <span />
            </Box>
            {showBigSteps && (
              <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                <Button
                  onClick={() => step(-BIG_STEP_CM, 0)}
                  sx={{ minHeight: touchTarget }}
                  aria-label={t('pages.bed.planting.position.bigLeft', { cm: BIG_STEP_CM })}
                  data-testid="position-big-left"
                >
                  −{BIG_STEP_CM} cm ←
                </Button>
                <Button
                  onClick={() => step(BIG_STEP_CM, 0)}
                  sx={{ minHeight: touchTarget }}
                  aria-label={t('pages.bed.planting.position.bigRight', { cm: BIG_STEP_CM })}
                  data-testid="position-big-right"
                >
                  → +{BIG_STEP_CM} cm
                </Button>
              </Box>
            )}
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                label={t('pages.bed.planting.position.x')}
                value={xText}
                onChange={(event) => setXText(event.target.value)}
                error={parsed === null}
                helperText={parsed === null ? t('pages.bed.planting.position.invalid') : undefined}
                slotProps={{
                  input: { endAdornment: <InputAdornment position="end">cm</InputAdornment> },
                  htmlInput: { inputMode: 'decimal', 'data-testid': 'position-x' },
                }}
                sx={{ flex: 1 }}
              />
              <TextField
                label={t('pages.bed.planting.position.y')}
                value={yText}
                onChange={(event) => setYText(event.target.value)}
                error={parsed === null}
                slotProps={{
                  input: { endAdornment: <InputAdornment position="end">cm</InputAdornment> },
                  htmlInput: { inputMode: 'decimal', 'data-testid': 'position-y' },
                }}
                sx={{ flex: 1 }}
              />
            </Box>
            {parsed !== null && !inside ? (
              <Alert severity="warning" data-testid="position-outside">
                {t('pages.bed.planting.position.outside')}
              </Alert>
            ) : null}
          </>
        ) : null}
      </DialogContent>
      <DialogActions sx={{ px: { xs: 2, sm: 3 }, pb: 2 }}>
        <Button onClick={onClose} disabled={saving} sx={{ minHeight: touchTarget }}>
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={() => void save()}
          disabled={saving || !changed}
          sx={{ minHeight: touchTarget, minWidth: touchTarget }}
          data-testid="position-save"
        >
          {t('pages.bed.planting.position.save')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
