import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import AddIcon from '@mui/icons-material/Add';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchFeedingEvents } from '@/store/slices/feedingEventsSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { FeedingEvent } from '@/api/types';
import FeedingEventCreateDialog from './FeedingEventCreateDialog';

export default function FeedingEventListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { events, loading } = useAppSelector((s) => s.feedingEvents);
  const [createOpen, setCreateOpen] = useState(false);
  const tableState = useTableUrlState({
    defaultSort: { column: 'timestamp', direction: 'desc' },
  });

  useEffect(() => {
    dispatch(fetchFeedingEvents({}));
  }, [dispatch]);

  const columns: Column<FeedingEvent>[] = [
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
      render: (r) => r.plant_key,
    },
    {
      id: 'applicationMethod',
      label: t('pages.feedingEvents.applicationMethod'),
      render: (r) => t(`enums.applicationMethod.${r.application_method}`),
      searchValue: (r) => t(`enums.applicationMethod.${r.application_method}`),
    },
    {
      id: 'volume',
      label: t('pages.feedingEvents.volumeApplied'),
      render: (r) => `${r.volume_applied_liters} L`,
      align: 'right',
      searchValue: (r) => String(r.volume_applied_liters),
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
        r.measured_ec_after != null ? `${r.measured_ec_after} mS` : '—',
      align: 'right',
    },
  ];

  return (
    <Box data-testid="feeding-event-list-page">
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <PageTitle title={t('pages.feedingEvents.title')} />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
          data-testid="create-button"
        >
          {t('pages.feedingEvents.create')}
        </Button>
      </Box>
      <DataTable
        columns={columns}
        rows={events}
        loading={loading}
        onRowClick={(r) => navigate(`/duengung/feeding-events/${r.key}`)}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.feedingEvents.create')}
        onEmptyAction={() => setCreateOpen(true)}
        tableState={tableState}
        ariaLabel={t('pages.feedingEvents.title')}
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
