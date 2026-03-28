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
import * as tenantApi from '@/api/endpoints/tenants';
import { parseApiError } from '@/api/errors';

export default function InvitationAcceptPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = params.get('token');

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>(() => token ? 'loading' : 'error');
  const [error, setError] = useState<string | null>(() => token ? null : t('pages.auth.invalidToken'));

  useEffect(() => {
    if (!token) return;

    tenantApi
      .acceptInvitation(token)
      .then(() => setStatus('success'))
      .catch((err) => {
        setStatus('error');
        setError(parseApiError(err));
      });
  }, [token, t]);

  return (
    <Box sx={{ maxWidth: 500, mx: 'auto', mt: 8 }}>
      <Card>
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
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
              <Button variant="contained" onClick={() => navigate('/dashboard')} sx={{ mt: 2 }}>
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
              <Typography color="text.secondary">{error}</Typography>
              <Button variant="outlined" onClick={() => navigate('/dashboard')} sx={{ mt: 2 }}>
                {t('nav.dashboard')}
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
