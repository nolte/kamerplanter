import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import CircularProgress from '@mui/material/CircularProgress';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import type { RemovePlantRequest, TerminationCause, TerminationType } from '@/api/types';

/** Selectable termination types (REQ-003 E5). Order = decreasing likelihood. */
const TERMINATION_TYPES: TerminationType[] = ['harvested', 'senesced', 'died', 'cancelled'];

/** Loss causes — only offered when the type is `died` (REQ-003 E5). */
const TERMINATION_CAUSES: TerminationCause[] = [
  'disease',
  'pest',
  'frost',
  'heat',
  'drought',
  'waterlogging',
  'neglect',
  'mechanical',
  'unknown',
];

interface Props {
  open: boolean;
  plantName: string;
  /** Called with the classified removal body. An empty object = plain removal. */
  onConfirm: (body: RemovePlantRequest) => void;
  onCancel: () => void;
  loading?: boolean;
}

/**
 * Removal dialog that classifies how a plant's lifecycle ended (REQ-003 E5).
 *
 * The termination type is optional — confirming without a selection performs a
 * plain removal (backward compatible). Selecting `died` reveals a required
 * cause select so the loss can feed the survival / failure-cause analytics.
 */
export default function TerminationDialog({ open, plantName, onConfirm, onCancel, loading = false }: Props) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));

  const [terminationType, setTerminationType] = useState<TerminationType | ''>('');
  const [terminationCause, setTerminationCause] = useState<TerminationCause | ''>('');

  // Reset the form each time the dialog is (re)opened.
  useEffect(() => {
    if (open) {
      setTerminationType('');
      setTerminationCause('');
    }
  }, [open]);

  const isDied = terminationType === 'died';
  // A `died` loss must name a cause; every other path may be confirmed directly.
  const canConfirm = !loading && (!isDied || terminationCause !== '');

  const body = useMemo<RemovePlantRequest>(() => {
    if (terminationType === '') return {};
    if (terminationType === 'died') {
      return { termination_type: 'died', termination_cause: terminationCause || undefined };
    }
    return { termination_type: terminationType };
  }, [terminationType, terminationCause]);

  const handleConfirm = () => {
    if (!canConfirm) return;
    onConfirm(body);
  };

  return (
    <Dialog
      open={open}
      onClose={onCancel}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      aria-labelledby="termination-dialog-title"
      aria-describedby="termination-dialog-description"
      role="alertdialog"
      data-testid="termination-dialog"
    >
      <DialogTitle id="termination-dialog-title">{t('pages.plantInstances.termination.title')}</DialogTitle>
      <DialogContent>
        <DialogContentText id="termination-dialog-description" sx={{ mb: 2 }}>
          {t('pages.plantInstances.termination.intro', { name: plantName })}
        </DialogContentText>

        <Alert severity="warning" sx={{ mb: 2 }} data-testid="termination-irreversible-warning">
          {t('pages.plantInstances.termination.irreversibleNote')}
        </Alert>

        <TextField
          select
          fullWidth
          autoFocus
          label={t('pages.plantInstances.termination.typeLabel')}
          value={terminationType}
          onChange={(e) => setTerminationType(e.target.value as TerminationType | '')}
          helperText={t('pages.plantInstances.termination.typeHelper')}
          disabled={loading}
          sx={{ mb: 2, mt: 1 }}
          data-testid="termination-type-select"
          slotProps={{ select: { displayEmpty: true } }}
        >
          <MenuItem value="">
            <em>{t('pages.plantInstances.termination.typeUnspecified')}</em>
          </MenuItem>
          {TERMINATION_TYPES.map((tt) => (
            <MenuItem key={tt} value={tt} data-testid={`termination-type-${tt}`}>
              {t(`enums.terminationType.${tt}`)}
            </MenuItem>
          ))}
        </TextField>

        {isDied && (
          <Box data-testid="termination-cause-block">
            <Alert severity="info" sx={{ mb: 2 }}>
              {t('pages.plantInstances.termination.causeExplainer')}
            </Alert>
            <TextField
              select
              fullWidth
              required
              label={t('pages.plantInstances.termination.causeLabel')}
              value={terminationCause}
              onChange={(e) => setTerminationCause(e.target.value as TerminationCause | '')}
              helperText={t('pages.plantInstances.termination.causeHelper')}
              error={terminationCause === ''}
              disabled={loading}
              sx={{ mb: 1 }}
              data-testid="termination-cause-select"
            >
              {TERMINATION_CAUSES.map((tc) => (
                <MenuItem key={tc} value={tc} data-testid={`termination-cause-${tc}`}>
                  {t(`enums.terminationCause.${tc}`)}
                </MenuItem>
              ))}
            </TextField>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel} disabled={loading} data-testid="termination-cancel">
          {t('common.cancel')}
        </Button>
        <Tooltip
          title={isDied && terminationCause === '' && !loading ? t('pages.plantInstances.termination.confirmDisabledHint') : ''}
        >
          <span>
            <Button
              variant="contained"
              color="error"
              onClick={handleConfirm}
              disabled={!canConfirm}
              startIcon={loading ? <CircularProgress size={16} color="inherit" /> : undefined}
              data-testid="termination-confirm"
            >
              {t('pages.plantInstances.remove')}
            </Button>
          </span>
        </Tooltip>
      </DialogActions>
    </Dialog>
  );
}
