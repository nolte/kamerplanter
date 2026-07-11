import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import Stack from '@mui/material/Stack';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutlined';
import PageTitle from '@/components/layout/PageTitle';
import DataTable from '@/components/common/DataTable';
import type { Column } from '@/components/common/DataTable';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import HelpTooltip from '@/components/common/HelpTooltip';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useEquipment } from '@/hooks/useEquipment';
import { useTableUrlState } from '@/hooks/useTableState';
import * as api from '@/api/endpoints/inventree';
import type { Equipment, EquipmentStatus } from '@/api/types';
import EquipmentDialog from './EquipmentDialog';

const statusColor: Record<EquipmentStatus, ChipProps['color']> = {
  active: 'success',
  maintenance: 'warning',
  stored: 'info',
  defective: 'error',
  retired: 'default',
};

export default function InventreePage() {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { equipment, connections, loading, reload } = useEquipment();
  const tableState = useTableUrlState({ defaultSort: { column: 'name', direction: 'asc' } });

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Equipment | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Equipment | null>(null);
  const [deleting, setDeleting] = useState(false);

  const handleCreate = useCallback(() => {
    setEditing(null);
    setDialogOpen(true);
  }, []);

  const handleEdit = useCallback((item: Equipment) => {
    setEditing(item);
    setDialogOpen(true);
  }, []);

  const handleSaved = useCallback(() => {
    setDialogOpen(false);
    notification.success(t('pages.inventree.equipmentSaved'));
    reload();
  }, [notification, t, reload]);

  const handleConfirmDelete = useCallback(async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.deleteEquipment(deleteTarget.key);
      notification.success(t('pages.inventree.equipmentDeleted'));
      setDeleteTarget(null);
      reload();
    } catch (error) {
      handleError(error);
    } finally {
      setDeleting(false);
    }
  }, [deleteTarget, notification, t, reload, handleError]);

  const activeConnection = useMemo(
    () => connections.find((c) => c.is_active) ?? null,
    [connections],
  );

  const columns = useMemo<Column<Equipment>[]>(
    () => [
      {
        id: 'name',
        label: t('pages.inventree.fields.name'),
        render: (row) => row.name,
        searchable: true,
        searchValue: (row) => row.name,
        sortable: true,
        sortKey: 'name',
      },
      {
        id: 'equipment_type',
        label: t('pages.inventree.fields.equipmentType'),
        render: (row) => t(`enums.equipmentType.${row.equipment_type}`),
        searchable: true,
        sortable: true,
      },
      {
        id: 'status',
        label: t('pages.inventree.fields.status'),
        render: (row) => (
          <Chip
            size="small"
            label={t(`enums.equipmentStatus.${row.status}`)}
            color={statusColor[row.status]}
          />
        ),
        searchable: true,
        searchValue: (row) => t(`enums.equipmentStatus.${row.status}`),
        sortable: true,
      },
      {
        id: 'inventree',
        label: t('pages.inventree.fields.inventreePartId'),
        render: (row) =>
          row.inventree_part_id != null ? (
            <Chip size="small" variant="outlined" label={`#${row.inventree_part_id}`} />
          ) : (
            <Typography variant="body2" color="text.secondary">
              —
            </Typography>
          ),
        searchable: true,
        searchValue: (row) => (row.inventree_part_id != null ? String(row.inventree_part_id) : ''),
        sortable: true,
        hideBelowBreakpoint: 'md',
      },
      {
        id: 'actions',
        label: t('common.actions'),
        align: 'right',
        searchable: false,
        sortable: false,
        render: (row) => (
          <Stack direction="row" spacing={0.5} sx={{ justifyContent: 'flex-end' }}>
            <Tooltip title={t('common.edit')}>
              <IconButton
                size="small"
                onClick={() => handleEdit(row)}
                aria-label={t('common.edit')}
                data-testid={`edit-equipment-${row.key}`}
              >
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title={t('common.delete')}>
              <IconButton
                size="small"
                color="error"
                onClick={() => setDeleteTarget(row)}
                aria-label={t('common.delete')}
                data-testid={`delete-equipment-${row.key}`}
              >
                <DeleteOutlineIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Stack>
        ),
      },
    ],
    [t, handleEdit],
  );

  return (
    <Box sx={{ p: 3 }} data-testid="inventree-page">
      <PageTitle
        title={t('pages.inventree.title')}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
            data-testid="create-equipment-button"
          >
            {t('pages.inventree.createEquipment')}
          </Button>
        }
      />

      <Typography color="text.secondary" sx={{ mb: 3 }}>
        {t('pages.inventree.intro')}
      </Typography>

      {activeConnection ? (
        <Alert
          severity={activeConnection.last_health_check_ok ? 'success' : 'info'}
          sx={{ mb: 3 }}
          data-testid="inventree-connection-status"
        >
          <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
            <span>{t('pages.inventree.connectionActive', { name: activeConnection.name })}</span>
            <HelpTooltip term="inventree" iconOnly />
          </Stack>
        </Alert>
      ) : (
        <Alert severity="info" sx={{ mb: 3 }} data-testid="inventree-connection-status">
          <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
            <span>{t('pages.inventree.noConnection')}</span>
            <HelpTooltip term="inventree" iconOnly />
          </Stack>
        </Alert>
      )}

      <DataTable
        columns={columns}
        rows={equipment}
        loading={loading}
        getRowKey={(row) => row.key}
        ariaLabel={t('pages.inventree.title')}
        tableState={tableState}
        emptyMessage={t('pages.inventree.emptyTitle')}
        emptyDescription={t('pages.inventree.emptyDescription')}
        emptyActionLabel={t('pages.inventree.createEquipment')}
        onEmptyAction={handleCreate}
      />

      <EquipmentDialog
        open={dialogOpen}
        equipment={editing}
        onClose={() => setDialogOpen(false)}
        onSaved={handleSaved}
      />

      <ConfirmDialog
        open={deleteTarget !== null}
        title={t('pages.inventree.deleteTitle')}
        message={t('pages.inventree.deleteConfirm', { name: deleteTarget?.name ?? '' })}
        confirmLabel={t('common.delete')}
        destructive
        loading={deleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </Box>
  );
}
