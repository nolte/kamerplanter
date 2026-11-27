/**
 * Crop-rotation and companion hints with a strength (REQ-053 GP-FR-132, D-09): shown in the planting
 * dialog before the layout is chosen, never as a blocker. From a warning on, the grower plants anyway
 * only with a reason ("Trotzdem pflanzen"), which the run stores as `rotation_override_reason`.
 * Root competition or allelopathy reported at the bed (GP-FR-165) adds one neutral note for the whole bed that names
 * exactly the flags set ("Allelopathy risk reported at this site"). Nothing is computed from it: no strength, no
 * `site_fit`, no reason needed to plant.
 * A species that needs a support (`support_required`, W-005) names the trellises drawn in the bed, or says there is
 * none (`SupportHint`, WP 10.10) - information only.
 * Soil hazards of the bed (REQ-053 §11.3a Nr. 6, #2888 F-21) come from the same server answer as the rotation hints
 * (`soil_hazard.*` codes) and are worded here only - nothing is computed in the client. They hang on the soil, not on
 * the rotation: a bed whose rotation check is off still lists them.
 */
import { Fragment } from 'react';
import { useTranslation } from 'react-i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Checkbox from '@mui/material/Checkbox';
import CircularProgress from '@mui/material/CircularProgress';
import FormControlLabel from '@mui/material/FormControlLabel';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import type { Translate } from '@/i18n/translate';
import type { HintState, MixPair } from './useBedHints';
import SiteAxisHints from './SiteAxisHints';
import SiteFitHint from './SiteFitHint';
import SupportHint from './SupportHint';
import type { BedTrellisState } from './useBedTrellises';
import type { SpeciesSiteFit } from './siteFitOf';
import type { SiteAxisHint } from '../model/siteFit';
import type { SunExposure } from '../model/types';
import type { SiteFlag } from '../bed/types';
import { siteFlagsLine } from '../bed/bedFormat';
import { formatDate } from '@/utils/formatting';
import { needsOverrideReason } from './plantingLogic';
import type { NeighbourHint, RotationFinding, RotationSeverity } from './plantingTypes';
import PlannerGlossary, { type PlannerGlossaryTerm } from '../glossary/PlannerGlossary';

const ALERT_SEVERITY: Record<RotationSeverity, 'success' | 'info' | 'warning' | 'error'> = {
  OK: 'success',
  INFO: 'info',
  WARNING: 'warning',
  CRITICAL: 'error',
};

/** The heading of a species' hints: a noun per strength ("kritischer Hinweis", not "Hinweis kritisch", #2764). */
const SEVERITY_HEADING_KEY: Record<RotationSeverity, string> = {
  OK: 'pages.bed.planting.hints.severity.OK',
  INFO: 'pages.bed.planting.hints.severity.INFO',
  WARNING: 'pages.bed.planting.hints.severity.WARNING',
  CRITICAL: 'pages.bed.planting.hints.severity.CRITICAL',
};

export const MAX_OVERRIDE_REASON = 500;

/** The terms the hints use (GP-UX-011): rotation, its pause, the neighbours and the perennial-crop exemption. */
const HINT_TERMS: readonly PlannerGlossaryTerm[] = ['fruchtfolge', 'anbaupause', 'mischkultur', 'dauerkultur'];

