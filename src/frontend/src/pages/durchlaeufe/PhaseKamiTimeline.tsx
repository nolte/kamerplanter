import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import { alpha, useTheme } from '@mui/material/styles';
import type { PhaseTimelineEntry } from '@/api/types';

// ── Kami phase illustrations ────────────────────────────────────────
import kamiGermination from '@/assets/brand/illustrations/phases/timeline-kami-phase-germination.svg';
import kamiSeedling from '@/assets/brand/illustrations/phases/timeline-kami-phase-seedling.svg';
import kamiVegetative from '@/assets/brand/illustrations/phases/timeline-kami-phase-vegetative.svg';
import kamiFlowering from '@/assets/brand/illustrations/phases/timeline-kami-phase-flowering.svg';
import kamiRipening from '@/assets/brand/illustrations/phases/timeline-kami-phase-ripening.svg';
import kamiHarvest from '@/assets/brand/illustrations/phases/timeline-kami-phase-harvest.svg';
import kamiDormancy from '@/assets/brand/illustrations/phases/timeline-kami-phase-dormancy.svg';
import kamiJuvenile from '@/assets/brand/illustrations/phases/timeline-kami-phase-juvenile.svg';
import kamiClimbing from '@/assets/brand/illustrations/phases/timeline-kami-phase-climbing.svg';
import kamiMature from '@/assets/brand/illustrations/phases/timeline-kami-phase-mature.svg';
import kamiSenescence from '@/assets/brand/illustrations/phases/timeline-kami-phase-senescence.svg';

const KAMI_PHASE_IMAGES: Record<string, string> = {
  germination: kamiGermination,
  seedling: kamiSeedling,
  vegetative: kamiVegetative,
  flowering: kamiFlowering,
  ripening: kamiRipening,
  fruiting: kamiRipening,
  harvest: kamiHarvest,
  dormancy: kamiDormancy,
  juvenile: kamiJuvenile,
  climbing: kamiClimbing,
  mature: kamiMature,
  senescence: kamiSenescence,
};

const PHASE_COLORS: Record<string, string> = {
  germination: '#a5d6a7',
  seedling: '#81c784',
  vegetative: '#4caf50',
  flowering: '#f48fb1',
  ripening: '#ffcc80',
  fruiting: '#ffcc80',
  harvest: '#ffb74d',
  drying: '#bcaaa4',
  curing: '#a1887f',
  flushing: '#90caf9',
  juvenile: '#c5e1a5',
  climbing: '#aed581',
  mature: '#66bb6a',
  dormancy: '#b0bec5',
  senescence: '#ef9a9a',
  establishment: '#a5d6a7',
  pup_establishment: '#a5d6a7',
  pre_bloom: '#ce93d8',
  recovery: '#80cbc4',
  sprouting: '#c5e1a5',
  hardening_off: '#b2dfdb',
  budding: '#ce93d8',
  corm_ripening: '#ffcc80',
  tuber_formation: '#ffcc80',
};

/** Normalize scientific name to i18n slug: "Monstera deliciosa" → "monstera_deliciosa" */
function toSpeciesSlug(scientificName: string): string {
  return scientificName.toLowerCase().replace(/[.×]/g, '').replace(/\s+/g, '_');
}

interface PhaseKamiTimelineProps {
  phases: PhaseTimelineEntry[];
  /** Scientific name of the species, used for species-specific i18n tooltips */
  speciesName?: string | null;
}

