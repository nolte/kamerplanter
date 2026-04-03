import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Autocomplete from '@mui/material/Autocomplete';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormChipInput from '@/components/form/FormChipInput';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import * as api from '@/api/endpoints/activities';
import type { Activity } from '@/api/types';

const schema = z.object({
  name: z.string().min(1).max(200),
  name_de: z.string(),
  description: z.string(),
  description_de: z.string(),
  category: z.enum(['training_hst', 'training_lst', 'pruning', 'ausgeizen', 'transplant', 'harvest_prep', 'propagation', 'general']),
  stress_level: z.enum(['none', 'low', 'medium', 'high']),
  skill_level: z.enum(['beginner', 'intermediate', 'advanced', 'expert']),
  recovery_days_default: z.number().min(0),
  estimated_duration_minutes: z.number().min(1).nullable(),
  requires_photo: z.boolean(),
  species_compatible: z.array(z.string()),
  forbidden_phases: z.array(z.string()),
  restricted_sub_phases: z.array(z.string()),
  tools_required: z.array(z.string()),
  tags: z.array(z.string()),
  sort_order: z.number().min(0),
});

type FormData = z.infer<typeof schema>;

/** Spacing between form panels (UI-NFR-008 R-039: 24px = spacing.lg) */
const PANEL_GAP = 4;

