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
import { fetchBotanicalFamilies } from '@/store/slices/botanicalFamiliesSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { BotanicalFamily } from '@/api/types';
import BotanicalFamilyCreateDialog from './BotanicalFamilyCreateDialog';

export default function BotanicalFamilyListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { items, loading } = useAppSelector((s) => s.botanicalFamilies);
  const [createOpen, setCreateOpen] = useState(false);
  const tableState = useTableUrlState({ defaultSort: { column: 'name', direction: 'asc' } });

  useEffect(() => {
    dispatch(fetchBotanicalFamilies({}));
  }, [dispatch]);

  const columns: Column<BotanicalFamily>[] = [
    { id: 'name', label: t('pages.botanicalFamilies.name'), render: (r) => r.name },
    {
      id: 'commonNameDe',
      label: t('pages.botanicalFamilies.commonNameDe'),
      render: (r) => r.common_name_de,
    },
    {
      id: 'nutrientDemand',
      label: t('pages.botanicalFamilies.nutrientDemand'),
      render: (r) => t(`enums.nutrientDemand.${r.typical_nutrient_demand}`),
      searchValue: (r) => t(`enums.nutrientDemand.${r.typical_nutrient_demand}`),
    },
    {
      id: 'frostTolerance',
      label: t('pages.botanicalFamilies.frostTolerance'),
      render: (r) => t(`enums.frostTolerance.${r.frost_tolerance}`),
      searchValue: (r) => t(`enums.frostTolerance.${r.frost_tolerance}`),
    },
    {
      id: 'rootDepth',
      label: t('pages.botanicalFamilies.rootDepth'),
      render: (r) => t(`enums.rootDepth.${r.typical_root_depth}`),
      searchValue: (r) => t(`enums.rootDepth.${r.typical_root_depth}`),
    },
    {
      id: 'rotationCategory',
      label: t('pages.botanicalFamilies.rotationCategory'),
      render: (r) => r.rotation_category,
    },
  ];

  return (
    <Box data-testid="botanical-family-list-page">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle title={t('pages.botanicalFamilies.title')} />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
          data-testid="create-button"
        >
          {t('pages.botanicalFamilies.create')}
        </Button>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.botanicalFamilies.listIntro')}
      </Typography>

      <DataTable
        columns={columns}
        rows={items}
        loading={loading}
        onRowClick={(r) => navigate(`/stammdaten/botanical-families/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.botanicalFamilies.create')}
        onEmptyAction={() => setCreateOpen(true)}
        tableState={tableState}
        ariaLabel={t('pages.botanicalFamilies.title')}
      />

      <BotanicalFamilyCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchBotanicalFamilies({}));
        }}
      />
    </Box>
  );
}
