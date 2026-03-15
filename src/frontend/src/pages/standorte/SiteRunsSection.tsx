import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import DataTable, { type Column } from '@/components/common/DataTable';
import EmptyState from '@/components/common/EmptyState';
import { useApiError } from '@/hooks/useApiError';
import { useTableLocalState } from '@/hooks/useTableState';
import * as siteApi from '@/api/endpoints/sites';
import * as runApi from '@/api/endpoints/plantingRuns';
import type { PlantingRun, PlantingRunStatus, Location } from '@/api/types';

const statusColor: Record<PlantingRunStatus, ChipProps['color']> = {
  planned: 'default',
  active: 'primary',
  harvesting: 'warning',
  completed: 'success',
  cancelled: 'error',
};

interface Props {
  siteKey: string;
}

export default function SiteRunsSection({ siteKey }: Props) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { handleError } = useApiError();
  const [runs, setRuns] = useState<PlantingRun[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(false);
  const tableState = useTableLocalState({ defaultSort: { column: 'name', direction: 'asc' } });

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const [locs, allRuns] = await Promise.all([
          siteApi.listLocations(siteKey),
          runApi.listPlantingRuns(0, 200),
        ]);
        if (cancelled) return;
        setLocations(locs);
        const locKeys = new Set(locs.map((l) => l.key));
        setRuns(allRuns.filter((r) => r.location_key && locKeys.has(r.location_key)));
      } catch (err) {
        if (!cancelled) handleError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [siteKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const locationNameMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const loc of locations) {
      map.set(loc.key, loc.name);
    }
    return map;
  }, [locations]);

  const columns: Column<PlantingRun>[] = [
    { id: 'name', label: t('pages.plantingRuns.name'), render: (r) => r.name },
    {
      id: 'location',
      label: t('pages.plantingRuns.location'),
      render: (r) => (r.location_key ? locationNameMap.get(r.location_key) ?? '—' : '—'),
      searchValue: (r) => (r.location_key ? locationNameMap.get(r.location_key) ?? '' : ''),
    },
    {
      id: 'status',
      label: t('pages.plantingRuns.status'),
      render: (r) => (
        <Chip
          label={t(`enums.plantingRunStatus.${r.status}`)}
          size="small"
          color={statusColor[r.status] ?? 'default'}
        />
      ),
      searchValue: (r) => t(`enums.plantingRunStatus.${r.status}`),
    },
    {
      id: 'phase',
      label: t('pages.plantingRuns.currentPhase'),
      render: (r) => {
        if (!r.phase_summary || r.status === 'planned') return '—';
        const { dominant_phase, dominant_phase_count, total_plant_count } = r.phase_summary;
        if (!dominant_phase) return '—';
        return (
          <Chip
            label={`${dominant_phase} (${dominant_phase_count}/${total_plant_count})`}
            size="small"
            color="info"
          />
        );
      },
      searchValue: (r) => r.phase_summary?.dominant_phase ?? '',
    },
    {
      id: 'plants',
      label: t('entities.plantInstances'),
      render: (r) => `${r.actual_quantity} / ${r.planned_quantity}`,
      align: 'right',
      searchValue: (r) => `${r.actual_quantity} ${r.planned_quantity}`,
    },
  ];

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>{t('entities.plantingRuns')}</Typography>
      {!loading && runs.length === 0 ? (
        <EmptyState message={t('pages.sites.noRuns')} />
      ) : (
        <DataTable
          columns={columns}
          rows={runs}
          loading={loading}
          onRowClick={(r) => navigate(`/durchlaeufe/planting-runs/${r.key}`)}
          getRowKey={(r) => r.key}
          tableState={tableState}
          ariaLabel={t('entities.plantingRuns')}
        />
      )}
    </Box>
  );
}
