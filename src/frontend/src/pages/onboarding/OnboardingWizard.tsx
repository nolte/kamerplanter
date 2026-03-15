import { useEffect, useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Stepper from '@mui/material/Stepper';
import Step from '@mui/material/Step';
import StepLabel from '@mui/material/StepLabel';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Slider from '@mui/material/Slider';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Divider from '@mui/material/Divider';
import InputAdornment from '@mui/material/InputAdornment';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import EmojiNatureIcon from '@mui/icons-material/EmojiNature';
import SchoolIcon from '@mui/icons-material/School';
import ScienceIcon from '@mui/icons-material/Science';
import PageTitle from '@/components/layout/PageTitle';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import {
  fetchOnboardingState,
  fetchStarterKits,
  completeOnboarding,
  skipOnboarding,
} from '@/store/slices/onboardingSlice';
import { useNotification } from '@/hooks/useNotification';
import { useApiError } from '@/hooks/useApiError';
import type { ExperienceLevel, SiteType, StarterKit } from '@/api/types';

const EXPERIENCE_LEVELS: {
  level: ExperienceLevel;
  icon: React.ReactNode;
}[] = [
  { level: 'beginner', icon: <EmojiNatureIcon sx={{ fontSize: '2.5rem' }} /> },
  { level: 'intermediate', icon: <SchoolIcon sx={{ fontSize: '2.5rem' }} /> },
  { level: 'expert', icon: <ScienceIcon sx={{ fontSize: '2.5rem' }} /> },
];

const SITE_TYPES: SiteType[] = [
  'indoor',
  'outdoor',
  'greenhouse',
  'windowsill',
  'balcony',
  'grow_tent',
];

export default function OnboardingWizard() {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const notification = useNotification();
  const { handleError } = useApiError();
  const { state: onboardingState, kits, loading } = useAppSelector((s) => s.onboarding);

  const [activeStep, setActiveStep] = useState(0);
  const [experienceLevel, setExperienceLevel] = useState<ExperienceLevel>('beginner');
  const [selectedKitId, setSelectedKitId] = useState<string | null>(null);
  const [siteName, setSiteName] = useState('');
  const [siteType, setSiteType] = useState<SiteType>('indoor');
  const [plantCount, setPlantCount] = useState(5);
  const [submitting, setSubmitting] = useState(false);
  const [hasRoSystem, setHasRoSystem] = useState(false);
  const [tapWaterEc, setTapWaterEc] = useState<string>('');
  const [tapWaterPh, setTapWaterPh] = useState<string>('');

  useEffect(() => {
    dispatch(fetchOnboardingState());
    dispatch(fetchStarterKits());
  }, [dispatch]);

  useEffect(() => {
    if (onboardingState?.completed || onboardingState?.skipped) {
      navigate('/dashboard', { replace: true });
    }
  }, [onboardingState, navigate]);

  const steps = useMemo(
    () => [
      t('pages.onboarding.step1'),
      t('pages.onboarding.step2'),
      t('pages.onboarding.step3'),
      t('pages.onboarding.step4'),
      t('pages.onboarding.step5'),
    ],
    [t],
  );

  const selectedKit = useMemo(
    () => kits.find((k) => k.kit_id === selectedKitId) ?? null,
    [kits, selectedKitId],
  );

  const getKitName = useCallback(
    (kit: StarterKit) => {
      return kit.name_i18n[i18n.language] ?? kit.name_i18n.de ?? kit.kit_id;
    },
    [i18n.language],
  );

  const getKitDescription = useCallback(
    (kit: StarterKit) => {
      return kit.description_i18n[i18n.language] ?? kit.description_i18n.de ?? '';
    },
    [i18n.language],
  );

  const handleNext = useCallback(() => {
    setActiveStep((prev) => Math.min(prev + 1, steps.length - 1));
  }, [steps.length]);

  const handleBack = useCallback(() => {
    setActiveStep((prev) => Math.max(prev - 1, 0));
  }, []);

  const handleComplete = useCallback(async () => {
    try {
      setSubmitting(true);
      await dispatch(
        completeOnboarding({
          kit_id: selectedKitId ?? undefined,
          experience_level: experienceLevel,
          site_name: siteName || undefined,
          plant_count: plantCount,
          has_ro_system: hasRoSystem || undefined,
          tap_water_ec_ms: tapWaterEc ? parseFloat(tapWaterEc) : undefined,
          tap_water_ph: tapWaterPh ? parseFloat(tapWaterPh) : undefined,
        }),
      ).unwrap();
      notification.success(t('pages.onboarding.complete'));
      navigate('/dashboard', { replace: true });
    } catch (err) {
      handleError(err);
    } finally {
      setSubmitting(false);
    }
  }, [
    dispatch,
    selectedKitId,
    experienceLevel,
    siteName,
    plantCount,
    hasRoSystem,
    tapWaterEc,
    tapWaterPh,
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
      navigate('/dashboard', { replace: true });
    } catch (err) {
      handleError(err);
    } finally {
      setSubmitting(false);
    }
  }, [dispatch, notification, handleError, navigate, t]);

  const canProceed = useMemo(() => {
    switch (activeStep) {
      case 0:
        return true; // Experience level always has a default
      case 1:
        return true; // Kit selection is optional
      case 2:
        return true; // Site setup is optional
      case 3:
        return plantCount > 0;
      case 4:
        return true;
      default:
        return false;
    }
  }, [activeStep, plantCount]);

  if (loading && !onboardingState) return <LoadingSkeleton variant="card" />;

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box data-testid="onboarding-step-welcome">
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              {t('pages.onboarding.subtitle')}
            </Typography>
            <Typography variant="h6" gutterBottom>
              {t('pages.onboarding.experienceLevel')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {t('pages.onboarding.experienceLevelHint')}
            </Typography>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' },
                gap: 2,
              }}
            >
              {EXPERIENCE_LEVELS.map(({ level, icon }) => (
                <Card
                  key={level}
                  variant={experienceLevel === level ? 'elevation' : 'outlined'}
                  sx={{
                    border: experienceLevel === level ? 2 : 1,
                    borderColor:
                      experienceLevel === level ? 'primary.main' : 'divider',
                    transition: 'border-color 0.15s, box-shadow 0.15s',
                  }}
                >
                  <CardActionArea
                    onClick={() => setExperienceLevel(level)}
                    data-testid={`experience-${level}`}
                    sx={{ p: 2, textAlign: 'center' }}
                  >
                    <Box sx={{ color: 'primary.main', mb: 1 }}>{icon}</Box>
                    <Typography variant="subtitle1" fontWeight={experienceLevel === level ? 700 : 400}>
                      {t(`enums.experienceLevel.${level}`)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t(`pages.auth.experienceLevel.${level}Description`)}
                    </Typography>
                  </CardActionArea>
                </Card>
              ))}
            </Box>
          </Box>
        );

      case 1:
        return (
          <Box data-testid="onboarding-step-kit">
            <Typography variant="h6" gutterBottom>
              {t('pages.onboarding.selectKit')}
            </Typography>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' },
                gap: 2,
              }}
            >
              {kits.map((kit) => (
                <Card
                  key={kit.kit_id}
                  variant={selectedKitId === kit.kit_id ? 'elevation' : 'outlined'}
                  sx={{
                    border: selectedKitId === kit.kit_id ? 2 : 1,
                    borderColor:
                      selectedKitId === kit.kit_id ? 'primary.main' : 'divider',
                  }}
                >
                  <CardActionArea
                    onClick={() =>
                      setSelectedKitId(
                        selectedKitId === kit.kit_id ? null : kit.kit_id,
                      )
                    }
                    data-testid={`kit-${kit.kit_id}`}
                    sx={{ p: 2 }}
                  >
                    <Typography variant="subtitle1" gutterBottom>
                      {kit.icon} {getKitName(kit)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {getKitDescription(kit)}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      <Chip
                        label={t(`enums.experienceLevel.${kit.difficulty}`)}
                        size="small"
                        variant="outlined"
                      />
                      {kit.toxicity_warning && (
                        <Chip label="!" size="small" color="warning" />
                      )}
                    </Box>
                  </CardActionArea>
                </Card>
              ))}
            </Box>
          </Box>
        );

      case 2:
        return (
          <Box
            data-testid="onboarding-step-site"
            sx={{ maxWidth: 480, display: 'flex', flexDirection: 'column', gap: 2.5 }}
          >
            <TextField
              label={t('pages.onboarding.siteName')}
              value={siteName}
              onChange={(e) => setSiteName(e.target.value)}
              fullWidth
              helperText={t('pages.onboarding.siteNameHelper')}
              autoFocus
              data-testid="site-name-field"
            />
            <FormControl fullWidth>
              <InputLabel id="site-type-label">
                {t('pages.onboarding.siteType')}
              </InputLabel>
              <Select
                labelId="site-type-label"
                value={siteType}
                label={t('pages.onboarding.siteType')}
                onChange={(e) => setSiteType(e.target.value as SiteType)}
                data-testid="site-type-select"
              >
                {SITE_TYPES.map((type) => (
                  <MenuItem key={type} value={type}>
                    {t(`enums.siteType.${type}`)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {experienceLevel !== 'beginner' && (
              <>
                <Divider sx={{ my: 0.5 }} />
                <Typography variant="subtitle2">
                  {t('pages.onboarding.waterSection')}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t('pages.onboarding.waterSectionHelper')}
                </Typography>
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
                  <TextField
                    label={t('pages.onboarding.tapWaterEc')}
                    type="number"
                    value={tapWaterEc}
                    onChange={(e) => setTapWaterEc(e.target.value)}
                    inputProps={{ step: 0.01, min: 0, max: 2.0, inputMode: 'decimal' }}
                    helperText={t('pages.onboarding.tapWaterEcHelper')}
                    InputProps={{
                      endAdornment: <InputAdornment position="end">mS/cm</InputAdornment>,
                    }}
                    data-testid="onboarding-tap-ec"
                  />
                  <TextField
                    label={t('pages.onboarding.tapWaterPh')}
                    type="number"
                    value={tapWaterPh}
                    onChange={(e) => setTapWaterPh(e.target.value)}
                    inputProps={{ step: 0.1, min: 3.0, max: 10.0, inputMode: 'decimal' }}
                    helperText={t('pages.onboarding.tapWaterPhHelper')}
                    data-testid="onboarding-tap-ph"
                  />
                </Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={hasRoSystem}
                      onChange={(e) => setHasRoSystem(e.target.checked)}
                      data-testid="onboarding-ro-toggle"
                    />
                  }
                  label={t('pages.onboarding.hasRoSystemToggle')}
                />
              </>
            )}
          </Box>
        );

      case 3:
        return (
          <Box
            data-testid="onboarding-step-plants"
            sx={{ maxWidth: 480 }}
          >
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              {selectedKit
                ? t('pages.onboarding.plantCountSuggestion', {
                    kit: getKitName(selectedKit),
                    count: selectedKit.plant_count_suggestion,
                  })
                : t('pages.onboarding.plantCountHelper')}
            </Typography>
            <Typography variant="subtitle2" gutterBottom>
              {t('pages.onboarding.plantCount')}: <strong>{plantCount}</strong>
            </Typography>
            <Box sx={{ px: 1, pt: 2, pb: 1 }}>
              <Slider
                value={plantCount}
                onChange={(_, val) => setPlantCount(val as number)}
                min={1}
                max={50}
                step={1}
                valueLabelDisplay="on"
                marks={[
                  { value: 1, label: '1' },
                  { value: 10, label: '10' },
                  { value: 25, label: '25' },
                  { value: 50, label: '50' },
                ]}
                data-testid="plant-count-slider"
                aria-label={t('pages.onboarding.plantCount')}
              />
            </Box>
          </Box>
        );

      case 4:
        return (
          <Box data-testid="onboarding-step-complete">
            <Box sx={{ textAlign: 'center', mb: 3 }}>
              <CheckCircleIcon
                sx={{ fontSize: '4rem', color: 'success.main', mb: 1 }}
              />
              <Typography variant="h5" gutterBottom>
                {t('pages.onboarding.reviewTitle')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t('pages.onboarding.reviewSubtitle')}
              </Typography>
            </Box>
            <Card variant="outlined" sx={{ maxWidth: 440, mx: 'auto' }}>
              <CardContent>
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: 'auto 1fr',
                    rowGap: 1.5,
                    columnGap: 2,
                    alignItems: 'baseline',
                  }}
                >
                  <Typography variant="body2" color="text.secondary">
                    {t('pages.onboarding.experienceLevel')}
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>
                    {t(`enums.experienceLevel.${experienceLevel}`)}
                  </Typography>

                  {selectedKit && (
                    <>
                      <Typography variant="body2" color="text.secondary">
                        {t('pages.onboarding.selectKit')}
                      </Typography>
                      <Typography variant="body2" fontWeight={600}>{getKitName(selectedKit)}</Typography>
                    </>
                  )}

                  {siteName && (
                    <>
                      <Typography variant="body2" color="text.secondary">
                        {t('pages.onboarding.siteName')}
                      </Typography>
                      <Typography variant="body2" fontWeight={600}>{siteName}</Typography>
                    </>
                  )}

                  <Typography variant="body2" color="text.secondary">
                    {t('pages.onboarding.plantCount')}
                  </Typography>
                  <Typography variant="body2" fontWeight={600}>{plantCount}</Typography>
                </Box>
              </CardContent>
            </Card>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Box data-testid="onboarding-wizard" sx={{ maxWidth: 960, mx: 'auto', p: 2 }}>
      <PageTitle title={t('pages.onboarding.title')} />

      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Box sx={{ minHeight: 300, mb: 4 }}>{renderStepContent()}</Box>

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

          {activeStep < steps.length - 1 ? (
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
    </Box>
  );
}
