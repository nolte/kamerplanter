import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import type { ChipProps } from '@mui/material/Chip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Divider from '@mui/material/Divider';
import Link from '@mui/material/Link';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';

import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import ScienceIcon from '@mui/icons-material/Science';
import LocalDrinkIcon from '@mui/icons-material/LocalDrink';
import { Link as RouterLink } from 'react-router-dom';
import DataTable, { type Column } from '@/components/common/DataTable';
import MobileCard from '@/components/common/MobileCard';
import type {
  PlantingRun,
  PlantingRunEntry,
  Fertilizer,
  Species,
  Cultivar,
  SpeciesPhaseTimeline,
} from '@/api/types';
import type { RunNutrientData, ChannelGroup } from '@/hooks/useRunNutrientData';

interface PlantingRunDetailsTabProps {
  run: PlantingRun;
  entries: PlantingRunEntry[];
  entryColumns: Column<PlantingRunEntry>[];
  speciesMap: Map<string, string>;
  assignedPlan: Record<string, unknown> | null;
  locationName: string;
  fertilizers: Fertilizer[];
  nutrientData: RunNutrientData;
  dosageMode: 'per_liter' | 'total';
  onDosageModeChange: (mode: 'per_liter' | 'total') => void;
  wateringCanLiters: number;
  tankVolumeLiters: number | null;
  tankName: string | null;
  phaseTimelines: SpeciesPhaseTimeline[];
  speciesData: Species | null;
  cultivarData: Cultivar | null;
}

function frostChipColor(sensitivity: string | null): ChipProps['color'] {
  if (!sensitivity) return 'default';
  if (sensitivity === 'hardy' || sensitivity === 'very_hardy') return 'success';
  if (sensitivity === 'moderate') return 'warning';
  if (sensitivity === 'sensitive') return 'error';
  return 'default';
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
        <Box sx={{ overflowX: 'auto' }}>
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
        </Box>
      </CardContent>
    </Card>
  );
}

