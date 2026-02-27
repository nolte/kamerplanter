import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchDiseases } from '@/store/slices/ipmSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { Disease } from '@/api/types';
import DiseaseCreateDialog from './DiseaseCreateDialog';

export default function DiseaseListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { diseases, loading } = useAppSelector((s) => s.ipm);
  const [createOpen, setCreateOpen] = useState(false);
  const tableState = useTableUrlState({
    defaultSort: { column: 'scientificName', direction: 'asc' },
  });

  useEffect(() => {
    dispatch(fetchDiseases({}));
  }, [dispatch]);

  const columns: Column<Disease>[] = [
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
      id: 'pathogenType',
      label: t('pages.ipm.pathogenType'),
      render: (r) => t(`enums.pathogenType.${r.pathogen_type}`),
      searchValue: (r) => t(`enums.pathogenType.${r.pathogen_type}`),
    },
    {
      id: 'incubationPeriodDays',
      label: t('pages.ipm.incubationPeriodDays'),
      render: (r) =>
        r.incubation_period_days != null
          ? `${r.incubation_period_days} ${t('pages.ipm.days')}`
          : '—',
      align: 'right',
      searchValue: (r) =>
        r.incubation_period_days != null ? String(r.incubation_period_days) : '',
    },
  ];

  return (
    <Box data-testid="disease-list-page">
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <PageTitle title={t('pages.ipm.diseasesTitle')} />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
          data-testid="create-button"
        >
          {t('pages.ipm.createDisease')}
        </Button>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.ipm.diseaseListIntro')}
      </Typography>
      <DataTable
        columns={columns}
        rows={diseases}
        loading={loading}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.ipm.createDisease')}
        onEmptyAction={() => setCreateOpen(true)}
        tableState={tableState}
        ariaLabel={t('pages.ipm.diseasesTitle')}
      />
      <DiseaseCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchDiseases({}));
        }}
      />
    </Box>
  );
}
