import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import Chip from '@mui/material/Chip';
import DataTable, { type Column } from '@/components/common/DataTable';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useTableLocalState } from '@/hooks/useTableState';
import CultivarCreateDialog from './CultivarCreateDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/species';
import type { Cultivar } from '@/api/types';

interface Props {
  speciesKey: string;
}

export default function CultivarListSection({ speciesKey }: Props) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [cultivars, setCultivars] = useState<Cultivar[]>([]);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Cultivar | null>(null);
  const tableState = useTableLocalState({ defaultSort: { column: 'name', direction: 'asc' } });

  const load = async () => {
    setLoading(true);
    try {
      setCultivars(await api.listCultivars(speciesKey));
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [speciesKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const onDelete = async () => {
    if (!deleteTarget) return;
    try {
      await api.deleteCultivar(speciesKey, deleteTarget.key);
      notification.success(t('common.delete'));
      load();
    } catch (err) {
      handleError(err);
    }
    setDeleteTarget(null);
  };

  const columns: Column<Cultivar>[] = [
    { id: 'name', label: t('pages.cultivars.name'), render: (r) => r.name },
    { id: 'breeder', label: t('pages.cultivars.breeder'), render: (r) => r.breeder ?? '-' },
    {
      id: 'traits',
      label: t('pages.cultivars.traits'),
      render: (r) => (
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
          {r.traits.map((tr) => (
            <Chip key={tr} label={t(`enums.plantTrait.${tr}`)} size="small" />
          ))}
        </Box>
      ),
    },
    {
      id: 'maturity',
      label: t('pages.cultivars.daysToMaturity'),
      render: (r) => r.days_to_maturity ?? '-',
      align: 'right',
    },
    {
      id: 'actions',
      label: t('common.actions'),
      width: 60,
      sortable: false,
      searchable: false,
      render: (r) => (
        <IconButton size="small" aria-label={t('common.delete')} onClick={(e) => { e.stopPropagation(); setDeleteTarget(r); }}>
          <DeleteIcon fontSize="small" />
        </IconButton>
      ),
    },
  ];

  return (
    <Box sx={{ mt: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">{t('pages.cultivars.title')}</Typography>
        <Button startIcon={<AddIcon />} onClick={() => setCreateOpen(true)} data-testid="create-button">
          {t('pages.cultivars.create')}
        </Button>
      </Box>

      <DataTable columns={columns} rows={cultivars} loading={loading} getRowKey={(r) => r.key} onRowClick={(r) => navigate(`/stammdaten/species/${speciesKey}/cultivars/${r.key}`)} tableState={tableState} ariaLabel={t('pages.cultivars.title')} />

      <CultivarCreateDialog
        speciesKey={speciesKey}
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => { setCreateOpen(false); load(); }}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: deleteTarget?.name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteTarget(null)}
        destructive
      />
    </Box>
  );
}
