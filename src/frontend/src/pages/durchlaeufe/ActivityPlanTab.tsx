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
import { alpha } from '@mui/material/styles';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import PlaylistAddCheckIcon from '@mui/icons-material/PlaylistAddCheck';
import BuildIcon from '@mui/icons-material/Build';
import TimerIcon from '@mui/icons-material/Timer';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as activityPlanApi from '@/api/endpoints/activityPlans';
import type { ActivityPlanResponse, TaskTemplateResponse } from '@/api/types';

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

/** Group flat templates into phases for accordion display. */
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
  // Sort each group by days_offset
  for (const group of map.values()) {
    group.templates.sort((a, b) => a.days_offset - b.days_offset);
  }
  return Array.from(map.values());
}

interface Props {
  speciesKey: string;
  /** When set, the "Apply" button applies to this run (all plants). */
  runKey?: string;
  /** When set, the "Apply" button applies to this single plant. */
  plantKey?: string;
  /** Current phase name of the plant — highlights the matching accordion. */
  currentPhaseName?: string;
}

export default function ActivityPlanTab({ speciesKey, runKey, plantKey, currentPhaseName }: Props) {
  const { t, i18n } = useTranslation();
  const { success } = useNotification();
  const { handleError } = useApiError();
  const [plan, setPlan] = useState<ActivityPlanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);

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

  // Auto-generate on mount
  useEffect(() => {
    if (speciesKey) {
      handleGenerate();
    }
  }, [speciesKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleToggle = useCallback(async (templateKey: string) => {
    if (!plan) return;
    const tt = plan.templates.find((t) => t.key === templateKey);
    if (!tt) return;
    try {
      const updated = await activityPlanApi.updateTaskTemplate(templateKey, {
        enabled: !tt.enabled,
      });
      setPlan((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          templates: prev.templates.map((t) => (t.key === templateKey ? updated : t)),
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
          templates: prev.templates.filter((t) => t.key !== templateKey),
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
          templates: prev.templates.map((t) => (t.key === templateKey ? updated : t)),
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
    } catch (err) {
      handleError(err);
    } finally {
      setApplying(false);
    }
  }, [plan, runKey, plantKey, success, handleError, t]);

  const phaseGroups = useMemo(() => (plan ? groupByPhase(plan.templates) : []), [plan]);
  const enabledCount = plan ? plan.templates.filter((t) => t.enabled).length : 0;

  const applyLabel = runKey
    ? t('pages.activityPlan.applyToRun')
    : t('pages.activityPlan.applyToPlant');

  const hasStressWarning = useCallback((tt: TaskTemplateResponse) => {
    const actStress = STRESS_RANK[tt.stress_level] ?? 0;
    const phaseTolerance = TOLERANCE_RANK[tt.phase_stress_tolerance] ?? 2;
    return actStress > phaseTolerance;
  }, []);

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
            {t('pages.activityPlan.noActivities')}
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
          {/* Summary header */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
              <Typography variant="h6">
                {plan.name}
              </Typography>
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
            const phaseEnabled = group.templates.filter((t) => t.enabled).length;
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
                                          <InfoOutlinedIcon sx={{ fontSize: 16, color: 'text.secondary', cursor: 'help' }} />
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
