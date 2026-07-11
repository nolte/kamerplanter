import { useCallback, useMemo, useState } from 'react';
import type { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';
import Alert from '@mui/material/Alert';
import LinearProgress from '@mui/material/LinearProgress';
import Divider from '@mui/material/Divider';
import Stack from '@mui/material/Stack';
import AddIcon from '@mui/icons-material/Add';
import ScienceIcon from '@mui/icons-material/Science';
import SetMealIcon from '@mui/icons-material/SetMeal';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutlined';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutlined';
import PageTitle from '@/components/layout/PageTitle';
import EmptyState from '@/components/common/EmptyState';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import HelpTooltip from '@/components/common/HelpTooltip';
import { useNotification } from '@/hooks/useNotification';
import { useAquaponicSystems } from '@/hooks/useAquaponicSystems';
import type { CyclingStatus, WaterQualitySeverity } from '@/api/types';
import AquaponicSystemDialog from './AquaponicSystemDialog';
import WaterTestDialog from './WaterTestDialog';

const cyclingColor: Record<CyclingStatus, ChipProps['color']> = {
  new: 'default',
  cycling: 'warning',
  cycled: 'success',
  dormant: 'info',
};

const severityColor: Record<WaterQualitySeverity, ChipProps['color']> = {
  ok: 'success',
  info: 'info',
  warning: 'warning',
  critical: 'error',
};

// UI-NFR-002 R-018: severity is never conveyed by color alone — every chip
// also carries a distinct icon so colorblind users can tell states apart.
const severityIcon: Record<WaterQualitySeverity, ReactElement> = {
  ok: <CheckCircleOutlineIcon />,
  info: <InfoOutlinedIcon />,
  warning: <WarningAmberIcon />,
  critical: <ErrorOutlineIcon />,
};

export default function AquaponikPage() {
  const { t, i18n } = useTranslation();
  const notification = useNotification();
  const {
    systems,
    loading,
    selectedKey,
    selectSystem,
    detail,
    detailLoading,
    reloadSystems,
    reloadDetail,
  } = useAquaponicSystems();

  const [systemDialogOpen, setSystemDialogOpen] = useState(false);
  const [waterTestDialogOpen, setWaterTestDialogOpen] = useState(false);

  const selectedSystem = useMemo(
    () => systems.find((s) => s.key === selectedKey) ?? null,
    [systems, selectedKey],
  );

  const handleSystemCreated = useCallback(() => {
    setSystemDialogOpen(false);
    notification.success(t('pages.aquaponik.systemCreated'));
    reloadSystems();
  }, [notification, t, reloadSystems]);

  const handleWaterTestRecorded = useCallback(() => {
    setWaterTestDialogOpen(false);
    notification.success(t('pages.aquaponik.waterTestRecorded'));
    reloadDetail();
  }, [notification, t, reloadDetail]);

  // Backend messages/descriptions come bilingually (`_de`/`_en`); pick the
  // one matching the active UI language instead of hard-coding German
  // (UI-NFR-007 — same convention as SubstrateDetailPage, CalendarPage etc.).
  const isEnglish = i18n.language?.startsWith('en') ?? false;

  const criticalAlerts = useMemo(
    () => detail?.waterQuality.filter((e) => e.severity === 'critical') ?? [],
    [detail],
  );

  return (
    <Box sx={{ p: 3 }} data-testid="aquaponik-page">
      <PageTitle
        title={t('pages.aquaponik.title')}
        action={
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setSystemDialogOpen(true)}
            data-testid="create-system-button"
          >
            {t('pages.aquaponik.createSystem')}
          </Button>
        }
      />

      <Typography color="text.secondary" sx={{ mb: 3 }}>
        {t('pages.aquaponik.intro')}
      </Typography>

      {loading ? (
        <LoadingSkeleton variant="card" />
      ) : systems.length === 0 ? (
        <EmptyState
          message={t('pages.aquaponik.emptyTitle')}
          description={t('pages.aquaponik.emptyDescription')}
          actionLabel={t('pages.aquaponik.createSystem')}
          onAction={() => setSystemDialogOpen(true)}
        />
      ) : (
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 4 }}>
            <Stack spacing={2}>
              {systems.map((system) => (
                <Card
                  key={system.key}
                  variant={system.key === selectedKey ? 'elevation' : 'outlined'}
                  data-testid={`system-card-${system.key}`}
                >
                  <CardActionArea onClick={() => selectSystem(system.key)}>
                    <CardContent>
                      <Box
                        sx={{ display: 'flex', justifyContent: 'space-between', gap: 1, mb: 1 }}
                      >
                        <Typography variant="h6" component="h2">
                          {system.name}
                        </Typography>
                        <Chip
                          size="small"
                          label={t(`enums.cyclingStatus.${system.cycling_status}`)}
                          color={cyclingColor[system.cycling_status]}
                        />
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {t(`enums.aquaponicSystemType.${system.system_type}`)} ·{' '}
                        {system.total_volume_liters} L · {system.grow_area_m2} m²
                      </Typography>
                    </CardContent>
                  </CardActionArea>
                </Card>
              ))}
            </Stack>
          </Grid>

          <Grid size={{ xs: 12, md: 8 }}>
            {selectedSystem && (
              <Card variant="outlined" data-testid="system-detail">
                <CardContent>
                  <Box
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                      gap: 1,
                      mb: 2,
                    }}
                  >
                    <Typography variant="h5" component="h2">
                      {selectedSystem.name}
                    </Typography>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<ScienceIcon />}
                      onClick={() => setWaterTestDialogOpen(true)}
                      data-testid="record-water-test-button"
                    >
                      {t('pages.aquaponik.recordWaterTest')}
                    </Button>
                  </Box>

                  {detailLoading ? (
                    <LoadingSkeleton variant="card" />
                  ) : (
                    <>
                      {criticalAlerts.length > 0 && (
                        <Alert severity="error" sx={{ mb: 2 }} data-testid="critical-alert">
                          {criticalAlerts.length === 1 ? (
                            isEnglish ? criticalAlerts[0].message_en : criticalAlerts[0].message_de
                          ) : (
                            <Box component="ul" sx={{ m: 0, pl: 2.5 }}>
                              {criticalAlerts.map((a, idx) => (
                                <li key={`${a.parameter}-${idx}`}>
                                  {isEnglish ? a.message_en : a.message_de}
                                </li>
                              ))}
                            </Box>
                          )}
                        </Alert>
                      )}

                      {detail?.cycling && (
                        <Box sx={{ mb: 3 }}>
                          <HelpTooltip term="biofilter_cycling" placement="right">
                            <Typography variant="subtitle2">
                              {t('pages.aquaponik.cyclingProgress')}
                            </Typography>
                          </HelpTooltip>
                          <LinearProgress
                            variant="determinate"
                            value={detail.cycling.progress_percent}
                            sx={{ height: 8, borderRadius: 1, mb: 0.5, mt: 0.5 }}
                          />
                          <Typography variant="body2" color="text.secondary">
                            {detail.cycling.progress_percent}% ·{' '}
                            {isEnglish
                              ? detail.cycling.phase_description_en
                              : detail.cycling.phase_description_de}
                          </Typography>
                        </Box>
                      )}

                      <Divider sx={{ my: 2 }} />

                      <Typography variant="subtitle2" sx={{ mb: 1 }}>
                        {t('pages.aquaponik.waterQuality')}
                      </Typography>
                      {detail && detail.waterQuality.length === 0 ? (
                        <Typography variant="body2" color="text.secondary">
                          {t('pages.aquaponik.noWaterData')}
                        </Typography>
                      ) : (
                        <Stack
                          direction="row"
                          spacing={1}
                          sx={{ flexWrap: 'wrap', gap: 1, mb: 2 }}
                        >
                          {detail?.waterQuality.map((e, idx) => (
                            <Chip
                              key={`${e.parameter}-${idx}`}
                              icon={severityIcon[e.severity]}
                              label={`${t(`pages.aquaponik.params.${e.parameter}`, e.parameter)}: ${e.value}`}
                              color={severityColor[e.severity]}
                              size="small"
                            />
                          ))}
                        </Stack>
                      )}

                      <Divider sx={{ my: 2 }} />

                      <Box
                        sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}
                      >
                        <SetMealIcon fontSize="small" color="action" />
                        <Typography variant="subtitle2">
                          {t('pages.aquaponik.fishStocks')}
                        </Typography>
                      </Box>
                      {detail && detail.stocks.length === 0 ? (
                        <Typography variant="body2" color="text.secondary">
                          {t('pages.aquaponik.noStocks')}
                        </Typography>
                      ) : (
                        <Stack spacing={0.5}>
                          {detail?.stocks.map((stock) => (
                            <Typography
                              key={stock.key}
                              variant="body2"
                              data-testid={`stock-${stock.key}`}
                            >
                              {stock.name}: {stock.count} ·{' '}
                              {stock.total_biomass_kg} kg
                            </Typography>
                          ))}
                        </Stack>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            )}
          </Grid>
        </Grid>
      )}

      <AquaponicSystemDialog
        open={systemDialogOpen}
        onClose={() => setSystemDialogOpen(false)}
        onCreated={handleSystemCreated}
      />
      {selectedKey && (
        <WaterTestDialog
          open={waterTestDialogOpen}
          systemKey={selectedKey}
          onClose={() => setWaterTestDialogOpen(false)}
          onRecorded={handleWaterTestRecorded}
        />
      )}
    </Box>
  );
}
