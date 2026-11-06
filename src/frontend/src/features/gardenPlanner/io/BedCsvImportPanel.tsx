/**
 * The CSV bed list path of the import assistant (REQ-053 GP-FR-174, WP 8.27): pick a `.csv` file, read the check
 * report of the dry run (line errors and warnings, the beds it would create), confirm - only the valid lines are
 * written - and go back to the editor, where the new beds are selected for arranging. It sits inside the import
 * wizard (lazy, like the snapshots) and is the lead's, as the wizard is. The server parses the file; nothing here
 * reads its cells.
 */
import { useId, useRef, useState, type ChangeEvent } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import LinearProgress from '@mui/material/LinearProgress';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import Stepper from '@mui/material/Stepper';
import Typography from '@mui/material/Typography';
import { isApiError } from '@/api/errors';
import { importBedCsv } from './ioApi';
import { codeKey } from './ImportReportView';
import {
  MAX_CSV_FILE_BYTES,
  MAX_CSV_ROWS,
  type BedCsvFinding,
  type BedCsvImportReport,
  type BedCsvRow,
} from './types';

const PREFIX = 'pages.gardenPlan.io.csv';
const STEPS = ['file', 'report', 'done'] as const;

interface BedCsvImportPanelProps {
  siteKey: string;
  /** Back to the backup import; absent when the panel was opened on its own. */
  onBack?: () => void;
  /** A request is running: the wizard keeps itself open meanwhile. */
  onBusyChange: (busy: boolean) => void;
  /** The valid lines were written; the report carries the new beds' keys (`rows[].location_key`). */
  onApplied: (report: BedCsvImportReport) => void;
}

/** A refused request: the key below `pages.gardenPlan.io.csv.failures` and what its message interpolates. */
interface Failure {
  key: string;
  values: Record<string, string | number>;
}

const KNOWN_FAILURES = new Set([
  'csv_invalid_encoding',
  'csv_invalid_delimiter',
  'csv_empty',
  'csv_malformed',
  'csv_missing_column',
  'csv_duplicate_column',
  'plan_quota_exceeded',
  'plan_revision_conflict',
  'import_forbidden',
]);

function failureOf(error: unknown): Failure {
  if (!isApiError(error)) return { key: 'failed', values: {} };
  if (error.statusCode === 413) return { key: 'tooLarge', values: {} };
  if (error.statusCode === 429) return { key: 'rateLimited', values: {} };
  if (error.statusCode === 404) return { key: 'notFound', values: {} };
  const code = codeKey(error.errorCode);
  if (!KNOWN_FAILURES.has(code)) return { key: 'failed', values: {} };
  const detail = (error.details[0] ?? {}) as unknown as Record<string, unknown>;
  const values: Record<string, string | number> = {};
  if (Array.isArray(detail.columns)) values.columns = detail.columns.map(String).join(', ');
  if (typeof detail.column === 'string') values.column = detail.column;
  if (typeof detail.limit === 'number') values.limit = detail.limit;
  if (typeof detail.current === 'number') values.current = detail.current;
  // A message that names a value the envelope did not carry falls back to the plain one.
  if (code === 'csv_missing_column' && values.columns === undefined) return { key: 'csv_missing_column_plain', values };
  if (code === 'csv_duplicate_column' && values.column === undefined) return { key: 'csv_duplicate_column_plain', values };
  if (code === 'plan_quota_exceeded' && values.limit === undefined) return { key: 'plan_quota_exceeded_plain', values };
  return { key: code, values };
}

/** A local check of the picked file, before anything is sent. */
function fileErrorOf(file: File): string | null {
  const isCsv = /\.csv$/i.test(file.name) || file.type === 'text/csv';
  if (!isCsv) return 'notCsv';
  if (file.size === 0) return 'empty';
  if (file.size > MAX_CSV_FILE_BYTES) return 'tooLarge';
  return null;
}

function FindingRow({ finding }: { finding: BedCsvFinding }) {
  const { t } = useTranslation();
  const where =
    finding.column === null
      ? t(`${PREFIX}.atLine`, { line: finding.line })
      : t(`${PREFIX}.atLineColumn`, { line: finding.line, column: finding.column });
  return (
    <ListItem disableGutters sx={{ py: 0.25 }}>
      <ListItemText
        primary={`${where}: ${t(`${PREFIX}.codes.${codeKey(finding.code)}`, { defaultValue: finding.code })}`}
      />
    </ListItem>
  );
}

