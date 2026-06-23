import { useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import Tooltip from '@mui/material/Tooltip';
import FavoriteIcon from '@mui/icons-material/Favorite';
import AddPhotoAlternateIcon from '@mui/icons-material/AddPhotoAlternate';
import type { ExperienceLevel } from '@/api/types';
import type { PestDetectionResult, PestFinding } from '@/api/types';

interface PestFindingsResultProps {
  /** The detection result to render (findings, abstention, disclaimer flags). */
  result: PestDetectionResult;
  /** Preview URL of the analysed photo — enables the bounding-box overlay. */
  previewUrl?: string | null;
  /** Experience level: beginner sees only the top finding. */
  level: ExperienceLevel;
  /** HITL feedback callback (confirmed / wrong / was beneficial). */
  onFeedback: (finding: PestFinding, confirmed: boolean, wasBeneficial?: boolean) => void;
  /** Navigate to the pest detail page for a matched pest. */
  onViewPest: (pestKey: string) => void;
  /** Pest keys whose photo was already contributed to the gallery. */
  addedPestKeys?: string[];
  /** Pest key whose gallery upload is currently in flight. */
  addingPestKey?: string | null;
  /** Add the captured photo to a matched pest's gallery (opt-in). Omit to hide. */
  onAddToGallery?: (pestKey: string) => void;
  /** Whether the add-to-gallery CTA may be shown (held File + not light-blocked). */
  canAddToGallery?: boolean;
}

/**
 * REQ-044 §7 — shared rendering of a pest-detection result.
 *
 * Extracted from {@link PestDetectionDialog} so the standalone pest-detection
 * page and the plant-bound dialog share one implementation: bounding-box
 * overlay (Mode 1), abstention hint, beneficial hint, no-findings note, the
 * findings list with HITL feedback, the "more about this pest" link and the
 * opt-in "add to gallery" CTA. Plant-specific actions (create inspection) stay
 * in the dialog. Never triggers a treatment.
 */
export default function PestFindingsResult({
  result,
  previewUrl,
  level,
  onFeedback,
  onViewPest,
  addedPestKeys = [],
  addingPestKey = null,
  onAddToGallery,
  canAddToGallery = false,
}: PestFindingsResultProps) {
  const { t } = useTranslation();

  const directFindings = useMemo(
    () => (result.findings ?? []).filter((f) => f.bounding_box != null),
    [result],
  );

  const visibleFindings = useMemo(() => {
    const findings = result.findings ?? [];
    return level === 'beginner' ? findings.slice(0, 1) : findings;
  }, [result, level]);

  const hasBeneficial = useMemo(
    () => (result.findings ?? []).some((f) => f.category === 'beneficial'),
    [result],
  );

  const handleAdd = useCallback(
    (pestKey: string) => {
      onAddToGallery?.(pestKey);
    },
    [onAddToGallery],
  );

  return (
    <Box sx={{ mt: 1 }} aria-live="polite">
      {/* Box overlay for direct findings (Mode 1). */}
      {previewUrl && (
        <Box
          sx={{ position: 'relative', mb: 2, lineHeight: 0 }}
          data-testid="pest-preview"
          role="img"
          aria-label={t('pages.pests.previewAlt')}
        >
          <Box
            component="img"
            src={previewUrl}
            alt=""
            aria-hidden="true"
            sx={{ width: '100%', borderRadius: 1, display: 'block' }}
          />
          {directFindings.map((f, i) => (
            <Tooltip
              key={`${f.label}-${i}`}
              title={t('pages.pests.boundingBoxLabel', { name: f.common_name })}
              placement="top"
            >
              <Box
                data-testid="pest-bounding-box"
                role="img"
                aria-label={t('pages.pests.boundingBoxLabel', { name: f.common_name })}
                tabIndex={0}
                sx={{
                  position: 'absolute',
                  left: `${(f.bounding_box?.x ?? 0) * 100}%`,
                  top: `${(f.bounding_box?.y ?? 0) * 100}%`,
                  width: `${(f.bounding_box?.width ?? 0) * 100}%`,
                  height: `${(f.bounding_box?.height ?? 0) * 100}%`,
                  border: '2px solid',
                  borderColor: f.category === 'beneficial' ? 'success.main' : 'warning.main',
                  borderRadius: 0.5,
                  cursor: 'default',
                  '&:focus-visible': {
                    outline: '2px solid',
                    outlineColor: 'primary.main',
                    outlineOffset: '2px',
                  },
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    px: 0.5,
                    lineHeight: 1.4,
                    bgcolor: f.category === 'beneficial' ? 'success.main' : 'warning.main',
                    color: 'common.white',
                    borderRadius: '0 0 4px 0',
                    maxWidth: '100%',
                    overflow: 'hidden',
                    whiteSpace: 'nowrap',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {f.common_name}
                </Typography>
              </Box>
            </Tooltip>
          ))}
        </Box>
      )}

      {/* Abstention (§4.3 / Szenario 2). */}
      {!result.is_confident && (
        <Alert severity="warning" sx={{ mb: 2 }} data-testid="pest-abstain">
          {t('pages.pests.abstain')}
        </Alert>
      )}

      {/* Beneficial hint (§9.1 / Szenario 3). */}
      {hasBeneficial && (
        <Alert severity="success" icon={<FavoriteIcon />} sx={{ mb: 2 }} data-testid="pest-beneficial">
          {t('pages.pests.beneficial')}
        </Alert>
      )}

      {/* No findings (still not proof of pest-freeness, §7.1). */}
      {result.findings.length === 0 && (
        <Alert severity="info" sx={{ mb: 2 }} data-testid="pest-no-findings">
          {t('pages.pests.noFindings')}
        </Alert>
      )}

      {visibleFindings.length > 0 && (
        <Stack
          spacing={1}
          divider={<Divider flexItem />}
          component="ul"
          sx={{ listStyle: 'none', p: 0, m: 0 }}
        >
          {visibleFindings.map((f, i) => (
            <Box
              key={`${f.label}-${i}`}
              component="li"
              data-testid="pest-finding"
              aria-label={t('pages.pests.findingAriaLabel', {
                index: i + 1,
                name: f.common_name,
                category: t(`enums.pestCategory.${f.category}`),
                confidence: Math.round(f.confidence * 100),
              })}
            >
              <Stack
                direction="row"
                spacing={1}
                sx={{ alignItems: 'center', flexWrap: 'wrap', mb: f.category !== 'beneficial' ? 1 : 0 }}
              >
                <Typography variant="subtitle2">{f.common_name}</Typography>
                <Chip
                  size="small"
                  color={f.category === 'beneficial' ? 'success' : 'default'}
                  label={t(`enums.pestCategory.${f.category}`)}
                />
                <Chip size="small" variant="outlined" label={t(`enums.pestMode.${f.mode}`)} />
                <Typography
                  variant="caption"
                  color="text.secondary"
                  aria-label={t('pages.pests.confidenceLabel', {
                    value: Math.round(f.confidence * 100),
                  })}
                >
                  {t('pages.pests.confidence')}: {Math.round(f.confidence * 100)}&nbsp;%
                </Typography>
              </Stack>
              {f.matched_pest_key && (
                <Button
                  size="small"
                  variant="text"
                  onClick={() => onViewPest(f.matched_pest_key as string)}
                  data-testid="pest-finding-detail-link"
                  sx={{ px: 0, mb: f.category !== 'beneficial' ? 1 : 0 }}
                >
                  {t('pages.pests.viewPestDetail')}
                </Button>
              )}
              {/* REQ-044 §8 — deliberate, opt-in contribution of the captured
                  photo to the pest gallery. Never an automatic save. */}
              {f.matched_pest_key && canAddToGallery && onAddToGallery && (
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<AddPhotoAlternateIcon />}
                  disabled={
                    addingPestKey === f.matched_pest_key ||
                    addedPestKeys.includes(f.matched_pest_key)
                  }
                  onClick={() => handleAdd(f.matched_pest_key as string)}
                  data-testid="pest-detection-add-to-gallery"
                  aria-label={t('pages.pests.addToGalleryAriaLabel', { name: f.common_name })}
                  sx={{ display: 'flex', mt: 0.5, mb: f.category !== 'beneficial' ? 1 : 0, minHeight: 44 }}
                >
                  {addedPestKeys.includes(f.matched_pest_key)
                    ? t('pages.pests.addToGallerySuccess')
                    : t('pages.pests.addToGallery')}
                </Button>
              )}
              {f.category !== 'beneficial' && (
                <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => onFeedback(f, true)}
                    data-testid="pest-feedback-confirm"
                    aria-label={t('pages.pests.feedbackConfirmAriaLabel')}
                    sx={{ minHeight: 44 }}
                  >
                    {t('pages.pests.feedbackConfirm')}
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => onFeedback(f, false)}
                    data-testid="pest-feedback-wrong"
                    aria-label={t('pages.pests.feedbackWrongAriaLabel')}
                    sx={{ minHeight: 44 }}
                  >
                    {t('pages.pests.feedbackWrong')}
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    color="success"
                    onClick={() => onFeedback(f, false, true)}
                    data-testid="pest-feedback-beneficial"
                    aria-label={t('pages.pests.feedbackBeneficialAriaLabel')}
                    sx={{ minHeight: 44 }}
                  >
                    {t('pages.pests.feedbackBeneficial')}
                  </Button>
                </Stack>
              )}
            </Box>
          ))}
        </Stack>
      )}
    </Box>
  );
}
