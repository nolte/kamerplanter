import { useEffect, useState, useCallback, useRef } from 'react';
import { useTabUrl } from '@/hooks/useTabUrl';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Collapse from '@mui/material/Collapse';
import Divider from '@mui/material/Divider';
import Slider from '@mui/material/Slider';
import { alpha, useTheme } from '@mui/material/styles';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ScienceIcon from '@mui/icons-material/Science';
import RepeatIcon from '@mui/icons-material/Repeat';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormChipInput from '@/components/form/FormChipInput';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import PhaseEntryDialog from './PhaseEntryDialog';
import DeliveryChannelChips from './DeliveryChannelChips';
import DeliveryChannelAccordion from './DeliveryChannelAccordion';
import PhaseGanttChart, { PHASE_COLORS } from './PhaseGanttChart';
import PhaseDetailGantt from './PhaseDetailGantt';
import {
  type FertilizerRemoveAllPayload,
} from './FertilizerGanttChart';
import DeliveryChannelDialog from './DeliveryChannelDialog';
import ChannelFertilizerDialog from './ChannelFertilizerDialog';
import type { DosageEntry } from './ChannelFertilizerDialog';
import DosageCalculatorTab from './DosageCalculatorTab';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import ExpertiseFieldWrapper from '@/components/common/ExpertiseFieldWrapper';
import PrintButton from '@/components/common/PrintButton';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useLocalFavorites } from '@/hooks/useLocalFavorites';
import WateringLogCreateDialog from '@/pages/giessprotokoll/WateringLogCreateDialog';
import * as planApi from '@/api/endpoints/nutrient-plans';
import { downloadNutrientPlanPdf } from '@/api/endpoints/print';
import * as fertApi from '@/api/endpoints/fertilizers';
import type {
  NutrientPlan,
  NutrientPlanPhaseEntry,
  PlanValidationResult,
  Fertilizer,
  ScheduleMode,
  DeliveryChannel,
  DeliveryChannelCreate,
  FertilizerDosage,
} from '@/api/types';

const substrateTypes = [
  'soil',
  'coco',
  'clay_pebbles',
  'perlite',
  'living_soil',
  'peat',
  'rockwool_slab',
  'rockwool_plug',
  'vermiculite',
  'none',
  'orchid_bark',
  'pon_mineral',
  'sphagnum',
  'hydro_solution',
] as const;

const applicationMethods = ['drench', 'foliar', 'top_dress'] as const;

const editSchema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().max(2000),
  recommended_substrate_type: z.enum(substrateTypes).nullable(),
  reference_substrate_type: z.enum(substrateTypes),
  author: z.string().max(200),
  is_template: z.boolean(),
  version: z.string().max(50),
  tags: z.array(z.string()),
  schedule_enabled: z.boolean(),
  schedule_mode: z.enum(['weekdays', 'interval']),
  weekday_schedule: z.array(z.number()),
  interval_days: z.number().min(1).max(90).nullable(),
  preferred_time: z.string().max(5),
  application_method: z.enum(applicationMethods),
  reminder_hours_before: z.number().min(0).max(24),
  times_per_day: z.number().min(1).max(6),
  water_mix_ratio_ro_percent: z.number().min(0).max(100).nullable(),
  cycle_restart_from_sequence: z.number().min(1).nullable(),
});

type EditFormData = z.infer<typeof editSchema>;

const WEEKDAY_KEYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] as const;

