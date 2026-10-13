import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import Button from '@mui/material/Button';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import GroupAddIcon from '@mui/icons-material/GroupAdd';
import * as tenantApi from '@/api/endpoints/tenants';
import { isApiError, parseApiError } from '@/api/errors';
import { useAppSelector } from '@/store/hooks';
import { forgetPendingInvitation } from '@/utils/pendingInvitation';

/** The backend's `error_code` for a tenant whose member limit is reached (#2133). */
const MEMBER_LIMIT_REACHED = 'MEMBER_LIMIT_REACHED';

type Status = 'confirm' | 'loading' | 'success' | 'error';

export default function InvitationAcceptPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = params.get('token');
  // #2162 review W3 — the dashboard only helps someone who is a member somewhere.
  const hasMembership = useAppSelector((s) => s.tenants.myTenants.length > 0);

  // #2162 review S-2 — the invitation is accepted on an explicit click, never on page load: the token
  // may have been remembered across a sign-in, and the account now signed in must choose to join.
  const [status, setStatus] = useState<Status>(() => (token ? 'confirm' : 'error'));
  const [error, setError] = useState<string | null>(() => (token ? null : t('pages.auth.invalidToken')));
  // A full tenant keeps the invitation valid (#2133): only every other refusal needs a new one.
  const [needsNewInvitation, setNeedsNewInvitation] = useState(true);

  useEffect(() => {
    // #2162 — the token remembered across the sign-in has arrived; a later sign-in goes to the dashboard.
    if (token) forgetPendingInvitation();
  }, [token]);

  const handleAccept = () => {
    if (!token) return;
    setStatus('loading');
    tenantApi
      .acceptInvitation(token)
      .then(() => setStatus('success'))
      .catch((err) => {
        const full = isApiError(err) && err.errorCode === MEMBER_LIMIT_REACHED;
        setStatus('error');
        setNeedsNewInvitation(!full);
        // A full tenant is not a broken link: the invitation stays open, so the
        // invitee is told why and that it can work later (#2133). Every other
        // refusal keeps the backend's own message.
        setError(full ? t('pages.tenants.memberLimitReached') : parseApiError(err));
      });
  };

  return (
    <Box sx={{ maxWidth: 500, mx: 'auto', mt: 8, px: 2 }} data-testid="invitation-accept-page">
      <Card>
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
          {status === 'confirm' && (
            <>
              <GroupAddIcon color="primary" sx={{ fontSize: 48, mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                {t('pages.tenants.invitationConfirmTitle')}
              </Typography>
              <Typography color="text.secondary">{t('pages.tenants.invitationConfirmHint')}</Typography>
              <Button
                variant="contained"
                onClick={handleAccept}
                sx={{ mt: 2, minHeight: 44 }}
                data-testid="invitation-accept-btn"
              >
                {t('pages.tenants.invitationAccept')}
              </Button>
            </>
          )}
          {status === 'loading' && (
            <>
              <CircularProgress sx={{ mb: 2 }} />
              <Typography>{t('common.loading')}</Typography>
            </>
          )}
          {status === 'success' && (
            <>
              <CheckCircleIcon color="success" sx={{ fontSize: 48, mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                {t('pages.tenants.invitationAccepted')}
              </Typography>
              <Button variant="contained" onClick={() => navigate('/dashboard')} sx={{ mt: 2, minHeight: 44 }}>
                {t('nav.dashboard')}
              </Button>
            </>
          )}
          {status === 'error' && (
            <>
              <ErrorIcon color="error" sx={{ fontSize: 48, mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                {t('pages.tenants.invitationFailed')}
              </Typography>
              <Typography color="text.secondary" role="alert" data-testid="invitation-error-detail">
                {error}
              </Typography>
              {needsNewInvitation && (
                <Typography color="text.secondary" sx={{ mt: 1 }} data-testid="invitation-error-next-step">
                  {t('pages.tenants.invitationAskForNew')}
                </Typography>
              )}
              {hasMembership && (
                <Button variant="outlined" onClick={() => navigate('/dashboard')} sx={{ mt: 2, minHeight: 44 }}>
                  {t('nav.dashboard')}
                </Button>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
