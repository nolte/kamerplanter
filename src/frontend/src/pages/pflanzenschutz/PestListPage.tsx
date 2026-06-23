import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import CameraAltOutlinedIcon from '@mui/icons-material/CameraAltOutlined';
import MobileCard from '@/components/common/MobileCard';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import {
  ColumnFilterBar,
  type ColumnFilterDef,
} from '@/components/common/ColumnFilterBar';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchPests } from '@/store/slices/ipmSlice';
import { fetchPestDetectionStatus } from '@/store/slices/pestDetectionSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import { useColumnFilters } from '@/hooks/useColumnFilters';
import { useLocalizedField } from '@/hooks/useLocalizedField';
import type { Pest } from '@/api/types';
import PestCreateDialog from './PestCreateDialog';
import { kamiIpm } from '@/assets/brand/illustrations';

type ChipColor = 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';

const difficultyColor: Record<string, ChipColor> = {
  easy: 'success',
  medium: 'warning',
  hard: 'error',
};

// Filterable enum domains. Keep these aligned with `enums.pestType.*` /
// `enums.detectionDifficulty.*` so option labels resolve via i18n.
const PEST_TYPE_VALUES = [
  'insect',
  'mite',
  'nematode',
  'mollusk',
  'arachnid',
  'gastropod',
  'mammal',
] as const;
const DIFFICULTY_VALUES = ['easy', 'medium', 'hard'] as const;

// URL query-param names owned by the column filters (comma-separated values).
const FILTER_PEST_TYPE = 'pest_type';
const FILTER_DIFFICULTY = 'difficulty';
const FILTER_RECOGNITION = 'recognition';
const FILTER_IDS = [FILTER_PEST_TYPE, FILTER_DIFFICULTY, FILTER_RECOGNITION] as const;

