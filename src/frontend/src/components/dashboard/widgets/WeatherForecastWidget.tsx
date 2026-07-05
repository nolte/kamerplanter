import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import CloudIcon from '@mui/icons-material/Cloud';

/**
 * REQ-046 §4.2 — dashboard weather widget.
 *
 * The daily-values read endpoint (`:WeatherForecast` list per site) is not part
 * of the REQ-046 backend surface yet — the fetch task writes records, but no
 * tenant-scoped read route exists. Rather than invent one, this widget renders
 * a configuration-oriented empty state that points growers at the per-site
 * "Wetterquelle" configurator. Once a forecast read endpoint lands, the daily
 * rows + source / `data_kind` badge (AC-10) and the "fallback active" hint slot
 * straight into this shell (see {@link WeatherProvenanceBadge}).
 */
export default function WeatherForecastWidget() {
  const { t } = useTranslation();

  return (
    <Card sx={{ height: '100%' }} data-testid="widget-weather_forecast">
      <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Typography variant="subtitle1" component="h3" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
          <CloudIcon fontSize="small" color="primary" />
          {t('dashboard.widgets.weather_forecast.label')}
        </Typography>
        <Box
          sx={{
            flexGrow: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            gap: 1.5,
            color: 'text.secondary',
          }}
        >
          <Typography variant="body2">
            {t('dashboard.widgets.weather_forecast.emptyHint')}
          </Typography>
          <Button
            component={RouterLink}
            to="/standorte/sites"
            size="small"
            variant="outlined"
            data-testid="weather-widget-configure"
          >
            {t('dashboard.widgets.weather_forecast.configureCta')}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
}
