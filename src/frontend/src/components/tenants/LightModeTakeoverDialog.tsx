import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import * as systemApi from '@/api/endpoints/system';
import type { TakeoverResourceCounts, TakeoverStatus } from '@/api/types';
import StepUpConfirmDialog from '@/components/common/StepUpConfirmDialog';
import type { StepUpConfirmation } from '@/components/common/StepUpConfirmDialog';
import { isLightMode } from '@/config/mode';
import { useStepUpResume } from '@/hooks/useStepUpReauth';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchProfile } from '@/store/slices/authSlice';
import { loadMyTenants, switchTenant } from '@/store/slices/tenantSlice';
import { toCredentialStepUpBody } from '@/utils/stepUp';

/** The counts the dialog lists, in this order; a zero count is left out. */
const COUNT_FIELDS: readonly (keyof TakeoverResourceCounts)[] = [
  'plants',
  'sites',
  'planting_runs',
  'nutrient_plans',
  'tasks',
];

/** The surface id the step-up dialog saves before a fresh sign-in at the identity provider. */
const STEP_UP_SURFACE = 'light-mode-takeover-step-up';

type Decision = 'accept' | 'decline';

/**
 * The guided take-over of a former light-mode installation's data (REQ-027 Szenario 5/6, #1855).
 *
 * After the switch from light to full mode the backend keeps the light-mode garden and opens a
 * take-over. The platform administrator — on an instance without one, the first account registered
 * after the switch — is asked once per session whether the garden becomes theirs. Either decision is
 * confirmed with the account's own step-up (`light_mode_takeover`, bound to the garden's key):
 * accepting makes them its lead (the data stay where they are) and switches to it; declining keeps it
 * for the admin area. "Decide later" only closes the dialog for this session; the take-over stays open.
 *
 * Renders nothing in light mode, before the profile is loaded and for an account that may not decide.
 */
export default function LightModeTakeoverDialog() {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const dispatch = useAppDispatch();
  const userKey = useAppSelector((s) => s.auth.user?.key ?? null);
  const [status, setStatus] = useState<TakeoverStatus | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [decision, setDecision] = useState<Decision | null>(null);
  // #1815 — back from a fresh sign-in at the identity provider: the chosen decision does not survive
  // the round trip, so the resume context is only consumed; the pending token is picked up when the
  // account confirms the same decision again within its five minutes (bound to the garden's key).
  useStepUpResume(STEP_UP_SURFACE);

  useEffect(() => {
    if (isLightMode || !userKey) return;
    let cancelled = false;
    systemApi
      .getTakeoverStatus()
      .then((result) => {
        if (!cancelled) setStatus(result);
      })
      .catch(() => {
        // The probe is a convenience: an older backend or a failed request shows no dialog.
        if (!cancelled) setStatus(null);
      });
    return () => {
      cancelled = true;
    };
  }, [userKey]);

  const open = Boolean(status?.pending && status.eligible) && !dismissed;
  if (!open || !status) return null;

  const counts = status.resource_counts;
  const listed = counts ? COUNT_FIELDS.filter((field) => counts[field] > 0) : [];

  // The account's OWN step-up; a rejection propagates to the step-up dialog, which shows it and stays open.
  const confirmDecision = async (credentials: StepUpConfirmation) => {
    if (!decision) return;
    const result = await systemApi.decideTakeover(decision === 'accept', toCredentialStepUpBody(credentials));
    await dispatch(fetchProfile());
    if (result.accepted && result.tenant_slug) {
      await dispatch(loadMyTenants());
      dispatch(switchTenant(result.tenant_slug));
    }
    setDecision(null);
    setStatus(null);
  };

  if (decision) {
    return (
      <StepUpConfirmDialog
        open
        title={t(`components.lightModeTakeover.confirm.${decision}.title`)}
        description={t(`components.lightModeTakeover.confirm.${decision}.description`, {
          name: status.tenant_name ?? '',
        })}
        confirmLabel={t(`components.lightModeTakeover.confirm.${decision}.label`)}
        confirmColor="primary"
        testIdPrefix={STEP_UP_SURFACE}
        stepUpAction="light_mode_takeover"
        stepUpTarget={status.tenant_key ?? undefined}
        onConfirm={confirmDecision}
        onCancel={() => setDecision(null)}
      />
    );
  }

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={() => setDismissed(true)}
      maxWidth="sm"
      fullWidth
      aria-labelledby="light-mode-takeover-title"
      aria-describedby="light-mode-takeover-description"
      data-testid="light-mode-takeover-dialog"
    >
      <DialogTitle id="light-mode-takeover-title">{t('components.lightModeTakeover.title')}</DialogTitle>
      <DialogContent>
        <DialogContentText id="light-mode-takeover-description" sx={{ mb: 1 }}>
          {t('components.lightModeTakeover.intro', { name: status.tenant_name ?? '' })}
        </DialogContentText>
        {listed.length > 0 && counts && (
          <List dense data-testid="light-mode-takeover-counts">
            {listed.map((field) => (
              <ListItem key={field} disableGutters data-testid={`light-mode-takeover-count-${field}`}>
                <ListItemText primary={t(`components.lightModeTakeover.counts.${field}`, { count: counts[field] })} />
              </ListItem>
            ))}
          </List>
        )}
        <DialogContentText sx={{ mt: 1 }}>{t('components.lightModeTakeover.acceptExplanation')}</DialogContentText>
        <DialogContentText sx={{ mt: 1 }}>{t('components.lightModeTakeover.declineExplanation')}</DialogContentText>
      </DialogContent>
      <DialogActions sx={{ flexWrap: 'wrap', gap: 1 }}>
        <Button onClick={() => setDismissed(true)} data-testid="light-mode-takeover-later">
          {t('components.lightModeTakeover.later')}
        </Button>
        <Button onClick={() => setDecision('decline')} data-testid="light-mode-takeover-decline">
          {t('components.lightModeTakeover.decline')}
        </Button>
        <Button
          variant="contained"
          onClick={() => setDecision('accept')}
          autoFocus
          data-testid="light-mode-takeover-accept"
        >
          {t('components.lightModeTakeover.accept')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
