import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import BugReportIcon from '@mui/icons-material/BugReport';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import ScheduleIcon from '@mui/icons-material/Schedule';
import HelpTooltip from '@/components/common/HelpTooltip';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import PageTitle from '@/components/layout/PageTitle';
import { useLocalizedField } from '@/hooks/useLocalizedField';
import { getTreatmentDetail } from '@/api/endpoints/ipm';
import type { TreatmentDetail } from '@/api/types';

type ChipColor = 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';

const treatmentTypeColor: Record<string, ChipColor> = {
  cultural: 'success',
  biological: 'info',
  mechanical: 'default',
  chemical: 'warning',
};

/**
 * REQ-010 — Treatment (countermeasure) detail page.
 *
 * Shows a localized profile of a plant-protection measure (description, how to
 * apply, mode of action, precautions, structured facts) plus the pests and
 * diseases it is used against. Data comes from `GET /ipm/treatments/{key}/detail`.
 * Multilingual content is seed-driven (name/name_de … via useLocalizedField).
 *
 * UI patterns:
 * - UI-NFR-017 Pattern C: two-row header (title + meta chips)
 * - UI-NFR-011: HelpTooltip for IPM, Karenzzeit, Nützlinge terms
 * - UI-NFR-008 R-038: Panel intro texts for all sections
 * - Responsive: mobile-first single column, md+ two-column for compact panels
 */
