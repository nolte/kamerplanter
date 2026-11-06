/**
 * The chronological list of the bed history and of the tenant-wide history (REQ-053 GP-FR-102,
 * GP-FR-107): newest first, one line per care event or derived planting event, 50 per page with a
 * "Load more" button. Read-only: corrections are made on the care tab (supersede / void, WP 4.1).
 */
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import Typography from '@mui/material/Typography';
import EmptyState from '@/components/common/EmptyState';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { categoryLabel, formatQuantity, itemHeadline } from './historyFormat';
import type { HistoryPages } from './useHistoryPages';
import type { HistoryItem } from './historyTypes';

interface HistoryListProps {
  pages: HistoryPages<HistoryItem>;
  /** Names a bed by key (tenant-wide list); omitted on a bed's own list. */
  bedName?: (locationKey: string) => string | undefined;
  /** Whether any filter is set, to word the empty state. */
  filtered: boolean;
  /** Resets the filters: the one action of the filtered empty state, open to every member (GP-UX-049). */
  onResetFilters: () => void;
  /**
   * "What stood here?" (backfill): the one action of an unfiltered empty bed history, passed only to the
   * roles that may write. The tenant-wide history is read-only and offers none there.
   */
  onBackfill?: () => void;
  testIdPrefix: string;
}

function timeOf(value: string, locale: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

/** Planting events carry a date, not an instant: show the day only. */
function dayOf(value: string, locale: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeZone: 'UTC' }).format(date);
}

function HistoryRow({ item, bedLabel, locale, testIdPrefix }: { item: HistoryItem; bedLabel?: string; locale: string; testIdPrefix: string }) {
  const { t } = useTranslation();
  const line = item.care_event;
  const derived = line === null;
  const quantity = line ? formatQuantity(t, line) : '';
  const details = line
    ? [
        quantity,
        line.product_label,
        line.material ? t(`enums.careMaterial.${line.material}`, { defaultValue: line.material }) : null,
        line.observed_outcome,
      ].filter((part): part is string => Boolean(part))
    : [];
  const who = line ? (line.performed_by_label ?? line.performed_by) : null;
  const dateOnly = derived && item.kind !== 'run_started' && item.kind !== 'run_completed';

  return (
    <ListItem
      divider
      alignItems="flex-start"
      data-testid={`${testIdPrefix}-item-${item.id}`}
      sx={{ display: 'flex', flexDirection: 'column', alignItems: 'stretch', gap: 0.5, py: 1.5, px: 0 }}
    >
      <Typography variant="body1" sx={{ overflowWrap: 'anywhere' }}>
        {itemHeadline(t, item)}
      </Typography>
      {details.length > 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>
          {details.join(' \u00B7 ')}
        </Typography>
      )}
      <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>
        <time dateTime={item.at}>{dateOnly ? dayOf(item.at, locale) : timeOf(item.at, locale)}</time>
        {who ? ` \u00B7 ${t('pages.bed.history.by', { name: who })}` : ''}
        {bedLabel && (
          <>
            {' \u00B7 '}
            <span>{bedLabel}</span>
          </>
        )}
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'center' }}>
        <Chip size="small" variant="outlined" label={categoryLabel(t, item.category)} />
        {line?.superseded_by_key && (
          <Chip size="small" color="warning" variant="outlined" label={t('pages.bed.history.state.corrected')} />
        )}
        {line?.supersedes_key && (
          <Chip size="small" variant="outlined" label={t('pages.bed.history.state.correction')} />
        )}
        {line?.voided_at && (
          <Chip size="small" color="error" variant="outlined" label={t('pages.bed.history.state.voided')} />
        )}
        {line?.redacted_at && (
          <Chip size="small" variant="outlined" label={t('pages.bed.history.state.redacted')} />
        )}
        {line?.trigger === 'backfill' && (
          <Chip size="small" variant="outlined" label={t('pages.bed.history.state.backfill')} />
        )}
      </Box>
      {line?.reason && (
        <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>
          {line.reason}
        </Typography>
      )}
    </ListItem>
  );
}

export default function HistoryList({ pages, bedName, filtered, onResetFilters, onBackfill, testIdPrefix }: HistoryListProps) {
  const { t, i18n } = useTranslation();
  const { state } = pages;

  if (state.status === 'loading') {
    return (
      <Box role="status" aria-busy="true" aria-label={t('pages.bed.history.loading')}>
        <LoadingSkeleton variant="card" />
      </Box>
    );
  }
  if (state.status === 'error') return <ErrorDisplay error={state.message} onRetry={pages.reload} />;
  if (state.items.length === 0 && !state.hasMore) {
    // GP-UX-049: a describing text and at most one action - reset a filter that hides everything, else
    // fill in an earlier year where the caller lets this role write.
    const backfill = !filtered ? onBackfill : undefined;
    const description = filtered
      ? 'pages.bed.history.empty.filteredDescription'
      : backfill
        ? 'pages.bed.history.empty.descriptionBackfill'
        : 'pages.bed.history.empty.description';
    return (
      <Box data-testid={`${testIdPrefix}-empty`}>
        <EmptyState
          message={t(filtered ? 'pages.bed.history.empty.filteredTitle' : 'pages.bed.history.empty.title')}
          description={t(description)}
        />
        {(filtered || backfill) && (
          <Box sx={{ display: 'flex', justifyContent: 'center', pb: 4 }}>
            {filtered ? (
              <Button variant="contained" onClick={onResetFilters} sx={{ minHeight: 48 }} data-testid={`${testIdPrefix}-empty-reset`}>
                {t('pages.bed.history.filters.reset')}
              </Button>
            ) : (
              <Button variant="contained" onClick={backfill} sx={{ minHeight: 48 }} data-testid={`${testIdPrefix}-empty-backfill`}>
                {t('pages.bed.history.timeline.whatStood')}
              </Button>
            )}
          </Box>
        )}
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      <List disablePadding data-testid={`${testIdPrefix}-list`} aria-label={t('pages.bed.history.list')}>
        {state.items.map((item) => (
          <HistoryRow
            key={item.id}
            item={item}
            bedLabel={item.care_event ? bedName?.(item.care_event.location_key) : undefined}
            locale={i18n.language}
            testIdPrefix={testIdPrefix}
          />
        ))}
      </List>
      <Box role="status" aria-live="polite" sx={{ minHeight: 24 }}>
        <Typography variant="body2" color="text.secondary">
          {state.loadingMore
            ? t('pages.bed.history.loadingMore')
            : t('pages.bed.history.shown', { count: state.items.length })}
        </Typography>
      </Box>
      {state.moreError && <ErrorDisplay error={state.moreError} />}
      {state.hasMore && (
        <Button
          variant="outlined"
          onClick={() => {
            // Not `disabled`: a disabled button drops the keyboard focus; the click is ignored while it runs.
            if (!state.loadingMore) pages.loadMore();
          }}
          aria-disabled={state.loadingMore}
          sx={{ minHeight: 48, alignSelf: 'flex-start' }}
          data-testid={`${testIdPrefix}-more`}
        >
          {state.moreError ? t('pages.bed.history.retryMore') : t('pages.bed.history.loadMore')}
        </Button>
      )}
    </Box>
  );
}