interface HintsPanelProps {
  /** Entries in the dialog's order: the species, its display name and the state of its request. */
  species: readonly {
    key: string;
    name: string;
    state: HintState | undefined;
    /** The site-fit hint of the species on this bed; `null` = nothing to say (GP-FR-160). */
    siteFit?: SpeciesSiteFit | null;
    /** The frost, wind and waterlogging hints of the species on this bed (GP-FR-161); empty = none. */
    axisHints?: readonly SiteAxisHint[];
    /** The trellises in the bed when the species needs a support (W-005); `null`/absent = no support hint. */
    support?: BedTrellisState | null;
  }[];
  /** The sun class of the bed, named in the site-fit line. */
  bedSun?: SunExposure;
  /** Competition flags of the bed (GP-FR-165); empty or absent = no line. */
  siteFlags?: readonly SiteFlag[];
  /** Names of species by key, for the neighbours the server names. */
  speciesNames: ReadonlyMap<string, string>;
  mix: readonly MixPair[];
  /** The strongest rotation/companion severity of all chosen species needs a reason. */
  overrideChecked: boolean;
  overrideReason: string;
  showReasonError: boolean;
  onOverrideChecked: (checked: boolean) => void;
  onOverrideReason: (reason: string) => void;
  /** Worst severity over all species; decides whether the "plant anyway" step is needed. */
  severity: RotationSeverity;
  /**
   * The caller can plant anyway with a reason (default). `false`: no "Trotzdem pflanzen" step - the single plant of
   * the plan's tool "Pflanze setzen" has no such path on the server (GP-UX-071), the caller says so itself.
   */
  overridable?: boolean;
}

/** The host a soil-hazard finding names: "Familie Brassicaceae", "Gattung Allium", "Art Solanum lycopersicum". */
function hostText(finding: RotationFinding, t: Translate): string {
  const name = finding.host_name?.trim() ?? '';
  if (!name || !finding.host_level) return t('pages.bed.planting.hints.soilHazard.hostUnnamed');
  return t(`pages.bed.planting.hints.soilHazard.host.${finding.host_level}`, { name });
}

/** The year a stage ends; only set where a 3/3-evidenced duration carries a time statement. */
function untilYear(finding: RotationFinding): string {
  return finding.hazard_until ? finding.hazard_until.slice(0, 4) : '';
}

/** A soil-hazard finding in words (REQ-053 §11.3a Nr. 6); `null` for a code this panel does not know. */
function soilHazardText(finding: RotationFinding, t: Translate): string | null {
  const values = {
    hazard: finding.hazard ? t(`enums.soilHazard.${finding.hazard}`) : t('pages.bed.planting.hints.soilHazard.unnamed'),
    confirmed: formatDate(finding.hazard_confirmed_at),
    host: hostText(finding, t),
    year: untilYear(finding),
  };
  switch (finding.code) {
    case 'soil_hazard.pause':
      return t('pages.bed.planting.hints.soilHazard.pause', values);
    case 'soil_hazard.no_evidenced_pause':
      return t('pages.bed.planting.hints.soilHazard.noEvidencedPause', values);
    case 'soil_hazard.residual':
      return t(
        finding.hazard_until
          ? 'pages.bed.planting.hints.soilHazard.residualUntil'
          : 'pages.bed.planting.hints.soilHazard.residualOpen',
        values,
      );
    case 'soil_hazard.soft':
      return t('pages.bed.planting.hints.soilHazard.soft', values);
    case 'soil_hazard.uncertain_host':
      return t('pages.bed.planting.hints.soilHazard.uncertainHost', values);
    default:
      return null;
  }
}

function findingText(
  finding: RotationFinding,
  t: Translate,
): string {
  const soil = soilHazardText(finding, t);
  if (soil !== null) return soil;
  // The server names the family (`family_name`). A family without a name is left out of the sentence: the database
  // key is never shown to the grower as if it were a name.
  const family = finding.family_name?.trim() ?? '';
  const named = family !== '';
  switch (finding.code) {
    case 'rotation.pause_not_elapsed':
      // Plural forms for both numbers: "vor 1 Jahr", "in diesem Jahr" for 0, "1 Jahr" pause (#2764).
      return t(named ? 'pages.bed.planting.hints.pauseNotElapsed' : 'pages.bed.planting.hints.pauseNotElapsedUnnamed', {
        family,
        count: finding.years_since ?? 0,
        pause: t('pages.bed.planting.hints.pauseYears', { count: finding.pause_years ?? 0 }),
        source: t(`pages.bed.planting.hints.pauseSource.${finding.pause_source ?? 'default'}`),
      });
    case 'rotation.pest_risk':
      return t(named ? 'pages.bed.planting.hints.pestRisk' : 'pages.bed.planting.hints.pestRiskUnnamed', { family });
    case 'rotation.replant_after_biotic_failure':
      // Disease or pest: the cause may sit in the soil (#2888). An unexpected cause reads as the disease sentence.
      return t(
        finding.termination_cause === 'pest'
          ? 'pages.bed.planting.hints.replantAfterPest'
          : 'pages.bed.planting.hints.replantAfterDisease',
      );
    case 'rotation.replant_cause_unknown':
      return t('pages.bed.planting.hints.replantCauseUnknown');
    case 'rotation.replant_foliar_disease':
      return t('pages.bed.planting.hints.replantFoliarDisease');
    case 'rotation.replant_soil_borne':
      return t(
        finding.termination_cause === 'pest'
          ? 'pages.bed.planting.hints.replantSoilBornePest'
          : 'pages.bed.planting.hints.replantSoilBorneDisease',
      );
    case 'rotation.no_family':
      return t('pages.bed.planting.hints.noFamily');
    case 'rotation.no_history':
      return t('pages.bed.planting.hints.noHistory');
    default:
      return finding.message;
  }
}

