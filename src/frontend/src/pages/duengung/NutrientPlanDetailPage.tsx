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
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ScienceIcon from '@mui/icons-material/Science';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormChipInput from '@/components/form/FormChipInput';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import PhaseEntryDialog from './PhaseEntryDialog';
import FertilizerDosageDialog from './FertilizerDosageDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as planApi from '@/api/endpoints/nutrient-plans';
import * as fertApi from '@/api/endpoints/fertilizers';
import type { NutrientPlan, NutrientPlanPhaseEntry, PlanValidationResult, Fertilizer, WateringSchedule } from '@/api/types';

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

const editSchema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().max(2000),
  recommended_substrate_type: z.enum(substrateTypes).nullable(),
  author: z.string().max(200),
  is_template: z.boolean(),
  version: z.string().max(50),
  tags: z.array(z.string()),
});

type EditFormData = z.infer<typeof editSchema>;

const WEEKDAY_KEYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] as const;

function WateringScheduleTabContent({ plan }: { plan: NutrientPlan }) {
  const { t } = useTranslation();

  // The watering_schedule may exist on the plan as an extra field from the backend
  const schedule = (plan as NutrientPlan & { watering_schedule?: WateringSchedule }).watering_schedule;

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

  return (
    <Card data-testid="watering-schedule-tab">
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

  // Fertilizer dosage dialog state
  const [dosageDialogOpen, setDosageDialogOpen] = useState(false);
  const [dosageEntryKey, setDosageEntryKey] = useState<string>('');
  const [dosageExisting, setDosageExisting] = useState<NutrientPlanPhaseEntry['fertilizer_dosages']>([]);

  // Expanded rows for fertilizer dosages
  const [expandedEntries, setExpandedEntries] = useState<Set<string>>(new Set());

  const {
    control,
    handleSubmit,
    reset,
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
    },
  });

  const load = useCallback(async () => {
    if (!key) return;
    setLoading(true);
    try {
      const [p, e, f] = await Promise.all([
        planApi.fetchNutrientPlan(key),
        planApi.fetchPhaseEntries(key),
        fertApi.fetchFertilizers(0, 200),
      ]);
      setPlan(p);
      setEntries(e);
      setFertilizers(f);
      reset({
        name: p.name,
        description: p.description,
        recommended_substrate_type: p.recommended_substrate_type as typeof substrateTypes[number] | null,
        author: p.author,
        is_template: p.is_template,
        version: p.version,
        tags: p.tags,
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
      await planApi.updateNutrientPlan(key, {
        name: data.name,
        description: data.description,
        recommended_substrate_type: data.recommended_substrate_type,
        author: data.author,
        is_template: data.is_template,
        version: data.version,
        tags: data.tags,
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

  const onRemoveFertilizer = async (entryKey: string, fertilizerKey: string) => {
    if (!key) return;
    try {
      await planApi.removeFertilizerFromEntry(key, entryKey, fertilizerKey);
      notification.success(t('common.delete'));
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

  const getFertilizerName = (fertKey: string): string => {
    const f = fertilizers.find((fert) => fert.key === fertKey);
    return f ? `${f.product_name} (${f.brand})` : fertKey;
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
                        <Typography variant="body2" color="text.secondary">
                          EC: {entry.target_ec_ms} mS
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          pH: {entry.target_ph.toFixed(1)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {entry.feeding_frequency_per_week}x / {t('pages.nutrientPlans.week')}
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

                    {/* Additional details row */}
                    {(entry.calcium_ppm != null || entry.magnesium_ppm != null || entry.volume_per_feeding_liters != null || entry.notes) && (
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
                        {entry.volume_per_feeding_liters != null && (
                          <Typography variant="body2" color="text.secondary">
                            {t('pages.nutrientPlans.volumePerFeeding')}: {entry.volume_per_feeding_liters} L
                          </Typography>
                        )}
                        {entry.notes && (
                          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                            {entry.notes}
                          </Typography>
                        )}
                      </Box>
                    )}

                    {/* Expandable fertilizer dosages */}
                    <Collapse in={expandedEntries.has(entry.key)}>
                      <Box sx={{ mt: 2 }}>
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
                            {t('pages.nutrientPlans.fertilizerDosages')}
                          </Typography>
                          <Button
                            size="small"
                            startIcon={<AddIcon />}
                            onClick={() => {
                              setDosageEntryKey(entry.key);
                              setDosageExisting(entry.fertilizer_dosages);
                              setDosageDialogOpen(true);
                            }}
                          >
                            {t('pages.nutrientPlans.addFertilizer')}
                          </Button>
                        </Box>

                        {entry.fertilizer_dosages.length === 0 ? (
                          <Alert severity="info" variant="outlined" sx={{ py: 0.5 }}>
                            {t('pages.nutrientPlans.noFertilizers')}
                          </Alert>
                        ) : (
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>{t('entities.fertilizer')}</TableCell>
                                <TableCell align="right">{t('pages.nutrientPlans.mlPerLiter')}</TableCell>
                                <TableCell align="center">{t('common.optional')}</TableCell>
                                <TableCell align="right">{t('common.actions')}</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {entry.fertilizer_dosages.map((dosage) => (
                                <TableRow key={dosage.fertilizer_key}>
                                  <TableCell>{getFertilizerName(dosage.fertilizer_key)}</TableCell>
                                  <TableCell align="right">{dosage.ml_per_liter} ml/L</TableCell>
                                  <TableCell align="center">
                                    {dosage.optional ? (
                                      <Chip label={t('common.yes')} size="small" variant="outlined" />
                                    ) : (
                                      <Chip label={t('common.no')} size="small" />
                                    )}
                                  </TableCell>
                                  <TableCell align="right">
                                    <IconButton
                                      size="small"
                                      color="error"
                                      onClick={() => onRemoveFertilizer(entry.key, dosage.fertilizer_key)}
                                    >
                                      <DeleteIcon fontSize="small" />
                                    </IconButton>
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        )}
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
                  {validation.completeness.issues.map((issue, i) => (
                    <Alert key={i} severity="warning" sx={{ mb: 0.5 }}>
                      {issue}
                    </Alert>
                  ))}
                </CardContent>
              </Card>

              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {t('pages.nutrientPlans.ecBudgets')}
                  </Typography>
                  {validation.ec_budgets.map((budget, i) => (
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
            </>
          )}
        </Box>
      )}

      {/* Tab 2: Watering Schedule */}
      {tab === 2 && (
        <WateringScheduleTabContent plan={plan} />
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

      {key && (
        <FertilizerDosageDialog
          open={dosageDialogOpen}
          onClose={() => setDosageDialogOpen(false)}
          planKey={key}
          entryKey={dosageEntryKey}
          existingDosages={dosageExisting}
          onSaved={() => {
            setDosageDialogOpen(false);
            load();
          }}
        />
      )}
    </Box>
  );
}
