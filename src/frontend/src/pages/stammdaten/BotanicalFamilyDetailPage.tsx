import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import DeleteIcon from '@mui/icons-material/Delete';
import ParkIcon from '@mui/icons-material/Park';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import EmptyState from '@/components/common/EmptyState';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormMultiSelectField from '@/components/form/FormMultiSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormChipInput from '@/components/form/FormChipInput';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchBotanicalFamily, clearCurrent } from '@/store/slices/botanicalFamiliesSlice';
import * as api from '@/api/endpoints/botanicalFamilies';
import type { Species } from '@/api/types';

const growthHabitValues = ['herb', 'shrub', 'tree', 'vine', 'groundcover'] as const;
const pollinationValues = ['insect', 'wind', 'self'] as const;

const schema = z.object({
  name: z.string().min(1).refine((v) => v.endsWith('aceae'), {
    message: "Muss auf '-aceae' enden",
  }),
  common_name_de: z.string(),
  common_name_en: z.string(),
  order: z.string(),
  description: z.string(),
  typical_nutrient_demand: z.enum(['light', 'medium', 'heavy']),
  nitrogen_fixing: z.boolean(),
  typical_root_depth: z.enum(['shallow', 'medium', 'deep']),
  soil_ph_min: z.union([z.number().min(3).max(9), z.literal('')]),
  soil_ph_max: z.union([z.number().min(3).max(9), z.literal('')]),
  frost_tolerance: z.enum(['sensitive', 'moderate', 'hardy', 'very_hardy']),
  typical_growth_forms: z.array(z.enum(growthHabitValues)).min(1),
  common_pests: z.array(z.string()),
  common_diseases: z.array(z.string()),
  pollination_type: z.array(z.enum(pollinationValues)).min(1),
  rotation_category: z.string(),
});

type FormData = z.infer<typeof schema>;

/** Spacing between form panels (UI-NFR-008 R-039: 24px = spacing.lg) */
const PANEL_GAP = 4;

