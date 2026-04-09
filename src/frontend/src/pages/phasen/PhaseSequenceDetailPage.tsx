import { useEffect, useMemo, useState, useCallback } from 'react';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import AddIcon from '@mui/icons-material/Add';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import LoopIcon from '@mui/icons-material/Loop';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useAppDispatch } from '@/store/hooks';
import { setBreadcrumbs } from '@/store/slices/uiSlice';
import * as phaseSequenceApi from '@/api/endpoints/phaseSequences';
import type { PhaseSequence, PhaseSequenceEntry } from '@/api/types';
import PhaseSequenceEntryDialog from './PhaseSequenceEntryDialog';

const cycleTypes = ['annual', 'biennial', 'perennial'] as const;

const editSchema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().optional().or(z.literal('')),
  cycle_type: z.enum(cycleTypes),
  is_repeating: z.boolean(),
  cycle_restart_entry_order: z.number().min(0).nullable(),
});

type EditFormData = z.infer<typeof editSchema>;

function EditSequenceDialog({
  open,
  onClose,
  sequence,
  onSaved,
}: {
  open: boolean;
  onClose: () => void;
  sequence: PhaseSequence;
  onSaved: () => void;
}) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      name: '',
      description: '',
      cycle_type: 'annual',
      is_repeating: false,
      cycle_restart_entry_order: null,
    },
  });

  useEffect(() => {
    if (open) {
      reset({
        name: sequence.name,
        description: sequence.description || '',
        cycle_type: sequence.cycle_type as EditFormData['cycle_type'],
        is_repeating: sequence.is_repeating,
        cycle_restart_entry_order: sequence.cycle_restart_entry_order,
      });
    }
  }, [open, sequence, reset]);

  const onSubmit = async (data: EditFormData) => {
    try {
      setSaving(true);
      await phaseSequenceApi.updatePhaseSequence(sequence.key, {
        name: data.name,
        description: data.description || undefined,
        cycle_type: data.cycle_type,
        is_repeating: data.is_repeating,
        cycle_restart_entry_order: data.cycle_restart_entry_order,
      });
      notification.success(t('pages.phaseSequences.sequenceUpdated'));
      onSaved();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="edit-sequence-dialog-title"
    >
      <DialogTitle id="edit-sequence-dialog-title">
        {t('pages.phaseSequences.editSequence')}
      </DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField
            name="name"
            control={control}
            label={t('common.name')}
            required
            autoFocus
          />
          <FormTextField
            name="description"
            control={control}
            label={t('common.description')}
            multiline
            rows={3}
          />
          <FormSelectField
            name="cycle_type"
            control={control}
            label={t('pages.phaseSequences.cycleType')}
            options={cycleTypes.map((v) => ({
              value: v,
              label: t(`enums.cycleType.${v}`),
            }))}
          />
          <FormSwitchField
            name="is_repeating"
            control={control}
            label={t('pages.phaseSequences.isRepeating')}
            helperText={t('pages.phaseSequences.isRepeatingHelper')}
          />
          <FormActions
            onCancel={onClose}
            loading={saving}
            saveLabel={t('common.save')}
          />
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function PhaseSequenceDetailPage() {
  const { key } = useParams<{ key: string }>();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const notification = useNotification();
  const { handleError } = useApiError();

  const [sequence, setSequence] = useState<PhaseSequence | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [entryDialogOpen, setEntryDialogOpen] = useState(false);
  const [editEntry, setEditEntry] = useState<PhaseSequenceEntry | undefined>(
    undefined,
  );
  const [deleteEntryKey, setDeleteEntryKey] = useState<string | null>(null);
  const [reordering, setReordering] = useState(false);
  const [linkedSpecies, setLinkedSpecies] = useState<{ key: string; scientific_name: string; common_names: string[] }[]>([]);
  const [showAllSpecies, setShowAllSpecies] = useState(false);

  const visibleSpecies = useMemo(
    () => (showAllSpecies ? linkedSpecies : linkedSpecies.slice(0, 5)),
    [showAllSpecies, linkedSpecies],
  );

  const loadSequence = useCallback(async () => {
    if (!key) return;
    try {
      setLoading(true);
      setError(null);
      const [data, species] = await Promise.all([
        phaseSequenceApi.getPhaseSequence(key),
        phaseSequenceApi.listSpeciesForSequence(key).catch(() => []),
      ]);
      setSequence(data);
      setLinkedSpecies(species);
    } catch (err) {
      setError(t('errors.notFound'));
      handleError(err);
    } finally {
      setLoading(false);
    }
  }, [key, t, handleError]);

  useEffect(() => {
    loadSequence();
  }, [loadSequence]);

  // Breadcrumbs
  useEffect(() => {
    if (!sequence) return;
    dispatch(
      setBreadcrumbs([
        { label: 'nav.dashboard', path: '/dashboard' },
        {
          label: 'pages.phaseSequences.phaseSequences',
          path: '/phasen/ablaeufe',
        },
        { label: (lang === 'de' ? sequence.display_name_de : sequence.display_name) || sequence.name },
      ]),
    );
  }, [sequence, dispatch, lang]);

  // Clear breadcrumbs on unmount
  useEffect(() => () => {
    dispatch(setBreadcrumbs([]));
  }, [dispatch]);

  const handleDeleteEntry = async () => {
    if (!deleteEntryKey || !key) return;
    try {
      await phaseSequenceApi.deleteSequenceEntry(key, deleteEntryKey);
      notification.success(t('pages.phaseSequences.sequenceUpdated'));
      setDeleteEntryKey(null);
      loadSequence();
    } catch (err) {
      handleError(err);
    }
  };

  const handleReorder = async (entryKey: string, direction: 'up' | 'down') => {
    if (!sequence || !key) return;
    const sorted = [...sequence.entries].sort(
      (a, b) => a.sequence_order - b.sequence_order,
    );
    const idx = sorted.findIndex((e) => e.key === entryKey);
    if (idx < 0) return;
    const swapIdx = direction === 'up' ? idx - 1 : idx + 1;
    if (swapIdx < 0 || swapIdx >= sorted.length) return;

    // Swap orders
    const newEntries = sorted.map((e, i) => {
      if (i === idx) return { key: e.key, sequence_order: sorted[swapIdx].sequence_order };
      if (i === swapIdx) return { key: e.key, sequence_order: sorted[idx].sequence_order };
      return { key: e.key, sequence_order: e.sequence_order };
    });

    try {
      setReordering(true);
      await phaseSequenceApi.reorderEntries(key, newEntries);
      await loadSequence();
    } catch (err) {
      handleError(err);
    } finally {
      setReordering(false);
    }
  };

  const handleOpenAddEntry = () => {
    setEditEntry(undefined);
    setEntryDialogOpen(true);
  };

  const handleOpenEditEntry = (entry: PhaseSequenceEntry) => {
    setEditEntry(entry);
    setEntryDialogOpen(true);
  };

  const handleEntrySaved = () => {
    setEntryDialogOpen(false);
    setEditEntry(undefined);
    loadSequence();
  };

  const sortedEntries = sequence
    ? [...sequence.entries].sort((a, b) => a.sequence_order - b.sequence_order)
    : [];

  const deleteEntryTarget = sortedEntries.find((e) => e.key === deleteEntryKey);

  const totalDuration = sortedEntries.reduce(
    (sum, e) => sum + e.effective_duration_days,
    0,
  );

  const hasTerminal = sortedEntries.some((e) => e.is_terminal);
  const hasHarvest = sortedEntries.some((e) => e.allows_harvest);

  if (loading) {
    return <LoadingSkeleton variant="form" />;
  }

  if (error || !sequence) {
    return (
      <Box>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/phasen/ablaeufe')}
          sx={{ mb: 2 }}
          data-testid="back-button"
        >
          {t('common.back')}
        </Button>
        <ErrorDisplay error={error ?? t('errors.notFound')} onRetry={loadSequence} />
      </Box>
    );
  }

  return (
    <Box data-testid="phase-sequence-detail-page">
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate('/phasen/ablaeufe')}
        sx={{ mb: 2 }}
        data-testid="back-button"
      >
        {t('common.back')}
      </Button>

      <PageTitle
        title={(lang === 'de' ? sequence.display_name_de : sequence.display_name) || sequence.name}
        action={
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={() => setEditOpen(true)}
            disabled={sequence.is_system}
            data-testid="edit-sequence-button"
          >
            {t('pages.phaseSequences.editSequence')}
          </Button>
        }
      />

      {/* Metadata */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 3 }}>
        <Chip
          label={t(`enums.cycleType.${sequence.cycle_type}`)}
          color="primary"
          variant="outlined"
        />
        {sequence.is_repeating && (
          <Chip
            icon={<LoopIcon />}
            label={t('pages.phaseSequences.isRepeating')}
            color="secondary"
            variant="outlined"
          />
        )}
        {sequence.is_system && (
          <Chip label={t('pages.phaseSequences.system')} color="info" variant="outlined" />
        )}
        <Chip
          label={t('pages.phaseSequences.totalDurationDays', { count: totalDuration })}
          variant="outlined"
        />
      </Box>

      {(sequence.description || sequence.description_de) && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {(lang === 'de' ? sequence.description_de : sequence.description) || sequence.description}
        </Typography>
      )}

      {/* Linked Species */}
      {linkedSpecies.length > 0 && (
        <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              {t('pages.phaseSequences.usedBySpecies')} ({linkedSpecies.length})
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {visibleSpecies.map((sp) => (
                <Chip
                  key={sp.key}
                  component={RouterLink}
                  to={`/stammdaten/species/${sp.key}`}
                  icon={<LocalFloristIcon />}
                  label={sp.common_names[0] ? `${sp.scientific_name} (${sp.common_names[0]})` : sp.scientific_name}
                  clickable
                  variant="outlined"
                  size="small"
                  sx={{ maxWidth: { xs: 200, sm: 'none' } }}
                />
              ))}
            </Box>
            {linkedSpecies.length > 5 && (
              <Button
                size="small"
                onClick={() => setShowAllSpecies(!showAllSpecies)}
                sx={{ mt: 1 }}
              >
                {showAllSpecies
                  ? t('common.showLess')
                  : t('common.showAll', { count: linkedSpecies.length })}
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Entries section */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2,
        }}
      >
        <Typography variant="h6" component="h2">
          {t('pages.phaseSequences.sequenceEntries')}
        </Typography>
        <Button
          variant="contained"
          size="small"
          startIcon={<AddIcon />}
          onClick={handleOpenAddEntry}
          disabled={sequence.is_system}
          data-testid="add-entry-button"
        >
          {t('pages.phaseSequences.addEntry')}
        </Button>
      </Box>

      {sortedEntries.length === 0 ? (
        <Paper variant="outlined" sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="text.secondary">
            {t('pages.phaseSequences.noDefinitions')}
          </Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper} variant="outlined" sx={{ overflowX: 'auto' }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ width: 60 }}>
                  {t('pages.phaseSequences.sequenceOrder')}
                </TableCell>
                <TableCell>{t('pages.phaseSequences.phaseName')}</TableCell>
                <TableCell>{t('pages.phaseSequences.effectiveDuration')}</TableCell>
                {hasTerminal && <TableCell>{t('pages.phaseSequences.isTerminal')}</TableCell>}
                {hasHarvest && <TableCell>{t('pages.phaseSequences.allowsHarvest')}</TableCell>}
                <TableCell align="right">{t('common.actions')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sortedEntries.map((entry, idx) => (
                <TableRow key={entry.key} data-testid={`entry-row-${entry.key}`}>
                  <TableCell>{entry.sequence_order}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Link
                        component={RouterLink}
                        to={`/phasen/definitionen/${entry.phase_definition_key}`}
                        underline="hover"
                        color="primary"
                      >
                        {(lang === 'de' ? entry.phase_definition?.display_name_de : entry.phase_definition?.display_name) ||
                          entry.phase_definition?.name ||
                          entry.phase_definition_key}
                      </Link>
                      {entry.is_recurring && (
                        <Chip
                          icon={<LoopIcon />}
                          label={t('pages.phaseSequences.isRecurring')}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    {t('pages.phaseSequences.durationDays', {
                      count: entry.effective_duration_days,
                    })}
                    {entry.override_duration_days !== null && (
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ ml: 1 }}
                      >
                        ({t('pages.phaseSequences.overrideIndicator')})
                      </Typography>
                    )}
                  </TableCell>
                  {hasTerminal && (
                    <TableCell>
                      {entry.is_terminal && (
                        <CheckCircleIcon fontSize="small" color="warning" aria-label={t('pages.phaseSequences.isTerminal')} />
                      )}
                    </TableCell>
                  )}
                  {hasHarvest && (
                    <TableCell>
                      {entry.allows_harvest && (
                        <CheckCircleIcon fontSize="small" color="success" aria-label={t('pages.phaseSequences.allowsHarvest')} />
                      )}
                    </TableCell>
                  )}
                  <TableCell align="right">
                    <Tooltip title={t('pages.phaseSequences.moveUp')}>
                      <span>
                        <IconButton
                          sx={{ p: 0.5 }}
                          disabled={idx === 0 || reordering || sequence.is_system}
                          onClick={() => handleReorder(entry.key, 'up')}
                          aria-label={t('pages.phaseSequences.moveUp')}
                        >
                          <ArrowUpwardIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
                    <Tooltip title={t('pages.phaseSequences.moveDown')}>
                      <span>
                        <IconButton
                          sx={{ p: 0.5 }}
                          disabled={
                            idx === sortedEntries.length - 1 ||
                            reordering ||
                            sequence.is_system
                          }
                          onClick={() => handleReorder(entry.key, 'down')}
                          aria-label={t('pages.phaseSequences.moveDown')}
                        >
                          <ArrowDownwardIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
                    <Tooltip title={t('common.edit')}>
                      <IconButton
                        sx={{ p: 0.5 }}
                        onClick={() => handleOpenEditEntry(entry)}
                        disabled={sequence.is_system}
                        aria-label={t('common.edit')}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={t('pages.phaseSequences.removeEntry')}>
                      <span>
                        <IconButton
                          sx={{ p: 0.5 }}
                          color="error"
                          disabled={sequence.is_system}
                          onClick={() => setDeleteEntryKey(entry.key)}
                          aria-label={t('pages.phaseSequences.removeEntry')}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Edit sequence metadata dialog */}
      {editOpen && (
        <EditSequenceDialog
          open={editOpen}
          onClose={() => setEditOpen(false)}
          sequence={sequence}
          onSaved={() => {
            setEditOpen(false);
            loadSequence();
          }}
        />
      )}

      {/* Add/edit entry dialog */}
      <PhaseSequenceEntryDialog
        open={entryDialogOpen}
        onClose={() => {
          setEntryDialogOpen(false);
          setEditEntry(undefined);
        }}
        sequenceKey={key!}
        entry={editEntry}
        onSaved={handleEntrySaved}
      />

      {/* Delete entry confirm */}
      <ConfirmDialog
        open={!!deleteEntryKey}
        title={t('pages.phaseSequences.removeEntry')}
        message={t('pages.phaseSequences.removeEntryConfirm', {
          name:
            (lang === 'de' ? deleteEntryTarget?.phase_definition?.display_name_de : deleteEntryTarget?.phase_definition?.display_name) ||
            deleteEntryTarget?.phase_definition?.name ||
            '',
        })}
        onConfirm={handleDeleteEntry}
        onCancel={() => setDeleteEntryKey(null)}
        destructive
      />
    </Box>
  );
}