/** ISO week number (1-based). */
function PhaseTimelineTab({
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
              <Chip
                label={`NPK ${entry.npk_ratio[0]}-${entry.npk_ratio[1]}-${entry.npk_ratio[2]}`}
                size="small"
                variant="outlined"
                sx={{ fontWeight: 600 }}
              />
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
                  <Chip
                    label={label}
                    size="small"
                    variant="outlined"
                    color="info"
                    sx={{ fontWeight: 600 }}
                  />
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

export default function NutrientPlanDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();

  const { isFavorite, toggleFavorite } = useLocalFavorites('kamerplanter-nutrient-plan-favorites');

  const [plan, setPlan] = useState<NutrientPlan | null>(null);
  const [entries, setEntries] = useState<NutrientPlanPhaseEntry[]>([]);
  const [fertilizers, setFertilizers] = useState<Fertilizer[]>([]);
  const [validation, setValidation] = useState<PlanValidationResult | null>(null);
  const [validating, setValidating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useTabUrl(['phases', 'validation', 'dosage', 'edit']);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  // Phase entry dialog state
  const [entryDialogOpen, setEntryDialogOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState<NutrientPlanPhaseEntry | null>(null);
  const [deleteEntryOpen, setDeleteEntryOpen] = useState(false);
  const [deletingEntry, setDeletingEntry] = useState<NutrientPlanPhaseEntry | null>(null);

  // DeliveryChannel dialog state
  const [channelDialogOpen, setChannelDialogOpen] = useState(false);
  const [channelDialogEntryKey, setChannelDialogEntryKey] = useState<string>('');
  const [channelDialogExistingIds, setChannelDialogExistingIds] = useState<string[]>([]);
  const [editingChannel, setEditingChannel] = useState<DeliveryChannel | null>(null);

  // Channel fertilizer dialog state
  const [fertDialogOpen, setFertDialogOpen] = useState(false);
  const [fertDialogEntryKey, setFertDialogEntryKey] = useState<string>('');
  const [fertDialogChannelId, setFertDialogChannelId] = useState<string>('');
  const [fertDialogExistingKeys, setFertDialogExistingKeys] = useState<string[]>([]);
  const [editingFertDosage, setEditingFertDosage] = useState<FertilizerDosage | null>(null);

  // Channel delete confirm
  const [deleteChannelOpen, setDeleteChannelOpen] = useState(false);
  const [deletingChannelEntryKey, setDeletingChannelEntryKey] = useState<string>('');
  const [deletingChannelId, setDeletingChannelId] = useState<string>('');

  // Remove fertilizer from all entries/channels confirm
  const [removeFertAllOpen, setRemoveFertAllOpen] = useState(false);
  const [removeFertAllPayload, setRemoveFertAllPayload] = useState<FertilizerRemoveAllPayload | null>(null);

  // Watering log dialog state
  const [wateringLogOpen, setWateringLogOpen] = useState(false);
  const [wateringLogChannel, setWateringLogChannel] = useState<import('@/pages/giessprotokoll/WateringLogCreateDialog').ChannelPreset | undefined>(undefined);

  // Expanded rows for fertilizer dosages
  const [expandedEntries, setExpandedEntries] = useState<Set<string>>(new Set());

  const {
    control,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { isDirty },
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      name: '',
      description: '',
      recommended_substrate_type: null,
      reference_substrate_type: 'soil',
      author: '',
      is_template: false,
      version: '',
      tags: [],
      schedule_enabled: false,
      schedule_mode: 'weekdays',
      weekday_schedule: [],
      interval_days: null,
      preferred_time: '',
      application_method: 'drench',
      reminder_hours_before: 2,
      times_per_day: 1,
      water_mix_ratio_ro_percent: null,
      cycle_restart_from_sequence: null,
    },
  });

  const editScheduleMode = watch('schedule_mode');
  const editWeekdaySchedule = watch('weekday_schedule');
  const editScheduleEnabled = watch('schedule_enabled');

  const handleEditWeekdayToggle = (dayIndex: number) => {
    const current = editWeekdaySchedule;
    if (current.includes(dayIndex)) {
      setValue('weekday_schedule', current.filter((d) => d !== dayIndex), { shouldDirty: true });
    } else {
      setValue('weekday_schedule', [...current, dayIndex].sort(), { shouldDirty: true });
    }
  };

  const load = useCallback(async (silent = false) => {
    if (!key) return;
    if (!silent) setLoading(true);
    try {
      const [p, e, f] = await Promise.all([
        planApi.fetchNutrientPlan(key),
        planApi.fetchPhaseEntries(key),
        fertApi.fetchFertilizers(0, 200),
      ]);
      setPlan(p);
      setEntries(e);
      setFertilizers(f);
      const ws = p.watering_schedule;
      reset({
        name: p.name,
        description: p.description,
        recommended_substrate_type: p.recommended_substrate_type as typeof substrateTypes[number] | null,
        reference_substrate_type: (p.reference_substrate_type ?? 'soil') as typeof substrateTypes[number],
        author: p.author,
        is_template: p.is_template,
        version: p.version,
        tags: p.tags,
        schedule_enabled: ws != null,
        schedule_mode: ws?.schedule_mode ?? 'weekdays',
        weekday_schedule: ws?.weekday_schedule ?? [],
        interval_days: ws?.interval_days ?? null,
        preferred_time: ws?.preferred_time ?? '',
        application_method: (ws?.application_method ?? 'drench') as typeof applicationMethods[number],
        reminder_hours_before: ws?.reminder_hours_before ?? 2,
        times_per_day: ws?.times_per_day ?? 1,
        water_mix_ratio_ro_percent: p.water_mix_ratio_ro_percent ?? null,
        cycle_restart_from_sequence: p.cycle_restart_from_sequence ?? null,
      });
      setError(null);
    } catch (err) {
      setError(String(err));
    } finally {
      if (!silent) setLoading(false);
    }
  }, [key, reset]);

  useEffect(() => {
    load();
  }, [load]);

  const loadValidation = useCallback(async () => {
    if (!key) return;
    setValidating(true);
    try {
      const result = await planApi.validateNutrientPlan(key);
      setValidation(result);
    } catch (err) {
      handleError(err);
    } finally {
      setValidating(false);
    }
  }, [key, handleError]);

  useEffect(() => {
    if (tab === 1) {
      loadValidation();
    }
  }, [tab, loadValidation]);

  const onSave = async (data: EditFormData) => {
    if (!key) return;
    try {
      setSaving(true);
      const hasSchedule = data.schedule_enabled && (
        (data.schedule_mode === 'weekdays' && data.weekday_schedule.length > 0) ||
        (data.schedule_mode === 'interval' && data.interval_days != null && data.interval_days > 0)
      );
      await planApi.updateNutrientPlan(key, {
        name: data.name,
        description: data.description,
        recommended_substrate_type: data.recommended_substrate_type,
        reference_substrate_type: data.reference_substrate_type,
        author: data.author,
        is_template: data.is_template,
        version: data.version,
        tags: data.tags,
        watering_schedule: hasSchedule ? {
          schedule_mode: data.schedule_mode,
          weekday_schedule: data.weekday_schedule,
          interval_days: data.interval_days,
          preferred_time: data.preferred_time || null,
          application_method: data.application_method,
          reminder_hours_before: data.reminder_hours_before,
          times_per_day: data.times_per_day,
        } : null,
        water_mix_ratio_ro_percent: data.water_mix_ratio_ro_percent,
        cycle_restart_from_sequence: data.cycle_restart_from_sequence,
      });
      notification.success(t('common.save'));
      load(true);
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async () => {
    if (!key) return;
    try {
      await planApi.deleteNutrientPlan(key);
      notification.success(t('common.delete'));
      navigate('/duengung/plans');
    } catch (err) {
      handleError(err);
    }
  };

  const onDeleteEntry = async () => {
    if (!key || !deletingEntry) return;
    try {
      await planApi.deletePhaseEntry(key, deletingEntry.key);
      notification.success(t('common.delete'));
      setDeleteEntryOpen(false);
      setDeletingEntry(null);
      load(true);
    } catch (err) {
      handleError(err);
    }
  };

  const toggleExpanded = (entryKey: string) => {
    setExpandedEntries((prev) => {
      const next = new Set(prev);
      if (next.has(entryKey)) {
        next.delete(entryKey);
      } else {
        next.add(entryKey);
      }
      return next;
    });
  };

  const onRemoveChannelFertilizer = async (entryKey: string, channelId: string, fertilizerKey: string) => {
    try {
      await planApi.removeFertilizerFromChannel(entryKey, channelId, fertilizerKey);
      notification.success(t('common.delete'));
      load(true);
    } catch (err) {
      handleError(err);
    }
  };

  const onConfirmRemoveFertilizerFromAll = async () => {
    if (!removeFertAllPayload) return;
    try {
      await Promise.all(
        removeFertAllPayload.targets.map((t) =>
          planApi.removeFertilizerFromChannel(t.entryKey, t.channelId, removeFertAllPayload.fertilizerKey),
        ),
      );
      notification.success(t('common.delete'));
      load(true);
    } catch (err) {
      handleError(err);
    } finally {
      setRemoveFertAllOpen(false);
      setRemoveFertAllPayload(null);
    }
  };

  const onSaveChannel = async (channel: DeliveryChannelCreate) => {
    if (!key || !channelDialogEntryKey) return;
    try {
      const entry = entries.find((e) => e.key === channelDialogEntryKey);
      if (!entry) return;
      const existing = entry.delivery_channels.find((ch) => ch.channel_id === channel.channel_id);
      const merged = {
        ...channel,
        fertilizer_dosages: channel.fertilizer_dosages ?? existing?.fertilizer_dosages ?? [],
      };
      const updatedChannels = [
        ...entry.delivery_channels.filter((ch) => ch.channel_id !== channel.channel_id),
        merged,
      ];
      await planApi.updatePhaseEntry(key, channelDialogEntryKey, {
        delivery_channels: updatedChannels,
      });
      notification.success(t('common.save'));
      setChannelDialogOpen(false);
      setEditingChannel(null);
      load(true);
    } catch (err) {
      handleError(err);
    }
  };

  const onEditChannel = (entryKey: string, channel: DeliveryChannel) => {
    setChannelDialogEntryKey(entryKey);
    const entry = entries.find((e) => e.key === entryKey);
    setChannelDialogExistingIds(
      entry?.delivery_channels
        .filter((ch) => ch.channel_id !== channel.channel_id)
        .map((ch) => ch.channel_id) ?? [],
    );
    setEditingChannel(channel);
    setChannelDialogOpen(true);
  };

  const onDeleteChannel = async () => {
    if (!key || !deletingChannelEntryKey || !deletingChannelId) return;
    try {
      const entry = entries.find((e) => e.key === deletingChannelEntryKey);
      if (!entry) return;
      const updatedChannels = entry.delivery_channels.filter(
        (ch) => ch.channel_id !== deletingChannelId,
      );
      await planApi.updatePhaseEntry(key, deletingChannelEntryKey, {
        delivery_channels: updatedChannels,
      });
      notification.success(t('common.delete'));
      setDeleteChannelOpen(false);
      setDeletingChannelId('');
      setDeletingChannelEntryKey('');
      load(true);
    } catch (err) {
      handleError(err);
    }
  };

  const handleEntriesChange = useCallback(
    async (updatedEntries: NutrientPlanPhaseEntry[]) => {
      if (!key) return;
      try {
        const promises = updatedEntries
          .filter((updated) => {
            const original = entries.find((e) => e.key === updated.key);
            if (!original) return false;
            return JSON.stringify(original.delivery_channels) !== JSON.stringify(updated.delivery_channels);
          })
          .map((e) =>
            planApi.updatePhaseEntry(key, e.key, {
              delivery_channels: e.delivery_channels,
            }),
          );
        if (promises.length > 0) {
          await Promise.all(promises);
          load(true);
        }
      } catch (err) {
        handleError(err);
      }
    },
    [key, entries, load, handleError],
  );

  const onAddChannelFertilizer = (entryKey: string, channelId: string) => {
    const entry = entries.find((e) => e.key === entryKey);
    const channel = entry?.delivery_channels.find((ch) => ch.channel_id === channelId);
    setFertDialogEntryKey(entryKey);
    setFertDialogChannelId(channelId);
    setFertDialogExistingKeys(
      channel?.fertilizer_dosages.map((d) => d.fertilizer_key) ?? [],
    );
    setEditingFertDosage(null);
    setFertDialogOpen(true);
  };

  const onEditChannelFertilizer = (entryKey: string, channelId: string, dosage: FertilizerDosage) => {
    const entry = entries.find((e) => e.key === entryKey);
    const channel = entry?.delivery_channels.find((ch) => ch.channel_id === channelId);
    setFertDialogEntryKey(entryKey);
    setFertDialogChannelId(channelId);
    setFertDialogExistingKeys(
      channel?.fertilizer_dosages.map((d) => d.fertilizer_key) ?? [],
    );
    setEditingFertDosage(dosage);
    setFertDialogOpen(true);
  };

  const onSaveChannelFertilizer = async (items: DosageEntry[]) => {
    try {
      if (editingFertDosage) {
        await planApi.removeFertilizerFromChannel(
          fertDialogEntryKey,
          fertDialogChannelId,
          editingFertDosage.fertilizer_key,
        );
      }
      for (const item of items) {
        await planApi.addFertilizerToChannel(fertDialogEntryKey, fertDialogChannelId, item);
      }
      notification.success(t('common.save'));
      setFertDialogOpen(false);
      setEditingFertDosage(null);
      load(true);
    } catch (err) {
      handleError(err);
    }
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} />;
  if (!plan) return <ErrorDisplay error={t('errors.notFound')} />;

  return (
    <Box data-testid="nutrient-plan-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: 1,
          mb: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
          <PageTitle title={plan.name} sx={{ mb: 0 }} />
          {key && (
            <>
              <Tooltip title={t('pages.nutrientPlans.favToggle')}>
                <IconButton
                  onClick={() => toggleFavorite(key)}
                  aria-label={t('pages.nutrientPlans.favToggle')}
                  sx={{ color: isFavorite(key) ? 'warning.main' : 'action.disabled' }}
                >
                  {isFavorite(key) ? <StarIcon /> : <StarBorderIcon />}
                </IconButton>
              </Tooltip>
              <PrintButton
                onPrint={() => downloadNutrientPlanPdf(key)}
                filename={`nutrient-plan-${key}.pdf`}
                label={t('print.nutrientPlan')}
              />
            </>
          )}
          {plan.is_template && (
            <Chip label={t('pages.nutrientPlans.isTemplate')} size="small" color="primary" />
          )}
          {plan.cycle_restart_from_sequence != null && (
            <Chip
              icon={<RepeatIcon />}
              label={`${t('pages.nutrientPlans.cycleRestartFromSequence')}: #${plan.cycle_restart_from_sequence}`}
              size="small"
              variant="outlined"
            />
          )}
        </Box>
        <Button
          variant="outlined"
          color="error"
          startIcon={<DeleteIcon />}
          onClick={() => setDeleteOpen(true)}
          data-testid="delete-nutrient-plan-button"
        >
          {t('common.delete')}
        </Button>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('pages.nutrientPlans.tabPhaseEntries')} />
        <Tab label={t('pages.nutrientPlans.tabValidation')} />
        <Tab label={t('pages.nutrientPlans.dosageCalc.tabTitle')} />
        <Tab label={t('common.edit')} />
      </Tabs>

      {/* Tab 0: Phase Entries — Timeline-first with Gantt hero */}
      {tab === 0 && <PhaseTimelineTab
        plan={plan}
        entries={entries}
        fertilizers={fertilizers}
        expandedEntries={expandedEntries}
        toggleExpanded={toggleExpanded}
        onAddEntry={() => {
          setEditingEntry(null);
          setEntryDialogOpen(true);
        }}
        onEditEntry={(entry) => {
          setEditingEntry(entry);
          setEntryDialogOpen(true);
        }}
        onDeleteEntry={(entry) => {
          setDeletingEntry(entry);
          setDeleteEntryOpen(true);
        }}
        onAddChannel={(entryKey, existingIds) => {
          setChannelDialogEntryKey(entryKey);
          setChannelDialogExistingIds(existingIds);
          setEditingChannel(null);
          setChannelDialogOpen(true);
        }}
        onEditChannel={onEditChannel}
        onDeleteChannel={(entryKey, channelId) => {
          setDeletingChannelEntryKey(entryKey);
          setDeletingChannelId(channelId);
          setDeleteChannelOpen(true);
        }}
        onAddChannelFertilizer={onAddChannelFertilizer}
        onEditChannelFertilizer={onEditChannelFertilizer}
        onRemoveChannelFertilizer={onRemoveChannelFertilizer}
        onRemoveFertilizerFromGantt={(fertilizerKey, isAuto, entriesSubset) => {
          const autoMethods = new Set(['fertigation']);
          const targets: { entryKey: string; channelId: string }[] = [];
          for (const entry of entriesSubset) {
            for (const ch of entry.delivery_channels) {
              const chIsAuto = autoMethods.has(ch.application_method);
              if (chIsAuto !== isAuto) continue;
              if (ch.fertilizer_dosages.some((d) => d.fertilizer_key === fertilizerKey)) {
                targets.push({ entryKey: entry.key, channelId: ch.channel_id });
              }
            }
          }
          if (targets.length === 0) return;
          const fert = fertilizers.find((f) => f.key === fertilizerKey);
          setRemoveFertAllPayload({
            fertilizerKey,
            fertilizerName: fert?.product_name ?? fertilizerKey,
            targets,
          });
          setRemoveFertAllOpen(true);
        }}
        onEntriesChange={handleEntriesChange}
        onLogWatering={(ch) => {
          const volumeLiters = ch.method_params
            ? ch.method_params.method === 'drench'
              ? ch.method_params.volume_per_feeding_liters
              : ch.method_params.method === 'foliar'
                ? ch.method_params.volume_per_spray_liters
                : null
            : null;
          setWateringLogChannel({
            channelId: ch.channel_id,
            channelLabel: ch.label || ch.channel_id,
            nutrientPlanKey: plan!.key,
            applicationMethod: ch.application_method as 'fertigation' | 'drench' | 'foliar' | 'top_dress',
            targetEcMs: ch.target_ec_ms,
            targetPh: ch.target_ph,
            fertilizers: ch.fertilizer_dosages
              .filter((d) => !d.optional)
              .sort((a, b) => a.mixing_order - b.mixing_order)
              .map((d) => ({ fertilizer_key: d.fertilizer_key, ml_per_liter: d.ml_per_liter })),
            volumeLiters,
          });
          setWateringLogOpen(true);
        }}
      />}

      {/* Tab 1: Validation */}
      {tab === 1 && (
        <Box>
          {validating && !validation && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          )}
          {validation && (
            <>
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {t('pages.nutrientPlans.completeness')}
                  </Typography>
                  <Alert
                    severity={validation.completeness.complete ? 'success' : 'warning'}
                    sx={{ mb: 1 }}
                  >
                    {validation.completeness.complete
                      ? t('pages.nutrientPlans.planComplete')
                      : t('pages.nutrientPlans.planIncomplete')}
                  </Alert>
                  {(validation.completeness.issues ?? []).map((issue, i) => (
                    <Alert key={i} severity="warning" sx={{ mb: 0.5 }}>
                      {issue}
                    </Alert>
                  ))}
                </CardContent>
              </Card>

              {/* Channel Validations with EC Budget */}
              {(validation.channel_validations ?? []).length > 0 && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {t('pages.deliveryChannels.validation.title')}
                    </Typography>
                    {(validation.channel_validations ?? []).map((cv, i) => (
                      <Box key={i} sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
                          {t(`enums.phaseName.${cv.phase_name}`)}
                        </Typography>
                        {(cv.channel_results ?? []).map((cr, j) => (
                          <Alert
                            key={j}
                            severity={cr.issues.length === 0 ? 'success' : 'error'}
                            sx={{ mb: 0.5 }}
                            action={
                              <Tooltip title={t('common.edit')}>
                                <IconButton
                                  size="small"
                                  onClick={() => {
                                    const entry = entries.find((e) => e.key === cv.entry_key);
                                    if (!entry) return;
                                    const channel = entry.delivery_channels.find(
                                      (ch) => ch.channel_id === cr.channel_id,
                                    );
                                    if (channel) {
                                      onEditChannel(entry.key, channel);
                                    }
                                  }}
                                >
                                  <EditIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            }
                          >
                            <strong>{cr.label || cr.channel_id}</strong>:{' '}
                            {cr.issues.length === 0
                              ? t('pages.deliveryChannels.validation.noIssues')
                              : cr.issues.join('; ')}
                            {cr.ec_budget && (
                              <Box component="span" sx={{ display: 'block', mt: 0.5, fontSize: '0.85em' }}>
                                EC: {cr.ec_budget.calculated.toFixed(2)} / {cr.ec_budget.target} mS
                                {' '}({t('pages.nutrientPlans.delta')}: {cr.ec_budget.delta > 0 ? '+' : ''}{cr.ec_budget.delta.toFixed(2)},
                                {' '}{t('pages.deliveryChannels.validation.tolerance')}: ±{cr.ec_budget.tolerance.toFixed(2)})
                              </Box>
                            )}
                          </Alert>
                        ))}
                      </Box>
                    ))}
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </Box>
      )}

      {/* Tab 2: Dosage Calculator */}
      {tab === 2 && (
        <DosageCalculatorTab plan={plan} entries={entries} />
      )}

      {/* Tab 3: Edit */}
      {tab === 3 && (
        <Box component="form" onSubmit={handleSubmit(onSave)} sx={{ maxWidth: 900, display: 'flex', flexDirection: 'column', gap: 4 }}>
          <Typography variant="body2" color="text.secondary">
            {t('pages.nutrientPlans.editIntro')}
          </Typography>

          {/* Section: General */}
          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.nutrientPlans.sectionGeneral')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.nutrientPlans.sectionGeneralDesc')}
              </Typography>
              <FormTextField
                name="name"
                control={control}
                label={t('pages.nutrientPlans.name')}
                required
                autoFocus
              />
              <FormTextField
                name="description"
                control={control}
                label={t('pages.nutrientPlans.description')}
                multiline
                rows={3}
              />
              <FormSelectField
                name="recommended_substrate_type"
                control={control}
                label={t('pages.nutrientPlans.substrateType')}
                options={substrateTypes.map((v) => ({
                  value: v,
                  label: t(`enums.substrateType.${v}`),
                }))}
              />
              <ExpertiseFieldWrapper minLevel="expert">
                <FormSelectField
                  name="reference_substrate_type"
                  control={control}
                  label={t('pages.nutrientPlans.referenceSubstrateType')}
                  options={substrateTypes.map((v) => ({
                    value: v,
                    label: t(`enums.substrateType.${v}`),
                  }))}
                />
              </ExpertiseFieldWrapper>
              <FormTextField
                name="author"
                control={control}
                label={t('pages.nutrientPlans.author')}
              />
              <FormSwitchField
                name="is_template"
                control={control}
                label={t('pages.nutrientPlans.isTemplate')}
              />
              <FormTextField
                name="version"
                control={control}
                label={t('pages.nutrientPlans.version')}
              />
              <FormChipInput
                name="tags"
                control={control}
                label={t('pages.nutrientPlans.tags')}
                placeholder={t('pages.nutrientPlans.tagsPlaceholder')}
              />
            </CardContent>
          </Card>

          {/* Section: Advanced */}
          <ExpertiseFieldWrapper minLevel="intermediate">
            <Card variant="outlined">
              <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
                <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                  {t('pages.nutrientPlans.sectionAdvanced')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {t('pages.nutrientPlans.sectionAdvancedDesc')}
                </Typography>

                {/* Water Mix Ratio */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {t('pages.nutrientPlans.waterMixRatio')}
                  </Typography>
                  <Controller
                    name="water_mix_ratio_ro_percent"
                    control={control}
                    render={({ field }) => (
                      <Slider
                        value={field.value ?? 0}
                        onChange={(_, val) => field.onChange(val as number || null)}
                        min={0}
                        max={100}
                        step={5}
                        valueLabelDisplay="auto"
                        valueLabelFormat={(v) => `${v}%`}
                        marks={[
                          { value: 0, label: '0%' },
                          { value: 50, label: '50%' },
                          { value: 100, label: '100%' },
                        ]}
                        data-testid="water-mix-slider"
                      />
                    )}
                  />
                </Box>

                {/* Cycle Restart */}
                <FormNumberField
                  name="cycle_restart_from_sequence"
                  control={control}
                  label={t('pages.nutrientPlans.cycleRestartFromSequence')}
                  min={1}
                  helperText={t('pages.nutrientPlans.cycleRestartHelper')}
                />
              </CardContent>
            </Card>
          </ExpertiseFieldWrapper>

          {/* Section: Watering Schedule */}
          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.nutrientPlans.sectionSchedule')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.nutrientPlans.sectionScheduleDesc')}
              </Typography>

              <FormSwitchField
                name="schedule_enabled"
                control={control}
                label={t('pages.wateringSchedule.title')}
              />

              <Collapse in={editScheduleEnabled}>
                <Box sx={{ pl: 1, pt: 1 }}>
                  {/* Schedule Mode Toggle */}
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {t('pages.wateringSchedule.mode')}
                    </Typography>
                    <Controller
                      name="schedule_mode"
                      control={control}
                      render={({ field }) => (
                        <ToggleButtonGroup
                          value={field.value}
                          exclusive
                          onChange={(_, value: ScheduleMode | null) => {
                            if (value) field.onChange(value);
                          }}
                          size="small"
                          fullWidth
                        >
                          <ToggleButton value="weekdays">
                            {t('pages.wateringSchedule.weekdays')}
                          </ToggleButton>
                          <ToggleButton value="interval">
                            {t('pages.wateringSchedule.interval')}
                          </ToggleButton>
                        </ToggleButtonGroup>
                      )}
                    />
                  </Box>

                  {/* Weekday Checkboxes */}
                  {editScheduleMode === 'weekdays' && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                        {t('pages.wateringSchedule.weekdays')}
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {WEEKDAY_KEYS.map((dayKey, index) => (
                          <FormControlLabel
                            key={dayKey}
                            control={
                              <Checkbox
                                checked={editWeekdaySchedule.includes(index)}
                                onChange={() => handleEditWeekdayToggle(index)}
                                size="small"
                              />
                            }
                            label={t(`pages.wateringSchedule.${dayKey}`)}
                          />
                        ))}
                      </Box>
                    </Box>
                  )}

                  {/* Interval Days */}
                  {editScheduleMode === 'interval' && (
                    <FormNumberField
                      name="interval_days"
                      control={control}
                      label={t('pages.wateringSchedule.intervalDays')}
                      min={1}
                      max={90}
                      step={1}
                    />
                  )}

                  {/* Preferred Time */}
                  <Controller
                    name="preferred_time"
                    control={control}
                    render={({ field, fieldState: { error } }) => (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                          {t('pages.wateringSchedule.preferredTime')}
                        </Typography>
                        <input
                          type="time"
                          value={field.value}
                          onChange={field.onChange}
                          onBlur={field.onBlur}
                          style={{
                            width: '100%',
                            padding: '0.5rem',
                            fontSize: '1rem',
                            border: error ? '1px solid red' : '1px solid rgba(0,0,0,0.23)',
                            borderRadius: '4px',
                          }}
                        />
                        {error?.message && (
                          <Typography variant="caption" color="error">
                            {error.message}
                          </Typography>
                        )}
                      </Box>
                    )}
                  />

                  {/* Application Method */}
                  <FormSelectField
                    name="application_method"
                    control={control}
                    label={t('pages.wateringSchedule.applicationMethod')}
                    options={applicationMethods.map((v) => ({
                      value: v,
                      label: t(`enums.applicationMethod.${v}`),
                    }))}
                  />

                  {/* Reminder Hours Before */}
                  <FormNumberField
                    name="reminder_hours_before"
                    control={control}
                    label={t('pages.wateringSchedule.reminderHoursBefore')}
                    min={0}
                    max={24}
                    step={1}
                  />

                  {/* Times Per Day */}
                  <FormNumberField
                    name="times_per_day"
                    control={control}
                    label={t('pages.wateringSchedule.timesPerDay')}
                    min={1}
                    max={6}
                    step={1}
                  />
                </Box>
              </Collapse>
            </CardContent>
          </Card>

          <Typography variant="caption" color="text.secondary">* {t('common.required')}</Typography>
          <FormActions
            onCancel={() => reset()}
            loading={saving}
            disabled={!isDirty}
          />
        </Box>
      )}

      {/* Dialogs */}
      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: plan.name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />

      <ConfirmDialog
        open={deleteEntryOpen}
        title={t('common.delete')}
        message={t('pages.nutrientPlans.deleteEntryConfirm', {
          phase: deletingEntry ? t(`enums.phaseName.${deletingEntry.phase_name}`) : '',
        })}
        onConfirm={onDeleteEntry}
        onCancel={() => {
          setDeleteEntryOpen(false);
          setDeletingEntry(null);
        }}
        destructive
      />

      <ConfirmDialog
        open={deleteChannelOpen}
        title={t('pages.deliveryChannels.deleteChannel')}
        message={t('pages.deliveryChannels.deleteChannelConfirm', {
          label: deletingChannelId,
        })}
        onConfirm={onDeleteChannel}
        onCancel={() => {
          setDeleteChannelOpen(false);
          setDeletingChannelId('');
          setDeletingChannelEntryKey('');
        }}
        destructive
      />

      <ConfirmDialog
        open={removeFertAllOpen}
        title={t('common.delete')}
        message={t('pages.fertilizerGantt.removeFertilizerConfirm', {
          name: removeFertAllPayload?.fertilizerName ?? '',
        })}
        onConfirm={onConfirmRemoveFertilizerFromAll}
        onCancel={() => {
          setRemoveFertAllOpen(false);
          setRemoveFertAllPayload(null);
        }}
        destructive
      />

      {key && (
        <PhaseEntryDialog
          open={entryDialogOpen}
          onClose={() => {
            setEntryDialogOpen(false);
            setEditingEntry(null);
          }}
          planKey={key}
          entry={editingEntry}
          onSaved={() => {
            setEntryDialogOpen(false);
            setEditingEntry(null);
            load(true);
          }}
        />
      )}

      <DeliveryChannelDialog
        open={channelDialogOpen}
        onClose={() => {
          setChannelDialogOpen(false);
          setEditingChannel(null);
        }}
        onSave={onSaveChannel}
        existingChannel={editingChannel}
        existingIds={channelDialogExistingIds}
      />

      <ChannelFertilizerDialog
        open={fertDialogOpen}
        onClose={() => {
          setFertDialogOpen(false);
          setEditingFertDosage(null);
        }}
        onSave={onSaveChannelFertilizer}
        fertilizers={fertilizers}
        existingFertilizerKeys={fertDialogExistingKeys}
        existingDosage={editingFertDosage}
      />

      <WateringLogCreateDialog
        open={wateringLogOpen}
        onClose={() => {
          setWateringLogOpen(false);
          setWateringLogChannel(undefined);
        }}
        onCreated={() => {
          setWateringLogOpen(false);
          setWateringLogChannel(undefined);
          notification.success(t('pages.wateringLogs.logged'));
        }}
        channelPreset={wateringLogChannel}
        availableFertilizers={fertilizers}
      />
    </Box>
  );
}
