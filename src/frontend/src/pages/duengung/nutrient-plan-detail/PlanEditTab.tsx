import type { FormEventHandler } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Collapse from '@mui/material/Collapse';
import Slider from '@mui/material/Slider';
import Checkbox from '@mui/material/Checkbox';
import FormControlLabel from '@mui/material/FormControlLabel';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import { Controller, type Control } from 'react-hook-form';
import ExpertiseFieldWrapper from '@/components/common/ExpertiseFieldWrapper';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormChipInput from '@/components/form/FormChipInput';
import FormActions from '@/components/form/FormActions';
import type { ScheduleMode } from '@/api/types';
import {
  substrateTypes,
  applicationMethods,
  WEEKDAY_KEYS,
  FORM_MAX_WIDTH,
  READING_COL_MAX,
  type EditFormData,
} from './nutrientPlanSchema';

interface PlanEditTabProps {
  control: Control<EditFormData>;
  /** Pre-bound react-hook-form submit handler (handleSubmit(onSave)). */
  onSubmit: FormEventHandler<HTMLFormElement>;
  isReadOnly: boolean;
  saving: boolean;
  isDirty: boolean;
  onCancel: () => void;
  scheduleMode: ScheduleMode;
  scheduleEnabled: boolean;
  weekdaySchedule: number[];
  onWeekdayToggle: (dayIndex: number) => void;
}

/**
 * Nutrient-plan master-data edit form (REQ-004). Presentational RHF section — it
 * owns no data of its own; the parent supplies the `control`, the bound submit
 * handler and the watched schedule values. Behaviour is identical to the inline
 * form it was extracted from (AP-20).
 */
