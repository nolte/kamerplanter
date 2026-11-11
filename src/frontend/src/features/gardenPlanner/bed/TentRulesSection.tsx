/**
 * The tent rules of a location (REQ-053 WP 10.11, W-016): the light-schedule hints of a tent or shelf level
 * (W-016.6, V-23 - a hint, never an error), the location's own neighbourhood factor (W-016.8) and its lamp height
 * and canopy distance (W-016.2/3, stored for a later light model - nothing is computed from them yet).
 *
 * Shown on the location page of every location whose type carries a slot layout (`supports_layout`: beds, tents,
 * shelves). The values are written with `PATCH /locations/{key}`; a viewer sees them read-only.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Form from '@/components/form/Form';
import FormActions from '@/components/form/FormActions';
import FormNumberField from '@/components/form/FormNumberField';
import FormRow from '@/components/form/FormRow';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import type { LocationLighting } from '@/api/types';
import { useApiError } from '@/hooks/useApiError';
import { useNotification } from '@/hooks/useNotification';
import { patchTentRules } from './bedApi';
import {
  MAX_ADJACENCY_FACTOR,
  MAX_LAMP_HEIGHT_CM,
  buildTentRulesSchema,
  formToTentRulesPatch,
  tentRulesToForm,
  type TentRulesFormData,
} from './tentRulesForm';
import { groupPhaseLabels } from './tentPhaseLabel';
import type { PhotoperiodGroup, TentHint } from './types';

interface TentRulesSectionProps {
  locationKey: string;
  /** The location's type carries a slot layout: the factor and the lighting can be edited. */
  supportsLayout: boolean;
  adjacencyFactor: number | null | undefined;
  lighting: LocationLighting | null | undefined;
  hints: TentHint[] | undefined;
  canEdit: boolean;
  /** The values were stored; the page reloads the summary. */
  onSaved: () => void;
}

function TentHintAlert({ hint }: { hint: TentHint }) {
  const { t, i18n } = useTranslation();
  const hoursFormat = useMemo(() => new Intl.NumberFormat(i18n.language, { maximumFractionDigits: 2 }), [i18n.language]);
  const group = (item: PhotoperiodGroup) => {
    const phases = groupPhaseLabels(t, i18n, item);
    return t(phases.length > 0 ? 'pages.bed.tentRules.hints.group' : 'pages.bed.tentRules.hints.groupNoPhase', {
      hours: hoursFormat.format(item.photoperiod_hours),
      count: item.plant_count,
      phases: phases.join(', '),
    });
  };
  const conflict = hint.code === 'tent.photoperiod_conflict';
  const unknown =
    hint.unknown_plant_count > 0
      ? t(conflict ? 'pages.bed.tentRules.hints.alsoUnknown' : 'pages.bed.tentRules.hints.photoperiodUnknown', {
          count: hint.unknown_plant_count,
        })
      : '';
  const names = hint.unknown_plant_names ?? [];
  const more = hint.unknown_plant_count - names.length;
  const affected =
    names.length === 0
      ? ''
      : more > 0
        ? t('pages.bed.tentRules.hints.unknownPlantsMore', { names: names.join(', '), count: more })
        : t('pages.bed.tentRules.hints.unknownPlants', { names: names.join(', ') });
  return (
    <Alert
      severity={hint.severity}
      role="status"
      data-testid={conflict ? 'tent-hint-photoperiod-conflict' : 'tent-hint-photoperiod-unknown'}
    >
      <AlertTitle>
        {t(conflict ? 'pages.bed.tentRules.hints.conflictTitle' : 'pages.bed.tentRules.hints.unknownTitle')}
      </AlertTitle>
      {conflict && (
        <Typography variant="body2">
          {t('pages.bed.tentRules.hints.conflict', { groups: hint.groups.map(group).join('; ') })}
        </Typography>
      )}
      {unknown && <Typography variant="body2">{unknown}</Typography>}
      {affected && (
        <Typography variant="body2" data-testid="tent-hint-unknown-plants">
          {affected}
        </Typography>
      )}
    </Alert>
  );
}

