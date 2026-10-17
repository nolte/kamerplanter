/**
 * The 409 dialog (REQ-053 GP-UX-017, GP-ACC-011, UI-NFR-022): somebody else changed the structure
 * of the plan while this copy was open. The unsaved changes cannot be merged, so the only ways on
 * are to keep them as a JSON copy and to reload (which discards them and the undo stack). There is
 * no close button on purpose: the slice leaves the conflict state only through a reload.
 */
import { useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DownloadIcon from '@mui/icons-material/Download';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { loadGardenPlan, selectGardenPlanState } from '../state/gardenPlanSlice';
import { buildChangesFile, downloadChangesFile } from './downloadChanges';

const PREFIX = 'pages.gardenPlan.editor.conflict';
const TITLE_ID = 'garden-plan-conflict-title';
const BODY_ID = 'garden-plan-conflict-body';

function formatWhen(iso: string | null, language: string): string | null {
  if (iso === null) return null;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat(language, { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

export function ConflictDialog() {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  const { conflict, plan, pending } = useAppSelector(selectGardenPlanState);
  const [downloaded, setDownloaded] = useState(false);
  const fullScreen = useMediaQuery(useTheme().breakpoints.down('sm'));

  const download = useCallback(() => {
    if (conflict === null || plan === null) return;
    downloadChangesFile(
      buildChangesFile(
        plan.siteKey,
        plan.revision,
        conflict.currentRevision,
        pending.map((item) => item.op),
      ),
    );
    setDownloaded(true);
  }, [conflict, pending, plan]);

  const reload = useCallback(() => {
    if (plan !== null) void dispatch(loadGardenPlan(plan.siteKey));
  }, [dispatch, plan]);

  const changedAt = useMemo(
    () => formatWhen(conflict?.changedAt ?? null, i18n.language),
    [conflict?.changedAt, i18n.language],
  );

  if (conflict === null) return null;

  // The name is the display name of the last editor (§22.1), never an account key.
  const who =
    conflict.changedBy && changedAt
      ? t(`${PREFIX}.byAt`, { name: conflict.changedBy, when: changedAt })
      : conflict.changedBy
        ? t(`${PREFIX}.by`, { name: conflict.changedBy })
        : changedAt
          ? t(`${PREFIX}.at`, { when: changedAt })
          : null;

  return (
    <Dialog
      open
      role="alertdialog"
      aria-labelledby={TITLE_ID}
      aria-describedby={BODY_ID}
      onClose={() => undefined}
      fullWidth
      maxWidth="sm"
      // A phone gets the whole screen so the text and both buttons are never cut off (UI-NFR-008).
      fullScreen={fullScreen}
      data-testid="plan-conflict-dialog"
    >
      <DialogTitle id={TITLE_ID}>{t(`${PREFIX}.title`)}</DialogTitle>
      <DialogContent>
        <DialogContentText id={BODY_ID} component="div">
          <Typography variant="body1" sx={{ mb: 1 }}>
            {t(`${PREFIX}.message`, { count: pending.length })}
          </Typography>
          {who && (
            <Typography variant="body2" sx={{ mb: 1 }} data-testid="plan-conflict-who">
              {who}
            </Typography>
          )}
          <Typography variant="body2">{t(`${PREFIX}.advice`)}</Typography>
        </DialogContentText>
        {downloaded && (
          <Typography
            variant="body2"
            color="success.main"
            role="status"
            sx={{ mt: 1 }}
            data-testid="plan-conflict-downloaded"
          >
            {t(`${PREFIX}.downloaded`)}
          </Typography>
        )}
      </DialogContent>
      <DialogActions
        sx={{
          flexDirection: { xs: 'column', sm: 'row' },
          alignItems: { xs: 'stretch', sm: 'center' },
          flexWrap: 'wrap',
          gap: 1,
          px: 3,
          pb: 2,
          // MUI adds a left margin to every button but the first; stacked buttons need none.
          '& > :not(style) ~ :not(style)': { ml: { xs: 0, sm: 1 } },
        }}
      >
        <Button
          onClick={download}
          startIcon={<DownloadIcon />}
          sx={{ minHeight: 44 }}
          data-testid="plan-conflict-download"
        >
          {t(`${PREFIX}.download`)}
        </Button>
        <Button
          variant="contained"
          onClick={reload}
          autoFocus
          startIcon={<RefreshIcon />}
          sx={{ minHeight: 44 }}
          data-testid="plan-conflict-reload"
        >
          {t(`${PREFIX}.reload`)}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
