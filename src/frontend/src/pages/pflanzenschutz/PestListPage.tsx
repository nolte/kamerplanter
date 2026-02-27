import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchPests } from '@/store/slices/ipmSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { Pest } from '@/api/types';
import PestCreateDialog from './PestCreateDialog';

export default function PestListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { pests, loading } = useAppSelector((s) => s.ipm);
  const [createOpen, setCreateOpen] = useState(false);
  const tableState = useTableUrlState({
    defaultSort: { column: 'scientificName', direction: 'asc' },
  });

  useEffect(() => {
    dispatch(fetchPests({}));
  }, [dispatch]);

  const columns: Column<Pest>[] = [
    {
      id: 'scientificName',
      label: t('pages.ipm.scientificName'),
      render: (r) => r.scientific_name,
    },
    {
      id: 'commonName',
      label: t('pages.ipm.commonName'),
      render: (r) => r.common_name,
    },
    {
      id: 'pestType',
      label: t('pages.ipm.pestType'),
      render: (r) => t(`enums.pestType.${r.pest_type}`),
      searchValue: (r) => t(`enums.pestType.${r.pest_type}`),
    },
    {
      id: 'lifecycleDays',
      label: t('pages.ipm.lifecycleDays'),
      render: (r) =>
        r.lifecycle_days != null ? `${r.lifecycle_days} ${t('pages.ipm.days')}` : '—',
      align: 'right',
      searchValue: (r) => (r.lifecycle_days != null ? String(r.lifecycle_days) : ''),
    },
    {
      id: 'detectionDifficulty',
      label: t('pages.ipm.detectionDifficulty'),
      render: (r) => t(`enums.detectionDifficulty.${r.detection_difficulty}`),
      searchValue: (r) => t(`enums.detectionDifficulty.${r.detection_difficulty}`),
    },
  ];

  return (
    <Box data-testid="pest-list-page">
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <PageTitle title={t('pages.ipm.pestsTitle')} />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
          data-testid="create-button"
        >
          {t('pages.ipm.createPest')}
        </Button>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.ipm.pestListIntro')}
      </Typography>
      <DataTable
        columns={columns}
        rows={pests}
        loading={loading}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.ipm.createPest')}
        onEmptyAction={() => setCreateOpen(true)}
        tableState={tableState}
        ariaLabel={t('pages.ipm.pestsTitle')}
      />
      <PestCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchPests({}));
        }}
      />
    </Box>
  );
}
