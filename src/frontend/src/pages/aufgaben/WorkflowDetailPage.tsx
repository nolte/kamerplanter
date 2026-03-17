import { useEffect, useState, useCallback, useMemo } from 'react';
import { useTabUrl } from '@/hooks/useTabUrl';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableContainer from '@mui/material/TableContainer';
import TableRow from '@mui/material/TableRow';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import IconButton from '@mui/material/IconButton';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Switch from '@mui/material/Switch';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import InputAdornment from '@mui/material/InputAdornment';
import CircularProgress from '@mui/material/CircularProgress';
import Collapse from '@mui/material/Collapse';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import SearchIcon from '@mui/icons-material/Search';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import FormTextField from '@/components/form/FormTextField';
import FormActions from '@/components/form/FormActions';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useAppDispatch } from '@/store/hooks';
import { setBreadcrumbs } from '@/store/slices/uiSlice';
import * as taskApi from '@/api/endpoints/tasks';
import * as activityApi from '@/api/endpoints/activities';
import * as speciesApi from '@/api/endpoints/species';
import type { WorkflowTemplate, TaskTemplate, Activity } from '@/api/types';
import TaskTemplateDialog from './TaskTemplateDialog';

const editSchema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().nullable(),
  version: z.string(),
  tags: z.string(),
});

type EditFormData = z.infer<typeof editSchema>;

