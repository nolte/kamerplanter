import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import { useFieldArray, Controller, type Control } from 'react-hook-form';
import ExpertiseFieldWrapper from '@/components/common/ExpertiseFieldWrapper';
import FormSelectField from '@/components/form/FormSelectField';
import FormTextField from '@/components/form/FormTextField';
import FormRow from '@/components/form/FormRow';
import {
  PROPAGATION_METHODS,
  WOOD_STAGES,
  PROPAGATION_DIFFICULTIES,
  GROWTH_HABITS,
  MONTHS,
  type SpeciesFormData,
} from './speciesDetailSchema';

interface SpeciesGrowthPanelProps {
  control: Control<SpeciesFormData>;
}

/**
 * Growth panel of the species edit form (UI-NFR-008 R-057): growth habit, root
 * type and the repeatable propagation-config editor. The propagation field
 * array is derived from `control` and therefore local to this panel.
 */
export default function SpeciesGrowthPanel({ control }: SpeciesGrowthPanelProps) {
  const { t } = useTranslation();
  const {
    fields: propagationFields,
    append: appendPropagation,
    remove: removePropagation,
  } = useFieldArray({ control, name: 'propagation_configs' });

  return (
    <Card variant="outlined">
      <CardContent
        component="fieldset"
        sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}
      >
        <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
          {t('pages.species.sectionGrowth')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.species.sectionGrowthDesc')}
        </Typography>
        <FormRow>
          <FormSelectField
            name="growth_habit"
            control={control}
            label={t('pages.species.growthHabit')}
            helperText={t('pages.species.growthHabitHelper')}
            options={GROWTH_HABITS.map((v) => ({
              value: v,
              label: t(`enums.growthHabit.${v}`),
            }))}
          />
          <ExpertiseFieldWrapper minLevel="expert">
            <FormSelectField
              name="root_type"
              control={control}
              label={t('pages.species.rootType')}
              helperText={t('pages.species.rootTypeHelper')}
              options={['fibrous', 'taproot', 'tuberous', 'bulbous', 'corm'].map((v) => ({
                value: v,
                label: t(`enums.rootType.${v}`),
              }))}
            />
          </ExpertiseFieldWrapper>
        </FormRow>
        {/* Propagation config editor — one repeatable entry per method
          (method + month picker + optional wood stage + notes). Replaces
          the former flat propagation_methods multi-select (WP-5). */}
        <Box sx={{ mt: 1 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            {t('pages.species.propagationConfigs')}
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1.5 }}>
            {t('pages.species.propagationConfigsHelper')}
          </Typography>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {propagationFields.map((cfg, index) => (
              <Card key={cfg.id} variant="outlined" data-testid={`propagation-config-${index}`}>
                <CardContent sx={{ '&:last-child': { pb: 2 } }}>
                  <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <FormSelectField
                        name={`propagation_configs.${index}.method`}
                        control={control}
                        label={t('pages.species.propagationMethods')}
                        options={PROPAGATION_METHODS.map((v) => ({
                          value: v,
                          label: t(`enums.propagationMethod.${v}`),
                        }))}
                      />
                    </Box>
                    <IconButton
                      color="error"
                      onClick={() => removePropagation(index)}
                      aria-label={t('pages.species.removePropagationMethod')}
                      data-testid={`remove-propagation-config-${index}`}
                      sx={{ mt: 1 }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>

                  {/* Month multi-picker (1..12) */}
                  <Controller
                    name={`propagation_configs.${index}.months`}
                    control={control}
                    render={({ field }) => {
                      const selected = field.value ?? [];
                      const toggle = (m: number) =>
                        field.onChange(
                          selected.includes(m)
                            ? selected.filter((x) => x !== m)
                            : [...selected, m].sort((a, b) => a - b),
                        );
                      return (
                        <Box sx={{ mb: 1.5 }}>
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ display: 'block', mb: 0.75 }}
                          >
                            {t('pages.species.propagationMonthsLabel')}
                          </Typography>
                          <Box
                            role="group"
                            aria-label={t('pages.species.propagationMonthsLabel')}
                            sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}
                            data-testid={`propagation-months-${index}`}
                          >
                            {MONTHS.map((m) => {
                              const isSelected = selected.includes(m);
                              const monthName = t(`pages.species.months.${m}`);
                              return (
                                <Chip
                                  key={m}
                                  size="small"
                                  clickable
                                  color={isSelected ? 'primary' : 'default'}
                                  variant={isSelected ? 'filled' : 'outlined'}
                                  label={monthName}
                                  aria-pressed={isSelected}
                                  onClick={() => toggle(m)}
                                  data-testid={`propagation-month-${index}-${m}`}
                                />
                              );
                            })}
                          </Box>
                        </Box>
                      );
                    }}
                  />

                  <FormSelectField
                    name={`propagation_configs.${index}.wood_stage`}
                    control={control}
                    label={t('pages.species.woodStage')}
                    helperText={t('pages.species.woodStageHelper')}
                    options={[
                      { value: '', label: '—' },
                      ...WOOD_STAGES.map((v) => ({
                        value: v,
                        label: t(`enums.woodStage.${v}`),
                      })),
                    ]}
                  />
                  <FormSelectField
                    name={`propagation_configs.${index}.difficulty`}
                    control={control}
                    label={t('pages.species.propagationDifficulty')}
                    options={[
                      { value: '', label: '—' },
                      ...PROPAGATION_DIFFICULTIES.map((v) => ({
                        value: v,
                        label: t(`enums.propagationDifficulty.${v}`),
                      })),
                    ]}
                  />
                  <FormTextField
                    name={`propagation_configs.${index}.notes`}
                    control={control}
                    label={t('pages.species.propagationNotesLabel')}
                    helperText={t('pages.species.propagationNotesHelper')}
                    multiline
                    minRows={2}
                    maxRows={6}
                  />
                </CardContent>
              </Card>
            ))}
          </Box>

          <Button
            variant="outlined"
            size="small"
            startIcon={<AddIcon />}
            onClick={() =>
              appendPropagation({
                method: 'seed',
                months: [],
                wood_stage: null,
                difficulty: null,
                notes: '',
              })
            }
            data-testid="add-propagation-method"
            sx={{ mt: 1.5 }}
          >
            {t('pages.species.addPropagationMethod')}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
}