export default function TentRulesSection({
  locationKey,
  supportsLayout,
  adjacencyFactor,
  lighting,
  hints,
  canEdit,
  onSaved,
}: TentRulesSectionProps) {
  const { t } = useTranslation();
  const { handleError } = useApiError();
  const notification = useNotification();
  const [saving, setSaving] = useState(false);

  const initial = useMemo(() => tentRulesToForm(adjacencyFactor, lighting), [adjacencyFactor, lighting]);
  const resolver = useMemo(() => zodResolver(buildTentRulesSchema(t)), [t]);
  const { control, handleSubmit, reset, formState } = useForm<TentRulesFormData>({
    resolver,
    defaultValues: initial,
    disabled: !canEdit,
  });

  // A reloaded summary replaces the form only when its values changed and nothing is being edited.
  const initialKey = useMemo(() => JSON.stringify(initial), [initial]);
  const dirtyRef = useRef(false);
  useEffect(() => {
    dirtyRef.current = formState.isDirty;
  });
  useEffect(() => {
    if (!dirtyRef.current) reset(initial);
    // `initial` is derived from `initialKey`; only a change of content may reset the form.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialKey, reset]);

  const onSubmit = async (data: TentRulesFormData) => {
    setSaving(true);
    try {
      await patchTentRules(locationKey, formToTentRulesPatch(data, lighting));
      notification.success(t('pages.bed.tentRules.saved'));
      reset(data);
      onSaved();
    } catch (error) {
      handleError(error);
    } finally {
      setSaving(false);
    }
  };

  const shownHints = hints ?? [];
  if (!supportsLayout && shownHints.length === 0) return null;

  return (
    <Stack spacing={2} sx={{ mt: 3, maxWidth: 1280 }} data-testid="tent-rules-section">
      {shownHints.map((hint) => (
        <TentHintAlert key={hint.code} hint={hint} />
      ))}
      {supportsLayout && (
        <Card variant="outlined">
          <CardContent>
            <UnsavedChangesGuard dirty={formState.isDirty} />
            <Typography variant="h6" component="h2" sx={{ mb: 0.5 }}>
              {t('pages.bed.tentRules.title')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {canEdit ? t('pages.bed.tentRules.intro') : t('pages.bed.tentRules.introReadOnly')}
            </Typography>
            <Form onSubmit={handleSubmit(onSubmit)} aria-label={t('pages.bed.tentRules.title')}>
              <FormNumberField
                name="adjacency_factor"
                control={control}
                label={t('pages.bed.tentRules.adjacencyFactor')}
                helperText={t('pages.bed.tentRules.adjacencyFactorHelper')}
                placeholder={t('pages.bed.tentRules.adjacencyFactorPlaceholder')}
                min={0}
                max={MAX_ADJACENCY_FACTOR}
                step="any"
                inputMode="decimal"
              />
              <Typography variant="subtitle2" component="h3" sx={{ mt: 1 }}>
                {t('pages.bed.tentRules.lighting')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('pages.bed.tentRules.lightingIntro')}
              </Typography>
              <FormRow>
                <FormNumberField
                  name="lamp_height_cm"
                  control={control}
                  label={t('pages.bed.tentRules.lampHeight')}
                  helperText={t('pages.bed.tentRules.lampHeightHelper')}
                  min={0}
                  max={MAX_LAMP_HEIGHT_CM}
                  step="any"
                  inputMode="decimal"
                  suffix="cm"
                />
                <FormNumberField
                  name="canopy_distance_cm"
                  control={control}
                  label={t('pages.bed.tentRules.canopyDistance')}
                  helperText={t('pages.bed.tentRules.canopyDistanceHelper')}
                  min={0}
                  max={MAX_LAMP_HEIGHT_CM}
                  step="any"
                  inputMode="decimal"
                  suffix="cm"
                />
              </FormRow>
              {canEdit && (
                <FormActions onCancel={() => reset(initial)} loading={saving} disabled={!formState.isDirty} />
              )}
            </Form>
          </CardContent>
        </Card>
      )}
    </Stack>
  );
}
