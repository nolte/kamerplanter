import { useMemo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Checkbox from '@mui/material/Checkbox';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import FilterListIcon from '@mui/icons-material/FilterList';
import type { CalendarEvent } from '@/api/types';

// ── Types ────────────────────────────────────────────────────────────

interface RunNode {
  runKey: string;
  runName: string;
  plants: PlantNode[];
}

interface PlantNode {
  plantKey: string;
  plantName: string;
}

interface PlantFilterTreeProps {
  events: CalendarEvent[];
  checkedPlantKeys: Set<string>;
  onCheckedChange: (keys: Set<string>) => void;
  expandedRuns: Set<string>;
  onExpandedChange: (keys: Set<string>) => void;
}

// ── Component ────────────────────────────────────────────────────────

export default function PlantFilterTree({
  events,
  checkedPlantKeys,
  onCheckedChange,
  expandedRuns,
  onExpandedChange,
}: PlantFilterTreeProps) {
  const { t } = useTranslation();

  // Build tree structure from events
  const { tree, allPlantKeys } = useMemo(() => {
    const runMap = new Map<string, { runName: string; plants: Map<string, string> }>();
    const standalone = new Map<string, string>();

    for (const ev of events) {
      const meta = ev.metadata as Record<string, string> | undefined;
      const runKey = meta?.run_key;
      const plantKey = meta?.plant_instance_key || ev.plant_key;
      const plantName = meta?.plant_name || meta?.instance_id || '';

      if (!plantKey) continue;

      if (runKey) {
        if (!runMap.has(runKey)) {
          runMap.set(runKey, {
            runName: meta?.run_name || runKey,
            plants: new Map(),
          });
        }
        const run = runMap.get(runKey)!;
        if (!run.plants.has(plantKey)) {
          run.plants.set(plantKey, plantName || plantKey);
        }
      } else {
        if (!standalone.has(plantKey)) {
          standalone.set(plantKey, plantName || plantKey);
        }
      }
    }

    const nodes: RunNode[] = [];
    const keys = new Set<string>();

    for (const [runKey, data] of runMap) {
      const plants: PlantNode[] = [];
      for (const [pk, pn] of data.plants) {
        plants.push({ plantKey: pk, plantName: pn });
        keys.add(pk);
      }
      plants.sort((a, b) => a.plantName.localeCompare(b.plantName));
      nodes.push({ runKey, runName: data.runName, plants });
    }

    // Collect all plant keys already assigned to a run
    const runAssignedKeys = new Set<string>();
    for (const data of runMap.values()) {
      for (const pk of data.plants.keys()) {
        runAssignedKeys.add(pk);
      }
    }

    // Filter standalone: exclude plants that belong to a run
    if (standalone.size > 0) {
      const plants: PlantNode[] = [];
      for (const [pk, pn] of standalone) {
        if (runAssignedKeys.has(pk)) continue;
        plants.push({ plantKey: pk, plantName: pn });
        keys.add(pk);
      }
      plants.sort((a, b) => a.plantName.localeCompare(b.plantName));
      nodes.push({
        runKey: '_standalone',
        runName: t('pages.calendar.phaseTimeline.noRun'),
        plants,
      });
    }

    nodes.sort((a, b) => {
      if (a.runKey === '_standalone') return 1;
      if (b.runKey === '_standalone') return -1;
      return a.runName.localeCompare(b.runName);
    });

    return { tree: nodes, allPlantKeys: keys };
  }, [events, t]);

  const allChecked = allPlantKeys.size > 0 && allPlantKeys.size === checkedPlantKeys.size;
  const noneChecked = checkedPlantKeys.size === 0;
  const isFiltering = !allChecked && !noneChecked;

  // Toggle all
  const handleToggleAll = useCallback(() => {
    if (allChecked) {
      onCheckedChange(new Set());
    } else {
      onCheckedChange(new Set(allPlantKeys));
    }
  }, [allChecked, allPlantKeys, onCheckedChange]);

  // Toggle a run (all its children)
  const handleToggleRun = useCallback(
    (run: RunNode) => {
      const next = new Set(checkedPlantKeys);
      const runPlantKeys = run.plants.map((p) => p.plantKey);
      const allRunChecked = runPlantKeys.every((k) => next.has(k));
      if (allRunChecked) {
        for (const k of runPlantKeys) next.delete(k);
      } else {
        for (const k of runPlantKeys) next.add(k);
      }
      onCheckedChange(next);
    },
    [checkedPlantKeys, onCheckedChange],
  );

  // Toggle a single plant
  const handleTogglePlant = useCallback(
    (plantKey: string) => {
      const next = new Set(checkedPlantKeys);
      if (next.has(plantKey)) {
        next.delete(plantKey);
      } else {
        next.add(plantKey);
      }
      onCheckedChange(next);
    },
    [checkedPlantKeys, onCheckedChange],
  );

  // Toggle run expand/collapse
  const handleToggleExpand = useCallback(
    (runKey: string) => {
      const next = new Set(expandedRuns);
      if (next.has(runKey)) {
        next.delete(runKey);
      } else {
        next.add(runKey);
      }
      onExpandedChange(next);
    },
    [expandedRuns, onExpandedChange],
  );

  if (tree.length === 0) return null;

  return (
    <Paper variant="outlined" sx={{ px: 2, py: 1.5 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
        <FilterListIcon sx={{ color: 'text.secondary', flexShrink: 0 }} />
        <Typography variant="subtitle2" sx={{ flex: 1, color: 'text.secondary' }}>
          {t('pages.calendar.plantFilter.title')}
        </Typography>
        {isFiltering && (
          <Button
            size="small"
            onClick={handleToggleAll}
            data-testid="plant-filter-clear"
          >
            {t('pages.calendar.plantFilter.showAll')}
          </Button>
        )}
      </Box>

      {/* Select all row */}
      <Box sx={{ display: 'flex', alignItems: 'center', ml: -0.5 }}>
        <Checkbox
          size="small"
          checked={allChecked}
          indeterminate={isFiltering}
          onChange={handleToggleAll}
          data-testid="plant-filter-select-all"
        />
        <Typography
          variant="body2"
          sx={{ fontWeight: 500, cursor: 'pointer' }}
          onClick={handleToggleAll}
        >
          {t('common.all')}
        </Typography>
      </Box>

      {/* Run nodes */}
      {tree.map((run) => {
        const runPlantKeys = run.plants.map((p) => p.plantKey);
        const checkedCount = runPlantKeys.filter((k) => checkedPlantKeys.has(k)).length;
        const allRunChecked = checkedCount === runPlantKeys.length;
        const someRunChecked = checkedCount > 0 && checkedCount < runPlantKeys.length;
        const isExpanded = expandedRuns.has(run.runKey);

        return (
          <Box key={run.runKey}>
            {/* Run row */}
            <Box sx={{ display: 'flex', alignItems: 'center', ml: 1 }}>
              <IconButton
                size="small"
                onClick={() => handleToggleExpand(run.runKey)}
                sx={{ p: 0.25 }}
                data-testid={`plant-filter-expand-${run.runKey}`}
              >
                {isExpanded ? (
                  <ExpandMoreIcon sx={{ fontSize: '1.1rem' }} />
                ) : (
                  <ChevronRightIcon sx={{ fontSize: '1.1rem' }} />
                )}
              </IconButton>
              <Checkbox
                size="small"
                checked={allRunChecked}
                indeterminate={someRunChecked}
                onChange={() => handleToggleRun(run)}
                data-testid={`plant-filter-run-${run.runKey}`}
              />
              <Typography
                variant="body2"
                sx={{
                  fontWeight: 600,
                  cursor: 'pointer',
                  color: allRunChecked || someRunChecked ? 'text.primary' : 'text.disabled',
                }}
                onClick={() => handleToggleRun(run)}
                noWrap
              >
                {run.runName}
                <Typography component="span" variant="caption" sx={{ ml: 0.5, color: 'text.secondary' }}>
                  ({run.plants.length})
                </Typography>
              </Typography>
            </Box>

            {/* Plant children */}
            <Collapse in={isExpanded}>
              {run.plants.map((plant) => (
                <Box
                  key={plant.plantKey}
                  sx={{ display: 'flex', alignItems: 'center', ml: 5 }}
                >
                  <Checkbox
                    size="small"
                    checked={checkedPlantKeys.has(plant.plantKey)}
                    onChange={() => handleTogglePlant(plant.plantKey)}
                    data-testid={`plant-filter-plant-${plant.plantKey}`}
                  />
                  <Typography
                    variant="body2"
                    sx={{
                      cursor: 'pointer',
                      color: checkedPlantKeys.has(plant.plantKey) ? 'text.primary' : 'text.disabled',
                    }}
                    onClick={() => handleTogglePlant(plant.plantKey)}
                    noWrap
                  >
                    {plant.plantName}
                  </Typography>
                </Box>
              ))}
            </Collapse>
          </Box>
        );
      })}
    </Paper>
  );
}
