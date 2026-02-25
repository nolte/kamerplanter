import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardActionArea from '@mui/material/CardActionArea';
import Typography from '@mui/material/Typography';
import Grid from '@mui/material/Grid';
import ParkIcon from '@mui/icons-material/Park';
import ScienceIcon from '@mui/icons-material/Science';
import PlaceIcon from '@mui/icons-material/Place';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import CalculateIcon from '@mui/icons-material/Calculate';
import LayersIcon from '@mui/icons-material/Layers';
import PageTitle from '@/components/layout/PageTitle';

export default function DashboardPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const quickActions = [
    { label: t('nav.botanicalFamilies'), path: '/stammdaten/botanical-families', icon: <ParkIcon sx={{ fontSize: 40 }} /> },
    { label: t('nav.species'), path: '/stammdaten/species', icon: <ScienceIcon sx={{ fontSize: 40 }} /> },
    { label: t('nav.sites'), path: '/standorte/sites', icon: <PlaceIcon sx={{ fontSize: 40 }} /> },
    { label: t('nav.substrates'), path: '/standorte/substrates', icon: <LayersIcon sx={{ fontSize: 40 }} /> },
    { label: t('nav.plantInstances'), path: '/pflanzen/plant-instances', icon: <LocalFloristIcon sx={{ fontSize: 40 }} /> },
    { label: t('nav.calculations'), path: '/pflanzen/calculations', icon: <CalculateIcon sx={{ fontSize: 40 }} /> },
  ];

  return (
    <Box data-testid="dashboard-page">
      <PageTitle title={t('pages.dashboard.title')} />
      <Typography variant="h5" sx={{ mb: 4 }} data-testid="dashboard-welcome">
        {t('pages.dashboard.welcome')}
      </Typography>

      <Typography variant="h6" sx={{ mb: 2 }}>
        {t('pages.dashboard.quickActions')}
      </Typography>
      <Grid container spacing={2}>
        {quickActions.map((action) => (
          <Grid size={{ xs: 6, sm: 4, md: 3 }} key={action.path}>
            <Card data-testid={`quick-action-${action.path}`}>
              <CardActionArea onClick={() => navigate(action.path)}>
                <CardContent sx={{ textAlign: 'center', py: 3 }}>
                  <Box sx={{ color: 'primary.main', mb: 1 }}>{action.icon}</Box>
                  <Typography variant="body2">{action.label}</Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
