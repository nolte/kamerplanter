/**
 * The bed list of a site (REQ-053 GP-FR-042, GP-FR-050, GP-API-011): name, type, area, status, who is
 * responsible, active plants, open tasks and the next due date. A click (or Enter) on a row selects
 * the bed on the plan and brings it into view (GP-ACC-016); the name links to the bed view. "My
 * beds" narrows the list to the beds assigned to the signed-in user.
 */
import { lazy, Suspense, useEffect, useMemo, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import FormControlLabel from '@mui/material/FormControlLabel';
import Link from '@mui/material/Link';
import MenuItem from '@mui/material/MenuItem';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import DataTable, { type Column } from '@/components/common/DataTable';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import MobileCard from '@/components/common/MobileCard';
import { parseApiError } from '@/api/errors';
import { useTableLocalState } from '@/hooks/useTableState';
import { useTenantPermissions } from '@/hooks/useTenantPermissions';
import type { BedStatus } from '../model/types';
import { listBeds } from './bedApi';
import { BED_STATUS_COLOR, formatBedDate, isOverdue } from './bedFormat';
import type { BedListItem } from './types';
import { useBedAssignments } from './useBedAssignments';
import { useLocationTypeNames } from './useLocationTypeNames';

// The batch dialog (GP-FR-088) is rare; it loads when it is opened.
const BatchCompleteDialog = lazy(() => import('../care/BatchCompleteDialog'));

type StatusFilter = 'open' | 'all' | BedStatus;

interface BedListSectionProps {
  siteKey: string;
  /** Changes whenever the plan was reloaded, so the counters follow. */
  reloadToken: string | null;
  /** The row was chosen: select the bed on the plan and bring it into view. */
  onSelectBed: (bed: BedListItem) => void;
}

type ListState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; beds: BedListItem[] };

function count(value: number | null | undefined): number {
  return value ?? 0;
}

