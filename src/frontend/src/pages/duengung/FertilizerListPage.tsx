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
import { fetchFertilizers } from '@/store/slices/fertilizersSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { Fertilizer } from '@/api/types';
import FertilizerCreateDialog from './FertilizerCreateDialog';

export default function FertilizerListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { fertilizers, loading } = useAppSelector((s) => s.fertilizers);
  const [createOpen, setCreateOpen] = useState(false);
  const tableState = useTableUrlState({ defaultSort: { column: 'product_name', direction: 'asc' } });

  useEffect(() => {
    dispatch(fetchFertilizers({}));
  }, [dispatch]);

  const columns: Column<Fertilizer>[] = [
    {
      id: 'product_name',
      label: t('pages.fertilizers.productName'),
      render: (r) => r.product_name,
    },
    {
      id: 'brand',
      label: t('pages.fertilizers.brand'),
      render: (r) => r.brand || '-',
    },
    {
      id: 'fertilizer_type',
      label: t('pages.fertilizers.fertilizerType'),
      render: (r) => (
        <Chip
          label={t(`enums.fertilizerType.${r.fertilizer_type}`)}
          size="small"
          variant="outlined"
        />
      ),
      searchValue: (r) => t(`enums.fertilizerType.${r.fertilizer_type}`),
    },
    {
      id: 'npk',
      label: 'NPK',
      render: (r) => `${r.npk_ratio[0]}-${r.npk_ratio[1]}-${r.npk_ratio[2]}`,
      searchValue: (r) => `${r.npk_ratio[0]}-${r.npk_ratio[1]}-${r.npk_ratio[2]}`,
    },
    {
      id: 'ec_contribution_per_ml',
      label: t('pages.fertilizers.ecContribution'),
      render: (r) => r.ec_contribution_per_ml.toFixed(3),
      align: 'right',
      searchValue: (r) => String(r.ec_contribution_per_ml),
    },
    {
      id: 'tank_safe',
      label: t('pages.fertilizers.tankSafe'),
      render: (r) => (
        <Chip
          label={r.tank_safe ? t('common.yes') : t('common.no')}
          size="small"
          color={r.tank_safe ? 'success' : 'default'}
        />
      ),
      searchValue: (r) => (r.tank_safe ? t('common.yes') : t('common.no')),
    },
    {
      id: 'is_organic',
      label: t('pages.fertilizers.isOrganic'),
      render: (r) => (
        <Chip
          label={r.is_organic ? t('common.yes') : t('common.no')}
          size="small"
          color={r.is_organic ? 'success' : 'default'}
        />
      ),
      searchValue: (r) => (r.is_organic ? t('common.yes') : t('common.no')),
    },
  ];

  return (
    <Box data-testid="fertilizer-list-page">
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <PageTitle title={t('pages.fertilizers.title')} />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
          data-testid="create-button"
        >
          {t('pages.fertilizers.create')}
        </Button>
      </Box>
      <DataTable
        columns={columns}
        rows={fertilizers}
        loading={loading}
        onRowClick={(r) => navigate(`/duengung/fertilizers/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.fertilizers.create')}
        onEmptyAction={() => setCreateOpen(true)}
        tableState={tableState}
        ariaLabel={t('pages.fertilizers.title')}
      />
      <FertilizerCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchFertilizers({}));
        }}
      />
    </Box>
  );
}
