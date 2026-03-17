import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import PlaceIcon from '@mui/icons-material/Place';
import YardIcon from '@mui/icons-material/Yard';
import type { StarterKit } from '@/api/types';

interface StarterKitStepProps {
  kits: StarterKit[];
  selectedKitId: string | null;
  onSelect: (kitId: string | null) => void;
}

export default function StarterKitStep({
  kits,
  selectedKitId,
  onSelect,
}: StarterKitStepProps) {
  const { t, i18n } = useTranslation();

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

  return (
    <Box data-testid="onboarding-step-kit">
      <Typography variant="h6" gutterBottom>
        {t('pages.onboarding.selectKit')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t('pages.onboarding.selectKitHint')}
      </Typography>
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' },
          gap: 2,
        }}
      >
        {kits.map((kit) => {
          const isSelected = selectedKitId === kit.kit_id;

          return (
            <Card
              key={kit.kit_id}
              variant={isSelected ? 'elevation' : 'outlined'}
              sx={{
                border: isSelected ? 2 : 1,
                borderColor: isSelected ? 'primary.main' : 'divider',
                transition: 'border-color 0.15s, box-shadow 0.15s',
              }}
            >
              <CardActionArea
                onClick={() =>
                  onSelect(isSelected ? null : kit.kit_id)
                }
                data-testid={`kit-${kit.kit_id}`}
                sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'stretch', justifyContent: 'flex-start' }}
              >
                <Typography variant="subtitle1" fontWeight={isSelected ? 700 : 500} gutterBottom>
                  {kit.icon} {getKitName(kit)}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5, flex: 1 }}>
                  {getKitDescription(kit)}
                </Typography>

                {/* Meta info: site type, plant count, difficulty */}
                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', alignItems: 'center' }}>
                  <Chip
                    icon={<PlaceIcon />}
                    label={t(`enums.siteType.${kit.site_type}`)}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    icon={<YardIcon />}
                    label={t('pages.onboarding.kitPlantCount', { count: kit.plant_count_suggestion })}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={t(`enums.starterKitDifficulty.${kit.difficulty}`)}
                    size="small"
                    variant="outlined"
                    color={
                      kit.difficulty === 'beginner'
                        ? 'success'
                        : kit.difficulty === 'intermediate'
                          ? 'warning'
                          : 'error'
                    }
                  />
                  {kit.toxicity_warning && (
                    <Chip
                      label={t('pages.onboarding.kitToxicityWarning')}
                      size="small"
                      color="warning"
                    />
                  )}
                </Box>
              </CardActionArea>
            </Card>
          );
        })}
      </Box>

      {/* Optional: skip hint */}
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
        {t('pages.onboarding.selectKitOptional')}
      </Typography>
    </Box>
  );
}
