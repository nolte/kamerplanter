import { useEffect, useState } from 'react';
import { useTabUrl } from '@/hooks/useTabUrl';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import OpacityIcon from '@mui/icons-material/Opacity';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import FormTextField from '@/components/form/FormTextField';
import FormSelectField from '@/components/form/FormSelectField';
import FormNumberField from '@/components/form/FormNumberField';
import FormChipInput from '@/components/form/FormChipInput';
import FormSwitchField from '@/components/form/FormSwitchField';
import FormActions from '@/components/form/FormActions';
import FormRow from '@/components/form/FormRow';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import CultivarListSection from './CultivarListSection';
import GrowingPeriodsSection from './GrowingPeriodsSection';
import LifecycleConfigSection from '@/pages/pflanzen/LifecycleConfigSection';
import SpeciesWorkflowsSection from './SpeciesWorkflowsSection';
import PlantInstanceCreateDialog from '@/pages/pflanzen/PlantInstanceCreateDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useSowingFavorites } from '@/hooks/useSowingFavorites';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchSpecies, clearCurrent } from '@/store/slices/speciesSlice';
import * as api from '@/api/endpoints/species';
import * as familiesApi from '@/api/endpoints/botanicalFamilies';
import * as planApi from '@/api/endpoints/nutrient-plans';
import type { BotanicalFamily, NutrientPlan } from '@/api/types';

const schema = z.object({
  scientific_name: z.string().min(1),
  common_names: z.array(z.string()),
  family_key: z.string().nullable(),
  genus: z.string(),
  growth_habit: z.enum(['herb', 'shrub', 'tree', 'vine', 'groundcover']),
  root_type: z.enum(['fibrous', 'taproot', 'tuberous', 'bulbous']),
  hardiness_zones: z.array(z.string()),
  native_habitat: z.string(),
  allelopathy_score: z.number().min(-1).max(1),
  base_temp: z.number(),
  description: z.string(),
  synonyms: z.array(z.string()),
  taxonomic_authority: z.string(),
  taxonomic_status: z.string(),
  container_suitable: z.enum(['yes', 'limited', 'no', '']).nullable(),
  recommended_container_volume_l: z.string(),
  min_container_depth_cm: z.number().min(1).max(200).nullable(),
  mature_height_cm: z.string(),
  mature_width_cm: z.string(),
  spacing_cm: z.string(),
  indoor_suitable: z.enum(['yes', 'limited', 'no', '']).nullable(),
  balcony_suitable: z.enum(['yes', 'limited', 'no', '']).nullable(),
  greenhouse_recommended: z.boolean(),
  support_required: z.boolean(),
  default_nutrient_plan_key: z.string().nullable(),
});

type FormData = z.infer<typeof schema>;

