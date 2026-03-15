import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Link from '@mui/material/Link';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import ScienceIcon from '@mui/icons-material/Science';
import LocalDrinkIcon from '@mui/icons-material/LocalDrink';
import { Link as RouterLink } from 'react-router-dom';
import DataTable, { type Column } from '@/components/common/DataTable';
import type { PlantingRun, PlantingRunEntry, Fertilizer } from '@/api/types';
import type { RunNutrientData, ChannelGroup } from '@/hooks/useRunNutrientData';

interface PlantingRunDetailsTabProps {
  run: PlantingRun;
  entries: PlantingRunEntry[];
  entryColumns: Column<PlantingRunEntry>[];
  assignedPlan: Record<string, unknown> | null;
  locationName: string;
  fertilizers: Fertilizer[];
  nutrientData: RunNutrientData;
  dosageMode: 'per_liter' | 'total';
  onDosageModeChange: (mode: 'per_liter' | 'total') => void;
  wateringCanLiters: number;
  tankVolumeLiters: number | null;
  tankName: string | null;
}

function ChannelCard({
  group,
  fertilizers,
  dosageMode,
  volumeLiters,
  volumeLabel,
  t,
}: {
  group: ChannelGroup;
  fertilizers: Fertilizer[];
  dosageMode: 'per_liter' | 'total';
  volumeLiters: number;
  volumeLabel: string;
  t: (key: string, opts?: Record<string, unknown>) => string;
}) {
  return (
    <Card variant="outlined" sx={{ flex: '1 1 300px' }}>
      <CardContent sx={{ pb: '12px !important' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
          <Typography variant="subtitle1" fontWeight={600}>
            {group.channelLabel}
          </Typography>
          <Chip
            label={t(`enums.applicationMethod.${group.applicationMethod}`)}
            size="small"
            variant="outlined"
          />
        </Box>
        <Box sx={{ display: 'flex', gap: 1.5, mb: 1.5, flexWrap: 'wrap' }}>
          {group.targetEcMs != null && (
            <Chip label={`EC ${group.targetEcMs} mS`} size="small" variant="outlined" />
          )}
          {group.targetPh != null && (
            <Chip label={`pH ${group.targetPh}`} size="small" variant="outlined" />
          )}
        </Box>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>{t('entities.fertilizer')}</TableCell>
                <TableCell align="right">
                  {dosageMode === 'per_liter' ? 'ml/L' : `ml / ${volumeLabel}`}
                </TableCell>
                <TableCell />
              </TableRow>
            </TableHead>
            <TableBody>
              {group.dosages.map((d) => {
                const fert = fertilizers.find((f) => f.key === d.fertilizerKey);
                const amount = dosageMode === 'per_liter'
                  ? d.mlPerLiter
                  : Math.round(d.mlPerLiter * volumeLiters * 100) / 100;
                return (
                  <TableRow key={d.fertilizerKey}>
                    <TableCell>{fert?.product_name ?? d.fertilizerKey}</TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight="bold">
                        {amount}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {d.optional && (
                        <Chip label={t('pages.wateringSchedule.optional')} size="small" variant="outlined" />
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
}

export default function PlantingRunDetailsTab({
  run,
  entries,
  entryColumns,
  assignedPlan,
  locationName,
  fertilizers,
  nutrientData,
  dosageMode,
  onDosageModeChange,
  wateringCanLiters,
  tankVolumeLiters,
  tankName,
}: PlantingRunDetailsTabProps) {
  const { t } = useTranslation();
  const { currentDosages, currentWeek } = nutrientData;

  // Determine volume for "total" mode per channel:
  // fertigation channels use tank volume, others use watering can
  const getVolumeForChannel = (group: ChannelGroup) => {
    if (group.applicationMethod === 'fertigation' && tankVolumeLiters) {
      return { liters: tankVolumeLiters, label: `${tankVolumeLiters} L Tank` };
    }
    return { liters: wateringCanLiters, label: `${wateringCanLiters} L` };
  };

  return (
    <Box role="tabpanel" aria-labelledby="tab-details">
      {/* Summary bar — Grid2 layout */}
      <Grid
        container
        spacing={2}
        sx={{ mb: 3, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: 1, borderColor: 'divider' }}
        data-testid="run-summary-bar"
      >
        <Grid size={{ xs: 6, sm: 4, md: 3 }}>
          <Typography variant="caption" color="text.secondary">{t('pages.plantingRuns.runType')}</Typography>
          <Typography variant="body1" fontWeight={500}>{t(`enums.plantingRunType.${run.run_type}`)}</Typography>
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 3 }}>
          <Typography variant="caption" color="text.secondary">{t('pages.plantingRuns.plannedQuantity')}</Typography>
          <Typography variant="body1">{run.planned_quantity}</Typography>
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 3 }}>
          <Typography variant="caption" color="text.secondary">{t('pages.plantingRuns.actualQuantity')}</Typography>
          <Typography variant="body1">{run.actual_quantity}</Typography>
        </Grid>
        {(run.started_at ?? run.planned_start_date) && (
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <Typography variant="caption" color="text.secondary">
              {run.started_at ? t('pages.plantingRuns.startedAt') : t('pages.plantingRuns.plannedStartDate')}
            </Typography>
            <Typography variant="body1">
              {run.started_at ? new Date(run.started_at).toLocaleDateString() : run.planned_start_date}
            </Typography>
          </Grid>
        )}
        {locationName && run.location_key && (
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <Typography variant="caption" color="text.secondary">{t('pages.plantingRuns.location')}</Typography>
            <Link
              component={RouterLink}
              to={`/standorte/locations/${run.location_key}`}
              underline="hover"
              variant="body1"
              display="block"
            >
              {locationName}
            </Link>
          </Grid>
        )}
        {assignedPlan && (
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <Typography variant="caption" color="text.secondary">{t('entities.nutrientPlan')}</Typography>
            <Link
              component={RouterLink}
              to={`/duengung/plans/${(assignedPlan as { key?: string }).key}`}
              underline="hover"
              variant="body1"
              display="block"
            >
              {(assignedPlan as { name?: string }).name ?? '\u2014'}
            </Link>
          </Grid>
        )}
      </Grid>

      {/* Current Dosage Overview — grouped by delivery channel */}
      {currentDosages && currentDosages.channelGroups.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <ScienceIcon color="primary" />
              <Typography variant="h6">
                {t('pages.wateringSchedule.currentDosage')}
              </Typography>
              <Chip label={currentDosages.phaseName} size="small" color="primary" />
              <Typography variant="body2" color="text.secondary">
                ({t('pages.wateringSchedule.week')} {currentWeek}
                {currentDosages.floweringWeek != null && (
                  <> &middot; {t('pages.wateringSchedule.floweringWeek', { week: currentDosages.floweringWeek })}</>
                )})
              </Typography>
            </Box>
            <ToggleButtonGroup
              value={dosageMode}
              exclusive
              onChange={(_, v) => { if (v) onDosageModeChange(v); }}
              size="small"
              aria-label={t('pages.wateringSchedule.dosageMode')}
            >
              <ToggleButton value="per_liter">ml/L</ToggleButton>
              <ToggleButton value="total">
                {tankVolumeLiters ? `${tankVolumeLiters} L` : `${wateringCanLiters} L`}
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>

          {/* Tank info hint */}
          {tankName && tankVolumeLiters && dosageMode === 'total' && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1.5 }}>
              <LocalDrinkIcon fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary">
                {t('pages.wateringSchedule.tankInfo', { name: tankName, volume: tankVolumeLiters })}
              </Typography>
            </Box>
          )}

          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            {currentDosages.channelGroups.map((group) => {
              const { liters, label } = getVolumeForChannel(group);
              return (
                <ChannelCard
                  key={group.channelId}
                  group={group}
                  fertilizers={fertilizers}
                  dosageMode={dosageMode}
                  volumeLiters={liters}
                  volumeLabel={label}
                  t={t}
                />
              );
            })}
          </Box>
        </Box>
      )}

      {/* Entries table */}
      {entries.length > 0 && (
        <Box>
          <Typography variant="h6" sx={{ mb: 2 }}>
            {t('pages.plantingRuns.entries')}
          </Typography>
          <DataTable
            columns={entryColumns}
            rows={entries}
            getRowKey={(r) => r.key}
            variant="simple"
            ariaLabel={t('pages.plantingRuns.entries')}
          />
        </Box>
      )}

      {/* Notes */}
      {run.notes && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              {t('pages.plantingRuns.notes')}
            </Typography>
            <Typography variant="body1">{run.notes}</Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
