import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import CloseIcon from '@mui/icons-material/Close';
import Alert from '@mui/material/Alert';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as phasesApi from '@/api/endpoints/phases';
import type { PhaseHistoryEntry } from '@/api/types';

interface Props {
  plantKey: string;
}

function formatDateTime(iso: string | null): string {
  if (!iso) return '-';
  return new Date(iso).toLocaleString();
}

export default function PhaseHistoryTable({ plantKey }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [history, setHistory] = useState<PhaseHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editEnteredAt, setEditEnteredAt] = useState('');
  const [editExitedAt, setEditExitedAt] = useState('');
  const [saving, setSaving] = useState(false);

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
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
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
            <input
              type="datetime-local"
              value={editEnteredAt}
              onChange={(e) => setEditEnteredAt(e.target.value)}
              style={{ fontSize: '0.875rem' }}
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
            <input
              type="datetime-local"
              value={editExitedAt}
              onChange={(e) => setEditExitedAt(e.target.value)}
              style={{ fontSize: '0.875rem' }}
            />
          );
        }
        return formatDateTime(r.exited_at);
      },
    },
    {
      id: 'duration',
      label: t('pages.plantingRuns.duration'),
      render: (r) => (r.actual_duration_days != null ? `${r.actual_duration_days}d` : '-'),
      align: 'right',
    },
    {
      id: 'reason',
      label: t('pages.phases.reason'),
      render: (r) => r.transition_reason || '-',
    },
    {
      id: 'actions',
      label: '',
      width: 90,
      sortable: false,
      searchable: false,
      render: (r) => {
        if (editingKey === r.key) {
          return (
            <Box sx={{ display: 'flex', gap: 0.5 }}>
              <IconButton size="small" onClick={saveEdit} disabled={saving} color="primary">
                {saving ? <CircularProgress size={16} /> : <SaveIcon fontSize="small" />}
              </IconButton>
              <IconButton size="small" onClick={cancelEdit}>
                <CloseIcon fontSize="small" />
              </IconButton>
            </Box>
          );
        }
        return (
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              startEdit(r);
            }}
            title={t('pages.plantingRuns.editPhaseDate')}
          >
            <EditIcon fontSize="small" />
          </IconButton>
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
    return <Alert severity="info">{t('pages.plantingRuns.noPlantsYet')}</Alert>;
  }

  return (
    <DataTable
      columns={columns}
      rows={history}
      getRowKey={(r) => r.key}
      variant="simple"
      ariaLabel={t('pages.plantingRuns.phaseTimeline')}
    />
  );
}
