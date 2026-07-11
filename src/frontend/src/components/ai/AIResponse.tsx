import { type ReactNode, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Chip from '@mui/material/Chip';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import CloudOutlinedIcon from '@mui/icons-material/CloudOutlined';
import PersonOutlineIcon from '@mui/icons-material/PersonOutlined';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import type { AiConfidence, AiSourceRef } from '@/api/types';

export interface AIResponseProps {
  /** The KI answer body (rendered as children). */
  children: ReactNode;
  /** Cited knowledge chunks — rendered as an aufklappbarer Quellen-Footer. */
  sources?: AiSourceRef[];
  /** Model name shown in the KI-Badge tooltip. */
  modelName?: string;
  /** Provider type (ollama / anthropic / …) shown in the KI-Badge tooltip. */
  providerType?: string;
  /** True → show the "nutzt deine Pflanzendaten"-Indikator. */
  usesTenantData?: boolean;
  /** True → show the Cloud-Provider-Indikator. */
  usesCloudProvider?: boolean;
  /** True → show the Sprach-Hinweis (englische Wissensbasis im Aufbau). */
  languageMismatchWarning?: boolean;
  /** ADR-002 confidence — `low`/`none` shows the "Allgemeine Information"-Badge. */
  confidence?: AiConfidence;
  /** Tenant-eigener Sortenname (Anzeige im Confidence-Tooltip). */
  cultivarHint?: string | null;
  /** Fallback-Art, auf der die Antwort beruht (Confidence-Tooltip). */
  fallbackSpecies?: string | null;
  /** data-testid passthrough. */
  'data-testid'?: string;
}

/**
 * REQ-031 §6.1 — Pflicht-Huelle fuer ALLE KI-generierten Inhalte.
 *
 * Rendert das sichtbare KI-Labeling (Badge + Modell-Tooltip), den
 * Tenant-Daten-Indikator, den Cloud-Provider-Indikator, das Confidence-Badge
 * (ADR-002), den aufklappbaren Quellen-Footer (erfahrungsstufen-abhaengig
 * vor-/zugeklappt) und den Disclaimer. KI-Inhalte ohne diese Huelle werden im
 * Code-Review abgelehnt.
 */
export default function AIResponse({
  children,
  sources = [],
  modelName,
  providerType,
  usesTenantData = false,
  usesCloudProvider = false,
  languageMismatchWarning = false,
  confidence = 'high',
  cultivarHint,
  fallbackSpecies,
  'data-testid': dataTestId,
}: AIResponseProps) {
  const { t } = useTranslation();
  const { level } = useExpertiseLevel();

  // Expert-Nutzer sehen die Quellen per Default ausgeklappt (REQ-021 §6.1).
  const sourcesDefaultExpanded = useMemo(() => level === 'expert', [level]);
  const showLowConfidence = confidence === 'low' || confidence === 'none';

  const modelTooltip = useMemo(() => {
    const parts = [providerType, modelName].filter(Boolean);
    return parts.length > 0 ? parts.join(' · ') : t('ai.badge.tooltipUnknown');
  }, [providerType, modelName, t]);

  return (
    <Box data-testid={dataTestId ?? 'ai-response'}>
      <Stack direction="row" spacing={1} sx={{ mb: 1, flexWrap: 'wrap' }}>
        <Tooltip title={modelTooltip}>
          <Chip
            size="small"
            color="primary"
            variant="outlined"
            icon={<AutoAwesomeIcon />}
            label={t('ai.badge.label')}
            data-testid="ai-badge"
          />
        </Tooltip>

        {usesTenantData && (
          <Tooltip title={t('ai.tenantData.tooltip')}>
            <Chip
              size="small"
              color="info"
              variant="outlined"
              icon={<PersonOutlineIcon />}
              label={t('ai.tenantData.label')}
              data-testid="ai-tenant-data-indicator"
            />
          </Tooltip>
        )}

        {usesCloudProvider && (
          <Tooltip title={t('ai.cloud.tooltip', { provider: providerType ?? '' })}>
            <Chip
              size="small"
              color="warning"
              variant="outlined"
              icon={<CloudOutlinedIcon />}
              label={t('ai.cloud.label')}
              data-testid="ai-cloud-indicator"
            />
          </Tooltip>
        )}

        {showLowConfidence && (
          <Tooltip
            title={t('ai.confidence.lowTooltip', {
              species: fallbackSpecies ?? t('ai.confidence.genericSpecies'),
              cultivar: cultivarHint ?? t('ai.confidence.yourCultivar'),
            })}
          >
            <Chip
              size="small"
              color="default"
              variant="outlined"
              icon={<InfoOutlinedIcon />}
              label={t('ai.confidence.lowLabel')}
              data-testid="ai-confidence-badge"
            />
          </Tooltip>
        )}
      </Stack>

      {languageMismatchWarning && (
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ display: 'block', mb: 1 }}
          data-testid="ai-language-warning"
        >
          {t('ai.languageMismatch')}
        </Typography>
      )}

      <Box sx={{ '& p': { m: 0 } }}>{children}</Box>

      {sources.length > 0 && (
        <Accordion
          defaultExpanded={sourcesDefaultExpanded}
          disableGutters
          elevation={0}
          sx={{ mt: 1, bgcolor: 'transparent', '&::before': { display: 'none' } }}
          data-testid="ai-sources"
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ px: 0, minHeight: 36 }}>
            <Typography variant="caption" color="text.secondary">
              {t('ai.sources.title', { count: sources.length })}
            </Typography>
          </AccordionSummary>
          <AccordionDetails sx={{ px: 0, pt: 0 }}>
            <Stack spacing={0.5}>
              {sources.map((source) => (
                <Typography
                  key={source.source_key}
                  variant="caption"
                  color="text.secondary"
                  data-testid="ai-source-item"
                >
                  {source.title || source.source_key}
                  {' · '}
                  {source.source_type}
                  {' · '}
                  {t('ai.sources.score', { score: source.score.toFixed(2) })}
                  {' · '}
                  {source.language.toUpperCase()}
                </Typography>
              ))}
            </Stack>
          </AccordionDetails>
        </Accordion>
      )}

      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ display: 'block', mt: 1, fontStyle: 'italic' }}
      >
        {t('ai.disclaimer')}
      </Typography>
    </Box>
  );
}
