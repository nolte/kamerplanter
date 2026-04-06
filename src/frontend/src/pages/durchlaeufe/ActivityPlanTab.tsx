import { useState, useCallback, useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import Chip from '@mui/material/Chip';
import Switch from '@mui/material/Switch';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Divider from '@mui/material/Divider';
import { alpha } from '@mui/material/styles';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import PlaylistAddCheckIcon from '@mui/icons-material/PlaylistAddCheck';
import BuildIcon from '@mui/icons-material/Build';
import TimerIcon from '@mui/icons-material/Timer';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import AssignmentIcon from '@mui/icons-material/Assignment';
import AlertTitle from '@mui/material/AlertTitle';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import LinkIcon from '@mui/icons-material/Link';
import { Link } from 'react-router-dom';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as activityPlanApi from '@/api/endpoints/activityPlans';
import * as taskApi from '@/api/endpoints/tasks';
import type { ActivityPlanResponse, TaskTemplateResponse, TaskItem } from '@/api/types';

// ── Shared color maps ───────────────────────────────────────────────

const stressColors: Record<string, 'default' | 'success' | 'warning' | 'error'> = {
  none: 'default',
  low: 'success',
  medium: 'warning',
  high: 'error',
};

const categoryColors: Record<string, 'default' | 'primary' | 'secondary' | 'warning' | 'info'> = {
  training_hst: 'error' as 'default',
  training_lst: 'warning',
  pruning: 'secondary',
  transplant: 'primary',
  harvest_prep: 'info',
  inspection: 'info',
  general: 'default',
  ausgeizen: 'secondary',
  propagation: 'info',
};

const STRESS_RANK: Record<string, number> = { none: 0, low: 1, medium: 2, high: 3 };
const TOLERANCE_RANK: Record<string, number> = { low: 1, medium: 2, high: 3 };

// ── Plan mode types ─────────────────────────────────────────────────

interface PhaseGroup {
  phaseName: string;
  phaseDisplayName: string;
  phaseDurationDays: number;
  phaseStressTolerance: string;
  templates: TaskTemplateResponse[];
}

function groupByPhase(templates: TaskTemplateResponse[]): PhaseGroup[] {
  const map = new Map<string, PhaseGroup>();
  for (const tt of templates) {
    const key = tt.trigger_phase ?? '__none__';
    if (!map.has(key)) {
      map.set(key, {
        phaseName: tt.trigger_phase ?? '',
        phaseDisplayName: tt.phase_display_name || tt.trigger_phase || '',
        phaseDurationDays: tt.phase_duration_days,
        phaseStressTolerance: tt.phase_stress_tolerance,
        templates: [],
      });
    }
    map.get(key)!.templates.push(tt);
  }
  for (const group of map.values()) {
    group.templates.sort((a, b) => a.days_offset - b.days_offset);
  }
  return Array.from(map.values());
}

// ── Task group types (assigned tasks mode) ──────────────────────────

interface TaskGroup {
  name: string;
  templateKey: string | null;
  category: string;
  stressLevel: string;
  triggerPhase: string | null;
  instruction: string;
  tasks: TaskItem[];
}

function groupTasks(tasks: TaskItem[]): TaskGroup[] {
  const map = new Map<string, TaskGroup>();
  for (const task of tasks) {
    const groupKey = task.template_key ?? task.name;
    if (!map.has(groupKey)) {
      map.set(groupKey, {
        name: task.name,
        templateKey: task.template_key,
        category: task.category,
        stressLevel: task.stress_level,
        triggerPhase: task.trigger_phase,
        instruction: task.instruction,
        tasks: [],
      });
    }
    map.get(groupKey)!.tasks.push(task);
  }
  return Array.from(map.values());
}

interface PhaseTaskGroups {
  phaseName: string;
  groups: TaskGroup[];
}

function groupTasksByPhase(taskGroups: TaskGroup[], t: (key: string) => string): PhaseTaskGroups[] {
  const phaseMap = new Map<string, TaskGroup[]>();
  for (const group of taskGroups) {
    const phase = group.triggerPhase ?? '__none__';
    if (!phaseMap.has(phase)) {
      phaseMap.set(phase, []);
    }
    phaseMap.get(phase)!.push(group);
  }
  return Array.from(phaseMap.entries()).map(([phase, groups]) => ({
    phaseName: phase === '__none__' ? t('pages.activityPlan.noPhase') : phase,
    groups,
  }));
}

type StatusColor = 'success' | 'info' | 'default' | 'error';

function getCompletionColor(tasks: TaskItem[]): StatusColor {
  const completed = tasks.filter((t) => t.status === 'completed').length;
  const hasOverdue = tasks.some(
    (t) => t.due_date && new Date(t.due_date) < new Date() && t.status !== 'completed' && t.status !== 'skipped',
  );
  if (hasOverdue) return 'error';
  if (completed === tasks.length) return 'success';
  if (tasks.some((t) => t.status === 'in_progress')) return 'info';
  return 'default';
}

// ── Props ───────────────────────────────────────────────────────────

interface Props {
  speciesKey: string;
  /** When set, the "Apply" button applies to this run (all plants). */
  runKey?: string;
  /** When set, the "Apply" button applies to this single plant. */
  plantKey?: string;
  /** Current phase name of the plant — highlights the matching accordion. */
  currentPhaseName?: string;
}

// ── Component ───────────────────────────────────────────────────────

export default function ActivityPlanTab({ speciesKey, runKey, plantKey, currentPhaseName }: Props) {
  const { t, i18n } = useTranslation();
  const { success } = useNotification();
  const { handleError } = useApiError();

  // Assigned tasks state
  const [assignedTasks, setAssignedTasks] = useState<TaskItem[]>([]);
  const [loadingTasks, setLoadingTasks] = useState(true);
  const [tasksLoaded, setTasksLoaded] = useState(false);

  // Plan generation state (fallback)
  const [plan, setPlan] = useState<ActivityPlanResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);

  // ── Load assigned tasks ───────────────────────────────────────────

  const loadAssignedTasks = useCallback(async () => {
    if (!runKey && !plantKey) {
      setLoadingTasks(false);
      setTasksLoaded(true);
      return;
    }
    setLoadingTasks(true);
    try {
      const filters: { entity_type?: string; entity_key?: string } = {};
      if (runKey) {
        filters.entity_type = 'planting_run';
        filters.entity_key = runKey;
      } else if (plantKey) {
        filters.entity_type = 'plant_instance';
        filters.entity_key = plantKey;
      }
      const tasks = await taskApi.listTasks(0, 200, filters);
      setAssignedTasks(tasks);
    } catch (err) {
      handleError(err);
    } finally {
      setLoadingTasks(false);
      setTasksLoaded(true);
    }
  }, [runKey, plantKey, handleError]);

  useEffect(() => {
    loadAssignedTasks();
  }, [loadAssignedTasks]);

  // ── Plan generation (fallback) ────────────────────────────────────

  const handleGenerate = useCallback(async (forceRegenerate = false) => {
    setLoading(true);
    try {
      const result = await activityPlanApi.generatePlan({
        species_key: speciesKey,
        force_regenerate: forceRegenerate,
      });
      setPlan(result);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }, [speciesKey, handleError]);

  const handleToggle = useCallback(async (templateKey: string) => {
    if (!plan) return;
    const tt = plan.templates.find((tmpl) => tmpl.key === templateKey);
    if (!tt) return;
    try {
      const updated = await activityPlanApi.updateTaskTemplate(templateKey, {
        enabled: !tt.enabled,
      });
      setPlan((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          templates: prev.templates.map((tmpl) => (tmpl.key === templateKey ? updated : tmpl)),
        };
      });
    } catch (err) {
      handleError(err);
    }
  }, [plan, handleError]);

  const handleRemoveTemplate = useCallback(async (templateKey: string) => {
    try {
      await activityPlanApi.deleteTaskTemplate(templateKey);
      setPlan((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          templates: prev.templates.filter((tmpl) => tmpl.key !== templateKey),
          total_activities: prev.total_activities - 1,
        };
      });
    } catch (err) {
      handleError(err);
    }
  }, [handleError]);

  const handleDayOffsetChange = useCallback(async (templateKey: string, newOffset: number) => {
    try {
      const updated = await activityPlanApi.updateTaskTemplate(templateKey, {
        days_offset: Math.max(0, newOffset),
      });
      setPlan((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          templates: prev.templates.map((tmpl) => (tmpl.key === templateKey ? updated : tmpl)),
        };
      });
    } catch (err) {
      handleError(err);
    }
  }, [handleError]);

  const handleApply = useCallback(async () => {
    if (!plan) return;
    setApplying(true);
    try {
      const result = await activityPlanApi.applyPlan({
        workflow_template_key: plan.workflow_template_key,
        run_key: runKey ?? undefined,
        plant_key: plantKey ?? undefined,
      });
      success(t('pages.activityPlan.successMessage', {
        count: result.total_tasks ?? result.created_count,
      }));
      // Reload assigned tasks after applying
      await loadAssignedTasks();
    } catch (err) {
      handleError(err);
    } finally {
      setApplying(false);
    }
  }, [plan, runKey, plantKey, success, handleError, t, loadAssignedTasks]);

  // ── Computed values ───────────────────────────────────────────────

  const hasAssignedTasks = assignedTasks.length > 0;
  const taskGroups = useMemo(() => groupTasks(assignedTasks), [assignedTasks]);
  const phaseTaskGroups = useMemo(() => groupTasksByPhase(taskGroups, t), [taskGroups, t]);
  const phaseGroups = useMemo(() => (plan ? groupByPhase(plan.templates) : []), [plan]);
  const enabledCount = plan ? plan.templates.filter((tmpl) => tmpl.enabled).length : 0;

  const applyLabel = runKey
    ? t('pages.activityPlan.applyToRun')
    : t('pages.activityPlan.applyToPlant');

  const hasStressWarning = useCallback((tt: TaskTemplateResponse) => {
    const actStress = STRESS_RANK[tt.stress_level] ?? 0;
    const phaseTolerance = TOLERANCE_RANK[tt.phase_stress_tolerance] ?? 2;
    return actStress > phaseTolerance;
  }, []);

  // ── Loading state ─────────────────────────────────────────────────

  if (loadingTasks && !tasksLoaded) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 1, py: 6 }}>
        <CircularProgress size={24} />
        <Typography variant="body1" color="text.secondary">
          {t('pages.activityPlan.loadingTasks')}
        </Typography>
      </Box>
    );
  }

  // ── Assigned tasks view ───────────────────────────────────────────

  if (hasAssignedTasks) {
    return (
      <Box>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            <AssignmentIcon color="primary" />
            <Typography variant="h6">
              {t('pages.activityPlan.assignedTasks')}
            </Typography>
            <Chip
              label={`${assignedTasks.filter((task) => task.status === 'completed').length}/${assignedTasks.length}`}
              size="small"
              color={getCompletionColor(assignedTasks)}
            />
            {assignedTasks.some((task) => task.workflow_execution_key) && (
              <Chip
                icon={<LinkIcon />}
                label={t('pages.activityPlan.basedOnWorkflow')}
                size="small"
                color="info"
                variant="outlined"
                component={Link}
                to="/aufgaben/workflows"
                clickable
                data-testid="workflow-origin-chip"
                aria-label={t('pages.activityPlan.viewWorkflows')}
              />
            )}
          </Box>
        </Box>

        {/* Phase accordions with task groups */}
        {phaseTaskGroups.map((phaseGroup) => {
          const isCurrentPhase = currentPhaseName != null && phaseGroup.phaseName === currentPhaseName;
          const phaseTasks = phaseGroup.groups.flatMap((g) => g.tasks);
          const phaseCompleted = phaseTasks.filter((task) => task.status === 'completed').length;

          return (
            <Accordion
              key={phaseGroup.phaseName}
              defaultExpanded={isCurrentPhase || phaseGroup.groups.length > 0}
              sx={isCurrentPhase ? (theme) => ({
                border: 2,
                borderColor: 'primary.main',
                '& .MuiAccordionSummary-root': {
                  bgcolor: alpha(theme.palette.primary.main, 0.08),
                },
                '& .MuiAccordionSummary-root.Mui-expanded': {
                  bgcolor: alpha(theme.palette.primary.main, 0.08),
                },
              }) : undefined}
            >
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                    {t(`enums.phaseName.${phaseGroup.phaseName}`, phaseGroup.phaseName)}
                  </Typography>
                  {isCurrentPhase && (
                    <Chip label={t('pages.activityPlan.currentPhase')} size="small" color="primary" />
                  )}
                  <Chip
                    label={t('pages.activityPlan.completedOf', {
                      completed: phaseCompleted,
                      total: phaseTasks.length,
                    })}
                    size="small"
                    color={getCompletionColor(phaseTasks)}
                  />
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <List disablePadding>
                  {phaseGroup.groups.map((group, idx) => {
                    const completedCount = group.tasks.filter((task) => task.status === 'completed').length;
                    const totalCount = group.tasks.length;
                    const completionColor = getCompletionColor(group.tasks);
                    const instructionText = i18n.language === 'de'
                      ? (group.tasks[0]?.instruction_de || group.instruction)
                      : group.instruction;
                    const displayName = i18n.language === 'de'
                      ? (group.tasks[0]?.name_de || group.name)
                      : group.name;

                    return (
                      <Box key={group.templateKey ?? group.name}>
                        {idx > 0 && <Divider />}
                        <ListItem sx={{ py: 1.5 }}>
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                                <Typography variant="body1" sx={{ fontWeight: 500 }}>
                                  {displayName}
                                </Typography>
                                <Chip
                                  label={t(`enums.taskCategory.${group.category}`, group.category)}
                                  size="small"
                                  color={categoryColors[group.category] ?? 'default'}
                                />
                                <Chip
                                  label={t(`enums.stressLevel.${group.stressLevel}`, group.stressLevel)}
                                  size="small"
                                  variant="outlined"
                                  color={stressColors[group.stressLevel] ?? 'default'}
                                />
                                <Chip
                                  icon={<CheckCircleOutlineIcon />}
                                  label={t('pages.activityPlan.completedOf', {
                                    completed: completedCount,
                                    total: totalCount,
                                  })}
                                  size="small"
                                  color={completionColor}
                                  variant={completionColor === 'default' ? 'outlined' : 'filled'}
                                />
                              </Box>
                            }
                            secondary={instructionText || undefined}
                            secondaryTypographyProps={{ sx: { mt: 0.5 } }}
                          />
                        </ListItem>
                      </Box>
                    );
                  })}
                </List>
              </AccordionDetails>
            </Accordion>
          );
        })}
      </Box>
    );
  }

  // ── Fallback: Generate plan flow ──────────────────────────────────

  return (
    <Box>
      {!plan && loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 1, py: 6 }}>
          <CircularProgress size={24} />
          <Typography variant="body1" color="text.secondary">
            {t('pages.activityPlanOverview.generating')}
          </Typography>
        </Box>
      )}

      {!plan && !loading && (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 6 }}>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            {t('pages.activityPlan.noAssignedTasks')}
          </Typography>
          <Button
            variant="contained"
            startIcon={<AutoFixHighIcon />}
            onClick={() => handleGenerate()}
            disabled={!speciesKey}
            data-testid="generate-activity-plan-button"
          >
            {t('pages.activityPlan.generateButton')}
          </Button>
        </Box>
      )}

      {plan && (
        <>
          {/* Workflow hint banner */}
          <Alert severity="info" sx={{ mb: 2 }}>
            <AlertTitle>{t('pages.activityPlan.workflowHintTitle')}</AlertTitle>
            {t('pages.activityPlan.workflowHintText')}{' '}
            <Link
              to={`/aufgaben/workflows/${plan.workflow_template_key}`}
              data-testid="workflow-hint-link"
              style={{ color: 'inherit', fontWeight: 600 }}
            >
              {t('pages.activityPlan.openWorkflow')}
            </Link>
          </Alert>

          {/* Summary header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
              <Link
                to={`/aufgaben/workflows/${plan.workflow_template_key}#templates`}
                data-testid="workflow-plan-name-link"
                style={{ textDecoration: 'none', color: 'inherit' }}
              >
                <Typography
                  variant="h6"
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 0.5,
                    '&:hover': { color: 'primary.main' },
                  }}
                >
                  {plan.name}
                  <OpenInNewIcon sx={{ fontSize: 16, verticalAlign: 'middle' }} />
                </Typography>
              </Link>
              <Chip label={`${plan.total_duration_days}d`} size="small" variant="outlined" icon={<TimerIcon />} />
              <Chip
                label={`${enabledCount}/${plan.total_activities}`}
                size="small"
                color={enabledCount > 0 ? 'primary' : 'default'}
              />
            </Box>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Button
                variant="outlined"
                startIcon={loading ? <CircularProgress size={20} /> : <AutoFixHighIcon />}
                onClick={() => handleGenerate(true)}
                disabled={loading}
                size="small"
              >
                {t('pages.activityPlan.generateButton')}
              </Button>
              <Button
                variant="contained"
                startIcon={applying ? <CircularProgress size={20} /> : <PlaylistAddCheckIcon />}
                onClick={handleApply}
                disabled={applying || enabledCount === 0}
              >
                {applyLabel}
              </Button>
            </Box>
          </Box>

          {/* Phase accordions */}
          {phaseGroups.map((group) => {
            const phaseEnabled = group.templates.filter((tmpl) => tmpl.enabled).length;
            const isCurrent = currentPhaseName != null && group.phaseName === currentPhaseName;
            const hasWarnings = group.templates.some(hasStressWarning);
            return (
              <Accordion
                key={group.phaseName}
                defaultExpanded={isCurrent || group.templates.length > 0}
                sx={isCurrent ? (theme) => ({
                  border: 2,
                  borderColor: 'primary.main',
                  '& .MuiAccordionSummary-root': {
                    bgcolor: alpha(theme.palette.primary.main, 0.08),
                  },
                  '& .MuiAccordionSummary-root.Mui-expanded': {
                    bgcolor: alpha(theme.palette.primary.main, 0.08),
                  },
                }) : undefined}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      {group.phaseDisplayName}
                    </Typography>
                    {isCurrent && (
                      <Chip label={t('pages.activityPlan.currentPhase')} size="small" color="primary" />
                    )}
                    <Chip
                      label={`${group.phaseDurationDays}d`}
                      size="small"
                      variant="outlined"
                    />
                    <Chip
                      label={`${phaseEnabled}/${group.templates.length}`}
                      size="small"
                      color={phaseEnabled > 0 ? 'primary' : 'default'}
                    />
                    <Tooltip title={t('pages.activityPlan.stressTolerance', { level: t(`enums.stressLevel.${group.phaseStressTolerance}`, group.phaseStressTolerance) })}>
                      <Chip
                        label={t(`enums.stressLevel.${group.phaseStressTolerance}`, group.phaseStressTolerance)}
                        size="small"
                        variant="outlined"
                        color={stressColors[group.phaseStressTolerance] ?? 'default'}
                      />
                    </Tooltip>
                    {hasWarnings && (
                      <Tooltip title={t('pages.activityPlan.warningStressExceedsTolerance')}>
                        <WarningAmberIcon color="warning" sx={{ fontSize: 20 }} />
                      </Tooltip>
                    )}
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  {group.templates.length === 0 ? (
                    <Alert severity="info" sx={{ mb: 1 }}>{t('pages.activityPlan.noActivitiesInPhase')}</Alert>
                  ) : (
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell padding="checkbox" />
                            <TableCell>{t('common.name')}</TableCell>
                            <TableCell>{t('pages.activityPlan.dayOffset')}</TableCell>
                            <TableCell>{t('enums.category')}</TableCell>
                            <TableCell>{t('pages.activityPlan.stressLevel')}</TableCell>
                            <TableCell>{t('pages.activityPlan.skillLevel')}</TableCell>
                            <TableCell>{t('pages.activityPlan.tools')}</TableCell>
                            <TableCell>{t('pages.activityPlan.rationale')}</TableCell>
                            <TableCell padding="checkbox" />
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {group.templates.map((tt) => {
                            const stressWarning = hasStressWarning(tt);
                            return (
                              <TableRow
                                key={tt.key}
                                sx={{
                                  opacity: tt.enabled ? 1 : 0.5,
                                  ...(stressWarning && tt.enabled ? { bgcolor: 'warning.light', '& td': { color: 'warning.contrastText' } } : {}),
                                }}
                              >
                                <TableCell padding="checkbox">
                                  <Switch
                                    size="small"
                                    checked={tt.enabled}
                                    onChange={() => handleToggle(tt.key)}
                                  />
                                </TableCell>
                                <TableCell>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                    {stressWarning && (
                                      <Tooltip title={t('pages.activityPlan.warningStressExceedsTolerance')}>
                                        <WarningAmberIcon color="warning" sx={{ fontSize: 16 }} />
                                      </Tooltip>
                                    )}
                                    {i18n.language === 'de' && tt.name_de
                                      ? tt.name_de
                                      : tt.name}
                                    {(() => {
                                      const desc = i18n.language === 'de' && tt.description_de
                                        ? tt.description_de
                                        : tt.description;
                                      return desc ? (
                                        <Tooltip
                                          title={<Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>{desc}</Typography>}
                                          arrow
                                          enterTouchDelay={0}
                                          leaveTouchDelay={5000}
                                        >
                                          <InfoOutlinedIcon
                                            tabIndex={0}
                                            role="button"
                                            aria-label={t('common.description')}
                                            sx={{ fontSize: 16, color: 'text.secondary', cursor: 'help' }}
                                          />
                                        </Tooltip>
                                      ) : null;
                                    })()}
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
                                    onChange={(e) => handleDayOffsetChange(tt.key, Number(e.target.value))}
                                    inputProps={{ min: 0, max: group.phaseDurationDays, style: { width: 48, textAlign: 'center', padding: '4px 4px' } }}
                                    variant="outlined"
                                    sx={{ '& .MuiOutlinedInput-root': { height: 30 } }}
                                  />
                                </TableCell>
                                <TableCell>
                                  <Chip
                                    label={t(`enums.activityCategory.${tt.category}`, tt.category)}
                                    size="small"
                                    color={categoryColors[tt.category] ?? 'default'}
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
                                  <Typography variant="caption">
                                    {t(`enums.skillLevel.${tt.skill_level}`, tt.skill_level)}
                                  </Typography>
                                </TableCell>
                                <TableCell>
                                  {tt.tools_required.length > 0 && (
                                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                                      {tt.tools_required.map((tool) => (
                                        <Chip key={tool} icon={<BuildIcon />} label={tool} size="small" variant="outlined" />
                                      ))}
                                    </Box>
                                  )}
                                </TableCell>
                                <TableCell>
                                  <Typography variant="caption" color="text.secondary">
                                    {i18n.language === 'de' && tt.rationale_de
                                      ? tt.rationale_de
                                      : tt.rationale}
                                  </Typography>
                                </TableCell>
                                <TableCell padding="checkbox">
                                  <Tooltip title={t('pages.activityPlan.removeActivity')}>
                                    <IconButton
                                      size="small"
                                      color="error"
                                      onClick={() => handleRemoveTemplate(tt.key)}
                                    >
                                      <DeleteOutlineIcon sx={{ fontSize: 16 }} />
                                    </IconButton>
                                  </Tooltip>
                                </TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  )}
                </AccordionDetails>
              </Accordion>
            );
          })}
        </>
      )}
    </Box>
  );
}
