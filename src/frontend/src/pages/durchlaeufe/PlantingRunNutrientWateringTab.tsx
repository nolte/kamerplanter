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
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import ScienceIcon from '@mui/icons-material/Science';
import DeleteIcon from '@mui/icons-material/Delete';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import { Link as RouterLink } from 'react-router-dom';
import PhaseGanttChart from '@/pages/duengung/PhaseGanttChart';
import PhaseDetailGantt from '@/pages/duengung/PhaseDetailGantt';
import WateringCalendarView from './WateringCalendarView';
import type {
  NutrientPlan,
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
  nutrientPlans: NutrientPlan[];
  selectedPlanKey: string;
  assigning: boolean;
  assignDialogOpen: boolean;
  nutrientData: RunNutrientData;
  fertilizers: Fertilizer[];
  wateringCalendar: WateringScheduleCalendarResponse | null;
  quickConfirming: string | null;
  phaseTimelines: SpeciesPhaseTimeline[];
  onSetSelectedPlanKey: (key: string) => void;
  onOpenAssignDialog: () => void;
  onCloseAssignDialog: () => void;
  onAssignPlan: () => Promise<void>;
  onOpenRemovePlan: () => void;
  onQuickConfirm: (date: string, channelId?: string, stateKey?: string) => Promise<void>;
  onOpenConfirmDialog: (dateStr: string, channelId?: string) => void;
}

export default function PlantingRunNutrientWateringTab({
  runStatus,
  wateringLoading,
  assignedPlan,
  nutrientPlans,
  selectedPlanKey,
  assigning,
  assignDialogOpen,
  nutrientData,
  fertilizers,
  wateringCalendar,
  quickConfirming,
  phaseTimelines,
  onSetSelectedPlanKey,
  onOpenAssignDialog,
  onCloseAssignDialog,
  onAssignPlan,
  onOpenRemovePlan,
  onQuickConfirm,
  onOpenConfirmDialog,
}: PlantingRunNutrientWateringTabProps) {
  const { t } = useTranslation();
  const { currentDosages, currentWeek, adaptedEntries } = nutrientData;

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
                  onClick={onOpenAssignDialog}
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
                onClick={onOpenAssignDialog}
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
                      />
                    )}
                    {flowerEntries.length > 0 && (
                      <PhaseDetailGantt
                        entries={flowerEntries}
                        fertilizers={fertilizers}
                        title={t('pages.gantt.floweringDetail')}
                        currentWeek={currentWeek}
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
      <Dialog open={assignDialogOpen} onClose={onCloseAssignDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{t('pages.nutrientPlans.assignPlan')}</DialogTitle>
        <DialogContent>
          <TextField
            select
            label={t('entities.nutrientPlan')}
            value={selectedPlanKey}
            onChange={(e) => onSetSelectedPlanKey(e.target.value)}
            fullWidth
            sx={{ mt: 1 }}
            data-testid="plan-select"
          >
            {nutrientPlans.map((plan) => (
              <MenuItem key={plan.key} value={plan.key}>
                {plan.name}
              </MenuItem>
            ))}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={onCloseAssignDialog}>
            {t('common.cancel')}
          </Button>
          <Button
            variant="contained"
            onClick={async () => {
              await onAssignPlan();
              onCloseAssignDialog();
            }}
            disabled={!selectedPlanKey || assigning}
            data-testid="assign-plan-button"
          >
            {assigning ? <CircularProgress size={20} /> : t('pages.nutrientPlans.assignPlan')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
