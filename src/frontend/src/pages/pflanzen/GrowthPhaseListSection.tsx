import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
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
import GrowthPhaseDialog from './GrowthPhaseDialog';
import ProfilesSection from './ProfilesSection';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as phasesApi from '@/api/endpoints/phases';
import type { GrowthPhase } from '@/api/types';

interface Props {
  lifecycleKey: string;
}

export default function GrowthPhaseListSection({ lifecycleKey }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [phases, setPhases] = useState<GrowthPhase[]>([]);
  const [loading, setLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editPhase, setEditPhase] = useState<GrowthPhase | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<GrowthPhase | null>(null);
  const [selectedPhase, setSelectedPhase] = useState<GrowthPhase | null>(null);
  const tableState = useTableLocalState({ defaultSort: { column: 'order', direction: 'asc' } });

  const load = async () => {
    setLoading(true);
    try {
      const items = await phasesApi.listGrowthPhases(lifecycleKey);
      setPhases(items.sort((a, b) => a.sequence_order - b.sequence_order));
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [lifecycleKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const onDelete = async () => {
    if (!deleteTarget) return;
    try {
      await phasesApi.deleteGrowthPhase(deleteTarget.key);
      notification.success(t('common.delete'));
      load();
    } catch (err) {
      handleError(err);
    }
    setDeleteTarget(null);
  };

  const columns: Column<GrowthPhase>[] = [
    { id: 'order', label: '#', width: 50, render: (r) => r.sequence_order, align: 'right' as const },
    { id: 'name', label: t('pages.growthPhases.name'), render: (r) => r.display_name || r.name },
    { id: 'duration', label: t('pages.growthPhases.duration'), render: (r) => `${r.typical_duration_days}d`, align: 'right' as const, searchValue: (r: GrowthPhase) => String(r.typical_duration_days) },
    {
      id: 'watering',
      label: t('pages.growthPhases.wateringInterval'),
      render: (r) => r.watering_interval_days != null ? `${r.watering_interval_days}d` : '—',
      align: 'right' as const,
      searchValue: (r: GrowthPhase) => r.watering_interval_days != null ? String(r.watering_interval_days) : '',
    },
    {
      id: 'stress',
      label: t('pages.growthPhases.stressTolerance'),
      render: (r) => t(`enums.stressTolerance.${r.stress_tolerance}`),
      searchValue: (r: GrowthPhase) => t(`enums.stressTolerance.${r.stress_tolerance}`),
    },
    {
      id: 'flags',
      label: '',
      render: (r) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {r.is_terminal && <Chip label={t('pages.growthPhases.isTerminal')} size="small" color="warning" />}
          {r.allows_harvest && <Chip label={t('pages.growthPhases.allowsHarvest')} size="small" color="success" />}
        </Box>
      ),
      searchValue: (r: GrowthPhase) => [
        r.is_terminal ? t('pages.growthPhases.isTerminal') : '',
        r.allows_harvest ? t('pages.growthPhases.allowsHarvest') : '',
      ].filter(Boolean).join(' '),
    },
    {
      id: 'actions',
      label: t('common.actions'),
      width: 120,
      sortable: false,
      searchable: false,
      render: (r) => (
        <Box>
          <Button size="small" onClick={(e) => { e.stopPropagation(); setSelectedPhase(r); }}>
            {t('entities.profile')}
          </Button>
          <IconButton size="small" aria-label={t('common.delete')} onClick={(e) => { e.stopPropagation(); setDeleteTarget(r); }}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Box>
      ),
    },
  ];

  return (
    <Box sx={{ mt: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">{t('pages.growthPhases.title')}</Typography>
        <Button startIcon={<AddIcon />} onClick={() => { setEditPhase(null); setDialogOpen(true); }}>
          {t('pages.growthPhases.create')}
        </Button>
      </Box>

      <DataTable
        columns={columns}
        rows={phases}
        loading={loading}
        onRowClick={(r) => { setEditPhase(r); setDialogOpen(true); }}
        getRowKey={(r) => r.key}
        tableState={tableState}
        ariaLabel={t('pages.growthPhases.title')}
      />

      <GrowthPhaseDialog
        lifecycleKey={lifecycleKey}
        phase={editPhase}
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSaved={() => { setDialogOpen(false); load(); }}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: deleteTarget?.name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteTarget(null)}
        destructive
      />

      {selectedPhase && <ProfilesSection phaseKey={selectedPhase.key} phaseName={selectedPhase.display_name || selectedPhase.name} />}
    </Box>
  );
}
