/**
 * The head of the bed view (REQ-053 GP-FR-047, GP-FR-077): area, type, status, soil, sun, active
 * plants, open tasks, last care, next due date, assignment and the previous year; the drainage only while it
 * is known. It reads the summary only and owns no state. A bed wider than its access reaches gets the
 * `bed.reach_too_wide` hint (GP-FR-166): a badge, never an error, shown only while it applies. Its access is the
 * stronger of the recorded `access_sides` and the server-derived `path_access` (paths beside the bed, #2703).
 * The cover photo (GP-FR-051) leads the head while the bed has one: full width on a phone, beside the facts from `sm`.
 * The nutrient hint (GP-FR-125, WP 8.10) is shown only while it says something: "Düngebedarf wahrscheinlich" for
 * `likely_deficit`, "Düngung prüfen" for `check`, each with its reasons - never a number. `ok` and
 * `insufficient_data` show nothing (until a threshold has a source every bed is `insufficient_data`, E-10).
 * The salt-limit reason `check_salt_content` (E-17 variant A) is no supply finding and never changes the state, so it
 * is shown as a fact of its own whenever the hint carries it - whatever the state - and left out of the nutrient
 * reasons. It stays hidden until a sourced salt threshold is configured on the server.
 * Root competition or allelopathy reported at the bed (GP-FR-165, WP 9.11) is part of the site line and a neutral
 * chip naming exactly the flags set, shown only while one is - a note, never a rating.
 * The distance to the nearest water source (GP-FR-167, WP 9.12) is derived on the server, edge to edge in a straight
 * line; it is shown only while the site has a water source and the bed a geometry - "no source" is not "0 m".
 */
