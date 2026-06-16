import { useState, type ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import i18n from 'i18next';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardMedia from '@mui/material/CardMedia';
import Chip from '@mui/material/Chip';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';
import { alpha } from '@mui/material/styles';
import { Link as RouterLink } from 'react-router-dom';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import EditIcon from '@mui/icons-material/Edit';
import OpacityIcon from '@mui/icons-material/Opacity';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import SpaIcon from '@mui/icons-material/Spa';
import AcUnitIcon from '@mui/icons-material/AcUnit';
import TipsAndUpdatesIcon from '@mui/icons-material/TipsAndUpdates';
import type { Species } from '@/api/types';
import ReferenceImageGallery from './ReferenceImageGallery';

interface Props {
  species: Species;
  phaseSequenceKey: string | null;
  onEdit: () => void;
}

interface HeroImageProps {
  url: string;
  attribution: string | null;
  license: string | null;
  alt: string;
}

/**
 * Detail-page hero image (REQ-029-A). Renders the external representative image
 * with a legally-required attribution/license caption. A failed external load
 * removes the whole hero rather than showing a broken-image box.
 */
function HeroImage({ url, attribution, license, alt }: HeroImageProps) {
  const [failed, setFailed] = useState(false);
  if (failed) return null;

  const captionParts: string[] = [];
  if (attribution) captionParts.push(`© ${attribution}`);
  if (license) captionParts.push(license);
  const caption = captionParts.join(' · ');

  return (
    <Card
      component="figure"
      variant="outlined"
      data-testid="species-hero-image"
      sx={{ m: 0 }}
    >
      <CardMedia
        component="img"
        image={url}
        alt={alt}
        loading="lazy"
        referrerPolicy="no-referrer"
        onError={() => setFailed(true)}
        sx={{
          // Taller on large screens where side-by-side context makes a bigger
          // hero worthwhile; compact on mobile where vertical space is scarce.
          maxHeight: { xs: 220, sm: 280, md: 360 },
          objectFit: 'cover',
          width: '100%',
          display: 'block',
        }}
      />
      {caption && (
        <CardContent
          component="figcaption"
          sx={{ py: 1, '&:last-child': { pb: 1 } }}
        >
          <Typography
            variant="caption"
            color="text.secondary"
            data-testid="species-hero-attribution"
          >
            {caption}
          </Typography>
        </CardContent>
      )}
    </Card>
  );
}

/** Human-readable month range(s) for a config's months, e.g. "März–April, Sep". */
function monthsLabel(months: number[], t: (k: string) => string): string {
  if (months.length === 0) return '';
  const sorted = [...months].sort((a, b) => a - b);
  const ranges: [number, number][] = [];
  let start = sorted[0];
  let end = sorted[0];
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i] === end + 1) {
      end = sorted[i];
    } else {
      ranges.push([start, end]);
      start = sorted[i];
      end = sorted[i];
    }
  }
  ranges.push([start, end]);
  return ranges
    .map(([s, e]) =>
      s === e
        ? t(`pages.species.months.${s}`)
        : `${t(`pages.species.months.${s}`)}–${t(`pages.species.months.${e}`)}`,
    )
    .join(', ');
}

/**
 * Read-optimised species overview (U-1/U-2). Renders the previously invisible
 * real species fields (allows_harvest, frost_sensitivity, growth_habit,
 * plant_category, harvest_pattern, harvested_part) as a profile chip strip,
 * plus description, read-only propagation, the watering guide (QW-4) and a
 * family link. The Edit tab remains the single source of edit; nothing here is
 * an input. No invented data — every chip is conditional on a real field value.
 */
