/**
 * "Beet räumen" at the end of the season (REQ-053 GP-FR-055, GP-API-019, F-02): one dialog, one confirmation, one
 * request. The server ends every standing plant (today, with the chosen `termination_type`) and every live run,
 * archives their slots and writes one `clearing` care event - in one transaction.
 *
 * The type applies to the whole bed: the route takes one `termination_type` (REQ-053 v1.5 (e), GP-ACC-040,
 * TC-053-027). A plant that ended differently is ended on its own page first; the hint says so. The default is
 * `harvested`, the usual end of a season. Planning mode only: destructive actions are not offered in field mode
 * (GP-UX-023). The dialog names what it affects (plants, runs) and what it does before anything is written
 * (UI-NFR-004 R-022/R-023); the confirm button is the danger colour (R-024) and locked while the request runs.
 */
import { useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import type { TerminationType } from '@/api/types';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import ChipChoice from './ChipChoice';
import { clearBed } from './bedApi';
import type { ClearBedResult } from './types';

const REASON_MAX = 1000;

/** The four ends of REQ-003 E5, in the order a grower meets them at the end of a season. */
const CLEAR_TERMINATION_TYPES: readonly TerminationType[] = ['harvested', 'senesced', 'died', 'cancelled'];
const DEFAULT_TERMINATION: TerminationType = 'harvested';

/** One literal key per effect line, so the i18n key checks see every key that is used. */
const EFFECT_KEYS = [
  'pages.bed.clear.effects.plants',
  'pages.bed.clear.effects.runs',
  'pages.bed.clear.effects.slots',
  'pages.bed.clear.effects.log',
] as const;

interface BedClearDialogProps {
  bedKey: string;
  bedName: string;
  /** Standing plants of the bed, as the planting tab lists them. */
  plantCount: number;
  /** Runs those plants belong to. */
  runCount: number;
  onClose: () => void;
  /** The server cleared the bed; the caller reloads what the bed shows. */
  onCleared: (result: ClearBedResult) => void;
}

export default function BedClearDialog({
  bedKey,
  bedName,
  plantCount,
  runCount,
  onClose,
  onCleared,
}: BedClearDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { handleError } = useApiError();
  const notification = useNotification();
  const titleId = useId();
  const descriptionId = useId();
  const [terminationType, setTerminationType] = useState<TerminationType>(DEFAULT_TERMINATION);
  const [reason, setReason] = useState('');
  const [saving, setSaving] = useState(false);

  const plants = t('pages.bed.clear.plants', { count: plantCount });
  const affected =
    runCount > 0
      ? t('pages.bed.clear.affected', { plants, runs: t('pages.bed.clear.runs', { count: runCount }) })
      : t('pages.bed.clear.affectedNoRun', { plants });

  const submit = async () => {
    if (saving) return;
    setSaving(true);
    try {
      const trimmed = reason.trim();
      const result = await clearBed(bedKey, terminationType, trimmed === '' ? undefined : trimmed);
      notification.success(t('pages.bed.clear.done', { count: result.plants_removed }));
      onCleared(result);
    } catch (error) {
      // The dialog stays open with the choice made; the error pattern of every bed action says why.
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
      maxWidth="sm"
      fullWidth
      aria-labelledby={titleId}
      aria-describedby={descriptionId}
      data-testid="bed-clear-dialog"
    >
      <DialogTitle id={titleId}>{t('pages.bed.clear.title', { name: bedName })}</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        <Box id={descriptionId}>
          <Typography
            variant="body1"
            sx={{ fontWeight: 500, mb: 1 }}
            data-testid="bed-clear-affected"
            data-plant-count={plantCount}
            data-run-count={runCount}
          >
            {affected}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('pages.bed.clear.effectsTitle')}
          </Typography>
          <Box component="ul" sx={{ m: 0, mt: 0.5, pl: 2.5 }} data-testid="bed-clear-effects">
            {EFFECT_KEYS.map((key) => (
              <Typography key={key} component="li" variant="body2" color="text.secondary">
                {t(key)}
              </Typography>
            ))}
          </Box>
        </Box>
        <ChipChoice<TerminationType>
          title={t('pages.bed.clear.terminationTitle')}
          hint={t('pages.bed.clear.terminationHint')}
          options={CLEAR_TERMINATION_TYPES.map((value) => ({ value, label: t(`enums.terminationType.${value}`) }))}
          value={[terminationType]}
          mode="single"
          onToggle={setTerminationType}
          disabled={saving}
          testId="bed-clear-termination"
        />
        <TextField
          label={t('pages.bed.clear.reason')}
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          multiline
          minRows={2}
          disabled={saving}
          helperText={t('pages.bed.clear.reasonHelp')}
          slotProps={{ htmlInput: { maxLength: REASON_MAX, 'data-testid': 'bed-clear-reason' } }}
        />
        <Alert severity="warning" data-testid="bed-clear-irreversible">
          {t('pages.bed.clear.irreversible')}
        </Alert>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving} sx={{ minHeight: 44 }} data-testid="bed-clear-cancel">
          {t('common.cancel')}
        </Button>
        <Button
          variant="contained"
          color="error"
          onClick={submit}
          loading={saving}
          sx={{ minHeight: 44 }}
          data-testid="bed-clear-submit"
        >
          {t('pages.bed.clear.submit')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
