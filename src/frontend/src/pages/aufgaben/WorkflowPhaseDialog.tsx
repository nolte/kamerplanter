import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Dialog from '@mui/material/Dialog';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import CircularProgress from '@mui/material/CircularProgress';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormActions from '@/components/form/FormActions';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as taskApi from '@/api/endpoints/tasks';
import * as speciesApi from '@/api/endpoints/species';
import * as phasesApi from '@/api/endpoints/phases';
import type { WorkflowPhase, WorkflowPhaseSuggestion, GrowthPhase } from '@/api/types';

type SpeciesOption = { key: string; scientific_name: string; common_names: string[] };

const stressLevels = ['none', 'low', 'medium', 'high'] as const;
const lifecyclePhases = [
  'germination', 'seedling', 'vegetative', 'flowering',
  'flushing', 'dormancy', 'harvest',
] as const;

const schema = z.object({
  name: z.string().min(1).max(200),
  description: z.string(),
  duration_days: z.number().min(0).nullable(),
  stress_tolerance: z.enum(stressLevels),
  trigger_phase: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onClose: () => void;
  workflowKey: string;
  phase?: WorkflowPhase;
  onSaved: () => void;
}

export default function WorkflowPhaseDialog({ open, onClose, workflowKey, phase, onSaved }: Props) {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const { t } = useTranslation();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [saving, setSaving] = useState(false);
  const isEdit = !!phase;

  // Species autocomplete state
  const [speciesOptions, setSpeciesOptions] = useState<SpeciesOption[]>([]);
  const [speciesLoading, setSpeciesLoading] = useState(false);
  const [selectedSpecies, setSelectedSpecies] = useState<SpeciesOption | null>(null);

  // Growth phases from selected species
  const [growthPhases, setGrowthPhases] = useState<GrowthPhase[]>([]);
  const [growthPhasesLoading, setGrowthPhasesLoading] = useState(false);

  // Existing phase suggestions
  const [suggestions, setSuggestions] = useState<WorkflowPhaseSuggestion[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);

  const defaultValues: FormData = {
    name: '',
    description: '',
    duration_days: null,
    stress_tolerance: 'none',
    trigger_phase: null,
  };

  const { control, handleSubmit, reset } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues,
  });

  useEffect(() => {
    if (open && phase) {
      reset({
        name: phase.name,
        description: phase.description,
        duration_days: phase.duration_days || null,
        stress_tolerance: (phase.stress_tolerance as FormData['stress_tolerance']) || 'none',
        trigger_phase: phase.trigger_phase,
      });
    } else if (open) {
      reset(defaultValues);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, phase, reset]);

  // Load species list and suggestions when dialog opens in create mode
  useEffect(() => {
    if (!open || isEdit) return;

    setSelectedSpecies(null);
    setGrowthPhases([]);

    setSpeciesLoading(true);
    speciesApi
      .listSpecies(0, 500)
      .then((res) => {
        setSpeciesOptions(
          res.items.map((s) => ({
            key: s.key,
            scientific_name: s.scientific_name,
            common_names: s.common_names,
          })),
        );
      })
      .catch(() => setSpeciesOptions([]))
      .finally(() => setSpeciesLoading(false));

    setSuggestionsLoading(true);
    taskApi
      .listPhaseSuggestions()
      .then(setSuggestions)
      .catch(() => setSuggestions([]))
      .finally(() => setSuggestionsLoading(false));
  }, [open, isEdit]);

  // Load growth phases when species changes
  useEffect(() => {
    if (!selectedSpecies) {
      setGrowthPhases([]);
      return;
    }

    setGrowthPhasesLoading(true);
    phasesApi
      .getLifecycleConfig(selectedSpecies.key)
      .then((lc) => phasesApi.listGrowthPhases(lc.key))
      .then((phases) => {
        const sorted = [...phases].sort((a, b) => a.sequence_order - b.sequence_order);
        setGrowthPhases(sorted);
      })
      .catch(() => setGrowthPhases([]))
      .finally(() => setGrowthPhasesLoading(false));
  }, [selectedSpecies]);

  const fillFromGrowthPhase = useCallback(
    (gp: GrowthPhase) => {
      reset({
        name: gp.display_name || gp.name,
        duration_days: gp.typical_duration_days,
        stress_tolerance: (gp.stress_tolerance as FormData['stress_tolerance']) || 'none',
        trigger_phase: gp.name,
        description: gp.description || '',
      });
    },
    [reset],
  );

  const fillFromSuggestion = useCallback(
    (suggestion: WorkflowPhaseSuggestion) => {
      reset({
        name: suggestion.name,
        duration_days: suggestion.duration_days,
        stress_tolerance:
          (suggestion.stress_tolerance as FormData['stress_tolerance']) || 'none',
        trigger_phase: suggestion.trigger_phase,
        description: '',
      });
    },
    [reset],
  );

  const onSubmit = async (data: FormData) => {
    try {
      setSaving(true);
      const payload = {
        name: data.name,
        description: data.description || undefined,
        duration_days: data.duration_days ?? undefined,
        stress_tolerance: data.stress_tolerance,
        trigger_phase: data.trigger_phase || null,
      };
      if (isEdit && phase) {
        await taskApi.updateWorkflowPhase(phase.key, payload);
        notification.success(t('pages.tasks.phaseUpdated'));
      } else {
        await taskApi.createWorkflowPhase(workflowKey, payload);
        notification.success(t('pages.tasks.phaseCreated'));
      }
      onSaved();
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="workflow-phase-dialog-title"
    >
      <DialogTitle id="workflow-phase-dialog-title">
        {isEdit ? t('pages.tasks.editPhase') : t('pages.tasks.createPhase')}
      </DialogTitle>
      <DialogContent>
        {/* Species selector and suggestions — only in create mode */}
        {!isEdit && (
          <>
            {/* Species-based phase loading */}
            <Typography variant="subtitle2" sx={{ mt: 1, mb: 1 }}>
              {t('pages.tasks.loadFromSpecies')}
            </Typography>
            <Autocomplete
              options={speciesOptions}
              loading={speciesLoading}
              value={selectedSpecies}
              onChange={(_e, value) => setSelectedSpecies(value)}
              getOptionLabel={(option) =>
                option.common_names.length > 0
                  ? `${option.scientific_name} (${option.common_names[0]})`
                  : option.scientific_name
              }
              isOptionEqualToValue={(option, value) => option.key === value.key}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label={t('pages.tasks.selectSpecies')}
                  size="small"
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
              sx={{ mb: 1 }}
            />

            {/* Growth phase chips */}
            {selectedSpecies && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                  {t('pages.tasks.speciesPhases', { name: selectedSpecies.scientific_name })}
                </Typography>
                {growthPhasesLoading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 1 }}>
                    <CircularProgress size={24} />
                  </Box>
                ) : (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {growthPhases.map((gp) => (
                      <Chip
                        key={gp.key}
                        label={gp.display_name || gp.name}
                        onClick={() => fillFromGrowthPhase(gp)}
                        color="primary"
                        variant="outlined"
                        size="small"
                        clickable
                      />
                    ))}
                  </Box>
                )}
              </Box>
            )}

            <Divider sx={{ my: 2 }} />

            {/* Existing phase suggestions */}
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              {t('pages.tasks.existingPhases')}
            </Typography>
            {suggestionsLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 1 }}>
                <CircularProgress size={24} />
              </Box>
            ) : suggestions.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {t('pages.tasks.noSuggestions')}
              </Typography>
            ) : (
              <List dense disablePadding sx={{ mb: 1 }}>
                {suggestions.map((s) => (
                  <ListItemButton
                    key={s.name}
                    onClick={() => fillFromSuggestion(s)}
                    sx={{ borderRadius: 1, mb: 0.5 }}
                  >
                    <ListItemText
                      primary={s.name}
                      secondary={
                        s.used_by_species.length > 0 ? (
                          <Box
                            component="span"
                            sx={{ display: 'inline-flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}
                          >
                            {s.used_by_species.map((species) => (
                              <Chip
                                key={species}
                                label={species}
                                size="small"
                                variant="outlined"
                                component="span"
                              />
                            ))}
                          </Box>
                        ) : undefined
                      }
                    />
                  </ListItemButton>
                ))}
              </List>
            )}

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              {t('pages.tasks.orCreateManually')}
            </Typography>
          </>
        )}

        {/* Manual form — always shown */}
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormTextField
            name="name"
            control={control}
            label={t('pages.tasks.phaseName')}
            required
            autoFocus={isEdit}
          />
          <FormTextField
            name="description"
            control={control}
            label={t('pages.tasks.phaseDescription')}
            multiline
            rows={3}
          />
          <FormNumberField
            name="duration_days"
            control={control}
            label={t('pages.tasks.phaseDuration')}
            min={0}
            step={1}
            suffix={t('common.days')}
          />
          <FormSelectField
            name="stress_tolerance"
            control={control}
            label={t('pages.tasks.phaseStressTolerance')}
            options={stressLevels.map((v) => ({
              value: v,
              label: t(`enums.stressLevel.${v}`),
            }))}
          />
          <FormSelectField
            name="trigger_phase"
            control={control}
            label={t('pages.tasks.phaseTriggerPhase')}
            options={[
              { value: '', label: '\u2014' },
              ...lifecyclePhases.map((v) => ({
                value: v,
                label: t(`enums.phaseName.${v}`),
              })),
            ]}
            helperText={t('pages.tasks.phaseTriggerPhaseHelper')}
          />
          <FormActions
            onCancel={onClose}
            loading={saving}
            saveLabel={isEdit ? t('common.save') : t('common.create')}
          />
        </form>
      </DialogContent>
    </Dialog>
  );
}
