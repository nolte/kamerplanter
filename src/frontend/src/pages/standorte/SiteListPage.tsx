import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import AddIcon from '@mui/icons-material/Add';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchSites } from '@/store/slices/sitesSlice';
import type { Site } from '@/api/types';
import SiteCreateDialog from './SiteCreateDialog';

export default function SiteListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { sites, loading } = useAppSelector((s) => s.sites);
  const [createOpen, setCreateOpen] = useState(false);

  useEffect(() => {
    dispatch(fetchSites({}));
  }, [dispatch]);

  const columns: Column<Site>[] = [
    { id: 'name', label: t('pages.sites.name'), render: (r) => r.name },
    { id: 'type', label: t('pages.sites.type'), render: (r) => t(`enums.siteType.${r.type}`) },
    { id: 'area', label: t('pages.sites.totalArea'), render: (r) => `${r.total_area_m2} m²` },
    { id: 'climate', label: t('pages.sites.climateZone'), render: (r) => r.climate_zone },
  ];

  return (
    <Box data-testid="site-list-page">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle title={t('pages.sites.title')} />
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)} data-testid="create-button">
          {t('pages.sites.create')}
        </Button>
      </Box>
      <DataTable
        columns={columns}
        rows={sites}
        loading={loading}
        onRowClick={(r) => navigate(`/standorte/sites/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.sites.create')}
        onEmptyAction={() => setCreateOpen(true)}
      />
      <SiteCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => { setCreateOpen(false); dispatch(fetchSites({})); }}
      />
    </Box>
  );
}
