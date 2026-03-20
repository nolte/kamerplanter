import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import CloseIcon from '@mui/icons-material/Close';
import DeleteIcon from '@mui/icons-material/Delete';
import EmptyState from '@/components/common/EmptyState';
import MobileCard from '@/components/common/MobileCard';
import DataTable, { type Column } from '@/components/common/DataTable';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as phasesApi from '@/api/endpoints/phases';
import type { PhaseHistoryEntry } from '@/api/types';

interface Props {
  plantKey: string;
  onChanged?: () => void;
}

function formatDateTime(iso: string | null): string {
  if (!iso) return '\u2014';
  return new Date(iso).toLocaleString();
}

export default function PhaseHistoryTable({ plantKey, onChanged }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [history, setHistory] = useState<PhaseHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editEnteredAt, setEditEnteredAt] = useState('');
  const [editExitedAt, setEditExitedAt] = useState('');
  const [saving, setSaving] = useState(false);
  const [deleteKey, setDeleteKey] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const loadHistory = () => {
    setLoading(true);
    phasesApi
      .getPhaseHistory(plantKey)
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadHistory();
  }, [plantKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const startEdit = (entry: PhaseHistoryEntry) => {
    setEditingKey(entry.key);
    // Convert to local datetime-local format
    setEditEnteredAt(entry.entered_at ? entry.entered_at.slice(0, 16) : '');
    setEditExitedAt(entry.exited_at ? entry.exited_at.slice(0, 16) : '');
  };

  const cancelEdit = () => {
    setEditingKey(null);
    setEditEnteredAt('');
    setEditExitedAt('');
  };

  const saveEdit = async () => {
    if (!editingKey) return;
    try {
      setSaving(true);
      const payload: { entered_at?: string; exited_at?: string } = {};
      if (editEnteredAt) payload.entered_at = new Date(editEnteredAt).toISOString();
      if (editExitedAt) payload.exited_at = new Date(editExitedAt).toISOString();
      await phasesApi.updatePhaseHistoryDates(plantKey, editingKey, payload);
      notification.success(t('pages.plantingRuns.phaseDateUpdated'));
      cancelEdit();
      loadHistory();
      onChanged?.();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteKey) return;
    try {
      setDeleting(true);
      await phasesApi.deletePhaseHistory(plantKey, deleteKey);
      notification.success(t('pages.phases.phaseDeleted'));
      setDeleteKey(null);
      loadHistory();
      onChanged?.();
    } catch (err) {
      handleError(err);
    } finally {
      setDeleting(false);
    }
  };

  const columns: Column<PhaseHistoryEntry>[] = [
    {
      id: 'phase',
      label: t('entities.phase'),
      render: (r) => <Chip label={r.phase_name} size="small" color="primary" />,
      searchValue: (r) => r.phase_name,
    },
    {
      id: 'enteredAt',
      label: t('pages.plantingRuns.actualStart'),
      render: (r) => {
        if (editingKey === r.key) {
          return (
            <TextField
              type="datetime-local"
              size="small"
              value={editEnteredAt}
              onChange={(e) => setEditEnteredAt(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
              sx={{ minWidth: 180 }}
            />
          );
        }
        return formatDateTime(r.entered_at);
      },
    },
    {
      id: 'exitedAt',
      label: t('pages.plantingRuns.actualEnd'),
      render: (r) => {
        if (editingKey === r.key) {
          return (
            <TextField
              type="datetime-local"
              size="small"
              value={editExitedAt}
              onChange={(e) => setEditExitedAt(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
              sx={{ minWidth: 180 }}
            />
          );
        }
        return formatDateTime(r.exited_at);
      },
    },
    {
      id: 'duration',
      label: t('pages.plantingRuns.duration'),
      render: (r) => (r.actual_duration_days != null ? `${r.actual_duration_days}d` : '\u2014'),
      align: 'right',
    },
    {
      id: 'reason',
      label: t('pages.phases.reason'),
      render: (r) => r.transition_reason || '\u2014',
    },
    {
      id: 'actions',
      label: '',
      width: 120,
      sortable: false,
      searchable: false,
      render: (r) => {
        if (editingKey === r.key) {
          return (
            <Box sx={{ display: 'flex', gap: 0.5 }}>
              <Tooltip title={t('common.save')}>
                <IconButton
                  size="small"
                  onClick={saveEdit}
                  disabled={saving}
                  color="primary"
                  aria-label={t('common.save')}
                  data-testid="save-phase-date-button"
                >
                  {saving ? <CircularProgress size={16} /> : <SaveIcon fontSize="small" />}
                </IconButton>
              </Tooltip>
              <Tooltip title={t('common.cancel')}>
                <IconButton
                  size="small"
                  onClick={cancelEdit}
                  aria-label={t('common.cancel')}
                  data-testid="cancel-phase-date-button"
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          );
        }
        return (
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <Tooltip title={t('pages.plantingRuns.editPhaseDate')}>
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  startEdit(r);
                }}
                aria-label={t('pages.plantingRuns.editPhaseDate')}
                data-testid={`edit-phase-date-${r.key}`}
              >
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title={t('common.delete')}>
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  setDeleteKey(r.key);
                }}
                color="error"
                aria-label={t('common.delete')}
                data-testid={`delete-phase-${r.key}`}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        );
      },
    },
  ];

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (history.length === 0) {
    return <EmptyState message={t('pages.plantingRuns.noPlantsYet')} />;
  }

  return (
    <>
      <DataTable
        columns={columns}
        rows={history}
        getRowKey={(r) => r.key}
        variant="simple"
        ariaLabel={t('pages.plantingRuns.phaseTimeline')}
        mobileCardRenderer={(r) => (
          <MobileCard
            title={r.phase_name}
            subtitle={formatDateTime(r.entered_at)}
            chips={
              <Chip label={r.phase_name} size="small" color="primary" />
            }
            fields={[
              ...(r.actual_duration_days != null ? [{ label: t('pages.plantingRuns.duration'), value: `${r.actual_duration_days}d` }] : []),
              ...(r.transition_reason ? [{ label: t('pages.phases.reason'), value: r.transition_reason }] : []),
            ]}
          />
        )}
      />
      <ConfirmDialog
        open={!!deleteKey}
        title={t('pages.phases.deletePhaseTitle')}
        message={t('pages.phases.deletePhaseMessage')}
        onConfirm={handleDelete}
        onCancel={() => setDeleteKey(null)}
        loading={deleting}
      />
    </>
  );
}
