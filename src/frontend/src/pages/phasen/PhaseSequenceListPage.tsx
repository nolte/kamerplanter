import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import AddIcon from '@mui/icons-material/Add';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DeleteIcon from '@mui/icons-material/Delete';
import LoopIcon from '@mui/icons-material/Loop';
import OriginChip from '@/components/common/OriginChip';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import PageTitle from '@/components/layout/PageTitle';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import MobileCard from '@/components/common/MobileCard';
import DataTable, { type Column } from '@/components/common/DataTable';
import { useTableUrlState } from '@/hooks/useTableState';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as phaseSequenceApi from '@/api/endpoints/phaseSequences';
import type { PhaseSequence } from '@/api/types';
import { kamiPhaseVegetative } from '@/assets/brand/illustrations';

const cycleTypes = ['annual', 'biennial', 'perennial'] as const;

const createSchema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().optional().or(z.literal('')),
  cycle_type: z.enum(cycleTypes),
  is_repeating: z.boolean(),
});

type CreateFormData = z.infer<typeof createSchema>;

function CreateSequenceDialog({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);

  const { control, handleSubmit, reset } = useForm<CreateFormData>({
    resolver: zodResolver(createSchema),
    defaultValues: {
      name: '',
      description: '',
      cycle_type: 'annual',
      is_repeating: false,
    },
  });

  useEffect(() => {
    if (open) {
      reset({
        name: '',
        description: '',
        cycle_type: 'annual',
        is_repeating: false,
      });
    }
  }, [open, reset]);

  const onSubmit = async (data: CreateFormData) => {
    try {
      setSaving(true);
      await phaseSequenceApi.createPhaseSequence({
        name: data.name,
        description: data.description || undefined,
        cycle_type: data.cycle_type,
        is_repeating: data.is_repeating,
      });
      notification.success(t('pages.phaseSequences.sequenceCreated'));
      onCreated();
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
      aria-labelledby="create-sequence-dialog-title"
    >
      <DialogTitle id="create-sequence-dialog-title">
        {t('pages.phaseSequences.createSequence')}
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
            saveLabel={t('common.create')}
          />
        </form>
      </DialogContent>
    </Dialog>
  );
}

function computeTotalDuration(seq: PhaseSequence): number {
  return seq.entries.reduce((sum, e) => sum + e.effective_duration_days, 0);
}

export default function PhaseSequenceListPage() {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const tableState = useTableUrlState({
    defaultSort: { column: 'name', direction: 'asc' },
    pageSizeStorageKey: 'phaseSequences.pageSize',
  });

  const [sequences, setSequences] = useState<PhaseSequence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [deleteKey, setDeleteKey] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const loadSequences = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await phaseSequenceApi.listPhaseSequences(0, 200);
      setSequences(data);
    } catch (err) {
      setError(t('errors.server'));
      handleError(err);
    } finally {
      setLoading(false);
    }
  }, [t, handleError]);

  useEffect(() => {
    loadSequences();
  }, [loadSequences]);

  const deleteTarget = sequences.find((s) => s.key === deleteKey);

  const handleDelete = async () => {
    if (!deleteKey) return;
    setDeleting(true);
    try {
      await phaseSequenceApi.deletePhaseSequence(deleteKey);
      notification.success(t('pages.phaseSequences.sequenceDeleted'));
      setDeleteKey(null);
      loadSequences();
    } catch (err) {
      handleError(err);
    } finally {
      setDeleting(false);
    }
  };

  const getDisplayName = (seq: PhaseSequence): string =>
    (lang === 'de' ? seq.display_name_de : seq.display_name) || seq.name;

  const handleClone = async (seq: PhaseSequence) => {
    try {
      const cloned = await phaseSequenceApi.clonePhaseSequence(seq.key, {
        new_name: `${getDisplayName(seq)} (${t('pages.phaseSequences.copySuffix')})`,
      });
      notification.success(t('pages.phaseSequences.sequenceCloned'));
      navigate(`/phasen/ablaeufe/${cloned.key}`);
    } catch (err) {
      handleError(err);
    }
  };

  const columns: Column<PhaseSequence>[] = [
    {
      id: 'name',
      label: t('common.name'),
      render: (seq) => getDisplayName(seq),
      searchValue: (seq) => `${getDisplayName(seq)} ${seq.name} ${seq.tags.join(' ')}`,
      sortFn: (a, b) => getDisplayName(a).localeCompare(getDisplayName(b)),
    },
    {
      id: 'cycleType',
      label: t('pages.phaseSequences.cycleType'),
      render: (seq) => (
        <Chip
          label={t(`enums.cycleType.${seq.cycle_type}`)}
          size="small"
          variant="outlined"
        />
      ),
      searchValue: (seq) => t(`enums.cycleType.${seq.cycle_type}`),
      sortFn: (a, b) => a.cycle_type.localeCompare(b.cycle_type),
    },
    {
      id: 'isRepeating',
      label: t('pages.phaseSequences.isRepeating'),
      render: (seq) =>
        seq.is_repeating ? (
          <Chip
            icon={<LoopIcon />}
            label={t('pages.phaseSequences.isRepeating')}
            size="small"
            color="secondary"
            variant="outlined"
          />
        ) : null,
      searchValue: (seq) => (seq.is_repeating ? t('pages.phaseSequences.isRepeating') : ''),
      sortFn: (a, b) => Number(a.is_repeating) - Number(b.is_repeating),
      hideBelowBreakpoint: 'md',
    },
    {
      id: 'entryCount',
      label: t('pages.phaseSequences.sequenceEntries'),
      render: (seq) => t('pages.phaseSequences.entryCount', { count: seq.entries.length }),
      searchValue: (seq) => String(seq.entries.length),
      sortFn: (a, b) => a.entries.length - b.entries.length,
      align: 'right',
      hideBelowBreakpoint: 'md',
    },
    {
      id: 'totalDuration',
      label: t('pages.phaseSequences.totalDuration'),
      render: (seq) =>
        t('pages.phaseSequences.totalDurationDays', { count: computeTotalDuration(seq) }),
      searchValue: (seq) => String(computeTotalDuration(seq)),
      sortFn: (a, b) => computeTotalDuration(a) - computeTotalDuration(b),
      align: 'right',
      hideBelowBreakpoint: 'md',
    },
    {
      // UI-NFR-018 R-002/R-019: Origin column
      id: 'origin',
      label: t('common.origin.filterLabel'),
      render: (seq) => <OriginChip isSystem={seq.is_system} />,
      sortable: false,
      searchable: false,
      hideBelowBreakpoint: 'md',
    },
    {
      id: 'actions',
      label: t('common.actions'),
      align: 'right',
      sortable: false,
      searchable: false,
      render: (seq) => (
        <Box onClick={(e) => e.stopPropagation()}>
          {/* UI-NFR-018 R-015: offer "copy as template" for read-only system data */}
          {seq.is_system && (
            <Tooltip title={t('pages.phaseSequences.duplicateTooltip')}>
              <IconButton
                size="small"
                color="primary"
                onClick={() => handleClone(seq)}
                aria-label={t('pages.phaseSequences.duplicate')}
                data-testid={`duplicate-sequence-${seq.key}`}
              >
                <ContentCopyIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {/* UI-NFR-018 R-013: hide delete action for system data */}
          {!seq.is_system && (
            <Tooltip title={t('common.delete')}>
              <IconButton
                size="small"
                color="error"
                onClick={() => setDeleteKey(seq.key)}
                aria-label={t('common.delete')}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      ),
    },
  ];

  return (
    <Box data-testid="phase-sequence-list-page">
      <PageTitle
        title={t('pages.phaseSequences.sequencesTitle')}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateOpen(true)}
            data-testid="create-sequence-button"
          >
            {t('pages.phaseSequences.createSequence')}
          </Button>
        }
      />

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {t('pages.phaseSequences.sequencesIntro')}
      </Typography>

      {error && <ErrorDisplay error={error} onRetry={loadSequences} />}

      <DataTable
        columns={columns}
        rows={sequences}
        loading={loading}
        getRowKey={(seq) => seq.key}
        onRowClick={(seq) => navigate(`/phasen/ablaeufe/${seq.key}`)}
        tableState={tableState}
        ariaLabel={t('pages.phaseSequences.sequencesTitle')}
        emptyMessage={t('pages.phaseSequences.noSequences')}
        emptyActionLabel={t('pages.phaseSequences.createSequence')}
        onEmptyAction={() => setCreateOpen(true)}
        emptyIllustration={kamiPhaseVegetative}
        mobileCardRenderer={(seq) => (
          <MobileCard
            title={getDisplayName(seq)}
            subtitle={seq.name}
            trailing={<OriginChip isSystem={seq.is_system} />}
            chips={
              <>
                <Chip
                  label={t(`enums.cycleType.${seq.cycle_type}`)}
                  size="small"
                  variant="outlined"
                />
                {seq.is_repeating && (
                  <Chip
                    icon={<LoopIcon />}
                    label={t('pages.phaseSequences.isRepeating')}
                    size="small"
                    color="secondary"
                    variant="outlined"
                  />
                )}
              </>
            }
            fields={[
              {
                label: t('pages.phaseSequences.sequenceEntries'),
                value: t('pages.phaseSequences.entryCount', {
                  count: seq.entries.length,
                }),
              },
              {
                label: t('pages.phaseSequences.totalDuration'),
                value: t('pages.phaseSequences.totalDurationDays', {
                  count: computeTotalDuration(seq),
                }),
              },
            ]}
          />
        )}
      />

      <CreateSequenceDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          loadSequences();
        }}
      />

      <ConfirmDialog
        open={!!deleteKey}
        title={t('pages.phaseSequences.deleteSequence')}
        message={t('pages.phaseSequences.deleteSequenceConfirm', {
          name: deleteTarget?.name ?? '',
        })}
        onConfirm={handleDelete}
        onCancel={() => setDeleteKey(null)}
        destructive
        loading={deleting}
      />
    </Box>
  );
}
