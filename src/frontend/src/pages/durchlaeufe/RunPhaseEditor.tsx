import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import TextField from '@mui/material/TextField';
import Alert from '@mui/material/Alert';
import Tooltip from '@mui/material/Tooltip';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import CloseIcon from '@mui/icons-material/Close';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RadioButtonCheckedIcon from '@mui/icons-material/RadioButtonChecked';
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import EmptyState from '@/components/common/EmptyState';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import { errorKey } from '@/api/errors';
import { captureHandledError } from '@/observability/errorTracking';
import MobileCard from '@/components/common/MobileCard';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as runApi from '@/api/endpoints/plantingRuns';
import type { SpeciesPhaseTimeline, PhaseTimelineEntry } from '@/api/types';
import { toLocalIsoDate } from '@/utils/calendarDay';

interface Props {
  runKey: string;
  isActive: boolean;
  onPhaseDatesChanged?: () => void;
}

function toDateInputValue(iso: string | null): string {
  if (!iso) return '';
  // The local day: the save path writes `<day>T00:00:00` local time back, so reading the UTC day
  // showed the day before for every zone east of UTC.
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '' : toLocalIsoDate(d);
}

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString();
}

function computeDurationDays(start: string | null, end: string | null): number | null {
  if (!start) return null;
  const startDate = new Date(start);
  const endDate = end ? new Date(end) : new Date();
  const diff = endDate.getTime() - startDate.getTime();
  return Math.max(0, Math.floor(diff / 86400000));
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'completed') return <CheckCircleIcon color="success" fontSize="small" />;
  if (status === 'current') return <RadioButtonCheckedIcon color="primary" fontSize="small" />;
  return <RadioButtonUncheckedIcon color="disabled" fontSize="small" />;
}

