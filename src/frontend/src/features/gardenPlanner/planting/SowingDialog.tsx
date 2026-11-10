/**
 * "Record sowing" for a planned row or zone (REQ-053 §11.3 "gesät", W-015): direct sowing creates no plant per
 * seed - the slot keeps the sowing day and shows as "sown" until it is thinned out. The day may lie up to a year
 * back, never in the future (the server checks the same).
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { useApiError } from '@/hooks/useApiError';
import { sowSlot } from './plantingApi';

/** How far back a sowing day may lie (`MAX_SOWING_AGE_DAYS` of the server). */
const MAX_SOWING_AGE_DAYS = 365;

interface SowingDialogProps {
  slotKey: string;
  slotLabel: string;
  speciesName: string;
  onClose: () => void;
  onSown: () => void;
}

function utcDay(offsetDays = 0): string {
  return new Date(Date.now() + offsetDays * 86_400_000).toISOString().slice(0, 10);
}

export default function SowingDialog({ slotKey, slotLabel, speciesName, onClose, onSown }: SowingDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { handleError } = useApiError();
  const [sownAt, setSownAt] = useState(() => utcDay());
  const [saving, setSaving] = useState(false);
  const earliest = utcDay(-MAX_SOWING_AGE_DAYS);
  const latest = utcDay();
  const invalid = sownAt === '' || sownAt < earliest || sownAt > latest;

  const submit = async () => {
    if (invalid) return;
    setSaving(true);
    try {
      await sowSlot(slotKey, sownAt);
      onSown();
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open
      onClose={saving ? undefined : onClose}
      fullScreen={fullScreen}
      maxWidth="xs"
      fullWidth
      aria-labelledby="sowing-dialog-title"
      data-testid="sowing-dialog"
    >
      <DialogTitle id="sowing-dialog-title">
        {t('pages.bed.planting.sowing.title', { species: speciesName, slot: slotLabel })}
      </DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {t('pages.bed.planting.sowing.help')}
        </Typography>
        <TextField
          label={t('pages.bed.planting.sowing.date')}
          value={sownAt}
          onChange={(event) => setSownAt(event.target.value)}
          type="date"
          error={invalid}
          helperText={t(invalid ? 'pages.bed.planting.sowing.dateInvalid' : 'pages.bed.planting.sowing.dateHelper')}
          slotProps={{
            inputLabel: { shrink: true },
            htmlInput: { min: earliest, max: latest, 'data-testid': 'sowing-date' },
          }}
          sx={{ '& .MuiInputBase-root': { minHeight: 48 } }}
        />
      </DialogContent>
      <DialogActions sx={{ px: { xs: 2, sm: 3 }, pb: 2 }}>
        <Button onClick={onClose} disabled={saving} sx={{ minHeight: 48 }}>
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          onClick={() => void submit()}
          disabled={saving || invalid}
          sx={{ minHeight: 48 }}
          data-testid="sowing-submit"
        >
          {t('pages.bed.planting.sowing.submit')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