import { useMemo, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import TerrainOutlinedIcon from '@mui/icons-material/TerrainOutlined';
import WbSunnyOutlinedIcon from '@mui/icons-material/WbSunnyOutlined';
import { assessReach, type ReachAccess } from '../model/reach';
import { DEFAULT_REACH_THRESHOLDS, reachOptions } from '../model/siteThresholds';
import type { ReachThresholds } from '@/api/types';
import BedCoverPhoto from './BedCoverPhoto';
import type { BedAssignee, BedSummary, NutrientHint, NutrientHintConfidence, NutrientHintReason } from './types';
import {
  BED_STATUS_COLOR,
  formatBedDate,
  isOverdue,
  siteConditionsLine,
  siteFlagsLine,
  sunProfileLine,
  waterSourceText,
} from './bedFormat';

interface BedHeaderProps {
  summary: BedSummary;
  /** Display name of the location type; the raw key is shown while the types are loading. */
  typeName: string;
  assignees: readonly BedAssignee[];
  /** The season shown (`?year=`) and the years on offer. */
  year: number;
  years: readonly number[];
  onYearChange: (year: number) => void;
  /** `null` hides the control (a viewer cannot change the status). */
  onChangeStatus: (() => void) | null;
  /** `null` hides the control (a viewer cannot change the sun class, GP-FR-157). */
  onChangeSun?: (() => void) | null;
  /** `null` hides the control (a viewer cannot change the site conditions, GP-FR-162/163/168). */
  onChangeSite?: (() => void) | null;
  /** Reasons given when a planting went ahead despite a crop-rotation hint (GP-FR-132); empty = no badge. */
  rotationReasons?: readonly string[];
  /** The site's reach thresholds (GP-FR-166, WP 8.24); absent = 1.2 / 0.6 m. The path distance acts on the server. */
  reachThresholds?: Readonly<Pick<ReachThresholds, 'both_sides_m' | 'one_side_m'>>;
}

/** One literal key per access class, so the i18n key checks see every key that is used. */
const REACH_DETAIL_KEY: Record<ReachAccess, string> = {
  both: 'pages.bed.header.reachDetail_both',
  one: 'pages.bed.header.reachDetail_one',
  unknown: 'pages.bed.header.reachDetail_unknown',
};

/** One literal key per reason code and confidence, so the i18n key checks see every key that is used. */
const NUTRIENT_REASON_KEY: Record<NutrientHintReason, string> = {
  substrate_bed: 'pages.bed.header.nutrient.reasons.substrate_bed',
  no_current_crop: 'pages.bed.header.nutrient.reasons.no_current_crop',
  species_not_readable: 'pages.bed.header.nutrient.reasons.species_not_readable',
  demand_unknown: 'pages.bed.header.nutrient.reasons.demand_unknown',
  thresholds_without_source: 'pages.bed.header.nutrient.reasons.thresholds_without_source',
  no_feeding_recorded: 'pages.bed.header.nutrient.reasons.no_feeding_recorded',
  feeding_overdue: 'pages.bed.header.nutrient.reasons.feeding_overdue',
  feeding_due: 'pages.bed.header.nutrient.reasons.feeding_due',
  fed_recently: 'pages.bed.header.nutrient.reasons.fed_recently',
  p_class_low: 'pages.bed.header.nutrient.reasons.p_class_low',
  k_class_low: 'pages.bed.header.nutrient.reasons.k_class_low',
  content_classes_sufficient: 'pages.bed.header.nutrient.reasons.content_classes_sufficient',
  demand_partly_unknown: 'pages.bed.header.nutrient.reasons.demand_partly_unknown',
  preceding_nitrogen_fixer: 'pages.bed.header.nutrient.reasons.preceding_nitrogen_fixer',
  standing_nitrogen_fixer: 'pages.bed.header.nutrient.reasons.standing_nitrogen_fixer',
  bark_mulch_n_binding: 'pages.bed.header.nutrient.reasons.bark_mulch_n_binding',
  p_or_k_class_high: 'pages.bed.header.nutrient.reasons.p_or_k_class_high',
  check_salt_content: 'pages.bed.header.nutrient.reasons.check_salt_content',
};
const NUTRIENT_CONFIDENCE_KEY: Record<NutrientHintConfidence, string> = {
  low: 'pages.bed.header.nutrient.confidence_low',
  medium: 'pages.bed.header.nutrient.confidence_medium',
  high: 'pages.bed.header.nutrient.confidence_high',
};

/** The hint states the head shows; the others say nothing a grower can act on. */
function shownNutrientHint(hint: NutrientHint | null | undefined): NutrientHint | null {
  return hint && (hint.state === 'likely_deficit' || hint.state === 'check') ? hint : null;
}

/** The salt-limit reason is shown on its own (it is independent of the nutrient state). */
const SALT_REASON: NutrientHintReason = 'check_salt_content';

function Fact({
  label,
  children,
  testId,
  fullRow = false,
}: {
  label: string;
  children: ReactNode;
  testId: string;
  fullRow?: boolean;
}) {
  return (
    <Box sx={{ minWidth: 0, overflowWrap: 'anywhere', ...(fullRow && { gridColumn: '1 / -1' }) }} data-testid={testId}>
      <Typography variant="caption" color="text.secondary" component="div">
        {label}
      </Typography>
      <Typography variant="body1" component="div">
        {children}
      </Typography>
    </Box>
  );
}

export default function BedHeader({
  summary,
  typeName,
  assignees,
  year,
  years,
  onYearChange,
  onChangeStatus,
  onChangeSun = null,
  onChangeSite = null,
  rotationReasons = [],
  reachThresholds = DEFAULT_REACH_THRESHOLDS,
}: BedHeaderProps) {
  const { t, i18n } = useTranslation();
  const language = i18n.language;
  const area = useMemo(
    () => new Intl.NumberFormat(language, { maximumFractionDigits: 2 }).format(summary.area_m2),
    [language, summary.area_m2],
  );
  const soil = summary.soil_profile;
  const lastCare = formatBedDate(summary.last_care_at, language);
  const nextDue = formatBedDate(summary.next_due_at, language);
  const overdue = isOverdue(summary.next_due_at);
  const notSet = t('pages.bed.header.unknown');
  const sunLine = sunProfileLine(t, summary.site_conditions?.sun_profile);
  const siteLine = siteConditionsLine(t, summary.site_conditions);
  const accessSides = summary.site_conditions?.access_sides;
  const flagsLine = siteFlagsLine(t, summary.site_conditions?.flags);
  const pathAccess = summary.path_access ?? null;
  const reach = useMemo(
    () =>
      assessReach(summary.geometry, accessSides, { ...reachOptions(reachThresholds), pathAccess }),
    [summary.geometry, accessSides, reachThresholds, pathAccess],
  );
  const waterText = waterSourceText(t, language, summary.nearest_water_source_m, 'header');
  const nutrientHint = shownNutrientHint(summary.nutrient_hint);
  const saltCheck = summary.nutrient_hint?.reasons.includes(SALT_REASON) ?? false;
  const reachNumbers = useMemo(() => {
    // Three digits: a bed of 0.601 m is wider than 0.6 m and must not read as "0.6 m".
    const format = new Intl.NumberFormat(language, { maximumFractionDigits: 3 });
    return { width: format.format(reach.widthM ?? 0), threshold: format.format(reach.thresholdM) };
  }, [language, reach.widthM, reach.thresholdM]);

  return (
    <Card variant="outlined" data-testid="bed-header" component="section" aria-label={t('pages.bed.header.title')}>
      <CardContent>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 2, alignItems: 'flex-start' }}>
          <BedCoverPhoto
            coverPhotoRef={summary.cover_photo_ref}
            bedName={summary.name}
            sx={{ width: { xs: '100%', sm: 200 }, height: { xs: 180, sm: 150 } }}
            testId="bed-header-cover"
          />
          <Box sx={{
              flex: 1,
              minWidth: 0,
              width: '100%',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
              gap: 2,
              alignItems: 'start',
            }}>
            <Fact label={t('pages.bed.header.area')} testId="bed-header-area">
              {area} m²
            </Fact>
            <Fact label={t('pages.bed.header.type')} testId="bed-header-type">
              {typeName || notSet}
            </Fact>
            <Fact label={t('pages.bed.header.status')} testId="bed-header-status">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                <Chip
                  size="small"
                  color={BED_STATUS_COLOR[summary.bed_status]}
                  label={t(`enums.bedStatus.${summary.bed_status}`)}
                />
                {onChangeStatus && (
                  <Button
                    size="small"
                    startIcon={<SwapHorizIcon />}
                    onClick={onChangeStatus}
                    data-testid="bed-status-change-button"
                    sx={{ minHeight: 44 }}
                  >
                    {t('pages.bed.header.changeStatus')}
                  </Button>
                )}
              </Box>
              {rotationReasons.length > 0 && (
                <Box sx={{ mt: 0.5 }} data-testid="bed-rotation-badge">
                  <Chip size="small" color="warning" label={t('pages.bed.header.rotationHint')} />
                  <Typography variant="caption" color="text.secondary" component="div">
                    {t('pages.bed.header.rotationReason', { reason: rotationReasons[0] })}
                  </Typography>
                </Box>
              )}
            </Fact>
            <Fact label={t('pages.bed.header.soil')} testId="bed-header-soil">
              {soil && soil.soil_texture !== 'unknown' ? t(`enums.soilTexture.${soil.soil_texture}`) : notSet}
            </Fact>
            {soil && soil.drainage !== 'unknown' && (
              <Fact label={t('pages.bed.soil.drainage')} testId="bed-header-drainage">
                {t(`enums.soilDrainage.${soil.drainage}`)}
              </Fact>
            )}
            <Fact label={t('pages.bed.header.sun')} testId="bed-header-sun">
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                {summary.sun_exposure !== 'unknown' ? t(`enums.sunExposure.${summary.sun_exposure}`) : notSet}
                {onChangeSun && (
                  <Button
                    size="small"
                    startIcon={<WbSunnyOutlinedIcon />}
                    onClick={onChangeSun}
                    data-testid="bed-sun-change-button"
                    sx={{ minHeight: 44 }}
                  >
                    {t('pages.bed.header.changeSun')}
                  </Button>
                )}
              </Box>
              {sunLine && (
                <Typography variant="caption" color="text.secondary" component="div" data-testid="bed-header-sun-profile">
                  {sunLine}
                </Typography>
              )}
            </Fact>
            {(siteLine || onChangeSite) && (
              <Fact label={t('pages.bed.header.site')} testId="bed-header-site">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                  {siteLine ?? notSet}
                  {onChangeSite && (
                    <Button
                      size="small"
                      startIcon={<TerrainOutlinedIcon />}
                      onClick={onChangeSite}
                      data-testid="bed-site-change-button"
                      sx={{ minHeight: 44 }}
                    >
                      {t('pages.bed.header.changeSite')}
                    </Button>
                  )}
                </Box>
                {flagsLine && (
                  <Box sx={{ mt: 0.5 }} data-testid="bed-site-flags">
                    <Chip
                      size="small"
                      color="info"
                      variant="outlined"
                      label={flagsLine}
                      data-testid="bed-site-flags-badge"
                      sx={{ maxWidth: '100%', height: 'auto', '& .MuiChip-label': { whiteSpace: 'normal' } }}
                    />
                  </Box>
                )}
              </Fact>
            )}
            {reach.hint && (
              <Fact label={t('pages.bed.header.reach')} testId="bed-header-reach">
                <Chip
                  size="small"
                  color="warning"
                  variant="outlined"
                  label={t('pages.bed.header.reachHint')}
                  data-testid="bed-reach-badge"
                />
                <Typography variant="caption" color="text.secondary" component="div" data-testid="bed-reach-detail">
                  {t(REACH_DETAIL_KEY[reach.access], reachNumbers)}
                </Typography>
              </Fact>
            )}
            {waterText && (
              <Fact label={t('pages.bed.header.waterSource')} testId="bed-header-water-source">
                {waterText}
              </Fact>
            )}
            {nutrientHint && (
              <Fact label={t('pages.bed.header.nutrient.label')} testId="bed-header-nutrient" fullRow>
                <Chip
                  size="small"
                  color={nutrientHint.state === 'likely_deficit' ? 'warning' : 'info'}
                  variant={nutrientHint.state === 'likely_deficit' ? 'filled' : 'outlined'}
                  label={t(
                    nutrientHint.state === 'likely_deficit'
                      ? 'pages.bed.header.nutrient.likelyDeficit'
                      : 'pages.bed.header.nutrient.check',
                  )}
                  data-testid="bed-nutrient-badge"
                  data-state={nutrientHint.state}
                />
                <Box component="ul" sx={{ m: 0, mt: 0.5, pl: 2 }} data-testid="bed-nutrient-reasons">
                  {nutrientHint.reasons.filter((reason) => reason !== SALT_REASON).map((reason) => (
                    <Typography key={reason} component="li" variant="caption" color="text.secondary">
                      {t(NUTRIENT_REASON_KEY[reason])}
                    </Typography>
                  ))}
                </Box>
                <Typography variant="caption" color="text.secondary" component="div" data-testid="bed-nutrient-note">
                  {t(NUTRIENT_CONFIDENCE_KEY[nutrientHint.confidence])} {t('pages.bed.header.nutrient.noAmount')}
                </Typography>
              </Fact>
            )}
            {saltCheck && (
              <Fact label={t('pages.bed.header.nutrient.saltLabel')} testId="bed-header-salt" fullRow>
                <Chip
                  size="small"
                  color="warning"
                  variant="outlined"
                  label={t('pages.bed.header.nutrient.saltCheck')}
                  data-testid="bed-salt-badge"
                />
                <Typography variant="caption" color="text.secondary" component="div" data-testid="bed-salt-detail">
                  {t(NUTRIENT_REASON_KEY[SALT_REASON])}
                </Typography>
              </Fact>
            )}
            <Fact label={t('pages.bed.header.plants')} testId="bed-header-plants">
              {t('pages.bed.header.plantCount', { count: summary.active_plant_count })}
              {summary.species_keys.length > 0 && (
                <Typography variant="caption" color="text.secondary" component="div">
                  {t('pages.bed.header.speciesCount', { count: summary.species_keys.length })}
                </Typography>
              )}
            </Fact>
            <Fact label={t('pages.bed.header.openTasks')} testId="bed-header-tasks">
              {t('pages.bed.header.taskCount', { count: summary.open_task_count })}
              {summary.overdue_task_count > 0 && (
                <Typography variant="caption" color="error" component="div">
                  {t('pages.bed.header.overdueCount', { count: summary.overdue_task_count })}
                </Typography>
              )}
            </Fact>
            <Fact label={t('pages.bed.header.lastCare')} testId="bed-header-last-care">
              {lastCare ?? t('pages.bed.header.never')}
            </Fact>
            <Fact label={t('pages.bed.header.nextDue')} testId="bed-header-next-due">
              {nextDue ? (
                <Typography component="span" color={overdue ? 'error' : 'inherit'}>
                  {nextDue}
                </Typography>
              ) : (
                t('pages.bed.header.none')
              )}
            </Fact>
            <Fact label={t('pages.bed.header.assigned')} testId="bed-header-assigned">
              {assignees.length > 0 ? (
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                  {assignees.map((person) => (
                    <Chip key={person.membershipKey} size="small" variant="outlined" label={person.displayName} />
                  ))}
                </Box>
              ) : (
                t('pages.bed.header.nobody')
              )}
            </Fact>
          </Box>
        </Box>

        <Box
          sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 2, alignItems: 'center' }}
          data-testid="bed-header-season"
        >
          <TextField
            select
            size="small"
            label={t('pages.bed.header.year')}
            value={year}
            onChange={(event) => onYearChange(Number(event.target.value))}
            sx={{ minWidth: 120, '& .MuiInputBase-root': { minHeight: 44 } }}
            slotProps={{ htmlInput: { 'data-testid': 'bed-year-select' } }}
          >
            {years.map((value) => (
              <MenuItem key={value} value={value}>
                {value}
              </MenuItem>
            ))}
          </TextField>
          <Typography variant="body2" color="text.secondary" data-testid="bed-header-previous-year">
            {t('pages.bed.header.previousYear', { year: year - 1 })}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}