function RowLine({ row }: { row: BedCsvRow }) {
  const { t, i18n } = useTranslation();
  const number = new Intl.NumberFormat(i18n.language, { maximumFractionDigits: 2 });
  return (
    <ListItem disableGutters sx={{ py: 0.25 }}>
      <ListItemText
        primary={row.name}
        secondary={[
          t(`${PREFIX}.atLine`, { line: row.line }),
          t(`${PREFIX}.size`, { width: number.format(row.width_m), length: number.format(row.length_m) }),
          t(`enums.sunExposure.${row.sun_exposure}`, { defaultValue: row.sun_exposure }),
        ].join(' · ')}
      />
    </ListItem>
  );
}

function FindingList({
  findings,
  total,
  title,
  severity,
  testId,
}: {
  findings: readonly BedCsvFinding[];
  total: number;
  title: string;
  severity: 'error' | 'warning';
  testId: string;
}) {
  const { t } = useTranslation();
  return (
    <Alert severity={severity} data-testid={testId}>
      <Typography variant="subtitle2" component="h4">
        {title}
      </Typography>
      <List dense disablePadding aria-label={title} sx={{ maxHeight: 240, overflowY: 'auto' }}>
        {findings.map((finding, index) => (
          <FindingRow key={`${finding.line}-${finding.column ?? ''}-${finding.code}-${index}`} finding={finding} />
        ))}
      </List>
      {total > findings.length && (
        <Typography variant="caption">
          {t('pages.gardenPlan.io.import.more', { count: total - findings.length })}
        </Typography>
      )}
    </Alert>
  );
}

function CsvReport({ report }: { report: BedCsvImportReport }) {
  const { t } = useTranslation();
  const bedsTitle = t(`${PREFIX}.bedsTitle`, { count: report.rows_valid });
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }} data-testid="plan-csv-report">
      <Typography variant="body2" data-testid="plan-csv-summary">
        {t(`${PREFIX}.summary`, { valid: report.rows_valid, total: report.rows_total, skipped: report.rows_skipped })}
      </Typography>

      {report.errors_total === 0 ? (
        <Alert severity="success" data-testid="plan-csv-ok">
          {t(`${PREFIX}.noErrors`)}
        </Alert>
      ) : (
        <FindingList
          findings={report.errors}
          total={report.errors_total}
          title={t(`${PREFIX}.errorsTitle`, { count: report.errors_total })}
          severity="error"
          testId="plan-csv-errors"
        />
      )}

      {report.warnings_total > 0 && (
        <FindingList
          findings={report.warnings}
          total={report.warnings_total}
          title={t(`${PREFIX}.warningsTitle`, { count: report.warnings_total })}
          severity="warning"
          testId="plan-csv-warnings"
        />
      )}

      {report.ignored_columns.length > 0 && (
        <Alert severity="info" data-testid="plan-csv-ignored">
          {t(`${PREFIX}.ignoredColumns`, { columns: report.ignored_columns.join(', ') })}
        </Alert>
      )}

      {report.rows.length > 0 && (
        <Box>
          <Typography variant="subtitle2" component="h4">
            {bedsTitle}
          </Typography>
          <List dense disablePadding aria-label={bedsTitle} sx={{ maxHeight: 240, overflowY: 'auto' }}>
            {report.rows.map((row) => (
              <RowLine key={row.line} row={row} />
            ))}
          </List>
        </Box>
      )}

      {report.rows_valid === 0 && (
        <Alert severity="warning" data-testid="plan-csv-nothing">
          {t(`${PREFIX}.nothingValid`)}
        </Alert>
      )}
    </Box>
  );
}

