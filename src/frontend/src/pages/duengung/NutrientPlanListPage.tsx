import { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import FilterListIcon from '@mui/icons-material/FilterList';
import MobileCard from '@/components/common/MobileCard';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchNutrientPlans } from '@/store/slices/nutrientPlansSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useLocalFavorites } from '@/hooks/useLocalFavorites';
import * as planApi from '@/api/endpoints/nutrient-plans';
import type { NutrientPlan } from '@/api/types';
import NutrientPlanCreateDialog from './NutrientPlanCreateDialog';
import { kamiFertilizer } from '@/assets/brand/illustrations';

export default function NutrientPlanListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { plans, loading } = useAppSelector((s) => s.nutrientPlans);
  const [createOpen, setCreateOpen] = useState(false);
  const [favFilterActive, setFavFilterActive] = useState(false);
  const { isFavorite, toggleFavorite, hasFavorites } = useLocalFavorites('kamerplanter-nutrient-plan-favorites');
  const tableState = useTableUrlState({ defaultSort: { column: 'name', direction: 'asc' } });

  useEffect(() => {
    dispatch(fetchNutrientPlans({}));
  }, [dispatch]);

  const handleClone = async (plan: NutrientPlan) => {
    try {
      const cloned = await planApi.cloneNutrientPlan(plan.key, {
        new_name: `${plan.name} (copy)`,
        author: plan.author,
      });
      notification.success(t('pages.nutrientPlans.cloned'));
      navigate(`/duengung/plans/${cloned.key}`);
    } catch (err) {
      handleError(err);
    }
  };

  const filteredPlans = useMemo(
    () => favFilterActive && hasFavorites ? plans.filter((p) => isFavorite(p.key)) : plans,
    [plans, favFilterActive, hasFavorites, isFavorite],
  );

  const columns: Column<NutrientPlan>[] = [
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
      id: 'name',
      label: t('pages.nutrientPlans.name'),
      render: (r) => r.name,
    },
    {
      id: 'author',
      label: t('pages.nutrientPlans.author'),
      render: (r) => r.author || '\u2014',
    },
    {
      id: 'recommended_substrate_type',
      label: t('pages.nutrientPlans.substrateType'),
      render: (r) =>
        r.recommended_substrate_type
          ? t(`enums.substrateType.${r.recommended_substrate_type}`)
          : '\u2014',
      searchValue: (r) =>
        r.recommended_substrate_type
          ? t(`enums.substrateType.${r.recommended_substrate_type}`)
          : '',
    },
    {
      id: 'is_template',
      label: t('pages.nutrientPlans.isTemplate'),
      render: (r) => (
        <Chip
          label={r.is_template ? t('common.yes') : t('common.no')}
          size="small"
          color={r.is_template ? 'primary' : 'default'}
        />
      ),
      searchValue: (r) => (r.is_template ? t('common.yes') : t('common.no')),
    },
    {
      id: 'version',
      label: t('pages.nutrientPlans.version'),
      render: (r) => r.version || '\u2014',
    },
    {
      id: 'tags',
      label: t('pages.nutrientPlans.tags'),
      render: (r) => {
        const MAX_VISIBLE = 3;
        const visible = r.tags.slice(0, MAX_VISIBLE);
        const remaining = r.tags.length - MAX_VISIBLE;
        return (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {visible.map((tag) => (
              <Chip key={tag} label={tag} size="small" variant="outlined" />
            ))}
            {remaining > 0 && (
              <Tooltip title={r.tags.slice(MAX_VISIBLE).join(', ')}>
                <Chip label={`+${remaining}`} size="small" variant="outlined" color="default" />
              </Tooltip>
            )}
          </Box>
        );
      },
      searchValue: (r) => r.tags.join(' '),
    },
    {
      id: 'actions',
      label: '',
      render: (r) => (
        <Tooltip title={t('pages.nutrientPlans.clone')}>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              handleClone(r);
            }}
          >
            <ContentCopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      ),
    },
  ];

  return (
    <Box data-testid="nutrient-plan-list-page">
      <PageTitle
        title={t('pages.nutrientPlans.title')}
        action={
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            {hasFavorites && (
              <Tooltip title={t('pages.nutrientPlans.favFilter')}>
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
              {t('pages.nutrientPlans.create')}
            </Button>
          </Box>
        }
      />
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.nutrientPlans.listIntro')}
      </Typography>
      <DataTable
        columns={columns}
        rows={filteredPlans}
        loading={loading}
        onRowClick={(r) => navigate(`/duengung/plans/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.nutrientPlans.create')}
        onEmptyAction={() => setCreateOpen(true)}
        emptyIllustration={kamiFertilizer}
        tableState={tableState}
        ariaLabel={t('pages.nutrientPlans.title')}
        mobileCardRenderer={(r) => (
          <MobileCard
            title={r.name}
            subtitle={r.author || undefined}
            chips={
              <>
                {r.is_template && <Chip label={t('pages.nutrientPlans.isTemplate')} size="small" color="primary" />}
                {r.tags.slice(0, 3).map((tag) => <Chip key={tag} label={tag} size="small" variant="outlined" />)}
                {r.tags.length > 3 && <Chip label={`+${r.tags.length - 3}`} size="small" variant="outlined" />}
              </>
            }
            fields={[
              ...(r.recommended_substrate_type ? [{ label: t('pages.nutrientPlans.substrateType'), value: t(`enums.substrateType.${r.recommended_substrate_type}`) }] : []),
              ...(r.version ? [{ label: t('pages.nutrientPlans.version'), value: r.version }] : []),
            ]}
          />
        )}
      />
      <NutrientPlanCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchNutrientPlans({}));
        }}
      />
    </Box>
  );
}
