import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import AddIcon from '@mui/icons-material/Add';
import PageTitle from '@/components/layout/PageTitle';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchWateringEvents } from '@/store/slices/wateringEventsSlice';
import { useTableUrlState } from '@/hooks/useTableState';
import type { WateringEvent } from '@/api/types';
import WateringEventCreateDialog from './WateringEventCreateDialog';

export default function WateringEventListPage() {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const { events, loading } = useAppSelector((s) => s.wateringEvents);
  const [createOpen, setCreateOpen] = useState(false);
  const tableState = useTableUrlState({
    defaultSort: { column: 'wateredAt', direction: 'desc' },
  });

  useEffect(() => {
    dispatch(fetchWateringEvents({}));
  }, [dispatch]);

  const columns: Column<WateringEvent>[] = [
    {
      id: 'wateredAt',
      label: t('pages.wateringEvents.wateredAt'),
      render: (r) =>
        r.watered_at ? new Date(r.watered_at).toLocaleString() : '—',
      searchValue: (r) =>
        r.watered_at ? new Date(r.watered_at).toLocaleString() : '',
    },
    {
      id: 'applicationMethod',
      label: t('pages.wateringEvents.applicationMethod'),
      render: (r) => t(`enums.applicationMethod.${r.application_method}`),
      searchValue: (r) => t(`enums.applicationMethod.${r.application_method}`),
    },
    {
      id: 'isSupplemental',
      label: t('pages.wateringEvents.isSupplemental'),
      render: (r) =>
        r.is_supplemental ? (
          <Chip label={t('common.yes')} size="small" color="info" />
        ) : null,
    },
    {
      id: 'volume',
      label: t('pages.wateringEvents.volumeLiters'),
      render: (r) => `${r.volume_liters} L`,
      align: 'right',
      searchValue: (r) => String(r.volume_liters),
    },
    {
      id: 'slots',
      label: t('pages.wateringEvents.slotKeys'),
      render: (r) => String(r.slot_keys.length),
      align: 'right',
    },
    {
      id: 'waterSource',
      label: t('pages.wateringEvents.waterSource'),
      render: (r) =>
        r.water_source ? t(`enums.waterSource.${r.water_source}`) : '—',
      searchValue: (r) =>
        r.water_source ? t(`enums.waterSource.${r.water_source}`) : '',
    },
  ];

  return (
    <Box data-testid="watering-event-list-page">
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <PageTitle title={t('pages.wateringEvents.title')} />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
          data-testid="create-button"
        >
          {t('pages.wateringEvents.create')}
        </Button>
      </Box>
      <DataTable
        columns={columns}
        rows={events}
        loading={loading}
        getRowKey={(r) => r.key}
        emptyActionLabel={t('pages.wateringEvents.create')}
        onEmptyAction={() => setCreateOpen(true)}
        tableState={tableState}
        ariaLabel={t('pages.wateringEvents.title')}
      />
      <WateringEventCreateDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          dispatch(fetchWateringEvents({}));
        }}
      />
    </Box>
  );
}