export default function TreatmentDetailPage() {
  const { t } = useTranslation();
  const l = useLocalizedField();
  const navigate = useNavigate();
  const { key = '' } = useParams<{ key: string }>();

  const [detail, setDetail] = useState<TreatmentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setDetail(await getTreatmentDetail(key));
    } catch {
      setError(t('pages.treatmentDetail.loadError'));
    } finally {
      setLoading(false);
    }
  }, [key, t]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  const goBack = useCallback(() => navigate('/pflanzenschutz/treatments'), [navigate]);

  // Stable memoized localized field values — React 19 + useMemo (style-guide obligation).
  const localizedFields = useMemo(
    () => ({
      name: detail ? l(detail.treatment, 'name') : '',
      description: detail ? l(detail.treatment, 'description') : null,
      howToApply: detail ? l(detail.treatment, 'how_to_apply') : null,
      modeOfAction: detail ? l(detail.treatment, 'mode_of_action') : null,
      precautions: detail ? l(detail.treatment, 'precautions') : null,
    }),
    [detail, l],
  );

  if (loading) {
    return (
      <Box data-testid="treatment-detail-page">
        <LoadingSkeleton variant="card" />
      </Box>
    );
  }

  if (error || !detail) {
    return (
      <Box data-testid="treatment-detail-page">
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
          <Button startIcon={<ArrowBackIcon />} onClick={goBack} data-testid="treatment-detail-back">
            {t('pages.treatmentDetail.back')}
          </Button>
        </Box>
        <Alert severity="error" data-testid="treatment-detail-error">
          {error ?? t('pages.treatmentDetail.notFound')}
        </Alert>
      </Box>
    );
  }

  const { treatment, targeted_pests, targeted_diseases } = detail;
  const { name, description, howToApply, modeOfAction, precautions } = localizedFields;

  return (
    <Box data-testid="treatment-detail-page">
      {/*
       * UI-NFR-017 Pattern C: two-row header.
       * Row 1: PageTitle (sx={{ mb: 0 }}) + back button (right)
       * Row 2: meta chips (treatment type, Karenz)
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
          <PageTitle title={name} sx={{ mb: 0 }} />
          {/* Row 2: type chip + optional Karenz chip */}
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 1,
              mt: 0.5,
            }}
          >
            <HelpTooltip term="ipm">
              <Chip
                label={t(`enums.treatmentType.${treatment.treatment_type}`)}
                size="small"
                color={treatmentTypeColor[treatment.treatment_type] ?? 'default'}
                data-testid="treatment-detail-type"
              />
            </HelpTooltip>
            {treatment.safety_interval_days > 0 && (
              <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center' }}>
                <Chip
                  icon={<ScheduleIcon />}
                  size="small"
                  color="warning"
                  variant="outlined"
                  label={t('pages.pestDetail.karenzDays', { days: treatment.safety_interval_days })}
                  data-testid="treatment-detail-karenz"
                />
                <HelpTooltip term="karenzzeit" iconOnly />
              </Stack>
            )}
          </Box>
        </Box>
        {/* Right: back navigation */}
        <Button startIcon={<ArrowBackIcon />} onClick={goBack} data-testid="treatment-detail-back">
          {t('pages.treatmentDetail.back')}
        </Button>
      </Box>

      {/* Page intro text — always visible (description or generic intro) */}
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {description ?? t('pages.treatmentDetail.pageIntro')}
      </Typography>

      {/* Structured facts */}
      <Card variant="outlined" sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" component="h2" gutterBottom>
            {t('pages.treatmentDetail.sectionFacts')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
            {t('pages.treatmentDetail.sectionFactsIntro')}
          </Typography>
          <Box
            component="dl"
            sx={{ m: 0, '& > *:not(:last-child)': { borderBottom: 1, borderColor: 'divider', pb: 1.5, mb: 1.5 } }}
          >
            <DetailRow
              label={t('pages.treatmentDetail.applicationMethod')}
              value={t(`enums.ipmApplicationMethod.${treatment.application_method}`)}
            />
            {treatment.active_ingredient && (
              <DetailRow
                label={t('pages.treatmentDetail.activeIngredient')}
                value={treatment.active_ingredient}
              />
            )}
            {treatment.dosage_per_liter != null && (
              <DetailRow
                label={t('pages.treatmentDetail.dosagePerLiter')}
                value={`${treatment.dosage_per_liter} ml/l`}
              />
            )}
            <DetailRow
              label={
                <HelpTooltip term="karenzzeit" iconOnly>
                  {t('pages.treatmentDetail.karenz')}
                </HelpTooltip>
              }
              value={
                treatment.safety_interval_days > 0
                  ? t('pages.treatmentDetail.karenzDaysValue', { days: treatment.safety_interval_days })
                  : t('pages.treatmentDetail.karenzNone')
              }
            />
            {treatment.protective_equipment.length > 0 && (
              <DetailRow
                label={t('pages.treatmentDetail.protectiveEquipment')}
                value={treatment.protective_equipment.join(', ')}
              />
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Responsive two-column grid for compact text sections on md+ */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            md: howToApply && modeOfAction ? '1fr 1fr' : '1fr',
          },
          gap: 2,
          mb: 2,
          alignItems: 'start',
        }}
      >
        {howToApply && (
          <DetailCard
            title={t('pages.treatmentDetail.sectionHowToApply')}
            intro={t('pages.treatmentDetail.sectionHowToApplyIntro')}
            body={howToApply}
            testid="treatment-how-to-apply"
          />
        )}
        {modeOfAction && (
          <DetailCard
            title={t('pages.treatmentDetail.sectionModeOfAction')}
            intro={t('pages.treatmentDetail.sectionModeOfActionIntro')}
            body={modeOfAction}
            testid="treatment-mode-of-action"
          />
        )}
      </Box>

      {precautions && (
        <Card variant="outlined" sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" component="h2" gutterBottom>
              {t('pages.treatmentDetail.sectionPrecautions')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
              {t('pages.treatmentDetail.sectionPrecautionsIntro')}
            </Typography>
            <Typography variant="body2" data-testid="treatment-precautions">
              {precautions}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Targets: pests (linked) + diseases */}
      {(targeted_pests.length > 0 || targeted_diseases.length > 0) && (
        <Card variant="outlined" sx={{ mb: 2 }}>
          <CardContent>
            <Typography variant="h6" component="h2" gutterBottom>
              {t('pages.treatmentDetail.sectionTargets')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
              {t('pages.treatmentDetail.sectionTargetsIntro')}
            </Typography>

            {targeted_pests.length > 0 && (
              <>
                <Typography
                  variant="subtitle2"
                  component="h3"
                  sx={{ fontWeight: 700, mb: 0.5, mt: targeted_diseases.length > 0 ? 0 : undefined }}
                >
                  {t('pages.treatmentDetail.targetedPests')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {t('pages.treatmentDetail.targetedPestsIntro')}
                </Typography>
                <Stack
                  direction="row"
                  sx={{ flexWrap: 'wrap', gap: 1, mb: targeted_diseases.length > 0 ? 2 : 0 }}
                  component="ul"
                  aria-label={t('pages.treatmentDetail.targetedPests')}
                  data-testid="treatment-targeted-pests"
                >
                  {targeted_pests.map((p) => (
                    <Box component="li" key={p.key} sx={{ listStyle: 'none' }}>
                      <Chip
                        component={RouterLink}
                        to={`/pflanzenschutz/pests/${p.key}`}
                        icon={<BugReportIcon />}
                        label={l(p, 'common_name')}
                        size="small"
                        variant="outlined"
                        aria-label={`${l(p, 'common_name')} — ${t('pages.treatmentDetail.viewPestDetail')}`}
                        sx={{ cursor: 'pointer', minHeight: 44 }}
                        data-testid="treatment-target-pest"
                        clickable
                      />
                    </Box>
                  ))}
                </Stack>
              </>
            )}

            {targeted_diseases.length > 0 && (
              <>
                <Typography variant="subtitle2" component="h3" sx={{ fontWeight: 700, mb: 0.5 }}>
                  {t('pages.treatmentDetail.targetedDiseases')}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {t('pages.treatmentDetail.targetedDiseasesIntro')}
                </Typography>
                <Stack
                  direction="row"
                  sx={{ flexWrap: 'wrap', gap: 1 }}
                  component="ul"
                  aria-label={t('pages.treatmentDetail.targetedDiseases')}
                  data-testid="treatment-targeted-diseases"
                >
                  {targeted_diseases.map((d) => (
                    <Box component="li" key={d.key} sx={{ listStyle: 'none' }}>
                      <Chip
                        icon={<LocalHospitalIcon />}
                        label={l(d, 'common_name')}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                  ))}
                </Stack>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

interface DetailCardProps {
  title: string;
  intro: string;
  body: string;
  testid: string;
}

/**
 * Reusable section card with heading, intro text and body content.
 * Uses component="h2" for correct heading hierarchy (PageTitle is h1).
 */
function DetailCard({ title, intro, body, testid }: DetailCardProps) {
  return (
    <Card variant="outlined" sx={{ mb: 0 }}>
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          {intro}
        </Typography>
        <Typography variant="body2" data-testid={testid}>
          {body}
        </Typography>
      </CardContent>
    </Card>
  );
}

interface DetailRowProps {
  label: React.ReactNode;
  value: React.ReactNode;
}

/**
 * Semantic label/value pair rendered as `dt`/`dd` within a `dl` container.
 * The parent `<Box component="dl">` provides the list context (WCAG 1.3.1).
 */
function DetailRow({ label, value }: DetailRowProps) {
  return (
    <Box>
      <Typography component="dt" variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.25 }}>
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
