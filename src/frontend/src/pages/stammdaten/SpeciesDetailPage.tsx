import { useEffect, useMemo, useState } from 'react';
import { useTabUrl } from '@/hooks/useTabUrl';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Alert from '@mui/material/Alert';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import StarIcon from '@mui/icons-material/Star';
import StarBorderIcon from '@mui/icons-material/StarBorder';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import OriginChip from '@/components/common/OriginChip';
import UnsavedChangesGuard from '@/components/form/UnsavedChangesGuard';
import { TabPanel, tabA11yProps } from '@/components/common/TabPanel';
import { useOriginProtection, resolveOrigin } from '@/hooks/useOriginProtection';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import CultivarListSection from './CultivarListSection';
import GrowingPeriodsSection from './GrowingPeriodsSection';
import SpeciesOverview from './SpeciesOverviewSection';
import LifecycleConfigSection from '@/pages/pflanzen/LifecycleConfigSection';
import SpeciesWorkflowsSection from './SpeciesWorkflowsSection';
import SpeciesEditTab from './species-detail/SpeciesEditTab';
import SpeciesCompanionTab from './species-detail/SpeciesCompanionTab';
import SpeciesCropRotationTab from './species-detail/SpeciesCropRotationTab';
import {
  speciesEditSchema,
  speciesFormDefaults,
  speciesToFormValues,
  type SpeciesFormData,
} from './species-detail/speciesDetailSchema';
import PlantInstanceCreateDialog from '@/pages/pflanzen/PlantInstanceCreateDialog';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import { useSowingFavorites } from '@/hooks/useSowingFavorites';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchSpecies, clearCurrent } from '@/store/slices/speciesSlice';
import * as api from '@/api/endpoints/species';
import * as familiesApi from '@/api/endpoints/botanicalFamilies';
import * as phaseSequenceApi from '@/api/endpoints/phaseSequences';
import * as planApi from '@/api/endpoints/nutrient-plans';
import type { BotanicalFamily, NutrientPlan } from '@/api/types';

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
  const [deleting, setDeleting] = useState(false);
  const [createPlantOpen, setCreatePlantOpen] = useState(false);
  const { isFieldVisible } = useExpertiseLevel();
  // U-4: Companion-planting & crop-rotation are expert-only capabilities
  // (consistent with the nav policy in fieldConfigs.ts). They are dropped from
  // both the tab strip and the slug list for non-experts, so the tab indices
  // stay contiguous and useTabUrl never resolves to a hidden tab.
  const showExpertTabs = isFieldVisible('expert');
  // U-1/U-2: read-optimised "overview" is the default landing (index 0); the
  // edit form moves to the end. Slug order drives the tab order below.
  const tabSlugs = useMemo(
    () =>
      [
        'overview',
        'growing-periods',
        'cultivars',
        'lifecycle',
        'workflows',
        ...(showExpertTabs ? (['companion-planting', 'crop-rotation'] as const) : []),
        'edit',
      ] as const,
    [showExpertTabs],
  );
  const tabSlugList = tabSlugs as readonly string[];
  const [tab, setTab] = useTabUrl(tabSlugList);
  // Resolve panels by slug rather than a hard-coded number, so the expert-tab
  // toggle never shifts a panel onto the wrong index. Returns -1 for a slug not
  // present in the current (expertise-dependent) tab set.
  const slugIndex = (slug: string) => tabSlugList.indexOf(slug);
  const overviewIdx = slugIndex('overview');
  const growingPeriodsIdx = slugIndex('growing-periods');
  const cultivarsIdx = slugIndex('cultivars');
  const lifecycleIdx = slugIndex('lifecycle');
  const workflowsIdx = slugIndex('workflows');
  const companionIdx = slugIndex('companion-planting');
  const cropRotationIdx = slugIndex('crop-rotation');
  const editIdx = slugIndex('edit');
  const [families, setFamilies] = useState<BotanicalFamily[]>([]);
  const [nutrientPlans, setNutrientPlans] = useState<NutrientPlan[]>([]);
  const [phaseSequenceKey, setPhaseSequenceKey] = useState<string | null>(null);
  const { toggleFavorite, isFavorite } = useSowingFavorites();
  const speciesOrigin = resolveOrigin(current);
  const { isReadOnly, isDeletionProtected, tooltipText: originTooltipText } = useOriginProtection({
    origin: speciesOrigin,
  });

  const {
    control,
    handleSubmit,
    reset,
    formState: { isDirty },
  } = useForm<SpeciesFormData>({
    resolver: zodResolver(speciesEditSchema),
    defaultValues: speciesFormDefaults,
  });

  useEffect(() => {
    if (key) {
      dispatch(fetchSpecies(key));
      phaseSequenceApi
        .getSpeciesPhaseSequence(key)
        .then((seq) => setPhaseSequenceKey(seq?.key ?? null))
        .catch(() => setPhaseSequenceKey(null));
    }
    familiesApi
      .listBotanicalFamilies(0, 200)
      .then(setFamilies)
      .catch(() => {});
    planApi
      .fetchNutrientPlans(0, 200)
      .then(setNutrientPlans)
      .catch(() => {});
    return () => {
      dispatch(clearCurrent());
    };
  }, [key, dispatch]);

  useEffect(() => {
    if (current) {
      reset(speciesToFormValues(current));
    }
  }, [current, reset]);

  const onSubmit = async (data: SpeciesFormData) => {
    if (!key) return;
    try {
      setSaving(true);
      const payload = {
        ...data,
        container_suitable: data.container_suitable || null,
        indoor_suitable: data.indoor_suitable || null,
        balcony_suitable: data.balcony_suitable || null,
        harvest_pattern: data.harvest_pattern || null,
        harvested_part: data.harvested_part || null,
        climacteric: data.climacteric || null,
        default_nutrient_plan_key: data.default_nutrient_plan_key || null,
        propagation_configs: data.propagation_configs.map((c) => ({
          method: c.method,
          months: [...new Set(c.months)].sort((a, b) => a - b),
          wood_stage: c.wood_stage || null,
          difficulty: c.difficulty || null,
          notes: c.notes?.trim() || null,
        })),
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
    setDeleting(true);
    try {
      await api.deleteSpecies(key);
      notification.success(t('common.delete'));
      navigate('/stammdaten/species');
    } catch (err) {
      handleError(err);
    } finally {
      setDeleting(false);
      setDeleteOpen(false);
    }
  };

  if (loading) return <LoadingSkeleton variant="form" />;
  if (error) return <ErrorDisplay error={error} onRetry={() => navigate(-1)} />;

  return (
    <>
      <UnsavedChangesGuard dirty={isDirty} />
      <PageTitle
        title={current?.scientific_name ?? t('entities.species')}
        meta={<OriginChip origin={speciesOrigin} />}
        action={
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
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={() => setCreatePlantOpen(true)}
            >
              {t('pages.species.createPlantInstance')}
            </Button>
            {/* UI-NFR-018 R-012: hide delete button for system data */}
            {!isDeletionProtected && (
              <Button color="error" startIcon={<DeleteIcon />} onClick={() => setDeleteOpen(true)}>
                {t('common.delete')}
              </Button>
            )}
          </Box>
        }
      />

      {/* UI-NFR-018 R-014: persistent, origin-specific explanation — visible on every
          tab (not just when the Edit tab is opened) so the "why can't I edit this"
          question is answered immediately, without relying on hovering the chip. */}
      {isReadOnly && (
        <Alert severity="info" sx={{ mb: 2 }} data-testid="species-readonly-banner">
          {originTooltipText}
        </Alert>
      )}

      <Tabs
        value={tab}
        onChange={(_, v) => setTab(v)}
        sx={{ mb: 3 }}
        variant="scrollable"
        scrollButtons="auto"
        aria-label={t('pages.species.tabsAriaLabel')}
      >
        <Tab label={t('pages.species.overviewTab')} {...tabA11yProps('species', overviewIdx)} />
        <Tab
          label={t('pages.species.growingPeriodsTab')}
          {...tabA11yProps('species', growingPeriodsIdx)}
        />
        <Tab label={t('pages.cultivars.title')} {...tabA11yProps('species', cultivarsIdx)} />
        <Tab label={t('pages.lifecycle.title')} {...tabA11yProps('species', lifecycleIdx)} />
        <Tab label={t('pages.species.workflows')} {...tabA11yProps('species', workflowsIdx)} />
        {showExpertTabs && [
          <Tab
            key="companion"
            label={t('pages.companionPlanting.title')}
            {...tabA11yProps('species', companionIdx)}
          />,
          <Tab
            key="crop-rotation"
            label={t('pages.cropRotation.title')}
            {...tabA11yProps('species', cropRotationIdx)}
          />,
        ]}
        <Tab label={t('common.edit')} {...tabA11yProps('species', editIdx)} />
      </Tabs>

      {/* ── Übersicht (read-optimised, default landing) ── */}
      <TabPanel index={overviewIdx} value={tab} idPrefix="species">
        {current && (
          <SpeciesOverview
            species={current}
            phaseSequenceKey={phaseSequenceKey}
            onEdit={() => setTab(editIdx)}
          />
        )}
      </TabPanel>

      <TabPanel index={editIdx} value={tab} idPrefix="species">
        <SpeciesEditTab
          control={control}
          onSubmit={handleSubmit(onSubmit)}
          families={families}
          nutrientPlans={nutrientPlans}
          isReadOnly={isReadOnly}
          saving={saving}
          phaseSequenceKey={phaseSequenceKey}
          currentFamilyKey={current?.family_key}
          onCancel={() => navigate(-1)}
        />
      </TabPanel>

      <TabPanel index={growingPeriodsIdx} value={tab} idPrefix="species">
        {key && current && (
          <GrowingPeriodsSection
            speciesKey={key}
            species={current}
            onSaved={() => dispatch(fetchSpecies(key))}
          />
        )}
      </TabPanel>
      <TabPanel index={cultivarsIdx} value={tab} idPrefix="species">
        {key && <CultivarListSection speciesKey={key} />}
      </TabPanel>
      <TabPanel index={lifecycleIdx} value={tab} idPrefix="species">
        {key && <LifecycleConfigSection speciesKey={key} />}
      </TabPanel>
      <TabPanel index={workflowsIdx} value={tab} idPrefix="species">
        {key && <SpeciesWorkflowsSection speciesKey={key} />}
      </TabPanel>

      {/* ── Companion Planting (Mischkultur) — expert-only (U-4) ── */}
      {showExpertTabs && (
        <TabPanel index={companionIdx} value={tab} idPrefix="species">
          {key && current && (
            <SpeciesCompanionTab
              speciesKey={key}
              speciesName={current.scientific_name}
              fullScreen={fullScreen}
            />
          )}
        </TabPanel>
      )}

      {/* ── Crop Rotation (Fruchtfolge) — expert-only (U-4) ── */}
      {showExpertTabs && (
        <TabPanel index={cropRotationIdx} value={tab} idPrefix="species">
          {key && current && (
            <SpeciesCropRotationTab familyKey={current.family_key} fullScreen={fullScreen} />
          )}
        </TabPanel>
      )}

      <ConfirmDialog
        open={deleteOpen}
        title={t('common.delete')}
        message={t('common.deleteConfirm', { name: current?.scientific_name })}
        onConfirm={onDelete}
        onCancel={() => setDeleteOpen(false)}
        destructive
        loading={deleting}
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
