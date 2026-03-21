import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Link from '@mui/material/Link';
import CircularProgress from '@mui/material/CircularProgress';
import ScienceIcon from '@mui/icons-material/Science';
import DeleteIcon from '@mui/icons-material/Delete';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import { Link as RouterLink } from 'react-router-dom';
import PhaseGanttChart from '@/pages/duengung/PhaseGanttChart';
import PhaseDetailGantt from '@/pages/duengung/PhaseDetailGantt';
import NutrientPlanAssignDialog from '@/pages/duengung/NutrientPlanAssignDialog';
import WateringCalendarView from './WateringCalendarView';
import { fetchWaterMixRecommendationsBatch } from '@/api/endpoints/nutrient-plans';
import type {
  Fertilizer,
  PlantingRunStatus,
  WateringScheduleCalendarResponse,
  SpeciesPhaseTimeline,
} from '@/api/types';
import type { RunNutrientData } from '@/hooks/useRunNutrientData';

interface PlantingRunNutrientWateringTabProps {
  runStatus: PlantingRunStatus | undefined;
  wateringLoading: boolean;
  assignedPlan: Record<string, unknown> | null;
  nutrientData: RunNutrientData;
  fertilizers: Fertilizer[];
  wateringCalendar: WateringScheduleCalendarResponse | null;
  quickConfirming: string | null;
  phaseTimelines: SpeciesPhaseTimeline[];
  planKey: string | null;
  siteKey: string | null;
  onAssignPlan: (planKey: string) => Promise<void>;
  onOpenRemovePlan: () => void;
  onQuickConfirm: (date: string, channelId?: string, stateKey?: string) => Promise<void>;
  onOpenConfirmDialog: (dateStr: string, channelId?: string) => void;
}

