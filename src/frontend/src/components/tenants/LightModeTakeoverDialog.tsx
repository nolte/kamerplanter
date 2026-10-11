import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import * as systemApi from '@/api/endpoints/system';
import { parseApiError } from '@/api/errors';
import type { TakeoverResourceCounts, TakeoverStatus } from '@/api/types';
import { isLightMode } from '@/config/mode';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchProfile } from '@/store/slices/authSlice';
import { loadMyTenants, switchTenant } from '@/store/slices/tenantSlice';

/** The counts the dialog lists, in this order; a zero count is left out. */
const COUNT_FIELDS: readonly (keyof TakeoverResourceCounts)[] = [
  'plants',
  'sites',
  'planting_runs',
  'nutrient_plans',
  'tasks',
];

type Decision = 'accept' | 'decline';

/**
 * The guided take-over of a former light-mode installation's data (REQ-027 Szenario 5/6, #1855).
 *
 * After the switch from light to full mode the backend keeps the light-mode garden and opens a
 * take-over. The platform administrator — on an instance without one, the first account — is asked
 * once per session whether the garden becomes theirs. Accepting makes them its lead (the data stay
 * where they are) and switches to it; declining keeps it for the admin area. "Decide later" only
 * closes the dialog for this session; the take-over stays open.
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
  const [pending, setPending] = useState<Decision | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  const decide = async (decision: Decision) => {
    setPending(decision);
    setError(null);
    try {
      const result = await systemApi.decideTakeover(decision === 'accept');
      await dispatch(fetchProfile());
      if (result.accepted && result.tenant_slug) {
        await dispatch(loadMyTenants());
        dispatch(switchTenant(result.tenant_slug));
      }
      setStatus(null);
    } catch (err) {
      setError(parseApiError(err));
    } finally {
      setPending(null);
    }
  };

  const busy = pending !== null;

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={busy ? undefined : () => setDismissed(true)}
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
        {error && (
          <Alert severity="error" sx={{ mt: 2 }} data-testid="light-mode-takeover-error">
            {error}
          </Alert>
        )}
      </DialogContent>
      <DialogActions sx={{ flexWrap: 'wrap', gap: 1 }}>
        <Button onClick={() => setDismissed(true)} disabled={busy} data-testid="light-mode-takeover-later">
          {t('components.lightModeTakeover.later')}
        </Button>
        <Button
          onClick={() => void decide('decline')}
          disabled={busy && pending !== 'decline'}
          loading={pending === 'decline'}
          data-testid="light-mode-takeover-decline"
        >
          {t('components.lightModeTakeover.decline')}
        </Button>
        <Button
          variant="contained"
          onClick={() => void decide('accept')}
          disabled={busy && pending !== 'accept'}
          loading={pending === 'accept'}
          autoFocus
          data-testid="light-mode-takeover-accept"
        >
          {t('components.lightModeTakeover.accept')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
