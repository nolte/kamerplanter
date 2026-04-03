import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import MobileCard from '@/components/common/MobileCard';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchTreatments } from '@/store/slices/ipmSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { Treatment } from '@/api/types';
import TreatmentCreateDialog from './TreatmentCreateDialog';
import { kamiIpm } from '@/assets/brand/illustrations';

type ChipColor = 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';

const treatmentTypeColor: Record<string, ChipColor> = {
  chemical: 'error',
  biological: 'success',
  cultural: 'info',
  mechanical: 'default',
};

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
      render: (r) => (
        <Chip
          label={t(`enums.treatmentType.${r.treatment_type}`)}
          size="small"
          color={treatmentTypeColor[r.treatment_type] ?? 'default'}
        />
      ),
      searchValue: (r) => t(`enums.treatmentType.${r.treatment_type}`),
    },
    {
      id: 'activeIngredient',
      label: t('pages.ipm.activeIngredient'),
      render: (r) => r.active_ingredient ?? '\u2014',
      hideBelowBreakpoint: 'md',
    },
    {
      id: 'safetyIntervalDays',
      label: t('pages.ipm.safetyIntervalDays'),
      render: (r) =>
        r.safety_interval_days > 0 ? (
          <Chip
            label={`${r.safety_interval_days}\u202f${t('pages.ipm.days')}`}
            size="small"
            color="warning"
            variant="outlined"
          />
        ) : '\u2014',
      align: 'right',
      searchValue: (r) =>
        r.safety_interval_days > 0 ? String(r.safety_interval_days) : '',
    },
    {
      id: 'applicationMethod',
      label: t('pages.ipm.applicationMethod'),
      render: (r) => t(`enums.ipmApplicationMethod.${r.application_method}`),
      searchValue: (r) => t(`enums.ipmApplicationMethod.${r.application_method}`),
      hideBelowBreakpoint: 'md',
    },
  ];

  return (
    <Box data-testid="treatment-list-page">
      <PageTitle
        title={t('pages.ipm.treatmentsTitle')}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateOpen(true)}
            data-testid="create-button"
          >
            {t('pages.ipm.createTreatment')}
          </Button>
        }
      />
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
        emptyIllustration={kamiIpm}
        tableState={tableState}
        ariaLabel={t('pages.ipm.treatmentsTitle')}
        mobileCardRenderer={(r) => (
          <MobileCard
            title={r.name}
            subtitle={r.active_ingredient ?? undefined}
            chips={
              <Chip
                label={t(`enums.treatmentType.${r.treatment_type}`)}
                size="small"
                color={treatmentTypeColor[r.treatment_type] ?? 'default'}
              />
            }
            fields={[
              { label: t('pages.ipm.applicationMethod'), value: t(`enums.ipmApplicationMethod.${r.application_method}`) },
              ...(r.safety_interval_days > 0
                ? [{ label: t('pages.ipm.safetyIntervalDays'), value: `${r.safety_interval_days}\u202f${t('pages.ipm.days')}` }]
                : []),
            ]}
          />
        )}
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
