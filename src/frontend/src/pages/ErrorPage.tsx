import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import ErrorIllustration from '@/components/common/ErrorIllustration';
import PageTitle from '@/components/layout/PageTitle';

export interface ErrorPageProps {
  statusCode?: number;
  onRetry?: () => void;
  /**
   * Whether this page owns the `main` landmark. Default `true`, which is right for
   * a whole-page route that replaces the layout.
   *
   * Pass `false` when rendering INSIDE a layout that already provides one —
   * `MainLayout` renders `component="main"`, so a nested `role="main"` produces
   * two `main` landmarks and an axe `landmark-unique` finding on the nightly a11y
   * lane. #1390 renders this component inside that layout on two admin routes.
   */
  landmark?: boolean;
}

export default function ErrorPage({ statusCode = 500, onRetry, landmark = true }: ErrorPageProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const title = t(`pages.error.${statusCode}.title`, t('pages.error.fallback.title'));
  const message = t(`pages.error.${statusCode}.message`, t('pages.error.fallback.message'));

  const canGoBack = window.history.length > 1;

  return (
    <Box
      sx={{ textAlign: 'center', py: { xs: 4, md: 8 }, px: 2 }}
      data-testid="error-page"
      role={landmark ? 'main' : undefined}
    >
      <PageTitle title={title} />

      <ErrorIllustration statusCode={statusCode} sx={{ mx: 'auto', display: 'block' }} />

      <Typography
        variant="h1"
        component="p"
        sx={{
          fontSize: { xs: '3.5rem', md: '5rem' },
          fontWeight: 700,
          color: 'text.secondary',
          mb: 1,
        }}
        // Decorative: the PageTitle h1 above already names the error.
        aria-hidden="true"
      >
        {statusCode}
      </Typography>

      <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
        {title}
      </Typography>

      <Typography
        variant="body1"
        color="text.secondary"
        sx={{ mb: 4, maxWidth: 480, mx: 'auto' }}
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
        {onRetry && (
          <Button
            variant="outlined"
            onClick={onRetry}
            data-testid="error-retry"
          >
            {t('common.retry')}
          </Button>
        )}
      </Stack>
    </Box>
  );
}
