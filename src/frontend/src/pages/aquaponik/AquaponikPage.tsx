import { useCallback, useEffect, useMemo, useState } from 'react';
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
import Tooltip from '@mui/material/Tooltip';
import AddIcon from '@mui/icons-material/Add';
import ScienceIcon from '@mui/icons-material/Science';
import SetMealIcon from '@mui/icons-material/SetMeal';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import PageTitle from '@/components/layout/PageTitle';
import EmptyState from '@/components/common/EmptyState';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/aquaponik';
import type {
  AquaponicSystem,
  CyclingProgress,
  CyclingStatus,
  FishStock,
  WaterQualityEvaluation,
  WaterQualitySeverity,
} from '@/api/types';
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

interface SystemDetail {
  cycling: CyclingProgress | null;
  waterQuality: WaterQualityEvaluation[];
  stocks: FishStock[];
}

export default function AquaponikPage() {
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [systems, setSystems] = useState<AquaponicSystem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [detail, setDetail] = useState<SystemDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [systemDialogOpen, setSystemDialogOpen] = useState(false);
  const [waterTestDialogOpen, setWaterTestDialogOpen] = useState(false);

  const loadSystems = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listSystems();
      setSystems(data);
      if (data.length > 0) {
        setSelectedKey((prev) => prev ?? data[0].key);
      }
    } catch (error) {
      handleError(error);
    } finally {
      setLoading(false);
    }
  }, [handleError]);

  const loadDetail = useCallback(
    async (key: string) => {
      setDetailLoading(true);
      try {
        const [cycling, waterQuality, stocks] = await Promise.all([
          api.getCyclingProgress(key),
          api.getWaterQualityStatus(key),
          api.listStocks(key),
        ]);
        setDetail({ cycling, waterQuality, stocks });
      } catch (error) {
        handleError(error);
      } finally {
        setDetailLoading(false);
      }
    },
    [handleError],
  );

  useEffect(() => {
    void loadSystems();
  }, [loadSystems]);

  useEffect(() => {
    if (selectedKey) {
      void loadDetail(selectedKey);
    }
  }, [selectedKey, loadDetail]);

  const selectedSystem = useMemo(
    () => systems.find((s) => s.key === selectedKey) ?? null,
    [systems, selectedKey],
  );

  const handleSystemCreated = useCallback(() => {
    setSystemDialogOpen(false);
    notification.success(t('pages.aquaponik.systemCreated'));
    void loadSystems();
  }, [notification, t, loadSystems]);

  const handleWaterTestRecorded = useCallback(() => {
    setWaterTestDialogOpen(false);
    notification.success(t('pages.aquaponik.waterTestRecorded'));
    if (selectedKey) {
      void loadDetail(selectedKey);
    }
  }, [notification, t, selectedKey, loadDetail]);

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
                  <CardActionArea onClick={() => setSelectedKey(system.key)}>
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
                          {criticalAlerts.map((a) => a.message_de).join(' ')}
                        </Alert>
                      )}

                      {detail?.cycling && (
                        <Box sx={{ mb: 3 }}>
                          <Box
                            sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}
                          >
                            <Typography variant="subtitle2">
                              {t('pages.aquaponik.cyclingProgress')}
                            </Typography>
                            <Tooltip title={t('pages.aquaponik.cyclingHelp')}>
                              <InfoOutlinedIcon
                                fontSize="small"
                                color="action"
                                aria-label={t('pages.aquaponik.cyclingHelp')}
                              />
                            </Tooltip>
                          </Box>
                          <LinearProgress
                            variant="determinate"
                            value={detail.cycling.progress_percent}
                            sx={{ height: 8, borderRadius: 1, mb: 0.5 }}
                          />
                          <Typography variant="body2" color="text.secondary">
                            {detail.cycling.progress_percent}% ·{' '}
                            {detail.cycling.phase_description_de}
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
