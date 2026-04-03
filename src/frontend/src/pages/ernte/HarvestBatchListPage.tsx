import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import MobileCard from '@/components/common/MobileCard';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchBatches } from '@/store/slices/harvestSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { HarvestBatch, PlantInstance } from '@/api/types';
import * as plantApi from '@/api/endpoints/plantInstances';
import HarvestCreateDialog from './HarvestCreateDialog';
import { kamiHarvest } from '@/assets/brand/illustrations';

type ChipColor = 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';

const qualityGradeColor: Record<string, ChipColor> = {
  a_plus: 'success',
  a: 'success',
  b: 'info',
  c: 'warning',
  d: 'error',
};

export default function HarvestBatchListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { batches, loading } = useAppSelector((s) => s.harvest);
  const [createOpen, setCreateOpen] = useState(false);
  const [plantMap, setPlantMap] = useState<Map<string, PlantInstance>>(new Map());
  const tableState = useTableUrlState({
    defaultSort: { column: 'harvestDate', direction: 'desc' },
  });

  useEffect(() => {
    dispatch(fetchBatches({}));
  }, [dispatch]);

  useEffect(() => {
    let cancelled = false;

    async function resolve() {
      const plants = await plantApi.listPlantInstances(0, 500);
      if (cancelled) return;
      const map = new Map<string, PlantInstance>();
      for (const p of plants) {
        map.set(p.key, p);
      }
      setPlantMap(map);
    }

    resolve().catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const columns: Column<HarvestBatch>[] = useMemo(() => [
    {
      id: 'batchId',
      label: t('pages.harvest.batchId'),
      render: (r) => r.batch_id || '\u2014',
    },
    {
      id: 'plantKey',
      label: t('pages.harvest.plantKey'),
      render: (r) => {
        const plant = plantMap.get(r.plant_key);
        return plant?.plant_name || plant?.instance_id || r.plant_key;
      },
      searchValue: (r) => {
        const plant = plantMap.get(r.plant_key);
        return plant?.plant_name || plant?.instance_id || r.plant_key;
      },
      hideBelowBreakpoint: 'md',
    },
    {
      id: 'harvestDate',
      label: t('pages.harvest.harvestDate'),
      render: (r) =>
        r.harvest_date ? new Date(r.harvest_date).toLocaleDateString() : '\u2014',
      sortFn: (a, b) => {
        const aDate = a.harvest_date ? new Date(a.harvest_date).getTime() : 0;
        const bDate = b.harvest_date ? new Date(b.harvest_date).getTime() : 0;
        return aDate - bDate;
      },
    },
    {
      id: 'harvestType',
      label: t('pages.harvest.harvestType'),
      render: (r) => (
        <Chip
          label={t(`enums.harvestType.${r.harvest_type}`)}
          size="small"
          variant="outlined"
        />
      ),
      searchValue: (r) => t(`enums.harvestType.${r.harvest_type}`),
      hideBelowBreakpoint: 'md',
    },
    {
      id: 'wetWeight',
      label: t('pages.harvest.wetWeightG'),
      render: (r) => (r.wet_weight_g != null ? `${r.wet_weight_g}\u202fg` : '\u2014'),
      align: 'right',
      searchValue: (r) =>
        r.wet_weight_g != null ? String(r.wet_weight_g) : '',
    },
    {
      id: 'qualityGrade',
      label: t('pages.harvest.qualityGrade'),
      render: (r) =>
        r.quality_grade ? (
          <Chip
            label={t(`enums.qualityGrade.${r.quality_grade}`)}
            size="small"
            color={qualityGradeColor[r.quality_grade] ?? 'default'}
          />
        ) : '\u2014',
      searchValue: (r) =>
        r.quality_grade
          ? t(`enums.qualityGrade.${r.quality_grade}`)
          : '',
    },
  ], [t, plantMap]);

  return (
    <Box data-testid="harvest-batch-list-page">
      <PageTitle
        title={t('pages.harvest.title')}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateOpen(true)}
            data-testid="create-button"
          >
            {t('pages.harvest.create')}
          </Button>
        }
      />
      <Typography
        variant="body2"
        color="text.secondary"
        sx={{ mb: 2 }}
      >
        {t('pages.harvest.listIntro')}
      </Typography>
      <DataTable
        columns={columns}
        rows={batches}
        loading={loading}
        onRowClick={(r) => navigate(`/ernte/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.harvest.create')}
        onEmptyAction={() => setCreateOpen(true)}
        emptyIllustration={kamiHarvest}
        tableState={tableState}
        ariaLabel={t('pages.harvest.title')}
        mobileCardRenderer={(r) => (
          <MobileCard
            title={r.batch_id || r.key}
            subtitle={r.harvest_date ? new Date(r.harvest_date).toLocaleDateString() : undefined}
            chips={
              <>
                <Chip
                  label={t(`enums.harvestType.${r.harvest_type}`)}
                  size="small"
                  variant="outlined"
                />
                {r.quality_grade && (
                  <Chip
                    label={t(`enums.qualityGrade.${r.quality_grade}`)}
                    size="small"
                    color={qualityGradeColor[r.quality_grade] ?? 'default'}
                  />
                )}
              </>
            }
            fields={[
              ...(r.wet_weight_g != null
                ? [{ label: t('pages.harvest.wetWeightG'), value: `${r.wet_weight_g}\u202fg` }]
                : []),
            ]}
          />
        )}
      />
      <HarvestCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchBatches({}));
        }}
      />
    </Box>
  );
}
