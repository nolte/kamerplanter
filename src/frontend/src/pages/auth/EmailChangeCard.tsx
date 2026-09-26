import { useState } from 'react';
import type { FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { z } from 'zod';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import { requestEmailChange } from '@/api/endpoints/privacy';
import { isApiError } from '@/api/errors';
import StepUpConfirmDialog from '@/components/common/StepUpConfirmDialog';
import type { StepUpConfirmation } from '@/components/common/StepUpConfirmDialog';
import { useStepUpResume } from '@/hooks/useStepUpReauth';
import { toStepUpBody } from '@/utils/stepUp';

/** The step-up surface id — the dialog's test-id prefix and the resume key after a fresh sign-in. */
export const EMAIL_CHANGE_SURFACE = 'email-change';

/**
 * The address being confirmed, kept across the round trip to the identity
 * provider (#1815): the browser leaves the app, and without it the reopened
 * dialog would not know which address to send. sessionStorage only — tab
 * scoped, gone with the tab — and removed on success or cancel.
 */
export const EMAIL_CHANGE_ADDRESS_KEY = 'kp.emailChange.address';

const emailSchema = z.email();

function readStoredAddress(): string | null {
  try {
    const value = sessionStorage.getItem(EMAIL_CHANGE_ADDRESS_KEY);
    return value && emailSchema.safeParse(value).success ? value : null;
  } catch {
    return null;
  }
}

function storeAddress(address: string): void {
  try {
    sessionStorage.setItem(EMAIL_CHANGE_ADDRESS_KEY, address);
  } catch {
    // Storage unavailable: only the fresh-sign-in resume is lost; password and code still work.
  }
}

function clearStoredAddress(): void {
  try {
    sessionStorage.removeItem(EMAIL_CHANGE_ADDRESS_KEY);
  } catch {
    // Nothing stored that could be removed.
  }
}

interface EmailChangeCardProps {
  /** The account's current sign-in address. */
  currentEmail: string;
}

/**
 * Requests a change of the sign-in address (REQ-025 Art. 16, #1841, #1848).
 *
 * The request is a step-up act (`email_change`, REQ-023 §3.9) without an echo:
 * submitting the new address opens `StepUpConfirmDialog`, which asks for the
 * current password, the e-mailed code or a fresh sign-in at the identity
 * provider — whichever the account needs. Nothing changes yet on success: the
 * backend mails a confirmation link to the new address and tells the current
 * one, and the card says so.
 *
 * After a fresh sign-in the browser comes back to this page; the dialog reopens
 * with the address kept in sessionStorage and sends the pending token.
 */
export default function EmailChangeCard({ currentEmail }: EmailChangeCardProps) {
  const { t } = useTranslation();
  const resume = useStepUpResume(EMAIL_CHANGE_SURFACE);
  const [resumedAddress] = useState<string | null>(() => (resume ? readStoredAddress() : null));
  const [newEmail, setNewEmail] = useState(resumedAddress ?? '');
  const [targetEmail, setTargetEmail] = useState(resumedAddress ?? '');
  const [dialogOpen, setDialogOpen] = useState(resumedAddress !== null);
  const [fieldError, setFieldError] = useState('');
  const [requestedAddress, setRequestedAddress] = useState<string | null>(null);

  const validate = (value: string): string => {
    if (!emailSchema.safeParse(value).success) return t('pages.emailChange.invalidEmail');
    if (currentEmail && value.toLowerCase() === currentEmail.trim().toLowerCase()) {
      return t('pages.emailChange.sameAsCurrent');
    }
    return '';
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = newEmail.trim();
    const error = validate(trimmed);
    setFieldError(error);
    if (error) return;
    setRequestedAddress(null);
    setTargetEmail(trimmed);
    storeAddress(trimmed);
    setDialogOpen(true);
  };

  const handleCancel = () => {
    clearStoredAddress();
    setDialogOpen(false);
  };

  const handleConfirm = async (confirmation: StepUpConfirmation) => {
    try {
      const result = await requestEmailChange({ new_email: targetEmail, ...toStepUpBody(confirmation) });
      clearStoredAddress();
      setDialogOpen(false);
      setNewEmail('');
      setFieldError('');
      setRequestedAddress(result.new_email);
    } catch (err) {
      // 422: the step-up passed, the address did not (the current one, a reserved
      // domain). That is the field's problem, not the dialog's — close it and say
      // so at the address; a retry needs a new confirmation anyway.
      if (isApiError(err) && err.statusCode === 422) {
        clearStoredAddress();
        setDialogOpen(false);
        setFieldError(t('pages.emailChange.addressRejected'));
        return;
      }
      // Every other refusal (401 step-up, 429 STEP_UP_LOCKED, …) is shown inside the dialog.
      throw err;
    }
  };

  return (
    <Card variant="outlined" data-testid="email-change-card">
      <CardContent
        component="form"
        noValidate
        onSubmit={handleSubmit}
        sx={{ '&:last-child': { pb: 2 }, px: 2, pt: 2 }}
      >
        <Typography component="h2" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
          {t('pages.emailChange.sectionTitle')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t('pages.emailChange.sectionDesc')}
        </Typography>
        {currentEmail && (
          <Typography variant="body2" sx={{ mb: 2, overflowWrap: 'anywhere' }}>
            {t('pages.emailChange.currentEmail', { email: currentEmail })}
          </Typography>
        )}
        {requestedAddress && (
          <Alert severity="success" sx={{ mb: 2, overflowWrap: 'anywhere' }} data-testid="email-change-pending">
            {t('pages.emailChange.pending', { email: requestedAddress })}
          </Alert>
        )}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            type="email"
            label={t('pages.emailChange.newEmailLabel')}
            helperText={fieldError || t('pages.emailChange.newEmailHelper')}
            error={fieldError.length > 0}
            value={newEmail}
            onChange={(e) => {
              setNewEmail(e.target.value);
              if (fieldError) setFieldError('');
            }}
            autoComplete="email"
            fullWidth
            required
            slotProps={{ htmlInput: { spellCheck: false, autoCapitalize: 'none', inputMode: 'email' } }}
            data-testid="email-change-new-email"
          />
          <Button
            type="submit"
            variant="contained"
            disabled={newEmail.trim().length === 0}
            sx={{ alignSelf: { xs: 'stretch', sm: 'flex-start' } }}
            data-testid="email-change-submit"
          >
            {t('pages.emailChange.submit')}
          </Button>
        </Box>
      </CardContent>

      <StepUpConfirmDialog
        open={dialogOpen}
        title={t('pages.emailChange.dialogTitle')}
        description={t('pages.emailChange.dialogDescription', { email: targetEmail })}
        confirmLabel={t('pages.emailChange.dialogConfirm')}
        confirmColor="primary"
        stepUpAction="email_change"
        testIdPrefix={EMAIL_CHANGE_SURFACE}
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
    </Card>
  );
}
