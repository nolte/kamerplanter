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
import type { PlantingRun, PlantingRunStatus } from '@/api/types';
import PlantingRunCreateDialog from './PlantingRunCreateDialog';

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
        />
      ),
    },
    {
      id: 'plannedQty',
      label: t('pages.plantingRuns.plannedQuantity'),
      render: (r) => r.planned_quantity,
    },
    {
      id: 'actualQty',
      label: t('pages.plantingRuns.actualQuantity'),
      render: (r) => r.actual_quantity,
    },
    {
      id: 'startedAt',
      label: t('pages.plantingRuns.startedAt'),
      render: (r) => (r.started_at ? new Date(r.started_at).toLocaleDateString() : '-'),
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
