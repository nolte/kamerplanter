import { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Alert from '@mui/material/Alert';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Collapse from '@mui/material/Collapse';
import Divider from '@mui/material/Divider';
import { alpha, useTheme } from '@mui/material/styles';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ScienceIcon from '@mui/icons-material/Science';
import RepeatIcon from '@mui/icons-material/Repeat';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import HelpTooltip from '@/components/common/HelpTooltip';
import ExpertiseFieldWrapper from '@/components/common/ExpertiseFieldWrapper';
import DeliveryChannelChips from '../DeliveryChannelChips';
import DeliveryChannelAccordion from '../DeliveryChannelAccordion';
import PhaseGanttChart, { PHASE_COLORS } from '../PhaseGanttChart';
import PhaseDetailGantt from '../PhaseDetailGantt';
import type {
  NutrientPlan,
  NutrientPlanPhaseEntry,
  Fertilizer,
  DeliveryChannel,
  FertilizerDosage,
} from '@/api/types';

export default function PhaseTimelineTab({
  plan,
  entries,
  fertilizers,
  expandedEntries,
  toggleExpanded,
  onAddEntry,
  onEditEntry,
  onDeleteEntry,
  onAddChannel,
  onEditChannel,
  onDeleteChannel,
  onAddChannelFertilizer,
  onEditChannelFertilizer,
  onRemoveChannelFertilizer,
  onRemoveFertilizerFromGantt,
  onEntriesChange,
  onLogWatering,
}: {
  plan: NutrientPlan;
  entries: NutrientPlanPhaseEntry[];
  fertilizers: Fertilizer[];
  expandedEntries: Set<string>;
  toggleExpanded: (key: string) => void;
  onAddEntry: () => void;
  onEditEntry: (entry: NutrientPlanPhaseEntry) => void;
  onDeleteEntry: (entry: NutrientPlanPhaseEntry) => void;
  onAddChannel: (entryKey: string, existingIds: string[]) => void;
  onEditChannel: (entryKey: string, channel: DeliveryChannel) => void;
  onDeleteChannel: (entryKey: string, channelId: string) => void;
  onAddChannelFertilizer: (entryKey: string, channelId: string) => void;
  onEditChannelFertilizer: (entryKey: string, channelId: string, dosage: FertilizerDosage) => void;
  onRemoveChannelFertilizer: (entryKey: string, channelId: string, fertKey: string) => void;
  onRemoveFertilizerFromGantt?: (fertilizerKey: string, isAuto: boolean, entriesSubset: NutrientPlanPhaseEntry[]) => void;
  onEntriesChange?: (updatedEntries: NutrientPlanPhaseEntry[]) => void;
  onLogWatering?: (channel: DeliveryChannel) => void;
}) {
  const { t } = useTranslation();
  const theme = useTheme();
  const [selectedPhaseKey, setSelectedPhaseKey] = useState<string | null>(null);
  const cardRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const isPerennial = plan.cycle_restart_from_sequence != null;
  const sorted = [...entries].sort((a, b) => a.sequence_order - b.sequence_order);
  const initialEntries = isPerennial ? sorted.filter((e) => !e.is_recurring) : sorted;
  const seasonalEntries = isPerennial ? sorted.filter((e) => e.is_recurring) : [];

  // Current ISO week number for highlighting "today" in the calendar Gantt
  const currentIsoWeek = (() => {
    const now = new Date();
    const jan4 = new Date(now.getFullYear(), 0, 4);
    const dayOfYear = Math.floor((now.getTime() - new Date(now.getFullYear(), 0, 1).getTime()) / 86400000) + 1;
    const jan4DayOfWeek = jan4.getDay() || 7; // Mon=1..Sun=7
    return Math.ceil((dayOfYear + jan4DayOfWeek - 1) / 7);
  })();

  // Map seasonal cycle into a 52-week calendar year with month headers.
  // Entries that cross the year boundary (week_end > 52) are kept as-is;
  // PhaseGanttChart and FertilizerGanttChart handle wrap-around rendering
  // so that e.g. dormancy W49-W66 appears as one row with bars at W49-52 + W1-14.
  const calendarSeasonalEntries = (() => {
    if (seasonalEntries.length === 0) return [];
    const cycleStart = seasonalEntries[0].week_start;
    const cycleEnd = seasonalEntries[seasonalEntries.length - 1].week_end;
    const cycleLen = cycleEnd - cycleStart + 1;
    // No mapping needed if cycle fits in 52 weeks starting at W1
    if (cycleLen <= 52 && cycleStart <= 52 && cycleEnd <= 52) {
      return seasonalEntries;
    }
    const result: NutrientPlanPhaseEntry[] = [];
    for (const e of seasonalEntries) {
      if (e.week_end <= 52) {
        result.push(e);
      } else if (e.week_start <= 52) {
        // Crosses year boundary — keep as single entry (week_end > 52)
        result.push(e);
      } else {
        // Entirely past 52 — shift to start of year
        result.push({
          ...e,
          week_start: e.week_start - 52,
          week_end: e.week_end - 52,
        });
      }
    }
    return result.sort((a, b) => a.week_start - b.week_start);
  })();
  const seasonalCycleLen = seasonalEntries.length > 0
    ? seasonalEntries[seasonalEntries.length - 1].week_end - seasonalEntries[0].week_start + 1
    : 0;

  const renderEntryCard = (entry: NutrientPlanPhaseEntry) => {
    const phaseColor = PHASE_COLORS[entry.phase_name] ?? theme.palette.grey[600];
    const isSelected = selectedPhaseKey === entry.key;
    const duration = entry.week_end - entry.week_start + 1;

    return (
      <Card
        key={entry.key}
        ref={(el: HTMLDivElement | null) => { cardRefs.current[entry.key] = el; }}
        onClick={() => setSelectedPhaseKey(entry.key)}
        sx={{
          mb: 0,
          borderLeft: `4px solid ${phaseColor}`,
          transition: 'box-shadow 0.2s, background-color 0.2s',
          ...(isSelected && {
            boxShadow: `0 0 0 1px ${alpha(phaseColor, 0.4)}, ${theme.shadows[4]}`,
            bgcolor: alpha(phaseColor, 0.03),
          }),
          cursor: 'pointer',
          '&:hover': {
            bgcolor: alpha(phaseColor, 0.05),
          },
        }}
      >
        <CardContent sx={{ pb: 1, '&:last-child': { pb: 1.5 } }}>
          {/* Phase header bar */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              mb: 1,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.75,
                  bgcolor: alpha(phaseColor, 0.12),
                  borderRadius: 1,
                  px: 1.5,
                  py: 0.5,
                }}
              >
                <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: phaseColor, flexShrink: 0 }} />
                <Typography variant="subtitle2" sx={{ fontWeight: 700, color: phaseColor }}>
                  {t(`enums.phaseName.${entry.phase_name}`)}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ fontVariantNumeric: 'tabular-nums' }}>
                {t('pages.gantt.week')}{entry.week_start}–{entry.week_end} ({duration} {t('pages.nutrientPlans.weeks')})
              </Typography>
              <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.25 }}>
                <Chip
                  label={`NPK ${entry.npk_ratio[0]}-${entry.npk_ratio[1]}-${entry.npk_ratio[2]}`}
                  size="small"
                  variant="outlined"
                  sx={{ fontWeight: 600 }}
                />
                <HelpTooltip term="npk" iconOnly />
              </Box>
              {(() => {
                const ecValues = entry.delivery_channels
                  .filter((ch) => ch.target_ec_ms != null)
                  .map((ch) => ch.target_ec_ms!);
                if (ecValues.length === 0) return null;
                const unique = [...new Set(ecValues)];
                const label = unique.length === 1
                  ? `EC ${unique[0]} mS/cm`
                  : `EC ${Math.min(...unique)}–${Math.max(...unique)} mS/cm`;
                return (
                  <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.25 }}>
                    <Chip
                      label={label}
                      size="small"
                      variant="outlined"
                      color="info"
                      sx={{ fontWeight: 600 }}
                    />
                    <HelpTooltip term="ec" iconOnly />
                  </Box>
                );
              })()}
              {entry.is_recurring && (
                <Chip
                  icon={<RepeatIcon />}
                  label={t('pages.nutrientPlans.isRecurring')}
                  size="small"
                  variant="outlined"
                  color="secondary"
                />
              )}
              {entry.watering_schedule_override && (
                <Chip
                  icon={<WaterDropIcon />}
                  label={`${t('pages.nutrientPlans.wateringScheduleOverride')}: ${entry.watering_schedule_override.interval_days ?? '?'}d`}
                  size="small"
                  variant="outlined"
                  color="info"
                />
              )}
            </Box>
            <Box sx={{ display: 'flex', gap: 0.5, flexShrink: 0 }}>
              <Tooltip title={t('pages.nutrientPlans.showFertilizers')}>
                <IconButton
                  size="small"
                  onClick={(e) => { e.stopPropagation(); toggleExpanded(entry.key); }}
                >
                  {expandedEntries.has(entry.key) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
              </Tooltip>
              <Tooltip title={t('common.edit')}>
                <IconButton
                  size="small"
                  onClick={(e) => { e.stopPropagation(); onEditEntry(entry); }}
                >
                  <EditIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title={t('common.delete')}>
                <IconButton
                  size="small"
                  color="error"
                  onClick={(e) => { e.stopPropagation(); onDeleteEntry(entry); }}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>

          {/* Delivery channel chips */}
          {entry.delivery_channels.length > 0 && (
            <ExpertiseFieldWrapper minLevel="intermediate">
              <DeliveryChannelChips channels={entry.delivery_channels} />
            </ExpertiseFieldWrapper>
          )}

          {/* Additional details row */}
          {(entry.calcium_ppm != null || entry.magnesium_ppm != null || entry.notes) && (
            <Box sx={{ display: 'flex', gap: 1.5, mt: 1, flexWrap: 'wrap' }}>
              {entry.calcium_ppm != null && (
                <Typography variant="body2" color="text.secondary">
                  Ca: {entry.calcium_ppm} ppm
                </Typography>
              )}
              {entry.magnesium_ppm != null && (
                <Typography variant="body2" color="text.secondary">
                  Mg: {entry.magnesium_ppm} ppm
                </Typography>
              )}
              {entry.notes && (
                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  {entry.notes}
                </Typography>
              )}
            </Box>
          )}

          {/* Expandable delivery channels */}
          <Collapse in={expandedEntries.has(entry.key)}>
            <Box sx={{ mt: 2 }}>
              <ExpertiseFieldWrapper minLevel="intermediate">
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    mb: 1,
                  }}
                >
                  <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <ScienceIcon fontSize="small" />
                    {t('pages.deliveryChannels.title')}
                  </Typography>
                  <Button
                    size="small"
                    startIcon={<AddIcon />}
                    onClick={(e) => {
                      e.stopPropagation();
                      onAddChannel(entry.key, entry.delivery_channels.map((ch) => ch.channel_id));
                    }}
                  >
                    {t('pages.deliveryChannels.addChannel')}
                  </Button>
                </Box>
                {entry.delivery_channels.length === 0 ? (
                  <Alert severity="info" variant="outlined" sx={{ py: 0.5 }}>
                    {t('pages.deliveryChannels.noChannels')}
                  </Alert>
                ) : (
                  <DeliveryChannelAccordion
                    channels={entry.delivery_channels}
                    fertilizers={fertilizers}
                    onEditChannel={(ch) => onEditChannel(entry.key, ch)}
                    onDeleteChannel={(cid) => onDeleteChannel(entry.key, cid)}
                    onAddFertilizer={(cid) => onAddChannelFertilizer(entry.key, cid)}
                    onEditFertilizer={(cid, dosage) => onEditChannelFertilizer(entry.key, cid, dosage)}
                    onRemoveFertilizer={(cid, fk) => onRemoveChannelFertilizer(entry.key, cid, fk)}
                    onLogWatering={onLogWatering}
                  />
                )}
              </ExpertiseFieldWrapper>
            </Box>
          </Collapse>
        </CardContent>
      </Card>
    );
  };

  return (
    <Box>
      {/* Add Entry button */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={onAddEntry}
        >
          {t('pages.nutrientPlans.addEntry')}
        </Button>
      </Box>

      {entries.length === 0 ? (
        <Alert severity="info">{t('pages.nutrientPlans.noEntries')}</Alert>
      ) : (
        <>
          {/* Gantt timeline hero */}
          {isPerennial ? (
            <>
              {initialEntries.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <PhaseGanttChart
                    entries={initialEntries}
                    fertilizers={fertilizers}
                    title={t('pages.nutrientPlans.initialRunSection')}
                    onEditEntry={onEditEntry}
                  />
                </Box>
              )}
              {calendarSeasonalEntries.length > 0 && (
                <>
                  {initialEntries.length > 0 && <Divider sx={{ my: 2 }} />}
                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <RepeatIcon fontSize="small" color="action" />
                      <Typography variant="h6">
                        {t('pages.nutrientPlans.seasonalCycleSection')}
                      </Typography>
                      <Chip
                        label={`${seasonalCycleLen} ${t('pages.nutrientPlans.weeksPerCycle')}`}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {seasonalEntries.map((e) => t(`enums.phaseName.${e.phase_name}`)).join(' → ')}
                    </Typography>
                    <PhaseGanttChart
                      entries={calendarSeasonalEntries}
                      fertilizers={fertilizers}
                      title=""
                      currentWeek={currentIsoWeek}
                      totalWeeksOverride={52}
                      showMonthHeaders
                      onEditEntry={onEditEntry}
                    />
                  </Box>
                </>
              )}
            </>
          ) : (
            <>
              <PhaseGanttChart
                entries={sorted}
                fertilizers={fertilizers}
                title={t('pages.gantt.title')}
                onEditEntry={onEditEntry}
              />
              {(() => {
                const vegEntries = sorted.filter((e) =>
                  e.phase_name === 'vegetative' || e.phase_name === 'seedling' || e.phase_name === 'germination',
                );
                const flowerEntries = sorted.filter((e) =>
                  e.phase_name === 'flowering' || e.phase_name === 'flushing' || e.phase_name === 'harvest',
                );
                return (
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                    {vegEntries.length > 0 && (
                      <PhaseDetailGantt
                        entries={vegEntries}
                        fertilizers={fertilizers}
                        title={t('pages.gantt.vegetativeDetail')}
                        onEntriesChange={onEntriesChange}
                        onRemoveFertilizer={onRemoveFertilizerFromGantt ? (fk, isAuto) => onRemoveFertilizerFromGantt(fk, isAuto, vegEntries) : undefined}
                        onAddFertilizer={onAddChannelFertilizer}
                      />
                    )}
                    {flowerEntries.length > 0 && (
                      <PhaseDetailGantt
                        entries={flowerEntries}
                        fertilizers={fertilizers}
                        title={t('pages.gantt.floweringDetail')}
                        onEntriesChange={onEntriesChange}
                        onRemoveFertilizer={onRemoveFertilizerFromGantt ? (fk, isAuto) => onRemoveFertilizerFromGantt(fk, isAuto, flowerEntries) : undefined}
                        onAddFertilizer={onAddChannelFertilizer}
                      />
                    )}
                  </Box>
                );
              })()}
            </>
          )}

          {/* Phase detail cards */}
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              gap: 1.5,
              mt: 3,
            }}
          >
            {isPerennial ? (
              <>
                {initialEntries.length > 0 && (
                  <>
                    <Box sx={{ mb: 0.5 }}>
                      <Typography variant="overline" color="text.secondary">
                        {t('pages.nutrientPlans.initialRunSection')}
                      </Typography>
                    </Box>
                    {initialEntries.map(renderEntryCard)}
                  </>
                )}
                {seasonalEntries.length > 0 && (
                  <>
                    <Divider sx={{ my: 1 }} />
                    <Box sx={{ mb: 0.5, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <RepeatIcon color="secondary" fontSize="small" />
                      <Typography variant="overline" color="text.secondary">
                        {t('pages.nutrientPlans.seasonalCycleSection')}
                      </Typography>
                    </Box>
                    {seasonalEntries.map(renderEntryCard)}
                  </>
                )}
              </>
            ) : (
              sorted.map(renderEntryCard)
            )}
          </Box>
        </>
      )}
    </Box>
  );
}