export default function PlantingRunNutrientWateringTab({
  runStatus,
  wateringLoading,
  assignedPlan,
  nutrientData,
  fertilizers,
  wateringCalendar,
  quickConfirming,
  phaseTimelines,
  planKey,
  siteKey,
  onAssignPlan,
  onOpenRemovePlan,
  onQuickConfirm,
  onOpenConfirmDialog,
}: PlantingRunNutrientWateringTabProps) {
  const { t } = useTranslation();
  const { currentDosages, currentWeek, adaptedEntries } = nutrientData;
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);

  // Fetch recommended RO% for each phase entry when plan + site are available
  const [recommendedRoMap, setRecommendedRoMap] = useState<Map<number, number>>(new Map());
  useEffect(() => {
    if (!planKey || !siteKey) {
      setRecommendedRoMap(new Map());
      return;
    }
    fetchWaterMixRecommendationsBatch(planKey, siteKey)
      .then((result) => {
        const map = new Map<number, number>();
        for (const rec of result.recommendations) {
          map.set(rec.sequence_order, rec.recommendation.recommended_ro_percent);
        }
        setRecommendedRoMap(map);
      })
      .catch(() => setRecommendedRoMap(new Map()));
  }, [planKey, siteKey]);

  return (
    <Box role="tabpanel" aria-labelledby="tab-nutrient-watering" data-testid="nutrient-watering-tab">
      {wateringLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {!wateringLoading && (
        <>
          {/* ── Plan assignment header ── */}
          {assignedPlan ? (
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ScienceIcon />
                <Link
                  component={RouterLink}
                  to={`/duengung/plans/${(assignedPlan as { key?: string }).key}`}
                  underline="hover"
                >
                  {(assignedPlan as { name?: string }).name}
                </Link>
              </Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<ScienceIcon />}
                  onClick={() => setAssignDialogOpen(true)}
                  disabled={runStatus === 'completed' || runStatus === 'cancelled'}
                >
                  {t('pages.nutrientPlans.assignPlan')}
                </Button>
                <Button
                  variant="outlined"
                  color="error"
                  size="small"
                  startIcon={<DeleteIcon />}
                  onClick={onOpenRemovePlan}
                >
                  {t('pages.nutrientPlans.removePlan')}
                </Button>
              </Box>
            </Box>
          ) : (
            <Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                {t('pages.nutrientPlans.noPlanAssigned')}
              </Alert>
              <Button
                variant="contained"
                startIcon={<ScienceIcon />}
                onClick={() => setAssignDialogOpen(true)}
                disabled={runStatus === 'completed' || runStatus === 'cancelled'}
              >
                {t('pages.nutrientPlans.assignPlan')}
              </Button>
            </Box>
          )}

          {/* Current phase / week indicator */}
          {currentDosages && currentWeek != null && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
              <Chip
                label={t(`enums.phaseName.${currentDosages.phaseName}`, currentDosages.phaseName)}
                size="small"
                color="primary"
              />
              <Typography variant="body2" color="text.secondary">
                {t('pages.wateringSchedule.week')} {currentWeek}
                {currentDosages.floweringWeek != null && (
                  <> &middot; {t('pages.wateringSchedule.floweringWeek', { week: currentDosages.floweringWeek })}</>
                )}
              </Typography>
            </Box>
          )}

          {/* Hint when water config is missing — RO% in Gantt will be empty */}
          {planKey && siteKey && recommendedRoMap.size === 0 && (
            <Alert severity="info" sx={{ mt: 1, mb: 1 }}>
              {t('pages.nutrientPlans.waterMix.noWaterConfig', { siteName: '' })}
              <Link component={RouterLink} to={`/standorte/sites/${siteKey}`} sx={{ ml: 0.5 }}>
                {t('pages.nutrientPlans.waterMix.configureSite')}
              </Link>
            </Alert>
          )}

          {/* Gantt charts */}
          {adaptedEntries.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <PhaseGanttChart
                entries={adaptedEntries}
                fertilizers={fertilizers}
                title=""
                currentWeek={currentWeek}
              />
              {(() => {
                const sorted = [...adaptedEntries].sort((a, b) => a.sequence_order - b.sequence_order);
                const vegPhases = new Set(['vegetative', 'seedling', 'germination']);
                const flowerPhases = new Set(['flowering', 'flushing', 'harvest']);
                const vegEntries = sorted.filter((e) => vegPhases.has(e.phase_name));
                const flowerEntries = sorted.filter((e) => flowerPhases.has(e.phase_name));
                return (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                    {vegEntries.length > 0 && (
                      <PhaseDetailGantt
                        entries={vegEntries}
                        fertilizers={fertilizers}
                        title={t('pages.gantt.vegetativeDetail')}
                        currentWeek={currentWeek}
                        recommendedRoMap={recommendedRoMap}
                      />
                    )}
                    {flowerEntries.length > 0 && (
                      <PhaseDetailGantt
                        entries={flowerEntries}
                        fertilizers={fertilizers}
                        title={t('pages.gantt.floweringDetail')}
                        currentWeek={currentWeek}
                        recommendedRoMap={recommendedRoMap}
                      />
                    )}
                  </Box>
                );
              })()}
            </Box>
          )}

          {/* ── Watering calendar ── */}
          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <WaterDropIcon color="primary" />
                <Typography variant="h6">
                  {t('pages.wateringSchedule.upcomingDates')}
                </Typography>
              </Box>

              {!wateringCalendar || !wateringCalendar.has_schedule ? (
                <Alert severity="info">
                  {t('pages.wateringSchedule.noPlan')}
                </Alert>
              ) : (
                <WateringCalendarView
                  dates={wateringCalendar.dates}
                  channelCalendars={wateringCalendar.channel_calendars ?? []}
                  quickConfirming={quickConfirming}
                  onQuickConfirm={onQuickConfirm}
                  onConfirm={(dateStr, channelId) => {
                    onOpenConfirmDialog(dateStr, channelId);
                  }}
                  phases={phaseTimelines.length > 0 ? phaseTimelines[0].phases : undefined}
                />
              )}
            </CardContent>
          </Card>
        </>
      )}

      {/* Assign Plan Dialog */}
      <NutrientPlanAssignDialog
        open={assignDialogOpen}
        onClose={() => setAssignDialogOpen(false)}
        onAssign={async (planKey) => {
          await onAssignPlan(planKey);
          setAssignDialogOpen(false);
        }}

      />
    </Box>
  );
}
