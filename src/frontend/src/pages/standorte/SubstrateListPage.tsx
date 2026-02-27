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
import { fetchSubstrates } from '@/store/slices/substratesSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { Substrate } from '@/api/types';
import SubstrateCreateDialog from './SubstrateCreateDialog';

export default function SubstrateListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { items, loading } = useAppSelector((s) => s.substrates);
  const [createOpen, setCreateOpen] = useState(false);
  const tableState = useTableUrlState({ defaultSort: { column: 'type', direction: 'asc' } });

  useEffect(() => {
    dispatch(fetchSubstrates({}));
  }, [dispatch]);

  const columns: Column<Substrate>[] = [
    { id: 'type', label: t('pages.substrates.type'), render: (r) => t(`enums.substrateType.${r.type}`), searchValue: (r) => t(`enums.substrateType.${r.type}`) },
    { id: 'brand', label: t('pages.substrates.brand'), render: (r) => r.brand ?? '-' },
    { id: 'ph', label: t('pages.substrates.phBase'), render: (r) => r.ph_base.toFixed(1), align: 'right', searchValue: (r) => r.ph_base.toFixed(1) },
    { id: 'ec', label: t('pages.substrates.ecBase'), render: (r) => r.ec_base_ms.toFixed(2), align: 'right', searchValue: (r) => r.ec_base_ms.toFixed(2) },
    {
      id: 'reusable',
      label: t('pages.substrates.reusable'),
      render: (r) => (
        <Chip label={r.reusable ? t('common.yes') : t('common.no')} size="small" color={r.reusable ? 'success' : 'default'} />
      ),
      searchValue: (r) => r.reusable ? t('common.yes') : t('common.no'),
    },
  ];

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle title={t('pages.substrates.title')} />
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
          {t('pages.substrates.create')}
        </Button>
      </Box>
      <DataTable
        columns={columns}
        rows={items}
        loading={loading}
        onRowClick={(r) => navigate(`/standorte/substrates/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.substrates.create')}
        onEmptyAction={() => setCreateOpen(true)}
        tableState={tableState}
        ariaLabel={t('pages.substrates.title')}
      />
      <SubstrateCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => { setCreateOpen(false); dispatch(fetchSubstrates({})); }}
      />
    </>
  );
}
