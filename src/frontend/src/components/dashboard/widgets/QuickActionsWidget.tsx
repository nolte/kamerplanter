import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardActionArea from '@mui/material/CardActionArea';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import ParkIcon from '@mui/icons-material/Park';
import ScienceIcon from '@mui/icons-material/Science';
import PlaceIcon from '@mui/icons-material/Place';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import CalculateIcon from '@mui/icons-material/Calculate';
import LayersIcon from '@mui/icons-material/Layers';
import { useModuleVisibility } from '@/hooks/useModuleVisibility';

/**
 * REQ-045 — the former hardcoded DashboardPage quick-action tiles, now a
 * catalog widget (`quick_actions`). Still respects REQ-042 module visibility
 * per action path.
 */
export default function QuickActionsWidget() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { isPathVisible } = useModuleVisibility();

  const quickActions = [
    { label: t('nav.botanicalFamilies'), path: '/stammdaten/botanical-families', icon: <ParkIcon sx={{ fontSize: 40 }} /> },
    { label: t('nav.species'), path: '/stammdaten/species', icon: <ScienceIcon sx={{ fontSize: 40 }} /> },
    { label: t('nav.sites'), path: '/standorte/sites', icon: <PlaceIcon sx={{ fontSize: 40 }} /> },
    { label: t('nav.substrates'), path: '/standorte/substrates', icon: <LayersIcon sx={{ fontSize: 40 }} /> },
    { label: t('nav.plantInstances'), path: '/pflanzen/plant-instances', icon: <LocalFloristIcon sx={{ fontSize: 40 }} /> },
    { label: t('nav.calculations'), path: '/pflanzen/calculations', icon: <CalculateIcon sx={{ fontSize: 40 }} /> },
  ];

  const visible = quickActions.filter((a) => isPathVisible(a.path));

  return (
    <Card sx={{ height: '100%' }} data-testid="widget-quick_actions">
      <CardContent>
        <Typography variant="subtitle1" component="h3" sx={{ mb: 2 }}>
          {t('dashboard.widgets.quick_actions.label')}
        </Typography>
        <Grid container spacing={2}>
          {visible.map((action) => (
            <Grid size={{ xs: 6, sm: 4, md: 2 }} key={action.path}>
              <Card variant="outlined" data-testid={`quick-action-${action.path}`}>
                <CardActionArea onClick={() => navigate(action.path)} sx={{ minHeight: 48 }}>
                  <CardContent sx={{ textAlign: 'center', py: 2 }}>
                    <Box sx={{ color: 'primary.main', mb: 1 }}>{action.icon}</Box>
                    <Typography variant="body2">{action.label}</Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
}