export default function PhaseKamiTimeline({ phases, speciesName }: PhaseKamiTimelineProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const speciesSlug = speciesName ? toSpeciesSlug(speciesName) : null;

  if (phases.length === 0) return null;

  return (
    <Box
      role="list"
      aria-label={t('pages.plantingRuns.phaseTimeline')}
      sx={{
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'space-between',
        width: '100%',
        pb: 1,
        pt: 1,
      }}
    >
      {phases.map((p, idx) => {
        const phaseKey = p.phase_name.toLowerCase();
        const color = PHASE_COLORS[phaseKey] ?? '#e0e0e0';
        const kamiImg = KAMI_PHASE_IMAGES[phaseKey];
        const isCurrent = p.status === 'current';
        const isCompleted = p.status === 'completed';
        const isProjected = p.status === 'projected';
        const durationDays =
          p.actual_duration_days ??
          (p.projected_start && p.projected_end
            ? Math.round(
                (new Date(p.projected_end).getTime() -
                  new Date(p.projected_start).getTime()) /
                  86400000,
              )
            : p.typical_duration_days);
        const phaseLabel = t(`enums.phaseName.${p.phase_name}`, {
          defaultValue: p.display_name || p.phase_name,
        });
        const phaseDescription =
          (speciesSlug
            ? t(`enums.phaseDescriptions.${speciesSlug}.${phaseKey}`, '')
            : '') || t(`enums.phaseDescription.${phaseKey}`, '');
        return (
          <Box
            key={p.phase_key}
            role="listitem"
            sx={{ display: 'flex', alignItems: 'flex-end', flex: 1, minWidth: 0 }}
          >
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                flex: '0 0 auto',
                opacity: isProjected ? 0.5 : 1,
                transition: 'opacity 0.2s',
              }}
            >
              {/* Kami illustration — decorative when a label is shown below */}
              {kamiImg && (
                <Box
                  component="img"
                  src={kamiImg}
                  alt=""
                  aria-hidden="true"
                  sx={{
                    width: { xs: 56, sm: 72, md: 88 },
                    height: { xs: 56, sm: 72, md: 88 },
                    objectFit: 'contain',
                    mb: 0.75,
                    filter: isProjected
                      ? 'grayscale(0.6)'
                      : isCurrent
                        ? 'drop-shadow(0 0 8px rgba(76, 175, 80, 0.6))'
                        : 'none',
                  }}
                />
              )}
              {/* Timeline dot — purely decorative */}
              <Box
                aria-hidden="true"
                sx={{
                  width: 14,
                  height: 14,
                  borderRadius: '50%',
                  bgcolor: isProjected ? 'action.disabled' : color,
                  border: isCurrent
                    ? `2px solid ${theme.palette.primary.main}`
                    : `2px solid ${color}`,
                  zIndex: 1,
                  boxShadow: isCurrent ? `0 0 0 4px ${alpha(color, 0.3)}` : 'none',
                }}
              />
              {/* Phase name with species-specific or generic tooltip */}
              <Tooltip
                title={phaseDescription}
                arrow
                placement="bottom"
                slotProps={{
                  tooltip: { sx: { maxWidth: 320, fontSize: '0.75rem', lineHeight: 1.5 } },
                }}
              >
                <Typography
                  variant="caption"
                  tabIndex={phaseDescription ? 0 : undefined}
                  sx={{
                    fontWeight: isCurrent ? 700 : 500,
                    color: isProjected ? 'text.disabled' : 'text.primary',
                    fontSize: { xs: '0.65rem', sm: '0.75rem' },
                    textAlign: 'center',
                    mt: 0.5,
                    lineHeight: 1.2,
                    cursor: phaseDescription ? 'help' : 'default',
                    '&:hover': phaseDescription
                      ? { textDecoration: 'underline dotted' }
                      : undefined,
                  }}
                >
                  {phaseLabel}
                </Typography>
              </Tooltip>
              {/* Duration */}
              {durationDays != null && (
                <Typography
                  variant="caption"
                  sx={{
                    color: 'text.secondary',
                    fontSize: { xs: '0.6rem', sm: '0.65rem' },
                    fontStyle: isProjected ? 'italic' : 'normal',
                  }}
                >
                  {`${durationDays}\u00A0${t('common.days')}`}
                </Typography>
              )}
            </Box>
            {/* Connector line — stretches to fill remaining space */}
            {idx < phases.length - 1 && (
              <Box
                aria-hidden="true"
                sx={{
                  flex: 1,
                  height: 2,
                  bgcolor: isCompleted ? color : 'action.disabled',
                  mb: '37px',
                  mx: 0.5,
                  minWidth: 8,
                }}
              />
            )}
          </Box>
        );
      })}
    </Box>
  );
}
