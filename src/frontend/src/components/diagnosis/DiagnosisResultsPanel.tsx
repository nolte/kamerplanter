import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Link as RouterLink } from 'react-router-dom';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Stack from '@mui/material/Stack';
import Chip from '@mui/material/Chip';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import AIResponse from '@/components/ai/AIResponse';
import type { AiConfidence, DiagnosisResult } from '@/api/types';

export interface DiagnosisResultsPanelProps {
  result: DiagnosisResult;
}

const CONFIDENCE_COLOR: Record<AiConfidence, 'success' | 'info' | 'warning' | 'default'> = {
  high: 'success',
  medium: 'info',
  low: 'warning',
  none: 'default',
};

/**
 * REQ-036 §5 — renders the top-3 diagnoses inside the mandatory `<AIResponse>`
 * shell (KI-labeling, confidence badge, sources, disclaimer, 3-experience-level
 * source toggle) and deep-links each candidate to its IPM pest / treatment
 * detail page.
 */
export default function DiagnosisResultsPanel({ result }: DiagnosisResultsPanelProps) {
  const { t } = useTranslation();

  const candidates = useMemo(() => result.candidates, [result.candidates]);

  return (
    <AIResponse
      sources={result.sources}
      modelName={result.model_name}
      providerType={result.provider_type}
      usesTenantData={result.uses_tenant_data}
      usesCloudProvider={result.uses_cloud_provider}
      confidence={result.confidence}
      data-testid="diagnosis-results"
    >
      <Stack spacing={2}>
        <Typography variant="body2" color="text.secondary">
          {t('diagnose.results.intro')}
        </Typography>

        {candidates.map((candidate) => (
          <Card key={candidate.rank} variant="outlined" data-testid={`diagnosis-candidate-${candidate.rank}`}>
            <CardContent>
              <Stack direction="row" spacing={1} sx={{ mb: 1, flexWrap: 'wrap', alignItems: 'center' }}>
                <Chip size="small" color="primary" label={t('diagnose.results.rank', { rank: candidate.rank })} />
                <Typography variant="subtitle1" component="h3" sx={{ fontWeight: 600 }}>
                  {candidate.name}
                </Typography>
                <Chip
                  size="small"
                  variant="outlined"
                  color={CONFIDENCE_COLOR[candidate.confidence_level]}
                  label={t('diagnose.results.confidence', {
                    percent: Math.round(candidate.confidence * 100),
                  })}
                  data-testid={`diagnosis-confidence-${candidate.rank}`}
                />
              </Stack>

              {candidate.scientific_name ? (
                <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic', display: 'block' }}>
                  {candidate.scientific_name}
                </Typography>
              ) : null}

              <Typography variant="body2" sx={{ mt: 1 }}>
                {candidate.explanation}
              </Typography>

              {candidate.recommended_actions.length > 0 ? (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="subtitle2">{t('diagnose.results.actions')}</Typography>
                  <List dense disablePadding>
                    {candidate.recommended_actions.map((action) => (
                      <ListItem key={action} disableGutters sx={{ py: 0 }}>
                        <ListItemText primary={action} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              ) : null}

              {candidate.matched_pest_detail_url ? (
                <Link
                  component={RouterLink}
                  to={candidate.matched_pest_detail_url}
                  variant="body2"
                  sx={{ display: 'inline-block', mt: 1 }}
                  data-testid={`diagnosis-pest-link-${candidate.rank}`}
                >
                  {t('diagnose.results.pestLink')}
                </Link>
              ) : null}

              {candidate.matched_treatments.length > 0 ? (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="subtitle2">{t('diagnose.results.treatments')}</Typography>
                  <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                    {candidate.matched_treatments.map((treatment) => (
                      <Chip
                        key={treatment.key}
                        size="small"
                        variant="outlined"
                        clickable
                        component={RouterLink}
                        to={treatment.detail_url}
                        icon={treatment.has_karenz ? <WarningAmberIcon /> : undefined}
                        color={treatment.has_karenz ? 'warning' : 'default'}
                        label={
                          treatment.has_karenz
                            ? t('diagnose.results.treatmentKarenz', {
                                name: treatment.name_de || treatment.name,
                                days: treatment.safety_interval_days,
                              })
                            : treatment.name_de || treatment.name
                        }
                        data-testid={`diagnosis-treatment-${treatment.key}`}
                      />
                    ))}
                  </Stack>
                </Box>
              ) : null}
            </CardContent>
          </Card>
        ))}
      </Stack>
    </AIResponse>
  );
}
