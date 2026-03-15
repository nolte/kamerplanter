import { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import AddIcon from '@mui/icons-material/Add';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import FilterListIcon from '@mui/icons-material/FilterList';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchSubstrates } from '@/store/slices/substratesSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { Substrate } from '@/api/types';
import SubstrateCreateDialog from './SubstrateCreateDialog';
import SubstrateMixDialog from './SubstrateMixDialog';
import { kamiLocations } from '@/assets/brand/illustrations';
import BlenderIcon from '@mui/icons-material/Blender';
import { useLocalFavorites } from '@/hooks/useLocalFavorites';

export default function SubstrateListPage() {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { items, loading } = useAppSelector((s) => s.substrates);
  const [createOpen, setCreateOpen] = useState(false);
  const [mixOpen, setMixOpen] = useState(false);
  const [favFilterActive, setFavFilterActive] = useState(false);
  const { isFavorite, toggleFavorite, hasFavorites } = useLocalFavorites('kamerplanter-substrate-favorites');
  const tableState = useTableUrlState({ defaultSort: { column: 'type', direction: 'asc' } });

  useEffect(() => {
    dispatch(fetchSubstrates({}));
  }, [dispatch]);

  const lang = i18n.language?.startsWith('en') ? 'en' : 'de';

  const filteredItems = useMemo(
    () => favFilterActive && hasFavorites ? items.filter((s) => isFavorite(s.key)) : items,
    [items, favFilterActive, hasFavorites, isFavorite],
  );

  const columns: Column<Substrate>[] = [
    {
      id: 'favorite',
      label: '',
      sortable: false,
      searchable: false,
      render: (r) => (
        <IconButton
          size="small"
          onClick={(e) => { e.stopPropagation(); toggleFavorite(r.key); }}
          sx={{ color: isFavorite(r.key) ? 'warning.main' : 'action.disabled' }}
        >
          {isFavorite(r.key) ? <StarIcon fontSize="small" /> : <StarBorderIcon fontSize="small" />}
        </IconButton>
      ),
    },
    {
      id: 'type',
      label: t('pages.substrates.type'),
      render: (r) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          {t(`enums.substrateType.${r.type}`)}
          {r.is_mix && <Chip label={t('pages.substrates.mix')} size="small" color="info" variant="outlined" />}
        </Box>
      ),
      searchValue: (r) => t(`enums.substrateType.${r.type}`),
    },
    {
      id: 'name',
      label: t('pages.substrates.name'),
      render: (r) => (lang === 'en' ? r.name_en : r.name_de) || r.brand || '\u2014',
      searchValue: (r) => `${r.name_de} ${r.name_en} ${r.brand ?? ''}`,
    },
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
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {hasFavorites && (
            <Tooltip title={t('pages.plantInstances.substrateFavFilter')}>
              <IconButton
                onClick={() => setFavFilterActive((p) => !p)}
                color={favFilterActive ? 'warning' : 'default'}
              >
                <FilterListIcon />
              </IconButton>
            </Tooltip>
          )}
          <Button variant="outlined" startIcon={<BlenderIcon />} onClick={() => setMixOpen(true)}>
            {t('pages.substrates.createMix')}
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
            {t('pages.substrates.create')}
          </Button>
        </Box>
      </Box>
      <DataTable
        columns={columns}
        rows={filteredItems}
        loading={loading}
        onRowClick={(r) => navigate(`/standorte/substrates/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.substrates.create')}
        onEmptyAction={() => setCreateOpen(true)}
        emptyIllustration={kamiLocations}
        tableState={tableState}
        ariaLabel={t('pages.substrates.title')}
      />
      <SubstrateCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => { setCreateOpen(false); dispatch(fetchSubstrates({})); }}
      />
      <SubstrateMixDialog
        open={mixOpen}
        onClose={() => setMixOpen(false)}
        onCreated={() => { setMixOpen(false); dispatch(fetchSubstrates({})); }}
      />
    </>
  );
}
