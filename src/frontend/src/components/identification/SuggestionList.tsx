import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import Chip from '@mui/material/Chip';
import LinearProgress from '@mui/material/LinearProgress';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Link from '@mui/material/Link';
import Tooltip from '@mui/material/Tooltip';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import StorageIcon from '@mui/icons-material/Storage';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import type { ExperienceLevel, IdentificationSuggestion } from '@/api/types';

interface SuggestionListProps {
  suggestions: IdentificationSuggestion[];
  selectedRank: number | null;
  onSelect: (rank: number) => void;
  level: ExperienceLevel;
  disabled?: boolean;
}

/** Reference-image size scales down as expertise rises (REQ-029 §4.3). */
const IMAGE_SIZE: Record<ExperienceLevel, number> = {
  beginner: 96,
  intermediate: 72,
  expert: 56,
};

/**
 * REQ-029 §4.1/§4.3 — candidate selection UI.
 *
 * Renders the rank-sorted suggestions as selectable cards. Confidence is hidden
 * for beginners, shown as a percentage for intermediate, and with the raw score
 * for experts. The "already in database" badge surfaces `species_in_database`.
 *
 * Usability improvements over v1:
 * - Intro text above the list guides the user (UI-NFR-008 R-038)
 * - "Familie" chip has tooltip explaining the botanical term (UI-NFR-011)
 * - Confidence bar has info-icon tooltip for beginners who see it at intermediate+ (UI-NFR-011)
 * - Common name shown more prominently (larger variant) — Casual users recognise common names
 * - Card min-height 80px ensures comfortable touch targets (UI-NFR-001 R-011)
 * - Scientific name visually de-emphasised to subtitle2 for beginners (primary: common name)
 * - Selected card shows full border highlight without relying on color alone (UI-NFR-002)
 */
