/**
 * The import assistant of the garden plan (REQ-053 GP-UX-051, GP-API-005) in three steps: pick the file, read the
 * check report (`dry_run`), choose the mode. `replace` names the mandatory snapshot and asks for the site's name
 * before anything is overwritten; the server asks for the same name. Lazy, like the export dialog.
 */
import { useId, useRef, useState, type ChangeEvent } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormLabel from '@mui/material/FormLabel';
import LinearProgress from '@mui/material/LinearProgress';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import Stepper from '@mui/material/Stepper';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { isApiError } from '@/api/errors';
import { fetchPlanExport, importPlan, saveBlob } from './ioApi';
import { ImportReportView, codeKey } from './ImportReportView';
import {
  MAX_IMPORT_FILE_BYTES,
  type ImportFinding,
  type ImportMode,
  type PlanImportReport,
} from './types';

const PREFIX = 'pages.gardenPlan.io.import';
const STEPS = ['file', 'report', 'mode'] as const;

interface ImportWizardProps {
  open: boolean;
  siteKey: string;
  siteName: string;
  onClose: () => void;
  /** The import was written; the page reloads the plan. */
  onImported: () => void;
}

interface Checked {
  report: PlanImportReport;
  mode: ImportMode;
  force: boolean;
}

interface Failure {
  /** Key below `pages.gardenPlan.io.import.failures`. */
  key: string;
  findings: ImportFinding[];
}

const KNOWN_FAILURES = new Set([
  'import_forbidden',
  'import_not_empty',
  'import_schema_version_missing',
  'import_schema_version_unsupported',
  'import_unknown_keys',
  'import_site_name_mismatch',
  'plan_revision_conflict',
  'REQUEST_BODY_TOO_LARGE',
  'VALIDATION_ERROR',
]);

function failureOf(error: unknown): Failure {
  if (!isApiError(error)) return { key: 'failed', findings: [] };
  if (error.statusCode === 429) return { key: 'rateLimited', findings: [] };
  if (error.statusCode === 404) return { key: 'notFound', findings: [] };
  const code = codeKey(error.errorCode);
  const findings = error.details
    .filter((detail) => typeof detail.code === 'string' && detail.code !== error.errorCode)
    .map((detail) => ({
      field: detail.field ?? '',
      code: String((detail as { code?: unknown }).code),
      key: typeof (detail as { key?: unknown }).key === 'string' ? String((detail as { key?: unknown }).key) : null,
    }));
  return { key: KNOWN_FAILURES.has(code) ? code : 'failed', findings };
}

