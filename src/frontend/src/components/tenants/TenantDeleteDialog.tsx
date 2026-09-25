import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import { listProviders } from '@/api/endpoints/auth';
import { isApiError, parseApiError } from '@/api/errors';
import type { TenantDeleteRequest } from '@/api/types';

interface TenantDeleteDialogProps {
  open: boolean;
  tenantName: string;
  tenantSlug: string;
  /** Runs the deletion with the step-up; a rejection is shown inside the dialog. */
  onConfirm: (stepUp: TenantDeleteRequest) => Promise<void>;
  onCancel: () => void;
}

/**
 * Confirms the irreversible erasure of a whole tenant with a step-up (#1791).
 *
 * The backend refuses a tenant deletion unless the body echoes the tenant's slug
 * (422) and, for an account with a local password, carries the current password
 * (401). The password field **fails closed**: it is shown unless the provider
 * list positively says the account is federated-only — a failed or pending load
 * must not hide it, or a local account would meet a 401 it has no field to
 * answer (the #394 dead end). An **empty** list counts as unknown too: seeded
 * accounts carry a password hash without a `local` provider row (#1791 review
 * SEC-003). And once the server answered 401, the field stays, whatever the
 * list said — the backend decides on the stored hash, not on the list. A
 * password sent for a federated account is ignored by the backend.
 */
export default function TenantDeleteDialog({
  open,
  tenantName,
  tenantSlug,
  onConfirm,
  onCancel,
}: TenantDeleteDialogProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const [slugEcho, setSlugEcho] = useState('');
  const [password, setPassword] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  // Tri-state: `null` = unknown (loading or failed) → fail closed.
  const [hasLocalPassword, setHasLocalPassword] = useState<boolean | null>(null);
  const [serverAskedForPassword, setServerAskedForPassword] = useState(false);
  const requiresPassword = hasLocalPassword !== false || serverAskedForPassword;

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    listProviders()
      .then((list) => {
        if (cancelled) return;
        // Only a non-empty list without `local` is positive proof of a
        // federated-only account; an empty one stays unknown (fail closed).
        setHasLocalPassword(list.length === 0 ? null : list.some((p) => p.provider === 'local'));
      })
      .catch(() => {
        if (!cancelled) setHasLocalPassword(null);
      });
    return () => {
      cancelled = true;
    };
  }, [open]);

  const slugMatches = slugEcho.trim() === tenantSlug;
  const canConfirm = slugMatches && (!requiresPassword || password.length > 0) && !pending;

  const reset = () => {
    setSlugEcho('');
    setPassword('');
    setError('');
  };

  const handleCancel = () => {
    if (pending) return;
    reset();
    onCancel();
  };

  const handleConfirm = async () => {
    if (!canConfirm) return;
    setPending(true);
    setError('');
    try {
      await onConfirm(
        requiresPassword ? { confirm_slug: slugEcho.trim(), password } : { confirm_slug: slugEcho.trim() },
      );
      reset();
    } catch (err) {
      // Stay open so the requester can correct the slug or the password.
      setError(parseApiError(err));
      setPassword('');
      if (isApiError(err) && err.statusCode === 401) setServerAskedForPassword(true);
    } finally {
      setPending(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={pending ? undefined : handleCancel}
      fullScreen={fullScreen}
      maxWidth="sm"
      fullWidth
      role="alertdialog"
      aria-labelledby="tenant-delete-dialog-title"
      aria-describedby="tenant-delete-dialog-description"
      data-testid="tenant-delete-dialog"
    >
      <DialogTitle id="tenant-delete-dialog-title">{t('pages.auth.tenantDeleteDialogTitle')}</DialogTitle>
      <DialogContent>
        <DialogContentText id="tenant-delete-dialog-description" sx={{ whiteSpace: 'pre-line' }}>
          {t('pages.auth.adminDeleteTenantConfirm', { name: tenantName })}
        </DialogContentText>
        <TextField
          label={t('pages.auth.tenantDeleteSlugLabel')}
          helperText={t('pages.auth.tenantDeleteSlugHelper', { slug: tenantSlug })}
          value={slugEcho}
          onChange={(e) => setSlugEcho(e.target.value)}
          autoComplete="off"
          fullWidth
          required
          autoFocus
          disabled={pending}
          error={slugEcho.length > 0 && !slugMatches}
          sx={{ mt: 2 }}
          slotProps={{ htmlInput: { spellCheck: false, autoCapitalize: 'none' } }}
          data-testid="tenant-delete-slug"
        />
        {requiresPassword && (
          <TextField
            type="password"
            label={t('pages.auth.tenantDeletePasswordLabel')}
            helperText={t('pages.auth.tenantDeletePasswordHelper')}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleConfirm();
            }}
            autoComplete="current-password"
            fullWidth
            required
            disabled={pending}
            sx={{ mt: 2 }}
            data-testid="tenant-delete-password"
          />
        )}
        {error && (
          <Alert severity="error" sx={{ mt: 2 }} data-testid="tenant-delete-error">
            {error}
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCancel} disabled={pending} data-testid="tenant-delete-cancel">
          {t('common.cancel')}
        </Button>
        <Button
          onClick={handleConfirm}
          color="error"
          variant="contained"
          disabled={!canConfirm}
          loading={pending}
          aria-busy={pending}
          data-testid="tenant-delete-confirm"
        >
          {t('pages.auth.adminConfirmDelete')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
