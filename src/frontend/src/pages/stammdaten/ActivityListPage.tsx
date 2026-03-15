import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import TextField from '@mui/material/TextField';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import InputAdornment from '@mui/material/InputAdornment';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchActivities } from '@/store/slices/activitiesSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { Activity } from '@/api/types';
import ActivityCreateDialog from './ActivityCreateDialog';
import { kamiMasterdata } from '@/assets/brand/illustrations';

const stressColors: Record<string, 'default' | 'success' | 'warning' | 'error'> = {
  none: 'default',
  low: 'success',
  medium: 'warning',
  high: 'error',
};

type ScopeFilter = 'all' | 'universal' | 'restricted';

export default function ActivityListPage() {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { items, loading } = useAppSelector((s) => s.activities);
  const [createOpen, setCreateOpen] = useState(false);
  const [scopeFilter, setScopeFilter] = useState<ScopeFilter>('all');
  const [speciesFilter, setSpeciesFilter] = useState('');
  const tableState = useTableUrlState({ defaultSort: { column: 'name', direction: 'asc' } });

  useEffect(() => {
    const params: { scope?: 'universal' | 'restricted'; species?: string } = {};
    if (scopeFilter !== 'all') params.scope = scopeFilter;
    if (speciesFilter.trim()) params.species = speciesFilter.trim();
    dispatch(fetchActivities(Object.keys(params).length > 0 ? params : undefined));
  }, [dispatch, scopeFilter, speciesFilter]);

  const lang = i18n.language?.startsWith('en') ? 'en' : 'de';

  const columns: Column<Activity>[] = [
    {
      id: 'name',
      label: t('pages.activities.name'),
      render: (r) => (lang === 'en' ? r.name : r.name_de || r.name),
      searchValue: (r) => `${r.name} ${r.name_de}`,
    },
    {
      id: 'category',
      label: t('pages.activities.category'),
      render: (r) => t(`enums.activityCategory.${r.category}`),
      searchValue: (r) => t(`enums.activityCategory.${r.category}`),
    },
    {
      id: 'scope',
      label: t('pages.activities.scope'),
      render: (r) => {
        const isUniversal = r.species_compatible.length === 0;
        return isUniversal ? (
          <Chip label={t('pages.activities.scopeUniversal')} size="small" color="default" variant="outlined" />
        ) : (
          <Tooltip title={r.species_compatible.join(', ')} arrow>
            <Chip
              label={`${t('pages.activities.scopeRestricted')} (${r.species_compatible.length})`}
              size="small"
              color="primary"
              variant="outlined"
            />
          </Tooltip>
        );
      },
      searchValue: (r) =>
        r.species_compatible.length === 0
          ? t('pages.activities.scopeUniversal')
          : r.species_compatible.join(' '),
    },
    {
      id: 'stress',
      label: t('pages.activities.stressLevel'),
      render: (r) => (
        <Chip
          label={t(`enums.stressLevel.${r.stress_level}`)}
          size="small"
          color={stressColors[r.stress_level] ?? 'default'}
        />
      ),
      searchValue: (r) => t(`enums.stressLevel.${r.stress_level}`),
    },
    {
      id: 'skill',
      label: t('pages.activities.skillLevel'),
      render: (r) => t(`enums.skillLevel.${r.skill_level}`),
      searchValue: (r) => t(`enums.skillLevel.${r.skill_level}`),
    },
    {
      id: 'recovery',
      label: t('pages.activities.recoveryDays'),
      render: (r) => r.recovery_days_default > 0 ? `${r.recovery_days_default}d` : '\u2014',
      align: 'right',
    },
    {
      id: 'system',
      label: t('pages.activities.system'),
      render: (r) => (
        <Chip
          label={r.is_system ? t('common.yes') : t('common.no')}
          size="small"
          color={r.is_system ? 'info' : 'default'}
          variant="outlined"
        />
      ),
    },
  ];

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle title={t('pages.activities.title')} />
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
          {t('pages.activities.create')}
        </Button>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.activities.listIntro')}
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <ToggleButtonGroup
          value={scopeFilter}
          exclusive
          onChange={(_, v) => { if (v !== null) setScopeFilter(v); }}
          size="small"
        >
          <ToggleButton value="all">{t('pages.activities.scopeAll')}</ToggleButton>
          <ToggleButton value="universal">{t('pages.activities.scopeUniversal')}</ToggleButton>
          <ToggleButton value="restricted">{t('pages.activities.scopeRestricted')}</ToggleButton>
        </ToggleButtonGroup>
        <TextField
          size="small"
          placeholder={t('pages.activities.filterBySpecies')}
          value={speciesFilter}
          onChange={(e) => setSpeciesFilter(e.target.value)}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            },
          }}
          sx={{ minWidth: 200 }}
        />
      </Box>
      <DataTable
        columns={columns}
        rows={items}
        loading={loading}
        onRowClick={(r) => navigate(`/stammdaten/activities/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyMessage={t('pages.activities.noActivities')}
        emptyActionLabel={t('pages.activities.create')}
        onEmptyAction={() => setCreateOpen(true)}
        emptyIllustration={kamiMasterdata}
        tableState={tableState}
        ariaLabel={t('pages.activities.title')}
      />
      <ActivityCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => { setCreateOpen(false); dispatch(fetchActivities()); }}
      />
    </>
  );
}
