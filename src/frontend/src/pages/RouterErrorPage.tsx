import { useRouteError, isRouteErrorResponse, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import ErrorIllustration from '@/components/common/ErrorIllustration';

interface RouterErrorPageProps {
  /**
   * Rendered inside the main layout's outlet (#3014): the shell already owns the
   * `main` landmark and the viewport, so the page neither repeats the landmark
   * nor stretches to full height.
   */
  embedded?: boolean;
}

export default function RouterErrorPage({ embedded = false }: RouterErrorPageProps) {
  const error = useRouteError();
  const { t } = useTranslation();
  const navigate = useNavigate();

  let statusCode = 500;
  if (isRouteErrorResponse(error)) {
    statusCode = error.status;
  }

  const title = t(`pages.error.${statusCode}.title`, t('pages.error.fallback.title'));
  const message = t(`pages.error.${statusCode}.message`, t('pages.error.fallback.message'));

  const canGoBack = window.history.length > 1;

  return (
    <Box
      sx={{
        textAlign: 'center',
        py: { xs: 4, md: 8 },
        px: 2,
        minHeight: embedded ? undefined : '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      data-testid="router-error-page"
      role={embedded ? undefined : 'main'}
    >
      <ErrorIllustration statusCode={statusCode} />

      <Typography
        variant="h1"
        sx={{
          fontSize: { xs: '3.5rem', md: '5rem' },
          fontWeight: 700,
          color: 'text.secondary',
          mb: 1,
        }}
        aria-label={t(`pages.error.${statusCode}.title`, t('pages.error.fallback.title'))}
      >
        {statusCode}
      </Typography>

      <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
        {title}
      </Typography>

      <Typography
        variant="body1"
        color="text.secondary"
        sx={{ mb: 4, maxWidth: 480 }}
      >
        {message}
      </Typography>

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ justifyContent: 'center' }}>
        <Button
          variant="contained"
          onClick={() => navigate('/dashboard')}
          data-testid="error-go-home"
        >
          {t('pages.error.backHome')}
        </Button>
        {canGoBack && (
          <Button
            variant="outlined"
            onClick={() => navigate(-1)}
            data-testid="error-go-back"
          >
            {t('common.back')}
          </Button>
        )}
        <Button
          variant="outlined"
          onClick={() => window.location.reload()}
          data-testid="error-reload"
        >
          {t('common.retry')}
        </Button>
      </Stack>
    </Box>
  );
}