export default function PestListPage() {
  const { t } = useTranslation();
  const l = useLocalizedField();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { pests, loading } = useAppSelector((s) => s.ipm);
  const detectionStatus = useAppSelector((s) => s.pestDetection.status);
  const [createOpen, setCreateOpen] = useState(false);
  const tableState = useTableUrlState({
    defaultSort: { column: 'scientificName', direction: 'asc' },
  });
  const columnFilters = useColumnFilters(FILTER_IDS);

  useEffect(() => {
    dispatch(fetchPests({}));
  }, [dispatch]);

  useEffect(() => {
    if (detectionStatus == null) {
      dispatch(fetchPestDetectionStatus());
    }
  }, [dispatch, detectionStatus]);

  // REQ-044 — only surface the "recognition available" marker while the pest
  // detection feature is actually enabled (master switch `pest_detection_enabled`,
  // mirrored by the tenant status endpoint's `available` flag). When the feature
  // is off, the backend already reports `has_reference_images=false`, but we
  // additionally hide the marker/column so the UI never hints at a disabled feature.
  const recognitionEnabled = detectionStatus?.available === true;

  // Available filter controls. The recognition filter is only offered while the
  // detection feature is enabled (mirrors the conditional recognition column).
  const filterDefs: ColumnFilterDef[] = useMemo(() => {
    const defs: ColumnFilterDef[] = [
      {
        id: FILTER_PEST_TYPE,
        label: t('pages.ipm.pestType'),
        options: PEST_TYPE_VALUES.map((v) => ({
          value: v,
          label: t(`enums.pestType.${v}`),
        })),
      },
      {
        id: FILTER_DIFFICULTY,
        label: t('pages.ipm.detectionDifficulty'),
        options: DIFFICULTY_VALUES.map((v) => ({
          value: v,
          label: t(`enums.detectionDifficulty.${v}`),
        })),
      },
    ];
    if (recognitionEnabled) {
      defs.push({
        id: FILTER_RECOGNITION,
        label: t('pages.ipm.recognitionColumn'),
        options: [
          { value: 'yes', label: t('common.yes') },
          { value: 'no', label: t('common.no') },
        ],
      });
    }
    return defs;
  }, [t, recognitionEnabled]);

  // Client-side filtering: the page loads the full pest list up front
  // (`fetchPests({})`), so we can apply the multi-select column filters in a
  // memo before handing the rows to the (also client-side) DataTable. The
  // free-text search/sort/pagination remain DataTable's responsibility.
  const filteredPests = useMemo(() => {
    const types = columnFilters.values[FILTER_PEST_TYPE] ?? [];
    const difficulties = columnFilters.values[FILTER_DIFFICULTY] ?? [];
    const recognition = recognitionEnabled
      ? columnFilters.values[FILTER_RECOGNITION] ?? []
      : [];
    if (types.length === 0 && difficulties.length === 0 && recognition.length === 0) {
      return pests;
    }
    return pests.filter((p) => {
      if (types.length > 0 && !types.includes(p.pest_type)) return false;
      if (difficulties.length > 0 && !difficulties.includes(p.detection_difficulty)) {
        return false;
      }
      if (recognition.length > 0) {
        const flag = p.has_reference_images ? 'yes' : 'no';
        if (!recognition.includes(flag)) return false;
      }
      return true;
    });
  }, [pests, columnFilters.values, recognitionEnabled]);

  const recognitionColumn: Column<Pest> = {
    id: 'recognition',
    label: t('pages.ipm.recognitionColumn'),
    render: (r) =>
      r.has_reference_images ? (
        <Tooltip title={t('pages.ipm.recognitionAvailableTooltip')}>
          <Chip
            icon={<CameraAltOutlinedIcon />}
            label={t('pages.ipm.recognitionAvailable')}
            size="small"
            color="info"
            variant="outlined"
            data-testid="recognition-chip"
          />
        </Tooltip>
      ) : null,
    searchable: false,
    sortable: false,
    hideBelowBreakpoint: 'md',
  };

  const columns: Column<Pest>[] = [
    {
      id: 'scientificName',
      label: t('pages.ipm.scientificName'),
      render: (r) => r.scientific_name,
    },
    {
      id: 'commonName',
      label: t('pages.ipm.commonName'),
      render: (r) => l(r, 'common_name'),
      searchValue: (r) => l(r, 'common_name'),
    },
    {
      id: 'pestType',
      label: t('pages.ipm.pestType'),
      render: (r) => (
        <Chip
          label={t(`enums.pestType.${r.pest_type}`)}
          size="small"
          variant="outlined"
        />
      ),
      searchValue: (r) => t(`enums.pestType.${r.pest_type}`),
      hideBelowBreakpoint: 'md',
    },
    {
      id: 'lifecycleDays',
      label: t('pages.ipm.lifecycleDays'),
      render: (r) =>
        r.lifecycle_days != null ? `${r.lifecycle_days}\u202f${t('pages.ipm.days')}` : '—',
      align: 'right',
      searchValue: (r) => (r.lifecycle_days != null ? String(r.lifecycle_days) : ''),
      hideBelowBreakpoint: 'md',
    },
    {
      id: 'detectionDifficulty',
      label: t('pages.ipm.detectionDifficulty'),
      render: (r) => (
        <Chip
          label={t(`enums.detectionDifficulty.${r.detection_difficulty}`)}
          size="small"
          color={difficultyColor[r.detection_difficulty] ?? 'default'}
        />
      ),
      searchValue: (r) => t(`enums.detectionDifficulty.${r.detection_difficulty}`),
    },
    ...(recognitionEnabled ? [recognitionColumn] : []),
  ];

  return (
    <Box data-testid="pest-list-page">
      <PageTitle
        title={t('pages.ipm.pestsTitle')}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateOpen(true)}
            data-testid="create-button"
          >
            {t('pages.ipm.createPest')}
          </Button>
        }
      />
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.ipm.pestListIntro')}
      </Typography>
      <ColumnFilterBar filters={filterDefs} state={columnFilters} />
      <DataTable
        columns={columns}
        rows={filteredPests}
        loading={loading}
        getRowKey={(r) => r.key}
        onRowClick={(r) => navigate(`/pflanzenschutz/pests/${r.key}`)}
        emptyActionLabel={t('pages.ipm.createPest')}
        onEmptyAction={() => setCreateOpen(true)}
        emptyIllustration={kamiIpm}
        tableState={tableState}
        ariaLabel={t('pages.ipm.pestsTitle')}
        hasActiveColumnFilters={columnFilters.activeCount > 0}
        onResetColumnFilters={columnFilters.clearAll}
        mobileCardRenderer={(r) => (
          <MobileCard
            title={r.scientific_name}
            subtitle={l(r, 'common_name')}
            chips={
              <>
                <Chip
                  label={t(`enums.pestType.${r.pest_type}`)}
                  size="small"
                  variant="outlined"
                />
                <Chip
                  label={t(`enums.detectionDifficulty.${r.detection_difficulty}`)}
                  size="small"
                  color={difficultyColor[r.detection_difficulty] ?? 'default'}
                />
                {recognitionEnabled && r.has_reference_images && (
                  <Chip
                    icon={<CameraAltOutlinedIcon />}
                    label={t('pages.ipm.recognitionAvailable')}
                    size="small"
                    color="info"
                    variant="outlined"
                  />
                )}
              </>
            }
            fields={[
              ...(r.lifecycle_days != null
                ? [{ label: t('pages.ipm.lifecycleDays'), value: `${r.lifecycle_days}\u202f${t('pages.ipm.days')}` }]
                : []),
            ]}
          />
        )}
      />
      <PestCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchPests({}));
        }}
      />
    </Box>
  );
}
