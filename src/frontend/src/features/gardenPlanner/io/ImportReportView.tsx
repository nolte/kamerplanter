/**
 * The check report of a plan import (REQ-053 GP-UX-051): what would be created, replaced and deleted, which
 * references of the file were dropped, and why the file cannot be imported. Plain data in, no requests.
 */
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import type { DroppedReference, ImportCounts, ImportFinding, PlanImportReport } from './types';

const PREFIX = 'pages.gardenPlan.io.import';

/** `import.not_empty` becomes `import_not_empty`: a dotted code would be read as a nested i18n path. */
export function codeKey(code: string): string {
  return code.replace(/\./g, '_');
}

interface ImportReportViewProps {
  report: PlanImportReport;
  /** Findings of a refused write (422), shown in the place of the report's own. */
  extraFindings?: readonly ImportFinding[];
}

function CountLine({ counts, label }: { counts: ImportCounts; label: string }) {
  const { t } = useTranslation();
  return (
    <Typography variant="body2">
      <strong>{label}:</strong>{' '}
      {t(`${PREFIX}.counts`, {
        locations: counts.locations,
        objects: counts.garden_objects,
        slots: counts.slots,
      })}
    </Typography>
  );
}

function FindingRow({ finding }: { finding: ImportFinding }) {
  const { t } = useTranslation();
  return (
    <ListItem disableGutters sx={{ py: 0.25 }}>
      <ListItemText
        primary={t(`${PREFIX}.codes.${codeKey(finding.code)}`, { defaultValue: finding.code })}
        secondary={[finding.field, finding.key].filter(Boolean).join(' · ')}
      />
    </ListItem>
  );
}

function DroppedRow({ dropped }: { dropped: DroppedReference }) {
  const { t } = useTranslation();
  return (
    <ListItem disableGutters sx={{ py: 0.25 }}>
      <ListItemText
        primary={t(`${PREFIX}.dropped.row`, {
          entity: t(`${PREFIX}.dropped.entities.${dropped.entity}`),
          field: dropped.field,
          reason: t(`${PREFIX}.dropped.reasons.${dropped.reason}`, { defaultValue: dropped.reason }),
        })}
        secondary={dropped.key}
      />
    </ListItem>
  );
}

export function ImportReportView({ report, extraFindings }: ImportReportViewProps) {
  const { t } = useTranslation();
  const findings = extraFindings && extraFindings.length > 0 ? extraFindings : report.errors;
  const findingsTotal = extraFindings && extraFindings.length > 0 ? extraFindings.length : report.errors_total;
  const hiddenDropped = report.dropped_references_total - report.dropped_references.length;
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }} data-testid="plan-import-report">
      <Box>
        <CountLine counts={report.would_create} label={t(`${PREFIX}.create`)} />
        {report.mode === 'replace' && (
          <CountLine counts={report.would_delete} label={t(`${PREFIX}.delete`)} />
        )}
        {report.kept_locations > 0 && (
          <Typography variant="body2">
            {t(`${PREFIX}.kept`, { count: report.kept_locations })}
          </Typography>
        )}
      </Box>

      {findingsTotal === 0 ? (
        <Alert severity="success" data-testid="plan-import-ok">
          {t(`${PREFIX}.noErrors`)}
        </Alert>
      ) : (
        <Alert severity="error" data-testid="plan-import-errors">
          <Typography variant="subtitle2" component="h4">
            {t(`${PREFIX}.errorsTitle`, { count: findingsTotal })}
          </Typography>
          <List dense disablePadding>
            {findings.map((finding, index) => (
              <FindingRow key={`${finding.code}-${finding.field}-${index}`} finding={finding} />
            ))}
          </List>
          {findingsTotal > findings.length && (
            <Typography variant="caption">
              {t(`${PREFIX}.more`, { count: findingsTotal - findings.length })}
            </Typography>
          )}
        </Alert>
      )}

      {report.dropped_references_total > 0 && (
        <Alert severity="warning" data-testid="plan-import-dropped">
          <Typography variant="subtitle2" component="h4">
            {t(`${PREFIX}.dropped.title`, { count: report.dropped_references_total })}
          </Typography>
          <Typography variant="body2">{t(`${PREFIX}.dropped.hint`)}</Typography>
          <List dense disablePadding>
            {report.dropped_references.map((dropped, index) => (
              <DroppedRow key={`${dropped.key}-${dropped.field}-${index}`} dropped={dropped} />
            ))}
          </List>
          {hiddenDropped > 0 && (
            <Typography variant="caption">{t(`${PREFIX}.more`, { count: hiddenDropped })}</Typography>
          )}
        </Alert>
      )}
    </Box>
  );
}
