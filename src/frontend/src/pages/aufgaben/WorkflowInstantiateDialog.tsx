import { useEffect, useState, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import Chip from '@mui/material/Chip';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as taskApi from '@/api/endpoints/tasks';
import * as plantApi from '@/api/endpoints/plantInstances';
import * as plantingRunApi from '@/api/endpoints/plantingRuns';
import type {
  PlantInstance,
  PlantingRun,
  PlantInRun,
  TaskTemplate,
} from '@/api/types';

// ── Types ────────────────────────────────────────────────────────────

type SelectionTarget =
  | { type: 'plant'; plant: PlantInstance }
  | { type: 'run'; run: PlantingRun; plants: PlantInRun[] };

// ── Props ────────────────────────────────────────────────────────────

interface Props {
  open: boolean;
  workflowKey: string;
  onClose: () => void;
  onInstantiated: () => void;
}

// ── Helper: format date for display ──────────────────────────────────

function formatDate(iso: string | null, locale: string): string {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString(locale, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return iso;
  }
}

// ── Component ────────────────────────────────────────────────────────

export default function WorkflowInstantiateDialog({
  open,
  workflowKey,
  onClose,
  onInstantiated,
}: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t, i18n } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();

  const [plants, setPlants] = useState<PlantInstance[]>([]);
  const [runs, setRuns] = useState<PlantingRun[]>([]);
  const [runPlantsMap, setRunPlantsMap] = useState<
    Record<string, PlantInRun[]>
  >({});
  const [templates, setTemplates] = useState<TaskTemplate[]>([]);
  const [selectedTarget, setSelectedTarget] = useState<SelectionTarget | null>(
    null,
  );
  const [loading, setLoading] = useState(false);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [saving, setSaving] = useState(false);
  const [batchProgress, setBatchProgress] = useState<{
    current: number;
    total: number;
  } | null>(null);

  // ── Load data on open ────────────────────────────────────────────

  useEffect(() => {
    if (!open) return;

    let cancelled = false;

    const loadData = async () => {
      setLoading(true);
      try {
        // Load plants first — always needed
        const plantsData = await plantApi.listPlantInstances(0, 200);
        if (cancelled) return;
        setPlants(plantsData);

        // Load runs separately — failure should not block plant display
        let activeRuns: PlantingRun[] = [];
        try {
          const runsData = await plantingRunApi.listPlantingRuns(0, 200);
          if (cancelled) return;
          activeRuns = runsData.filter(
            (r) => r.status === 'active' || r.status === 'harvesting',
          );
        } catch {
          // Runs not available — continue with standalone plants only
          if (!cancelled) setLoading(false);
          return;
        }

        // Load plants for each run — individual failures are tolerated
        const plantsMap: Record<string, PlantInRun[]> = {};
        await Promise.all(
          activeRuns.map(async (run) => {
            try {
              const runPlants = await plantingRunApi.listRunPlants(run.key);
              plantsMap[run.key] = runPlants;
            } catch {
              // Skip this run if its plants can't be loaded
            }
          }),
        );

        if (cancelled) return;

        // Only include runs that have loaded plants
        setRuns(activeRuns.filter((r) => r.key in plantsMap));
        setRunPlantsMap(plantsMap);
      } catch (err) {
        if (!cancelled) handleError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    const loadTemplates = async () => {
      setLoadingTemplates(true);
      try {
        const data = await taskApi.listTaskTemplates(workflowKey);
        if (!cancelled) setTemplates(data);
      } catch (err) {
        if (!cancelled) handleError(err);
      } finally {
        if (!cancelled) setLoadingTemplates(false);
      }
    };

    loadData();
    loadTemplates();

    return () => {
      cancelled = true;
    };
  }, [open, workflowKey, handleError]);

  // ── Build unified options ────────────────────────────────────────

  const options = useMemo<SelectionTarget[]>(() => {
    // Collect all plant keys that belong to any run
    const runPlantKeys = new Set<string>();
    for (const runPlants of Object.values(runPlantsMap)) {
      for (const p of runPlants) {
        runPlantKeys.add(p.key);
      }
    }

    // Run options first
    const runOptions: SelectionTarget[] = runs.map((run) => ({
      type: 'run' as const,
      run,
      plants: (runPlantsMap[run.key] ?? []).filter(
        (p) => !p.detached_at && !p.removed_on,
      ),
    }));

    // Standalone plant options (not in any run, not removed)
    const standalonePlantOptions: SelectionTarget[] = plants
      .filter((p) => !runPlantKeys.has(p.key) && !p.removed_on)
      .map((plant) => ({
        type: 'plant' as const,
        plant,
      }));

    return [...runOptions, ...standalonePlantOptions];
  }, [plants, runs, runPlantsMap]);

  // ── Option label ─────────────────────────────────────────────────

  const getOptionLabel = useCallback(
    (option: SelectionTarget): string => {
      if (option.type === 'run') {
        const count = option.plants.length;
        return `${option.run.name} (${t('pages.tasks.runPlantCount', { count })})`;
      }
      const p = option.plant;
      return p.plant_name
        ? `${p.instance_id} - ${p.plant_name}`
        : p.instance_id;
    },
    [t],
  );

  // ── Instantiate handler ──────────────────────────────────────────

  const handleInstantiate = useCallback(async () => {
    if (!selectedTarget) return;

    setSaving(true);
    setBatchProgress(null);

    try {
      if (selectedTarget.type === 'plant') {
        await taskApi.instantiateWorkflow(workflowKey, {
          plant_key: selectedTarget.plant.key,
        });
        notification.success(t('pages.tasks.workflowInstantiated'));
      } else {
        // Batch instantiation for run plants
        const activePlants = selectedTarget.plants;
        const total = activePlants.length;
        let successCount = 0;
        const failures: string[] = [];

        for (let i = 0; i < activePlants.length; i++) {
          setBatchProgress({ current: i + 1, total });
          try {
            await taskApi.instantiateWorkflow(workflowKey, {
              plant_key: activePlants[i].key,
            });
            successCount++;
          } catch (err) {
            const plantId = activePlants[i].instance_id;
            failures.push(plantId);
            // Continue with remaining plants
            console.error(
              `Failed to instantiate workflow for plant ${plantId}:`,
              err,
            );
          }
        }

        if (failures.length > 0 && successCount > 0) {
          notification.warning(
            `${t('pages.tasks.instantiatedCount', { count: successCount })} ${failures.length} ${t('common.failed', { defaultValue: 'failed' })}.`,
          );
        } else if (failures.length > 0 && successCount === 0) {
          notification.error(
            t('pages.tasks.instantiateError', {
              defaultValue: 'Workflow instantiation failed for all plants.',
            }),
          );
        } else {
          notification.success(
            t('pages.tasks.instantiatedCount', { count: successCount }),
          );
        }
      }

      onInstantiated();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
      setBatchProgress(null);
    }
  }, [
    workflowKey,
    selectedTarget,
    notification,
    handleError,
    t,
    onInstantiated,
  ]);

  // ── Close handler ────────────────────────────────────────────────

  const handleClose = () => {
    if (saving) return;
    setSelectedTarget(null);
    setBatchProgress(null);
    onClose();
  };

  // ── Render ───────────────────────────────────────────────────────

  const isDisabled = !selectedTarget || saving;
  const locale = i18n.language === 'de' ? 'de-DE' : 'en-US';

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>{t('pages.tasks.instantiateWorkflow')}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.tasks.instantiateIntroNew')}
        </Typography>

        <Autocomplete<SelectionTarget>
          options={options}
          getOptionLabel={getOptionLabel}
          groupBy={(option) =>
            option.type === 'run'
              ? t('pages.tasks.instantiateGroupRuns')
              : t('pages.tasks.instantiateGroupPlants')
          }
          loading={loading}
          disabled={saving}
          onChange={(_, value) => setSelectedTarget(value)}
          isOptionEqualToValue={(option, value) => {
            if (option.type === 'run' && value.type === 'run') {
              return option.run.key === value.run.key;
            }
            if (option.type === 'plant' && value.type === 'plant') {
              return option.plant.key === value.plant.key;
            }
            return false;
          }}
          renderOption={({ key: liKey, ...restProps }, option) => {
            if (option.type === 'run') {
              const run = option.run;
              const activePlantCount = option.plants.length;
              return (
                <li key={liKey} {...restProps}>
                  <Box sx={{ width: '100%' }}>
                    <Stack
                      direction="row"
                      spacing={1}
                      alignItems="center"
                      flexWrap="wrap"
                    >
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        {run.name}
                      </Typography>
                      <Chip
                        label={t(`enums.plantingRunStatus.${run.status}`)}
                        size="small"
                        color={
                          run.status === 'active' ? 'success' : 'warning'
                        }
                        variant="outlined"
                      />
                      <Chip
                        label={t('pages.tasks.runPlantCount', {
                          count: activePlantCount,
                        })}
                        size="small"
                        variant="outlined"
                      />
                    </Stack>
                    {run.started_at && (
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ display: 'block', mt: 0.5 }}
                      >
                        {t('pages.tasks.plantedOn')}:{' '}
                        {formatDate(run.started_at, locale)}
                      </Typography>
                    )}
                  </Box>
                </li>
              );
            }

            const plant = option.plant;
            return (
              <li key={liKey} {...restProps}>
                <Box sx={{ width: '100%' }}>
                  <Stack
                    direction="row"
                    spacing={1}
                    alignItems="center"
                    flexWrap="wrap"
                  >
                    <Typography variant="body1" sx={{ fontWeight: 500 }}>
                      {plant.plant_name
                        ? `${plant.instance_id} - ${plant.plant_name}`
                        : plant.instance_id}
                    </Typography>
                    <Chip
                      label={t(`enums.phase.${plant.current_phase}`)}
                      size="small"
                      variant="outlined"
                    />
                  </Stack>
                  {plant.planted_on && (
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ display: 'block', mt: 0.5 }}
                    >
                      {t('pages.tasks.plantedOn')}:{' '}
                      {formatDate(plant.planted_on, locale)}
                    </Typography>
                  )}
                </Box>
              </li>
            );
          }}
          renderInput={(params) => (
            <TextField
              {...params}
              label={t('pages.tasks.instantiateTarget')}
              required
              sx={{ mb: 2 }}
              slotProps={{
                input: {
                  ...params.InputProps,
                  endAdornment: (
                    <>
                      {loading && <CircularProgress size={16} />}
                      {params.InputProps.endAdornment}
                    </>
                  ),
                },
              }}
              data-testid="target-select"
            />
          )}
        />

        {/* Batch progress indicator */}
        {batchProgress && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {t('pages.tasks.instantiatingProgress', {
                current: batchProgress.current,
                total: batchProgress.total,
              })}
            </Typography>
            <LinearProgress
              variant="determinate"
              value={(batchProgress.current / batchProgress.total) * 100}
            />
          </Box>
        )}

        {/* Task template preview */}
        {loadingTemplates ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            <CircularProgress size={24} />
          </Box>
        ) : templates.length > 0 ? (
          <Box>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              {t('pages.tasks.taskPreview')} ({templates.length})
            </Typography>
            <List dense>
              {templates
                .sort((a, b) => a.sequence_order - b.sequence_order)
                .map((tmpl) => (
                  <ListItem key={tmpl.key} disablePadding sx={{ mb: 0.5 }}>
                    <ListItemText
                      primary={
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1,
                          }}
                        >
                          <Chip
                            label={tmpl.sequence_order}
                            size="small"
                            variant="outlined"
                          />
                          <span>{tmpl.name}</span>
                          <Chip
                            label={t(`enums.taskCategory.${tmpl.category}`)}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                      }
                      secondary={tmpl.instruction || undefined}
                    />
                  </ListItem>
                ))}
            </List>
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            {t('pages.tasks.noTemplates')}
          </Typography>
        )}

        {/* Action buttons */}
        <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
          <Button
            variant="outlined"
            onClick={handleClose}
            disabled={saving}
            data-testid="form-cancel-button"
          >
            {t('common.cancel')}
          </Button>
          <Button
            variant="contained"
            onClick={handleInstantiate}
            disabled={isDisabled}
            startIcon={
              saving && !batchProgress ? (
                <CircularProgress size={16} />
              ) : undefined
            }
            data-testid="instantiate-button"
          >
            {t('pages.tasks.instantiate')}
          </Button>
        </Box>
      </DialogContent>
    </Dialog>
  );
}
