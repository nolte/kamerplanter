import { useId } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import SettingsIcon from '@mui/icons-material/Settings';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

import { useModuleVisibility } from '@/hooks/useModuleVisibility';

/**
 * REQ-042 — deep-link guard. Direct URL access to a route of a hidden module
 * does not 404; it renders a reactivation hint instead, so shared/saved links
 * stay usable. Core and unowned paths pass straight through.
 */
export default function ModuleGuard({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { isPathVisible } = useModuleVisibility();
  const descId = useId();

  if (isPathVisible(location.pathname)) {
    return <>{children}</>;
  }

  return (
    <Box
      role="main"
      data-testid="module-guard-hint"
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: { xs: 'flex-start', sm: 'center' },
        minHeight: { xs: 'auto', sm: '60vh' },
        px: 2,
        pt: { xs: 4, sm: 0 },
      }}
    >
      <Card
        variant="outlined"
        sx={{ maxWidth: { xs: '100%', sm: 480 }, width: '100%' }}
        aria-labelledby="module-guard-title"
        aria-describedby={descId}
      >
        <CardContent
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            gap: 2,
            py: { xs: 4, sm: 5 },
            px: { xs: 2, sm: 4 },
          }}
        >
          {/* Decorative icon */}
          <VisibilityOffIcon
            sx={{ fontSize: { xs: 48, sm: 56 }, color: 'text.disabled' }}
            aria-hidden="true"
          />

          {/* Heading */}
          <Typography variant="h6" component="h1" id="module-guard-title">
            {t('modules.guard.title')}
          </Typography>

          {/* Explanatory text */}
          <Typography id={descId} variant="body2" color="text.secondary" sx={{ maxWidth: '36ch' }}>
            {t('modules.guard.description')}
          </Typography>

          {/* Data-safety reassurance */}
          <Alert
            severity="info"
            icon={<InfoOutlinedIcon fontSize="small" />}
            sx={{ textAlign: 'left', width: '100%' }}
          >
            <Typography variant="body2">{t('modules.guard.dataSafeNote')}</Typography>
          </Alert>

          {/* Primary CTA */}
          <Button
            variant="contained"
            size="large"
            startIcon={<SettingsIcon />}
            onClick={() => navigate('/settings#modules')}
            data-testid="module-guard-action"
            // Minimum 48px touch target (size="large" = 42px default; py override)
            sx={{ minHeight: 48, px: 3 }}
          >
            {t('modules.guard.action')}
          </Button>

          {/* Secondary: go back */}
          <Button
            variant="text"
            size="small"
            onClick={() => navigate(-1)}
            data-testid="module-guard-back"
            sx={{ color: 'text.secondary' }}
          >
            {t('modules.guard.goBack')}
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
}
