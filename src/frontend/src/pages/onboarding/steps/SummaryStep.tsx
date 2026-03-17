import { useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import StarIcon from '@mui/icons-material/Star';
import ScienceIcon from '@mui/icons-material/Science';
import YardIcon from '@mui/icons-material/Yard';
import type { ExperienceLevel, PlantConfig, Site, SiteType, Species, StarterKit } from '@/api/types';

interface SummaryStepProps {
  experienceLevel: ExperienceLevel;
  selectedKit: StarterKit | null;
  siteName: string;
  siteType: SiteType;
  selectedSite: Site | null;
  allSpecies: Species[];
  plantConfigs: PlantConfig[];
  plantCount: number;
  favoriteSpeciesCount?: number;
  favoriteNutrientPlanCount?: number;
}

interface SummaryRowProps {
  label: string;
  children: React.ReactNode;
}

function SummaryRow({ label, children }: SummaryRowProps) {
  return (
    <>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Box>{children}</Box>
    </>
  );
}

export default function SummaryStep({
  experienceLevel,
  selectedKit,
  siteName,
  siteType,
  selectedSite,
  allSpecies,
  plantConfigs,
  plantCount,
  favoriteSpeciesCount = 0,
  favoriteNutrientPlanCount = 0,
}: SummaryStepProps) {
  const { t, i18n } = useTranslation();

  const speciesMap = useMemo(() => {
    const map = new Map<string, Species>();
    for (const sp of allSpecies) {
      map.set(sp.key, sp);
    }
    return map;
  }, [allSpecies]);

  const getSpeciesName = useCallback(
    (key: string): string => {
      const sp = speciesMap.get(key);
      if (!sp) return key;
      return sp.common_names?.[0] ?? sp.scientific_name;
    },
    [speciesMap],
  );

  const getKitName = useCallback(
    (kit: StarterKit) => {
      return kit.name_i18n[i18n.language] ?? kit.name_i18n.de ?? kit.kit_id;
    },
    [i18n.language],
  );

  const hasFavorites = favoriteSpeciesCount > 0 || favoriteNutrientPlanCount > 0;
  const activeConfigs = plantConfigs.filter((c) => c.count > 0);

  return (
    <Box data-testid="onboarding-step-complete">
      {/* Hero area */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <CheckCircleIcon
          sx={{ fontSize: '3.5rem', color: 'success.main', mb: 1 }}
          aria-hidden="true"
        />
        <Typography variant="h5" gutterBottom>
          {t('pages.onboarding.reviewTitle')}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t('pages.onboarding.reviewSubtitle')}
        </Typography>
      </Box>

      {/* Summary card */}
      <Card variant="outlined" sx={{ maxWidth: 480, mx: 'auto' }}>
        <CardContent>
          {/* Setup section */}
          <Typography
            variant="overline"
            color="text.secondary"
            sx={{ display: 'block', mb: 1.5, letterSpacing: '0.08em' }}
          >
            {t('pages.onboarding.summary.sectionSetup')}
          </Typography>

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: 'auto 1fr',
              rowGap: 1.5,
              columnGap: 2,
              alignItems: 'start',
            }}
          >
            <SummaryRow label={t('pages.onboarding.experienceLevel')}>
              <Typography variant="body2" fontWeight={600}>
                {t(`enums.experienceLevel.${experienceLevel}`)}
              </Typography>
            </SummaryRow>

            {selectedKit && (
              <SummaryRow label={t('pages.onboarding.selectKit')}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                  <Typography variant="body2" fontWeight={600}>
                    {getKitName(selectedKit)}
                  </Typography>
                  <Chip
                    label={t(`enums.starterKitDifficulty.${selectedKit.difficulty}`)}
                    size="small"
                    variant="outlined"
                  />
                </Box>
              </SummaryRow>
            )}

            {selectedSite ? (
              <SummaryRow label={t('pages.onboarding.siteName')}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                  <Typography variant="body2" fontWeight={600}>
                    {selectedSite.name}
                  </Typography>
                  <Chip
                    label={t(`enums.siteType.${selectedSite.type}`)}
                    size="small"
                    variant="outlined"
                  />
                </Box>
              </SummaryRow>
            ) : (
              <>
                <SummaryRow label={t('pages.onboarding.siteType')}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                    <Typography variant="body2" fontWeight={600}>
                      {t(`enums.siteType.${siteType}`)}
                    </Typography>
                    <Chip
                      label={t('pages.onboarding.site.newBadge')}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  </Box>
                </SummaryRow>

                {siteName && (
                  <SummaryRow label={t('pages.onboarding.siteName')}>
                    <Typography variant="body2" fontWeight={600}>
                      {siteName}
                    </Typography>
                  </SummaryRow>
                )}
              </>
            )}

            <SummaryRow label={t('pages.onboarding.plantCount')}>
              <Typography variant="body2" fontWeight={600}>
                {plantCount}
              </Typography>
            </SummaryRow>
          </Box>

          {/* Plant configs section — only when configs exist */}
          {activeConfigs.length > 0 && (
            <>
              <Divider sx={{ my: 2 }} />

              <Typography
                variant="overline"
                color="text.secondary"
                sx={{ display: 'block', mb: 1.5, letterSpacing: '0.08em' }}
              >
                {t('pages.onboarding.summary.sectionPlants')}
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {activeConfigs.map((c) => (
                  <Box
                    key={c.species_key}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                    }}
                  >
                    <YardIcon fontSize="small" sx={{ color: 'success.main' }} aria-hidden="true" />
                    <Typography variant="body2" fontWeight={600} sx={{ flex: 1, minWidth: 0 }} noWrap>
                      {getSpeciesName(c.species_key)}
                    </Typography>
                    <Chip
                      label={`${c.count}x`}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                    <Chip
                      label={t(`enums.phaseName.${c.initial_phase}`)}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                ))}
              </Box>
            </>
          )}

          {/* Favorites section — only when at least one favorite was set */}
          {hasFavorites && (
            <>
              <Divider sx={{ my: 2 }} />

              <Typography
                variant="overline"
                color="text.secondary"
                sx={{ display: 'block', mb: 1.5, letterSpacing: '0.08em' }}
              >
                {t('pages.onboarding.summary.sectionFavorites')}
              </Typography>

              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: 'auto 1fr',
                  rowGap: 1.5,
                  columnGap: 2,
                  alignItems: 'center',
                }}
              >
                {favoriteSpeciesCount > 0 && (
                  <SummaryRow label={t('pages.onboarding.favoritesCount')}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <StarIcon fontSize="small" sx={{ color: 'warning.main' }} aria-hidden="true" />
                      <Typography variant="body2" fontWeight={600}>
                        {t('pages.onboarding.summary.speciesCount', { count: favoriteSpeciesCount })}
                      </Typography>
                    </Box>
                  </SummaryRow>
                )}

                {favoriteNutrientPlanCount > 0 && (
                  <SummaryRow label={t('entities.nutrientPlans')}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <ScienceIcon fontSize="small" sx={{ color: 'warning.main' }} aria-hidden="true" />
                      <Typography variant="body2" fontWeight={600}>
                        {t('pages.onboarding.summary.planCount', { count: favoriteNutrientPlanCount })}
                      </Typography>
                    </Box>
                  </SummaryRow>
                )}
              </Box>
            </>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