export default function ActivityDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const [activity, setActivity] = useState<Activity | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const {
    control,
    handleSubmit,
    reset,
    watch,
    formState: { isDirty },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      name_de: '',
      description: '',
      description_de: '',
      category: 'general',
      stress_level: 'none',
      skill_level: 'beginner',
      recovery_days_default: 0,
      estimated_duration_minutes: null,
      requires_photo: false,
      species_compatible: [],
      forbidden_phases: [],
      restricted_sub_phases: [],
      tools_required: [],
      tags: [],
      sort_order: 0,
    },
  });

  const speciesCompatible = watch('species_compatible');

  useEffect(() => {
    if (!key) return;
    setLoading(true);
    api.getActivity(key)
      .then((data) => {
        setActivity(data);
        reset({
          name: data.name,
          name_de: data.name_de,
          description: data.description,
          description_de: data.description_de,
          category: data.category,
          stress_level: data.stress_level,
          skill_level: data.skill_level,
          recovery_days_default: data.recovery_days_default,
          estimated_duration_minutes: data.estimated_duration_minutes,
          requires_photo: data.requires_photo,
          species_compatible: data.species_compatible,
          forbidden_phases: data.forbidden_phases,
          restricted_sub_phases: data.restricted_sub_phases,
          tools_required: data.tools_required,
          tags: data.tags,
          sort_order: data.sort_order,
        });
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [key, reset]);

  const onSubmit = async (data: FormData) => {
    if (!key) return;
    try {
      setSaving(true);
      const updated = await api.updateActivity(key, {
        ...data,
        estimated_duration_minutes: data.estimated_duration_minutes ?? undefined,
      });
      setActivity(updated);
      reset({
        name: updated.name,
        name_de: updated.name_de,
        description: updated.description,
        description_de: updated.description_de,
        category: updated.category,
        stress_level: updated.stress_level,
        skill_level: updated.skill_level,
        recovery_days_default: updated.recovery_days_default,
        estimated_duration_minutes: updated.estimated_duration_minutes,
        requires_photo: updated.requires_photo,
        species_compatible: updated.species_compatible,
        forbidden_phases: updated.forbidden_phases,
        restricted_sub_phases: updated.restricted_sub_phases,
        tools_required: updated.tools_required,
        tags: updated.tags,
        sort_order: updated.sort_order,
      });
      notification.success(t('common.saved'));
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!key) return;
    try {
      await api.deleteActivity(key);
      notification.success(t('common.deleted'));
      navigate('/stammdaten/activities');
    } catch (err) {
      handleError(err);
    }
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} />;
  if (!activity) return <ErrorDisplay error={t('errors.notFound')} />;

  const lang = i18n.language?.startsWith('en') ? 'en' : 'de';
  const displayName = lang === 'en' ? activity.name : activity.name_de || activity.name;

  const categoryOptions = [
    'training_hst', 'training_lst', 'pruning', 'ausgeizen',
    'transplant', 'harvest_prep', 'propagation', 'general',
  ].map((v) => ({ value: v, label: t(`enums.activityCategory.${v}`) }));

  const stressOptions = ['none', 'low', 'medium', 'high'].map((v) => ({
    value: v, label: t(`enums.stressLevel.${v}`),
  }));

  const skillOptions = ['beginner', 'intermediate', 'advanced', 'expert'].map((v) => ({
    value: v, label: t(`enums.skillLevel.${v}`),
  }));

  return (
    <Box data-testid="activity-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <PageTitle
        title={displayName}
        action={
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            {activity.is_system && (
              <Chip label={t('pages.activities.systemActivity')} color="info" size="small" />
            )}
            {!activity.is_system && (
              <Button color="error" onClick={() => setDeleteOpen(true)}>
                {t('common.delete')}
              </Button>
            )}
          </Box>
        }
      />

      {activity.is_system && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {t('pages.activities.systemHint')}
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate sx={{ maxWidth: 900, display: 'flex', flexDirection: 'column', gap: PANEL_GAP }}>
        <Typography variant="body2" color="text.secondary">
          {t('pages.activities.editIntro')}
        </Typography>

        {/* ── Panel 1: Bezeichnung ── */}
        {/* UI-NFR-008 R-037/R-038/R-040: Card panel, h6 heading, required fields first */}
        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.activities.sectionIdentification')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.activities.sectionIdentificationDesc')}
            </Typography>
            <FormRow>
              <FormTextField name="name" control={control} label={t('pages.activities.nameEn')} required autoFocus />
              <FormTextField name="name_de" control={control} label={t('pages.activities.nameDe')} />
            </FormRow>
            <FormRow>
              <FormTextField name="description" control={control} label={t('pages.activities.descriptionEn')} multiline rows={3} />
              <FormTextField name="description_de" control={control} label={t('pages.activities.descriptionDe')} multiline rows={3} />
            </FormRow>
          </CardContent>
        </Card>

        {/* ── Panel 2: Klassifizierung ── */}
        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.activities.sectionClassification')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.activities.sectionClassificationDesc')}
            </Typography>
            <FormRow>
              <FormSelectField name="category" control={control} label={t('pages.activities.category')} options={categoryOptions} />
              <FormSelectField name="skill_level" control={control} label={t('pages.activities.skillLevel')} options={skillOptions} />
            </FormRow>
            <FormRow>
              <FormSelectField
                name="stress_level"
                control={control}
                label={t('pages.activities.stressLevel')}
                helperText={t('pages.activities.stressLevelHint')}
                options={stressOptions}
              />
              <FormNumberField
                name="recovery_days_default"
                control={control}
                label={t('pages.activities.recoveryDays')}
                helperText={t('pages.activities.recoveryDaysHint')}
                min={0}
                suffix="d"
              />
            </FormRow>
          </CardContent>
        </Card>

        {/* ── Panel 3: Ausführung ── */}
        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.activities.sectionExecution')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.activities.sectionExecutionDesc')}
            </Typography>
            <FormRow>
              <FormNumberField
                name="estimated_duration_minutes"
                control={control}
                label={t('pages.activities.estimatedDuration')}
                min={1}
                suffix="min"
              />
              <FormSwitchField
                name="requires_photo"
                control={control}
                label={t('pages.activities.requiresPhoto')}
                helperText={t('pages.activities.requiresPhotoHint')}
              />
            </FormRow>
            <FormChipInput
              name="tools_required"
              control={control}
              label={t('pages.activities.toolsRequired')}
              helperText={t('pages.activities.toolsRequiredHint')}
            />
          </CardContent>
        </Card>

        {/* ── Panel 4: Geltungsbereich ── */}
        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.activities.sectionScope')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.activities.sectionScopeDesc')}
            </Typography>
            <Alert
              severity={speciesCompatible.length === 0 ? 'success' : 'info'}
              sx={{ mb: 2 }}
              icon={false}
            >
              {speciesCompatible.length === 0
                ? t('pages.activities.scopeUniversalInfo')
                : t('pages.activities.scopeRestrictedInfo', { count: speciesCompatible.length })}
            </Alert>
            <Controller
              name="species_compatible"
              control={control}
              render={({ field }) => (
                <Autocomplete
                  multiple
                  freeSolo
                  options={[]}
                  value={field.value}
                  onChange={(_, newValue) => field.onChange(newValue)}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => {
                      const { key: tagKey, ...tagProps } = getTagProps({ index });
                      return <Chip key={tagKey} label={option} size="small" color="primary" variant="outlined" {...tagProps} />;
                    })
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label={t('pages.activities.speciesCompatible')}
                      helperText={t('pages.activities.speciesCompatibleHint')}
                    />
                  )}
                />
              )}
            />
          </CardContent>
        </Card>

        {/* ── Panel 5: Phasenbeschränkungen ── */}
        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.activities.sectionPhaseRestrictions')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.activities.sectionPhaseRestrictionsDesc')}
            </Typography>
            <FormChipInput
              name="forbidden_phases"
              control={control}
              label={t('pages.activities.forbiddenPhases')}
              helperText={t('pages.activities.forbiddenPhasesHint')}
            />
            <FormChipInput
              name="restricted_sub_phases"
              control={control}
              label={t('pages.activities.restrictedSubPhases')}
              helperText={t('pages.activities.restrictedSubPhasesHint')}
            />
          </CardContent>
        </Card>

        {/* ── Panel 6: Tags & Sortierung ── */}
        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.activities.sectionMeta')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.activities.sectionMetaDesc')}
            </Typography>
            <FormChipInput
              name="tags"
              control={control}
              label={t('pages.activities.tags')}
              helperText={t('pages.activities.tagsHint')}
            />
            <FormNumberField
              name="sort_order"
              control={control}
              label={t('pages.activities.sortOrder')}
              helperText={t('pages.activities.sortOrderHint')}
              min={0}
              step={1}
            />
          </CardContent>
        </Card>

        {/* UI-NFR-008 R-025: Required field legend */}
        <Typography variant="caption" color="text.secondary">
          * {t('common.required')}
        </Typography>

        <FormActions
          onCancel={() => navigate('/stammdaten/activities')}
          loading={saving}
          disabled={!isDirty}
        />
      </Box>

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.confirmDelete')}
        message={t('pages.activities.deleteConfirm', { name: displayName })}
        onConfirm={handleDelete}
        onCancel={() => setDeleteOpen(false)}
      />
    </Box>
  );
}
