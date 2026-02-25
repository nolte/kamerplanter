import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import AddIcon from '@mui/icons-material/Add';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchPlantInstances } from '@/store/slices/plantInstancesSlice';
import type { PlantInstance } from '@/api/types';
import PlantInstanceCreateDialog from './PlantInstanceCreateDialog';

export default function PlantInstanceListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { items, loading } = useAppSelector((s) => s.plantInstances);
  const [createOpen, setCreateOpen] = useState(false);

  useEffect(() => {
    dispatch(fetchPlantInstances({}));
  }, [dispatch]);

  const columns: Column<PlantInstance>[] = [
    { id: 'instanceId', label: t('pages.plantInstances.instanceId'), render: (r) => r.instance_id },
    { id: 'plantName', label: t('pages.plantInstances.plantName'), render: (r) => r.plant_name ?? '-' },
    { id: 'plantedOn', label: t('pages.plantInstances.plantedOn'), render: (r) => r.planted_on },
    {
      id: 'currentPhase',
      label: t('pages.plantInstances.currentPhase'),
      render: (r) => <Chip label={r.current_phase} size="small" color="primary" />,
    },
    {
      id: 'removedOn',
      label: t('pages.plantInstances.removedOn'),
      render: (r) => r.removed_on ?? '-',
    },
  ];

  return (
    <Box data-testid="plant-instance-list-page">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle title={t('pages.plantInstances.title')} />
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)} data-testid="create-button">
          {t('pages.plantInstances.create')}
        </Button>
      </Box>
      <DataTable
        columns={columns}
        rows={items}
        loading={loading}
        onRowClick={(r) => navigate(`/pflanzen/plant-instances/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.plantInstances.create')}
        onEmptyAction={() => setCreateOpen(true)}
      />
      <PlantInstanceCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => { setCreateOpen(false); dispatch(fetchPlantInstances({})); }}
      />
    </Box>
  );
}