export default function RunPhaseEditor({ runKey, isActive, onPhaseDatesChanged }: Props) {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [timelines, setTimelines] = useState<SpeciesPhaseTimeline[]>([]);
  const [loading, setLoading] = useState(true);
  // A failed read is shown with a retry, never as "no plants yet" (#3037).
  const [loadError, setLoadError] = useState<string | null>(null);
  const [editingPhaseKey, setEditingPhaseKey] = useState<string | null>(null);
  const [editEnteredAt, setEditEnteredAt] = useState('');
  const [editExitedAt, setEditExitedAt] = useState('');
  const [saving, setSaving] = useState(false);

  const loadTimelines = () => {
    setLoading(true);
    runApi
      .getPhaseTimeline(runKey)
      .then((data) => {
        setTimelines(data);
        setLoadError(null);
      })
      .catch((err: unknown) => {
        captureHandledError(err, { source: 'RunPhaseEditor' });
        setTimelines([]);
        setLoadError(errorKey(err, 'errors.loadFailed'));
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadTimelines();
  }, [runKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const startEdit = (phase: PhaseTimelineEntry) => {
    setEditingPhaseKey(phase.phase_key);
    setEditEnteredAt(toDateInputValue(phase.actual_entered_at ?? phase.projected_start));
    setEditExitedAt(toDateInputValue(phase.actual_exited_at));
  };

  const cancelEdit = () => {
    setEditingPhaseKey(null);
    setEditEnteredAt('');
    setEditExitedAt('');
  };

  const saveEdit = async () => {
    if (!editingPhaseKey) return;
    try {
      setSaving(true);
      const payload: runApi.BatchUpdatePhaseDatesRequest = {
        phase_key: editingPhaseKey,
      };
      if (editEnteredAt) {
        payload.entered_at = new Date(editEnteredAt + 'T00:00:00').toISOString();
      }
      if (editExitedAt) {
        payload.exited_at = new Date(editExitedAt + 'T23:59:59').toISOString();
      }
      const result = await runApi.batchUpdatePhaseDates(runKey, payload);
      notification.success(
        t('pages.plantingRuns.bulkPhaseDateUpdated', { count: result.updated_count }),
      );
      cancelEdit();
      loadTimelines();
      onPhaseDatesChanged?.();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (loadError) {
    return <ErrorDisplay error={loadError} onRetry={loadTimelines} />;
  }

  if (timelines.length === 0) {
    return <EmptyState message={t('pages.plantingRuns.noPlantsYet')} />;
  }

  const columns: Column<PhaseTimelineEntry>[] = [
    {
      id: 'status',
      label: '',
      width: 40,
      sortable: false,
      searchable: false,
      render: (r) => <StatusIcon status={r.status} />,
    },
    {
      id: 'phase',
      label: t('entities.phase'),
      render: (r) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="body2">{r.display_name || r.phase_name}</Typography>
          <Chip
            size="small"
            label={t(`pages.plantingRuns.phase${r.status.charAt(0).toUpperCase() + r.status.slice(1)}`)}
            color={
              r.status === 'completed'
                ? 'success'
                : r.status === 'current'
                  ? 'primary'
                  : 'default'
            }
            variant="outlined"
          />
        </Box>
      ),
      searchValue: (r) => r.display_name || r.phase_name,
    },
    {
      id: 'enteredAt',
      label: t('pages.plantingRuns.actualStart'),
      render: (r) => {
        if (editingPhaseKey === r.phase_key) {
          return (
            <TextField
              type="date"
              size="small"
              value={editEnteredAt}
              onChange={(e) => setEditEnteredAt(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
              sx={{ minWidth: 150 }}
            />
          );
        }
        if (r.status === 'projected') {
          return (
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              {r.projected_start ? `~${formatDate(r.projected_start)}` : '—'}
            </Typography>
          );
        }
        return formatDate(r.actual_entered_at);
      },
    },
    {
      id: 'exitedAt',
      label: t('pages.plantingRuns.actualEnd'),
      render: (r) => {
        if (editingPhaseKey === r.phase_key) {
          return (
            <TextField
              type="date"
              size="small"
              value={editExitedAt}
              onChange={(e) => setEditExitedAt(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
              sx={{ minWidth: 150 }}
            />
          );
        }
        if (r.status === 'current') {
          return (
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              {t('pages.plantingRuns.phaseCurrent')}
            </Typography>
          );
        }
        if (r.status === 'projected') {
          return (
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              {r.projected_end ? `~${formatDate(r.projected_end)}` : '—'}
            </Typography>
          );
        }
        return formatDate(r.actual_exited_at);
      },
    },
    {
      id: 'duration',
      label: t('pages.plantingRuns.durationDays'),
      align: 'right',
      render: (r) => {
        if (r.status === 'completed' && r.actual_duration_days != null) {
          return (
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {r.actual_duration_days} {t('pages.plantingRuns.daysShort')}
            </Typography>
          );
        }
        if (r.status === 'current') {
          const days = computeDurationDays(r.actual_entered_at, null);
          return (
            <Typography variant="body2" color="primary">
              {days ?? 0} / {r.typical_duration_days} {t('pages.plantingRuns.daysShort')}
            </Typography>
          );
        }
        // projected
        return (
          <Typography variant="body2" color="text.secondary">
            ~{r.typical_duration_days} {t('pages.plantingRuns.daysShort')}
          </Typography>
        );
      },
    },
    {
      id: 'actions',
      label: '',
      width: 90,
      sortable: false,
      searchable: false,
      render: (r) => {
        if (!isActive) return null;
        // Only allow editing completed/current phases (not projected)
        if (r.status === 'projected') return null;

        if (editingPhaseKey === r.phase_key) {
          return (
            <Box sx={{ display: 'flex', gap: 0.5 }}>
              <Tooltip title={t('common.save')}>
                <IconButton
                  size="small"
                  onClick={saveEdit}
                  disabled={saving}
                  color="primary"
                  aria-label={t('common.save')}
                  data-testid="save-phase-edit-button"
                >
                  {saving ? <CircularProgress size={16} /> : <SaveIcon fontSize="small" />}
                </IconButton>
              </Tooltip>
              <Tooltip title={t('common.cancel')}>
                <IconButton
                  size="small"
                  onClick={cancelEdit}
                  aria-label={t('common.cancel')}
                  data-testid="cancel-phase-edit-button"
                >
                  <CloseIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          );
        }
        return (
          <Tooltip title={t('pages.plantingRuns.editPhaseDate')}>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                startEdit(r);
              }}
              aria-label={t('pages.plantingRuns.editPhaseDate')}
              data-testid={`edit-phase-${r.phase_key}`}
            >
              <EditIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        );
      },
    },
  ];

  return (
    <Box data-testid="run-phase-editor">
      {timelines.map((tl) => (
        <Box key={tl.species_key} sx={{ mb: 3 }}>
          {timelines.length > 1 && (
            <Typography variant="subtitle1" sx={{ mb: 1 }}>
              {tl.species_name ?? tl.species_key} ({tl.plant_count} {t('pages.plantingRuns.plantsLabel')})
            </Typography>
          )}
          <DataTable
            columns={columns}
            rows={tl.phases}
            getRowKey={(r) => r.phase_key}
            variant="simple"
            ariaLabel={t('pages.plantingRuns.phaseTimeline')}
            mobileCardRenderer={(r) => (
              <MobileCard
                title={r.display_name || r.phase_name}
                titleId="phase"
                chips={[
                  {
                    id: 'status',
                    content: (
                      <Chip
                        size="small"
                        label={t(`pages.plantingRuns.phase${r.status.charAt(0).toUpperCase() + r.status.slice(1)}`)}
                        color={r.status === 'completed' ? 'success' : r.status === 'current' ? 'primary' : 'default'}
                        variant="outlined"
                      />
                    ),
                  },
                ]}
                fields={[
                  { id: 'enteredAt', label: t('pages.plantingRuns.actualStart'), value: r.actual_entered_at ? formatDate(r.actual_entered_at) : r.projected_start ? `~${formatDate(r.projected_start)}` : '—' },
                  { id: 'duration', label: t('pages.plantingRuns.durationDays'), value: r.actual_duration_days != null ? `${r.actual_duration_days} ${t('pages.plantingRuns.daysShort')}` : `~${r.typical_duration_days} ${t('pages.plantingRuns.daysShort')}` },
                ]}
              />
            )}
          />
        </Box>
      ))}

      {isActive && (
        <Alert severity="info" sx={{ mt: 2 }}>
          {t('pages.plantingRuns.bulkPhaseEditHint')}
        </Alert>
      )}
    </Box>
  );
}
