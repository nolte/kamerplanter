import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import Divider from '@mui/material/Divider';
import FormControlLabel from '@mui/material/FormControlLabel';
import Switch from '@mui/material/Switch';
import Typography from '@mui/material/Typography';
import EmojiNatureIcon from '@mui/icons-material/EmojiNature';
import SchoolIcon from '@mui/icons-material/School';
import ScienceIcon from '@mui/icons-material/Science';
import type { ExperienceLevel } from '@/api/types';

const EXPERIENCE_LEVELS: {
  level: ExperienceLevel;
  icon: React.ReactNode;
}[] = [
  { level: 'beginner', icon: <EmojiNatureIcon sx={{ fontSize: '2.5rem' }} /> },
  { level: 'intermediate', icon: <SchoolIcon sx={{ fontSize: '2.5rem' }} /> },
  { level: 'expert', icon: <ScienceIcon sx={{ fontSize: '2.5rem' }} /> },
];

interface ExperienceLevelStepProps {
  experienceLevel: ExperienceLevel;
  onSelect: (level: ExperienceLevel) => void;
  smartHomeEnabled: boolean;
  onSmartHomeEnabledChange: (enabled: boolean) => void;
}

export default function ExperienceLevelStep({
  experienceLevel,
  onSelect,
  smartHomeEnabled,
  onSmartHomeEnabledChange,
}: ExperienceLevelStepProps) {
  const { t } = useTranslation();

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
              onClick={() => onSelect(level)}
              data-testid={`experience-${level}`}
              sx={{ p: 2, textAlign: 'center' }}
            >
              <Box sx={{ color: 'primary.main', mb: 1 }}>{icon}</Box>
              <Typography
                variant="subtitle1"
                fontWeight={experienceLevel === level ? 700 : 400}
              >
                {t(`enums.experienceLevel.${level}`)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {t(`pages.auth.experienceLevel.${level}Description`)}
              </Typography>
            </CardActionArea>
          </Card>
        ))}
      </Box>

      {experienceLevel !== 'beginner' && (
        <Box sx={{ mt: 4 }}>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {t('pages.onboarding.smartHome.title')}
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={smartHomeEnabled}
                onChange={(e) => onSmartHomeEnabledChange(e.target.checked)}
                data-testid="smart-home-toggle"
              />
            }
            label={t('pages.onboarding.smartHome.toggle')}
          />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, ml: 6 }}>
            {smartHomeEnabled
              ? t('pages.onboarding.smartHome.enabledHint')
              : t('pages.onboarding.smartHome.disabledHint')
            }
          </Typography>
        </Box>
      )}
    </Box>
  );
}
