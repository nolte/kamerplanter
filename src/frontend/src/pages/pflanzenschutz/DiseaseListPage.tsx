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
import { fetchDiseases } from '@/store/slices/ipmSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { Disease } from '@/api/types';
import DiseaseCreateDialog from './DiseaseCreateDialog';
import { kamiIpm } from '@/assets/brand/illustrations';

type ChipColor = 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';

const pathogenTypeColor: Record<string, ChipColor> = {
  fungal: 'warning',
  bacterial: 'error',
  viral: 'secondary',
  physiological: 'info',
};

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
      render: (r) => (
        <Chip
          label={t(`enums.pathogenType.${r.pathogen_type}`)}
          size="small"
          color={pathogenTypeColor[r.pathogen_type] ?? 'default'}
        />
      ),
      searchValue: (r) => t(`enums.pathogenType.${r.pathogen_type}`),
    },
    {
      id: 'incubationPeriodDays',
      label: t('pages.ipm.incubationPeriodDays'),
      render: (r) =>
        r.incubation_period_days != null
          ? `${r.incubation_period_days}\u202f${t('pages.ipm.days')}`
          : '\u2014',
      align: 'right',
      searchValue: (r) =>
        r.incubation_period_days != null ? String(r.incubation_period_days) : '',
      hideBelowBreakpoint: 'md',
    },
  ];

  return (
    <Box data-testid="disease-list-page">
      <PageTitle
        title={t('pages.ipm.diseasesTitle')}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateOpen(true)}
            data-testid="create-button"
          >
            {t('pages.ipm.createDisease')}
          </Button>
        }
      />
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
        emptyIllustration={kamiIpm}
        tableState={tableState}
        ariaLabel={t('pages.ipm.diseasesTitle')}
        mobileCardRenderer={(r) => (
          <MobileCard
            title={r.scientific_name}
            subtitle={r.common_name}
            chips={
              <Chip
                label={t(`enums.pathogenType.${r.pathogen_type}`)}
                size="small"
                color={pathogenTypeColor[r.pathogen_type] ?? 'default'}
              />
            }
            fields={[
              ...(r.incubation_period_days != null
                ? [{ label: t('pages.ipm.incubationPeriodDays'), value: `${r.incubation_period_days}\u202f${t('pages.ipm.days')}` }]
                : []),
            ]}
          />
        )}
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
