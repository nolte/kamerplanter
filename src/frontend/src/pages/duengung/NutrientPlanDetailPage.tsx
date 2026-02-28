import { useEffect, useState, useCallback } from 'react';
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
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ScienceIcon from '@mui/icons-material/Science';
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
import PhaseGanttChart from './PhaseGanttChart';
import FertilizerGanttChart from './FertilizerGanttChart';
import DeliveryChannelDialog from './DeliveryChannelDialog';
import ChannelFertilizerDialog from './ChannelFertilizerDialog';
import type { DosageEntry } from './ChannelFertilizerDialog';
import ExpertiseFieldWrapper from '@/components/common/ExpertiseFieldWrapper';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as planApi from '@/api/endpoints/nutrient-plans';
import * as fertApi from '@/api/endpoints/fertilizers';
import * as tankApi from '@/api/endpoints/tanks';
import type {
  NutrientPlan,
  NutrientPlanPhaseEntry,
  PlanValidationResult,
  Fertilizer,
  Tank,
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
});

type EditFormData = z.infer<typeof editSchema>;

const WEEKDAY_KEYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] as const;

function WateringScheduleTabContent({
  plan,
  entries,
  fertilizers,
}: {
  plan: NutrientPlan;
  entries: NutrientPlanPhaseEntry[];
  fertilizers: Fertilizer[];
}) {
  const { t } = useTranslation();

  const schedule = plan.watering_schedule;

  if (!schedule) {
    return (
      <Card>
        <CardContent>
          <Alert severity="info">
            {t('pages.wateringSchedule.noSchedule')}
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const entriesWithChannels = entries
    .filter((e) => e.delivery_channels.length > 0)
    .sort((a, b) => a.sequence_order - b.sequence_order);

  return (
    <Box data-testid="watering-schedule-tab" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {t('pages.wateringSchedule.title')}
          </Typography>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Mode */}
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                {t('pages.wateringSchedule.mode')}
              </Typography>
              <Typography>
                {schedule.schedule_mode === 'weekdays'
                  ? t('pages.wateringSchedule.weekdays')
                  : t('pages.wateringSchedule.interval')}
              </Typography>
            </Box>

            {/* Weekdays */}
            {schedule.schedule_mode === 'weekdays' && schedule.weekday_schedule.length > 0 && (
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  {t('pages.wateringSchedule.weekdays')}
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                  {schedule.weekday_schedule.map((dayIndex) => (
                    <Chip
                      key={dayIndex}
                      label={t(`pages.wateringSchedule.${WEEKDAY_KEYS[dayIndex]}`)}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  ))}
                </Box>
              </Box>
            )}

            {/* Interval */}
            {schedule.schedule_mode === 'interval' && schedule.interval_days != null && (
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  {t('pages.wateringSchedule.intervalDays')}
                </Typography>
                <Typography>{schedule.interval_days}</Typography>
              </Box>
            )}

            {/* Preferred Time */}
            {schedule.preferred_time && (
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  {t('pages.wateringSchedule.preferredTime')}
                </Typography>
                <Typography>{schedule.preferred_time}</Typography>
              </Box>
            )}

            {/* Application Method */}
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                {t('pages.wateringSchedule.applicationMethod')}
              </Typography>
              <Typography>
                {t(`enums.applicationMethod.${schedule.application_method}`)}
              </Typography>
            </Box>

            {/* Reminder Hours Before */}
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                {t('pages.wateringSchedule.reminderHoursBefore')}
              </Typography>
              <Typography>{schedule.reminder_hours_before}h</Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Phase Gantt Chart */}
      {entries.length > 0 && <PhaseGanttChart entries={entries} fertilizers={fertilizers} />}

      {/* Fertilizer Gantt Chart */}
      {entries.length > 0 && <FertilizerGanttChart entries={entries} fertilizers={fertilizers} />}

      {/* Delivery Channels per Phase */}
      {entriesWithChannels.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('pages.deliveryChannels.title')}
            </Typography>
            {entriesWithChannels.map((entry) => (
              <Box key={entry.key} sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                  <Chip
                    label={`#${entry.sequence_order}`}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={t(`enums.phaseName.${entry.phase_name}`)}
                    size="small"
                    color="primary"
                  />
                  <Typography variant="body2" color="text.secondary">
                    {t('pages.nutrientPlans.weeks')}: {entry.week_start}–{entry.week_end}
                  </Typography>
                </Box>
                <DeliveryChannelAccordion
                  channels={entry.delivery_channels}
                  fertilizers={fertilizers}
                />
              </Box>
            ))}
          </CardContent>
        </Card>
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

  const [plan, setPlan] = useState<NutrientPlan | null>(null);
  const [entries, setEntries] = useState<NutrientPlanPhaseEntry[]>([]);
  const [fertilizers, setFertilizers] = useState<Fertilizer[]>([]);
  const [tanks, setTanks] = useState<Tank[]>([]);
  const [validation, setValidation] = useState<PlanValidationResult | null>(null);
  const [validating, setValidating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState(0);
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

  const load = useCallback(async () => {
    if (!key) return;
    setLoading(true);
    try {
      const [p, e, f, tk] = await Promise.all([
        planApi.fetchNutrientPlan(key),
        planApi.fetchPhaseEntries(key),
        fertApi.fetchFertilizers(0, 200),
        tankApi.listTanks(0, 200),
      ]);
      setPlan(p);
      setEntries(e);
      setFertilizers(f);
      setTanks(tk);
      const ws = p.watering_schedule;
      reset({
        name: p.name,
        description: p.description,
        recommended_substrate_type: p.recommended_substrate_type as typeof substrateTypes[number] | null,
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
      });
      setError(null);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
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
      });
      notification.success(t('common.save'));
      load();
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
      load();
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
      load();
    } catch (err) {
      handleError(err);
    }
  };

  const onSaveChannel = async (channel: DeliveryChannelCreate) => {
    if (!key || !channelDialogEntryKey) return;
    try {
      const entry = entries.find((e) => e.key === channelDialogEntryKey);
      if (!entry) return;
      const updatedChannels = [
        ...entry.delivery_channels.filter((ch) => ch.channel_id !== channel.channel_id),
        channel,
      ];
      await planApi.updatePhaseEntry(key, channelDialogEntryKey, {
        delivery_channels: updatedChannels,
      });
      notification.success(t('common.save'));
      setChannelDialogOpen(false);
      setEditingChannel(null);
      load();
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
      load();
    } catch (err) {
      handleError(err);
    }
  };

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
      load();
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
          alignItems: 'center',
          mb: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PageTitle title={plan.name} />
          {plan.is_template && (
            <Chip label={t('pages.nutrientPlans.isTemplate')} size="small" color="primary" />
          )}
        </Box>
        <Button
          variant="outlined"
          color="error"
          startIcon={<DeleteIcon />}
          onClick={() => setDeleteOpen(true)}
        >
          {t('common.delete')}
        </Button>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('pages.nutrientPlans.tabPhaseEntries')} />
        <Tab label={t('pages.nutrientPlans.tabValidation')} />
        <Tab label={t('pages.wateringSchedule.title')} />
        <Tab label={t('common.edit')} />
      </Tabs>

      {/* Tab 0: Phase Entries with CRUD */}
      {tab === 0 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                setEditingEntry(null);
                setEntryDialogOpen(true);
              }}
            >
              {t('pages.nutrientPlans.addEntry')}
            </Button>
          </Box>

          {entries.length === 0 ? (
            <Alert severity="info">{t('pages.nutrientPlans.noEntries')}</Alert>
          ) : (
            entries
              .sort((a, b) => a.sequence_order - b.sequence_order)
              .map((entry) => (
                <Card key={entry.key} sx={{ mb: 2 }}>
                  <CardContent sx={{ pb: 1 }}>
                    {/* Entry header row */}
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
                        <Chip
                          label={`#${entry.sequence_order}`}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          label={t(`enums.phaseName.${entry.phase_name}`)}
                          size="small"
                          color="primary"
                        />
                        <Typography variant="body2" color="text.secondary">
                          {t('pages.nutrientPlans.weeks')}: {entry.week_start}–{entry.week_end}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          NPK: {entry.npk_ratio[0]}-{entry.npk_ratio[1]}-{entry.npk_ratio[2]}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        <Tooltip title={t('pages.nutrientPlans.showFertilizers')}>
                          <IconButton
                            size="small"
                            onClick={() => toggleExpanded(entry.key)}
                          >
                            {expandedEntries.has(entry.key) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={t('common.edit')}>
                          <IconButton
                            size="small"
                            onClick={() => {
                              setEditingEntry(entry);
                              setEntryDialogOpen(true);
                            }}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={t('common.delete')}>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => {
                              setDeletingEntry(entry);
                              setDeleteEntryOpen(true);
                            }}
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
                              onClick={() => {
                                setChannelDialogEntryKey(entry.key);
                                setChannelDialogExistingIds(
                                  entry.delivery_channels.map((ch) => ch.channel_id),
                                );
                                setEditingChannel(null);
                                setChannelDialogOpen(true);
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
                              onEditChannel={(ch) =>
                                onEditChannel(entry.key, ch)
                              }
                              onDeleteChannel={(cid) => {
                                setDeletingChannelEntryKey(entry.key);
                                setDeletingChannelId(cid);
                                setDeleteChannelOpen(true);
                              }}
                              onAddFertilizer={(cid) =>
                                onAddChannelFertilizer(entry.key, cid)
                              }
                              onEditFertilizer={(cid, dosage) =>
                                onEditChannelFertilizer(entry.key, cid, dosage)
                              }
                              onRemoveFertilizer={(cid, fk) =>
                                onRemoveChannelFertilizer(entry.key, cid, fk)
                              }
                            />
                          )}
                        </ExpertiseFieldWrapper>
                      </Box>
                    </Collapse>
                  </CardContent>
                </Card>
              ))
          )}
        </Box>
      )}

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

              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {t('pages.nutrientPlans.ecBudgets')}
                  </Typography>
                  {(validation.ec_budgets ?? []).map((budget, i) => (
                    <Alert
                      key={i}
                      severity={budget.valid ? 'success' : 'error'}
                      sx={{ mb: 0.5 }}
                    >
                      <strong>{t(`enums.phaseName.${budget.phase_name}`)}</strong>:{' '}
                      {budget.message} ({t('pages.nutrientPlans.targetEc')}: {budget.target_ec},{' '}
                      {t('pages.nutrientPlans.calculatedEc')}: {budget.calculated_ec.toFixed(2)},{' '}
                      {t('pages.nutrientPlans.delta')}: {budget.delta.toFixed(2)})
                    </Alert>
                  ))}
                </CardContent>
              </Card>

              {/* Channel Validations */}
              {(validation.channel_validations ?? []).length > 0 && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {t('pages.deliveryChannels.validation.title')}
                    </Typography>
                    {(validation.channel_validations ?? []).map((cv, i) => (
                      <Box key={i} sx={{ mb: 1 }}>
                        <Typography variant="subtitle2">
                          {t(`enums.phaseName.${cv.phase_name}`)}
                        </Typography>
                        {(cv.channel_results ?? []).map((cr, j) => (
                          <Alert
                            key={j}
                            severity={cr.issues.length === 0 ? 'success' : 'error'}
                            sx={{ mb: 0.5 }}
                          >
                            <strong>{cr.label || cr.channel_id}</strong>:{' '}
                            {cr.issues.length === 0
                              ? t('pages.deliveryChannels.validation.noIssues')
                              : cr.issues.join('; ')}
                            {cr.ec_budget && (
                              <> ({t('pages.deliveryChannels.validation.ecBudget')}: {cr.ec_budget.target} / {cr.ec_budget.calculated})</>
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

      {/* Tab 2: Watering Schedule */}
      {tab === 2 && (
        <WateringScheduleTabContent plan={plan} entries={entries} fertilizers={fertilizers} />
      )}

      {/* Tab 3: Edit */}
      {tab === 3 && (
        <Card>
          <CardContent>
            <form onSubmit={handleSubmit(onSave)}>
              <FormTextField
                name="name"
                control={control}
                label={t('pages.nutrientPlans.name')}
                required
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

              {/* Watering Schedule Section */}
              <Box sx={{ mt: 3, mb: 2 }}>
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
              </Box>

              <FormActions
                onCancel={() => reset()}
                loading={saving}
                disabled={!isDirty}
              />
            </form>
          </CardContent>
        </Card>
      )}

      {/* Dialogs */}
      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: plan.name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
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
            load();
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
        tanks={tanks}
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
    </Box>
  );
}
