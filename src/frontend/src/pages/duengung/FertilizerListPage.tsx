import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import InputAdornment from '@mui/material/InputAdornment';
import MenuItem from '@mui/material/MenuItem';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import FilterListIcon from '@mui/icons-material/FilterList';
import FilterListOffIcon from '@mui/icons-material/FilterListOff';
import SearchIcon from '@mui/icons-material/Search';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import MobileCard from '@/components/common/MobileCard';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchFertilizers } from '@/store/slices/fertilizersSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import { useDebounce } from '@/hooks/useDebounce';
import { useLocalFavorites } from '@/hooks/useLocalFavorites';
import type { Fertilizer } from '@/api/types';
import FertilizerCreateDialog from './FertilizerCreateDialog';
import { kamiFertilizer } from '@/assets/brand/illustrations';

const FERTILIZER_TYPES = ['base', 'supplement', 'booster', 'biological', 'ph_adjuster', 'organic', 'silicate'] as const;

export default function FertilizerListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { fertilizers, loading } = useAppSelector((s) => s.fertilizers);
  const [createOpen, setCreateOpen] = useState(false);
  const [favFilterActive, setFavFilterActive] = useState(false);
  const { isFavorite, toggleFavorite, hasFavorites } = useLocalFavorites('kamerplanter-fertilizer-favorites');
  const tableState = useTableUrlState({ defaultSort: { column: 'product_name', direction: 'asc' } });

  const [filterType, setFilterType] = useState('');
  const [filterBrand, setFilterBrand] = useState('');
  const [filterTankSafe, setFilterTankSafe] = useState<string>('');
  const [filterOrganic, setFilterOrganic] = useState<string>('');
  const debouncedBrand = useDebounce(filterBrand, 400);

  // Table search — local input with debounce synced to tableState
  const [searchInput, setSearchInput] = useState(tableState.search);
  const debouncedSearch = useDebounce(searchInput, 300);

  useEffect(() => {
    if (debouncedSearch !== tableState.search) {
      tableState.setSearch(debouncedSearch);
    }
  }, [debouncedSearch]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (tableState.search !== searchInput && tableState.search !== debouncedSearch) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- sync external search state back to local input
      setSearchInput(tableState.search);
    }
  }, [tableState.search]); // eslint-disable-line react-hooks/exhaustive-deps

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filterType) count++;
    if (filterBrand) count++;
    if (filterTankSafe) count++;
    if (filterOrganic) count++;
    if (searchInput) count++;
    return count;
  }, [filterType, filterBrand, filterTankSafe, filterOrganic, searchInput]);

  const resetFilters = useCallback(() => {
    setFilterType('');
    setFilterBrand('');
    setFilterTankSafe('');
    setFilterOrganic('');
    setSearchInput('');
    tableState.setSearch('');
  }, [tableState]);

  const buildFilterArgs = useCallback(() => {
    const args: {
      fertilizerType?: string;
      brand?: string;
      tankSafe?: boolean;
      isOrganic?: boolean;
    } = {};
    if (filterType) args.fertilizerType = filterType;
    if (debouncedBrand) args.brand = debouncedBrand;
    if (filterTankSafe === 'true') args.tankSafe = true;
    if (filterTankSafe === 'false') args.tankSafe = false;
    if (filterOrganic === 'true') args.isOrganic = true;
    if (filterOrganic === 'false') args.isOrganic = false;
    return args;
  }, [filterType, debouncedBrand, filterTankSafe, filterOrganic]);

  useEffect(() => {
    dispatch(fetchFertilizers(buildFilterArgs()));
  }, [dispatch, buildFilterArgs]);

  const filteredFertilizers = useMemo(
    () => favFilterActive && hasFavorites ? fertilizers.filter((f) => isFavorite(f.key)) : fertilizers,
    [fertilizers, favFilterActive, hasFavorites, isFavorite],
  );

  const columns: Column<Fertilizer>[] = [
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
      id: 'product_name',
      label: t('pages.fertilizers.productName'),
      render: (r) => r.product_name,
    },
    {
      id: 'brand',
      label: t('pages.fertilizers.brand'),
      render: (r) => r.brand || '\u2014',
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
      render: (r) => `${r.ec_contribution_per_ml.toFixed(3)} mS/ml`,
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
      <PageTitle
        title={t('pages.fertilizers.title')}
        action={
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            {hasFavorites && (
              <Tooltip title={t('pages.fertilizers.favFilter')}>
                <IconButton
                  onClick={() => setFavFilterActive((p) => !p)}
                  color={favFilterActive ? 'warning' : 'default'}
                >
                  <FilterListIcon />
                </IconButton>
              </Tooltip>
            )}
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCreateOpen(true)}
              data-testid="create-button"
            >
              {t('pages.fertilizers.create')}
            </Button>
          </Box>
        }
      />
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.fertilizers.listIntro')}
      </Typography>

      <Paper
        variant="outlined"
        data-testid="fertilizer-filters"
        sx={{ px: 2, py: 1.5, mb: 2 }}
      >
        <Box
          sx={{
            display: 'flex',
            gap: 2,
            alignItems: 'center',
            flexWrap: 'wrap',
          }}
        >
          <TextField
            placeholder={t('table.searchPlaceholder')}
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            size="small"
            slotProps={{
              input: {
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
              },
            }}
            sx={{ flex: '1 1 auto', minWidth: { xs: 120, sm: 160 }, maxWidth: 220 }}
            data-testid="table-search-input"
          />

          <TextField
            select
            label={t('pages.fertilizers.fertilizerType')}
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            size="small"
            sx={{ flex: '1 1 auto', minWidth: { xs: 120, sm: 160 }, maxWidth: 220 }}
            data-testid="filter-fertilizer-type"
          >
            <MenuItem value="">{t('common.all')}</MenuItem>
            {FERTILIZER_TYPES.map((ft) => (
              <MenuItem key={ft} value={ft}>
                {t(`enums.fertilizerType.${ft}`)}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            label={t('pages.fertilizers.brand')}
            value={filterBrand}
            onChange={(e) => setFilterBrand(e.target.value)}
            size="small"
            sx={{ flex: '1 1 auto', minWidth: 140, maxWidth: 220 }}
            data-testid="filter-brand"
          />

          <TextField
            select
            label={t('pages.fertilizers.tankSafe')}
            value={filterTankSafe}
            onChange={(e) => setFilterTankSafe(e.target.value)}
            size="small"
            sx={{ flex: '1 1 auto', minWidth: 120, maxWidth: 220 }}
            data-testid="filter-tank-safe"
          >
            <MenuItem value="">{t('common.all')}</MenuItem>
            <MenuItem value="true">{t('common.yes')}</MenuItem>
            <MenuItem value="false">{t('common.no')}</MenuItem>
          </TextField>

          <TextField
            select
            label={t('pages.fertilizers.isOrganic')}
            value={filterOrganic}
            onChange={(e) => setFilterOrganic(e.target.value)}
            size="small"
            sx={{ flex: '1 1 auto', minWidth: 120, maxWidth: 220 }}
            data-testid="filter-organic"
          >
            <MenuItem value="">{t('common.all')}</MenuItem>
            <MenuItem value="true">{t('common.yes')}</MenuItem>
            <MenuItem value="false">{t('common.no')}</MenuItem>
          </TextField>

          {activeFilterCount > 0 && (
            <Button
              size="small"
              startIcon={<FilterListOffIcon />}
              onClick={resetFilters}
              data-testid="reset-filters"
            >
              {t('table.resetFilters')}
            </Button>
          )}
        </Box>
      </Paper>

      <DataTable
        columns={columns}
        rows={filteredFertilizers}
        loading={loading}
        onRowClick={(r) => navigate(`/duengung/fertilizers/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.fertilizers.create')}
        onEmptyAction={() => setCreateOpen(true)}
        emptyIllustration={kamiFertilizer}
        tableState={tableState}
        searchable={false}
        ariaLabel={t('pages.fertilizers.title')}
        mobileCardRenderer={(r) => (
          <MobileCard
            title={r.product_name}
            subtitle={r.brand || undefined}
            chips={
              <>
                <Chip label={t(`enums.fertilizerType.${r.fertilizer_type}`)} size="small" variant="outlined" />
                {r.is_organic && <Chip label={t('pages.fertilizers.isOrganic')} size="small" color="success" />}
                {r.tank_safe && <Chip label={t('pages.fertilizers.tankSafe')} size="small" color="success" />}
              </>
            }
            fields={[
              { label: 'NPK', value: `${r.npk_ratio[0]}-${r.npk_ratio[1]}-${r.npk_ratio[2]}` },
              { label: 'EC', value: `${r.ec_contribution_per_ml.toFixed(3)} mS/ml` },
            ]}
          />
        )}
      />
      <FertilizerCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchFertilizers(buildFilterArgs()));
        }}
      />
    </Box>
  );
}
