import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import Link from '@mui/material/Link';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import FavoriteIcon from '@mui/icons-material/Favorite';
import ScheduleIcon from '@mui/icons-material/Schedule';
import HelpTooltip from '@/components/common/HelpTooltip';
import PestImageGallery from '@/components/pests/PestImageGallery';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import PageTitle from '@/components/layout/PageTitle';
import { useLocalizedField } from '@/hooks/useLocalizedField';
import { getPestDetail } from '@/api/endpoints/ipm';
import type { PestDetail, TreatmentType } from '@/api/types';

type ChipColor = 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';

const difficultyColor: Record<string, ChipColor> = {
  easy: 'success',
  medium: 'warning',
  hard: 'error',
};

const severityColor: Record<string, ChipColor> = {
  low: 'success',
  medium: 'warning',
  high: 'error',
};

// IPM hierarchy: cultural first, chemical last (REQ-010).
const TREATMENT_ORDER: TreatmentType[] = ['cultural', 'biological', 'mechanical', 'chemical'];

/**
 * REQ-010 — Pest detail page.
 *
 * Aggregates master data (profile), curated reference images and
 * countermeasures per IPM hierarchy plus matching beneficial organisms.
 * Data comes from the aggregated endpoint `GET /ipm/pests/{key}/detail`.
 *
 * UI patterns:
 * - UI-NFR-017 Pattern C: two-row header (title + meta chips)
 * - UI-NFR-011: HelpTooltip for IPM and Karenzzeit terms
 * - Responsive: 2-column grid on md+ for profile + beneficials panels
 */