export default function SpeciesOverview({ species, phaseSequenceKey, onEdit }: Props) {
  const { t } = useTranslation();
  const propagationConfigs = species.propagation_configs ?? [];
  const watering = species.watering_guide;

  // Steckbrief chips — only render a chip when the underlying field is set.
  const chips: { key: string; icon: ReactElement; label: string }[] = [];

  // allows_harvest → edible / ornamental (always known: boolean).
  chips.push(
    species.allows_harvest
      ? {
          key: 'edible',
          icon: <RestaurantIcon fontSize="small" />,
          label: t('pages.species.edible'),
        }
      : {
          key: 'ornamental',
          icon: <SpaIcon fontSize="small" />,
          label: t('pages.species.ornamental'),
        },
  );

  if (species.frost_sensitivity) {
    chips.push({
      key: 'frost',
      icon: <AcUnitIcon fontSize="small" />,
      label: t(`enums.frostTolerance.${species.frost_sensitivity}`),
    });
  }
  if (species.growth_habit) {
    chips.push({
      key: 'growth',
      icon: <SpaIcon fontSize="small" />,
      label: t(`enums.growthHabit.${species.growth_habit}`),
    });
  }
  // plant_category is a free string on Species; only show it when a matching
  // enum label exists, so we never surface a raw, untranslated key.
  if (species.plant_category && i18n.exists(`enums.plantCategory.${species.plant_category}`)) {
    chips.push({
      key: 'category',
      icon: <SpaIcon fontSize="small" />,
      label: t(`enums.plantCategory.${species.plant_category}`),
    });
  }
  if (species.harvest_pattern) {
    chips.push({
      key: 'harvest_pattern',
      icon: <RestaurantIcon fontSize="small" />,
      label: t(`enums.harvestPattern.${species.harvest_pattern}`),
    });
  }
  if (species.harvested_part) {
    chips.push({
      key: 'harvested_part',
      icon: <RestaurantIcon fontSize="small" />,
      label: t(`enums.harvestedPart.${species.harvested_part}`),
    });
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Representative image hero (REQ-029-A) — only when a real URL is set. */}
      {species.representative_image_url && (
        <HeroImage
          url={species.representative_image_url}
          attribution={species.representative_image_attribution}
          license={species.representative_image_license}
          alt={species.scientific_name}
        />
      )}

      {/* Primary edit affordance (U-2). */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'center' }}>
        <Button
          variant="contained"
          startIcon={<EditIcon />}
          onClick={onEdit}
          data-testid="overview-edit-button"
        >
          {t('pages.species.overviewEdit')}
        </Button>
        {phaseSequenceKey && (
          <Chip
            component={RouterLink}
            to={`/phasen/ablaeufe/${phaseSequenceKey}`}
            icon={<AccountTreeIcon />}
            label={t('pages.phaseSequences.viewPhaseSequence')}
            clickable
            variant="outlined"
            size="small"
          />
        )}
      </Box>

      {/* Steckbrief chip strip. */}
      <Box>
        <Typography component="h2" variant="h6" sx={{ mb: 1 }} data-testid="overview-chips-heading">
          {t('pages.species.overviewChipsLabel')}
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }} data-testid="overview-chips">
          {chips.map((c) => (
            <Chip
              key={c.key}
              icon={c.icon}
              label={c.label}
              variant="outlined"
              size="small"
              data-testid={`overview-chip-${c.key}`}
            />
          ))}
        </Box>
      </Box>

      {/* Description. */}
      {species.description?.trim() && (
        <Box>
          <Typography component="h2" variant="h6" sx={{ mb: 1 }}>
            {t('pages.species.description')}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'pre-line' }}>
            {species.description}
          </Typography>
        </Box>
      )}

      {/* Family link. */}
      {species.family_key && (
        <Box>
          <Typography component="h2" variant="h6" sx={{ mb: 1 }}>
            {t('pages.species.family')}
          </Typography>
          <Link
            component={RouterLink}
            to={`/stammdaten/botanical-families/${species.family_key}`}
            variant="body2"
            data-testid="overview-family-link"
          >
            {species.family_name ?? t('pages.species.viewFamily')}
          </Link>
        </Box>
      )}

      {/* Propagation (read-only — edited on the Edit tab, single source of edit). */}
      {propagationConfigs.length > 0 && (
        <Box>
          <Typography component="h2" variant="h6" sx={{ mb: 1 }}>
            {t('pages.species.propagationOverviewLabel')}
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            {propagationConfigs.map((cfg, idx) => (
              <Box
                key={`${cfg.method}-${idx}`}
                data-testid={`overview-propagation-${idx}`}
                sx={{
                  pb: idx < propagationConfigs.length - 1 ? 1.5 : 0,
                  borderBottom: idx < propagationConfigs.length - 1 ? '1px solid' : 'none',
                  borderColor: 'divider',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 0.75 }}>
                  <Chip
                    size="small"
                    variant="outlined"
                    color={cfg.method === 'seed' ? 'success' : 'default'}
                    label={t(`enums.propagationMethod.${cfg.method}`)}
                  />
                  {cfg.wood_stage && (
                    <Chip
                      size="small"
                      variant="outlined"
                      label={t(`enums.woodStage.${cfg.wood_stage}`)}
                    />
                  )}
                  {(cfg.months?.length ?? 0) > 0 && (
                    <Typography variant="body2" color="text.secondary">
                      {t('pages.species.propagationMonthsValue', {
                        range: monthsLabel(cfg.months, t),
                      })}
                    </Typography>
                  )}
                </Box>
                {cfg.notes?.trim() && (
                  <Box
                    role="note"
                    aria-label={t('pages.species.propagationNotesLabel')}
                    sx={{
                      mt: 1,
                      display: 'flex',
                      gap: 1,
                      alignItems: 'flex-start',
                      px: 1.5,
                      py: 1,
                      borderRadius: 1,
                      border: '1px solid',
                      borderColor: 'divider',
                      bgcolor: (th) => alpha(th.palette.action.selected, 0.04),
                    }}
                  >
                    <TipsAndUpdatesIcon
                      aria-hidden="true"
                      sx={{ fontSize: 18, color: 'text.secondary', mt: 0.25, flexShrink: 0 }}
                    />
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ whiteSpace: 'pre-line' }}
                    >
                      {cfg.notes}
                    </Typography>
                  </Box>
                )}
              </Box>
            ))}
          </Box>
        </Box>
      )}

      {/* Watering guide (read-only — QW-4). Empty case suppressed (no grey line). */}
      {watering && (
        <Card variant="outlined">
          <CardContent>
            <Typography
              component="h2"
              variant="h6"
              sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}
            >
              <OpacityIcon fontSize="small" />
              {t('pages.species.sectionWateringGuide')}
            </Typography>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
                gap: 1,
              }}
            >
              <Typography variant="body2">
                <strong>{t('pages.species.wateringInterval')}:</strong>{' '}
                {t('pages.species.wateringIntervalDays', { count: watering.interval_days })}
              </Typography>
              <Typography variant="body2">
                <strong>{t('pages.species.wateringVolume')}:</strong>{' '}
                {t('pages.species.wateringVolumeMl', {
                  min: watering.volume_ml_min,
                  max: watering.volume_ml_max,
                })}
              </Typography>
              <Typography variant="body2">
                <strong>{t('pages.species.wateringMethod')}:</strong>{' '}
                {t(`enums.wateringMethod.${watering.watering_method}`)}
              </Typography>
              {watering.water_quality_hint && (
                <Typography variant="body2">
                  <strong>{t('pages.species.waterQualityHint')}:</strong>{' '}
                  {watering.water_quality_hint}
                </Typography>
              )}
            </Box>
            {watering.practical_tip && (
              <Alert severity="info" sx={{ mt: 1 }}>
                {watering.practical_tip}
              </Alert>
            )}
            {watering.seasonal_adjustments.length > 0 && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                  <strong>{t('pages.species.seasonalAdjustments')}:</strong>
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {watering.seasonal_adjustments.map((adj) => (
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
      )}

      {/* Reference-image gallery (REQ-029-A) — lazily loaded, empty = discreet hint. */}
      <ReferenceImageGallery speciesKey={species.key} scientificName={species.scientific_name} />
    </Box>
  );
}
