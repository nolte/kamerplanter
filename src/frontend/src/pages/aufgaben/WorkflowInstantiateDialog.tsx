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
import * as siteApi from '@/api/endpoints/sites';
import * as tankApi from '@/api/endpoints/tanks';
import type {
  PlantInstance,
  PlantingRun,
  PlantInRun,
  Location,
  Tank,
  TaskTemplate,
  WorkflowTargetType,
} from '@/api/types';

// ── Types ────────────────────────────────────────────────────────────

type SelectionTarget =
  | { type: 'plant'; plant: PlantInstance }
  | { type: 'run'; run: PlantingRun; plants: PlantInRun[] }
  | { type: 'location'; location: Location }
  | { type: 'tank'; tank: Tank };

// ── Props ────────────────────────────────────────────────────────────

interface Props {
  open: boolean;
  workflowKey: string;
  targetEntityTypes?: WorkflowTargetType[];
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
  targetEntityTypes = ['plant_instance'],
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
  const [locations, setLocations] = useState<Location[]>([]);
  const [tanks, setTanks] = useState<Tank[]>([]);
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

    const loadPlantData = async () => {
      setLoading(true);
      try {
        const plantsData = await plantApi.listPlantInstances(0, 200);
        if (cancelled) return;
        setPlants(plantsData);

        let activeRuns: PlantingRun[] = [];
        try {
          const runsData = await plantingRunApi.listPlantingRuns(0, 200);
          if (cancelled) return;
          activeRuns = runsData.filter(
            (r) => r.status === 'active' || r.status === 'harvesting',
          );
        } catch {
          if (!cancelled) setLoading(false);
          return;
        }

        const plantsMap: Record<string, PlantInRun[]> = {};
        await Promise.all(
          activeRuns.map(async (run) => {
            try {
              const runPlants = await plantingRunApi.listRunPlants(run.key);
              plantsMap[run.key] = runPlants;
            } catch {
              // Skip this run
            }
          }),
        );

        if (cancelled) return;
        setRuns(activeRuns.filter((r) => r.key in plantsMap));
        setRunPlantsMap(plantsMap);
      } catch (err) {
        if (!cancelled) handleError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    const loadLocationData = async () => {
      setLoading(true);
      try {
        const sites = await siteApi.listSites(0, 200);
        if (cancelled) return;
        const allLocations: Location[] = [];
        await Promise.all(
          sites.map(async (site) => {
            try {
              const locs = await siteApi.listLocations(site.key);
              allLocations.push(...locs);
            } catch {
              // Skip this site
            }
          }),
        );
        if (!cancelled) setLocations(allLocations);
      } catch (err) {
        if (!cancelled) handleError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    const loadTankData = async () => {
      setLoading(true);
      try {
        const tanksData = await tankApi.listTanks(0, 200);
        if (!cancelled) setTanks(tanksData);
      } catch (err) {
        if (!cancelled) handleError(err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    // Load entities based on target types
    const needsPlantData = targetEntityTypes.includes('plant_instance') || targetEntityTypes.includes('planting_run');
    const needsLocationData = targetEntityTypes.includes('location');
    const needsTankData = targetEntityTypes.includes('tank');

    if (needsPlantData) loadPlantData();
    if (needsLocationData) loadLocationData();
    if (needsTankData) loadTankData();

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

    loadTemplates();

    return () => {
      cancelled = true;
    };
  }, [open, workflowKey, targetEntityTypes, handleError]);

  // ── Build unified options ────────────────────────────────────────

  const options = useMemo<SelectionTarget[]>(() => {
    const result: SelectionTarget[] = [];

    const hasPlantInstance = targetEntityTypes.includes('plant_instance');
    const hasPlantingRun = targetEntityTypes.includes('planting_run');
    const hasLocation = targetEntityTypes.includes('location');
    const hasTank = targetEntityTypes.includes('tank');

    if (hasPlantInstance || hasPlantingRun) {
      const runPlantKeys = new Set<string>();
      for (const runPlants of Object.values(runPlantsMap)) {
        for (const p of runPlants) {
          runPlantKeys.add(p.key);
        }
      }

      if (hasPlantingRun || hasPlantInstance) {
        const runOptions: SelectionTarget[] = runs.map((run) => ({
          type: 'run' as const,
          run,
          plants: (runPlantsMap[run.key] ?? []).filter(
            (p) => !p.detached_at && !p.removed_on,
          ),
        }));
        result.push(...runOptions);
      }

      if (hasPlantInstance) {
        const standalonePlantOptions: SelectionTarget[] = plants
          .filter((p) => !runPlantKeys.has(p.key) && !p.removed_on)
          .map((plant) => ({
            type: 'plant' as const,
            plant,
          }));
        result.push(...standalonePlantOptions);
      }
    }

    if (hasLocation) {
      result.push(...locations.map((loc) => ({ type: 'location' as const, location: loc })));
    }

    if (hasTank) {
      result.push(...tanks.map((tank) => ({ type: 'tank' as const, tank })));
    }

    return result;
  }, [plants, runs, runPlantsMap, locations, tanks, targetEntityTypes]);

  // ── Option label ─────────────────────────────────────────────────

  const getOptionLabel = useCallback(
    (option: SelectionTarget): string => {
      if (option.type === 'run') {
        const count = option.plants.length;
        return `${option.run.name} (${t('pages.tasks.runPlantCount', { count })})`;
      }
      if (option.type === 'plant') {
        const p = option.plant;
        return p.plant_name
          ? `${p.instance_id} - ${p.plant_name}`
          : p.instance_id;
      }
      if (option.type === 'location') {
        return option.location.name;
      }
      return option.tank.name;
    },
    [t],
  );

  // ── Group by ─────────────────────────────────────────────────────

  const getGroupLabel = useCallback(
    (option: SelectionTarget): string => {
      switch (option.type) {
        case 'run':
          return t('pages.tasks.instantiateGroupRuns');
        case 'plant':
          return t('pages.tasks.instantiateGroupPlants');
        case 'location':
          return t('pages.tasks.instantiateGroupLocations');
        case 'tank':
          return t('pages.tasks.instantiateGroupTanks');
      }
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
          entity_key: selectedTarget.plant.key,
          entity_type: 'plant_instance',
        });
        notification.success(t('pages.tasks.workflowInstantiated'));
      } else if (selectedTarget.type === 'run') {
        const activePlants = selectedTarget.plants;
        const total = activePlants.length;
        let successCount = 0;
        const failures: string[] = [];

        for (let i = 0; i < activePlants.length; i++) {
          setBatchProgress({ current: i + 1, total });
          try {
            await taskApi.instantiateWorkflow(workflowKey, {
              entity_key: activePlants[i].key,
              entity_type: 'plant_instance',
            });
            successCount++;
          } catch (err) {
            const plantId = activePlants[i].instance_id;
            failures.push(plantId);
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
      } else if (selectedTarget.type === 'location') {
        await taskApi.instantiateWorkflow(workflowKey, {
          entity_key: selectedTarget.location.key,
          entity_type: 'location',
        });
        notification.success(t('pages.tasks.workflowInstantiated'));
      } else if (selectedTarget.type === 'tank') {
        await taskApi.instantiateWorkflow(workflowKey, {
          entity_key: selectedTarget.tank.key,
          entity_type: 'tank',
        });
        notification.success(t('pages.tasks.workflowInstantiated'));
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

  const inputLabel = useMemo(() => {
    if (targetEntityTypes.length === 1) {
      const et = targetEntityTypes[0];
      if (et === 'location' || et === 'tank') {
        return t('pages.tasks.selectEntity');
      }
    }
    return t('pages.tasks.instantiateTarget');
  }, [targetEntityTypes, t]);

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
          groupBy={getGroupLabel}
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
            if (option.type === 'location' && value.type === 'location') {
              return option.location.key === value.location.key;
            }
            if (option.type === 'tank' && value.type === 'tank') {
              return option.tank.key === value.tank.key;
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
                      spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
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

            if (option.type === 'plant') {
              const plant = option.plant;
              return (
                <li key={liKey} {...restProps}>
                  <Box sx={{ width: '100%' }}>
                    <Stack
                      direction="row"
                      spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
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
            }

            if (option.type === 'location') {
              return (
                <li key={liKey} {...restProps}>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {option.location.name}
                  </Typography>
                </li>
              );
            }

            // tank
            return (
              <li key={liKey} {...restProps}>
                <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {option.tank.name}
                  </Typography>
                  <Chip
                    label={t(`enums.tankType.${option.tank.tank_type}`)}
                    size="small"
                    variant="outlined"
                  />
                </Stack>
              </li>
            );
          }}
          renderInput={({ InputProps: MuiInputProps, inputProps: muiInputProps, InputLabelProps: muiInputLabelProps, ...params }) => (
            <TextField
              {...params}
              label={inputLabel}
              required
              sx={{ mb: 2 }}
              slotProps={{
                input: {
                  ...MuiInputProps,
                  endAdornment: (
                    <>
                      {loading && <CircularProgress size={16} />}
                      {MuiInputProps?.endAdornment}
                    </>
                  ),
                },
                htmlInput: muiInputProps,
                inputLabel: muiInputLabelProps,
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