export default function BotanicalFamilyDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { current, loading, error } = useAppSelector((s) => s.botanicalFamilies);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [familySpecies, setFamilySpecies] = useState<Species[]>([]);

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      common_name_de: '',
      common_name_en: '',
      order: '',
      description: '',
      typical_nutrient_demand: 'medium',
      nitrogen_fixing: false,
      typical_root_depth: 'medium',
      soil_ph_min: '',
      soil_ph_max: '',
      frost_tolerance: 'moderate',
      typical_growth_forms: ['herb'],
      common_pests: [],
      common_diseases: [],
      pollination_type: ['insect'],
      rotation_category: '',
    },
  });

  useEffect(() => {
    if (key) {
      dispatch(fetchBotanicalFamily(key));
      api.listSpeciesByFamily(key).then(setFamilySpecies).catch(() => {});
    }
    return () => {
      dispatch(clearCurrent());
    };
  }, [key, dispatch]);

  useEffect(() => {
    if (current) {
      reset({
        name: current.name,
        common_name_de: current.common_name_de,
        common_name_en: current.common_name_en,
        order: current.order ?? '',
        description: current.description,
        typical_nutrient_demand: current.typical_nutrient_demand,
        nitrogen_fixing: current.nitrogen_fixing,
        typical_root_depth: current.typical_root_depth,
        soil_ph_min: current.soil_ph_preference?.min_ph ?? '',
        soil_ph_max: current.soil_ph_preference?.max_ph ?? '',
        frost_tolerance: current.frost_tolerance,
        typical_growth_forms: current.typical_growth_forms,
        common_pests: current.common_pests,
        common_diseases: current.common_diseases,
        pollination_type: current.pollination_type,
        rotation_category: current.rotation_category,
      });
    }
  }, [current, reset]);

  const onSubmit = async (data: FormData) => {
    if (!key) return;
    try {
      setSaving(true);
      const { soil_ph_min, soil_ph_max, ...rest } = data;
      const payload = {
        ...rest,
        order: data.order || undefined,
        soil_ph_preference:
          typeof soil_ph_min === 'number' && typeof soil_ph_max === 'number'
            ? { min_ph: soil_ph_min, max_ph: soil_ph_max }
            : undefined,
      };
      await api.updateBotanicalFamily(key, payload);
      notification.success(t('common.save'));
      dispatch(fetchBotanicalFamily(key));
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async () => {
    if (!key) return;
    try {
      await api.deleteBotanicalFamily(key);
      notification.success(t('common.delete'));
      navigate('/stammdaten/botanical-families');
    } catch (err) {
      handleError(err);
    }
    setDeleteOpen(false);
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} onRetry={() => navigate(-1)} />;

  const nutrientDemandOptions = [
    { value: 'light', label: t('enums.nutrientDemand.light') },
    { value: 'medium', label: t('enums.nutrientDemand.medium') },
    { value: 'heavy', label: t('enums.nutrientDemand.heavy') },
  ];

  const rootDepthOptions = [
    { value: 'shallow', label: t('enums.rootDepth.shallow') },
    { value: 'medium', label: t('enums.rootDepth.medium') },
    { value: 'deep', label: t('enums.rootDepth.deep') },
  ];

  const frostToleranceOptions = [
    { value: 'sensitive', label: t('enums.frostTolerance.sensitive') },
    { value: 'moderate', label: t('enums.frostTolerance.moderate') },
    { value: 'hardy', label: t('enums.frostTolerance.hardy') },
    { value: 'very_hardy', label: t('enums.frostTolerance.very_hardy') },
  ];

  const growthFormOptions = [
    { value: 'herb', label: t('enums.growthHabit.herb') },
    { value: 'shrub', label: t('enums.growthHabit.shrub') },
    { value: 'tree', label: t('enums.growthHabit.tree') },
    { value: 'vine', label: t('enums.growthHabit.vine') },
    { value: 'groundcover', label: t('enums.growthHabit.groundcover') },
  ];

  const pollinationOptions = [
    { value: 'insect', label: t('enums.pollinationType.insect') },
    { value: 'wind', label: t('enums.pollinationType.wind') },
    { value: 'self', label: t('enums.pollinationType.self') },
  ];

  return (
    <Box data-testid="botanical-family-detail-page">
      <UnsavedChangesGuard dirty={isDirty} />
      <PageTitle
        title={current?.name ?? t('entities.botanicalFamily')}
        action={
          <Button
            color="error"
            startIcon={<DeleteIcon />}
            onClick={() => setDeleteOpen(true)}
          >
            {t('common.delete')}
          </Button>
        }
      />

      <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 900, display: 'flex', flexDirection: 'column', gap: PANEL_GAP }}>
        <Typography variant="body2" color="text.secondary">
          {t('pages.botanicalFamilies.editIntro')}
        </Typography>

        {/* ── Panel 1: Taxonomie (Pflichtfelder zuerst) ── */}
        {/* UI-NFR-008 R-037/R-038/R-040: Card panel, h6 heading, required fields first */}
        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.botanicalFamilies.sectionTaxonomy')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.botanicalFamilies.sectionTaxonomyDesc')}
            </Typography>
            <FormTextField
              name="name"
              control={control}
              label={t('pages.botanicalFamilies.name')}
              required
              autoFocus
              helperText={t('pages.botanicalFamilies.nameHelper')}
            />
            <FormRow>
              <FormTextField
                name="common_name_de"
                control={control}
                label={t('pages.botanicalFamilies.commonNameDe')}
                helperText={t('pages.botanicalFamilies.commonNameDeHelper')}
              />
              <FormTextField
                name="common_name_en"
                control={control}
                label={t('pages.botanicalFamilies.commonNameEn')}
                helperText={t('pages.botanicalFamilies.commonNameEnHelper')}
              />
            </FormRow>
            <FormTextField
              name="order"
              control={control}
              label={t('pages.botanicalFamilies.order')}
              helperText={t('pages.botanicalFamilies.orderHelper')}
            />
            <FormTextField
              name="description"
              control={control}
              label={t('pages.botanicalFamilies.description')}
              multiline
              rows={2}
              helperText={t('pages.botanicalFamilies.descriptionHelper')}
            />
          </CardContent>
        </Card>

        {/* ── Panel 2: Wachstum & Nährstoffe ── */}
        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.botanicalFamilies.sectionGrowth')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.botanicalFamilies.sectionGrowthDesc')}
            </Typography>
            <FormRow>
              <FormSelectField
                name="typical_nutrient_demand"
                control={control}
                label={t('pages.botanicalFamilies.nutrientDemand')}
                options={nutrientDemandOptions}
                helperText={t('pages.botanicalFamilies.nutrientDemandHelper')}
              />
              <FormSelectField
                name="typical_root_depth"
                control={control}
                label={t('pages.botanicalFamilies.rootDepth')}
                options={rootDepthOptions}
                helperText={t('pages.botanicalFamilies.rootDepthHelper')}
              />
            </FormRow>
            <FormSwitchField
              name="nitrogen_fixing"
              control={control}
              label={t('pages.botanicalFamilies.nitrogenFixing')}
              helperText={t('pages.botanicalFamilies.nitrogenFixingHelper')}
            />
            <FormMultiSelectField
              name="typical_growth_forms"
              control={control}
              label={t('pages.botanicalFamilies.growthForms')}
              options={growthFormOptions}
              required
              helperText={t('pages.botanicalFamilies.growthFormsHelper')}
            />
          </CardContent>
        </Card>

        {/* ── Panel 3: Umgebung & Boden ── */}
        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.botanicalFamilies.sectionEnvironment')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.botanicalFamilies.sectionEnvironmentDesc')}
            </Typography>
            <FormRow>
              <FormNumberField
                name="soil_ph_min"
                control={control}
                label={t('pages.botanicalFamilies.soilPhMin')}
                min={3}
                max={9}
                step={0.1}
                helperText={t('pages.botanicalFamilies.soilPhHelper')}
              />
              <FormNumberField
                name="soil_ph_max"
                control={control}
                label={t('pages.botanicalFamilies.soilPhMax')}
                min={3}
                max={9}
                step={0.1}
              />
            </FormRow>
            <FormSelectField
              name="frost_tolerance"
              control={control}
              label={t('pages.botanicalFamilies.frostTolerance')}
              options={frostToleranceOptions}
              helperText={t('pages.botanicalFamilies.frostToleranceHelper')}
            />
          </CardContent>
        </Card>

        {/* ── Panel 4: Schädlinge & Krankheiten ── */}
        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.botanicalFamilies.sectionPestsAndDiseases')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.botanicalFamilies.sectionPestsAndDiseasesDesc')}
            </Typography>
            <FormRow>
              <FormChipInput
                name="common_pests"
                control={control}
                label={t('pages.botanicalFamilies.commonPests')}
                helperText={t('pages.botanicalFamilies.commonPestsHelper')}
              />
              <FormChipInput
                name="common_diseases"
                control={control}
                label={t('pages.botanicalFamilies.commonDiseases')}
                helperText={t('pages.botanicalFamilies.commonDiseasesHelper')}
              />
            </FormRow>
          </CardContent>
        </Card>

        {/* ── Panel 5: Bestäubung & Fruchtfolge ── */}
        <Card variant="outlined">
          <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
            <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
              {t('pages.botanicalFamilies.sectionReproduction')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.botanicalFamilies.sectionReproductionDesc')}
            </Typography>
            <FormMultiSelectField
              name="pollination_type"
              control={control}
              label={t('pages.botanicalFamilies.pollinationType')}
              options={pollinationOptions}
              required
              helperText={t('pages.botanicalFamilies.pollinationTypeHelper')}
            />
            <FormTextField
              name="rotation_category"
              control={control}
              label={t('pages.botanicalFamilies.rotationCategory')}
              helperText={t('pages.botanicalFamilies.rotationCategoryHelper')}
            />
          </CardContent>
        </Card>

        {/* UI-NFR-008 R-025: Required field legend */}
        <Typography variant="caption" color="text.secondary">
          * {t('common.required')}
        </Typography>

        <FormActions onCancel={() => navigate(-1)} loading={saving} />
      </Box>

      <Divider sx={{ my: 4 }} />

      <Typography variant="h6" sx={{ mb: 1 }}>
        {t('pages.botanicalFamilies.speciesInFamily')}
        {familySpecies.length > 0 && (
          <Chip label={familySpecies.length} size="small" sx={{ ml: 1 }} />
        )}
      </Typography>

      {familySpecies.length === 0 ? (
        <EmptyState
          message={t('pages.botanicalFamilies.noSpeciesInFamily')}
          actionLabel={t('pages.botanicalFamilies.showAllSpeciesFiltered')}
          onAction={() => navigate(`/stammdaten/species?family=${key}`)}
        />
      ) : (
        <List dense>
          {familySpecies.map((s) => (
            <ListItemButton
              key={s.key}
              component={RouterLink}
              to={`/stammdaten/species/${s.key}`}
            >
              <ListItemText
                primary={s.scientific_name}
                secondary={s.common_names.join(', ') || undefined}
                primaryTypographyProps={{ variant: 'body2' }}
              />
              <ParkIcon fontSize="small" sx={{ color: 'text.disabled', ml: 1 }} />
            </ListItemButton>
          ))}
        </List>
      )}

      {familySpecies.length > 0 && (
        <Box sx={{ mt: 1 }}>
          <Button
            variant="outlined"
            size="small"
            component={RouterLink}
            to={`/stammdaten/species?family=${key}`}
          >
            {t('pages.botanicalFamilies.showAllSpeciesFiltered')}
          </Button>
        </Box>
      )}

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: current?.name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />
    </Box>
  );
}
