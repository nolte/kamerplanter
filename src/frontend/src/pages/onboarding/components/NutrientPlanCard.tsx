import { useState, useCallback, useId } from 'react';
import { useTranslation } from 'react-i18next';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Box from '@mui/material/Box';
import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import Divider from '@mui/material/Divider';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ScienceIcon from '@mui/icons-material/Science';
import FavoriteToggle from '@/components/common/FavoriteToggle';
import type { NutrientPlanMatch, ExperienceLevel } from '@/api/types';

interface NutrientPlanCardProps {
  plan: NutrientPlanMatch;
  favorited: boolean;
  onToggleFavorite: () => void;
  experienceLevel: ExperienceLevel;
}

export default function NutrientPlanCard({
  plan,
  favorited,
  onToggleFavorite,
  experienceLevel,
}: NutrientPlanCardProps) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);
  const expandId = useId();

  const toggleExpand = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setExpanded((prev) => !prev);
  }, []);

  const showFertilizerSection = experienceLevel !== 'beginner' && plan.fertilizers.length > 0;

  return (
    <Card
      variant="outlined"
      sx={{
        // Border width + color change indicates selection; add left accent for extra non-color cue
        borderWidth: favorited ? 2 : 1,
        borderColor: favorited ? 'warning.main' : 'divider',
        borderLeftWidth: favorited ? 4 : 1,
        borderLeftColor: favorited ? 'warning.main' : 'divider',
        transition: 'border-color 0.2s ease, border-width 0.1s ease',
      }}
      // aria-selected communicates selection state to screen readers without nested buttons
      aria-selected={favorited}
      role="option"
    >
      {/* Header row — favorite toggle is separate from card click to avoid nested interactive elements */}
      <CardContent sx={{ pb: showFertilizerSection ? 0 : undefined }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1 }}>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography variant="subtitle1" fontWeight={600} sx={{ lineHeight: 1.3 }}>
              {plan.name}
            </Typography>
            {plan.description && (
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mt: 0.5, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}
              >
                {plan.description}
              </Typography>
            )}
          </Box>

          {/* FavoriteToggle is the only interactive element on the card header */}
          <FavoriteToggle
            favorited={favorited}
            onToggle={onToggleFavorite}
            size="small"
            testId={plan.plan_key}
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 1, mt: 1.5, flexWrap: 'wrap' }}>
          {plan.substrate_type && (
            <Chip
              label={t(`enums.substrateType.${plan.substrate_type}`, { defaultValue: plan.substrate_type })}
              size="small"
              variant="outlined"
            />
          )}
          <Chip
            icon={<ScienceIcon />}
            label={t('pages.onboarding.nutrientPlans.fertilizerCount', {
              count: plan.fertilizer_count,
            })}
            size="small"
            variant={favorited ? 'filled' : 'outlined'}
            color={favorited ? 'warning' : 'default'}
          />
        </Box>
      </CardContent>

      {/* Fertilizer details — intermediate/expert only */}
      {showFertilizerSection && (
        <>
          <Divider />
          <Box sx={{ px: 2, py: 0.5 }}>
            <Box
              sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
            >
              <Typography variant="caption" color="text.secondary">
                {t('pages.onboarding.nutrientPlans.fertilizers')}
              </Typography>
              <IconButton
                size="small"
                onClick={toggleExpand}
                aria-expanded={expanded}
                aria-controls={expandId}
                aria-label={
                  expanded
                    ? t('pages.onboarding.nutrientPlans.collapseFertilizers')
                    : t('pages.onboarding.nutrientPlans.expandFertilizers')
                }
                sx={{
                  transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.2s',
                  // Touch target
                  minWidth: 48,
                  minHeight: 48,
                }}
              >
                <ExpandMoreIcon fontSize="small" />
              </IconButton>
            </Box>

            <Collapse in={expanded} id={expandId}>
              <Box
                component="ul"
                sx={{ pl: 0, m: 0, listStyle: 'none', pb: 1 }}
                aria-label={t('pages.onboarding.nutrientPlans.fertilizers')}
              >
                {plan.fertilizers.map((f) => (
                  <Box
                    key={f.key}
                    component="li"
                    sx={{ display: 'flex', alignItems: 'center', gap: 0.5, py: 0.25 }}
                  >
                    <ScienceIcon
                      fontSize="inherit"
                      sx={{ color: 'text.disabled', fontSize: '0.75rem', flexShrink: 0 }}
                      aria-hidden="true"
                    />
                    <Typography variant="body2" color="text.secondary">
                      {f.product_name}
                      {f.brand ? (
                        <Typography component="span" variant="caption" color="text.disabled" sx={{ ml: 0.5 }}>
                          ({f.brand})
                        </Typography>
                      ) : null}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Collapse>
          </Box>
        </>
      )}
    </Card>
  );
}
