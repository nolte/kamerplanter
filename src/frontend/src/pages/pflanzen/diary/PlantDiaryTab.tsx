import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import EmptyState from '@/components/common/EmptyState';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import DiaryEntryCard from '@/components/diary/DiaryEntryCard';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import { isApiError } from '@/api/errors';
import {
  DIARY_PAGE_SIZE,
  cancelDiaryEntryAnalysis,
  deletePlantDiaryEntry,
  listPlantDiaryEntries,
  requestDiaryEntryAnalysis,
} from '@/api/endpoints/diary';
import type { PlantDiaryEntry } from '@/api/types';
import DiaryEntryDialog from './DiaryEntryDialog';

interface PlantDiaryTabProps {
  plantInstanceKey: string;
  /** Disable write actions when the instance is removed/read-only. */
  readOnly?: boolean;
}

/**
 * REQ-050 §2.5.1 — the "Tagebuch" tab of a plant instance.
 *
 * Shows the entries of this one plant, newest first, and is the place entries
 * are created, edited, deleted and marked for analysis (AK-14). Built on the
 * standalone diary endpoints (`/plant-instances/{key}/diary`), so a plant that
 * belongs to no planting run has a diary too — which is exactly the plant this
 * tab exists for.
 *
 * **The analysis button is not authorised here.** Whether a user may mark an
 * entry follows from role, authorship (§7.2), consent (§7.1) and operating mode
 * (§7.5); §2.5.2 states plainly that reproducing that rule in the client means
 * maintaining it in two places and forgetting one at the next change. The tab
 * therefore renders the server's verdict — `can_request_analysis`, which every
 * entry of the listing carries — and treats a 403 on the marking call as the
 * binding answer (AK-19, AK-18a).
 *
 * The same holds for `analysis_state`: it is the *displayed* state, already
 * corrected for a run-out agent lease server-side. The tab used to fetch that
 * pair from a second endpoint (the tenant-wide overview, filtered to this
 * plant) because the entry payload carried neither. It carries both now, so the
 * tab issues **one** request per open and cannot contradict the overview about
 * the same entry.
 */