export default function PlanEditTab({
  control,
  onSubmit,
  isReadOnly,
  saving,
  isDirty,
  onCancel,
  scheduleMode,
  scheduleEnabled,
  weekdaySchedule,
  onWeekdayToggle,
}: PlanEditTabProps) {
  const { t } = useTranslation();

  return (
    <Box component="form" onSubmit={onSubmit} sx={{ maxWidth: FORM_MAX_WIDTH, display: 'flex', flexDirection: 'column', gap: 4 }}>
      <Typography variant="body2" color="text.secondary">
        {t('pages.nutrientPlans.editIntro')}
      </Typography>

      {/* UI-NFR-018 R-027: when read-only the whole form must reject input, not
        just hide the save button — fieldset[disabled] grays out and disables
        every native form control beneath it (matches SpeciesEditTab pattern). */}
      <Box
        component="fieldset"
        disabled={isReadOnly}
        sx={{ border: 'none', p: 0, m: 0, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 4 }}
      >
      {/* UI-NFR-008 R-061: Master-detail layout — left column = General (identification +
          description, reading-width), right column = stacked compact panel (Advanced).
          Schedule and the phases timeline remain full-width below (R-058). */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: `minmax(0, ${READING_COL_MAX}px) 1fr` },
          gap: 4,
          alignItems: 'start',
        }}
      >
        {/* ── Section: General (master column, reading-width) ── */}
        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.nutrientPlans.sectionGeneral')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.nutrientPlans.sectionGeneralDesc')}
            </Typography>
            <FormTextField
              name="name"
              control={control}
              label={t('pages.nutrientPlans.name')}
              required
              autoFocus
            />
            {/* UI-NFR-008 R-054 + R-055: prose field capped at reading width */}
            <Box sx={{ maxWidth: READING_COL_MAX }}>
              <FormTextField
                name="description"
                control={control}
                label={t('pages.nutrientPlans.description')}
                multiline
                minRows={4}
                maxRows={14}
              />
            </Box>
            <FormSelectField
              name="recommended_substrate_type"
              control={control}
              label={t('pages.nutrientPlans.substrateType')}
              options={substrateTypes.map((v) => ({
                value: v,
                label: t(`enums.substrateType.${v}`),
              }))}
            />
            <ExpertiseFieldWrapper minLevel="expert">
              <FormSelectField
                name="reference_substrate_type"
                control={control}
                label={t('pages.nutrientPlans.referenceSubstrateType')}
                options={substrateTypes.map((v) => ({
                  value: v,
                  label: t(`enums.substrateType.${v}`),
                }))}
              />
            </ExpertiseFieldWrapper>
            <FormTextField
              name="author"
              control={control}
              label={t('pages.nutrientPlans.author')}
            />
            <FormSwitchField
              name="is_template"
              control={control}
              label={t('pages.nutrientPlans.isTemplate')}
            />
            <FormTextField
              name="version"
              control={control}
              label={t('pages.nutrientPlans.version')}
            />
            <FormChipInput
              name="tags"
              control={control}
              label={t('pages.nutrientPlans.tags')}
              placeholder={t('pages.nutrientPlans.tagsPlaceholder')}
            />
          </CardContent>
        </Card>

        {/* ── Detail column: Advanced (compact, R-057) ── */}
        <ExpertiseFieldWrapper minLevel="intermediate">
          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.nutrientPlans.sectionAdvanced')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.nutrientPlans.sectionAdvancedDesc')}
              </Typography>

              {/* Water Mix Ratio */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {t('pages.nutrientPlans.waterMixRatio')}
                </Typography>
                <Controller
                  name="water_mix_ratio_ro_percent"
                  control={control}
                  render={({ field }) => (
                    <Slider
                      value={field.value ?? 0}
                      onChange={(_, val) => field.onChange(val as number || null)}
                      min={0}
                      max={100}
                      step={5}
                      valueLabelDisplay="auto"
                      valueLabelFormat={(v) => `${v}%`}
                      marks={[
                        { value: 0, label: '0%' },
                        { value: 50, label: '50%' },
                        { value: 100, label: '100%' },
                      ]}
                      data-testid="water-mix-slider"
                    />
                  )}
                />
              </Box>

              {/* Cycle Restart */}
              <FormNumberField
                name="cycle_restart_from_sequence"
                control={control}
                label={t('pages.nutrientPlans.cycleRestartFromSequence')}
                min={1}
                helperText={t('pages.nutrientPlans.cycleRestartHelper')}
              />
            </CardContent>
          </Card>
        </ExpertiseFieldWrapper>
      </Box>

      {/* Section: Watering Schedule (full-width below master-detail, R-058) */}
      <Card variant="outlined">
        <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
          <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
            {t('pages.nutrientPlans.sectionSchedule')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.nutrientPlans.sectionScheduleDesc')}
          </Typography>

          <FormSwitchField
            name="schedule_enabled"
            control={control}
            label={t('pages.wateringSchedule.title')}
          />

          <Collapse in={scheduleEnabled}>
            <Box sx={{ pl: 1, pt: 1 }}>
              {/* Schedule Mode Toggle */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {t('pages.wateringSchedule.mode')}
                </Typography>
                <Controller
                  name="schedule_mode"
                  control={control}
                  render={({ field }) => (
                    <ToggleButtonGroup
                      value={field.value}
                      exclusive
                      onChange={(_, value: ScheduleMode | null) => {
                        if (value) field.onChange(value);
                      }}
                      size="small"
                      fullWidth
                    >
                      <ToggleButton value="weekdays">
                        {t('pages.wateringSchedule.weekdays')}
                      </ToggleButton>
                      <ToggleButton value="interval">
                        {t('pages.wateringSchedule.interval')}
                      </ToggleButton>
                    </ToggleButtonGroup>
                  )}
                />
              </Box>

              {/* Weekday Checkboxes */}
              {scheduleMode === 'weekdays' && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                    {t('pages.wateringSchedule.weekdays')}
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {WEEKDAY_KEYS.map((dayKey, index) => (
                      <FormControlLabel
                        key={dayKey}
                        control={
                          <Checkbox
                            checked={weekdaySchedule.includes(index)}
                            onChange={() => onWeekdayToggle(index)}
                            size="small"
                          />
                        }
                        label={t(`pages.wateringSchedule.${dayKey}`)}
                      />
                    ))}
                  </Box>
                </Box>
              )}

              {/* Interval Days */}
              {scheduleMode === 'interval' && (
                <FormNumberField
                  name="interval_days"
                  control={control}
                  label={t('pages.wateringSchedule.intervalDays')}
                  min={1}
                  max={90}
                  step={1}
                />
              )}

              {/* Preferred Time */}
              <Controller
                name="preferred_time"
                control={control}
                render={({ field, fieldState: { error } }) => (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      {t('pages.wateringSchedule.preferredTime')}
                    </Typography>
                    <input
                      type="time"
                      value={field.value}
                      onChange={field.onChange}
                      onBlur={field.onBlur}
                      style={{
                        width: '100%',
                        padding: '0.5rem',
                        fontSize: '1rem',
                        border: error ? '1px solid red' : '1px solid rgba(0,0,0,0.23)',
                        borderRadius: '4px',
                      }}
                    />
                    {error?.message && (
                      <Typography variant="caption" color="error">
                        {error.message}
                      </Typography>
                    )}
                  </Box>
                )}
              />

              {/* Application Method */}
              <FormSelectField
                name="application_method"
                control={control}
                label={t('pages.wateringSchedule.applicationMethod')}
                options={applicationMethods.map((v) => ({
                  value: v,
                  label: t(`enums.applicationMethod.${v}`),
                }))}
              />

              {/* Reminder Hours Before */}
              <FormNumberField
                name="reminder_hours_before"
                control={control}
                label={t('pages.wateringSchedule.reminderHoursBefore')}
                min={0}
                max={24}
                step={1}
              />

              {/* Times Per Day */}
              <FormNumberField
                name="times_per_day"
                control={control}
                label={t('pages.wateringSchedule.timesPerDay')}
                min={1}
                max={6}
                step={1}
              />
            </Box>
          </Collapse>
        </CardContent>
      </Card>

      <Typography variant="caption" color="text.secondary">* {t('common.required')}</Typography>
      </Box>

      {/* UI-NFR-018 R-011: hide save/cancel actions for read-only system/enrichment data */}
      {!isReadOnly && (
        <FormActions
          onCancel={onCancel}
          loading={saving}
          disabled={!isDirty}
        />
      )}
      {isReadOnly && (
        <Typography variant="body2" color="text.secondary">
          {t('common.origin.readOnlyHint')}
        </Typography>
      )}
    </Box>
  );
}