export default function BedCsvImportPanel({ siteKey, onBack, onBusyChange, onApplied }: BedCsvImportPanelProps) {
  const { t } = useTranslation();
  const fileInput = useRef<HTMLInputElement>(null);
  const helpId = useId();
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [report, setReport] = useState<BedCsvImportReport | null>(null);
  /** The plan changed since the check (409): the report is stale until the file is checked again. */
  const [stale, setStale] = useState(false);
  const [busy, setBusyState] = useState(false);
  const [failure, setFailure] = useState<Failure | null>(null);
  const [result, setResult] = useState<BedCsvImportReport | null>(null);

  const setBusy = (next: boolean) => {
    setBusyState(next);
    onBusyChange(next);
  };

  const check = async (source: File) => {
    setBusy(true);
    setFailure(null);
    setStale(false);
    try {
      setReport(await importBedCsv(siteKey, source, { dryRun: true }));
    } catch (error) {
      setReport(null);
      setFailure(failureOf(error));
    } finally {
      setBusy(false);
    }
  };

  const pickFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const picked = event.target.files?.[0];
    event.target.value = '';
    if (!picked) return;
    setFailure(null);
    setReport(null);
    const error = fileErrorOf(picked);
    setFileError(error);
    if (error !== null) {
      setFile(null);
      return;
    }
    setFile(picked);
    await check(picked);
  };

  const apply = async () => {
    if (file === null || report === null) return;
    setBusy(true);
    setFailure(null);
    try {
      const written = await importBedCsv(siteKey, file, { dryRun: false, expectedRevision: report.plan_revision });
      setResult(written);
      onApplied(written);
    } catch (error) {
      const next = failureOf(error);
      if (next.key === 'plan_revision_conflict') setStale(true);
      setFailure(next);
    } finally {
      setBusy(false);
    }
  };

  const step = result !== null ? 2 : report !== null ? 1 : 0;
  const canApply = report !== null && !stale && report.rows_valid > 0 && !busy;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }} data-testid="plan-csv-import">
      <Stepper activeStep={step} alternativeLabel aria-label={t(`${PREFIX}.stepsLabel`)}>
        {STEPS.map((name) => (
          <Step key={name} completed={result !== null ? true : undefined}>
            <StepLabel>{t(`${PREFIX}.steps.${name}`)}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Box role="status" aria-live="polite">
        {busy && (
          <>
            <LinearProgress aria-hidden="true" sx={{ mb: 0.5 }} />
            <Typography variant="body2">{t('pages.gardenPlan.io.import.working')}</Typography>
          </>
        )}
      </Box>

      {failure !== null && (
        <Alert severity="error" role="alert" data-testid="plan-csv-failure">
          {t(`${PREFIX}.failures.${failure.key}`, failure.values)}
        </Alert>
      )}

      {result !== null ? (
        <Alert severity="success" data-testid="plan-csv-done">
          {t(`${PREFIX}.done`, { count: result.rows_valid })}
          {result.rows_skipped > 0 && ` ${t(`${PREFIX}.doneSkipped`, { count: result.rows_skipped })}`}
        </Alert>
      ) : (
        <>
          <Box id={helpId} sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            <Typography variant="body2">{t(`${PREFIX}.help`)}</Typography>
            <Typography variant="body2" color="text.secondary">
              {t(`${PREFIX}.columns`)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t(`${PREFIX}.format`, { rows: MAX_CSV_ROWS })}
            </Typography>
          </Box>
          <input
            ref={fileInput}
            type="file"
            accept=".csv,text/csv"
            hidden
            onChange={pickFile}
            data-testid="plan-csv-file"
            tabIndex={-1}
            aria-hidden="true"
          />
          <Box>
            <Button
              variant={report === null ? 'contained' : 'outlined'}
              onClick={() => fileInput.current?.click()}
              disabled={busy}
              aria-describedby={helpId}
              sx={{ minHeight: 48 }}
              data-testid="plan-csv-choose"
            >
              {t(report === null ? `${PREFIX}.chooseFile` : `${PREFIX}.chooseOther`)}
            </Button>
          </Box>
          {file !== null && fileError === null && (
            <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>
              {t('pages.gardenPlan.io.import.chosen', { name: file.name })}
            </Typography>
          )}
          {fileError !== null && (
            <Alert severity="error" role="alert" data-testid="plan-csv-file-error">
              {t(`${PREFIX}.fileErrors.${fileError}`)}
            </Alert>
          )}

          {report !== null && <CsvReport report={report} />}

          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {onBack !== undefined && (
              <Button onClick={onBack} disabled={busy} sx={{ minHeight: 44 }} data-testid="plan-csv-back">
                {t('common.back')}
              </Button>
            )}
            {stale && file !== null && (
              <Button
                variant="outlined"
                onClick={() => void check(file)}
                disabled={busy}
                sx={{ minHeight: 44 }}
                data-testid="plan-csv-recheck"
              >
                {t(`${PREFIX}.recheck`)}
              </Button>
            )}
            {report !== null && (
              <Button
                variant="contained"
                onClick={() => void apply()}
                loading={busy}
                disabled={!canApply}
                sx={{ minHeight: 44 }}
                data-testid="plan-csv-apply"
              >
                {t(`${PREFIX}.apply`, { count: report.rows_valid })}
              </Button>
            )}
          </Box>
        </>
      )}
    </Box>
  );
}