export default function PlantDiaryTab({
  plantInstanceKey,
  readOnly = false,
}: PlantDiaryTabProps) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { canEdit } = useTenantPermissions();
  const canWrite = canEdit && !readOnly;

  const [entries, setEntries] = useState<PlantDiaryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<PlantDiaryEntry | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<PlantDiaryEntry | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [analysisBusyKey, setAnalysisBusyKey] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // One request: the listing is both the content and the permission
      // verdict. Each entry carries its own `can_request_analysis` and its
      // lease-corrected `analysis_state`.
      const page = await listPlantDiaryEntries(plantInstanceKey, {
        offset: 0,
        limit: DIARY_PAGE_SIZE,
      });
      setEntries(page);
      setHasMore(page.length === DIARY_PAGE_SIZE);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [plantInstanceKey]);

  useEffect(() => {
    load();
  }, [load]);

  const loadMore = useCallback(async () => {
    setLoadingMore(true);
    try {
      const page = await listPlantDiaryEntries(plantInstanceKey, {
        offset: entries.length,
        limit: DIARY_PAGE_SIZE,
      });
      setEntries((prev) => [...prev, ...page]);
      setHasMore(page.length === DIARY_PAGE_SIZE);
    } catch (err) {
      handleError(err);
    } finally {
      setLoadingMore(false);
    }
  }, [plantInstanceKey, entries.length, handleError]);

  const handleSaved = useCallback((saved: PlantDiaryEntry) => {
    // The create/update response is a full entry, verdict included — there is
    // nothing left to re-fetch after a save.
    setEntries((prev) => {
      const exists = prev.some((e) => e.key === saved.key);
      return exists ? prev.map((e) => (e.key === saved.key ? saved : e)) : [saved, ...prev];
    });
    setEditTarget(null);
  }, []);

  const handleConfirmDelete = useCallback(async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deletePlantDiaryEntry(plantInstanceKey, deleteTarget.key);
      setEntries((prev) => prev.filter((e) => e.key !== deleteTarget.key));
      notification.success(t('pages.plantDiary.deleted'));
      setDeleteTarget(null);
    } catch (err) {
      handleError(err);
    } finally {
      setDeleting(false);
    }
  }, [deleteTarget, plantInstanceKey, notification, handleError, t]);

  /**
   * Replace an entry with the version the server answered with.
   *
   * Both marking endpoints return the **entry**, not 204, precisely so the UI
   * can show the state it actually ended up in instead of assuming the
   * transition it asked for succeeded as imagined. Since that entry carries the
   * verdict as well, nothing has to be merged in from elsewhere.
   */
  const applyUpdated = useCallback((updated: PlantDiaryEntry) => {
    setEntries((prev) => prev.map((e) => (e.key === updated.key ? updated : e)));
  }, []);

  /** Turn a failed transition into a sentence the user can act on (AK-19). */
  const reportAnalysisError = useCallback(
    (err: unknown) => {
      if (isApiError(err) && err.statusCode === 403) {
        notification.error(t('pages.plantDiary.analysis.forbidden'));
        return;
      }
      if (isApiError(err) && err.statusCode === 409) {
        notification.error(t('pages.plantDiary.analysis.conflict'));
        return;
      }
      handleError(err);
    },
    [notification, handleError, t],
  );

  const handleRequestAnalysis = useCallback(
    async (entry: PlantDiaryEntry) => {
      setAnalysisBusyKey(entry.key);
      try {
        applyUpdated(await requestDiaryEntryAnalysis(plantInstanceKey, entry.key));
        notification.success(t('pages.plantDiary.analysis.requested'));
      } catch (err) {
        reportAnalysisError(err);
      } finally {
        setAnalysisBusyKey(null);
      }
    },
    [plantInstanceKey, applyUpdated, notification, t, reportAnalysisError],
  );

  const handleCancelAnalysis = useCallback(
    async (entry: PlantDiaryEntry) => {
      setAnalysisBusyKey(entry.key);
      try {
        applyUpdated(await cancelDiaryEntryAnalysis(plantInstanceKey, entry.key));
        notification.success(t('pages.plantDiary.analysis.cancelled'));
      } catch (err) {
        reportAnalysisError(err);
      } finally {
        setAnalysisBusyKey(null);
      }
    },
    [plantInstanceKey, applyUpdated, notification, t, reportAnalysisError],
  );

  const emptyDescription = useMemo(
    () =>
      canWrite
        ? t('pages.plantDiary.emptyDescriptionWrite')
        : t('pages.plantDiary.emptyDescriptionRead'),
    [canWrite, t],
  );

  if (loading) return <LoadingSkeleton variant="card" />;
  if (error) return <ErrorDisplay error={error} onRetry={load} />;

  return (
    <Box data-testid="plant-diary-tab">
      <Box
        sx={{
          display: 'flex',
          alignItems: { xs: 'flex-start', sm: 'center' },
          justifyContent: 'space-between',
          gap: 2,
          mb: 2,
          flexWrap: 'wrap',
        }}
      >
        <Box>
          <Typography component="h2" variant="subtitle1" sx={{ fontWeight: 600 }}>
            {t('pages.plantDiary.sectionTitle')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('pages.plantDiary.intro')}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {/* No live channel exists for the analysis state (§2.5.4), so the
              refresh is explicit rather than implied by a spinner. */}
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={load}
            sx={{ minHeight: 44 }}
            data-testid="diary-refresh"
          >
            {t('pages.plantDiary.refresh')}
          </Button>
          {canWrite && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                setEditTarget(null);
                setDialogOpen(true);
              }}
              sx={{ minHeight: 44 }}
              data-testid="diary-add-entry"
            >
              {t('pages.plantDiary.createEntry')}
            </Button>
          )}
        </Box>
      </Box>

      {entries.length === 0 ? (
        <EmptyState
          message={t('pages.plantDiary.emptyTitle')}
          description={emptyDescription}
          actionLabel={canWrite ? t('pages.plantDiary.createEntry') : undefined}
          onAction={
            canWrite
              ? () => {
                  setEditTarget(null);
                  setDialogOpen(true);
                }
              : undefined
          }
        />
      ) : (
        <>
          {/* `entry.analysis_state` is already the *displayed* state, corrected
              server-side for a run-out lease — there is nothing to override. */}
          {entries.map((entry) => (
            <DiaryEntryCard
              key={entry.key}
              entry={entry}
              canRequestAnalysis={entry.can_request_analysis}
              canWrite={canWrite}
              analysisBusy={analysisBusyKey === entry.key}
              onEdit={(target) => {
                setEditTarget(target);
                setDialogOpen(true);
              }}
              onDelete={setDeleteTarget}
              onRequestAnalysis={handleRequestAnalysis}
              onCancelAnalysis={handleCancelAnalysis}
            />
          ))}
          {hasMore && (
            <Button
              onClick={loadMore}
              disabled={loadingMore}
              sx={{ minHeight: 44 }}
              data-testid="diary-load-more"
            >
              {t('pages.plantDiary.loadMore')}
            </Button>
          )}
        </>
      )}

      <DiaryEntryDialog
        open={dialogOpen}
        plantInstanceKey={plantInstanceKey}
        entry={editTarget}
        onClose={() => {
          setDialogOpen(false);
          setEditTarget(null);
        }}
        onSaved={handleSaved}
      />

      <ConfirmDialog
        open={deleteTarget !== null}
        title={t('pages.plantDiary.deleteTitle')}
        message={t('pages.plantDiary.deleteConfirm')}
        confirmLabel={t('common.delete')}
        destructive
        loading={deleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </Box>
  );
}
