import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import AddIcon from '@mui/icons-material/Add';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchTanks } from '@/store/slices/tanksSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { Tank } from '@/api/types';
import TankCreateDialog from './TankCreateDialog';
import { kamiTanks } from '@/assets/brand/illustrations';

export default function TankListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { tanks, loading } = useAppSelector((s) => s.tanks);
  const [createOpen, setCreateOpen] = useState(false);
  const tableState = useTableUrlState({ defaultSort: { column: 'name', direction: 'asc' } });

  useEffect(() => {
    dispatch(fetchTanks({}));
  }, [dispatch]);

  const columns: Column<Tank>[] = [
    { id: 'name', label: t('pages.tanks.name'), render: (r) => r.name },
    {
      id: 'tankType',
      label: t('pages.tanks.tankType'),
      render: (r) => t(`enums.tankType.${r.tank_type}`),
      searchValue: (r) => t(`enums.tankType.${r.tank_type}`),
    },
    {
      id: 'volume',
      label: t('pages.tanks.volumeLiters'),
      render: (r) => `${r.volume_liters} L`,
      align: 'right',
      searchValue: (r) => String(r.volume_liters),
    },
    {
      id: 'material',
      label: t('pages.tanks.material'),
      render: (r) => t(`enums.tankMaterial.${r.material}`),
      searchValue: (r) => t(`enums.tankMaterial.${r.material}`),
    },
  ];

  return (
    <Box data-testid="tank-list-page">
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <PageTitle title={t('pages.tanks.title')} />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
          data-testid="create-button"
        >
          {t('pages.tanks.create')}
        </Button>
      </Box>
      <DataTable
        columns={columns}
        rows={tanks}
        loading={loading}
        onRowClick={(r) => navigate(`/standorte/tanks/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.tanks.create')}
        onEmptyAction={() => setCreateOpen(true)}
        emptyIllustration={kamiTanks}
        tableState={tableState}
        ariaLabel={t('pages.tanks.title')}
      />
      <TankCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchTanks({}));
        }}
      />
    </Box>
  );
}
