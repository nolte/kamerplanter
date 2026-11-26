import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import PhotoCameraIcon from '@mui/icons-material/PhotoCamera';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import ChecklistIcon from '@mui/icons-material/Checklist';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import AssignmentIcon from '@mui/icons-material/Assignment';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { useAppSelector } from '@/store/hooks';

interface QuickAction {
  key: string;
  labelKey: string;
  path: string;
  icon: React.ReactNode;
  color: string;
}

/**
 * UI-NFR-019 §2.3 — kiosk start page (R-014). Four large quick-action tiles
 * (R-015: identify plant — the spec's QR scan does not exist, see below — log
 * watering, start round, report problem) plus a
 * "Current status" summary (R-016). Tiles are far larger than the 80×80px
 * minimum so they are usable with gloves or the back of a hand.
 */
export default function KioskStartPage() {
  const { t } = useTranslation();

  const openTasks = useAppSelector((s) => s.tasks?.taskQueue?.length ?? 0);
  const overdueTasks = useAppSelector((s) => s.tasks?.overdueTasks?.length ?? 0);

  const actions = useMemo<QuickAction[]>(
    () => [
      // R-015 asks for "Pflanze scannen (QR)". The app has no QR scanner — the plant labels carry a
      // QR code that a phone's camera opens as a URL — and this tile leads to the photo-based
      // identification. It is named for what it does (#3025 N-38) until a scanner exists.
      {
        key: 'identify',
        labelKey: 'pages.kiosk.actions.identifyPlant',
        path: '/pflanzen/identifikation',
        icon: <PhotoCameraIcon sx={{ fontSize: 72 }} />,
        color: 'primary.main',
      },
      {
        key: 'watering',
        labelKey: 'pages.kiosk.actions.logWatering',
        path: '/giessprotokoll',
        icon: <WaterDropIcon sx={{ fontSize: 72 }} />,
        color: 'secondary.main',
      },
      {
        key: 'round',
        labelKey: 'pages.kiosk.actions.startRound',
        path: '/aufgaben/queue',
        icon: <ChecklistIcon sx={{ fontSize: 72 }} />,
        color: 'success.main',
      },
      {
        key: 'problem',
        labelKey: 'pages.kiosk.actions.reportProblem',
        path: '/pflanzenschutz/erkennung',
        icon: <ReportProblemIcon sx={{ fontSize: 72 }} />,
        color: 'error.main',
      },
    ],
    [],
  );

  return (
    <Box data-testid="kiosk-start-page">
      <Typography variant="h3" component="h1" sx={{ fontWeight: 700, mb: 4 }}>
        {t('pages.kiosk.startTitle')}
      </Typography>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' },
          gap: 3,
          mb: 4,
        }}
      >
        {actions.map((action) => (
          <Card key={action.key} sx={{ minHeight: 200 }}>
            <CardActionArea
              component={RouterLink}
              to={action.path}
              aria-label={t(action.labelKey)}
              data-testid={`kiosk-tile-${action.key}`}
              sx={{
                height: '100%',
                minHeight: 200,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 2,
                p: 3,
              }}
            >
              <Box sx={{ color: action.color }}>{action.icon}</Box>
              <Typography
                variant="h4"
                component="span"
                sx={{ fontWeight: 700, textAlign: 'center' }}
              >
                {t(action.labelKey)}
              </Typography>
            </CardActionArea>
          </Card>
        ))}
      </Box>

      {/* R-016 — current status summary */}
      <Card sx={{ p: 3 }} data-testid="kiosk-status-panel">
        <Typography variant="h5" component="h2" sx={{ fontWeight: 700, mb: 2 }}>
          {t('pages.kiosk.status.title')}
        </Typography>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={3}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <AssignmentIcon color="primary" aria-hidden="true" sx={{ fontSize: 40 }} />
            <Typography variant="h6" component="span">
              {t('pages.kiosk.status.openTasks', { count: openTasks })}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <WarningAmberIcon
              color={overdueTasks > 0 ? 'error' : 'disabled'}
              aria-hidden="true"
              sx={{ fontSize: 40 }}
            />
            <Typography variant="h6" component="span">
              {t('pages.kiosk.status.warnings', { count: overdueTasks })}
            </Typography>
          </Box>
        </Stack>
      </Card>
    </Box>
  );
}
