/**
 * Change the lifecycle status of a bed with a reason (REQ-053 GP-FR-046, GP-API-018). Retiring needs
 * a reason (the server logs it as a care event); other changes accept an optional one. A bed that
 * still holds plants cannot be retired - the server answers 409 `location.has_active_plants`.
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import type { BedStatus } from '../model/types';
import { changeBedStatus } from './bedApi';

const REASON_MAX = 1000;

interface BedStatusDialogProps {
  open: boolean;
  bedKey: string;
  current: BedStatus;
  targets: readonly BedStatus[];
  onClose: () => void;
  /** The status was stored; the page reloads its summary. */
  onChanged: () => void;
}

export default function BedStatusDialog({
  open,
  bedKey,
  current,
  targets,
  onClose,
  onChanged,
}: BedStatusDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { handleError } = useApiError();
  const notification = useNotification();
  const [chosen, setChosen] = useState<BedStatus | null>(null);
  const [reason, setReason] = useState('');
  const [saving, setSaving] = useState(false);

  const target = chosen !== null && targets.includes(chosen) ? chosen : (targets[0] ?? null);
  const reasonRequired = target === 'retired';
  const trimmed = reason.trim();
  const invalid = target === null || (reasonRequired && trimmed === '');

  const submit = async () => {
    if (target === null || invalid) return;
    setSaving(true);
    try {
      await changeBedStatus(bedKey, target, trimmed === '' ? undefined : trimmed);
      notification.success(t('pages.bed.status.changed'));
      setReason('');
      setChosen(null);
      onChanged();
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={saving ? undefined : onClose}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      aria-labelledby="bed-status-title"
      data-testid="bed-status-dialog"
    >
      <DialogTitle id="bed-status-title">{t('pages.bed.status.title')}</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {t('pages.bed.status.current', { status: t(`enums.bedStatus.${current}`) })}
        </Typography>
        <TextField
          select
          label={t('pages.bed.status.target')}
          value={target ?? ''}
          onChange={(event) => setChosen(event.target.value as BedStatus)}
          slotProps={{ htmlInput: { 'data-testid': 'bed-status-target' } }}
        >
          {targets.map((status) => (
            <MenuItem key={status} value={status}>
              {t(`enums.bedStatus.${status}`)}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          label={t('pages.bed.status.reason')}
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          required={reasonRequired}
          multiline
          minRows={2}
          error={reasonRequired && reason !== '' && trimmed === ''}
          helperText={reasonRequired ? t('pages.bed.status.reasonRequired') : t('pages.bed.status.reasonOptional')}
          slotProps={{ htmlInput: { maxLength: REASON_MAX, 'data-testid': 'bed-status-reason' } }}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={submit}
          loading={saving}
          disabled={invalid}
          data-testid="bed-status-submit"
        >
          {t('pages.bed.status.submit')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
