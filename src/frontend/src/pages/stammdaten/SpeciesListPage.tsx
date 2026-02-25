import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchSpeciesList } from '@/store/slices/speciesSlice';
import { usePagination } from '@/hooks/usePagination';
import type { Species } from '@/api/types';
import SpeciesCreateDialog from './SpeciesCreateDialog';

export default function SpeciesListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { items, total, loading } = useAppSelector((s) => s.species);
  const { page, rowsPerPage, offset, setPage, setRowsPerPage } = usePagination();
  const [createOpen, setCreateOpen] = useState(false);

  useEffect(() => {
    dispatch(fetchSpeciesList({ offset, limit: rowsPerPage }));
  }, [dispatch, offset, rowsPerPage]);

  const columns: Column<Species>[] = [
    {
      id: 'scientificName',
      label: t('pages.species.scientificName'),
      render: (r) => r.scientific_name,
    },
    {
      id: 'commonNames',
      label: t('pages.species.commonNames'),
      render: (r) => r.common_names.join(', '),
    },
    {
      id: 'genus',
      label: t('pages.species.genus'),
      render: (r) => r.genus,
    },
    {
      id: 'growthHabit',
      label: t('pages.species.growthHabit'),
      render: (r) => t(`enums.growthHabit.${r.growth_habit}`),
    },
    {
      id: 'rootType',
      label: t('pages.species.rootType'),
      render: (r) => t(`enums.rootType.${r.root_type}`),
    },
  ];

  return (
    <Box data-testid="species-list-page">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle title={t('pages.species.title')} />
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
          {t('pages.species.create')}
        </Button>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.species.listIntro')}
      </Typography>

      <DataTable
        columns={columns}
        rows={items}
        loading={loading}
        total={total}
        page={page}
        rowsPerPage={rowsPerPage}
        onPageChange={setPage}
        onRowsPerPageChange={setRowsPerPage}
        onRowClick={(r) => navigate(`/stammdaten/species/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.species.create')}
        onEmptyAction={() => setCreateOpen(true)}
      />

      <SpeciesCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchSpeciesList({ offset, limit: rowsPerPage }));
        }}
      />
    </Box>
  );
}
