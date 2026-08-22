import { useCallback, useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import SpaIcon from '@mui/icons-material/Spa';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import DiaryEntryCard from '@/components/diary/DiaryEntryCard';
import {
  cancelDiaryEntryAnalysis,
  getPlantDiaryEntry,
  requestDiaryEntryAnalysis,
} from '@/api/endpoints/diary';
import type { DiaryOverviewItem, PlantDiaryEntry } from '@/api/types';

interface DiaryEntryDetailDialogProps {
  /** The clicked row; `null` keeps the dialog closed. */
  row: DiaryOverviewItem | null;
  onClose: () => void;
  /**
   * The entry after a state change, so the list row can follow without a full
   * reload. Called with exactly what the server answered — never with a state
   * this dialog assumed.
   */
  onEntryChanged: (entry: PlantDiaryEntry) => void;
  /** Turn a failed marking call into a sentence (403/409 have their own text). */
  onAnalysisError: (error: unknown) => void;
}

/**
 * REQ-051 §6.2 — a row click opens the complete entry with its photos and,
 * where one exists, the analysis result.
 *
 * The overview row is deliberately slim: it carries the summary and nothing
 * else of the result (AK-18). The full finding list with its rationales, the
 * recommended actions, the provenance and the disclaimer live behind this
 * single-entry read — which is also the only place that can show them without
 * shipping 50 complete results for a page that displays one line of each.
 *
 * **Editing is not offered here.** §2.5.1 fixes the capture side to the plant's
 * diary tab; a shortcut to "go to the plant" is the honest substitute, because
 * an edit dialog inside a tenant-wide list would still belong to exactly one
 * plant. Marking for analysis *is* offered — the state is what this page is for.
 */
export default function DiaryEntryDetailDialog({
  row,
  onClose,
  onEntryChanged,
  onAnalysisError,
}: DiaryEntryDetailDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));

  const [entry, setEntry] = useState<PlantDiaryEntry | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const plantKey = row?.plant_key ?? null;
  const entryKey = row?.key ?? null;

  const load = useCallback(async () => {
    if (!plantKey || !entryKey) return;
    setLoading(true);
    setError(null);
    try {
      setEntry(await getPlantDiaryEntry(plantKey, entryKey));
    } catch (err) {
      setEntry(null);
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [plantKey, entryKey]);

  useEffect(() => {
    if (!plantKey || !entryKey) {
      // Drop the previous entry when the dialog closes, so re-opening another
      // row never flashes the entry that was open before it.
      setEntry(null);
      setError(null);
      return;
    }
    load();
  }, [plantKey, entryKey, load]);

  /** Apply whatever the server answered with — never an assumed transition. */
  const applyUpdated = useCallback(
    (updated: PlantDiaryEntry) => {
      setEntry(updated);
      onEntryChanged(updated);
    },
    [onEntryChanged],
  );

  const handleRequestAnalysis = useCallback(
    async (target: PlantDiaryEntry) => {
      if (!plantKey) return;
      setBusy(true);
      try {
        applyUpdated(await requestDiaryEntryAnalysis(plantKey, target.key));
      } catch (err) {
        onAnalysisError(err);
      } finally {
        setBusy(false);
      }
    },
    [plantKey, applyUpdated, onAnalysisError],
  );

  const handleCancelAnalysis = useCallback(
    async (target: PlantDiaryEntry) => {
      if (!plantKey) return;
      setBusy(true);
      try {
        applyUpdated(await cancelDiaryEntryAnalysis(plantKey, target.key));
      } catch (err) {
        onAnalysisError(err);
      } finally {
        setBusy(false);
      }
    },
    [plantKey, applyUpdated, onAnalysisError],
  );

  const plantLabel = row?.plant_name || row?.instance_id || '';

  return (
    <Dialog
      open={row !== null}
      onClose={onClose}
      fullScreen={fullScreen}
      maxWidth="md"
      fullWidth
      aria-labelledby="diary-entry-detail-title"
      data-testid="diary-entry-detail-dialog"
    >
      <DialogTitle id="diary-entry-detail-title">
        {t('pages.diaryOverview.detail.title')}
        {plantLabel && (
          <Typography variant="body2" color="text.secondary" component="div">
            {plantLabel}
            {row?.species_name ? ` · ${row.species_name}` : ''}
          </Typography>
        )}
      </DialogTitle>

      <DialogContent dividers>
        {loading && <LoadingSkeleton variant="card" />}
        {!loading && error && <ErrorDisplay error={error} onRetry={load} />}
        {!loading && !error && entry && (
          <DiaryEntryCard
            entry={entry}
            canRequestAnalysis={entry.can_request_analysis}
            /* Editing and deleting belong to the plant's diary tab (§2.5.1). */
            canWrite={false}
            analysisBusy={busy}
            onRequestAnalysis={handleRequestAnalysis}
            onCancelAnalysis={handleCancelAnalysis}
          />
        )}
      </DialogContent>

      <DialogActions sx={{ flexWrap: 'wrap', gap: 1 }}>
        {row && (
          <Button
            component={RouterLink}
            to={`/pflanzen/plant-instances/${row.plant_key}`}
            startIcon={<SpaIcon />}
            sx={{ minHeight: 44 }}
            data-testid="diary-detail-open-plant"
          >
            {t('pages.diaryOverview.detail.openPlant')}
          </Button>
        )}
        <Box sx={{ flex: 1 }} />
        <Button onClick={onClose} sx={{ minHeight: 44 }} data-testid="diary-detail-close">
          {t('common.close')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
