import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import LinearProgress from '@mui/material/LinearProgress';
import AddIcon from '@mui/icons-material/Add';
import PageTitle from '@/components/layout/PageTitle';
import MobileCard from '@/components/common/MobileCard';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchPostHarvestBatches } from '@/store/slices/postHarvestSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { PostHarvestBatch, PostHarvestStage } from '@/api/types';
import StartDryingDialog from './StartDryingDialog';
import PostHarvestDetailDialog from './PostHarvestDetailDialog';

type ChipColor = 'default' | 'info' | 'success' | 'warning';

const STAGE_COLOR: Record<PostHarvestStage, ChipColor> = {
  drying: 'info',
  curing: 'warning',
  stored: 'success',
  released: 'default',
};

export default function PostHarvestPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { batches, loading } = useAppSelector((s) => s.postHarvest);
  const [startOpen, setStartOpen] = useState(false);
  const [detailKey, setDetailKey] = useState<string | null>(null);
  const tableState = useTableUrlState({
    defaultSort: { column: 'stage', direction: 'asc' },
  });

  useEffect(() => {
    dispatch(fetchPostHarvestBatches({}));
  }, [dispatch]);

  const columns: Column<PostHarvestBatch>[] = useMemo(
    () => [
      {
        id: 'harvestBatch',
        label: t('pages.postHarvest.harvestBatch'),
        render: (r) => r.harvest_batch_key || '—',
      },
      {
        id: 'stage',
        label: t('pages.postHarvest.stage'),
        render: (r) => (
          <Chip
            label={t(`enums.postHarvestStage.${r.stage}`)}
            size="small"
            color={STAGE_COLOR[r.stage]}
          />
        ),
        searchValue: (r) => t(`enums.postHarvestStage.${r.stage}`),
      },
      {
        id: 'dryness',
        label: t('pages.postHarvest.drynessProgress'),
        render: (r) => (
          <Box sx={{ minWidth: 120 }}>
            <Typography variant="caption" color="text.secondary">
              {r.dryness_progress_percent.toFixed(0)}%
            </Typography>
            <LinearProgress
              variant="determinate"
              value={Math.min(100, Math.max(0, r.dryness_progress_percent))}
              color={r.ready_for_curing ? 'success' : 'info'}
              aria-label={t('pages.postHarvest.drynessProgress')}
            />
          </Box>
        ),
        sortFn: (a, b) => a.dryness_progress_percent - b.dryness_progress_percent,
        hideBelowBreakpoint: 'md',
      },
      {
        id: 'method',
        label: t('pages.postHarvest.dryingMethod'),
        render: (r) => (
          <Chip
            label={t(`enums.dryingMethod.${r.drying_method}`)}
            size="small"
            variant="outlined"
          />
        ),
        searchValue: (r) => t(`enums.dryingMethod.${r.drying_method}`),
        hideBelowBreakpoint: 'md',
      },
    ],
    [t],
  );

  return (
    <Box data-testid="post-harvest-page">
      <PageTitle
        title={t('pages.postHarvest.title')}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setStartOpen(true)}
            data-testid="start-drying-button"
          >
            {t('pages.postHarvest.startDrying')}
          </Button>
        }
      />
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.postHarvest.listIntro')}
      </Typography>
      <DataTable
        columns={columns}
        rows={batches}
        loading={loading}
        onRowClick={(r) => setDetailKey(r.key)}
        getRowKey={(r) => r.key}
        emptyMessage={t('pages.postHarvest.emptyTitle')}
        emptyDescription={t('pages.postHarvest.emptyDescription')}
        emptyActionLabel={t('pages.postHarvest.startDrying')}
        onEmptyAction={() => setStartOpen(true)}
        tableState={tableState}
        ariaLabel={t('pages.postHarvest.title')}
        mobileCardRenderer={(r) => (
          <MobileCard
            title={r.harvest_batch_key || r.key}
            chips={
              <>
                <Chip
                  label={t(`enums.postHarvestStage.${r.stage}`)}
                  size="small"
                  color={STAGE_COLOR[r.stage]}
                />
                <Chip
                  label={t(`enums.dryingMethod.${r.drying_method}`)}
                  size="small"
                  variant="outlined"
                />
              </>
            }
            fields={[
              {
                label: t('pages.postHarvest.drynessProgress'),
                value: (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 96 }}>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(100, Math.max(0, r.dryness_progress_percent))}
                      color={r.ready_for_curing ? 'success' : 'info'}
                      aria-label={t('pages.postHarvest.drynessProgress')}
                      sx={{ flex: 1 }}
                    />
                    <span>{r.dryness_progress_percent.toFixed(0)}%</span>
                  </Box>
                ),
              },
            ]}
          />
        )}
      />
      <StartDryingDialog
        open={startOpen}
        onClose={() => setStartOpen(false)}
        onCreated={() => {
          setStartOpen(false);
          dispatch(fetchPostHarvestBatches({}));
        }}
      />
      <PostHarvestDetailDialog
        batchKey={detailKey}
        onClose={() => setDetailKey(null)}
        onChanged={() => dispatch(fetchPostHarvestBatches({}))}
      />
    </Box>
  );
}
