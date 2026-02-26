import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import AddIcon from '@mui/icons-material/Add';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchNutrientPlans } from '@/store/slices/nutrientPlansSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as planApi from '@/api/endpoints/nutrient-plans';
import type { NutrientPlan } from '@/api/types';
import NutrientPlanCreateDialog from './NutrientPlanCreateDialog';

export default function NutrientPlanListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { plans, loading } = useAppSelector((s) => s.nutrientPlans);
  const [createOpen, setCreateOpen] = useState(false);
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

  const columns: Column<NutrientPlan>[] = [
    {
      id: 'name',
      label: t('pages.nutrientPlans.name'),
      render: (r) => r.name,
    },
    {
      id: 'author',
      label: t('pages.nutrientPlans.author'),
      render: (r) => r.author || '-',
    },
    {
      id: 'recommended_substrate_type',
      label: t('pages.nutrientPlans.substrateType'),
      render: (r) =>
        r.recommended_substrate_type
          ? t(`enums.substrateType.${r.recommended_substrate_type}`)
          : '-',
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
      render: (r) => r.version || '-',
    },
    {
      id: 'tags',
      label: t('pages.nutrientPlans.tags'),
      render: (r) => (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
          {r.tags.map((tag) => (
            <Chip key={tag} label={tag} size="small" variant="outlined" />
          ))}
        </Box>
      ),
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
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <PageTitle title={t('pages.nutrientPlans.title')} />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
          data-testid="create-button"
        >
          {t('pages.nutrientPlans.create')}
        </Button>
      </Box>
      <DataTable
        columns={columns}
        rows={plans}
        loading={loading}
        onRowClick={(r) => navigate(`/duengung/plans/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.nutrientPlans.create')}
        onEmptyAction={() => setCreateOpen(true)}
        tableState={tableState}
        ariaLabel={t('pages.nutrientPlans.title')}
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
