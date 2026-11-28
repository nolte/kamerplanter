/**
 * "Bodengefahr eintragen" (AP-API-012, REQ-054 §5.2, #2888 F-20): which soil hazard, since when, and how it was
 * confirmed - a lab result, plant-protection advice or an unmistakable symptom (a category, no name). For juglone the
 * date is the felling of a felled walnut, or the day the gardener noticed a standing one. A later confirmation of a hazard the bed
 * already carries replaces the stored date, an earlier one changes nothing (the server's rule). An area that is no bed
 * takes juglone only (#2888 O3): the list then holds that one hazard, chosen already.
 *
 * The server validates it, so saving is locked offline and says why (UI-NFR-012 R-020a).
 */
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import MenuItem from '@mui/material/MenuItem';
import Stack from '@mui/material/Stack';
import TextField from '@mui/material/TextField';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import RequiresConnectivity from '@/components/common/RequiresConnectivity';
import { getFieldViolations } from '@/api/errors';
import type { PathogenConfirmationSource, SoilHazard } from '@/api/types';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import { useOnlineStatus } from '@/hooks/useOnlineStatus';
import { toUtcIsoDate } from '@/utils/calendarDay';
import { recordSoilHazard } from './soilHazardApi';
import { CONFIRMATION_SOURCES, SOIL_HAZARDS } from './soilHazardTypes';

const TOUCH = { '& .MuiInputBase-root': { minHeight: 48 } };
const PREFIX = 'pages.bed.soilHazards';
/** The server's lower bound of a confirmation date (`EARLIEST_CONFIRMATION`). */
const EARLIEST = '1900-01-01';
/** The refusals the server names for this form; anything else goes to the general error handling. */
const KNOWN_REFUSALS = new Set([
  'soil_hazard.container',
  'soil_hazard.not_a_bed',
  'soil_hazard.hydroponic',
  'soil_hazard.confirmed_in_future',
  'soil_hazard.confirmed_too_early',
]);

interface SoilHazardDialogProps {
  bedKey: string;
  bedName: string;
  /** The hazards this location takes (`recordableSoilHazards` of its scope); every hazard when not given. */
  hazards?: readonly SoilHazard[];
  onClose: () => void;
  /** The hazard was stored; the section reloads the summary. */
  onSaved: () => void;
}

