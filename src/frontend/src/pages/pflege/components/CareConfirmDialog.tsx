import { useState, useCallback, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import Alert from '@mui/material/Alert';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import CircularProgress from '@mui/material/CircularProgress';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchFertilizers } from '@/store/slices/fertilizersSlice';
import type { ReminderType, Fertilizer } from '@/api/types';
import type { ConfirmFeedingDetail } from '@/api/endpoints/careReminders';

export interface DosagePreset {
  fertilizer_key: string;
  ml_per_liter: number;
}

interface CareConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (options: {
    notes?: string;
    volume_liters?: number;
    fertilizers_used?: ConfirmFeedingDetail[];
    measured_ec?: number;
    measured_ph?: number;
  }) => void;
  plantName: string;
  reminderType: ReminderType;
  loading?: boolean;
  defaultDosages?: DosagePreset[];
  defaultTargetEc?: number;
  defaultTargetPh?: number;
  phaseName?: string;
  /** Recommended watering volume in liters (pre-fills the volume field). */
  defaultVolumeLiters?: number;
  /** Human-readable explanation of how the volume was calculated. */
  volumeHint?: string;
  /** Pass fertilizers directly to avoid waiting for Redux store fetch. */
  availableFertilizers?: Fertilizer[];
}

interface FertilizerRow {
  fertilizer: Fertilizer | null;
  ml_applied: string;
}

const FEEDING_TYPES: ReminderType[] = ['watering', 'fertilizing'];

