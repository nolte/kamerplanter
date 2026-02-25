import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import PageTitle from '@/components/layout/PageTitle';

export default function NotFoundPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <Box sx={{ textAlign: 'center', py: 8 }} data-testid="not-found-page">
      <PageTitle title={t('pages.notFound.title')} />
      <Typography variant="h1" sx={{ fontSize: '6rem', fontWeight: 700, color: 'text.secondary', mb: 2 }}>
        404
      </Typography>
      <Typography variant="body1" sx={{ mb: 4 }}>
        {t('pages.notFound.message')}
      </Typography>
      <Button variant="contained" onClick={() => navigate('/dashboard')}>
        {t('pages.notFound.backHome')}
      </Button>
    </Box>
  );
}