export default function SoilHazardDialog({
  bedKey,
  bedName,
  hazards = SOIL_HAZARDS,
  onClose,
  onSaved,
}: SoilHazardDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const online = useOnlineStatus();
  const { handleError } = useApiError();
  const notification = useNotification();
  // The day the server calls "today" (UTC): it refuses a later confirmation.
  const today = useMemo(() => toUtcIsoDate(new Date()), []);
  // A single choice (an area: juglone) is preset; the field still shows it, so the form reads the same everywhere.
  const [hazard, setHazard] = useState<SoilHazard | ''>(hazards.length === 1 ? hazards[0] : '');
  const [confirmedAt, setConfirmedAt] = useState(today);
  const [source, setSource] = useState<PathogenConfirmationSource | ''>('');
  const [touched, setTouched] = useState(false);
  const [saving, setSaving] = useState(false);
  const [refusal, setRefusal] = useState<string | null>(null);

  const missing = {
    hazard: hazard === '',
    confirmedAt: confirmedAt === '' || confirmedAt > today || confirmedAt < EARLIEST,
    source: source === '',
  };

  const save = async () => {
    setTouched(true);
    if (saving || !online || hazard === '' || source === '' || missing.confirmedAt) return;
    setSaving(true);
    setRefusal(null);
    try {
      const result = await recordSoilHazard(bedKey, { hazard, confirmed_at: confirmedAt, source });
      const name = t(`enums.soilHazard.${hazard}`);
      if (result.changed) {
        notification.success(t(`${PREFIX}.recorded`, { hazard: name }));
      } else {
        // Nothing written (review D3): the bed already carries it with a later date - never "eingetragen".
        notification.info(t(`${PREFIX}.unchanged`, { hazard: name }));
      }
      onSaved();
    } catch (error) {
      const code = getFieldViolations(error)
        .map((violation) => violation.code)
        .find((candidate): candidate is string => candidate !== undefined && KNOWN_REFUSALS.has(candidate));
      if (code) {
        setRefusal(code);
      } else {
        handleError(error);
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      open
      onClose={saving ? undefined : onClose}
      fullScreen={fullScreen}
      fullWidth
      maxWidth="sm"
      aria-labelledby="soil-hazard-dialog-title"
      data-testid="soil-hazard-dialog"
    >
      <DialogTitle id="soil-hazard-dialog-title">{t(`${PREFIX}.dialogTitle`, { name: bedName })}</DialogTitle>
      <DialogContent>
        <DialogContentText sx={{ mb: 2 }}>{t(`${PREFIX}.dialogIntro`)}</DialogContentText>
        {refusal && (
          <Alert severity="error" sx={{ mb: 2 }} data-testid="soil-hazard-dialog-refusal">
            {t(`${PREFIX}.refusal.${refusal.replace('soil_hazard.', '')}`)}
          </Alert>
        )}
        <Stack spacing={2} sx={{ pt: 1 }}>
          <TextField
            select
            required
            label={t(`${PREFIX}.hazard`)}
            value={hazard}
            onChange={(event) => setHazard(event.target.value as SoilHazard)}
            error={touched && missing.hazard}
            helperText={
              touched && missing.hazard
                ? t(`${PREFIX}.hazardMissing`)
                : t(hazards.length === 1 ? `${PREFIX}.hazardHelperArea` : `${PREFIX}.hazardHelper`)
            }
            fullWidth
            sx={TOUCH}
            data-testid="form-field-hazard"
          >
            {hazards.map((value) => (
              <MenuItem key={value} value={value}>
                {t(`enums.soilHazard.${value}`)}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            type="date"
            required
            label={t(`${PREFIX}.confirmedAt`)}
            value={confirmedAt}
            onChange={(event) => setConfirmedAt(event.target.value)}
            error={touched && missing.confirmedAt}
            helperText={
              touched && missing.confirmedAt
                ? t(`${PREFIX}.confirmedAtInvalid`)
                : t(hazard === 'juglone' ? `${PREFIX}.confirmedAtJuglone` : `${PREFIX}.confirmedAtHelper`)
            }
            fullWidth
            sx={TOUCH}
            data-testid="form-field-confirmed-at"
            slotProps={{ inputLabel: { shrink: true }, htmlInput: { min: EARLIEST, max: today } }}
          />
          <TextField
            select
            required
            label={t(`${PREFIX}.source`)}
            value={source}
            onChange={(event) => setSource(event.target.value as PathogenConfirmationSource)}
            error={touched && missing.source}
            helperText={touched && missing.source ? t(`${PREFIX}.sourceMissing`) : t(`${PREFIX}.sourceHelper`)}
            fullWidth
            sx={TOUCH}
            data-testid="form-field-source"
          >
            {CONFIRMATION_SOURCES.map((value) => (
              <MenuItem key={value} value={value}>
                {t(`enums.pathogenConfirmationSource.${value}`)}
              </MenuItem>
            ))}
          </TextField>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving} sx={{ minHeight: 48 }} data-testid="soil-hazard-dialog-cancel">
          {t('common.cancel')}
        </Button>
        <RequiresConnectivity offline={!online}>
          <Button
            variant="contained"
            onClick={() => void save()}
            loading={saving}
            sx={{ minHeight: 48 }}
            data-testid="soil-hazard-dialog-save"
          >
            {t(`${PREFIX}.save`)}
          </Button>
        </RequiresConnectivity>
      </DialogActions>
    </Dialog>
  );
}
