/**
 * "New season from the previous year" (REQ-053 GP-FR-171, GP-UX, WP 7.17): the year, the check report (`dry_run`),
 * a confirmation. The report names what is created (free slots, no plants, no runs) and what is skipped and why.
 * The optional *Here stood: {family}* line is a display-only hint from GP-API-039; it never changes the request.
 * Lead only (the menu keeps it off for anyone else); lazy, like the other plan dialogs (UI-NFR-003).
 */
import { useEffect, useId, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControlLabel from '@mui/material/FormControlLabel';
import LinearProgress from '@mui/material/LinearProgress';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { isApiError } from '@/api/errors';
import { familiesOfYear, startNewSeason } from './seasonApi';
import { MIN_SEASON_YEAR, type SeasonBedOutcome, type SeasonReport } from './seasonTypes';

const PREFIX = 'pages.gardenPlan.io.season';
/** The hint asks one request per bed; a long list is cut here (the report itself stays complete). */
const MAX_HINTS = 20;
const KNOWN_FAILURES = new Set([
  'season_forbidden',
  'season_invalid_year',
  'plan_revision_conflict',
  'plan_quota_exceeded',
  'VALIDATION_ERROR',
]);

interface NewSeasonDialogProps {
  open: boolean;
  siteKey: string;
  /** Names of the beds by key, to read the report; a bed without one is shown by a neutral label. */
  bedNames: Record<string, string>;
  onClose: () => void;
  /** Slots were written; the page reloads the plan. */
  onApplied: () => void;
}

function failureKey(error: unknown): string {
  if (!isApiError(error)) return 'failed';
  if (error.statusCode === 429) return 'rateLimited';
  if (error.statusCode === 404) return 'notFound';
  if (error.statusCode === 403) return 'season_forbidden';
  const code = error.errorCode.replace(/\./g, '_');
  return KNOWN_FAILURES.has(code) ? code : 'failed';
}

/** The year as the server wants it: a whole number from 2001 up to next year; anything else is `null`. */
function parseSeasonYear(raw: string, now = new Date()): number | null {
  const text = raw.trim();
  if (!/^\d{4}$/.test(text)) return null;
  const value = Number(text);
  return value >= MIN_SEASON_YEAR && value <= now.getFullYear() + 1 ? value : null;
}

export default function NewSeasonDialog({
  open,
  siteKey,
  bedNames,
  onClose,
  onApplied,
}: NewSeasonDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const phone = useMediaQuery(theme.breakpoints.down('sm'));
  const yearId = useId();
  const [yearText, setYearText] = useState(() => String(new Date().getFullYear() + 1));
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);
  const [checked, setChecked] = useState<SeasonReport | null>(null);
  const [applied, setApplied] = useState<SeasonReport | null>(null);
  const [showHints, setShowHints] = useState(false);
  const [hints, setHints] = useState<Record<string, string[]>>({});

  const year = parseSeasonYear(yearText);
  const yearInvalid = yearText !== '' && year === null;
  /** The report belongs to the year it was made for; a changed year needs a new check. */
  const current = checked !== null && checked.year === year ? checked : null;
  const hinted = useMemo(
    () => (current?.beds ?? []).filter((bed) => bed.status === 'copied').slice(0, MAX_HINTS),
    [current],
  );

  useEffect(() => {
    if (!showHints || current === null) return undefined;
    const controller = new AbortController();
    void Promise.all(
      hinted.map(
        async (bed) =>
          [
            bed.location_key,
            await familiesOfYear(bed.location_key, current.source_year, controller.signal),
          ] as const,
      ),
    ).then((rows) => {
      if (!controller.signal.aborted) setHints(Object.fromEntries(rows));
    });
    return () => controller.abort();
  }, [showHints, current, hinted]);

  const run = async (dryRun: boolean) => {
    if (year === null) return;
    setBusy(true);
    setFailure(null);
    try {
      const report = await startNewSeason(siteKey, {
        year,
        dry_run: dryRun,
        expected_revision: dryRun ? null : (current?.plan_revision ?? null),
      });
      if (dryRun) {
        setChecked(report);
        setHints({});
      } else {
        setApplied(report);
        onApplied();
      }
    } catch (error) {
      setFailure(failureKey(error));
    } finally {
      setBusy(false);
    }
  };

  const nameOf = (bed: SeasonBedOutcome) => bedNames[bed.location_key] ?? t(`${PREFIX}.unnamedBed`);
  const canConfirm = current !== null && current.slots_to_create > 0 && !busy;

  return (
    <Dialog
      open={open}
      onClose={busy ? undefined : onClose}
      fullScreen={phone}
      maxWidth="sm"
      fullWidth
      aria-labelledby="plan-season-title"
      data-testid="plan-season-dialog"
    >
      <DialogTitle id="plan-season-title">{t(`${PREFIX}.title`)}</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        <Box role="status" aria-live="polite">
          {busy && (
            <>
              <LinearProgress aria-hidden="true" sx={{ mb: 0.5 }} />
              <Typography variant="body2">{t(`${PREFIX}.working`)}</Typography>
            </>
          )}
        </Box>

        {failure !== null && (
          <Alert severity="error" role="alert" data-testid="plan-season-failure">
            {t(`${PREFIX}.failures.${failure}`)}
          </Alert>
        )}

        {applied !== null ? (
          <Alert severity="success" data-testid="plan-season-done">
            {t(`${PREFIX}.done`, { slots: applied.slots_to_create, beds: applied.beds_copied })}
          </Alert>
        ) : (
          <>
            <Typography variant="body2">{t(`${PREFIX}.intro`)}</Typography>
            <TextField
              id={yearId}
              label={t(`${PREFIX}.year`)}
              value={yearText}
              onChange={(event) => setYearText(event.target.value)}
              error={yearInvalid}
              helperText={
                yearInvalid
                  ? t(`${PREFIX}.yearInvalid`, {
                      min: MIN_SEASON_YEAR,
                      max: new Date().getFullYear() + 1,
                    })
                  : t(`${PREFIX}.yearHelp`)
              }
              slotProps={{
                htmlInput: {
                  inputMode: 'numeric',
                  maxLength: 4,
                  'data-testid': 'plan-season-year',
                },
              }}
              sx={{ maxWidth: 200 }}
            />

            {current !== null && (
              <Box
                data-testid="plan-season-report"
                sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}
              >
                <Typography variant="subtitle2" component="h3">
                  {t(`${PREFIX}.report.title`, { source: current.source_year, year: current.year })}
                </Typography>
                <Typography variant="body2">
                  {t(`${PREFIX}.report.summary`, {
                    slots: current.slots_to_create,
                    beds: current.beds_copied,
                  })}
                </Typography>
                {current.beds_skipped > 0 && (
                  <Typography variant="body2">
                    {t(`${PREFIX}.report.skipped`, { beds: current.beds_skipped })}
                  </Typography>
                )}
                {current.beds.length === 0 && (
                  <Alert severity="info">
                    {t(`${PREFIX}.report.empty`, { source: current.source_year })}
                  </Alert>
                )}
                <List dense disablePadding aria-label={t(`${PREFIX}.report.listLabel`)}>
                  {current.beds.map((bed) => (
                    <ListItem key={bed.location_key} disableGutters>
                      <ListItemText
                        primary={`${nameOf(bed)}: ${t(`${PREFIX}.status.${bed.status}`, { slots: bed.slots })}`}
                        secondary={
                          showHints && bed.status === 'copied'
                            ? (hints[bed.location_key] ?? []).length > 0
                              ? t(`${PREFIX}.hereStood`, {
                                  what: (hints[bed.location_key] ?? []).join(', '),
                                })
                              : t(`${PREFIX}.hereStoodUnknown`)
                            : bed.slots_outside_bed > 0
                              ? t(`${PREFIX}.outsideBed`, { count: bed.slots_outside_bed })
                              : undefined
                        }
                      />
                    </ListItem>
                  ))}
                </List>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={showHints}
                      onChange={(event) => setShowHints(event.target.checked)}
                    />
                  }
                  label={t(`${PREFIX}.showHints`)}
                />
                <Typography variant="caption" color="text.secondary">
                  {t(`${PREFIX}.promise`)}
                </Typography>
              </Box>
            )}
          </>
        )}
      </DialogContent>
      <DialogActions sx={{ gap: 1 }}>
        <Button onClick={onClose} disabled={busy} sx={{ minHeight: 44 }}>
          {applied !== null ? t(`${PREFIX}.close`) : t(`${PREFIX}.cancel`)}
        </Button>
        {applied === null && (
          <>
            <Button
              onClick={() => void run(true)}
              disabled={busy || year === null}
              variant={current === null ? 'contained' : 'outlined'}
              sx={{ minHeight: 44 }}
              data-testid="plan-season-check"
            >
              {t(`${PREFIX}.check`)}
            </Button>
            <Button
              onClick={() => void run(false)}
              disabled={!canConfirm}
              variant="contained"
              sx={{ minHeight: 44 }}
              data-testid="plan-season-confirm"
            >
              {t(`${PREFIX}.confirm`)}
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
}
