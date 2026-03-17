import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Slider from '@mui/material/Slider';
import type { StarterKit } from '@/api/types';

interface PlantCountStepProps {
  plantCount: number;
  onPlantCountChange: (count: number) => void;
  selectedKit: StarterKit | null;
}

export default function PlantCountStep({
  plantCount,
  onPlantCountChange,
  selectedKit,
}: PlantCountStepProps) {
  const { t, i18n } = useTranslation();

  const getKitName = useCallback(
    (kit: StarterKit) => {
      return kit.name_i18n[i18n.language] ?? kit.name_i18n.de ?? kit.kit_id;
    },
    [i18n.language],
  );

  return (
    <Box data-testid="onboarding-step-plants" sx={{ maxWidth: 480 }}>
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
          onChange={(_, val) => onPlantCountChange(val as number)}
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
}