export default function ImportWizard({ open, siteKey, siteName, onClose, onImported }: ImportWizardProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const phone = useMediaQuery(theme.breakpoints.down('sm'));
  const fileInput = useRef<HTMLInputElement>(null);
  const nameId = useId();
  const [step, setStep] = useState<0 | 1 | 2>(0);
  const [document_, setDocument] = useState<Record<string, unknown> | null>(null);
  const [fileName, setFileName] = useState('');
  const [fileError, setFileError] = useState<string | null>(null);
  const [checked, setChecked] = useState<Checked | null>(null);
  const [mode, setMode] = useState<ImportMode>('replace');
  const [force, setForce] = useState(false);
  const [confirmName, setConfirmName] = useState('');
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<Failure | null>(null);
  const [result, setResult] = useState<PlanImportReport | null>(null);

  const check = async (nextMode: ImportMode, nextForce: boolean, source = document_) => {
    if (source === null) return;
    setBusy(true);
    setFailure(null);
    try {
      const report = await importPlan(siteKey, {
        mode: nextMode,
        dry_run: true,
        force: nextForce,
        confirm_site_name: null,
        document: source,
      });
      setChecked({ report, mode: nextMode, force: nextForce });
      setStep((current) => (current === 0 ? 1 : current));
    } catch (error) {
      setFailure(failureOf(error));
    } finally {
      setBusy(false);
    }
  };

  const pickFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    setFileError(null);
    setFailure(null);
    setChecked(null);
    if (file.size > MAX_IMPORT_FILE_BYTES) {
      setFileError('tooLarge');
      return;
    }
    let parsed: unknown;
    try {
      parsed = JSON.parse(await file.text());
    } catch {
      setFileError('notJson');
      return;
    }
    if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed) || !('schema_version' in parsed)) {
      setFileError('notABackup');
      return;
    }
    const source = parsed as Record<string, unknown>;
    setDocument(source);
    setFileName(file.name);
    setMode('replace');
    setForce(false);
    setConfirmName('');
    await check('replace', false, source);
  };

  const apply = async () => {
    if (document_ === null) return;
    setBusy(true);
    setFailure(null);
    try {
      const report = await importPlan(siteKey, {
        mode,
        dry_run: false,
        force,
        confirm_site_name: mode === 'replace' ? confirmName : null,
        document: document_,
      });
      setResult(report);
      onImported();
    } catch (error) {
      setFailure(failureOf(error));
    } finally {
      setBusy(false);
    }
  };

  const downloadBackup = async () => {
    setBusy(true);
    try {
      const file = await fetchPlanExport(siteKey, {
        format: 'json',
        paper: 'a4',
        orientation: 'landscape',
        scale: 'auto',
        layers: [],
        bedList: false,
      });
      saveBlob(file.blob, file.filename);
    } catch {
      setFailure({ key: 'failed', findings: [] });
    } finally {
      setBusy(false);
    }
  };

  const current = checked !== null && checked.mode === mode && checked.force === force ? checked : null;
  const onlyNotEmpty =
    checked !== null && checked.report.errors.every((finding) => finding.code === 'import.not_empty');
  const stepOneBlocked = checked === null || (checked.report.errors_total > 0 && !onlyNotEmpty);
  const needsForce = checked?.report.errors.some((finding) => finding.code === 'import.not_empty') ?? false;
  const nameMatches = confirmName.trim() === siteName.trim() && confirmName.trim() !== '';
  const canApply =
    current !== null && current.report.errors_total === 0 && (mode === 'merge' || nameMatches);

  return (
    <Dialog
      open={open}
      onClose={busy ? undefined : onClose}
      fullScreen={phone}
      maxWidth="md"
      fullWidth
      aria-labelledby="plan-import-title"
      data-testid="plan-import-wizard"
    >
      <DialogTitle id="plan-import-title">{t(`${PREFIX}.title`)}</DialogTitle>
      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        {result === null && (
          <Stepper
            activeStep={step}
            alternativeLabel={phone}
            aria-label={t(`${PREFIX}.stepsLabel`)}
          >
            {STEPS.map((name) => (
              <Step key={name}>
                <StepLabel>{t(`${PREFIX}.steps.${name}`)}</StepLabel>
              </Step>
            ))}
          </Stepper>
        )}

        <Box role="status" aria-live="polite">
          {busy && (
            <>
              <LinearProgress aria-hidden="true" sx={{ mb: 0.5 }} />
              <Typography variant="body2">{t(`${PREFIX}.working`)}</Typography>
            </>
          )}
        </Box>

        {failure !== null && (
          <Alert severity="error" role="alert" data-testid="plan-import-failure">
            {t(`${PREFIX}.failures.${failure.key}`)}
          </Alert>
        )}

        {result !== null ? (
          <Alert severity="success" data-testid="plan-import-done">
            {t(`${PREFIX}.done`, {
              locations: result.would_create.locations,
              objects: result.would_create.garden_objects,
              slots: result.would_create.slots,
            })}
            {result.snapshot_written && ` ${t(`${PREFIX}.doneSnapshot`)}`}
          </Alert>
        ) : (
          <>
            {step === 0 && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                <Typography variant="body2">{t(`${PREFIX}.fileHelp`)}</Typography>
                <input
                  ref={fileInput}
                  type="file"
                  accept=".json,application/json"
                  hidden
                  onChange={pickFile}
                  data-testid="plan-import-file"
                  tabIndex={-1}
                  aria-hidden="true"
                />
                <Box>
                  <Button
                    variant="outlined"
                    onClick={() => fileInput.current?.click()}
                    disabled={busy}
                    sx={{ minHeight: 48 }}
                    data-testid="plan-import-choose"
                  >
                    {t(`${PREFIX}.chooseFile`)}
                  </Button>
                </Box>
                {fileName !== '' && fileError === null && (
                  <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>
                    {t(`${PREFIX}.chosen`, { name: fileName })}
                  </Typography>
                )}
                {fileError !== null && (
                  <Alert severity="error" role="alert" data-testid="plan-import-file-error">
                    {t(`${PREFIX}.fileErrors.${fileError}`)}
                  </Alert>
                )}
              </Box>
            )}

            {step === 1 && checked !== null && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Typography variant="h3" sx={{ fontSize: '1.05rem' }}>
                  {t(`${PREFIX}.reportTitle`, { name: fileName })}
                </Typography>
                <ImportReportView report={checked.report} />
              </Box>
            )}

            {step === 2 && (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <FormControl>
                  <FormLabel id="plan-import-mode-label">{t(`${PREFIX}.mode`)}</FormLabel>
                  <RadioGroup
                    aria-labelledby="plan-import-mode-label"
                    value={mode}
                    onChange={(event) => setMode(event.target.value as ImportMode)}
                  >
                    <FormControlLabel
                      value="replace"
                      control={<Radio slotProps={{ input: { 'data-testid': 'plan-import-mode-replace' } as object }} />}
                      label={
                        <Box>
                          <Typography variant="body1">{t(`${PREFIX}.modes.replace`)}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            {t(`${PREFIX}.modeHints.replace`)}
                          </Typography>
                        </Box>
                      }
                      sx={{ alignItems: 'flex-start', minHeight: 48, mb: 0.5 }}
                    />
                    <FormControlLabel
                      value="merge"
                      control={<Radio slotProps={{ input: { 'data-testid': 'plan-import-mode-merge' } as object }} />}
                      label={
                        <Box>
                          <Typography variant="body1">{t(`${PREFIX}.modes.merge`)}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            {t(`${PREFIX}.modeHints.merge`)}
                          </Typography>
                        </Box>
                      }
                      sx={{ alignItems: 'flex-start', minHeight: 48, mb: 0.5 }}
                    />
                  </RadioGroup>
                </FormControl>

                {mode === 'replace' && needsForce && (
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={force}
                        onChange={(event) => setForce(event.target.checked)}
                        slotProps={{ input: { 'data-testid': 'plan-import-force' } as object }}
                      />
                    }
                    label={t(`${PREFIX}.force`)}
                    sx={{ alignItems: 'flex-start', minHeight: 44 }}
                  />
                )}

                {current === null && checked !== null && (
                  <Alert severity="info" data-testid="plan-import-recheck-hint">
                    {t(`${PREFIX}.recheckHint`)}
                  </Alert>
                )}
                {current !== null && (current.report.errors_total > 0 || (failure?.findings.length ?? 0) > 0) && (
                  <ImportReportView report={current.report} extraFindings={failure?.findings} />
                )}

                {mode === 'replace' && current !== null && (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                    <Alert severity="warning" data-testid="plan-import-snapshot-notice">
                      {t(`${PREFIX}.snapshotNotice`)}
                    </Alert>
                    <Box>
                      <Button
                        onClick={downloadBackup}
                        disabled={busy}
                        sx={{ minHeight: 44 }}
                        data-testid="plan-import-backup"
                      >
                        {t(`${PREFIX}.backupFirst`)}
                      </Button>
                    </Box>
                    <TextField
                      id={nameId}
                      label={t(`${PREFIX}.confirmName`, { name: siteName })}
                      value={confirmName}
                      onChange={(event) => setConfirmName(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' && canApply && !busy) {
                          event.preventDefault();
                          void apply();
                        }
                      }}
                      autoComplete="off"
                      error={confirmName !== '' && !nameMatches}
                      helperText={
                        confirmName !== '' && !nameMatches
                          ? t(`${PREFIX}.confirmNameMismatch`)
                          : t(`${PREFIX}.confirmNameHelp`)
                      }
                      slotProps={{ htmlInput: { 'data-testid': 'plan-import-confirm-name', maxLength: 200 } }}
                    />
                  </Box>
                )}
              </Box>
            )}
          </>
        )}
      </DialogContent>
      <DialogActions>
        {result !== null ? (
          <Button variant="contained" onClick={onClose} autoFocus sx={{ minHeight: 44 }} data-testid="plan-import-close">
            {t('common.close')}
          </Button>
        ) : (
          <>
            <Button onClick={onClose} disabled={busy} sx={{ minHeight: 44 }}>
              {t('common.cancel')}
            </Button>
            {step > 0 && (
              <Button
                onClick={() => setStep((previous) => (previous === 2 ? 1 : 0))}
                disabled={busy}
                sx={{ minHeight: 44 }}
              >
                {t('common.back')}
              </Button>
            )}
            {step === 1 && (
              <Button
                variant="contained"
                onClick={() => setStep(2)}
                disabled={busy || stepOneBlocked}
                sx={{ minHeight: 44 }}
                data-testid="plan-import-next"
              >
                {t('common.next')}
              </Button>
            )}
            {step === 2 && current === null && (
              <Button
                variant="contained"
                onClick={() => void check(mode, force)}
                loading={busy}
                sx={{ minHeight: 44 }}
                data-testid="plan-import-check"
              >
                {t(`${PREFIX}.check`)}
              </Button>
            )}
            {step === 2 && current !== null && (
              <Button
                variant="contained"
                color={mode === 'replace' ? 'error' : 'primary'}
                onClick={apply}
                loading={busy}
                disabled={!canApply}
                sx={{ minHeight: 44 }}
                data-testid="plan-import-apply"
              >
                {t(`${PREFIX}.apply.${mode}`)}
              </Button>
            )}
          </>
        )}
      </DialogActions>
    </Dialog>
  );
}
