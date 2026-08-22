import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import RefreshIcon from '@mui/icons-material/Refresh';
import PhotoLibraryIcon from '@mui/icons-material/PhotoLibrary';
import SpaIcon from '@mui/icons-material/Spa';
import AuthImage from '@/components/common/AuthImage';
import DataTable, { type Column } from '@/components/common/DataTable';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import MobileCard from '@/components/common/MobileCard';
import PageTitle from '@/components/layout/PageTitle';
import { useApiError } from '@/hooks/useApiError';
import { useDebounce } from '@/hooks/useDebounce';
import { useNotification } from '@/hooks/useNotification';
import { isApiError } from '@/api/errors';
import {
  diaryPhotoUri,
  listDiaryOverview,
  requestDiaryEntryAnalysis,
} from '@/api/endpoints/diary';
import { listAllPlantInstances } from '@/api/endpoints/plantInstances';
import { formatDateTime } from '@/utils/formatting';
import type { DiaryOverviewItem, PlantDiaryEntry, PlantInstance } from '@/api/types';
import { kamiCare } from '@/assets/brand/illustrations';
import DiaryEntryDetailDialog from './DiaryEntryDetailDialog';
import DiaryOverviewAnalysisCell from './DiaryOverviewAnalysisCell';
import DiaryOverviewFilters, { type DiaryFilterOption } from './DiaryOverviewFilters';
import {
  activeDiaryFilterCount,
  EMPTY_DIARY_FILTERS,
  type DiaryOverviewFilterState,
} from './diaryOverviewFilterState';

/** Page size the overview starts with; the backend caps `limit` at 200. */
const DEFAULT_PAGE_SIZE = 50;

/** Debounce of the two free-typing filters, matching the DataTable toolbar. */
const TYPING_DEBOUNCE_MS = 300;

/**
 * Project the entry a marking call answered with back onto its overview row.
 *
 * Only the fields the row actually carries are touched, and each of them comes
 * from the response rather than from the transition we asked for — a refused or
 * differently-resolved request must not leave the list claiming success. The
 * summary is taken from `analysis.summary` because the row never carries the
 * findings (AK-18).
 */
function mergeEntryIntoRow(row: DiaryOverviewItem, entry: PlantDiaryEntry): DiaryOverviewItem {
  return {
    ...row,
    analysis_state: entry.analysis_state,
    analysis_summary: entry.analysis?.summary ?? null,
    analysis_error: entry.analysis_error,
    analyzed_at: entry.analysis?.analyzed_at ?? null,
    can_request_analysis: entry.can_request_analysis,
    photo_count: entry.photo_refs.length,
    preview_photo_id: entry.photo_refs[0] ?? null,
    title: entry.title,
    tags: entry.tags,
  };
}

/**
 * REQ-051 §6.2 — the tenant-wide diary overview.
 *
 * Every diary entry of **every** plant of the tenant in one chronologically
 * descending list, so the analysis state can be surveyed without clicking
 * through plant after plant. In a shared garden it legitimately shows other
 * members' entries — they belong to the same tenant — while marking stays
 * restricted to the caller's own (AK-19).
 *
 * Three properties are load-bearing:
 *
 * * **Filtering, sorting and paging are server-side.** Every control maps onto a
 *   query parameter, so `total` is the real number of matches across all pages
 *   and the free-text search reaches entries that are not on the loaded page.
 * * **Refreshing is explicit** (AK-29, §2.5.4). The state is re-read when the
 *   page opens and when the user asks for it. No polling and no push channel:
 *   the MCP transport has no server-to-client direction, and inventing one for
 *   this feature would be a channel nobody asked for.
 * * **No progress indication for `requested`** (AK-27). See
 *   {@link DiaryOverviewAnalysisCell}.
 *
 * The page is owned by the REQ-042 module `diary` (`core: false`), so a user who
 * keeps no diary can switch the entry off entirely; `ModuleGuard` in MainLayout
 * turns a deep link into the reactivation hint rather than a 404 (AK-31).
 */
