import { useEffect, useState, useMemo } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import AddIcon from '@mui/icons-material/Add';
import SpaIcon from '@mui/icons-material/Spa';
import MobileCard from '@/components/common/MobileCard';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchFeedingEvents } from '@/store/slices/feedingEventsSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { FeedingEvent, PlantInstance } from '@/api/types';
import { getPlantLabel } from '@/utils/plantDisplay';
import * as plantApi from '@/api/endpoints/plantInstances';
import FeedingEventCreateDialog from './FeedingEventCreateDialog';
import { formatFeedingAmount } from './feedingEventDose';
import { kamiFertilizer } from '@/assets/brand/illustrations';

export default function FeedingEventListPage() {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { events, loading } = useAppSelector((s) => s.feedingEvents);
  const [createOpen, setCreateOpen] = useState(false);
  const [plantMap, setPlantMap] = useState<Map<string, PlantInstance>>(new Map());
  const tableState = useTableUrlState({
    defaultSort: { column: 'timestamp', direction: 'desc' },
  });

  useEffect(() => {
    dispatch(fetchFeedingEvents({}));
  }, [dispatch]);

  // Resolve plant_key → PlantInstance for display names
  const plantKeys = useMemo(
    () => [...new Set(events.map((e) => e.plant_key).filter(Boolean))],
    [events],
  );

  useEffect(() => {
    if (plantKeys.length === 0) return;
    let cancelled = false;

    async function resolve() {
      const plants = await plantApi.listAllPlantInstances();
      if (cancelled) return;
      const map = new Map<string, PlantInstance>();
      for (const p of plants) {
        map.set(p.key, p);
      }
      setPlantMap(map);
    }

    resolve().catch(() => {});
    return () => { cancelled = true; };
  }, [plantKeys]);

  const columns: Column<FeedingEvent>[] = useMemo(() => [
    {
      id: 'timestamp',
      label: t('pages.feedingEvents.timestamp'),
      render: (r) =>
        r.timestamp ? new Date(r.timestamp).toLocaleString() : '—',
      searchValue: (r) =>
        r.timestamp ? new Date(r.timestamp).toLocaleString() : '',
    },
    {
      id: 'plantKey',
      label: t('pages.feedingEvents.plantKey'),
      render: (r) => {
        const plant = plantMap.get(r.plant_key);
        const name = plant ? getPlantLabel(plant, i18n.language) : r.plant_key;
        return (
          <Chip
            icon={<SpaIcon />}
            label={name}
            size="small"
            color="success"
            variant="outlined"
            component={RouterLink}
            to={`/pflanzen/plant-instances/${r.plant_key}`}
            clickable
            onClick={(e: React.MouseEvent) => e.stopPropagation()}
            sx={{ maxWidth: 'none' }}
          />
        );
      },
      searchValue: (r) => {
        const plant = plantMap.get(r.plant_key);
        return plant ? getPlantLabel(plant, i18n.language) : r.plant_key;
      },
    },
    {
      id: 'applicationMethod',
      label: t('pages.feedingEvents.applicationMethod'),
      render: (r) => t(`enums.applicationMethod.${r.application_method}`),
      searchValue: (r) => t(`enums.applicationMethod.${r.application_method}`),
    },
    {
      id: 'volume',
      // A solution's litres or a top dress's dose (#2903) - never "0 L" for compost.
      label: t('pages.feedingEvents.amount'),
      render: (r) => formatFeedingAmount(t, r),
      align: 'right',
      // A number for a solution, so the column keeps sorting by litres; a top dress's dose as shown.
      searchValue: (r) =>
        r.volume_applied_liters > 0 ? String(r.volume_applied_liters) : formatFeedingAmount(t, r),
    },
    {
      id: 'isSupplemental',
      label: t('pages.feedingEvents.isSupplemental'),
      render: (r) =>
        r.is_supplemental ? (
          <Chip label={t('common.yes')} size="small" color="info" />
        ) : null,
    },
    {
      id: 'ecAfter',
      label: t('pages.feedingEvents.ecAfter'),
      render: (r) =>
        r.measured_ec_after != null ? `${r.measured_ec_after} mS/cm` : '—',
      align: 'right',
      searchValue: (r) => r.measured_ec_after != null ? String(r.measured_ec_after) : '',
    },
  ], [t, plantMap, i18n.language]);

  return (
    <Box data-testid="feeding-event-list-page">
      <PageTitle
        title={t('pages.feedingEvents.title')}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateOpen(true)}
            data-testid="create-button"
          >
            {t('pages.feedingEvents.create')}
          </Button>
        }
      />
      <DataTable
        columns={columns}
        rows={events}
        loading={loading}
        onRowClick={(r) => navigate(`/duengung/feeding-events/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.feedingEvents.create')}
        onEmptyAction={() => setCreateOpen(true)}
        emptyIllustration={kamiFertilizer}
        tableState={tableState}
        ariaLabel={t('pages.feedingEvents.title')}
        mobileCardRenderer={(r) => {
          const plant = plantMap.get(r.plant_key);
          const plantName = plant ? getPlantLabel(plant, i18n.language) : r.plant_key;
          return (
            <MobileCard
              title={plantName}
              titleId="plantKey"
              subtitle={r.timestamp ? new Date(r.timestamp).toLocaleString() : undefined}
              subtitleId="timestamp"
              chips={[
                {
                  id: 'applicationMethod',
                  content: (
                    <Chip
                      label={t(`enums.applicationMethod.${r.application_method}`)}
                      size="small"
                      variant="outlined"
                    />
                  ),
                },
                ...(r.is_supplemental
                  ? [
                      {
                        id: 'isSupplemental',
                        content: <Chip label={t('common.yes')} size="small" color="info" />,
                      },
                    ]
                  : []),
              ]}
              fields={[
                { id: 'volume', label: t('pages.feedingEvents.amount'), value: formatFeedingAmount(t, r) },
                ...(r.measured_ec_after != null
                  ? [{ id: 'ecAfter', label: t('pages.feedingEvents.ecAfter'), value: `${r.measured_ec_after} mS/cm` }]
                  : []),
              ]}
            />
          );
        }}
      />
      <FeedingEventCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchFeedingEvents({}));
        }}
      />
    </Box>
  );
}
