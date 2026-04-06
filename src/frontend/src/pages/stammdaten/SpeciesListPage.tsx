import { useEffect, useState, useMemo, useCallback } from 'react';
import { useNavigate, useSearchParams, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import FilterListIcon from '@mui/icons-material/FilterList';
import Link from '@mui/material/Link';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import YardIcon from '@mui/icons-material/Yard';
import MobileCard from '@/components/common/MobileCard';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchSpeciesList } from '@/store/slices/speciesSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import { useSowingFavorites } from '@/hooks/useSowingFavorites';
import type { Species, GrowthHabit } from '@/api/types';
import { fetchPlantInstances } from '@/store/slices/plantInstancesSlice';
import SpeciesCreateDialog from './SpeciesCreateDialog';
import { kamiMasterdata } from '@/assets/brand/illustrations';

type ToggleFilter =
  | 'favoritesOnly'
  | 'sowNow'
  | 'indoor'
  | 'container'
  | 'balcony'
  | 'greenhouse'
  | 'frostHardy'
  | 'harvestable'
  | 'supportNeeded';

const ALL_GROWTH_HABITS: GrowthHabit[] = ['herb', 'shrub', 'tree', 'vine', 'groundcover'];

function matchesToggleFilter(
  species: Species,
  filter: ToggleFilter,
  isFavorite: (key: string) => boolean,
): boolean {
  switch (filter) {
    case 'favoritesOnly':
      return isFavorite(species.key);
    case 'sowNow': {
      const month = new Date().getMonth() + 1;
      return (species.direct_sow_months ?? []).includes(month);
    }
    case 'indoor':
      return species.indoor_suitable === 'yes' || species.indoor_suitable === 'limited';
    case 'container':
      return species.container_suitable === 'yes' || species.container_suitable === 'limited';
    case 'balcony':
      return species.balcony_suitable === 'yes' || species.balcony_suitable === 'limited';
    case 'greenhouse':
      return species.greenhouse_recommended === true;
    case 'frostHardy':
      return species.frost_sensitivity === 'hardy' || species.frost_sensitivity === 'very_hardy';
    case 'harvestable':
      return species.allows_harvest === true;
    case 'supportNeeded':
      return species.support_required === true;
  }
}