export default function SuggestionList({
  suggestions,
  selectedRank,
  onSelect,
  level,
  disabled = false,
}: SuggestionListProps) {
  const { t } = useTranslation();
  const showConfidence = level !== 'beginner';
  const showRawScore = level === 'expert';
  const showGbif = level === 'expert';
  const imageSize = IMAGE_SIZE[level];
  const isBeginner = level === 'beginner';

  return (
    <Box data-testid="suggestion-list">
      {/* Intro text — guides the user to make an explicit selection (UI-NFR-008 R-038) */}
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
        {t('pages.plantIdentification.resultsIntro')}
      </Typography>

      <Stack spacing={1.5}>
        {suggestions.map((s) => {
          const isSelected = selectedRank === s.rank;
          const confidencePct = Math.round(s.confidence * 100);
          const primaryCommonName = s.common_names[0];

          return (
            <Card
              key={`${s.rank}-${s.external_id}`}
              variant="outlined"
              data-testid={`suggestion-card-${s.rank}`}
              sx={{
                borderColor: isSelected ? 'primary.main' : 'divider',
                borderWidth: isSelected ? 2 : 1,
                // Ensure minimum comfortable touch height
                minHeight: 80,
              }}
            >
              <CardActionArea
                onClick={() => onSelect(s.rank)}
                disabled={disabled}
                aria-pressed={isSelected}
                aria-label={t('pages.plantIdentification.selectCandidateAria', {
                  name: s.scientific_name,
                })}
                data-testid={`suggestion-select-${s.rank}`}
                sx={{ p: 1.5, height: '100%' }}
              >
                <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
                  {s.image_url && (
                    <Box
                      component="img"
                      src={s.image_url}
                      alt={t('pages.plantIdentification.referenceImageAlt', {
                        name: s.scientific_name,
                      })}
                      loading="lazy"
                      sx={{
                        width: imageSize,
                        height: imageSize,
                        flexShrink: 0,
                        objectFit: 'cover',
                        borderRadius: 1,
                        border: '1px solid',
                        borderColor: 'divider',
                      }}
                      data-testid={`suggestion-image-${s.rank}`}
                    />
                  )}

                  <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                    {/*
                     * Name hierarchy: beginners see common name first (more recognisable),
                     * experts see scientific name first. Selected indicator is colour + icon
                     * so it never relies on colour alone (UI-NFR-002 R-015).
                     */}
                    {isBeginner && primaryCommonName ? (
                      <>
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 0.5,
                            flexWrap: 'wrap',
                          }}
                        >
                          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                            {primaryCommonName}
                          </Typography>
                          {isSelected && (
                            <CheckCircleIcon
                              color="primary"
                              fontSize="small"
                              aria-hidden
                            />
                          )}
                        </Box>
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{ fontStyle: 'italic' }}
                        >
                          {s.scientific_name}
                        </Typography>
                      </>
                    ) : (
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 0.5,
                          flexWrap: 'wrap',
                        }}
                      >
                        <Typography
                          variant="subtitle1"
                          sx={{ fontStyle: 'italic', fontWeight: 600 }}
                        >
                          {s.scientific_name}
                        </Typography>
                        {isSelected && (
                          <CheckCircleIcon color="primary" fontSize="small" aria-hidden />
                        )}
                      </Box>
                    )}

                    {/* Common name secondary line for intermediate/expert */}
                    {!isBeginner && primaryCommonName && (
                      <Typography variant="body2" color="text.secondary">
                        {primaryCommonName}
                      </Typography>
                    )}

                    <Stack
                      direction="row"
                      spacing={0.5}
                      sx={{ mt: 0.5, flexWrap: 'wrap', gap: 0.5 }}
                    >
                      {s.family && (
                        /*
                         * "Familie" is a botanical term — Casual users may not know it.
                         * Tooltip explains it in plain language (UI-NFR-011 §2.2).
                         */
                        <Tooltip
                          title={t('pages.plantIdentification.familyHelp')}
                          placement="top"
                          arrow
                        >
                          <Chip
                            label={`${t('pages.plantIdentification.familyLabel')}: ${s.family}`}
                            size="small"
                            variant="outlined"
                            data-testid={`suggestion-family-${s.rank}`}
                            // tabIndex so keyboard users can reach the tooltip
                            tabIndex={0}
                          />
                        </Tooltip>
                      )}
                      {s.species_in_database && (
                        <Chip
                          icon={<StorageIcon />}
                          label={t('pages.plantIdentification.inDatabase')}
                          size="small"
                          color="success"
                          variant="outlined"
                          data-testid={`suggestion-in-db-${s.rank}`}
                        />
                      )}
                    </Stack>

                    {showConfidence && (
                      <Box sx={{ mt: 1 }}>
                        <Box
                          sx={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            mb: 0.25,
                          }}
                        >
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Typography variant="caption" color="text.secondary">
                              {t('pages.plantIdentification.confidence')}
                            </Typography>
                            {/* Info icon explains confidence score for non-experts (UI-NFR-011) */}
                            <Tooltip
                              title={t('pages.plantIdentification.confidenceHelp')}
                              placement="top"
                              arrow
                            >
                              <InfoOutlinedIcon
                                sx={{ fontSize: 14, color: 'text.disabled', cursor: 'help' }}
                                aria-label={t('pages.plantIdentification.confidenceHelp')}
                                tabIndex={0}
                              />
                            </Tooltip>
                          </Box>
                          <Typography variant="caption" color="text.secondary">
                            {confidencePct}%
                            {showRawScore && ` (${s.confidence.toFixed(4)})`}
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={confidencePct}
                          aria-label={t('pages.plantIdentification.confidence')}
                          aria-valuenow={confidencePct}
                          aria-valuemin={0}
                          aria-valuemax={100}
                          sx={{ height: 6, borderRadius: 3 }}
                          data-testid={`suggestion-confidence-${s.rank}`}
                        />
                      </Box>
                    )}

                    {showGbif && s.gbif_id != null && (
                      <Link
                        href={`https://www.gbif.org/species/${s.gbif_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        variant="caption"
                        onClick={(e) => e.stopPropagation()}
                        sx={{ display: 'inline-block', mt: 0.5 }}
                        data-testid={`suggestion-gbif-${s.rank}`}
                      >
                        {t('pages.plantIdentification.gbifLink')}
                      </Link>
                    )}
                  </Box>
                </Box>
              </CardActionArea>
            </Card>
          );
        })}
      </Stack>
    </Box>
  );
}