export default function PlantingRunDetailsTab({
  run,
  entries,
  entryColumns,
  speciesMap,
  assignedPlan,
  locationName,
  fertilizers,
  nutrientData,
  dosageMode,
  onDosageModeChange,
  wateringCanLiters,
  tankVolumeLiters,
  tankName,
  phaseTimelines,
  speciesData,
  cultivarData,
}: PlantingRunDetailsTabProps) {
  const { t, i18n } = useTranslation();
  const { currentDosages, currentWeek } = nutrientData;

  // Phase & harvest estimation
  const currentPhaseEntry = phaseTimelines[0]?.phases.find((p) => p.status === 'current') ?? null;
  // eslint-disable-next-line react-hooks/purity -- Date.now() during render is intentional for display-only elapsed time
  const now = Date.now();
  const daysInPhase = currentPhaseEntry?.actual_entered_at
    ? Math.floor((now - new Date(currentPhaseEntry.actual_entered_at).getTime()) / 86400000)
    : null;

  const totalDays = phaseTimelines[0]?.phases.reduce((sum, p) => sum + p.typical_duration_days, 0) ?? 0;
  const startDate = run.started_at ?? run.planned_start_date;
  const estimatedHarvestDate = startDate && totalDays > 0
    ? new Date(new Date(startDate).getTime() + totalDays * 86400000)
    : null;
  const daysRemaining = estimatedHarvestDate
    ? Math.ceil((estimatedHarvestDate.getTime() - now) / 86400000)
    : null;

  const monthName = (m: number) =>
    new Date(2024, m - 1).toLocaleString(i18n.language, { month: 'short' });

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
        {currentPhaseEntry && (
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <Typography variant="caption" color="text.secondary">{t('pages.plantingRuns.currentPhase')}</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
              <Chip
                label={currentPhaseEntry.display_name || currentPhaseEntry.phase_name}
                size="small"
                color="primary"
              />
            </Box>
          </Grid>
        )}
        {daysInPhase != null && currentPhaseEntry && (
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <Typography variant="caption" color="text.secondary">{t('pages.plantInstances.daysInPhase')}</Typography>
            <Typography variant="body1">
              {t('pages.plantingRuns.daysOfTypical', {
                current: daysInPhase,
                typical: currentPhaseEntry.typical_duration_days,
              })}
            </Typography>
          </Grid>
        )}
        {estimatedHarvestDate && daysRemaining != null && (
          <Grid size={{ xs: 6, sm: 4, md: 3 }}>
            <Typography variant="caption" color="text.secondary">{t('pages.plantInstances.estimatedHarvest')}</Typography>
            <Typography
              variant="body1"
              fontWeight={500}
              color={
                daysRemaining < 0
                  ? 'error.main'
                  : daysRemaining <= 7
                    ? 'warning.main'
                    : 'text.primary'
              }
            >
              {estimatedHarvestDate.toLocaleDateString(i18n.language)} ({daysRemaining > 0
                ? t('pages.plantingRuns.daysRemaining', { count: daysRemaining })
                : t('pages.plantingRuns.overdue', { count: Math.abs(daysRemaining) })})
            </Typography>
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

      {/* Species & Cultivar cards */}
      {speciesData && (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', md: cultivarData ? '1fr 1fr' : '1fr' },
            gap: 3,
            mb: 3,
          }}
        >
          <Card data-testid="run-species-card">
            <CardContent>
              {/* Header with name + link */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                <Box>
                  <Typography variant="h6" fontStyle="italic">{speciesData.scientific_name}</Typography>
                  {speciesData.common_names.length > 0 && (
                    <Typography variant="body2" color="text.secondary">
                      {speciesData.common_names.join(', ')}
                    </Typography>
                  )}
                </Box>
                <Link
                  component={RouterLink}
                  to={`/stammdaten/species/${speciesData.key}`}
                  underline="hover"
                  sx={{ whiteSpace: 'nowrap', ml: 2 }}
                >
                  {t('pages.plantInstances.viewSpecies')}
                </Link>
              </Box>

              <Divider sx={{ my: 1.5 }} />

              {/* Properties in 2-column grid */}
              <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, rowGap: 0.5, columnGap: 2 }}>
                {speciesData.growth_habit && (
                  <Typography variant="body2">
                    <Typography component="span" variant="body2" color="text.secondary">{t('pages.species.growthHabit')}: </Typography>
                    {t(`enums.growthHabit.${speciesData.growth_habit}`)}
                  </Typography>
                )}
                {speciesData.root_type && (
                  <Typography variant="body2">
                    <Typography component="span" variant="body2" color="text.secondary">{t('pages.species.rootType')}: </Typography>
                    {t(`enums.rootType.${speciesData.root_type}`)}
                  </Typography>
                )}
                {speciesData.mature_height_cm && (
                  <Typography variant="body2">
                    <Typography component="span" variant="body2" color="text.secondary">{t('pages.species.matureHeightCm')}: </Typography>
                    {speciesData.mature_height_cm} cm
                  </Typography>
                )}
                {speciesData.mature_width_cm && (
                  <Typography variant="body2">
                    <Typography component="span" variant="body2" color="text.secondary">{t('pages.species.matureWidthCm')}: </Typography>
                    {speciesData.mature_width_cm} cm
                  </Typography>
                )}
                {speciesData.spacing_cm && (
                  <Typography variant="body2">
                    <Typography component="span" variant="body2" color="text.secondary">{t('pages.species.spacingCm')}: </Typography>
                    {speciesData.spacing_cm} cm
                  </Typography>
                )}
                {speciesData.recommended_container_volume_l && (
                  <Typography variant="body2">
                    <Typography component="span" variant="body2" color="text.secondary">{t('pages.species.recommendedContainerVolumeL')}: </Typography>
                    {speciesData.recommended_container_volume_l} L
                  </Typography>
                )}
              </Box>

              {/* Suitability + frost as compact chips */}
              {(speciesData.frost_sensitivity || speciesData.indoor_suitable || speciesData.balcony_suitable ||
                speciesData.container_suitable || speciesData.greenhouse_recommended || speciesData.support_required) && (
                <>
                  <Divider sx={{ my: 1.5 }} />
                  <Box sx={{ display: 'flex', gap: 0.75, flexWrap: 'wrap' }}>
                    {speciesData.frost_sensitivity && (
                      <Chip
                        label={`${t('pages.species.frostSensitivity')}: ${t(`enums.frostTolerance.${speciesData.frost_sensitivity}`)}`}
                        size="small"
                        color={frostChipColor(speciesData.frost_sensitivity)}
                      />
                    )}
                    {speciesData.indoor_suitable && (
                      <Chip
                        label={`${t('pages.species.indoorSuitable')}: ${t(`enums.suitability.${speciesData.indoor_suitable}`)}`}
                        size="small"
                        variant="outlined"
                      />
                    )}
                    {speciesData.balcony_suitable && (
                      <Chip
                        label={`${t('pages.species.balconySuitable')}: ${t(`enums.suitability.${speciesData.balcony_suitable}`)}`}
                        size="small"
                        variant="outlined"
                      />
                    )}
                    {speciesData.container_suitable && (
                      <Chip
                        label={`${t('pages.species.containerSuitable')}: ${t(`enums.suitability.${speciesData.container_suitable}`)}`}
                        size="small"
                        variant="outlined"
                      />
                    )}
                    {speciesData.greenhouse_recommended && (
                      <Chip label={t('pages.species.greenhouseRecommended')} size="small" variant="outlined" />
                    )}
                    {speciesData.support_required && (
                      <Chip label={t('pages.species.supportRequired')} size="small" variant="outlined" />
                    )}
                  </Box>
                </>
              )}

              {/* Calendar months */}
              {(speciesData.harvest_months.length > 0 || speciesData.bloom_months.length > 0 || speciesData.direct_sow_months.length > 0) && (
                <>
                  <Divider sx={{ my: 1.5 }} />
                  {speciesData.harvest_months.length > 0 && (
                    <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 0.5, mb: 0.75 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5 }}>
                        {t('pages.species.harvestMonths')}:
                      </Typography>
                      {speciesData.harvest_months.map((m) => (
                        <Chip key={m} label={monthName(m)} size="small" />
                      ))}
                    </Box>
                  )}
                  {speciesData.bloom_months.length > 0 && (
                    <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 0.5, mb: 0.75 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5 }}>
                        {t('pages.species.bloomMonths')}:
                      </Typography>
                      {speciesData.bloom_months.map((m) => (
                        <Chip key={m} label={monthName(m)} size="small" />
                      ))}
                    </Box>
                  )}
                  {speciesData.direct_sow_months.length > 0 && (
                    <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 0.5 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5 }}>
                        {t('pages.species.directSowMonths')}:
                      </Typography>
                      {speciesData.direct_sow_months.map((m) => (
                        <Chip key={m} label={monthName(m)} size="small" />
                      ))}
                    </Box>
                  )}
                </>
              )}
            </CardContent>
          </Card>

          {cultivarData && (
            <Card data-testid="run-cultivar-card">
              <CardContent>
                {/* Header with name + link */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                  <Typography variant="h6">{cultivarData.name}</Typography>
                  <Link
                    component={RouterLink}
                    to={`/stammdaten/species/${speciesData.key}/cultivars/${cultivarData.key}`}
                    underline="hover"
                    sx={{ whiteSpace: 'nowrap', ml: 2 }}
                  >
                    {t('pages.plantInstances.viewCultivar')}
                  </Link>
                </Box>

                <Divider sx={{ my: 1.5 }} />

                {/* Properties in 2-column grid */}
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, rowGap: 0.5, columnGap: 2 }}>
                  {cultivarData.breeder && (
                    <Typography variant="body2">
                      <Typography component="span" variant="body2" color="text.secondary">{t('pages.cultivars.breeder')}: </Typography>
                      {cultivarData.breeder}{cultivarData.breeding_year ? ` (${cultivarData.breeding_year})` : ''}
                    </Typography>
                  )}
                  {cultivarData.days_to_maturity != null && (
                    <Typography variant="body2">
                      <Typography component="span" variant="body2" color="text.secondary">{t('pages.cultivars.daysToMaturity')}: </Typography>
                      {cultivarData.days_to_maturity}
                    </Typography>
                  )}
                  {cultivarData.patent_status && (
                    <Typography variant="body2">
                      <Typography component="span" variant="body2" color="text.secondary">{t('pages.cultivars.patentStatus')}: </Typography>
                      {cultivarData.patent_status}
                    </Typography>
                  )}
                </Box>

                {/* Traits */}
                {cultivarData.traits.length > 0 && (
                  <>
                    <Divider sx={{ my: 1.5 }} />
                    <Typography variant="caption" color="text.secondary">{t('pages.cultivars.traits')}</Typography>
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
                      {cultivarData.traits.map((trait) => (
                        <Chip key={trait} label={t(`enums.plantTrait.${trait}`)} size="small" />
                      ))}
                    </Box>
                  </>
                )}

                {/* Disease resistances */}
                {cultivarData.disease_resistances.length > 0 && (
                  <>
                    <Divider sx={{ my: 1.5 }} />
                    <Typography variant="caption" color="text.secondary">{t('pages.cultivars.diseaseResistances')}</Typography>
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
                      {cultivarData.disease_resistances.map((r) => (
                        <Chip key={r} label={r} size="small" variant="outlined" />
                      ))}
                    </Box>
                  </>
                )}
              </CardContent>
            </Card>
          )}
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
            mobileCardRenderer={(r) => (
              <MobileCard
                title={speciesMap.get(r.species_key) ?? r.species_key}
                subtitle={r.cultivar_key ? (speciesMap.get(r.cultivar_key) ?? r.cultivar_key) : undefined}
                chips={
                  <Chip label={r.id_prefix} size="small" variant="outlined" />
                }
                fields={[
                  { label: t('pages.plantingRuns.quantity'), value: String(r.quantity) },
                  ...(r.spacing_cm ? [{ label: t('pages.plantingRuns.spacing'), value: `${r.spacing_cm} cm` }] : []),
                ]}
              />
            )}
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