export default function SpeciesListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { items, loading } = useAppSelector((s) => s.species);
  const tableState = useTableUrlState({ defaultSort: { column: 'scientificName', direction: 'asc' } });
  const [searchParams, setSearchParams] = useSearchParams();
  const familyFilter = searchParams.get('family') ?? '';
  const [createOpen, setCreateOpen] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [activeFilters, setActiveFilters] = useState<Set<ToggleFilter>>(new Set());
  const [growthHabitFilter, setGrowthHabitFilter] = useState<GrowthHabit | ''>('');
  const { favorites, toggleFavorite, isFavorite } = useSowingFavorites();

  const plantInstances = useAppSelector((s) => s.plantInstances.items);

  useEffect(() => {
    dispatch(fetchSpeciesList({ offset: 0, limit: 1000 }));
    dispatch(fetchPlantInstances({ offset: 0, limit: 200 }));
  }, [dispatch]);

  const activeCountMap = useMemo(() => {
    const counts = new Map<string, number>();
    for (const p of plantInstances) {
      if (!p.removed_on) {
        counts.set(p.species_key, (counts.get(p.species_key) ?? 0) + 1);
      }
    }
    return counts;
  }, [plantInstances]);

  const toggleFilter = useCallback((filter: ToggleFilter) => {
    setActiveFilters((prev) => {
      const next = new Set(prev);
      if (next.has(filter)) {
        next.delete(filter);
      } else {
        next.add(filter);
      }
      return next;
    });
  }, []);

  const filterCount = activeFilters.size + (growthHabitFilter ? 1 : 0) + (familyFilter ? 1 : 0);
  const hasActiveFilters = filterCount > 0;

  const clearAllFilters = useCallback(() => {
    setActiveFilters(new Set());
    setGrowthHabitFilter('');
    setSearchParams((prev) => {
      prev.delete('family');
      return prev;
    });
  }, [setSearchParams]);

  const filteredItems = useMemo(() => {
    let result = items;

    if (familyFilter) {
      result = result.filter((s) => s.family_key === familyFilter);
    }

    for (const filter of activeFilters) {
      result = result.filter((s) => matchesToggleFilter(s, filter, isFavorite));
    }

    if (growthHabitFilter) {
      result = result.filter((s) => s.growth_habit === growthHabitFilter);
    }

    // Sort favorites first
    if (favorites.size > 0) {
      result = [...result].sort((a, b) => {
        const aFav = isFavorite(a.key);
        const bFav = isFavorite(b.key);
        if (aFav !== bFav) return aFav ? -1 : 1;
        return 0;
      });
    }

    return result;
  }, [items, activeFilters, growthHabitFilter, familyFilter, favorites, isFavorite]);

  // Auto-open filter panel when filters are active
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- auto-open filter panel when filters become active
    if (hasActiveFilters) setFiltersOpen(true);
  }, [hasActiveFilters]);

  const columns: Column<Species>[] = [
    {
      id: 'favorite',
      label: '',
      render: (r) => (
        <IconButton
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            toggleFavorite(r.key);
          }}
          color={isFavorite(r.key) ? 'warning' : 'default'}
          aria-label={t('pages.calendar.sowingCalendar.toggleFavorite')}
          sx={{ p: 0.25 }}
        >
          {isFavorite(r.key) ? (
            <StarIcon fontSize="small" />
          ) : (
            <StarBorderIcon fontSize="small" />
          )}
        </IconButton>
      ),
      sortable: false,
      width: 48,
    },
    {
      id: 'scientificName',
      label: t('pages.species.scientificName'),
      render: (r) => r.scientific_name,
    },
    {
      id: 'commonNames',
      label: t('pages.species.commonNames'),
      render: (r) => r.common_names.join(', ') || '\u2014',
    },
    {
      id: 'family',
      label: t('pages.species.family'),
      render: (r) =>
        r.family_key ? (
          <Link
            component={RouterLink}
            to={`/stammdaten/botanical-families/${r.family_key}`}
            onClick={(e: React.MouseEvent) => e.stopPropagation()}
          >
            {r.family_name ?? r.family_key}
          </Link>
        ) : (
          '\u2014'
        ),
      searchValue: (r) => r.family_name ?? '',
      hideBelowBreakpoint: 'md',
    },
    {
      id: 'genus',
      label: t('pages.species.genus'),
      render: (r) => r.genus,
    },
    {
      id: 'growthHabit',
      label: t('pages.species.growthHabit'),
      render: (r) => t(`enums.growthHabit.${r.growth_habit}`),
      searchValue: (r) => t(`enums.growthHabit.${r.growth_habit}`),
    },
    {
      id: 'activePlants',
      label: t('pages.species.activePlants'),
      render: (r) => activeCountMap.get(r.key) ?? 0,
      align: 'right',
      sortFn: (a, b) => (activeCountMap.get(a.key) ?? 0) - (activeCountMap.get(b.key) ?? 0),
    },
    {
      id: 'rootType',
      label: t('pages.species.rootType'),
      render: (r) => t(`enums.rootType.${r.root_type}`),
      searchValue: (r) => t(`enums.rootType.${r.root_type}`),
      hideBelowBreakpoint: 'md',
    },
  ];

  const filterChips: { key: ToggleFilter; label: string; icon?: React.ReactElement }[] = [
    { key: 'favoritesOnly', label: t('pages.species.filterFavorites'), icon: <StarIcon /> },
    { key: 'sowNow', label: t('pages.species.filterSowNow'), icon: <YardIcon /> },
    { key: 'indoor', label: t('pages.species.filterIndoor') },
    { key: 'container', label: t('pages.species.filterContainer') },
    { key: 'balcony', label: t('pages.species.filterBalcony') },
    { key: 'greenhouse', label: t('pages.species.filterGreenhouse') },
    { key: 'frostHardy', label: t('pages.species.filterFrostHardy') },
    { key: 'harvestable', label: t('pages.species.filterHarvestable') },
    { key: 'supportNeeded', label: t('pages.species.filterSupportNeeded') },
  ];

  return (
    <Box data-testid="species-list-page">
      {/* Combined header: title + filter toggle + result count + create */}
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: 1,
          mb: 2,
        }}
      >
        <Box sx={{ '& [data-testid="page-title"]': { mb: 0 } }}>
          <PageTitle title={t('pages.species.title')} />
        </Box>

        <Tooltip title={t('pages.species.filters')}>
          <Button
            size="small"
            variant={hasActiveFilters ? 'contained' : 'outlined'}
            startIcon={<FilterListIcon />}
            onClick={() => setFiltersOpen((prev) => !prev)}
            data-testid="toggle-filters-button"
          >
            {t('pages.species.filters')}
            {hasActiveFilters && ` (${filterCount})`}
          </Button>
        </Tooltip>

        {hasActiveFilters && (
          <>
            <Typography variant="body2" color="text.secondary">
              {t('pages.species.filterResultCount', {
                count: filteredItems.length,
                total: items.length,
              })}
            </Typography>
            <Button
              size="small"
              onClick={clearAllFilters}
              data-testid="clear-filters-button"
            >
              {t('pages.species.clearFilters')}
            </Button>
          </>
        )}

        <Box sx={{ flex: 1 }} />

        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
          data-testid="create-button"
        >
          {t('pages.species.create')}
        </Button>
      </Box>

      {/* Family filter banner from URL param */}
      {familyFilter && filteredItems.length > 0 && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Chip
            label={`${t('pages.species.family')}: ${filteredItems[0]?.family_name ?? familyFilter}`}
            onDelete={() =>
              setSearchParams((prev) => {
                prev.delete('family');
                return prev;
              })
            }
            color="primary"
          />
        </Box>
      )}

      {/* Filter panel */}
      <Collapse in={filtersOpen}>
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: 1,
            mb: 2,
            p: 2,
            borderRadius: 1,
            bgcolor: 'action.hover',
          }}
          data-testid="species-filter-panel"
        >
          {filterChips.map(({ key, label, icon }) => (
            <Chip
              key={key}
              label={label}
              icon={icon}
              variant={activeFilters.has(key) ? 'filled' : 'outlined'}
              color={activeFilters.has(key) ? 'primary' : 'default'}
              onClick={() => toggleFilter(key)}
              data-testid={`filter-chip-${key}`}
            />
          ))}

          <TextField
            select
            size="small"
            label={t('pages.species.growthHabit')}
            value={growthHabitFilter}
            onChange={(e) => setGrowthHabitFilter(e.target.value as GrowthHabit | '')}
            sx={{ minWidth: 160 }}
            data-testid="filter-growth-habit"
          >
            <MenuItem value="">{t('pages.species.filterAll')}</MenuItem>
            {ALL_GROWTH_HABITS.map((h) => (
              <MenuItem key={h} value={h}>
                {t(`enums.growthHabit.${h}`)}
              </MenuItem>
            ))}
          </TextField>
        </Box>
      </Collapse>

      <DataTable
        columns={columns}
        rows={filteredItems}
        loading={loading}
        onRowClick={(r) => navigate(`/stammdaten/species/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.species.create')}
        onEmptyAction={() => setCreateOpen(true)}
        emptyIllustration={kamiMasterdata}
        tableState={tableState}
        ariaLabel={t('pages.species.title')}
        mobileCardRenderer={(r) => (
          <MobileCard
            title={r.scientific_name}
            subtitle={r.common_names.join(', ') || undefined}
            chips={
              <>
                <Chip
                  label={t(`enums.growthHabit.${r.growth_habit}`)}
                  size="small"
                  variant="outlined"
                />
                <Chip
                  label={t(`enums.rootType.${r.root_type}`)}
                  size="small"
                  variant="outlined"
                />
              </>
            }
            fields={[
              { label: t('pages.species.genus'), value: r.genus },
              { label: t('pages.species.activePlants'), value: activeCountMap.get(r.key) ?? 0 },
            ]}
          />
        )}
      />

      <SpeciesCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchSpeciesList({ offset: 0, limit: 1000 }));
        }}
      />
    </Box>
  );
}
