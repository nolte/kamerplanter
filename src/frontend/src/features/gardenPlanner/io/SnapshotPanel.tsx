/**
 * The earlier states of the plan (REQ-053 GP-FR-148/170, WP 7.19): the snapshots a `replace` import left behind, a
 * check of what restoring one would change, and the restore itself. It sits inside the import wizard (lazy, like
 * it) and is the lead's, as the wizard is. A restore is a `replace` with the stored plan: it asks for the site's
 * name, keeps beds with active plants unless told otherwise and writes the plan it overwrites as a snapshot of its
 * own first, so it can be undone the same way.
 */
import { useCallback, useEffect, useId, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import LinearProgress from '@mui/material/LinearProgress';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { isApiError } from '@/api/errors';
import { listPlanSnapshots, restorePlanSnapshot } from './ioApi';
import { ImportReportView, codeKey } from './ImportReportView';
import type { PlanImportReport, PlanSnapshot } from './types';

const PREFIX = 'pages.gardenPlan.io.snapshots';

interface SnapshotPanelProps {
  siteKey: string;
  siteName: string;
  onBack: () => void;
  /** The snapshot was written back; the page reloads the plan. */
  onRestored: (report: PlanImportReport) => void;
}

type Listing =
  | { status: 'loading' }
  | { status: 'ready'; snapshots: PlanSnapshot[] }
  | { status: 'error'; key: string };

/** Key below `pages.gardenPlan.io.snapshots.failures` for a refused request. */
function failureKey(error: unknown): string {
  if (!isApiError(error)) return 'failed';
  if (error.statusCode === 403) return 'forbidden';
  if (error.statusCode === 404) return 'notFound';
  if (error.statusCode === 429) return 'rateLimited';
  const code = codeKey(error.errorCode);
  return ['import_not_empty', 'import_site_name_mismatch', 'plan_revision_conflict'].includes(code) ? code : 'failed';
}

function when(value: string, language: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString(language);
}

export default function SnapshotPanel({ siteKey, siteName, onBack, onRestored }: SnapshotPanelProps) {
  const { t, i18n } = useTranslation();
  const nameId = useId();
  const [listing, setListing] = useState<Listing>({ status: 'loading' });
  const [chosen, setChosen] = useState<PlanSnapshot | null>(null);
  const [checked, setChecked] = useState<{ auditKey: string; force: boolean; report: PlanImportReport } | null>(null);
  const [force, setForce] = useState(false);
  const [confirmName, setConfirmName] = useState('');
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listPlanSnapshots(siteKey)
      .then((snapshots) => {
        if (!cancelled) setListing({ status: 'ready', snapshots });
      })
      .catch((error: unknown) => {
        if (!cancelled) setListing({ status: 'error', key: failureKey(error) });
      });
    return () => {
      cancelled = true;
    };
  }, [siteKey]);

  const check = useCallback(
    async (snapshot: PlanSnapshot, withForce: boolean) => {
      setBusy(true);
      setFailure(null);
      try {
        const report = await restorePlanSnapshot(siteKey, snapshot.audit_key, {
          dry_run: true,
          force: withForce,
          confirm_site_name: null,
        });
        setChecked({ auditKey: snapshot.audit_key, force: withForce, report });
      } catch (error) {
        setChecked(null);
        setFailure(failureKey(error));
      } finally {
        setBusy(false);
      }
    },
    [siteKey],
  );

  const choose = (snapshot: PlanSnapshot) => {
    setChosen(snapshot);
    setForce(false);
    setConfirmName('');
    setChecked(null);
    void check(snapshot, false);
  };

  const restore = async () => {
    if (chosen === null) return;
    setBusy(true);
    setFailure(null);
    try {
      const report = await restorePlanSnapshot(siteKey, chosen.audit_key, {
        dry_run: false,
        force,
        confirm_site_name: confirmName,
      });
      onRestored(report);
    } catch (error) {
      setFailure(failureKey(error));
    } finally {
      setBusy(false);
    }
  };

  const current =
    chosen !== null && checked !== null && checked.auditKey === chosen.audit_key && checked.force === force
      ? checked.report
      : null;
  const needsForce = checked?.report.errors.some((finding) => finding.code === 'import.not_empty') ?? false;
  const nameMatches = confirmName.trim() === siteName.trim() && confirmName.trim() !== '';
  const canRestore = current !== null && current.errors_total === 0 && nameMatches;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }} data-testid="plan-snapshots">
      <Typography variant="h3" sx={{ fontSize: '1.05rem' }}>
        {t(`${PREFIX}.title`)}
      </Typography>
      <Typography variant="body2">{t(`${PREFIX}.help`)}</Typography>

      <Box role="status" aria-live="polite">
        {(busy || listing.status === 'loading') && (
          <>
            <LinearProgress aria-hidden="true" sx={{ mb: 0.5 }} />
            <Typography variant="body2">{t('pages.gardenPlan.io.import.working')}</Typography>
          </>
        )}
      </Box>

      {listing.status === 'error' && (
        <Alert severity="error" role="alert" data-testid="plan-snapshots-error">
          {t(`${PREFIX}.failures.${listing.key}`)}
        </Alert>
      )}
      {failure !== null && (
        <Alert severity="error" role="alert" data-testid="plan-snapshots-failure">
          {t(`${PREFIX}.failures.${failure}`)}
        </Alert>
      )}

      {listing.status === 'ready' && listing.snapshots.length === 0 && (
        <Alert severity="info" data-testid="plan-snapshots-empty">
          {t(`${PREFIX}.empty`)}
        </Alert>
      )}
      {listing.status === 'ready' && listing.snapshots.length > 0 && (
        <List dense aria-label={t(`${PREFIX}.title`)} sx={{ maxHeight: 240, overflowY: 'auto' }}>
          {listing.snapshots.map((snapshot) => (
            <ListItemButton
              key={snapshot.audit_key}
              selected={chosen?.audit_key === snapshot.audit_key}
              onClick={() => choose(snapshot)}
              disabled={busy}
              sx={{ minHeight: 48 }}
              data-testid={`plan-snapshot-${snapshot.audit_key}`}
            >
              <ListItemText
                primary={when(snapshot.at, i18n.language)}
                secondary={[
                  t(`${PREFIX}.counts`, {
                    locations: snapshot.locations,
                    objects: snapshot.garden_objects,
                    slots: snapshot.slots,
                  }),
                  snapshot.changed_by_name,
                ]
                  .filter(Boolean)
                  .join(' · ')}
              />
            </ListItemButton>
          ))}
        </List>
      )}

      {chosen !== null && current !== null && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          <ImportReportView report={current} />
          <Alert severity="warning" data-testid="plan-snapshots-notice">
            {t(`${PREFIX}.notice`)}
          </Alert>
          {(needsForce || force) && (
            <FormControlLabel
              control={
                <Checkbox
                  checked={force}
                  onChange={(event) => {
                    setForce(event.target.checked);
                    void check(chosen, event.target.checked);
                  }}
                  slotProps={{ input: { 'data-testid': 'plan-snapshots-force' } as object }}
                />
              }
              label={t('pages.gardenPlan.io.import.force')}
              sx={{ alignItems: 'flex-start', minHeight: 44 }}
            />
          )}
          <TextField
            id={nameId}
            label={t('pages.gardenPlan.io.import.confirmName', { name: siteName })}
            value={confirmName}
            onChange={(event) => setConfirmName(event.target.value)}
            autoComplete="off"
            error={confirmName !== '' && !nameMatches}
            helperText={
              confirmName !== '' && !nameMatches
                ? t('pages.gardenPlan.io.import.confirmNameMismatch')
                : t('pages.gardenPlan.io.import.confirmNameHelp')
            }
            slotProps={{ htmlInput: { 'data-testid': 'plan-snapshots-confirm-name', maxLength: 200 } }}
          />
        </Box>
      )}
      {chosen !== null && current === null && !busy && failure === null && checked !== null && (
        <Alert severity="info">{t('pages.gardenPlan.io.import.recheckHint')}</Alert>
      )}

      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        <Button onClick={onBack} disabled={busy} sx={{ minHeight: 44 }} data-testid="plan-snapshots-back">
          {t('common.back')}
        </Button>
        <Button
          variant="contained"
          color="error"
          onClick={() => void restore()}
          disabled={!canRestore || busy}
          sx={{ minHeight: 44 }}
          data-testid="plan-snapshots-restore"
        >
          {t(`${PREFIX}.restore`)}
        </Button>
      </Box>
    </Box>
  );
}