export default function PestDetailPage() {
  const { t, i18n } = useTranslation();
  const l = useLocalizedField();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { key = '' } = useParams<{ key: string }>();

  const [detail, setDetail] = useState<PestDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Collapsible image panel: `null` follows the responsive default (collapsed on
  // mobile, expanded on desktop); once the user toggles, their choice sticks.
  const [imagesExpanded, setImagesExpanded] = useState<boolean | null>(null);
  const imagesOpen = imagesExpanded ?? !isMobile;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setDetail(await getPestDetail(key));
    } catch {
      setError(t('pages.pestDetail.loadError'));
    } finally {
      setLoading(false);
    }
  }, [key, t]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  const goBack = useCallback(() => navigate('/pflanzenschutz/pests'), [navigate]);

  // Group countermeasures by IPM tier (order per TREATMENT_ORDER).
  const treatmentGroups = useMemo(() => {
    const treatments = detail?.treatments ?? [];
    return TREATMENT_ORDER.map((type) => ({
      type,
      items: treatments.filter((tr) => tr.treatment_type === type),
    })).filter((group) => group.items.length > 0);
  }, [detail]);

  if (loading) {
    return (
      <Box data-testid="pest-detail-page">
        <LoadingSkeleton variant="card" />
      </Box>
    );
  }

  if (error || !detail) {
    return (
      <Box data-testid="pest-detail-page">
        {/* Pattern B: title + back action (error state has no meta chips) */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            mb: 2,
            flexWrap: 'wrap',
            gap: 1,
          }}
        >
          <PageTitle title={t('nav.detail')} sx={{ mb: 0 }} />
          <Button startIcon={<ArrowBackIcon />} onClick={goBack} data-testid="pest-detail-back">
            {t('pages.pestDetail.back')}
          </Button>
        </Box>
        <Alert severity="error" data-testid="pest-detail-error">
          {error ?? t('pages.pestDetail.notFound')}
        </Alert>
      </Box>
    );
  }

  const { pest, beneficials } = detail;
  // Localized free-text fields (base = EN fallback, *_de = German variant).
  const symptoms = l(pest, 'damage_symptoms') || detail.detection_symptom_hint;
  const preventionTips = l(pest, 'prevention_tips');
  const monitoringHints = l(pest, 'monitoring_hints');
  const hostPlants =
    i18n.language === 'de' && pest.host_plants_de.length > 0 ? pest.host_plants_de : pest.host_plants;
  const hasTempRange = pest.optimal_temp_min != null && pest.optimal_temp_max != null;
  const hasHumidityRange = pest.optimal_humidity_min != null && pest.optimal_humidity_max != null;

  return (
    <Box data-testid="pest-detail-page">
      {/*
       * UI-NFR-017 Pattern C: two-row header.
       * Row 1: PageTitle (sx={{ mb: 0 }}) + back button (right)
       * Row 2: meta chips (pest type, detection difficulty, severity)
       */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          mb: 2,
          flexWrap: 'wrap',
          gap: 1,
        }}
      >
        {/* Left: title + meta row */}
        <Box>
          {/* Row 1: page title */}
          <PageTitle title={l(pest, 'common_name')} sx={{ mb: 0 }} />
          {/* Row 2: scientific name + classification chips */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 1,
              mt: 0.5,
            }}
          >
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ fontStyle: 'italic' }}
              component="span"
            >
              {pest.scientific_name}
            </Typography>
            <Chip label={t(`enums.pestType.${pest.pest_type}`)} size="small" variant="outlined" />
            <Chip
              label={`${t('pages.ipm.detectionDifficulty')}: ${t(`enums.detectionDifficulty.${pest.detection_difficulty}`)}`}
              size="small"
              color={difficultyColor[pest.detection_difficulty] ?? 'default'}
            />
            {pest.severity && (
              <Chip
                label={`${t('pages.pestDetail.severity')}: ${t(`enums.pestSeverity.${pest.severity}`)}`}
                size="small"
                color={severityColor[pest.severity] ?? 'default'}
                data-testid="pest-detail-severity"
              />
            )}
          </Box>
        </Box>
        {/* Right: back navigation */}
        <Button startIcon={<ArrowBackIcon />} onClick={goBack} data-testid="pest-detail-back">
          {t('pages.pestDetail.back')}
        </Button>
      </Box>

      {/* Page intro text — visible for all users */}
      {pest.description && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {pest.description}
        </Typography>
      )}
      {!pest.description && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t('pages.pestDetail.pageIntro')}
        </Typography>
      )}

      {/* User-contributed reference image gallery (upload or camera) —
          collapsible because it can get long on mobile (default: collapsed on
          mobile, expanded on desktop). */}
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Box
            component="button"
            type="button"
            onClick={() => setImagesExpanded(!imagesOpen)}
            aria-expanded={imagesOpen}
            aria-controls="pest-detail-images-panel"
            aria-label={t('pages.pestDetail.sectionImagesToggle')}
            data-testid="pest-detail-images-toggle"
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              width: '100%',
              gap: 1,
              p: 0,
              border: 0,
              background: 'none',
              cursor: 'pointer',
              color: 'inherit',
              font: 'inherit',
              textAlign: 'left',
              '&:focus-visible': {
                outline: '2px solid',
                outlineColor: 'primary.main',
                outlineOffset: 2,
                borderRadius: 1,
              },
            }}
          >
            <Typography variant="h6" component="span">
              {t('pages.pestDetail.sectionImages')}
            </Typography>
            <IconButton
              component="span"
              size="small"
              aria-hidden="true"
              sx={{ pointerEvents: 'none' }}
            >
              {imagesOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>
          <Collapse in={imagesOpen} timeout="auto" unmountOnExit>
            <Box id="pest-detail-images-panel" sx={{ pt: 1 }}>
              <PestImageGallery
                pestKey={pest.key}
                pestName={l(pest, 'common_name')}
                detectionSlug={pest.detection_slug ?? null}
              />
            </Box>
          </Collapse>
        </CardContent>
      </Card>

      {/*
       * Two-column layout on md+ for profile + beneficials panels.
       * Both panels are standalone on xs/sm.
       */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: beneficials.length > 0 ? '3fr 2fr' : '1fr' },
          gap: 2,
          mb: 2,
          alignItems: 'start',
        }}
      >
        {/* Pest profile (Steckbrief) */}
        <Card variant="outlined">
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('pages.pestDetail.sectionProfile')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
              {t('pages.pestDetail.sectionProfileIntro')}
            </Typography>
            <Box
              component="dl"
              sx={{ m: 0, '& > *:not(:last-child)': { borderBottom: 1, borderColor: 'divider', pb: 1.5, mb: 1.5 } }}
            >
              {symptoms && (
                <DetailRow label={t('pages.pestDetail.damageSymptoms')} value={symptoms} />
              )}
              {pest.affected_plant_parts.length > 0 && (
                <DetailRow
                  label={t('pages.pestDetail.affectedParts')}
                  value={
                    <Stack
                      direction="row"
                      spacing={0.5}
                      sx={{ flexWrap: 'wrap', gap: 0.5 }}
                      role="list"
                      aria-label={t('pages.pestDetail.affectedParts')}
                    >
                      {pest.affected_plant_parts.map((part) => (
                        <Chip
                          key={part}
                          size="small"
                          label={t(`enums.plantPart.${part}`)}
                          role="listitem"
                        />
                      ))}
                    </Stack>
                  }
                />
              )}
              {hostPlants.length > 0 && (
                <DetailRow
                  label={t('pages.pestDetail.hostPlants')}
                  value={hostPlants.join(', ')}
                />
              )}
              {pest.lifecycle_days != null && (
                <DetailRow
                  label={t('pages.ipm.lifecycleDays')}
                  value={`${pest.lifecycle_days} ${t('pages.ipm.days')}`}
                />
              )}
              {hasTempRange && (
                <DetailRow
                  label={t('pages.pestDetail.tempRange')}
                  value={`${pest.optimal_temp_min}\u2013${pest.optimal_temp_max} \u00b0C`}
                />
              )}
              {hasHumidityRange && (
                <DetailRow
                  label={t('pages.pestDetail.humidityRange')}
                  value={`${pest.optimal_humidity_min}\u2013${pest.optimal_humidity_max} %`}
                />
              )}
            </Box>
          </CardContent>
        </Card>

        {/* Beneficial organisms — shown only when present */}
        {beneficials.length > 0 && (
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <HelpTooltip term="nuetzlinge">
                  {t('pages.pestDetail.sectionBeneficials')}
                </HelpTooltip>
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
                {t('pages.pestDetail.sectionBeneficialsIntro2')}
              </Typography>
              <Stack
                spacing={1}
                component="ul"
                sx={{ listStyle: 'none', p: 0, m: 0 }}
                data-testid="pest-detail-beneficials"
              >
                {beneficials.map((b) => (
                  <Box
                    key={b.key}
                    component="li"
                    data-testid="beneficial-item"
                    sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
                  >
                    <FavoriteIcon
                      color="success"
                      fontSize="small"
                      aria-hidden="true"
                      sx={{ flexShrink: 0 }}
                    />
                    <Box>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {b.common_name}
                      </Typography>
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ fontStyle: 'italic', display: 'block' }}
                        aria-label={`${t('pages.pestDetail.beneficialScientificName')}: ${b.scientific_name}`}
                      >
                        {b.scientific_name}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Stack>
            </CardContent>
          </Card>
        )}
      </Box>

      {/* Countermeasures per IPM hierarchy */}
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <HelpTooltip term="ipm">
              {t('pages.pestDetail.sectionTreatments')}
            </HelpTooltip>
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('pages.pestDetail.treatmentsIntro')}
          </Typography>
          {treatmentGroups.length === 0 ? (
            <Typography
              variant="body2"
              color="text.secondary"
              data-testid="pest-detail-no-treatments"
            >
              {t('pages.pestDetail.noTreatments')}
            </Typography>
          ) : (
            <Stack spacing={2} data-testid="pest-detail-treatments">
              {treatmentGroups.map((group) => (
                <Box key={group.type} data-testid={`treatment-group-${group.type}`}>
                  <Typography
                    variant="subtitle2"
                    gutterBottom
                    component="h3"
                    sx={{ fontWeight: 700 }}
                  >
                    {t(`enums.treatmentType.${group.type}`)}
                  </Typography>
                  <Stack spacing={1} component="ul" sx={{ listStyle: 'none', p: 0, m: 0 }}>
                    {group.items.map((tr) => (
                      <Box
                        key={tr.key}
                        component="li"
                        sx={{ pl: 1.5, borderLeft: 3, borderColor: 'divider' }}
                        data-testid="treatment-item"
                      >
                        <Link
                          component={RouterLink}
                          to={`/pflanzenschutz/treatments/${tr.key}`}
                          variant="body2"
                          underline="hover"
                          sx={{ fontWeight: 600, textAlign: 'left', display: 'block' }}
                          data-testid="treatment-detail-link"
                        >
                          {l(tr, 'name')}
                        </Link>
                        {/* Why the measure helps — short localized summary (REQ-010). */}
                        {(l(tr, 'description') || l(tr, 'mode_of_action')) && (
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ display: 'block', mt: 0.25 }}
                            data-testid="treatment-summary"
                          >
                            {l(tr, 'description') || l(tr, 'mode_of_action')}
                          </Typography>
                        )}
                        {tr.active_ingredient && (
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ display: 'block', mt: 0.25 }}
                          >
                            {t('pages.pestDetail.activeIngredient')}: {tr.active_ingredient}
                          </Typography>
                        )}
                        {tr.safety_interval_days > 0 && (
                          <Stack
                            direction="row"
                            spacing={0.5}
                            sx={{ alignItems: 'center', mt: 0.5 }}
                          >
                            <Chip
                              icon={<ScheduleIcon />}
                              size="small"
                              color="warning"
                              variant="outlined"
                              label={t('pages.pestDetail.karenzDays', {
                                days: tr.safety_interval_days,
                              })}
                              data-testid="treatment-karenz"
                            />
                            <HelpTooltip term="karenzzeit" iconOnly />
                          </Stack>
                        )}
                      </Box>
                    ))}
                  </Stack>
                </Box>
              ))}
            </Stack>
          )}
        </CardContent>
      </Card>

      {/* Prevention & monitoring */}
      {(preventionTips || monitoringHints) && (
        <Card variant="outlined" sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {t('pages.pestDetail.sectionPrevention')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
              {t('pages.pestDetail.sectionPreventionIntro')}
            </Typography>
            <Box
              component="dl"
              sx={{ m: 0, '& > *:not(:last-child)': { borderBottom: 1, borderColor: 'divider', pb: 1.5, mb: 1.5 } }}
            >
              {preventionTips && (
                <DetailRow
                  label={t('pages.pestDetail.preventionTips')}
                  value={preventionTips}
                />
              )}
              {monitoringHints && (
                <DetailRow
                  label={t('pages.pestDetail.monitoringHints')}
                  value={monitoringHints}
                />
              )}
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

interface DetailRowProps {
  label: string;
  value: React.ReactNode;
}

/**
 * Semantic label/value pair rendered as `dt`/`dd` within a `dl` container.
 * The parent `<Box component="dl">` provides the list context (WCAG 1.3.1).
 */
function DetailRow({ label, value }: DetailRowProps) {
  return (
    <Box>
      <Typography
        component="dt"
        variant="caption"
        color="text.secondary"
        sx={{ display: 'block', mb: 0.25 }}
      >
        {label}
      </Typography>
      {typeof value === 'string' ? (
        <Typography component="dd" variant="body2" sx={{ m: 0 }}>
          {value}
        </Typography>
      ) : (
        <Box component="dd" sx={{ m: 0 }}>
          {value}
        </Box>
      )}
    </Box>
  );
}