export default function DiaryOverviewPage() {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [filters, setFilters] = useState<DiaryOverviewFilterState>(EMPTY_DIARY_FILTERS);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [rows, setRows] = useState<DiaryOverviewItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  /** Bumped by the refresh button — the only thing that re-reads on demand. */
  const [reloadToken, setReloadToken] = useState(0);
  const [plants, setPlants] = useState<PlantInstance[]>([]);
  const [detailRow, setDetailRow] = useState<DiaryOverviewItem | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);

  const debouncedQuery = useDebounce(filters.q, TYPING_DEBOUNCE_MS);
  const debouncedTag = useDebounce(filters.tag, TYPING_DEBOUNCE_MS);

  const {
    analysisStates,
    plantKey,
    speciesKey,
    entryType,
    from,
    to,
    sort,
  } = filters;
  // Join once: the effect below must not re-run because a new array instance
  // with the same members was produced by a keystroke elsewhere.
  const analysisStateKey = analysisStates.join(',');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await listDiaryOverview({
        analysis_state: analysisStateKey
          ? (analysisStateKey.split(',') as DiaryOverviewFilterState['analysisStates'])
          : undefined,
        plant_key: plantKey || undefined,
        species_key: speciesKey || undefined,
        entry_type: entryType || undefined,
        tag: debouncedTag.trim() || undefined,
        from: from || undefined,
        to: to || undefined,
        q: debouncedQuery.trim() || undefined,
        sort,
        limit: pageSize,
        offset: page * pageSize,
      });
      setRows(response.items);
      setTotal(response.total);
    } catch (err) {
      setRows([]);
      setTotal(0);
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [
    analysisStateKey,
    plantKey,
    speciesKey,
    entryType,
    debouncedTag,
    from,
    to,
    debouncedQuery,
    sort,
    page,
    pageSize,
  ]);

  useEffect(() => {
    load();
  }, [load, reloadToken]);

  // The plant/species dropdown options. Loaded once and independently of the
  // listing: a tenant without a readable plant list still gets a usable page,
  // it just cannot filter by plant.
  useEffect(() => {
    let cancelled = false;
    listAllPlantInstances()
      .then((all) => {
        if (!cancelled) setPlants(all);
      })
      .catch(() => {
        if (!cancelled) setPlants([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const plantOptions: DiaryFilterOption[] = useMemo(
    () =>
      plants
        .map((plant) => ({
          value: plant.key,
          label: plant.plant_name || plant.instance_id,
        }))
        .sort((a, b) => a.label.localeCompare(b.label)),
    [plants],
  );

  const speciesOptions: DiaryFilterOption[] = useMemo(() => {
    const byKey = new Map<string, string>();
    for (const plant of plants) {
      if (!plant.species_key) continue;
      const label =
        plant.species?.scientific_name ||
        plant.species?.common_names?.[0] ||
        plant.species_key;
      if (!byKey.has(plant.species_key)) byKey.set(plant.species_key, label);
    }
    return Array.from(byKey, ([value, label]) => ({ value, label })).sort((a, b) =>
      a.label.localeCompare(b.label),
    );
  }, [plants]);

  /** A filter change always returns to the first page — page 4 of the old result
   *  set is not page 4 of the new one. */
  const handleFiltersChange = useCallback((next: DiaryOverviewFilterState) => {
    setFilters(next);
    setPage(0);
  }, []);

  /** Turn a refused transition into a sentence the user can act on (AK-18a). */
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

  const applyEntry = useCallback((entry: PlantDiaryEntry) => {
    setRows((prev) =>
      prev.map((row) => (row.key === entry.key ? mergeEntryIntoRow(row, entry) : row)),
    );
    setDetailRow((current) =>
      current && current.key === entry.key ? mergeEntryIntoRow(current, entry) : current,
    );
  }, []);

  const handleRequestAnalysis = useCallback(
    async (row: DiaryOverviewItem) => {
      setBusyKey(row.key);
      try {
        // The marking endpoint is plant-scoped, and the row carries its plant —
        // no extra lookup is needed to reach it from the tenant-wide list.
        applyEntry(await requestDiaryEntryAnalysis(row.plant_key, row.key));
        notification.success(t('pages.plantDiary.analysis.requested'));
      } catch (err) {
        reportAnalysisError(err);
      } finally {
        setBusyKey(null);
      }
    },
    [applyEntry, notification, t, reportAnalysisError],
  );

  const columns: Column<DiaryOverviewItem>[] = useMemo(
    () => [
      {
        id: 'createdAt',
        label: t('pages.diaryOverview.columns.createdAt'),
        sortable: false,
        // `created_at` is nullable at the record (§2.5.2): a single legacy
        // document without a timestamp must render a dash, not blow up a page.
        render: (row) =>
          row.created_at ? (
            formatDateTime(row.created_at)
          ) : (
            <Typography variant="body2" color="text.secondary">
              {'—'}
            </Typography>
          ),
      },
      {
        id: 'plant',
        label: t('pages.diaryOverview.columns.plant'),
        sortable: false,
        render: (row) => (
          <Chip
            icon={<SpaIcon />}
            label={row.plant_name || row.instance_id}
            size="small"
            color="success"
            variant="outlined"
            component={RouterLink}
            to={`/pflanzen/plant-instances/${row.plant_key}`}
            // The row itself opens the entry; without this a tap would follow
            // the link *and* open the dialog.
            onClick={(e) => e.stopPropagation()}
            data-testid={`diary-plant-link-${row.plant_key}`}
          />
        ),
      },
      {
        id: 'species',
        label: t('pages.diaryOverview.columns.species'),
        sortable: false,
        hideBelowBreakpoint: 'md',
        render: (row) => (
          <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
            {row.species_name || '—'}
          </Typography>
        ),
      },
      {
        id: 'entryType',
        label: t('pages.diaryOverview.columns.entryType'),
        sortable: false,
        render: (row) => (
          <Chip
            size="small"
            variant="outlined"
            label={t(`enums.diaryEntryType.${row.entry_type}`)}
            data-testid="diary-entry-type"
          />
        ),
      },
      {
        id: 'title',
        label: t('pages.diaryOverview.columns.title'),
        sortable: false,
        render: (row) => (
          <Typography
            variant="body2"
            sx={{
              maxWidth: { xs: 200, md: 320 },
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={row.title || row.excerpt}
            data-testid="diary-entry-title"
          >
            {/* Title, otherwise the server-side excerpt of the free text. */}
            {row.title || row.excerpt || '—'}
          </Typography>
        ),
      },
      {
        id: 'photos',
        label: t('pages.diaryOverview.columns.photos'),
        sortable: false,
        hideBelowBreakpoint: 'md',
        render: (row) =>
          row.photo_count === 0 ? (
            <Typography variant="body2" color="text.secondary">
              {'—'}
            </Typography>
          ) : (
            <Box
              sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
              data-testid="diary-photo-count"
              data-count={row.photo_count}
            >
              {row.preview_photo_id && (
                <AuthImage
                  /* 128 px is the smallest rendition (NFR-013 §8.2) — a list of
                     50 rows must not pull 50 full-size images for a thumbnail. */
                  uri={diaryPhotoUri(row.preview_photo_id, 128)}
                  alt={t('pages.diaryOverview.photoPreviewAlt')}
                  sx={{ width: 40, height: 40, borderRadius: 1, bgcolor: 'action.hover' }}
                  data-testid="diary-photo-preview"
                />
              )}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <PhotoLibraryIcon fontSize="small" color="action" aria-hidden="true" />
                <Typography variant="body2">{row.photo_count}</Typography>
              </Box>
            </Box>
          ),
      },
      {
        id: 'analysis',
        label: t('pages.diaryOverview.columns.analysis'),
        sortable: false,
        render: (row) => (
          <DiaryOverviewAnalysisCell
            row={row}
            busy={busyKey === row.key}
            onRequestAnalysis={handleRequestAnalysis}
          />
        ),
      },
    ],
    [t, busyKey, handleRequestAnalysis],
  );

  const activeFilters = activeDiaryFilterCount(filters);

  if (error) {
    return (
      <Box data-testid="diary-overview-page">
        <PageTitle title={t('pages.diaryOverview.title')} />
        <ErrorDisplay error={error} onRetry={load} />
      </Box>
    );
  }

  return (
    <Box data-testid="diary-overview-page">
      <PageTitle
        title={t('pages.diaryOverview.title')}
        action={
          /* AK-29: refreshing is a button, because there is no channel that
             could tell the browser an agent finished (§2.5.4). */
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => setReloadToken((token) => token + 1)}
            sx={{ minHeight: 44 }}
            data-testid="diary-overview-refresh"
          >
            {t('pages.diaryOverview.refresh')}
          </Button>
        }
      />

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.diaryOverview.description')}
      </Typography>

      <DiaryOverviewFilters
        value={filters}
        onChange={handleFiltersChange}
        plantOptions={plantOptions}
        speciesOptions={speciesOptions}
      />

      <DataTable
        columns={columns}
        rows={rows}
        loading={loading}
        // Server-side paging: `total` counts the matches across all pages, so
        // the pager is honest even though only `pageSize` rows are in memory.
        total={total}
        page={page}
        rowsPerPage={pageSize}
        onPageChange={setPage}
        onRowsPerPageChange={(size) => {
          setPageSize(size);
          setPage(0);
        }}
        getRowKey={(row) => row.key}
        onRowClick={setDetailRow}
        ariaLabel={t('pages.diaryOverview.title')}
        sectionTestId="diary-overview"
        emptyMessage={t('pages.diaryOverview.emptyTitle')}
        emptyDescription={t('pages.diaryOverview.emptyDescription')}
        emptyIllustration={kamiCare}
        // Without this an empty *filtered* result would offer the "record your
        // first entry" illustration, which is wrong twice over: entries exist,
        // and they cannot be created from this page anyway (§2.5.1).
        hasActiveColumnFilters={activeFilters > 0}
        onResetColumnFilters={() => handleFiltersChange(EMPTY_DIARY_FILTERS)}
        mobileCardRenderer={(row) => (
          <MobileCard
            title={row.title || row.excerpt || t(`enums.diaryEntryType.${row.entry_type}`)}
            titleId="title"
            subtitle={row.created_at ? formatDateTime(row.created_at) : '—'}
            subtitleId="createdAt"
            /* The photo column is hidden below `md` on the table; on the card
               the thumbnail moves into the leading slot instead of vanishing,
               because "how many photos, and what do they look like" is half of
               why a row is worth opening (§2.5.2). */
            leading={
              row.preview_photo_id ? (
                <AuthImage
                  uri={diaryPhotoUri(row.preview_photo_id, 128)}
                  alt={t('pages.diaryOverview.photoPreviewAlt')}
                  sx={{ width: 56, height: 56, borderRadius: 1, bgcolor: 'action.hover' }}
                  data-testid="diary-photo-preview"
                />
              ) : undefined
            }
            chips={[
              {
                id: 'plant',
                content: (
                  <Chip
                    icon={<SpaIcon />}
                    label={row.plant_name || row.instance_id}
                    size="small"
                    color="success"
                    variant="outlined"
                    component={RouterLink}
                    to={`/pflanzen/plant-instances/${row.plant_key}`}
                    onClick={(e) => e.stopPropagation()}
                  />
                ),
              },
              {
                id: 'entryType',
                content: (
                  <Chip
                    size="small"
                    variant="outlined"
                    label={t(`enums.diaryEntryType.${row.entry_type}`)}
                  />
                ),
              },
              {
                id: 'analysis',
                content: (
                  <Box sx={{ display: 'inline-flex' }}>
                    <DiaryOverviewAnalysisCell
                      row={row}
                      busy={busyKey === row.key}
                      onRequestAnalysis={handleRequestAnalysis}
                    />
                  </Box>
                ),
              },
            ]}
            fields={[
              ...(row.species_name
                ? [
                    {
                      id: 'species',
                      label: t('pages.diaryOverview.columns.species'),
                      value: row.species_name,
                    },
                  ]
                : []),
              ...(row.photo_count > 0
                ? [
                    {
                      id: 'photos',
                      label: t('pages.diaryOverview.columns.photos'),
                      value: String(row.photo_count),
                    },
                  ]
                : []),
            ]}
          />
        )}
      />

      <DiaryEntryDetailDialog
        row={detailRow}
        onClose={() => setDetailRow(null)}
        onEntryChanged={applyEntry}
        onAnalysisError={reportAnalysisError}
      />
    </Box>
  );
}