export default function BedListSection({ siteKey, reloadToken, onSelectBed }: BedListSectionProps) {
  const { t, i18n } = useTranslation();
  const language = i18n.language;
  const tableState = useTableLocalState({ defaultSort: { column: 'name', direction: 'asc' } });
  const typeNames = useLocationTypeNames();
  const assignments = useBedAssignments(true);
  const [state, setState] = useState<ListState>({ status: 'loading' });
  const [attempt, setAttempt] = useState(0);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('open');
  const [onlyMine, setOnlyMine] = useState(false);
  const { canEdit } = useTenantPermissions();
  const [batchOpen, setBatchOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    listBeds(siteKey)
      .then((beds) => {
        if (!cancelled) setState({ status: 'ready', beds });
      })
      .catch((error: unknown) => {
        if (!cancelled) setState({ status: 'error', message: parseApiError(error) });
      });
    return () => {
      cancelled = true;
    };
  }, [siteKey, reloadToken, attempt]);

  const beds = state.status === 'ready' ? state.beds : null;
  const rows = useMemo(() => {
    if (beds === null) return [];
    return beds.filter((bed) => {
      if (statusFilter === 'open' && bed.bed_status === 'retired') return false;
      if (statusFilter !== 'open' && statusFilter !== 'all' && bed.bed_status !== statusFilter) return false;
      return !onlyMine || assignments.mine.has(bed.key);
    });
  }, [beds, statusFilter, onlyMine, assignments.mine]);

  const typeName = (bed: BedListItem) => typeNames.get(bed.location_type_key) ?? bed.location_type_key;
  const area = (bed: BedListItem) =>
    `${new Intl.NumberFormat(language, { maximumFractionDigits: 2 }).format(bed.area_m2)} m²`;
  const assignedNames = (bed: BedListItem) =>
    (assignments.byLocation.get(bed.key) ?? []).map((person) => person.displayName).join(', ');
  const due = (bed: BedListItem) => formatBedDate(bed.next_due_at, language) ?? '';

  const columns: Column<BedListItem>[] = [
    {
      id: 'name',
      label: t('pages.bed.list.name'),
      searchValue: (bed) => bed.name,
      render: (bed) => (
        <Link
          component={RouterLink}
          to={`/standorte/locations/${bed.key}`}
          onClick={(event) => event.stopPropagation()}
          data-testid={`bed-list-link-${bed.key}`}
        >
          {bed.name}
        </Link>
      ),
    },
    { id: 'type', label: t('pages.bed.list.type'), render: typeName, searchValue: typeName, hideBelowBreakpoint: 'md' },
    {
      id: 'area',
      label: t('pages.bed.list.area'),
      render: area,
      searchValue: (bed) => String(bed.area_m2),
      align: 'right',
    },
    {
      id: 'status',
      label: t('pages.bed.list.status'),
      searchValue: (bed) => t(`enums.bedStatus.${bed.bed_status}`),
      render: (bed) => (
        <Chip size="small" color={BED_STATUS_COLOR[bed.bed_status]} label={t(`enums.bedStatus.${bed.bed_status}`)} />
      ),
    },
    {
      id: 'assigned',
      label: t('pages.bed.list.assigned'),
      render: (bed) => assignedNames(bed) || '—',
      searchValue: assignedNames,
      hideBelowBreakpoint: 'lg',
    },
    {
      id: 'plants',
      label: t('pages.bed.list.plants'),
      render: (bed) => count(bed.active_plant_count),
      searchValue: (bed) => String(count(bed.active_plant_count)),
      align: 'right',
    },
    {
      id: 'tasks',
      label: t('pages.bed.list.tasks'),
      searchValue: (bed) => String(count(bed.open_task_count)),
      align: 'right',
      render: (bed) => {
        const overdue = count(bed.overdue_task_count) > 0;
        const visible = overdue
          ? t('pages.bed.list.tasksOverdue', { open: count(bed.open_task_count), overdue: count(bed.overdue_task_count) })
          : String(count(bed.open_task_count));
        return (
          <Link
            component={RouterLink}
            to={`/standorte/locations/${bed.key}#care`}
            color={overdue ? 'error' : 'inherit'}
            variant="body2"
            onClick={(event) => event.stopPropagation()}
            aria-label={t('pages.bed.list.careLink', { tasks: visible, name: bed.name })}
            sx={{ display: 'inline-block', minHeight: 24 }}
            data-testid={`bed-list-care-${bed.key}`}
          >
            {visible}
          </Link>
        );
      },
    },
    {
      id: 'nextDue',
      label: t('pages.bed.list.nextDue'),
      searchValue: due,
      sortFn: (a, b) => (a.next_due_at ?? '').localeCompare(b.next_due_at ?? ''),
      render: (bed) => (
        <Typography component="span" variant="body2" color={isOverdue(bed.next_due_at) ? 'error' : 'inherit'}>
          {due(bed) || '—'}
        </Typography>
      ),
      hideBelowBreakpoint: 'md',
    },
  ];

  return (
    <Box component="section" aria-labelledby="bed-list-heading" sx={{ mt: 3 }} data-testid="bed-list-section">
      <Box sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 2, mb: 1 }}>
        <Typography id="bed-list-heading" variant="h6" component="h2" sx={{ flexGrow: 1 }}>
          {t('pages.bed.list.title')}
        </Typography>
        <TextField
          select
          size="small"
          label={t('pages.bed.list.statusFilter')}
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
          sx={{ minWidth: 180, '& .MuiInputBase-root': { minHeight: 44 } }}
          slotProps={{ htmlInput: { 'data-testid': 'bed-list-status-filter' } }}
        >
          <MenuItem value="open">{t('pages.bed.list.filterOpen')}</MenuItem>
          <MenuItem value="all">{t('pages.bed.list.filterAll')}</MenuItem>
          {(['planned', 'active', 'retired'] as const).map((status) => (
            <MenuItem key={status} value={status}>
              {t(`enums.bedStatus.${status}`)}
            </MenuItem>
          ))}
        </TextField>
        <FormControlLabel
          control={
            <Switch
              checked={onlyMine}
              onChange={(event) => setOnlyMine(event.target.checked)}
              disabled={!assignments.ready || assignments.mine.size === 0}
              data-testid="bed-list-only-mine"
            />
          }
          label={t('pages.bed.list.onlyMine')}
        />
        {canEdit && (
          <Button
            variant="outlined"
            onClick={() => setBatchOpen(true)}
            disabled={rows.length === 0}
            sx={{ minHeight: 44 }}
            data-testid="bed-list-batch"
          >
            {t('pages.bed.list.batchOpen')}
          </Button>
        )}
        {assignments.ready && assignments.mine.size === 0 && (
          <Typography variant="caption" color="text.secondary" data-testid="bed-list-only-mine-hint">
            {t('pages.bed.list.onlyMineNone')}
          </Typography>
        )}
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {t('pages.bed.list.hint')}
      </Typography>
      {state.status === 'error' ? (
        <ErrorDisplay error={state.message} onRetry={() => setAttempt((value) => value + 1)} />
      ) : (
        <DataTable<BedListItem>
          columns={columns}
          rows={rows}
          loading={state.status === 'loading'}
          getRowKey={(bed) => bed.key}
          onRowClick={onSelectBed}
          tableState={tableState}
          ariaLabel={t('pages.bed.list.title')}
          sectionTestId="bed-list"
          emptyMessage={t('pages.bed.list.empty')}
          emptyDescription={t('pages.bed.list.emptyDescription')}
          hasActiveColumnFilters={statusFilter !== 'open' || onlyMine}
          onResetColumnFilters={() => {
            setStatusFilter('open');
            setOnlyMine(false);
          }}
          mobileCardRenderer={(bed) => (
            <MobileCard
              title={
                <Link
                  component={RouterLink}
                  to={`/standorte/locations/${bed.key}`}
                  onClick={(event) => event.stopPropagation()}
                  data-testid={`bed-list-link-${bed.key}`}
                  sx={{ display: 'inline-block', py: 1 }}
                >
                  {bed.name}
                </Link>
              }
              titleId="name"
              subtitle={typeName(bed)}
              subtitleId="type"
              chips={[
                {
                  id: 'status',
                  content: (
                    <Chip
                      size="small"
                      color={BED_STATUS_COLOR[bed.bed_status]}
                      label={t(`enums.bedStatus.${bed.bed_status}`)}
                    />
                  ),
                },
              ]}
              fields={[
                { id: 'area', label: t('pages.bed.list.area'), value: area(bed) },
                { id: 'plants', label: t('pages.bed.list.plants'), value: String(count(bed.active_plant_count)) },
                {
                  id: 'tasks',
                  label: t('pages.bed.list.tasks'),
                  value:
                    count(bed.overdue_task_count) > 0
                      ? t('pages.bed.list.tasksOverdue', {
                          open: count(bed.open_task_count),
                          overdue: count(bed.overdue_task_count),
                        })
                      : String(count(bed.open_task_count)),
                },
              ]}
            />
          )}
        />
      )}
      {batchOpen && (
        <Suspense fallback={null}>
          <BatchCompleteDialog
            beds={rows.filter((bed) => bed.bed_status !== 'retired')}
            onClose={() => setBatchOpen(false)}
            onChanged={() => setAttempt((value) => value + 1)}
          />
        </Suspense>
      )}
    </Box>
  );
}
