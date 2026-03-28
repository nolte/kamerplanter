import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import { useTranslation } from 'react-i18next';
import { useAppDispatch } from '@/store/hooks';
import { setAccessToken, fetchProfile } from '@/store/slices/authSlice';

export default function OAuthCallbackPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState<string | null>(() => {
    const errorParam = searchParams.get('error');
    if (errorParam) return errorParam;
    if (!searchParams.get('access_token')) return t('pages.auth.oauthNoToken');
    return null;
  });

  useEffect(() => {
    const accessToken = searchParams.get('access_token');
    if (!accessToken || searchParams.get('error')) return;

    // Store the access token and fetch user profile
    dispatch(setAccessToken(accessToken));
    dispatch(fetchProfile())
      .unwrap()
      .then(() => {
        navigate('/dashboard', { replace: true });
      })
      .catch(() => {
        setError(t('pages.auth.oauthProfileError'));
      });
  }, [searchParams, dispatch, navigate, t]);

  if (error) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
        <Alert severity="error" sx={{ maxWidth: 400 }}>
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
      <CircularProgress sx={{ mb: 2 }} />
      <Typography>{t('pages.auth.oauthProcessing')}</Typography>
    </Box>
  );
}
