import { useEffect, useState, useMemo, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Stepper from '@mui/material/Stepper';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import MobileStepper from '@mui/material/MobileStepper';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  fetchOnboardingState,
  fetchStarterKits,
  fetchAllSpecies,
  fetchExistingFavorites,
  fetchExistingSites,
  completeOnboarding,
  skipOnboarding,
  resetOnboarding,
  saveProgress,
  fetchMatchingNutrientPlans,
  setFavoriteSpecies,
  toggleFavoriteSpecies,
  toggleFavoriteNutrientPlan,
} from '@/store/slices/onboardingSlice';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import type { ExperienceLevel, PlantConfig, SiteType } from '@/api/types';

import ExperienceLevelStep from './steps/ExperienceLevelStep';
import StarterKitStep from './steps/StarterKitStep';
import FavoriteSpeciesStep from './steps/FavoriteSpeciesStep';
import SiteSetupStep from './steps/SiteSetupStep';
import PlantSelectionStep from './steps/PlantSelectionStep';
import NutrientPlanStep from './steps/NutrientPlanStep';
import SummaryStep from './steps/SummaryStep';

type WizardStepId = 'experience' | 'kit' | 'favorites' | 'site' | 'plants' | 'nutrientPlans' | 'summary';

export default function OnboardingWizard() {
  const { t } = useTranslation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const {
    state: onboardingState,
    kits,
    loading,
    favoriteSpeciesKeys,
    favoriteNutrientPlanKeys,
    matchingNutrientPlans,
    matchingPlansLoading,
    allSpecies,
    allSpeciesLoading,
    existingFavoriteKeys,
    existingSites,
    existingSitesLoading,
  } = useAppSelector((s) => s.onboarding);
  const activeTenant = useAppSelector((s) => s.tenants.activeTenant);

  const [activeStep, setActiveStep] = useState(0);
  const [experienceLevel, setExperienceLevel] = useState<ExperienceLevel>('beginner');
  const [selectedKitId, setSelectedKitId] = useState<string | null>(null);
  const [siteName, setSiteName] = useState('');
  const [siteType, setSiteType] = useState<SiteType>('indoor');
  const [plantConfigs, setPlantConfigs] = useState<PlantConfig[]>([]);
  const [selectedSiteKey, setSelectedSiteKey] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [smartHomeEnabled, setSmartHomeEnabled] = useState(false);
  const [hasRoSystem, setHasRoSystem] = useState(false);
  const [tapWaterEc, setTapWaterEc] = useState<string>('');
  const [tapWaterPh, setTapWaterPh] = useState<string>('');

  // Track whether the user has manually changed the site name
  const siteNameManuallyChanged = useRef(false);

  useEffect(() => {
    dispatch(fetchOnboardingState());
    dispatch(fetchStarterKits(activeTenant ? { useTenant: true } : undefined));
  }, [dispatch, activeTenant]);

  // Resume progress from saved state on mount
  useEffect(() => {
    if (
      onboardingState &&
      !onboardingState.completed &&
      !onboardingState.skipped &&
      onboardingState.wizard_step > 0
    ) {
      setActiveStep(onboardingState.wizard_step);
      if (onboardingState.selected_experience_level) {
        setExperienceLevel(onboardingState.selected_experience_level);
      }
      if (onboardingState.selected_kit_id) {
        setSelectedKitId(onboardingState.selected_kit_id);
      }
      if (onboardingState.site_name) {
        setSiteName(onboardingState.site_name);
        siteNameManuallyChanged.current = true;
      }
      if (onboardingState.site_type) {
        setSiteType(onboardingState.site_type as SiteType);
      }
      if (onboardingState.selected_site_key) {
        setSelectedSiteKey(onboardingState.selected_site_key);
      }
      if (onboardingState.plant_configs?.length) {
        setPlantConfigs(onboardingState.plant_configs);
      }
    }
    // Only run on initial load
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onboardingState?.key]);

  // Dynamic steps based on experience level and favorites
  const wizardSteps = useMemo<{ id: WizardStepId; label: string }[]>(() => {
    const baseSteps: { id: WizardStepId; label: string }[] = [
      { id: 'experience', label: t('pages.onboarding.step1') },
      { id: 'kit', label: t('pages.onboarding.step2') },
      { id: 'favorites', label: t('pages.onboarding.stepFavorites') },
      { id: 'site', label: t('pages.onboarding.step3') },
    ];

    if (experienceLevel !== 'beginner') {
      baseSteps.push({ id: 'plants', label: t('pages.onboarding.step4') });

      // Only show nutrient plans step if user has favorites and plans exist
      if (favoriteSpeciesKeys.length > 0) {
        baseSteps.push({ id: 'nutrientPlans', label: t('pages.onboarding.step4b') });
      }
    }

    baseSteps.push({ id: 'summary', label: t('pages.onboarding.step5') });

    return baseSteps;
  }, [experienceLevel, favoriteSpeciesKeys.length, t]);

  const selectedKit = useMemo(
    () => kits.find((k) => k.kit_id === selectedKitId) ?? null,
    [kits, selectedKitId],
  );

  // Auto-populate defaults from kit selection
  const handleKitSelect = useCallback(
    (kitId: string | null) => {
      setSelectedKitId(kitId);

      if (kitId) {
        const kit = kits.find((k) => k.kit_id === kitId);
        if (kit) {
          // Auto-populate site type from kit
          setSiteType(kit.site_type);

          // Auto-populate site name if user hasn't manually changed it
          if (!siteNameManuallyChanged.current) {
            // Use i18n key so the default is localised
            const defaultName = t(`pages.onboarding.siteNameDefault.${kit.site_type}`, {
              defaultValue: '',
            });
            setSiteName(defaultName);
          }

          // Auto-populate plant configs from kit suggestion
          if (kit.species_keys.length > 0) {
            const perSpecies = Math.max(1, Math.round(kit.plant_count_suggestion / kit.species_keys.length));
            setPlantConfigs(
              kit.species_keys.map((sk) => ({
                species_key: sk,
                count: perSpecies,
                initial_phase: 'germination' as const,
              })),
            );
          }

          // Pre-select kit species as favorites
          if (kit.species_keys.length > 0) {
            dispatch(setFavoriteSpecies(kit.species_keys));
          }
        }
      }
    },
    [kits, t, dispatch],
  );

  const handleSiteNameChange = useCallback((name: string) => {
    setSiteName(name);
    siteNameManuallyChanged.current = true;
  }, []);

  const handleToggleFavoriteSpecies = useCallback(
    (key: string) => {
      dispatch(toggleFavoriteSpecies(key));
    },
    [dispatch],
  );

  const handleToggleFavoritePlan = useCallback(
    (key: string) => {
      dispatch(toggleFavoriteNutrientPlan(key));
    },
    [dispatch],
  );

  const handleNext = useCallback(() => {
    const nextStep = Math.min(activeStep + 1, wizardSteps.length - 1);
    setActiveStep(nextStep);

    const currentStepId = wizardSteps[activeStep]?.id;
    const nextStepId = wizardSteps[nextStep]?.id;

    // When entering favorites step, fetch all species and existing favorites
    if (nextStepId === 'favorites' && allSpecies.length === 0) {
      dispatch(fetchAllSpecies());
      dispatch(fetchExistingFavorites());
    }

    // When entering site step, fetch existing sites
    if (nextStepId === 'site' && existingSites.length === 0) {
      dispatch(fetchExistingSites());
    }

    // When advancing past plant selection, fetch matching nutrient plans
    if (currentStepId === 'plants' && favoriteSpeciesKeys.length > 0) {
      dispatch(fetchMatchingNutrientPlans({ speciesKeys: favoriteSpeciesKeys }));
    }

    dispatch(
      saveProgress({
        wizard_step: nextStep,
        selected_kit_id: selectedKitId ?? undefined,
        selected_experience_level: experienceLevel,
        site_name: siteName || undefined,
        site_type: siteType,
        selected_site_key: selectedSiteKey ?? undefined,
        plant_configs: plantConfigs.length > 0 ? plantConfigs : undefined,
        favorite_species_keys: favoriteSpeciesKeys.length > 0 ? favoriteSpeciesKeys : undefined,
        favorite_nutrient_plan_keys:
          favoriteNutrientPlanKeys.length > 0 ? favoriteNutrientPlanKeys : undefined,
      }),
    );
  }, [
    activeStep,
    wizardSteps,
    dispatch,
    selectedKitId,
    experienceLevel,
    siteName,
    siteType,
    selectedSiteKey,
    plantConfigs,
    favoriteSpeciesKeys,
    favoriteNutrientPlanKeys,
    allSpecies.length,
    existingSites.length,
  ]);

  const handleBack = useCallback(() => {
    setActiveStep((prev) => Math.max(prev - 1, 0));
  }, []);

  const handleComplete = useCallback(async () => {
    const totalPlants = plantConfigs.reduce((sum, c) => sum + c.count, 0);
    const finalPlantCount =
      experienceLevel === 'beginner' && selectedKit
        ? selectedKit.plant_count_suggestion
        : Math.max(totalPlants, 1);

    try {
      setSubmitting(true);
      await dispatch(
        completeOnboarding({
          kit_id: selectedKitId ?? undefined,
          experience_level: experienceLevel,
          site_name: selectedSiteKey ? undefined : (siteName || undefined),
          selected_site_key: selectedSiteKey ?? undefined,
          plant_count: finalPlantCount,
          plant_configs: plantConfigs.filter((c) => c.count > 0),
          has_ro_system: hasRoSystem || undefined,
          tap_water_ec_ms: tapWaterEc ? parseFloat(tapWaterEc) : undefined,
          tap_water_ph: tapWaterPh ? parseFloat(tapWaterPh) : undefined,
          favorite_species_keys:
            favoriteSpeciesKeys.length > 0 ? favoriteSpeciesKeys : undefined,
          favorite_nutrient_plan_keys:
            favoriteNutrientPlanKeys.length > 0 ? favoriteNutrientPlanKeys : undefined,
          smart_home_enabled: smartHomeEnabled || undefined,
        }),
      ).unwrap();
      notification.success(t('pages.onboarding.complete'));
      navigate('/pflanzen/plant-instances', { replace: true });
    } catch (err) {
      handleError(err);
    } finally {
      setSubmitting(false);
    }
  }, [
    dispatch,
    selectedKitId,
    selectedKit,
    selectedSiteKey,
    experienceLevel,
    siteName,
    plantConfigs,
    smartHomeEnabled,
    hasRoSystem,
    tapWaterEc,
    tapWaterPh,
    favoriteSpeciesKeys,
    favoriteNutrientPlanKeys,
    notification,
    handleError,
    navigate,
    t,
  ]);

  const handleSkip = useCallback(async () => {
    try {
      setSubmitting(true);
      await dispatch(skipOnboarding()).unwrap();
      notification.info(t('pages.onboarding.skip'));
      navigate('/pflanzen/plant-instances', { replace: true });
    } catch (err) {
      handleError(err);
    } finally {
      setSubmitting(false);
    }
  }, [dispatch, notification, handleError, navigate, t]);

  const handleRestart = useCallback(async () => {
    try {
      await dispatch(resetOnboarding()).unwrap();
      setActiveStep(0);
      setExperienceLevel('beginner');
      setSelectedKitId(null);
      setSiteName('');
      setSiteType('indoor');
      setSelectedSiteKey(null);
      setPlantConfigs([]);
      setSmartHomeEnabled(false);
      setHasRoSystem(false);
      setTapWaterEc('');
      setTapWaterPh('');
      siteNameManuallyChanged.current = false;
    } catch (err) {
      handleError(err);
    }
  }, [dispatch, handleError]);

  const canProceed = useMemo(() => {
    if (activeStep >= wizardSteps.length) return false;
    const currentStepId = wizardSteps[activeStep]?.id;
    switch (currentStepId) {
      case 'experience':
        return true;
      case 'kit':
        return true;
      case 'favorites':
        return true;
      case 'site':
        return true;
      case 'plants':
        return true;
      case 'nutrientPlans':
        return true;
      case 'summary':
        return true;
      default:
        return false;
    }
  }, [activeStep, wizardSteps]);

  if (loading && !onboardingState) return <LoadingSkeleton variant="card" />;

  // Show completed card instead of auto-redirect
  if (onboardingState?.completed || onboardingState?.skipped) {
    return (
      <Box data-testid="onboarding-wizard" sx={{ maxWidth: 960, mx: 'auto', p: 2 }}>
        <PageTitle title={t('pages.onboarding.title')} />
        <Card sx={{ maxWidth: 500, mx: 'auto', mt: 4 }}>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <CheckCircleIcon sx={{ fontSize: '4rem', color: 'success.main', mb: 2 }} aria-hidden="true" />
            <Typography variant="h5" gutterBottom>
              {t('pages.onboarding.alreadyCompleted')}
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 3 }}>
              <Button
                variant="outlined"
                onClick={handleRestart}
                data-testid="onboarding-restart"
              >
                {t('pages.onboarding.rerunButton')}
              </Button>
              <Button
                variant="contained"
                onClick={() => navigate('/dashboard')}
                data-testid="onboarding-go-dashboard"
              >
                {t('pages.onboarding.goToDashboard')}
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  }

  const renderStepContent = () => {
    if (activeStep >= wizardSteps.length) return null;
    const currentStepId = wizardSteps[activeStep].id;

    switch (currentStepId) {
      case 'experience':
        return (
          <ExperienceLevelStep
            experienceLevel={experienceLevel}
            onSelect={setExperienceLevel}
            smartHomeEnabled={smartHomeEnabled}
            onSmartHomeEnabledChange={setSmartHomeEnabled}
          />
        );
      case 'kit':
        return (
          <StarterKitStep
            kits={kits}
            selectedKitId={selectedKitId}
            onSelect={handleKitSelect}
          />
        );
      case 'favorites':
        return (
          <FavoriteSpeciesStep
            allSpecies={allSpecies}
            allSpeciesLoading={allSpeciesLoading}
            favoriteSpeciesKeys={favoriteSpeciesKeys}
            onToggleFavoriteSpecies={handleToggleFavoriteSpecies}
            kitSpeciesKeys={selectedKit?.species_keys ?? []}
            existingFavoriteKeys={existingFavoriteKeys}
          />
        );
      case 'site':
        return (
          <SiteSetupStep
            siteName={siteName}
            onSiteNameChange={handleSiteNameChange}
            siteType={siteType}
            onSiteTypeChange={setSiteType}
            experienceLevel={experienceLevel}
            tapWaterEc={tapWaterEc}
            onTapWaterEcChange={setTapWaterEc}
            tapWaterPh={tapWaterPh}
            onTapWaterPhChange={setTapWaterPh}
            hasRoSystem={hasRoSystem}
            onHasRoSystemChange={setHasRoSystem}
            existingSites={existingSites}
            existingSitesLoading={existingSitesLoading}
            selectedSiteKey={selectedSiteKey}
            onSelectedSiteKeyChange={setSelectedSiteKey}
          />
        );
      case 'plants':
        return (
          <PlantSelectionStep
            allSpecies={allSpecies}
            favoriteSpeciesKeys={favoriteSpeciesKeys}
            plantConfigs={plantConfigs}
            onPlantConfigsChange={setPlantConfigs}
          />
        );
      case 'nutrientPlans':
        return (
          <NutrientPlanStep
            plans={matchingNutrientPlans}
            loading={matchingPlansLoading}
            favoriteNutrientPlanKeys={favoriteNutrientPlanKeys}
            onToggleFavoritePlan={handleToggleFavoritePlan}
            experienceLevel={experienceLevel}
          />
        );
      case 'summary':
        return (
          <SummaryStep
            experienceLevel={experienceLevel}
            selectedKit={selectedKit}
            siteName={siteName}
            siteType={siteType}
            selectedSite={existingSites.find((s) => s.key === selectedSiteKey) ?? null}
            allSpecies={allSpecies}
            plantConfigs={plantConfigs}
            plantCount={
              experienceLevel === 'beginner' && selectedKit
                ? selectedKit.plant_count_suggestion
                : plantConfigs.reduce((sum, c) => sum + c.count, 0)
            }
            favoriteSpeciesCount={favoriteSpeciesKeys.length}
            favoriteNutrientPlanCount={favoriteNutrientPlanKeys.length}
          />
        );
      default:
        return null;
    }
  };

  const isLastStep = activeStep === wizardSteps.length - 1;

  return (
    <Box data-testid="onboarding-wizard" sx={{ maxWidth: 960, mx: 'auto', p: { xs: 1.5, sm: 2 } }}>
      <PageTitle title={t('pages.onboarding.title')} />

      {/* Desktop stepper — hidden on mobile to save vertical space */}
      {!isMobile && (
        <Stepper
          activeStep={activeStep}
          alternativeLabel
          sx={{ mb: 4 }}
          aria-label={t('pages.onboarding.stepperAriaLabel')}
        >
          {wizardSteps.map((step) => (
            <Step key={step.id}>
              <StepLabel>{step.label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      )}

      {/* Mobile step indicator */}
      {isMobile && (
        <Box sx={{ mb: 2, textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            {t('pages.onboarding.stepIndicator', {
              current: activeStep + 1,
              total: wizardSteps.length,
              label: wizardSteps[activeStep]?.label ?? '',
            })}
          </Typography>
        </Box>
      )}

      {/* Step content — aria-live region announces step changes to screen readers */}
      <Box
        sx={{ mb: 4 }}
        role="region"
        aria-live="polite"
        aria-atomic="false"
        aria-label={wizardSteps[activeStep]?.label}
      >
        {renderStepContent()}
      </Box>

      {/* Navigation — MobileStepper on small screens, custom on desktop */}
      {isMobile ? (
        <MobileStepper
          variant="dots"
          steps={wizardSteps.length}
          position="static"
          activeStep={activeStep}
          sx={{ bgcolor: 'transparent', px: 0 }}
          nextButton={
            isLastStep ? (
              <Button
                variant="contained"
                size="small"
                onClick={handleComplete}
                disabled={submitting}
                startIcon={submitting ? <CircularProgress size={14} /> : <CheckCircleIcon />}
                data-testid="onboarding-complete"
              >
                {t('pages.onboarding.completeButton')}
              </Button>
            ) : (
              <Button
                size="small"
                onClick={handleNext}
                disabled={!canProceed || submitting}
                endIcon={<KeyboardArrowRightIcon />}
                data-testid="onboarding-next"
              >
                {t('common.next')}
              </Button>
            )
          }
          backButton={
            <Button
              size="small"
              onClick={handleBack}
              disabled={activeStep === 0 || submitting}
              startIcon={<KeyboardArrowLeftIcon />}
              data-testid="onboarding-back"
            >
              {t('common.back')}
            </Button>
          }
        />
      ) : (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Button
            variant="text"
            onClick={handleSkip}
            disabled={submitting}
            data-testid="skip-onboarding"
          >
            {t('pages.onboarding.skip')}
          </Button>

          <Box sx={{ display: 'flex', gap: 1 }}>
            {activeStep > 0 && (
              <Button
                variant="outlined"
                onClick={handleBack}
                disabled={submitting}
                data-testid="onboarding-back"
              >
                {t('common.back')}
              </Button>
            )}

            {!isLastStep ? (
              <Button
                variant="contained"
                onClick={handleNext}
                disabled={!canProceed || submitting}
                data-testid="onboarding-next"
              >
                {t('common.next')}
              </Button>
            ) : (
              <Button
                variant="contained"
                onClick={handleComplete}
                disabled={submitting}
                startIcon={
                  submitting ? <CircularProgress size={16} /> : <CheckCircleIcon />
                }
                data-testid="onboarding-complete"
              >
                {t('pages.onboarding.completeButton')}
              </Button>
            )}
          </Box>
        </Box>
      )}

      {/* Skip link for mobile — shown below the mobile stepper */}
      {isMobile && (
        <Box sx={{ textAlign: 'center', mt: 1 }}>
          <Button
            variant="text"
            size="small"
            onClick={handleSkip}
            disabled={submitting}
            data-testid="skip-onboarding"
          >
            {t('pages.onboarding.skip')}
          </Button>
        </Box>
      )}
    </Box>
  );
}
