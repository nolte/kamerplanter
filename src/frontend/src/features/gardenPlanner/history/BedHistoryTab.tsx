/**
 * The "History" tab of the bed view (REQ-053 GP-FR-102, GP-FR-103, GP-FR-131): the planting
 * timeline per year with the family colour-coded, and below it the chronological list of care
 * events and planting events with the filters category, period, plant and person. Corrections
 * (superseded entries, `position_corrected`) are hidden until "Show corrections" is switched on.
 * "What stood here in {year}?" fills in a year the app never saw.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useApiError } from '@/hooks/useApiError';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import type { BedSummary } from '../bed/types';
import { useUndoSnackbar } from '../care/useUndoSnackbar';
import BackfillDialog from './BackfillDialog';
import { firstEmptyYear } from './backfillForm';
import HistoryFilterBar from './HistoryFilterBar';
import HistoryList from './HistoryList';
import PlantingTimeline from './PlantingTimeline';
import { cancelBackfill, getBedHistory, listBedPlantOptions } from './historyApi';
import { activeFilterCount, emptyFilters, toQuery, isRangeInverted, type HistoryFilters } from './historyFilters';
import type { BackfillResult, FilterOption } from './historyTypes';
import { useHistoryPages } from './useHistoryPages';
import { usePersonOptions } from './usePersonOptions';
import { useRotationTimeline } from './useRotationTimeline';

/** A bed's history has no default window: every year the retention keeps. */
const DEFAULTS: HistoryFilters = emptyFilters('all');

interface BedHistoryTabProps {
  bed: BedSummary;
}

export default function BedHistoryTab({ bed }: BedHistoryTabProps) {
  const { t } = useTranslation();
  const { canEdit } = useTenantPermissions();
  const { handleError } = useApiError();
  const { offerUndo } = useUndoSnackbar();
  const people = usePersonOptions();
  const [filters, setFilters] = useState<HistoryFilters>(DEFAULTS);
  const [plants, setPlants] = useState<FilterOption[]>([]);
  const [backfillYearChoice, setBackfillYearChoice] = useState<number | null>(null);
  const [cancelling, setCancelling] = useState<{ key: string; year: number } | null>(null);
  const [cancelBusy, setCancelBusy] = useState(false);
  const timeline = useRotationTimeline(bed.key);

  useEffect(() => {
    let cancelled = false;
    listBedPlantOptions(bed.key)
      .then((options) => {
        if (!cancelled) setPlants(options);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [bed.key]);

  const inverted = isRangeInverted(filters);
  // The query is read at the instant the filters change, not on every render: "30 days" would otherwise
  // move with the clock and refetch forever.
  const query = useMemo(() => toQuery(filters, new Date(), 'bed'), [filters]);
  const resetKey = JSON.stringify(query);
  const fetchPage = useCallback(
    (offset: number) => (inverted ? Promise.resolve([]) : getBedHistory(bed.key, query, offset)),
    [bed.key, query, inverted],
  );
  const pages = useHistoryPages(fetchPage, `${bed.key}:${resetKey}`);
  const { reload: reloadHistory } = pages;
  const { reload: reloadTimeline } = timeline;

  const changed = useCallback(() => {
    reloadHistory();
    reloadTimeline();
  }, [reloadHistory, reloadTimeline]);

  const onSaved = (result: BackfillResult) => {
    setBackfillYearChoice(null);
    changed();
    offerUndo({
      message: t('pages.bed.history.backfill.saved', { year: result.year }),
      undo: () => cancelBackfill(bed.key, result.care_event_key),
      onUndone: changed,
    });
  };

  const confirmCancel = async () => {
    if (!cancelling) return;
    setCancelBusy(true);
    try {
      await cancelBackfill(bed.key, cancelling.key);
      setCancelling(null);
      changed();
    } catch (error) {
      handleError(error);
    } finally {
      setCancelBusy(false);
    }
  };

  const startYear =
    timeline.state.status === 'ready' ? firstEmptyYear(timeline.state.timeline.timeline, new Date()) : new Date().getFullYear() - 1;

  return (
    <Box data-testid="bed-history-tab" sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <PlantingTimeline
        state={timeline.state}
        canEdit={canEdit}
        onBackfill={(year) => setBackfillYearChoice(year ?? startYear)}
        onCancel={(key, year) => setCancelling({ key, year })}
        onRetry={reloadTimeline}
      />

      <Box component="section" aria-labelledby="bed-history-title" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'space-between', alignItems: 'baseline' }}>
          <Typography id="bed-history-title" variant="h6" component="h2">
            {t('pages.bed.history.title')}
          </Typography>
          <Link component={RouterLink} to="/standorte/historie" sx={{ minHeight: 44, display: 'inline-flex', alignItems: 'center' }} data-testid="history-all-beds">
            {t('pages.bed.history.allBeds')}
          </Link>
        </Box>
        <HistoryFilterBar
          filters={filters}
          defaults={DEFAULTS}
          onChange={(patch) => setFilters((current) => ({ ...current, ...patch }))}
          onReset={() => setFilters(DEFAULTS)}
          plants={plants}
          people={people}
          testIdPrefix="history"
        />
        <HistoryList pages={pages} filtered={activeFilterCount(filters, DEFAULTS) > 0} testIdPrefix="history" />
      </Box>

      {backfillYearChoice !== null && (
        <BackfillDialog
          bedKey={bed.key}
          initialYear={backfillYearChoice}
          onClose={() => setBackfillYearChoice(null)}
          onSaved={onSaved}
        />
      )}
      <ConfirmDialog
        open={cancelling !== null}
        title={t('pages.bed.history.timeline.cancelTitle', { year: cancelling?.year ?? '' })}
        message={t('pages.bed.history.timeline.cancelMessage')}
        confirmLabel={t('pages.bed.history.timeline.cancelConfirm')}
        onConfirm={() => void confirmCancel()}
        onCancel={() => setCancelling(null)}
        destructive
        loading={cancelBusy}
      />
    </Box>
  );
}