export default function CareConfirmDialog({
  open,
  onClose,
  onConfirm,
  plantName,
  reminderType,
  loading = false,
  defaultDosages,
  defaultTargetEc,
  defaultTargetPh,
  phaseName,
  defaultVolumeLiters,
  volumeHint,
  availableFertilizers,
}: CareConfirmDialogProps) {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const storeFertilizers = useAppSelector((s) => s.fertilizers.fertilizers);

  // Use prop fertilizers if provided, otherwise fall back to Redux store
  const fertilizers = availableFertilizers && availableFertilizers.length > 0
    ? availableFertilizers
    : storeFertilizers;

  const showFeedingSection = FEEDING_TYPES.includes(reminderType);
  const hasPresets = showFeedingSection && defaultDosages != null && defaultDosages.length > 0;
  const [feedingExpanded, setFeedingExpanded] = useState(false);
  const [notes, setNotes] = useState('');
  const [volumeLiters, setVolumeLiters] = useState('');
  const [measuredEc, setMeasuredEc] = useState('');
  const [measuredPh, setMeasuredPh] = useState('');
  const [fertilizerRows, setFertilizerRows] = useState<FertilizerRow[]>([]);
  const [presetsApplied, setPresetsApplied] = useState(false);

  // Fetch fertilizers from store if not provided via prop
  useEffect(() => {
    if (open && showFeedingSection && !availableFertilizers?.length && storeFertilizers.length === 0) {
      dispatch(fetchFertilizers({ offset: 0, limit: 200 }));
    }
  }, [open, showFeedingSection, availableFertilizers, storeFertilizers.length, dispatch]);

  // Apply presets from nutrient plan when dialog opens and fertilizers are available
  useEffect(() => {
    if (!open || presetsApplied || !hasPresets || fertilizers.length === 0) return;

    const rows: FertilizerRow[] = defaultDosages!.map((d) => {
      const fert = fertilizers.find((f) => f.key === d.fertilizer_key) ?? null;
      return { fertilizer: fert, ml_applied: String(d.ml_per_liter) };
    });

    if (rows.length > 0) {
      setFertilizerRows(rows);
      setFeedingExpanded(true);
      setPresetsApplied(true);
    }
  }, [open, presetsApplied, hasPresets, defaultDosages, fertilizers]);

  // Reset state when dialog closes; pre-fill volume when it opens
  useEffect(() => {
    if (!open) {
      setNotes('');
      setVolumeLiters('');
      setMeasuredEc('');
      setMeasuredPh('');
      setFertilizerRows([]);
      setFeedingExpanded(false);
      setPresetsApplied(false);
    } else if (defaultVolumeLiters != null) {
      setVolumeLiters(String(defaultVolumeLiters));
    }
  }, [open, defaultVolumeLiters]);

  const handleAddFertilizer = useCallback(() => {
    setFertilizerRows((prev) => [...prev, { fertilizer: null, ml_applied: '' }]);
  }, []);

  const handleRemoveFertilizer = useCallback((index: number) => {
    setFertilizerRows((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleFertilizerChange = useCallback((index: number, fertilizer: Fertilizer | null) => {
    setFertilizerRows((prev) =>
      prev.map((row, i) => (i === index ? { ...row, fertilizer } : row)),
    );
  }, []);

  const handleMlChange = useCallback((index: number, ml: string) => {
    setFertilizerRows((prev) =>
      prev.map((row, i) => (i === index ? { ...row, ml_applied: ml } : row)),
    );
  }, []);

  const handleSubmit = useCallback(() => {
    const vol = volumeLiters ? parseFloat(volumeLiters) : undefined;
    const ec = measuredEc ? parseFloat(measuredEc) : undefined;
    const ph = measuredPh ? parseFloat(measuredPh) : undefined;

    const ferts: ConfirmFeedingDetail[] = fertilizerRows
      .filter((r) => r.fertilizer && r.ml_applied)
      .map((r) => ({
        fertilizer_key: r.fertilizer!.key,
        ml_applied: parseFloat(r.ml_applied),
      }));

    onConfirm({
      notes: notes || undefined,
      volume_liters: vol,
      fertilizers_used: ferts.length > 0 ? ferts : undefined,
      measured_ec: ec,
      measured_ph: ph,
    });
  }, [notes, volumeLiters, measuredEc, measuredPh, fertilizerRows, onConfirm]);

  const dialogTitle = useMemo(
    () =>
      `${t(`enums.reminderType.${reminderType}`)} — ${plantName}`,
    [t, reminderType, plantName],
  );

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{dialogTitle}</DialogTitle>
      <DialogContent>
        <TextField
          label={t('common.notes')}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          fullWidth
          multiline
          minRows={2}
          margin="normal"
          size="small"
          inputProps={{ 'aria-label': t('common.notes') }}
          data-testid="confirm-notes-field"
        />

        {showFeedingSection && (
          <Box sx={{ mt: 1 }}>
            <Box
              sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
              onClick={() => setFeedingExpanded((prev) => !prev)}
            >
              <Typography variant="subtitle2" color="text.secondary">
                {t('pages.pflege.feedingDetails')}
              </Typography>
              <IconButton size="small">
                {feedingExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>

            <Collapse in={feedingExpanded}>
              {hasPresets && phaseName && (
                <Alert severity="info" sx={{ mb: 1.5 }}>
                  {t('pages.pflege.presetFromPlan', { phase: t(`enums.phaseName.${phaseName}`) })}
                </Alert>
              )}

              <Box sx={{ display: 'flex', gap: 2, mt: 1, flexWrap: { xs: 'wrap', sm: 'nowrap' } }}>
                <TextField
                  label={t('pages.pflege.volumeLiters')}
                  value={volumeLiters}
                  onChange={(e) => setVolumeLiters(e.target.value)}
                  type="number"
                  size="small"
                  inputProps={{ min: 0, step: 0.1, inputMode: 'decimal' }}
                  helperText={volumeHint ?? t('pages.pflege.volumeLitersHelper')}
                  sx={{ flex: 1, minWidth: { xs: '100%', sm: 'unset' } }}
                  data-testid="confirm-volume-field"
                />
                <TextField
                  label={defaultTargetEc
                    ? `EC — ${t('pages.pflege.target')}: ${defaultTargetEc} mS/cm`
                    : t('pages.pflege.measuredEc')}
                  value={measuredEc}
                  onChange={(e) => setMeasuredEc(e.target.value)}
                  type="number"
                  size="small"
                  inputProps={{ min: 0, step: 0.1, inputMode: 'decimal' }}
                  helperText={t('pages.pflege.measuredEcHelper')}
                  sx={{ flex: 1, minWidth: { xs: '100%', sm: 'unset' } }}
                  data-testid="confirm-ec-field"
                />
                <TextField
                  label={defaultTargetPh
                    ? `pH — ${t('pages.pflege.target')}: ${defaultTargetPh}`
                    : t('pages.pflege.measuredPh')}
                  value={measuredPh}
                  onChange={(e) => setMeasuredPh(e.target.value)}
                  type="number"
                  size="small"
                  inputProps={{ min: 0, max: 14, step: 0.1, inputMode: 'decimal' }}
                  helperText={t('pages.pflege.measuredPhHelper')}
                  sx={{ flex: 1, minWidth: { xs: '100%', sm: 'unset' } }}
                  data-testid="confirm-ph-field"
                />
              </Box>

              <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2, mb: 1 }}>
                {t('pages.pflege.fertilizersUsed')}
              </Typography>

              {fertilizerRows.map((row, index) => (
                <Box key={index} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'center' }}>
                  <Autocomplete
                    options={fertilizers}
                    getOptionLabel={(f) => `${f.product_name} (${f.brand})`}
                    value={row.fertilizer}
                    onChange={(_, val) => handleFertilizerChange(index, val)}
                    size="small"
                    sx={{ flex: 2 }}
                    renderInput={(params) => (
                      <TextField {...params} label={t('entities.fertilizer')} />
                    )}
                  />
                  <TextField
                    label="ml/L"
                    value={row.ml_applied}
                    onChange={(e) => handleMlChange(index, e.target.value)}
                    type="number"
                    size="small"
                    inputProps={{ min: 0, step: 0.1 }}
                    sx={{ flex: 1 }}
                  />
                  <IconButton size="small" onClick={() => handleRemoveFertilizer(index)}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Box>
              ))}

              <Button
                startIcon={<AddIcon />}
                size="small"
                onClick={handleAddFertilizer}
                sx={{ mt: 0.5 }}
              >
                {t('pages.pflege.addFertilizer')}
              </Button>
            </Collapse>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading} data-testid="confirm-dialog-cancel">
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          color="success"
          onClick={handleSubmit}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={18} /> : undefined}
          data-testid="confirm-dialog-submit"
        >
          {t('pages.pflege.confirmAction')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
