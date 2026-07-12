import { useCallback, useMemo, useState } from 'react';
import type { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import PageTitle from '@/components/layout/PageTitle';
import DataTable from '@/components/common/DataTable';
import type { Column } from '@/components/common/DataTable';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import MobileCard from '@/components/common/MobileCard';
import HelpTooltip from '@/components/common/HelpTooltip';
import { TabPanel, tabA11yProps } from '@/components/common/TabPanel';
import { useNotification } from '@/hooks/useNotification';
import { useTabUrl } from '@/hooks/useTabUrl';
import { usePropagationEvents } from '@/hooks/usePropagationEvents';
import type { PropagationEvent, PropagationEventStatus } from '@/api/types';
import { formatDate } from '@/utils/formatting';
import PropagationEventDialog from './PropagationEventDialog';
import LineagePanel from './LineagePanel';

/** URL hash anchors for the two tabs — index 0 (#'') = events, #lineage = lineage. */
const PROPAGATION_TABS = ['events', 'lineage'] as const;

const statusColor: Record<PropagationEventStatus, ChipProps['color']> = {
  in_progress: 'info',
  rooted: 'primary',
  transplanted: 'secondary',
  completed: 'success',
  failed: 'error',
};

export default function PropagationPage(): ReactElement {
  const { t } = useTranslation();
  const notification = useNotification();
  const { events, loading, reload } = usePropagationEvents();

  const [tab, setTab] = useTabUrl(PROPAGATION_TABS);
  const [dialogOpen, setDialogOpen] = useState(false);

  const handleCreated = useCallback(() => {
    setDialogOpen(false);
    notification.success(t('pages.propagation.eventCreated'));
    reload();
  }, [notification, t, reload]);

  const columns = useMemo<Column<PropagationEvent>[]>(
    () => [
      {
        id: 'method',
        label: t('pages.propagation.fields.method'),
        searchValue: (row) => t(`enums.propagationEventMethod.${row.method}`),
        render: (row) => (
          <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.25 }}>
            <span>{t(`enums.propagationEventMethod.${row.method}`)}</span>
            <HelpTooltip term="vermehrung" iconOnly />
          </Box>
        ),
      },
      {
        id: 'status',
        label: t('pages.propagation.fields.status'),
        searchValue: (row) => t(`enums.propagationEventStatus.${row.status}`),
        render: (row) => (
          <Chip
            size="small"
            label={t(`enums.propagationEventStatus.${row.status}`)}
            color={statusColor[row.status]}
          />
        ),
      },
      {
        id: 'quantity',
        label: t('pages.propagation.fields.quantity'),
        align: 'right',
        render: (row) => row.quantity,
      },
      {
        id: 'survived',
        label: t('pages.propagation.fields.survived'),
        align: 'right',
        render: (row) =>
          row.survived_count == null ? '—' : `${row.survived_count} / ${row.quantity}`,
      },
      {
        id: 'successRate',
        label: t('pages.propagation.fields.successRate'),
        align: 'right',
        render: (row) =>
          row.success_rate == null ? '—' : `${Math.round(row.success_rate * 100)} %`,
      },
      {
        id: 'happenedAt',
        label: t('pages.propagation.fields.happenedAt'),
        hideBelowBreakpoint: 'md',
        render: (row) => formatDate(row.happened_at),
      },
    ],
    [t],
  );

  return (
    <Box sx={{ p: 3 }} data-testid="propagation-page">
      <PageTitle
        title={t('pages.propagation.title')}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setDialogOpen(true)}
            data-testid="create-event-button"
            sx={{ minHeight: 48 }}
          >
            {t('pages.propagation.createEvent')}
          </Button>
        }
      />

      <Typography color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.propagation.intro')}
      </Typography>

      <Tabs
        value={tab}
        onChange={(_e, v: number) => setTab(v)}
        sx={{ mb: 2 }}
        aria-label={t('pages.propagation.title')}
      >
        <Tab
          label={t('pages.propagation.tabs.events')}
          data-testid="tab-events"
          {...tabA11yProps('propagation', 0)}
        />
        <Tab
          label={t('pages.propagation.tabs.lineage')}
          data-testid="tab-lineage"
          {...tabA11yProps('propagation', 1)}
        />
      </Tabs>

      <TabPanel index={0} value={tab} idPrefix="propagation">
        {loading ? (
          <LoadingSkeleton variant="table" />
        ) : (
          <DataTable
            columns={columns}
            rows={events}
            getRowKey={(row) => row._key ?? ''}
            ariaLabel={t('pages.propagation.tabs.events')}
            emptyMessage={t('pages.propagation.emptyTitle')}
            emptyDescription={t('pages.propagation.emptyDescription')}
            emptyActionLabel={t('pages.propagation.createEvent')}
            onEmptyAction={() => setDialogOpen(true)}
            mobileCardRenderer={(row) => (
              <MobileCard
                title={t(`enums.propagationEventMethod.${row.method}`)}
                subtitle={formatDate(row.happened_at)}
                chips={
                  <Chip
                    size="small"
                    label={t(`enums.propagationEventStatus.${row.status}`)}
                    color={statusColor[row.status]}
                  />
                }
                fields={[
                  { label: t('pages.propagation.fields.quantity'), value: row.quantity },
                  {
                    label: t('pages.propagation.fields.survived'),
                    value:
                      row.survived_count == null
                        ? '—'
                        : `${row.survived_count} / ${row.quantity}`,
                  },
                  {
                    label: t('pages.propagation.fields.successRate'),
                    value:
                      row.success_rate == null
                        ? '—'
                        : `${Math.round(row.success_rate * 100)} %`,
                  },
                ]}
              />
            )}
          />
        )}
      </TabPanel>

      <TabPanel index={1} value={tab} idPrefix="propagation">
        <LineagePanel />
      </TabPanel>

      <PropagationEventDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onCreated={handleCreated}
      />
    </Box>
  );
}