export default function WorkflowDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [workflow, setWorkflow] = useState<WorkflowTemplate | null>(null);
  const [templates, setTemplates] = useState<TaskTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useTabUrl(['details', 'templates', 'edit']);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteTemplateKey, setDeleteTemplateKey] = useState<string | null>(null);
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  const [editTemplate, setEditTemplate] = useState<TaskTemplate | undefined>(undefined);

  // Add-from-catalog dialog state
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [addTargetPhase, setAddTargetPhase] = useState<string>('');
  const [addTargetPhaseDisplay, setAddTargetPhaseDisplay] = useState('');
  const [addTargetPhaseDays, setAddTargetPhaseDays] = useState(0);
  const [addTargetPhaseStress, setAddTargetPhaseStress] = useState('');
  const [allActivities, setAllActivities] = useState<Activity[]>([]);
  const [activitiesLoading, setActivitiesLoading] = useState(false);
  const [selectedActivity, setSelectedActivity] = useState<Activity | null>(null);
  const [addDayOffset, setAddDayOffset] = useState(0);
  const [activityFilter, setActivityFilter] = useState('');
  const [expandedDesc, setExpandedDesc] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      name: '', description: null, version: '1.0', tags: '',
    },
  });

  const load = useCallback(async () => {
    if (!key) return;
    setLoading(true);
    try {
      const [wf, tts] = await Promise.all([
        taskApi.getWorkflow(key),
        taskApi.listTaskTemplates(key),
      ]);
      setWorkflow(wf);
      setTemplates(tts);
      reset({
        name: wf.name,
        description: wf.description,
        version: wf.version,
        tags: wf.tags.join(', '),
      });
      // Build dynamic breadcrumbs
      const crumbs: { label: string; path?: string }[] = [
        { label: 'nav.dashboard', path: '/dashboard' },
        { label: 'nav.species', path: '/stammdaten/species' },
      ];
      if (wf.species_key) {
        try {
          const sp = await speciesApi.getSpecies(wf.species_key);
          crumbs.push({
            label: sp.common_names?.[0] || sp.scientific_name,
            path: `/stammdaten/species/${wf.species_key}#workflows`,
          });
        } catch { /* species may not resolve */ }
      }
      crumbs.push({ label: wf.name });
      dispatch(setBreadcrumbs(crumbs));
      setError(null);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [key, reset, dispatch]);

  useEffect(() => {
    load();
    return () => { dispatch(setBreadcrumbs([])); };
  }, [load, dispatch]);

  const onSave = async (data: EditFormData) => {
    if (!key) return;
    try {
      setSaving(true);
      await taskApi.updateWorkflow(key, {
        name: data.name,
        description: data.description,
        version: data.version,
        tags: data.tags ? data.tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
      });
      notification.success(t('pages.tasks.workflowUpdated'));
      load();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const onDeleteWorkflow = async () => {
    if (!key) return;
    try {
      await taskApi.deleteWorkflow(key);
      notification.success(t('pages.tasks.workflowDeleted'));
      navigate('/aufgaben/workflows');
    } catch (err) {
      handleError(err);
    }
  };

  const onDeleteTemplate = async () => {
    if (!deleteTemplateKey) return;
    try {
      await taskApi.deleteTaskTemplate(deleteTemplateKey);
      notification.success(t('pages.tasks.taskTemplateDeleted'));
      setDeleteTemplateKey(null);
      load();
    } catch (err) {
      handleError(err);
    }
  };

  // Group templates by phase for the accordion view
  const phaseGroups = useMemo(() => {
    const groups: { phase: string; displayName: string; durationDays: number; stressTolerance: string; templates: TaskTemplate[] }[] = [];
    const phaseMap = new Map<string, typeof groups[0]>();
    for (const tt of templates) {
      const phase = tt.trigger_phase ?? '_unassigned';
      if (!phaseMap.has(phase)) {
        const group = {
          phase,
          displayName: tt.phase_display_name || phase,
          durationDays: tt.phase_duration_days || 0,
          stressTolerance: tt.phase_stress_tolerance || '',
          templates: [] as TaskTemplate[],
        };
        phaseMap.set(phase, group);
        groups.push(group);
      }
      phaseMap.get(phase)!.templates.push(tt);
    }
    // Sort templates within each group by days_offset
    for (const g of groups) {
      g.templates.sort((a, b) => a.days_offset - b.days_offset);
    }
    return groups;
  }, [templates]);

  const handleToggleEnabled = useCallback(async (tt: TaskTemplate) => {
    try {
      await taskApi.updateTaskTemplate(tt.key, { ...tt, enabled: !tt.enabled } as TaskTemplate);
      load();
    } catch (err) {
      handleError(err);
    }
  }, [load, handleError]);

  const handleDaysOffsetChange = useCallback(async (tt: TaskTemplate, newOffset: number) => {
    try {
      await taskApi.updateTaskTemplate(tt.key, { ...tt, days_offset: Math.max(0, newOffset) } as TaskTemplate);
      load();
    } catch (err) {
      handleError(err);
    }
  }, [load, handleError]);

  const handleDuplicate = useCallback(async (tt: TaskTemplate) => {
    try {
      await taskApi.createTaskTemplate({
        ...tt,
        workflow_template_key: key ?? null,
        days_offset: tt.days_offset + (tt.recovery_days || 1) + 1,
        sequence_order: tt.sequence_order + 1,
      });
      notification.success(t('pages.tasks.taskTemplateDuplicated'));
      load();
    } catch (err) {
      handleError(err);
    }
  }, [key, load, handleError, notification, t]);

  const loadActivities = useCallback(async () => {
    if (allActivities.length > 0) return;
    setActivitiesLoading(true);
    try {
      const list = await activityApi.listActivities();
      setAllActivities(list);
    } catch (err) {
      handleError(err);
    } finally {
      setActivitiesLoading(false);
    }
  }, [allActivities.length, handleError]);

  const handleOpenAddFromCatalog = useCallback((phase: string, phaseDisplay: string, phaseDays: number, phaseStress: string) => {
    setAddTargetPhase(phase);
    setAddTargetPhaseDisplay(phaseDisplay);
    setAddTargetPhaseDays(phaseDays);
    setAddTargetPhaseStress(phaseStress);
    setSelectedActivity(null);
    setAddDayOffset(0);
    setActivityFilter('');
    setExpandedDesc(null);
    setAddDialogOpen(true);
    loadActivities();
  }, [loadActivities]);

  const handleAddFromCatalog = useCallback(async () => {
    if (!selectedActivity || !key) return;
    const act = selectedActivity;
    const maxSeq = templates.reduce((max, tt) => Math.max(max, tt.sequence_order), 0);
    try {
      await taskApi.createTaskTemplate({
        name: act.name,
        name_de: act.name_de,
        instruction: act.description,
        instruction_de: act.description_de,
        description: act.description,
        description_de: act.description_de,
        category: act.category,
        trigger_type: 'phase_entry',
        trigger_phase: addTargetPhase,
        phase_display_name: addTargetPhaseDisplay,
        phase_duration_days: addTargetPhaseDays,
        phase_stress_tolerance: addTargetPhaseStress,
        days_offset: addDayOffset,
        stress_level: act.stress_level,
        skill_level: act.skill_level,
        estimated_duration_minutes: act.estimated_duration_minutes,
        tools_required: act.tools_required,
        activity_key: act.key,
        recovery_days: act.recovery_days_default,
        workflow_template_key: key,
        sequence_order: maxSeq + 1,
      } as TaskTemplate);
      notification.success(t('pages.tasks.taskTemplateCreated'));
      setAddDialogOpen(false);
      load();
    } catch (err) {
      handleError(err);
    }
  }, [selectedActivity, key, addTargetPhase, addDayOffset, templates, load, handleError, notification, t]);

  // Filter activities for the dialog
  const filteredActivities = useMemo(() => {
    if (!activityFilter) return allActivities;
    const lower = activityFilter.toLowerCase();
    return allActivities.filter((a) => {
      const name = i18n.language === 'de' && a.name_de ? a.name_de : a.name;
      const desc = i18n.language === 'de' && a.description_de ? a.description_de : a.description;
      const cat = t(`enums.activityCategory.${a.category}`, a.category);
      return name.toLowerCase().includes(lower)
        || desc.toLowerCase().includes(lower)
        || cat.toLowerCase().includes(lower)
        || a.tags.some((tag) => tag.toLowerCase().includes(lower));
    });
  }, [allActivities, activityFilter, i18n.language, t]);

  const stressColors: Record<string, 'default' | 'success' | 'warning' | 'error'> = {
    none: 'default', low: 'success', medium: 'warning', high: 'error',
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} />;
  if (!workflow) return <ErrorDisplay error={t('errors.notFound')} />;

  return (
    <Box data-testid="workflow-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <PageTitle title={workflow.name} />
        <Box sx={{ display: 'flex', gap: 1 }}>
          {workflow.is_system && <Chip label={t('pages.tasks.systemWorkflow')} color="info" variant="outlined" />}
        </Box>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('pages.tasks.tabDetails')} />
        <Tab label={t('pages.tasks.taskTemplates')} />
        <Tab label={t('common.edit')} />
      </Tabs>

      {tab === 0 && (
        <Card>
          <CardContent>
            <Table size="small" aria-label={t('pages.tasks.tabDetails')}>
              <TableBody>
                <TableRow><TableCell component="th">{t('pages.tasks.version')}</TableCell><TableCell>{workflow.version}</TableCell></TableRow>
                {workflow.description && <TableRow><TableCell component="th">{t('common.description')}</TableCell><TableCell>{workflow.description}</TableCell></TableRow>}
                {workflow.tags.length > 0 && (
                  <TableRow><TableCell component="th">{t('pages.tasks.tags')}</TableCell><TableCell>{workflow.tags.map((tag) => <Chip key={tag} label={tag} size="small" sx={{ mr: 0.5 }} />)}</TableCell></TableRow>
                )}
                <TableRow><TableCell component="th">{t('pages.tasks.taskTemplates')}</TableCell><TableCell>{templates.length}</TableCell></TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {tab === 1 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => { setEditTemplate(undefined); setTemplateDialogOpen(true); }}>
              {t('pages.tasks.addTaskTemplate')}
            </Button>
          </Box>

          {phaseGroups.length === 0 && (
            <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
              {t('pages.tasks.noTaskTemplates')}
            </Typography>
          )}

          {phaseGroups.map((group) => {
            const enabledCount = group.templates.filter((tt) => tt.enabled).length;
            return (
              <Accordion key={group.phase} defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      {group.displayName}
                    </Typography>
                    {group.durationDays > 0 && (
                      <Chip label={`${group.durationDays}d`} size="small" variant="outlined" />
                    )}
                    <Chip
                      label={`${enabledCount}/${group.templates.length}`}
                      size="small"
                      color={enabledCount > 0 ? 'primary' : 'default'}
                    />
                    {group.stressTolerance && (
                      <Chip
                        label={t(`enums.stressLevel.${group.stressTolerance}`, group.stressTolerance)}
                        size="small"
                        variant="outlined"
                        color={stressColors[group.stressTolerance] ?? 'default'}
                      />
                    )}
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell padding="checkbox" />
                          <TableCell>{t('common.name')}</TableCell>
                          <TableCell>{t('pages.tasks.dayOffset')}</TableCell>
                          <TableCell>{t('pages.tasks.stressLevel')}</TableCell>
                          <TableCell>{t('pages.tasks.estimatedDuration')}</TableCell>
                          <TableCell />
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {group.templates.map((tt) => {
                          const displayName = i18n.language === 'de' && tt.name_de ? tt.name_de : tt.name;
                          const desc = i18n.language === 'de' && tt.description_de ? tt.description_de : tt.description;
                          return (
                            <TableRow key={tt.key} sx={{ opacity: tt.enabled ? 1 : 0.4 }}>
                              <TableCell padding="checkbox">
                                <Switch
                                  size="small"
                                  checked={tt.enabled}
                                  onChange={() => handleToggleEnabled(tt)}
                                />
                              </TableCell>
                              <TableCell>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  {displayName}
                                  {desc && (
                                    <Tooltip
                                      title={<Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>{desc}</Typography>}
                                      arrow
                                      enterTouchDelay={0}
                                      leaveTouchDelay={5000}
                                    >
                                      <InfoOutlinedIcon sx={{ fontSize: 16, color: 'text.secondary', cursor: 'help' }} />
                                    </Tooltip>
                                  )}
                                  {tt.is_optional && (
                                    <Chip label={t('pages.activityPlan.optional')} size="small" color="warning" variant="outlined" />
                                  )}
                                </Box>
                              </TableCell>
                              <TableCell>
                                <TextField
                                  type="number"
                                  size="small"
                                  value={tt.days_offset}
                                  onChange={(e) => handleDaysOffsetChange(tt, Number(e.target.value))}
                                  inputProps={{ min: 0, style: { width: 48, textAlign: 'center', padding: '4px 4px' } }}
                                  variant="outlined"
                                  sx={{ '& .MuiOutlinedInput-root': { height: 30 } }}
                                />
                              </TableCell>
                              <TableCell>
                                <Chip
                                  label={t(`enums.stressLevel.${tt.stress_level}`, tt.stress_level)}
                                  size="small"
                                  color={stressColors[tt.stress_level] ?? 'default'}
                                  variant="outlined"
                                />
                              </TableCell>
                              <TableCell>
                                {tt.estimated_duration_minutes != null
                                  ? `${tt.estimated_duration_minutes} min`
                                  : '\u2014'}
                              </TableCell>
                              <TableCell>
                                <Box sx={{ display: 'flex', gap: 0 }}>
                                  <Tooltip title={t('pages.tasks.duplicateTemplate')}>
                                    <IconButton size="small" onClick={() => handleDuplicate(tt)}>
                                      <ContentCopyIcon sx={{ fontSize: 16 }} />
                                    </IconButton>
                                  </Tooltip>
                                  <Tooltip title={t('common.edit')}>
                                    <IconButton size="small" onClick={() => { setEditTemplate(tt); setTemplateDialogOpen(true); }}>
                                      <EditIcon sx={{ fontSize: 16 }} />
                                    </IconButton>
                                  </Tooltip>
                                  {tt.activity_key && (
                                    <Tooltip title={t('pages.tasks.openActivity')}>
                                      <IconButton size="small" onClick={() => navigate(`/stammdaten/activities/${tt.activity_key}`)}>
                                        <SearchIcon sx={{ fontSize: 16 }} />
                                      </IconButton>
                                    </Tooltip>
                                  )}
                                  <Tooltip title={t('common.delete')}>
                                    <IconButton size="small" color="error" onClick={() => setDeleteTemplateKey(tt.key)}>
                                      <DeleteIcon sx={{ fontSize: 16 }} />
                                    </IconButton>
                                  </Tooltip>
                                </Box>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </TableContainer>
                  <Box sx={{ mt: 1 }}>
                    <Button
                      size="small"
                      startIcon={<AddIcon />}
                      onClick={() => handleOpenAddFromCatalog(group.phase, group.displayName, group.durationDays, group.stressTolerance)}
                    >
                      {t('pages.tasks.addActivityFromCatalog')}
                    </Button>
                  </Box>
                </AccordionDetails>
              </Accordion>
            );
          })}
        </Box>
      )}

      {/* Add Activity from Catalog Dialog */}
      <Dialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {t('pages.tasks.addActivityToPhase', { phase: addTargetPhaseDisplay })}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            {/* Search/Filter */}
            <TextField
              size="small"
              placeholder={t('pages.tasks.searchActivities')}
              value={activityFilter}
              onChange={(e) => setActivityFilter(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              autoFocus
            />

            {activitiesLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
                <CircularProgress size={24} />
              </Box>
            ) : (
              <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                {filteredActivities.map((act) => {
                  const actName = i18n.language === 'de' && act.name_de ? act.name_de : act.name;
                  const actDesc = i18n.language === 'de' && act.description_de ? act.description_de : act.description;
                  const isSelected = selectedActivity?.key === act.key;
                  const isExpanded = expandedDesc === act.key;
                  return (
                    <Box
                      key={act.key}
                      sx={{
                        p: 1.5,
                        mb: 0.5,
                        borderRadius: 1,
                        cursor: 'pointer',
                        border: 1,
                        borderColor: isSelected ? 'primary.main' : 'divider',
                        bgcolor: isSelected ? 'action.selected' : 'transparent',
                        '&:hover': { bgcolor: isSelected ? 'action.selected' : 'action.hover' },
                      }}
                      onClick={() => setSelectedActivity(isSelected ? null : act)}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                          {actName}
                        </Typography>
                        <Chip
                          label={t(`enums.activityCategory.${act.category}`, act.category)}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          label={t(`enums.stressLevel.${act.stress_level}`, act.stress_level)}
                          size="small"
                          color={stressColors[act.stress_level] ?? 'default'}
                          variant="outlined"
                        />
                        <Chip
                          label={t(`enums.skillLevel.${act.skill_level}`, act.skill_level)}
                          size="small"
                          variant="outlined"
                        />
                        {act.estimated_duration_minutes && (
                          <Chip label={`${act.estimated_duration_minutes} min`} size="small" variant="outlined" />
                        )}
                        {act.tools_required.length > 0 && (
                          <Typography variant="caption" color="text.secondary">
                            {act.tools_required.join(', ')}
                          </Typography>
                        )}
                      </Box>
                      {actDesc && (
                        <Box sx={{ mt: 0.5 }}>
                          <Button
                            size="small"
                            variant="text"
                            sx={{ p: 0, minWidth: 0, textTransform: 'none', fontSize: '0.75rem' }}
                            onClick={(e) => { e.stopPropagation(); setExpandedDesc(isExpanded ? null : act.key); }}
                            endIcon={isExpanded ? <ExpandLessIcon sx={{ fontSize: 14 }} /> : <ExpandMoreIcon sx={{ fontSize: 14 }} />}
                          >
                            {t('pages.tasks.showDescription')}
                          </Button>
                          <Collapse in={isExpanded}>
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, whiteSpace: 'pre-line' }}>
                              {actDesc}
                            </Typography>
                          </Collapse>
                        </Box>
                      )}
                    </Box>
                  );
                })}
                {filteredActivities.length === 0 && (
                  <Typography color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                    {t('pages.tasks.noActivitiesFound')}
                  </Typography>
                )}
              </Box>
            )}

            {/* Day offset input — shown when activity is selected */}
            {selectedActivity && (
              <TextField
                label={t('pages.tasks.dayOffset')}
                type="number"
                size="small"
                value={addDayOffset}
                onChange={(e) => setAddDayOffset(Math.max(0, Number(e.target.value)))}
                inputProps={{ min: 0 }}
                helperText={t('pages.tasks.dayOffsetHelper')}
              />
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>
            {t('common.cancel')}
          </Button>
          <Button
            variant="contained"
            onClick={handleAddFromCatalog}
            disabled={!selectedActivity}
            startIcon={<AddIcon />}
          >
            {t('pages.tasks.addActivityFromCatalog')}
          </Button>
        </DialogActions>
      </Dialog>

      {tab === 2 && (
        <Box sx={{ maxWidth: 900, display: 'flex', flexDirection: 'column', gap: 4 }}>
          <Typography variant="body2" color="text.secondary">
            {t('pages.tasks.workflowEditIntro')}
          </Typography>

          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.tasks.sectionWorkflow')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.tasks.sectionWorkflowDesc')}
              </Typography>
              <form onSubmit={handleSubmit(onSave)}>
                <FormTextField name="name" control={control} label={t('pages.tasks.workflowName')} required autoFocus />
                <FormTextField name="description" control={control} label={t('common.description')} multiline rows={3} />
                <FormTextField name="version" control={control} label={t('pages.tasks.version')} />
                <FormTextField name="tags" control={control} label={t('pages.tasks.tags')} helperText={t('pages.tasks.tagsHelper')} />
                <Typography variant="caption" color="text.secondary">* {t('common.required')}</Typography>
                <FormActions onCancel={() => reset()} loading={saving} disabled={!isDirty} />
              </form>
            </CardContent>
          </Card>

          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={() => setDeleteOpen(true)}
              disabled={workflow.is_system}
            >
              {workflow.is_system ? t('pages.tasks.systemTemplateDeleteDisabled') : t('pages.tasks.deleteWorkflow')}
            </Button>
          </Box>
        </Box>
      )}

      <TaskTemplateDialog
        open={templateDialogOpen}
        onClose={() => { setTemplateDialogOpen(false); setEditTemplate(undefined); }}
        workflowKey={key ?? ''}
        template={editTemplate}
        onSaved={() => { setTemplateDialogOpen(false); setEditTemplate(undefined); load(); }}
      />

      <ConfirmDialog
        open={deleteOpen}
        title={t('pages.tasks.deleteWorkflow')}
        message={t('common.deleteConfirm', { name: workflow.name })}
        onConfirm={onDeleteWorkflow}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />

      <ConfirmDialog
        open={!!deleteTemplateKey}
        title={t('pages.tasks.deleteTaskTemplate')}
        message={t('common.deleteConfirm', { name: templates.find((t) => t.key === deleteTemplateKey)?.name ?? '' })}
        onConfirm={onDeleteTemplate}
        onCancel={() => setDeleteTemplateKey(null)}
        destructive
      />
    </Box>
  );
}
