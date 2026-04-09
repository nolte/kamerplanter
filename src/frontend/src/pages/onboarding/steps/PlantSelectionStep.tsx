import { useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import IconButton from '@mui/material/IconButton';
import AddIcon from '@mui/icons-material/Add';
import RemoveIcon from '@mui/icons-material/Remove';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import type { Species, PhaseName, PlantConfig } from '@/api/types';

const PHASE_OPTIONS: PhaseName[] = [
  'germination',
  'seedling',
  'vegetative',
  'flowering',
];

interface PlantSelectionStepProps {
  allSpecies: Species[];
  favoriteSpeciesKeys: string[];
  plantConfigs: PlantConfig[];
  onPlantConfigsChange: (configs: PlantConfig[]) => void;
}

export default function PlantSelectionStep({
  allSpecies,
  favoriteSpeciesKeys,
  plantConfigs,
  onPlantConfigsChange,
}: PlantSelectionStepProps) {
  const { t } = useTranslation();

  const speciesMap = useMemo(() => {
    const map = new Map<string, Species>();
    for (const sp of allSpecies) {
      map.set(sp.key, sp);
    }
    return map;
  }, [allSpecies]);

  const getSpeciesName = useCallback(
    (key: string): string => {
      const sp = speciesMap.get(key);
      if (!sp) return key;
      return sp.common_names?.[0] ?? sp.scientific_name;
    },
    [speciesMap],
  );

  // Build a config map for quick lookup
  const configMap = useMemo(() => {
    const map = new Map<string, PlantConfig>();
    for (const c of plantConfigs) {
      map.set(c.species_key, c);
    }
    return map;
  }, [plantConfigs]);

  const updateConfig = useCallback(
    (speciesKey: string, patch: Partial<Omit<PlantConfig, 'species_key'>>) => {
      const existing = configMap.get(speciesKey);
      const base: PlantConfig = existing ?? {
        species_key: speciesKey,
        count: 1,
        initial_phase: 'germination',
      };
      const updated = { ...base, ...patch };

      const newConfigs = plantConfigs.filter((c) => c.species_key !== speciesKey);
      if (updated.count > 0) {
        newConfigs.push(updated);
      }
      onPlantConfigsChange(newConfigs);
    },
    [configMap, plantConfigs, onPlantConfigsChange],
  );

  const incrementCount = useCallback(
    (speciesKey: string) => {
      const current = configMap.get(speciesKey)?.count ?? 0;
      if (current < 50) {
        updateConfig(speciesKey, { count: current + 1 });
      }
    },
    [configMap, updateConfig],
  );

  const decrementCount = useCallback(
    (speciesKey: string) => {
      const current = configMap.get(speciesKey)?.count ?? 0;
      if (current > 0) {
        updateConfig(speciesKey, { count: current - 1 });
      }
    },
    [configMap, updateConfig],
  );

  const totalPlants = useMemo(
    () => plantConfigs.reduce((sum, c) => sum + c.count, 0),
    [plantConfigs],
  );

  return (
    <Box data-testid="onboarding-step-plant-selection">
      <Typography variant="h6" gutterBottom>
        {t('pages.onboarding.plants.title')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t('pages.onboarding.plants.configSubtitle')}
      </Typography>

      {favoriteSpeciesKeys.length > 0 ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {favoriteSpeciesKeys.map((key) => {
            const config = configMap.get(key);
            const count = config?.count ?? 0;
            const phase = config?.initial_phase ?? 'germination';
            const sp = speciesMap.get(key);

            return (
              <Box
                key={key}
                sx={{
                  display: 'flex',
                  flexDirection: { xs: 'column', sm: 'row' },
                  alignItems: { sm: 'center' },
                  gap: { xs: 1.5, sm: 2 },
                  p: 2,
                  border: 1,
                  borderColor: count > 0 ? 'primary.main' : 'divider',
                  borderRadius: 1,
                  bgcolor: count > 0 ? 'action.selected' : 'background.paper',
                  transition: 'border-color 0.2s, background-color 0.2s',
                }}
                data-testid={`plant-config-${key}`}
              >
                {/* Species name */}
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="subtitle2" noWrap>
                    {getSpeciesName(key)}
                  </Typography>
                  {sp && sp.scientific_name !== (sp.common_names?.[0] ?? sp.scientific_name) && (
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      noWrap
                      sx={{ fontStyle: 'italic' }}
                    >
                      {sp.scientific_name}
                    </Typography>
                  )}
                </Box>

                {/* Count stepper */}
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 0.5,
                    flexShrink: 0,
                  }}
                >
                  <IconButton
                    size="small"
                    onClick={() => decrementCount(key)}
                    disabled={count === 0}
                    aria-label={t('pages.onboarding.plants.decreaseCount')}
                    data-testid={`plant-count-minus-${key}`}
                  >
                    <RemoveIcon fontSize="small" />
                  </IconButton>
                  <TextField
                    type="number"
                    size="small"
                    value={count}
                    onChange={(e) => {
                      const val = Math.max(0, Math.min(50, parseInt(e.target.value, 10) || 0));
                      updateConfig(key, { count: val });
                    }}
                    slotProps={{ htmlInput: {
                      min: 0,
                      max: 50,
                      style: { textAlign: 'center', width: 48 },
                      'aria-label': t('pages.onboarding.plants.countLabel', { name: getSpeciesName(key) }),
                    } }}
                    sx={{ width: 72 }}
                    data-testid={`plant-count-input-${key}`}
                  />
                  <IconButton
                    size="small"
                    onClick={() => incrementCount(key)}
                    disabled={count >= 50}
                    aria-label={t('pages.onboarding.plants.increaseCount')}
                    data-testid={`plant-count-plus-${key}`}
                  >
                    <AddIcon fontSize="small" />
                  </IconButton>
                </Box>

                {/* Phase selector — only visible when count > 0 */}
                {count > 0 && (
                  <FormControl size="small" sx={{ minWidth: 140, flexShrink: 0 }}>
                    <InputLabel id={`phase-label-${key}`}>
                      {t('pages.onboarding.plants.phaseLabel')}
                    </InputLabel>
                    <Select
                      labelId={`phase-label-${key}`}
                      value={phase}
                      label={t('pages.onboarding.plants.phaseLabel')}
                      onChange={(e) => updateConfig(key, { initial_phase: e.target.value as PhaseName })}
                      data-testid={`plant-phase-select-${key}`}
                    >
                      {PHASE_OPTIONS.map((p) => (
                        <MenuItem key={p} value={p}>
                          {t(`enums.phaseName.${p}`)}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
              </Box>
            );
          })}

          {/* Total summary */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              pt: 1,
              borderTop: 1,
              borderColor: 'divider',
            }}
          >
            <Typography variant="subtitle2" color="text.secondary">
              {t('pages.onboarding.plants.totalPlants')}
            </Typography>
            <Typography variant="h6" color="primary" sx={{ fontWeight: 700 }}>
              {totalPlants}
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5 }}>
            <InfoOutlinedIcon fontSize="small" sx={{ color: 'text.secondary', mt: '1px', flexShrink: 0 }} aria-hidden="true" />
            <Typography variant="caption" color="text.secondary">
              {t('pages.onboarding.plants.configHint')}
            </Typography>
          </Box>
        </Box>
      ) : (
        <Box
          sx={{
            p: 3,
            border: 1,
            borderColor: 'divider',
            borderRadius: 1,
            textAlign: 'center',
          }}
        >
          <Typography variant="body2" color="text.secondary">
            {t('pages.onboarding.plants.noFavorites')}
          </Typography>
        </Box>
      )}
    </Box>
  );
}