function neighbourText(
  hint: NeighbourHint,
  names: ReadonlyMap<string, string>,
  t: Translate,
): string {
  const name = names.get(hint.species_key) ?? hint.species_key;
  if (hint.code === 'companion.incompatible') {
    return t('pages.bed.planting.hints.incompatibleNeighbour', { name });
  }
  if (hint.code === 'companion.compatible') {
    return t('pages.bed.planting.hints.compatibleNeighbour', { name });
  }
  return hint.message;
}

export default function HintsPanel({
  species,
  speciesNames,
  bedSun = 'unknown',
  siteFlags = [],
  mix,
  overrideChecked,
  overrideReason,
  showReasonError,
  onOverrideChecked,
  onOverrideReason,
  severity,
  overridable = true,
}: HintsPanelProps) {
  const { t } = useTranslation();
  const mustGiveReason = overridable && needsOverrideReason(severity);
  const flagsLine = siteFlagsLine(t, siteFlags);
  const nameOf = (key: string) => speciesNames.get(key) ?? key;

  /** The rotation and neighbour hints of one species, or the reason there are none. */
  const rotationBlock = (key: string, name: string, state: HintState | undefined) => {
    if (!state || state.status === 'loading') {
      return (
        <Box key={key} sx={{ display: 'flex', alignItems: 'center', gap: 1 }} role="status">
          <CircularProgress size={16} />
          <Typography variant="body2">{t('pages.bed.planting.hints.checking', { name })}</Typography>
        </Box>
      );
    }
    if (state.status === 'error') {
      return (
        <Alert key={key} severity="info" data-testid={`planting-hint-${key}`}>
          {t('pages.bed.planting.hints.unavailable', { name, message: t(state.message) })}
        </Alert>
      );
    }
    const { data } = state;
    // Off for the rotation, the bed may still carry soil hazards (REQ-053 §11.3a Nr. 6): those come as findings.
    if (!data.rotation_applicable && data.rotation.length === 0) {
      return (
        <Alert key={key} severity="info" data-testid={`planting-hint-${key}`}>
          {t('pages.bed.planting.hints.notApplicable', { name })}
        </Alert>
      );
    }
    const lines = [
      ...data.rotation.map((finding) => ({
        id: `${finding.code}-${finding.hazard ?? finding.family_key ?? ''}`,
        severity: finding.severity,
        text: findingText(finding, t),
      })),
      ...data.neighbours.map((hint) => ({
        id: `${hint.code}-${hint.species_key}`,
        severity: hint.severity,
        text: neighbourText(hint, speciesNames, t),
      })),
    ];
    if (lines.length === 0) {
      return (
        <Alert key={key} severity="success" data-testid={`planting-hint-${key}`}>
          {t('pages.bed.planting.hints.allClear', { name })}
        </Alert>
      );
    }
    return (
      <Alert key={key} severity={ALERT_SEVERITY[data.severity]} data-testid={`planting-hint-${key}`}>
        <Typography variant="subtitle2" component="div">
          {t('pages.bed.planting.hints.forSpecies', {
            name,
            strength: t(SEVERITY_HEADING_KEY[data.severity]),
          })}
        </Typography>
        {!data.rotation_applicable ? (
          <Typography variant="body2" data-testid={`planting-hint-${key}-rotation-off`}>
            {t('pages.bed.planting.hints.notApplicableSoilStill')}
          </Typography>
        ) : null}
        <Box component="ul" sx={{ m: 0, pl: 2 }}>
          {lines.map((line) => (
            <li key={line.id}>
              {line.text}
              {line.severity !== data.severity ? (
                <Typography component="span" variant="caption" color="text.secondary">
                  {' '}
                  ({t(`enums.rotationSeverity.${line.severity}`)})
                </Typography>
              ) : null}
            </li>
          ))}
        </Box>
      </Alert>
    );
  };

  return (
    <Box
      component="section"
      aria-label={t('pages.bed.planting.hints.title')}
      data-testid="planting-hints"
      sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}
    >
      <Typography variant="subtitle1" component="h3">
        {t('pages.bed.planting.hints.title')}
      </Typography>
      <PlannerGlossary id="planting-hints" terms={HINT_TERMS} />
      {flagsLine ? (
        <Alert severity="info" data-testid="planting-site-flags">
          <Typography variant="subtitle2" component="div">
            {flagsLine}
          </Typography>
          {t('pages.bed.planting.hints.siteFlagsDetail')}
        </Alert>
      ) : null}
      {species.map(({ key, name, state, siteFit, axisHints, support }) => (
        <Fragment key={key}>
          {rotationBlock(key, name, state)}
          {siteFit ? (
            <SiteFitHint
              speciesKey={key}
              speciesName={name}
              bedSun={bedSun}
              lightRequirement={siteFit.lightRequirement}
              shadeTolerance={siteFit.shadeTolerance}
              result={siteFit.result}
            />
          ) : null}
          {axisHints && axisHints.length > 0 ? (
            <SiteAxisHints speciesKey={key} speciesName={name} hints={axisHints} />
          ) : null}
          {support ? <SupportHint speciesKey={key} speciesName={name} state={support} /> : null}
        </Fragment>
      ))}
      {mix.map((pair) => (
        <Alert
          key={`${pair.a}|${pair.b}`}
          severity={pair.kind === 'incompatible' ? 'warning' : 'success'}
          data-testid={`planting-mix-${pair.a}-${pair.b}`}
        >
          {pair.kind === 'incompatible'
            ? t('pages.bed.planting.hints.mixIncompatible', { a: nameOf(pair.a), b: nameOf(pair.b) })
            : t('pages.bed.planting.hints.mixCompatible', { a: nameOf(pair.a), b: nameOf(pair.b) })}
          {pair.reason ? ` ${pair.reason}` : ''}
        </Alert>
      ))}

      {mustGiveReason ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <FormControlLabel
            control={
              <Checkbox
                checked={overrideChecked}
                onChange={(event) => onOverrideChecked(event.target.checked)}
                slotProps={{ input: { 'data-testid': 'planting-override-check' } as object }}
              />
            }
            label={t('pages.bed.planting.hints.plantAnyway')}
            sx={{ minHeight: 48 }}
          />
          {overrideChecked ? (
            <TextField
              label={t('pages.bed.planting.hints.reason')}
              value={overrideReason}
              onChange={(event) => onOverrideReason(event.target.value)}
              required
              multiline
              minRows={2}
              error={showReasonError && overrideReason.trim() === ''}
              helperText={
                showReasonError && overrideReason.trim() === ''
                  ? t('pages.bed.planting.hints.reasonRequired')
                  : t('pages.bed.planting.hints.reasonHelp')
              }
              slotProps={{
                htmlInput: { maxLength: MAX_OVERRIDE_REASON, 'data-testid': 'planting-override-reason' },
              }}
            />
          ) : (
            <Typography variant="body2" color="text.secondary">
              {t('pages.bed.planting.hints.confirmToContinue')}
            </Typography>
          )}
        </Box>
      ) : null}
    </Box>
  );
}
