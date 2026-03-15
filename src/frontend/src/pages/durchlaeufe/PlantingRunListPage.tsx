import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';
import AddIcon from '@mui/icons-material/Add';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchPlantingRuns } from '@/store/slices/plantingRunsSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { PlantingRun, PlantingRunStatus } from '@/api/types';
import PlantingRunCreateDialog from './PlantingRunCreateDialog';
import { kamiPlantingRuns } from '@/assets/brand/illustrations';

const statusColor: Record<PlantingRunStatus, ChipProps['color']> = {
  planned: 'default',
  active: 'primary',
  harvesting: 'warning',
  completed: 'success',
  cancelled: 'error',
};

export default function PlantingRunListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { runs, loading } = useAppSelector((s) => s.plantingRuns);
  const [createOpen, setCreateOpen] = useState(false);
  const tableState = useTableUrlState({ defaultSort: { column: 'name', direction: 'asc' } });

  useEffect(() => {
    dispatch(fetchPlantingRuns({}));
  }, [dispatch]);

  const columns: Column<PlantingRun>[] = [
    { id: 'name', label: t('pages.plantingRuns.name'), render: (r) => r.name },
    {
      id: 'runType',
      label: t('pages.plantingRuns.runType'),
      render: (r) => t(`enums.plantingRunType.${r.run_type}`),
    },
    {
      id: 'status',
      label: t('pages.plantingRuns.status'),
      render: (r) => (
        <Chip
          label={t(`enums.plantingRunStatus.${r.status}`)}
          size="small"
          color={statusColor[r.status] ?? 'default'}
          data-testid={`status-chip-${r.key}`}
        />
      ),
      searchValue: (r) => t(`enums.plantingRunStatus.${r.status}`),
    },
    {
      id: 'phase',
      label: t('pages.plantingRuns.currentPhase'),
      render: (r) => {
        if (!r.phase_summary || r.status === 'planned') return '\u2014';
        const { dominant_phase, dominant_phase_count, total_plant_count } = r.phase_summary;
        if (!dominant_phase) return '\u2014';
        return (
          <Chip
            label={`${t(`enums.phase.${dominant_phase}`, dominant_phase)} (${dominant_phase_count}/${total_plant_count})`}
            size="small"
            color="info"
          />
        );
      },
      searchValue: (r) => r.phase_summary?.dominant_phase ?? '',
    },
    {
      id: 'plannedQty',
      label: t('pages.plantingRuns.plannedQuantity'),
      render: (r) => r.planned_quantity,
      align: 'right',
    },
    {
      id: 'actualQty',
      label: t('pages.plantingRuns.actualQuantity'),
      render: (r) => r.actual_quantity,
      align: 'right',
    },
    {
      id: 'startedAt',
      label: t('pages.plantingRuns.startedAt'),
      render: (r) => (r.started_at ? new Date(r.started_at).toLocaleDateString() : '\u2014'),
    },
  ];

  return (
    <Box data-testid="planting-run-list-page">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle title={t('pages.plantingRuns.title')} />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
          data-testid="create-button"
        >
          {t('pages.plantingRuns.create')}
        </Button>
      </Box>
      <DataTable
        columns={columns}
        rows={runs}
        loading={loading}
        onRowClick={(r) => navigate(`/durchlaeufe/planting-runs/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.plantingRuns.create')}
        onEmptyAction={() => setCreateOpen(true)}
        emptyIllustration={kamiPlantingRuns}
        tableState={tableState}
        ariaLabel={t('pages.plantingRuns.title')}
      />
      <PlantingRunCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchPlantingRuns({}));
        }}
      />
    </Box>
  );
}
