import { useEffect, useMemo, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import Skeleton from '@mui/material/Skeleton';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import LoopIcon from '@mui/icons-material/Loop';
import SearchIcon from '@mui/icons-material/Search';
import SettingsIcon from '@mui/icons-material/Settings';
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
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as phaseSequenceApi from '@/api/endpoints/phaseSequences';
import type { PhaseSequence } from '@/api/types';

const cycleTypes = ['annual', 'biennial', 'perennial'] as const;

const createSchema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().optional().or(z.literal('')),
  cycle_type: z.enum(cycleTypes),
  is_repeating: z.boolean(),
});

type CreateFormData = z.infer<typeof createSchema>;

function LoadingSkeletonTable() {
  return (
    <TableContainer component={Paper} variant="outlined">
      <Table>
        <TableHead>
          <TableRow>
            {Array.from({ length: 5 }).map((_, i) => (
              <TableCell key={i}>
                <Skeleton variant="text" width={80} />
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {Array.from({ length: 5 }).map((_, i) => (
            <TableRow key={i}>
              {Array.from({ length: 5 }).map((_, j) => (
                <TableCell key={j}>
                  <Skeleton variant="text" width={j === 0 ? 120 : 60} />
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

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

export default function PhaseSequenceListPage() {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [sequences, setSequences] = useState<PhaseSequence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [createOpen, setCreateOpen] = useState(false);
  const [deleteKey, setDeleteKey] = useState<string | null>(null);

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

  const filteredSequences = useMemo(() => {
    if (!searchQuery.trim()) return sequences;
    const query = searchQuery.toLowerCase();
    return sequences.filter(
      (s) =>
        s.name.toLowerCase().includes(query) ||
        s.display_name.toLowerCase().includes(query) ||
        s.display_name_de.toLowerCase().includes(query) ||
        s.tags.some((tag) => tag.toLowerCase().includes(query)),
    );
  }, [sequences, searchQuery]);

  const handleDelete = async () => {
    if (!deleteKey) return;
    try {
      await phaseSequenceApi.deletePhaseSequence(deleteKey);
      notification.success(t('pages.phaseSequences.sequenceDeleted'));
      setDeleteKey(null);
      loadSequences();
    } catch (err) {
      handleError(err);
    }
  };

  const computeTotalDuration = (seq: PhaseSequence): number =>
    seq.entries.reduce((sum, e) => sum + e.effective_duration_days, 0);

  const deleteTarget = sequences.find((s) => s.key === deleteKey);

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

      <TextField
        size="small"
        placeholder={t('pages.phaseSequences.searchSequences')}
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon color="action" />
              </InputAdornment>
            ),
          },
        }}
        sx={{ mb: 2, maxWidth: 400, width: '100%' }}
        data-testid="sequence-search"
        aria-label={t('pages.phaseSequences.searchSequences')}
      />

      {error && <ErrorDisplay error={error} onRetry={loadSequences} />}

      {loading ? (
        <LoadingSkeletonTable />
      ) : filteredSequences.length === 0 ? (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            py: 8,
            px: 2,
          }}
        >
          <Typography variant="h6" color="text.secondary" align="center">
            {searchQuery
              ? t('common.noSearchResults')
              : t('pages.phaseSequences.noSequences')}
          </Typography>
        </Box>
      ) : (
        <TableContainer component={Paper} variant="outlined">
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>{t('common.name')}</TableCell>
                <TableCell>{t('pages.phaseSequences.cycleType')}</TableCell>
                <TableCell>{t('pages.phaseSequences.isRepeating')}</TableCell>
                <TableCell>{t('pages.phaseSequences.sequenceEntries')}</TableCell>
                <TableCell>{t('pages.phaseSequences.totalDuration')}</TableCell>
                <TableCell align="right">{t('common.actions')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredSequences.map((seq) => (
                <TableRow
                  key={seq.key}
                  hover
                  sx={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/phasen/ablaeufe/${seq.key}`)}
                  data-testid={`sequence-row-${seq.key}`}
                >
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {(lang === 'de' ? seq.display_name_de : seq.display_name) || seq.name}
                      {seq.is_system && (
                        <Chip
                          icon={<SettingsIcon />}
                          label={t('pages.phaseSequences.system')}
                          size="small"
                          color="info"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={t(`enums.cycleType.${seq.cycle_type}`)}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    {seq.is_repeating && (
                      <Chip
                        icon={<LoopIcon />}
                        label={t('pages.phaseSequences.isRepeating')}
                        size="small"
                        color="secondary"
                        variant="outlined"
                      />
                    )}
                  </TableCell>
                  <TableCell>
                    {t('pages.phaseSequences.entryCount', {
                      count: seq.entries.length,
                    })}
                  </TableCell>
                  <TableCell>
                    {t('pages.phaseSequences.totalDurationDays', {
                      count: computeTotalDuration(seq),
                    })}
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip
                      title={
                        seq.is_system
                          ? t('pages.phaseSequences.system')
                          : t('common.delete')
                      }
                    >
                      <span>
                        <IconButton
                          size="small"
                          color="error"
                          disabled={seq.is_system}
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteKey(seq.key);
                          }}
                          aria-label={t('common.delete')}
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
      />
    </Box>
  );
}
