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
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
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
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import BuildOutlinedIcon from '@mui/icons-material/BuildOutlined';
import SearchIcon from '@mui/icons-material/Search';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import { useForm, Controller } from 'react-hook-form';
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
import type { WorkflowExecutionEnriched } from '@/api/endpoints/tasks';
import TaskTemplateDialog from './TaskTemplateDialog';
import Autocomplete from '@mui/material/Autocomplete';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemIcon from '@mui/material/ListItemIcon';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import FormControlLabel from '@mui/material/FormControlLabel';
import LinearProgress from '@mui/material/LinearProgress';
import * as favApi from '@/api/endpoints/favorites';

const entityTypes = ['plant_instance', 'planting_run', 'location', 'tank'] as const;

const editSchema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().nullable(),
  version: z.string(),
  tags: z.string(),
  target_entity_types: z.array(z.enum(entityTypes)).min(1),
});

type EditFormData = z.infer<typeof editSchema>;

export default function WorkflowDetailPage() {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
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

  // Executions (assigned plants/runs)
  const [executions, setExecutions] = useState<WorkflowExecutionEnriched[]>([]);
  const [hideInactive, setHideInactive] = useState(true);

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
  const [catalogFilter, setCatalogFilter] = useState<'all' | 'favorites' | 'compatible'>('all');
  const [activityFavKeys, setActivityFavKeys] = useState<Set<string>>(new Set());

  // Species selection
  type SpeciesOption = { key: string; scientific_name: string; common_names: string[]; plant_category: string | null; family_name: string | null };
  const [allSpecies, setAllSpecies] = useState<SpeciesOption[]>([]);
  const [speciesLoading, setSpeciesLoading] = useState(false);
  const [selectedSpecies, setSelectedSpecies] = useState<SpeciesOption[]>([]);
  const [favoriteKeys, setFavoriteKeys] = useState<Set<string>>(new Set());
  const [speciesFilter, setSpeciesFilter] = useState<'all' | 'favorites'>('all');

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<EditFormData>({
    resolver: zodResolver(editSchema),
    defaultValues: {
      name: '', description: null, version: '1.0', tags: '',
      target_entity_types: ['plant_instance'],
    },
  });

  const load = useCallback(async () => {
    if (!key) return;
    setLoading(true);
    try {
      const [wf, tts, execs] = await Promise.all([
        taskApi.getWorkflow(key),
        taskApi.listTaskTemplates(key),
        taskApi.listWorkflowExecutions(key),
      ]);
      setWorkflow(wf);
      setTemplates(tts);
      setExecutions(execs);
      reset({
        name: wf.name,
        description: wf.description,
        version: wf.version,
        tags: wf.tags.join(', '),
        target_entity_types: (wf.target_entity_types ?? ['plant_instance']) as EditFormData['target_entity_types'],
      });
      // Build dynamic breadcrumbs
      const crumbs: { label: string; path?: string }[] = [
        { label: 'nav.aufgaben', path: '/aufgaben' },
        { label: 'nav.workflows', path: '/aufgaben/workflows' },
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

  // Load all species + favorites for the compatible-species picker
  useEffect(() => {
    if (!workflow) return;
    setSpeciesLoading(true);
    Promise.all([
      speciesApi.listSpecies(0, 500),
      favApi.listFavorites('species').catch(() => []),
    ])
      .then(([res, favs]) => {
        const items: SpeciesOption[] = res.items.map((s) => ({
          key: s.key, scientific_name: s.scientific_name, common_names: s.common_names,
          plant_category: s.plant_category, family_name: s.family_name,
        }));
        setAllSpecies(items);
        setFavoriteKeys(new Set(favs.map((f) => f.target_key)));
        const compatNames = new Set(workflow.species_compatible ?? []);
        setSelectedSpecies(items.filter((s) => compatNames.has(s.scientific_name) || compatNames.has(s.key)));
      })
      .catch(() => setAllSpecies([]))
      .finally(() => setSpeciesLoading(false));
  }, [workflow]);

  const onSave = async (data: EditFormData) => {
    if (!key) return;
    try {
      setSaving(true);
      await taskApi.updateWorkflow(key, {
        name: data.name,
        description: data.description,
        version: data.version,
        tags: data.tags ? data.tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
        target_entity_types: data.target_entity_types,
        species_compatible: selectedSpecies.map((s) => s.scientific_name),
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
          displayName: tt.phase_display_name || (phase === '_unassigned' ? t('pages.tasks.unassignedPhase') : phase),
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
  }, [templates, t]);

  // Filtered species options based on active filter
  const filteredSpeciesOptions = useMemo(() => {
    let filtered = allSpecies;
    if (speciesFilter === 'favorites') {
      filtered = filtered.filter((s) => favoriteKeys.has(s.key));
    }
    // Sort: favorites first, then alphabetically
    return [...filtered].sort((a, b) => {
      const aFav = favoriteKeys.has(a.key) ? 0 : 1;
      const bFav = favoriteKeys.has(b.key) ? 0 : 1;
      if (aFav !== bFav) return aFav - bFav;
      return a.scientific_name.localeCompare(b.scientific_name);
    });
  }, [allSpecies, speciesFilter, favoriteKeys]);

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
      const [list, favs] = await Promise.all([
        activityApi.listActivities(),
        favApi.listFavorites('activities').catch(() => []),
      ]);
      setAllActivities(list);
      setActivityFavKeys(new Set(favs.map((f) => f.target_key)));
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
    setCatalogFilter('all');
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
  }, [selectedActivity, key, addTargetPhase, addTargetPhaseDisplay, addTargetPhaseDays, addTargetPhaseStress, addDayOffset, templates, load, handleError, notification, t]);

  // Filter activities for the dialog
  const filteredActivities = useMemo(() => {
    const compatSpecies = workflow?.species_compatible ?? [];

    let filtered = allActivities;

    // Apply catalog filter
    if (catalogFilter === 'favorites') {
      filtered = filtered.filter((a) => activityFavKeys.has(a.key));
    } else if (catalogFilter === 'compatible') {
      filtered = filtered.filter((a) => {
        // Universal activities (empty species_compatible) always match
        if (!a.species_compatible.length) return true;
        // Check if any workflow species matches any activity species_compatible entry
        return compatSpecies.some((ws) =>
          a.species_compatible.some((as_) =>
            ws.toLowerCase().includes(as_.toLowerCase()) || as_.toLowerCase().includes(ws.toLowerCase()),
          ),
        );
      });
    }

    // Apply text search
    if (activityFilter) {
      const lower = activityFilter.toLowerCase();
      filtered = filtered.filter((a) => {
        const name = i18n.language === 'de' && a.name_de ? a.name_de : a.name;
        const desc = i18n.language === 'de' && a.description_de ? a.description_de : a.description;
        const cat = t(`enums.activityCategory.${a.category}`, a.category);
        return name.toLowerCase().includes(lower)
          || desc.toLowerCase().includes(lower)
          || cat.toLowerCase().includes(lower)
          || a.tags.some((tag) => tag.toLowerCase().includes(lower));
      });
    }

    return filtered;
  }, [allActivities, activityFilter, catalogFilter, activityFavKeys, workflow?.species_compatible, i18n.language, t]);

  // Group executions: by planting_run if available, otherwise collect standalone plants
  type RunGroup = {
    groupKey: string;
    run: { key: string; name: string; status: string } | null;
    plants: { key: string; name: string; removed: boolean }[];
    species_name: string;
    avg_completion: number;
    all_completed: boolean;
    on_schedule: boolean;
  };

  const groupedByRun = useMemo((): RunGroup[] => {
    // Deduplicate executions per entity (keep latest)
    const latestPerEntity = new Map<string, WorkflowExecutionEnriched>();
    for (const ex of executions) {
      const existing = latestPerEntity.get(ex.entity_key);
      if (!existing || (ex.started_at ?? ex.key) > (existing.started_at ?? existing.key)) {
        latestPerEntity.set(ex.entity_key, ex);
      }
    }
    const unique = Array.from(latestPerEntity.values());

    // Group all executions as standalone entries (no run grouping needed)
    const entries = unique;
    const totalCompletion = entries.reduce((s, e) => s + e.completion_percentage, 0);
    if (entries.length === 0) return [];

    return [{
      groupKey: '__all__',
      run: null,
      plants: entries.map((e) => ({ key: e.entity_key, name: e.entity_name, removed: e.plant_removed })),
      species_name: entries[0]?.species_name ?? '',
      avg_completion: totalCompletion / entries.length,
      all_completed: entries.every((e) => e.completed_at !== null),
      on_schedule: entries.every((e) => e.on_schedule),
    }];
  }, [executions]);

  const filteredGroups = useMemo(() => {
    if (!hideInactive) return groupedByRun;
    return groupedByRun.filter((g) => {
      if (g.all_completed) return false;
      if (g.run && (g.run.status === 'cancelled' || g.run.status === 'completed')) return false;
      return g.plants.some((p) => !p.removed);
    });
  }, [groupedByRun, hideInactive]);

  const stressColors: Record<string, 'default' | 'success' | 'warning' | 'error'> = {
    none: 'default', low: 'success', medium: 'warning', high: 'error',
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} />;
  if (!workflow) return <ErrorDisplay error={t('errors.notFound')} />;

  return (
    <Box data-testid="workflow-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <PageTitle
        title={workflow.name}
        action={
          workflow.is_system ? <Chip label={t('pages.tasks.systemWorkflow')} color="info" variant="outlined" /> : undefined
        }
      />

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={t('pages.tasks.tabDetails')} />
        <Tab label={t('pages.tasks.taskTemplates')} />
        <Tab label={t('common.edit')} />
      </Tabs>

      {tab === 0 && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Card>
            <CardContent>
              <Table size="small" aria-label={t('pages.tasks.tabDetails')}>
                <TableBody>
                  <TableRow><TableCell component="th">{t('pages.tasks.version')}</TableCell><TableCell>{workflow.version}</TableCell></TableRow>
                  {workflow.description && <TableRow><TableCell component="th">{t('common.description')}</TableCell><TableCell>{workflow.description}</TableCell></TableRow>}
                  {workflow.tags.length > 0 && (
                    <TableRow><TableCell component="th">{t('pages.tasks.tags')}</TableCell><TableCell>{workflow.tags.map((tag) => <Chip key={tag} label={tag} size="small" sx={{ mr: 0.5 }} />)}</TableCell></TableRow>
                  )}
                  <TableRow>
                    <TableCell component="th">{t('pages.tasks.targetEntityTypes')}</TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                        {(workflow.target_entity_types ?? ['plant_instance']).map((et) => (
                          <Chip
                            key={et}
                            label={t(`pages.tasks.entityTypes.${et}`, { defaultValue: et })}
                            size="small"
                            color="info"
                            variant="outlined"
                          />
                        ))}
                      </Box>
                    </TableCell>
                  </TableRow>
                  {(workflow.species_compatible?.length ?? 0) > 0 && (
                    <TableRow>
                      <TableCell component="th">{t('pages.tasks.speciesCompatible')}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {workflow.species_compatible!.map((sp) => (
                            <Chip key={sp} label={sp} size="small" variant="outlined" icon={<LocalFloristIcon />} />
                          ))}
                        </Box>
                      </TableCell>
                    </TableRow>
                  )}
                  <TableRow><TableCell component="th">{t('pages.tasks.taskTemplates')}</TableCell><TableCell>{templates.length}</TableCell></TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Assigned Plants & Planting Runs */}
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="h6">
                  {t('pages.tasks.assignedExecutions')}
                  {' '}
                  <Chip label={filteredGroups.length} size="small" color="primary" />
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      size="small"
                      checked={hideInactive}
                      onChange={(_, v) => setHideInactive(v)}
                    />
                  }
                  label={t('pages.tasks.hideInactive')}
                />
              </Box>
              {filteredGroups.length === 0 ? (
                <Typography color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                  {hideInactive && executions.length > 0
                    ? t('pages.tasks.allExecutionsInactive')
                    : t('pages.tasks.noExecutions')}
                </Typography>
              ) : (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>{t('pages.tasks.plantingRun')}</TableCell>
                        <TableCell>{t('entities.species')}</TableCell>
                        <TableCell>{t('pages.runs.plantCount')}</TableCell>
                        <TableCell>{t('pages.tasks.progress')}</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {filteredGroups.map((g) => (
                        <TableRow
                          key={g.groupKey}
                          sx={{ opacity: g.all_completed ? 0.5 : 1 }}
                        >
                          <TableCell>
                            {g.run ? (
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                <Typography
                                  variant="body2"
                                  component="a"
                                  href={`/durchlaeufe/planting-runs/${g.run.key}`}
                                  onClick={(e) => { e.preventDefault(); navigate(`/durchlaeufe/planting-runs/${g.run!.key}`); }}
                                  sx={{ color: 'primary.main', textDecoration: 'none', cursor: 'pointer', '&:hover': { textDecoration: 'underline' } }}
                                >
                                  {g.run.name}
                                </Typography>
                                <Chip
                                  label={t(`enums.plantingRunStatus.${g.run.status}`, g.run.status)}
                                  size="small"
                                  variant="outlined"
                                  color={
                                    g.run.status === 'active' || g.run.status === 'harvesting' ? 'success'
                                      : g.run.status === 'cancelled' ? 'error'
                                      : g.run.status === 'completed' ? 'default'
                                      : 'warning'
                                  }
                                />
                              </Box>
                            ) : (
                              <Typography variant="body2" color="text.secondary">
                                {t('pages.runs.standalonePlants')}
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" color="text.secondary">
                              {g.species_name}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Tooltip
                              title={g.plants.map((p) => p.name).join(', ')}
                              arrow
                              placement="top"
                            >
                              <Chip
                                icon={<LocalFloristIcon />}
                                label={g.plants.length}
                                size="small"
                                variant="outlined"
                              />
                            </Tooltip>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 120 }}>
                              <LinearProgress
                                variant="determinate"
                                value={g.avg_completion}
                                sx={{ flexGrow: 1, height: 6, borderRadius: 3 }}
                                color={g.all_completed ? 'inherit' : g.on_schedule ? 'primary' : 'warning'}
                              />
                              <Typography variant="caption" sx={{ minWidth: 36, textAlign: 'right' }}>
                                {Math.round(g.avg_completion)}%
                              </Typography>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Box>
      )}

      {tab === 1 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mb: 2 }}>
            <Button
              variant="outlined"
              size="small"
              startIcon={<BuildOutlinedIcon />}
              onClick={() => { setEditTemplate(undefined); setTemplateDialogOpen(true); }}
            >
              {t('pages.tasks.createManually')}
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                const first = phaseGroups[0];
                if (first) {
                  handleOpenAddFromCatalog(first.phase, first.displayName, first.durationDays, first.stressTolerance);
                } else {
                  handleOpenAddFromCatalog('_unassigned', t('pages.tasks.unassignedPhase'), 0, '');
                }
              }}
            >
              {t('pages.tasks.addActivityFromCatalog')}
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
                                  {tt.activity_key ? (
                                    <Chip
                                      icon={<LocalFloristIcon sx={{ fontSize: 14 }} />}
                                      label={t('pages.tasks.sourceCatalog')}
                                      size="small"
                                      color="success"
                                      variant="outlined"
                                    />
                                  ) : (
                                    <Chip
                                      icon={<BuildOutlinedIcon sx={{ fontSize: 14 }} />}
                                      label={t('pages.tasks.sourceManual')}
                                      size="small"
                                      variant="outlined"
                                    />
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
      <Dialog fullScreen={fullScreen} open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {t('pages.tasks.addActivityToPhase', { phase: addTargetPhaseDisplay })}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            {/* Filter chips */}
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
              <Chip
                label={t('common.all')}
                size="small"
                variant={catalogFilter === 'all' ? 'filled' : 'outlined'}
                color={catalogFilter === 'all' ? 'primary' : 'default'}
                onClick={() => setCatalogFilter('all')}
              />
              <Chip
                icon={<StarIcon fontSize="small" />}
                label={t('common.favorites')}
                size="small"
                variant={catalogFilter === 'favorites' ? 'filled' : 'outlined'}
                color={catalogFilter === 'favorites' ? 'warning' : 'default'}
                onClick={() => setCatalogFilter('favorites')}
              />
              {(workflow?.species_compatible?.length ?? 0) > 0 && (
                <Chip
                  icon={<LocalFloristIcon fontSize="small" />}
                  label={t('pages.tasks.compatibleOnly')}
                  size="small"
                  variant={catalogFilter === 'compatible' ? 'filled' : 'outlined'}
                  color={catalogFilter === 'compatible' ? 'success' : 'default'}
                  onClick={() => setCatalogFilter('compatible')}
                />
              )}
            </Box>
            {/* Search */}
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
                <Controller
                  name="target_entity_types"
                  control={control}
                  render={({ field }) => (
                    <FormControl fullWidth sx={{ mb: 2 }}>
                      <InputLabel>{t('pages.tasks.targetEntityTypes')}</InputLabel>
                      <Select
                        {...field}
                        multiple
                        label={t('pages.tasks.targetEntityTypes')}
                        renderValue={(selected) => (
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                            {(selected as string[]).map((v) => (
                              <Chip key={v} label={t(`pages.tasks.entityTypes.${v}`)} size="small" />
                            ))}
                          </Box>
                        )}
                      >
                        {entityTypes.map((v) => (
                          <MenuItem key={v} value={v}>
                            {t(`pages.tasks.entityTypes.${v}`)}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  )}
                />
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" sx={{ mb: 1 }}>{t('pages.tasks.speciesCompatible')}</Typography>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1.5 }}>
                    <Chip
                      label={t('common.all')}
                      size="small"
                      variant={speciesFilter === 'all' ? 'filled' : 'outlined'}
                      color={speciesFilter === 'all' ? 'primary' : 'default'}
                      onClick={() => setSpeciesFilter('all')}
                    />
                    <Chip
                      icon={<StarIcon fontSize="small" />}
                      label={t('common.favorites')}
                      size="small"
                      variant={speciesFilter === 'favorites' ? 'filled' : 'outlined'}
                      color={speciesFilter === 'favorites' ? 'warning' : 'default'}
                      onClick={() => setSpeciesFilter('favorites')}
                    />
                  </Box>
                  <Autocomplete
                    multiple
                    options={filteredSpeciesOptions}
                    value={selectedSpecies}
                    onChange={(_, newValue) => setSelectedSpecies(newValue)}
                    getOptionLabel={(opt) => {
                      const common = opt.common_names?.[0];
                      return common ? `${common} (${opt.scientific_name})` : opt.scientific_name;
                    }}
                    isOptionEqualToValue={(opt, val) => opt.key === val.key}
                    loading={speciesLoading}
                    groupBy={(opt) => opt.plant_category ? t(`enums.plantCategory.${opt.plant_category}`, { defaultValue: opt.plant_category }) : t('common.other')}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        placeholder={t('common.search')}
                        helperText={t('pages.tasks.speciesCompatibleHelper')}
                        slotProps={{
                          input: {
                            ...params.InputProps,
                            endAdornment: (
                              <>
                                {speciesLoading ? <CircularProgress size={20} /> : null}
                                {params.InputProps.endAdornment}
                              </>
                            ),
                          },
                        }}
                      />
                    )}
                    renderOption={(props, opt) => {
                      const { key: liKey, ...liProps } = props;
                      const isFav = favoriteKeys.has(opt.key);
                      return (
                        <ListItem key={liKey} {...liProps} dense>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            {isFav ? <StarIcon fontSize="small" color="warning" /> : <StarBorderIcon fontSize="small" sx={{ opacity: 0.3 }} />}
                          </ListItemIcon>
                          <ListItemText
                            primary={opt.common_names?.[0] || opt.scientific_name}
                            secondary={opt.common_names?.[0] ? opt.scientific_name : opt.family_name}
                            slotProps={{ primary: { variant: 'body2' }, secondary: { variant: 'caption' } }}
                          />
                        </ListItem>
                      );
                    }}
                    renderTags={(value, getTagProps) =>
                      value.map((opt, index) => {
                        const { key: tagKey, ...tagProps } = getTagProps({ index });
                        return (
                          <Chip
                            key={tagKey}
                            icon={favoriteKeys.has(opt.key) ? <StarIcon fontSize="small" /> : undefined}
                            label={opt.common_names?.[0] || opt.scientific_name}
                            size="small"
                            {...tagProps}
                          />
                        );
                      })
                    }
                  />
                </Box>
                <Typography variant="caption" color="text.secondary">* {t('common.required')}</Typography>
                <FormActions onCancel={() => { reset(); setSelectedSpecies(allSpecies.filter((s) => (workflow?.species_compatible ?? []).includes(s.scientific_name) || (workflow?.species_compatible ?? []).includes(s.key))); }} loading={saving} disabled={!isDirty && selectedSpecies.map((s) => s.scientific_name).sort().join(',') === (workflow?.species_compatible ?? []).sort().join(',')} />
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
