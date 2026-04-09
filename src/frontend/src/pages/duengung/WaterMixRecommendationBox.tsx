import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';
import Chip from '@mui/material/Chip';
import CircularProgress from '@mui/material/CircularProgress';
import Collapse from '@mui/material/Collapse';
import Stack from '@mui/material/Stack';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutlined';
import { useApiError } from '@/hooks/useApiError';
import * as planApi from '@/api/endpoints/nutrient-plans';
import type { WaterMixRecommendation } from '@/api/endpoints/nutrient-plans';

interface Props {
  planKey: string;
  sequenceOrder: number;
  siteKey: string | null;
  substrateType?: string;
  onApply?: (roPercent: number) => void;
}

export default function WaterMixRecommendationBox({
  planKey,
  sequenceOrder,
  siteKey,
  substrateType,
  onApply,
}: Props) {
  const { t } = useTranslation();
  const { handleError } = useApiError();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<WaterMixRecommendation | null>(null);
  const [expanded, setExpanded] = useState(false);

  const fetchRecommendation = useCallback(async () => {
    if (!siteKey) return;
    try {
      setLoading(true);
      setExpanded(true);
      const data = await planApi.fetchWaterMixRecommendation(
        planKey,
        sequenceOrder,
        siteKey,
        substrateType,
      );
      setResult(data);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }, [planKey, sequenceOrder, siteKey, substrateType, handleError]);

  if (!siteKey) return null;

  const rec = result?.recommendation;

  return (
    <Box sx={{ mt: 2, mb: 1 }}>
      <Button
        variant="outlined"
        startIcon={<WaterDropIcon />}
        onClick={fetchRecommendation}
        disabled={loading}
        size="small"
        data-testid="water-mix-recommendation-btn"
      >
        {loading ? (
          <CircularProgress size={16} sx={{ mr: 1 }} />
        ) : null}
        {t('pages.nutrientPlans.waterMix.fetchRecommendation')}
      </Button>

      <Collapse in={expanded && !!rec}>
        {rec && (
          <Alert
            severity="info"
            icon={<WaterDropIcon />}
            sx={{ mt: 1 }}
            data-testid="water-mix-recommendation-result"
          >
            <AlertTitle>
              {t('pages.nutrientPlans.waterMix.recommendedTitle', {
                percent: rec.recommended_ro_percent,
              })}
            </AlertTitle>

            <Typography variant="body2" sx={{ mb: 1 }}>
              {rec.reasoning}
            </Typography>

            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', mb: 1 }} useFlexGap>
              <Chip
                label={`EC ${rec.effective_ec_ms.toFixed(2)} mS/cm`}
                size="small"
                variant="outlined"
              />
              <Chip
                label={t('pages.nutrientPlans.waterMix.headroom', {
                  percent: (rec.ec_headroom * 100).toFixed(0),
                })}
                size="small"
                variant="outlined"
              />
              <Chip
                label={t('pages.nutrientPlans.waterMix.available', {
                  ec: rec.available_ec_for_nutrients.toFixed(2),
                })}
                size="small"
                variant="outlined"
              />
            </Stack>

            {rec.calmag_correction && rec.calmag_correction.needs_correction && (
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  <Tooltip title={t('pages.nutrientPlans.waterMix.calmagTooltip')}>
                    <InfoOutlinedIcon sx={{ fontSize: '1rem', verticalAlign: 'text-bottom', mr: 0.5 }} />
                  </Tooltip>
                  {t('pages.nutrientPlans.waterMix.calmagNeeded', {
                    ca: rec.calmag_correction.calcium_deficit_ppm.toFixed(1),
                    mg: rec.calmag_correction.magnesium_deficit_ppm.toFixed(1),
                  })}
                </Typography>
                {rec.calmag_correction.ca_mg_ratio_warning && (
                  <Typography variant="caption" color="warning.main">
                    {rec.calmag_correction.ca_mg_ratio_warning}
                  </Typography>
                )}
              </Box>
            )}

            {rec.alternatives.length > 0 && (
              <Box sx={{ mb: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 'medium', mb: 0.5 }}>
                  {t('pages.nutrientPlans.waterMix.alternatives')}
                </Typography>
                <Stack direction="row" spacing={0.5} useFlexGap sx={{ flexWrap: 'wrap' }}>
                  {rec.alternatives.map((alt) => (
                    <Tooltip key={alt.ro_percent} title={alt.trade_off}>
                      <Chip
                        label={`${alt.ro_percent}% RO`}
                        size="small"
                        clickable={!!onApply}
                        onClick={onApply ? () => onApply(alt.ro_percent) : undefined}
                        data-testid={`water-mix-alt-${alt.ro_percent}`}
                      />
                    </Tooltip>
                  ))}
                </Stack>
              </Box>
            )}

            {onApply && (
              <Button
                variant="contained"
                size="small"
                startIcon={<CheckCircleOutlineIcon />}
                onClick={() => onApply(rec.recommended_ro_percent)}
                data-testid="water-mix-apply-btn"
                sx={{ mt: 0.5 }}
              >
                {t('pages.nutrientPlans.waterMix.apply', {
                  percent: rec.recommended_ro_percent,
                })}
              </Button>
            )}
          </Alert>
        )}
      </Collapse>
    </Box>
  );
}