export default function SpeciesDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { current, loading, error } = useAppSelector((s) => s.species);
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [createPlantOpen, setCreatePlantOpen] = useState(false);
  const [tab, setTab] = useTabUrl(['edit', 'growing-periods', 'cultivars', 'lifecycle', 'workflows']);
  const [families, setFamilies] = useState<BotanicalFamily[]>([]);
  const [nutrientPlans, setNutrientPlans] = useState<NutrientPlan[]>([]);
  const { toggleFavorite, isFavorite } = useSowingFavorites();

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      scientific_name: '',
      common_names: [],
      family_key: null,
      genus: '',
      growth_habit: 'herb',
      root_type: 'fibrous',
      hardiness_zones: [],
      native_habitat: '',
      allelopathy_score: 0,
      base_temp: 10,
      description: '',
      synonyms: [],
      taxonomic_authority: '',
      taxonomic_status: '',
      container_suitable: null,
      recommended_container_volume_l: '',
      min_container_depth_cm: null,
      mature_height_cm: '',
      mature_width_cm: '',
      spacing_cm: '',
      indoor_suitable: null,
      balcony_suitable: null,
      greenhouse_recommended: false,
      support_required: false,
      default_nutrient_plan_key: null,
    },
  });

  useEffect(() => {
    if (key) dispatch(fetchSpecies(key));
    familiesApi.listBotanicalFamilies().then(setFamilies).catch(() => {});
    planApi.fetchNutrientPlans(0, 200).then(setNutrientPlans).catch(() => {});
    return () => { dispatch(clearCurrent()); };
  }, [key, dispatch]);

  useEffect(() => {
    if (current) {
      reset({
        scientific_name: current.scientific_name,
        common_names: current.common_names,
        family_key: current.family_key,
        genus: current.genus,
        growth_habit: current.growth_habit,
        root_type: current.root_type,
        hardiness_zones: current.hardiness_zones,
        native_habitat: current.native_habitat,
        allelopathy_score: current.allelopathy_score,
        base_temp: current.base_temp,
        description: current.description ?? '',
        synonyms: current.synonyms ?? [],
        taxonomic_authority: current.taxonomic_authority ?? '',
        taxonomic_status: current.taxonomic_status ?? '',
        container_suitable: current.container_suitable ?? null,
        recommended_container_volume_l: current.recommended_container_volume_l ?? '',
        min_container_depth_cm: current.min_container_depth_cm ?? null,
        mature_height_cm: current.mature_height_cm ?? '',
        mature_width_cm: current.mature_width_cm ?? '',
        spacing_cm: current.spacing_cm ?? '',
        indoor_suitable: current.indoor_suitable ?? null,
        balcony_suitable: current.balcony_suitable ?? null,
        greenhouse_recommended: current.greenhouse_recommended ?? false,
        support_required: current.support_required ?? false,
        default_nutrient_plan_key: current.default_nutrient_plan_key ?? null,
      });
    }
  }, [current, reset]);

  const onSubmit = async (data: FormData) => {
    if (!key) return;
    try {
      setSaving(true);
      const payload = {
        ...data,
        container_suitable: data.container_suitable || null,
        indoor_suitable: data.indoor_suitable || null,
        balcony_suitable: data.balcony_suitable || null,
        default_nutrient_plan_key: data.default_nutrient_plan_key || null,
      };
      await api.updateSpecies(key, payload);
      notification.success(t('common.save'));
      dispatch(fetchSpecies(key));
    } catch (err) {
      handleError(err);
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async () => {
    if (!key) return;
    try {
      await api.deleteSpecies(key);
      notification.success(t('common.delete'));
      navigate('/stammdaten/species');
    } catch (err) {
      handleError(err);
    }
    setDeleteOpen(false);
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} onRetry={() => navigate(-1)} />;

  return (
    <>
      <UnsavedChangesGuard dirty={isDirty} />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <PageTitle title={current?.scientific_name ?? t('entities.species')} />
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {key && (
            <Tooltip title={t('pages.calendar.sowingCalendar.toggleFavorite')}>
              <IconButton
                onClick={() => toggleFavorite(key)}
                color={isFavorite(key) ? 'warning' : 'default'}
                data-testid="species-favorite-toggle"
              >
                {isFavorite(key) ? <StarIcon /> : <StarBorderIcon />}
              </IconButton>
            </Tooltip>
          )}
          <Button variant="outlined" startIcon={<AddIcon />} onClick={() => setCreatePlantOpen(true)}>
            {t('pages.species.createPlantInstance')}
          </Button>
          <Button color="error" startIcon={<DeleteIcon />} onClick={() => setDeleteOpen(true)}>
            {t('common.delete')}
          </Button>
        </Box>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab label={t('common.edit')} />
        <Tab label={t('pages.species.growingPeriodsTab')} />
        <Tab label={t('pages.cultivars.title')} />
        <Tab label={t('pages.lifecycle.title')} />
        <Tab label={t('pages.species.workflows')} />
      </Tabs>

      {tab === 0 && (
        <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 900 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.species.editIntro')}
          </Typography>

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.species.sectionTaxonomy')}
          </Typography>
          <FormTextField
            name="scientific_name"
            control={control}
            label={t('pages.species.scientificName')}
            helperText={t('pages.species.scientificNameHelper')}
            required
          />
          <FormChipInput
            name="common_names"
            control={control}
            label={t('pages.species.commonNames')}
            helperText={t('pages.species.commonNamesHelper')}
          />
          <FormRow>
            <Box>
              <FormSelectField
                name="family_key"
                control={control}
                label={t('pages.species.family')}
                helperText={t('pages.species.familyHelper')}
                options={[
                  { value: '', label: '\u2014' },
                  ...families.map((f) => ({ value: f.key, label: f.name })),
                ]}
              />
              {current?.family_key && (
                <Link
                  component={RouterLink}
                  to={`/stammdaten/botanical-families/${current.family_key}`}
                  variant="body2"
                  sx={{ display: 'inline-block', mt: -1, mb: 1 }}
                >
                  {t('pages.species.viewFamily')}
                </Link>
              )}
            </Box>
            <FormTextField
              name="genus"
              control={control}
              label={t('pages.species.genus')}
              helperText={t('pages.species.genusHelper')}
            />
          </FormRow>
          <FormTextField
            name="description"
            control={control}
            label={t('pages.species.description')}
            helperText={t('pages.species.descriptionHelper')}
            multiline
            rows={3}
          />

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.species.sectionGrowth')}
          </Typography>
          <FormRow>
            <FormSelectField
              name="growth_habit"
              control={control}
              label={t('pages.species.growthHabit')}
              helperText={t('pages.species.growthHabitHelper')}
              options={['herb', 'shrub', 'tree', 'vine', 'groundcover'].map((v) => ({
                value: v,
                label: t(`enums.growthHabit.${v}`),
              }))}
            />
            <FormSelectField
              name="root_type"
              control={control}
              label={t('pages.species.rootType')}
              helperText={t('pages.species.rootTypeHelper')}
              options={['fibrous', 'taproot', 'tuberous', 'bulbous'].map((v) => ({
                value: v,
                label: t(`enums.rootType.${v}`),
              }))}
            />
          </FormRow>

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.species.sectionEnvironment')}
          </Typography>
          <FormChipInput
            name="hardiness_zones"
            control={control}
            label={t('pages.species.hardinessZones')}
            helperText={t('pages.species.hardinessZonesHelper')}
          />
          <FormTextField
            name="native_habitat"
            control={control}
            label={t('pages.species.nativeHabitat')}
            helperText={t('pages.species.nativeHabitatHelper')}
          />
          <FormRow>
            <FormNumberField
              name="allelopathy_score"
              control={control}
              label={t('pages.species.allelopathyScore')}
              helperText={t('pages.species.allelopathyScoreHelper')}
              min={-1}
              max={1}
              step={0.1}
            />
            <FormNumberField
              name="base_temp"
              control={control}
              label={t('pages.species.baseTemp')}
              helperText={t('pages.species.baseTempHelper')}
            />
          </FormRow>

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.species.sectionClassification')}
          </Typography>
          <FormChipInput
            name="synonyms"
            control={control}
            label={t('pages.species.synonyms')}
            helperText={t('pages.species.synonymsHelper')}
          />
          <FormRow>
            <FormTextField
              name="taxonomic_authority"
              control={control}
              label={t('pages.species.taxonomicAuthority')}
              helperText={t('pages.species.taxonomicAuthorityHelper')}
            />
            <FormTextField
              name="taxonomic_status"
              control={control}
              label={t('pages.species.taxonomicStatus')}
              helperText={t('pages.species.taxonomicStatusHelper')}
            />
          </FormRow>

          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
            {t('pages.species.sectionCultivation')}
          </Typography>
          <FormRow>
            <FormSelectField
              name="container_suitable"
              control={control}
              label={t('pages.species.containerSuitable')}
              helperText={t('pages.species.containerSuitableHelper')}
              options={[
                { value: '', label: '\u2014' },
                ...['yes', 'limited', 'no'].map((v) => ({
                  value: v,
                  label: t(`enums.suitability.${v}`),
                })),
              ]}
            />
            <FormTextField
              name="recommended_container_volume_l"
              control={control}
              label={t('pages.species.recommendedContainerVolumeL')}
              helperText={t('pages.species.recommendedContainerVolumeLHelper')}
            />
          </FormRow>
          <FormRow>
            <FormNumberField
              name="min_container_depth_cm"
              control={control}
              label={t('pages.species.minContainerDepthCm')}
              helperText={t('pages.species.minContainerDepthCmHelper')}
              min={1}
              max={200}
            />
            <FormTextField
              name="mature_height_cm"
              control={control}
              label={t('pages.species.matureHeightCm')}
              helperText={t('pages.species.matureHeightCmHelper')}
            />
          </FormRow>
          <FormRow>
            <FormTextField
              name="mature_width_cm"
              control={control}
              label={t('pages.species.matureWidthCm')}
              helperText={t('pages.species.matureWidthCmHelper')}
            />
            <FormTextField
              name="spacing_cm"
              control={control}
              label={t('pages.species.spacingCm')}
              helperText={t('pages.species.spacingCmHelper')}
            />
          </FormRow>
          <FormRow>
            <FormSelectField
              name="indoor_suitable"
              control={control}
              label={t('pages.species.indoorSuitable')}
              helperText={t('pages.species.indoorSuitableHelper')}
              options={[
                { value: '', label: '\u2014' },
                ...['yes', 'limited', 'no'].map((v) => ({
                  value: v,
                  label: t(`enums.suitability.${v}`),
                })),
              ]}
            />
            <FormSelectField
              name="balcony_suitable"
              control={control}
              label={t('pages.species.balconySuitable')}
              helperText={t('pages.species.balconySuitableHelper')}
              options={[
                { value: '', label: '\u2014' },
                ...['yes', 'limited', 'no'].map((v) => ({
                  value: v,
                  label: t(`enums.suitability.${v}`),
                })),
              ]}
            />
          </FormRow>
          <FormRow>
            <FormSwitchField
              name="greenhouse_recommended"
              control={control}
              label={t('pages.species.greenhouseRecommended')}
              helperText={t('pages.species.greenhouseRecommendedHelper')}
            />
            <FormSwitchField
              name="support_required"
              control={control}
              label={t('pages.species.supportRequired')}
              helperText={t('pages.species.supportRequiredHelper')}
            />
          </FormRow>
          <FormRow>
            <FormSelectField
              name="default_nutrient_plan_key"
              control={control}
              label={t('pages.species.defaultNutrientPlan')}
              helperText={t('pages.species.defaultNutrientPlanHelper')}
              options={[
                { value: '', label: '—' },
                ...nutrientPlans.map((p) => ({
                  value: p.key,
                  label: `${p.name}${p.is_template ? ` (${t('pages.nutrientPlans.isTemplate')})` : ''}`,
                })),
              ]}
            />
          </FormRow>
          <FormActions onCancel={() => navigate(-1)} loading={saving} />

          {/* Watering Guide (read-only display from seed data) */}
          {current?.watering_guide ? (
            <Card variant="outlined" sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <OpacityIcon fontSize="small" />
                  {t('pages.species.sectionWateringGuide')}
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 1 }}>
                  <Typography variant="body2">
                    <strong>{t('pages.species.wateringInterval')}:</strong>{' '}
                    {t('pages.species.wateringIntervalDays', { count: current.watering_guide.interval_days })}
                  </Typography>
                  <Typography variant="body2">
                    <strong>{t('pages.species.wateringVolume')}:</strong>{' '}
                    {t('pages.species.wateringVolumeMl', { min: current.watering_guide.volume_ml_min, max: current.watering_guide.volume_ml_max })}
                  </Typography>
                  <Typography variant="body2">
                    <strong>{t('pages.species.wateringMethod')}:</strong>{' '}
                    {t(`enums.wateringMethod.${current.watering_guide.watering_method}`)}
                  </Typography>
                  {current.watering_guide.water_quality_hint && (
                    <Typography variant="body2">
                      <strong>{t('pages.species.waterQualityHint')}:</strong>{' '}
                      {current.watering_guide.water_quality_hint}
                    </Typography>
                  )}
                </Box>
                {current.watering_guide.practical_tip && (
                  <Alert severity="info" sx={{ mt: 1 }}>
                    {current.watering_guide.practical_tip}
                  </Alert>
                )}
                {current.watering_guide.seasonal_adjustments.length > 0 && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      <strong>{t('pages.species.seasonalAdjustments')}:</strong>
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {current.watering_guide.seasonal_adjustments.map((adj) => (
                        <Chip
                          key={adj.label}
                          size="small"
                          label={`${adj.label}: ${t('pages.species.wateringIntervalDays', { count: adj.interval_days })}, ${t('pages.species.wateringVolumeMl', { min: adj.volume_ml_min, max: adj.volume_ml_max })}`}
                        />
                      ))}
                    </Box>
                  </Box>
                )}
              </CardContent>
            </Card>
          ) : (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              {t('pages.species.noWateringGuide')}
            </Typography>
          )}
        </Box>
      )}

      {tab === 1 && key && current && (
        <GrowingPeriodsSection speciesKey={key} species={current} onSaved={() => dispatch(fetchSpecies(key))} />
      )}
      {tab === 2 && key && <CultivarListSection speciesKey={key} />}
      {tab === 3 && key && <LifecycleConfigSection speciesKey={key} />}
      {tab === 4 && key && <SpeciesWorkflowsSection speciesKey={key} />}

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: current?.scientific_name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
      />

      {key && (
        <PlantInstanceCreateDialog
          open={createPlantOpen}
          onClose={() => setCreatePlantOpen(false)}
          onCreated={(newKey) => {
            setCreatePlantOpen(false);
            navigate(`/pflanzen/plant-instances/${newKey}`);
          }}
          initialSpeciesKey={key}
        />
      )}
    </>
  );
}
