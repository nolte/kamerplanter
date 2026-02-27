import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchTreatments } from '@/store/slices/ipmSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { Treatment } from '@/api/types';
import TreatmentCreateDialog from './TreatmentCreateDialog';

export default function TreatmentListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { treatments, loading } = useAppSelector((s) => s.ipm);
  const [createOpen, setCreateOpen] = useState(false);
  const tableState = useTableUrlState({
    defaultSort: { column: 'name', direction: 'asc' },
  });

  useEffect(() => {
    dispatch(fetchTreatments({}));
  }, [dispatch]);

  const columns: Column<Treatment>[] = [
    {
      id: 'name',
      label: t('pages.ipm.treatmentName'),
      render: (r) => r.name,
    },
    {
      id: 'treatmentType',
      label: t('pages.ipm.treatmentType'),
      render: (r) => t(`enums.treatmentType.${r.treatment_type}`),
      searchValue: (r) => t(`enums.treatmentType.${r.treatment_type}`),
    },
    {
      id: 'activeIngredient',
      label: t('pages.ipm.activeIngredient'),
      render: (r) => r.active_ingredient ?? '—',
    },
    {
      id: 'safetyIntervalDays',
      label: t('pages.ipm.safetyIntervalDays'),
      render: (r) =>
        r.safety_interval_days > 0
          ? `${r.safety_interval_days} ${t('pages.ipm.days')}`
          : '—',
      align: 'right',
      searchValue: (r) =>
        r.safety_interval_days > 0 ? String(r.safety_interval_days) : '',
    },
    {
      id: 'applicationMethod',
      label: t('pages.ipm.applicationMethod'),
      render: (r) => t(`enums.ipmApplicationMethod.${r.application_method}`),
      searchValue: (r) => t(`enums.ipmApplicationMethod.${r.application_method}`),
    },
  ];

  return (
    <Box data-testid="treatment-list-page">
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <PageTitle title={t('pages.ipm.treatmentsTitle')} />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
          data-testid="create-button"
        >
          {t('pages.ipm.createTreatment')}
        </Button>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.ipm.treatmentListIntro')}
      </Typography>
      <DataTable
        columns={columns}
        rows={treatments}
        loading={loading}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.ipm.createTreatment')}
        onEmptyAction={() => setCreateOpen(true)}
        tableState={tableState}
        ariaLabel={t('pages.ipm.treatmentsTitle')}
      />
      <TreatmentCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchTreatments({}));
        }}
      />
    </Box>
  );
}
