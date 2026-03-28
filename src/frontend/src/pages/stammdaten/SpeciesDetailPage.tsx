import { useEffect, useState } from 'react';
import { useTabUrl } from '@/hooks/useTabUrl';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Chip from '@mui/material/Chip';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import AddIcon from '@mui/icons-material/Add';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import CancelIcon from '@mui/icons-material/Cancel';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import OpacityIcon from '@mui/icons-material/Opacity';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import EmptyState from '@/components/common/EmptyState';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import ExpertiseFieldWrapper from '@/components/common/ExpertiseFieldWrapper';
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
import * as companionApi from '@/api/endpoints/companionPlanting';
import * as rotationApi from '@/api/endpoints/cropRotation';
import * as planApi from '@/api/endpoints/nutrient-plans';
import type {
  BotanicalFamily,
  CompatibleSpecies,
  IncompatibleSpecies,
  NutrientPlan,
  RotationSuccessor,
  Species,
} from '@/api/types';
import { kamiMasterdata } from '@/assets/brand/illustrations';

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

/** Spacing between form panels (UI-NFR-008 R-039: 24px = spacing.lg) */
const PANEL_GAP = 4;

export default function SpeciesDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { current, loading, error } = useAppSelector((s) => s.species);
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const [saving, setSaving] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [createPlantOpen, setCreatePlantOpen] = useState(false);
  const [tab, setTab] = useTabUrl(['edit', 'growing-periods', 'cultivars', 'lifecycle', 'workflows', 'companion-planting', 'crop-rotation']);
  const [families, setFamilies] = useState<BotanicalFamily[]>([]);
  const [nutrientPlans, setNutrientPlans] = useState<NutrientPlan[]>([]);

  // Companion planting state (tab 5)
  const [companionSpeciesList, setCompanionSpeciesList] = useState<Species[]>([]);
  const [compatible, setCompatible] = useState<CompatibleSpecies[]>([]);
  const [incompatible, setIncompatible] = useState<IncompatibleSpecies[]>([]);
  const [companionLoading, setCompanionLoading] = useState(false);
  const [companionDialogType, setCompanionDialogType] = useState<'compatible' | 'incompatible' | null>(null);
  const [companionTargetKey, setCompanionTargetKey] = useState('');
  const [companionScore, setCompanionScore] = useState(1);
  const [companionReason, setCompanionReason] = useState('');

  // Crop rotation state (tab 6)
  const [currentFamily, setCurrentFamily] = useState<BotanicalFamily | null>(null);
  const [rotationSuccessors, setRotationSuccessors] = useState<RotationSuccessor[]>([]);
  const [rotationLoading, setRotationLoading] = useState(false);
  const [rotationDialogOpen, setRotationDialogOpen] = useState(false);
  const [rotationFamilies, setRotationFamilies] = useState<BotanicalFamily[]>([]);
  const [rotationFamiliesLoaded, setRotationFamiliesLoaded] = useState(false);
  const [rotationTargetKey, setRotationTargetKey] = useState('');
  const [rotationWaitYears, setRotationWaitYears] = useState(3);
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
    familiesApi.listBotanicalFamilies(0, 200).then(setFamilies).catch(() => {});
    planApi.fetchNutrientPlans(0, 200).then(setNutrientPlans).catch(() => {});
    return () => { dispatch(clearCurrent()); };
  }, [key, dispatch]);

  // Load companion planting data when tab 5 is selected
  useEffect(() => {
    if (tab === 5 && key) {
      setCompanionLoading(true);
      api.listSpecies(0, 200).then((r) => setCompanionSpeciesList(r.items)).catch(() => {});
      Promise.all([
        companionApi.getCompatibleSpecies(key),
        companionApi.getIncompatibleSpecies(key),
      ])
        .then(([comp, incomp]) => {
          setCompatible(comp);
          setIncompatible(incomp);
        })
        .catch((err) => handleError(err))
        .finally(() => setCompanionLoading(false));
    }
  }, [tab, key]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load crop rotation data when tab 6 is selected
  useEffect(() => {
    if (tab === 6 && current?.family_key) {
      setRotationLoading(true);
      familiesApi.getBotanicalFamily(current.family_key).then(setCurrentFamily).catch(() => {});
      rotationApi
        .getSuccessors(current.family_key)
        .then(setRotationSuccessors)
        .catch((err) => handleError(err))
        .finally(() => setRotationLoading(false));
    }
  }, [tab, current?.family_key]); // eslint-disable-line react-hooks/exhaustive-deps

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

  const reloadCompanionRelations = async () => {
    if (!key) return;
    try {
      const [comp, incomp] = await Promise.all([
        companionApi.getCompatibleSpecies(key),
        companionApi.getIncompatibleSpecies(key),
      ]);
      setCompatible(comp);
      setIncompatible(incomp);
    } catch (err) {
      handleError(err);
    }
  };

  const handleAddCompanion = async () => {
    if (!key || !companionTargetKey) return;
    try {
      if (companionDialogType === 'compatible') {
        await companionApi.setCompatible({ from_species_key: key, to_species_key: companionTargetKey, score: companionScore });
      } else {
        await companionApi.setIncompatible({ from_species_key: key, to_species_key: companionTargetKey, reason: companionReason });
      }
      notification.success(t('common.create'));
      reloadCompanionRelations();
    } catch (err) {
      handleError(err);
    }
    setCompanionDialogType(null);
    setCompanionTargetKey('');
  };

  const handleAddRotationSuccessor = async () => {
    if (!current?.family_key || !rotationTargetKey) return;
    try {
      await rotationApi.setSuccessor({
        from_family_key: current.family_key,
        to_family_key: rotationTargetKey,
        wait_years: rotationWaitYears,
      });
      notification.success(t('common.create'));
      const updated = await rotationApi.getSuccessors(current.family_key);
      setRotationSuccessors(updated);
    } catch (err) {
      handleError(err);
    }
    setRotationDialogOpen(false);
    setRotationTargetKey('');
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

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }} variant="scrollable" scrollButtons="auto">
        <Tab label={t('common.edit')} />
        <Tab label={t('pages.species.growingPeriodsTab')} />
        <Tab label={t('pages.cultivars.title')} />
        <Tab label={t('pages.lifecycle.title')} />
        <Tab label={t('pages.species.workflows')} />
        <Tab label={t('pages.companionPlanting.title')} />
        <Tab label={t('pages.cropRotation.title')} />
      </Tabs>

      {tab === 0 && (
        <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 900, display: 'flex', flexDirection: 'column', gap: PANEL_GAP }}>
          <Typography variant="body2" color="text.secondary">
            {t('pages.species.editIntro')}
          </Typography>

          {/* ── Panel 1: Taxonomie (intermediate — Pflichtfelder) ── */}
          {/* UI-NFR-008 R-037/R-038/R-040: Card panel, h6 heading, required fields first */}
          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 0.5 }}>
                {t('pages.species.sectionTaxonomy')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {t('pages.species.editIntro')}
              </Typography>
              <FormTextField
                name="scientific_name"
                control={control}
                label={t('pages.species.scientificName')}
                helperText={t('pages.species.scientificNameHelper')}
                required
                autoFocus
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
            </CardContent>
          </Card>

          {/* ── Panel 2: Wachstum (intermediate) ── */}
          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 2 }}>
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
                <ExpertiseFieldWrapper minLevel="expert">
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
                </ExpertiseFieldWrapper>
              </FormRow>
            </CardContent>
          </Card>

          {/* ── Panel 3: Anbaubedingungen (intermediate — key cultivation info) ── */}
          <Card variant="outlined">
            <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
              <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 2 }}>
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
              </FormRow>
              <FormRow>
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
                <FormSelectField
                  name="default_nutrient_plan_key"
                  control={control}
                  label={t('pages.species.defaultNutrientPlan')}
                  helperText={t('pages.species.defaultNutrientPlanHelper')}
                  options={[
                    { value: '', label: '\u2014' },
                    ...nutrientPlans.map((p) => ({
                      value: p.key,
                      label: `${p.name}${p.is_template ? ` (${t('pages.nutrientPlans.isTemplate')})` : ''}`,
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

              {/* Expert: Sizing & spacing details */}
              <ExpertiseFieldWrapper minLevel="expert">
                <FormRow>
                  <FormTextField
                    name="recommended_container_volume_l"
                    control={control}
                    label={t('pages.species.recommendedContainerVolumeL')}
                    helperText={t('pages.species.recommendedContainerVolumeLHelper')}
                  />
                  <FormNumberField
                    name="min_container_depth_cm"
                    control={control}
                    label={t('pages.species.minContainerDepthCm')}
                    helperText={t('pages.species.minContainerDepthCmHelper')}
                    min={1}
                    max={200}
                  />
                </FormRow>
                <FormRow>
                  <FormTextField
                    name="mature_height_cm"
                    control={control}
                    label={t('pages.species.matureHeightCm')}
                    helperText={t('pages.species.matureHeightCmHelper')}
                  />
                  <FormTextField
                    name="mature_width_cm"
                    control={control}
                    label={t('pages.species.matureWidthCm')}
                    helperText={t('pages.species.matureWidthCmHelper')}
                  />
                </FormRow>
                <FormRow>
                  <FormTextField
                    name="spacing_cm"
                    control={control}
                    label={t('pages.species.spacingCm')}
                    helperText={t('pages.species.spacingCmHelper')}
                  />
                </FormRow>
              </ExpertiseFieldWrapper>
            </CardContent>
          </Card>

          {/* ── Panel 4: Umgebung (expert) ── */}
          {/* UI-NFR-008 R-041: Expert-only panel hidden as a whole */}
          <ExpertiseFieldWrapper minLevel="expert">
            <Card variant="outlined">
              <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
                <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 2 }}>
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
              </CardContent>
            </Card>
          </ExpertiseFieldWrapper>

          {/* ── Panel 5: Klassifikation (expert) ── */}
          {/* UI-NFR-008 R-041: Expert-only panel hidden as a whole */}
          <ExpertiseFieldWrapper minLevel="expert">
            <Card variant="outlined">
              <CardContent component="fieldset" sx={{ border: 'none', p: 0, m: 0, '&:last-child': { pb: 2 }, px: 2, pt: 2 }}>
                <Typography component="legend" variant="h6" sx={{ pt: 1.5, mb: 2 }}>
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
              </CardContent>
            </Card>
          </ExpertiseFieldWrapper>

          {/* ── Watering Guide (read-only, before actions) ── */}
          {current?.watering_guide ? (
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" sx={{ pt: 1.5, mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
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
            <Typography variant="body2" color="text.secondary">
              {t('pages.species.noWateringGuide')}
            </Typography>
          )}

          {/* UI-NFR-008 R-025: Required field legend */}
          <Typography variant="caption" color="text.secondary">
            * {t('common.required')}
          </Typography>

          <FormActions onCancel={() => navigate(-1)} loading={saving} />
        </Box>
      )}

      {tab === 1 && key && current && (
        <GrowingPeriodsSection speciesKey={key} species={current} onSaved={() => dispatch(fetchSpecies(key))} />
      )}
      {tab === 2 && key && <CultivarListSection speciesKey={key} />}
      {tab === 3 && key && <LifecycleConfigSection speciesKey={key} />}
      {tab === 4 && key && <SpeciesWorkflowsSection speciesKey={key} />}

      {/* ── Tab 5: Companion Planting (Mischkultur) ── */}
      {tab === 5 && key && current && (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            {t('pages.species.companionPlantingIntro', { name: current.scientific_name })}
          </Typography>

          {companionLoading && <LoadingSkeleton variant="card" />}

          {!companionLoading && (
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
              {/* Compatible species */}
              <Card sx={{ flex: 1, minWidth: 300 }} variant="outlined">
                <CardHeader
                  title={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <CheckCircleIcon fontSize="small" color="success" />
                      <Typography variant="subtitle1">
                        {t('pages.companionPlanting.compatible')}
                      </Typography>
                      {compatible.length > 0 && (
                        <Chip label={compatible.length} size="small" color="success" variant="outlined" />
                      )}
                    </Box>
                  }
                  action={
                    <Button
                      size="small"
                      startIcon={<AddIcon />}
                      onClick={() => setCompanionDialogType('compatible')}
                      data-testid="add-compatible-button"
                    >
                      {t('pages.companionPlanting.addCompatible')}
                    </Button>
                  }
                  sx={{ pb: 0 }}
                />
                <CardContent>
                  {compatible.length === 0 ? (
                    <EmptyState
                      illustration={kamiMasterdata}
                      message={t('pages.companionPlanting.noCompatible')}
                    />
                  ) : (
                    <List dense disablePadding>
                      {compatible.map((c) => (
                        <ListItem key={c.species_key} divider>
                          <ListItemText
                            primary={
                              <Link component={RouterLink} to={`/stammdaten/species/${c.species_key}`} variant="body2" underline="hover">
                                {c.scientific_name ?? c.species_key}
                              </Link>
                            }
                          />
                          <Chip
                            label={`${t('pages.companionPlanting.score')}: ${c.score}`}
                            size="small"
                            color="success"
                            variant="outlined"
                          />
                        </ListItem>
                      ))}
                    </List>
                  )}
                </CardContent>
              </Card>

              {/* Incompatible species */}
              <Card sx={{ flex: 1, minWidth: 300 }} variant="outlined">
                <CardHeader
                  title={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <CancelIcon fontSize="small" color="error" />
                      <Typography variant="subtitle1">
                        {t('pages.companionPlanting.incompatible')}
                      </Typography>
                      {incompatible.length > 0 && (
                        <Chip label={incompatible.length} size="small" color="error" variant="outlined" />
                      )}
                    </Box>
                  }
                  action={
                    <Button
                      size="small"
                      startIcon={<AddIcon />}
                      onClick={() => setCompanionDialogType('incompatible')}
                      data-testid="add-incompatible-button"
                    >
                      {t('pages.companionPlanting.addIncompatible')}
                    </Button>
                  }
                  sx={{ pb: 0 }}
                />
                <CardContent>
                  {incompatible.length === 0 ? (
                    <EmptyState
                      illustration={kamiMasterdata}
                      message={t('pages.companionPlanting.noIncompatible')}
                    />
                  ) : (
                    <List dense disablePadding>
                      {incompatible.map((c) => (
                        <ListItem key={c.species_key} divider>
                          <ListItemText
                            primary={
                              <Link component={RouterLink} to={`/stammdaten/species/${c.species_key}`} variant="body2" underline="hover">
                                {c.scientific_name ?? c.species_key}
                              </Link>
                            }
                            secondary={c.reason || undefined}
                            secondaryTypographyProps={{ variant: 'caption' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  )}
                </CardContent>
              </Card>
            </Box>
          )}

          {/* Companion planting dialog */}
          <Dialog fullScreen={fullScreen} open={!!companionDialogType} onClose={() => setCompanionDialogType(null)} maxWidth="sm" fullWidth>
            <DialogTitle>
              {companionDialogType === 'compatible'
                ? t('pages.companionPlanting.addCompatible')
                : t('pages.companionPlanting.addIncompatible')}
            </DialogTitle>
            <DialogContent>
              <DialogContentText sx={{ mb: 2 }}>
                {companionDialogType === 'compatible'
                  ? t('pages.companionPlanting.addCompatibleHint')
                  : t('pages.companionPlanting.addIncompatibleHint')}
              </DialogContentText>
              <TextField
                select
                fullWidth
                label={t('pages.companionPlanting.selectSpecies')}
                value={companionTargetKey}
                onChange={(e) => setCompanionTargetKey(e.target.value)}
                helperText={t('pages.companionPlanting.targetSpeciesHelper')}
                sx={{ mt: 1, mb: 2 }}
                data-testid="target-species-select"
              >
                {companionSpeciesList.filter((s) => s.key !== key).map((s) => (
                  <MenuItem key={s.key} value={s.key}>{s.scientific_name}</MenuItem>
                ))}
              </TextField>
              {companionDialogType === 'compatible' && (
                <TextField
                  type="number"
                  label={t('pages.companionPlanting.score')}
                  value={companionScore}
                  onChange={(e) => setCompanionScore(Number(e.target.value))}
                  fullWidth
                  helperText={t('pages.companionPlanting.scoreHelper')}
                  inputProps={{ min: 0, max: 1, step: 0.1 }}
                  data-testid="score-input"
                />
              )}
              {companionDialogType === 'incompatible' && (
                <TextField
                  label={t('pages.companionPlanting.reason')}
                  value={companionReason}
                  onChange={(e) => setCompanionReason(e.target.value)}
                  fullWidth
                  helperText={t('pages.companionPlanting.reasonHelper')}
                  multiline
                  rows={2}
                  data-testid="reason-input"
                />
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setCompanionDialogType(null)}>{t('common.cancel')}</Button>
              <Button variant="contained" onClick={handleAddCompanion} disabled={!companionTargetKey}>
                {t('common.create')}
              </Button>
            </DialogActions>
          </Dialog>
        </>
      )}

      {/* ── Tab 6: Crop Rotation (Fruchtfolge) ── */}
      {tab === 6 && key && current && (
        <Box sx={{ maxWidth: 800 }}>
          {!current.family_key ? (
            <Alert severity="info" data-testid="no-family-alert">
              {t('pages.species.noFamilyForCropRotation')}
            </Alert>
          ) : (
            <>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                {t('pages.species.cropRotationIntro')}
              </Typography>

              {/* Current family card — clickable */}
              <Card
                variant="outlined"
                component={RouterLink}
                to={`/stammdaten/botanical-families/${current.family_key}`}
                sx={{
                  mb: 3,
                  display: 'block',
                  textDecoration: 'none',
                  transition: 'border-color 0.15s, box-shadow 0.15s',
                  '&:hover': { borderColor: 'primary.main', boxShadow: 1 },
                }}
                data-testid="family-card-link"
              >
                <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 1.5, '&:last-child': { pb: 1.5 } }}>
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: 0.6 }}>
                      {t('pages.species.family')}
                    </Typography>
                    <Typography variant="h6" color="text.primary" sx={{ mt: 0.25, lineHeight: 1.3 }}>
                      {currentFamily?.name ?? '…'}
                    </Typography>
                    {currentFamily?.common_name_de && (
                      <Typography variant="body2" color="text.secondary">
                        {currentFamily.common_name_de}
                      </Typography>
                    )}
                    {currentFamily?.rotation_category && (
                      <Chip label={currentFamily.rotation_category} size="small" variant="outlined" sx={{ mt: 0.75 }} />
                    )}
                  </Box>
                  <ArrowForwardIcon color="action" />
                </CardContent>
              </Card>

              {rotationLoading && <LoadingSkeleton variant="card" />}

              {!rotationLoading && (
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        {t('pages.cropRotation.successorsTitle')}
                      </Typography>
                      {rotationSuccessors.length > 0 && (
                        <Chip label={rotationSuccessors.length} size="small" variant="outlined" />
                      )}
                    </Box>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<AddIcon />}
                      onClick={() => {
                        if (!rotationFamiliesLoaded) {
                          familiesApi.listBotanicalFamilies(0, 500).then((f) => {
                            setRotationFamilies(f);
                            setRotationFamiliesLoaded(true);
                          }).catch(() => {});
                        }
                        setRotationDialogOpen(true);
                      }}
                      data-testid="add-successor-button"
                    >
                      {t('pages.cropRotation.addSuccessor')}
                    </Button>
                  </Box>

                  {rotationSuccessors.length === 0 ? (
                    <EmptyState
                      illustration={kamiMasterdata}
                      message={t('pages.cropRotation.noSuccessors')}
                      actionLabel={t('pages.cropRotation.addSuccessor')}
                      onAction={() => {
                        if (!rotationFamiliesLoaded) {
                          familiesApi.listBotanicalFamilies(0, 500).then((f) => {
                            setRotationFamilies(f);
                            setRotationFamiliesLoaded(true);
                          }).catch(() => {});
                        }
                        setRotationDialogOpen(true);
                      }}
                    />
                  ) : (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                      {rotationSuccessors.map((s) => (
                        <Card
                          key={s.family_key}
                          variant="outlined"
                          component={RouterLink}
                          to={`/stammdaten/botanical-families/${s.family_key}`}
                          sx={{
                            display: 'block',
                            textDecoration: 'none',
                            transition: 'border-color 0.15s, box-shadow 0.15s',
                            '&:hover': { borderColor: 'primary.main', boxShadow: 1 },
                          }}
                        >
                          <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 1.25, '&:last-child': { pb: 1.25 } }}>
                            <Box sx={{ flex: 1, minWidth: 0 }}>
                              <Typography variant="body1" color="text.primary" fontWeight={500}>
                                {s.name ?? s.family_key}
                              </Typography>
                              {s.benefit_reason && (
                                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.25 }}>
                                  {s.benefit_reason}
                                </Typography>
                              )}
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 2, flexShrink: 0 }}>
                              <Chip
                                label={`${s.wait_years} ${t('pages.cropRotation.waitYears')}`}
                                size="small"
                                color={s.wait_years <= 1 ? 'success' : s.wait_years <= 3 ? 'warning' : 'error'}
                                variant="outlined"
                              />
                              <ArrowForwardIcon fontSize="small" color="action" />
                            </Box>
                          </CardContent>
                        </Card>
                      ))}
                    </Box>
                  )}
                </Box>
              )}

              {/* Crop rotation dialog */}
              <Dialog fullScreen={fullScreen} open={rotationDialogOpen} onClose={() => setRotationDialogOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>{t('pages.cropRotation.addSuccessor')}</DialogTitle>
                <DialogContent>
                  <DialogContentText sx={{ mb: 2 }}>
                    {t('pages.cropRotation.addSuccessorHint')}
                  </DialogContentText>
                  <TextField
                    select
                    fullWidth
                    label={t('pages.cropRotation.toFamily')}
                    value={rotationTargetKey}
                    onChange={(e) => setRotationTargetKey(e.target.value)}
                    helperText={t('pages.cropRotation.toFamilyHelper')}
                    sx={{ mt: 1, mb: 2 }}
                    data-testid="to-family-select"
                  >
                    {rotationFamilies.filter((f) => f.key !== current.family_key).map((f) => (
                      <MenuItem key={f.key} value={f.key}>{f.name}</MenuItem>
                    ))}
                  </TextField>
                  <TextField
                    type="number"
                    label={t('pages.cropRotation.waitYears')}
                    value={rotationWaitYears}
                    onChange={(e) => setRotationWaitYears(Number(e.target.value))}
                    fullWidth
                    helperText={t('pages.cropRotation.waitYearsHelper')}
                    inputProps={{ min: 1, max: 10 }}
                    data-testid="wait-years-input"
                  />
                </DialogContent>
                <DialogActions>
                  <Button onClick={() => setRotationDialogOpen(false)}>{t('common.cancel')}</Button>
                  <Button variant="contained" onClick={handleAddRotationSuccessor} disabled={!rotationTargetKey}>
                    {t('common.create')}
                  </Button>
                </DialogActions>
              </Dialog>
            </>
          )}
        </Box>
      )}

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
