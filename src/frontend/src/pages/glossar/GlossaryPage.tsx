import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardActionArea from '@mui/material/CardActionArea';
import Chip from '@mui/material/Chip';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { glossaryApi } from '@/api';
import type { GlossaryExpertiseLevel, GlossaryTermSummary } from '@/api/types';
import AIResponse from '@/components/ai/AIResponse';
import EmptyState from '@/components/common/EmptyState';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { useGlossaryTerm } from '@/hooks/useGlossaryTerm';

/**
 * REQ-035 §5.2 — `<GlossaryPage>` term browser.
 *
 * Lists all active glossary terms grouped by category. Selecting a term reveals
 * the full RAG explanation (same content as `<TermTooltip>`, rendered as a full
 * panel through the mandatory `<AIResponse>` shell) with a back button. Reachable
 * at `/glossar` (tenant) and, in light mode, as the anonymous knowledge browser.
 */
export default function GlossaryPage() {
  const { t, i18n } = useTranslation();
  const { level } = useExpertiseLevel();

  const language = useMemo<'de' | 'en'>(
    () => (i18n.language.startsWith('en') ? 'en' : 'de'),
    [i18n.language],
  );
  const expertise = level as GlossaryExpertiseLevel;

  const [terms, setTerms] = useState<GlossaryTermSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);
    glossaryApi
      .listTerms(undefined, language)
      .then((result) => {
        if (cancelled) return;
        setTerms(result);
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setError(true);
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [language]);

  // Group terms by category for the browse view.
  const grouped = useMemo(() => {
    const byCategory = new Map<string, GlossaryTermSummary[]>();
    for (const term of terms) {
      const bucket = byCategory.get(term.category) ?? [];
      bucket.push(term);
      byCategory.set(term.category, bucket);
    }
    return [...byCategory.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [terms]);

  const detail = useGlossaryTerm(selectedSlug, language, expertise);

  const handleBack = useCallback(() => setSelectedSlug(null), []);

  const categoryLabel = useCallback(
    (category: string) => t(`pages.glossary.categories.${category}`, { defaultValue: category }),
    [t],
  );

  return (
    <Box sx={{ p: 3 }} data-testid="glossary-page">
      <Typography variant="h4" gutterBottom>
        {t('pages.glossary.title')}
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        {t('pages.glossary.subtitle')}
      </Typography>

      {loading && <LoadingSkeleton variant="card" />}

      {error && !loading && (
        <EmptyState message={t('pages.glossary.loadError')} />
      )}

      {!loading && !error && terms.length === 0 && (
        <EmptyState message={t('pages.glossary.empty')} />
      )}

      {/* Detail view for the selected term. */}
      {selectedSlug && (
        <Box data-testid="glossary-detail">
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={handleBack}
            sx={{ mb: 2 }}
            data-testid="glossary-detail-back"
          >
            {t('pages.glossary.backToList')}
          </Button>
          {detail.loading && <LoadingSkeleton variant="form" />}
          {detail.error && !detail.loading && (
            <EmptyState message={t('pages.glossary.tooltip.error')} />
          )}
          {detail.answer && !detail.loading && !detail.error && (
            <Card sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom>
                {detail.answer.long_label}
              </Typography>
              <AIResponse
                sources={detail.answer.sources}
                modelName={detail.answer.model_name}
                providerType={detail.answer.provider_type}
                usesCloudProvider={detail.answer.uses_cloud_provider}
                languageMismatchWarning={detail.answer.language_mismatch_warning}
                data-testid="glossary-detail-response"
              >
                <Typography variant="body1">{detail.answer.answer_text}</Typography>
                {detail.answer.is_fallback && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ display: 'block', mt: 1, fontStyle: 'italic' }}
                    data-testid="glossary-detail-fallback-hint"
                  >
                    {t('pages.glossary.tooltip.fallbackHint')}
                  </Typography>
                )}
                {detail.answer.related_terms.length > 0 && (
                  <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5, mt: 2 }}>
                    {detail.answer.related_terms.map((related) => (
                      <Chip
                        key={related.slug}
                        size="small"
                        label={related.label}
                        onClick={() => setSelectedSlug(related.slug)}
                        data-testid={`glossary-detail-related-${related.slug}`}
                      />
                    ))}
                  </Stack>
                )}
              </AIResponse>
            </Card>
          )}
        </Box>
      )}

      {/* Browse view (hidden while a term detail is open). */}
      {!selectedSlug && !loading && !error && grouped.length > 0 && (
        <Stack spacing={3}>
          {grouped.map(([category, categoryTerms]) => (
            <Box key={category} data-testid={`glossary-category-${category}`}>
              <Typography variant="h6" gutterBottom>
                {categoryLabel(category)}
              </Typography>
              <Box
                sx={{
                  display: 'grid',
                  gap: 1.5,
                  gridTemplateColumns: {
                    xs: '1fr',
                    sm: 'repeat(2, 1fr)',
                    md: 'repeat(3, 1fr)',
                  },
                }}
              >
                {categoryTerms.map((term) => (
                  <Card key={term.slug} variant="outlined">
                    <CardActionArea
                      onClick={() => setSelectedSlug(term.slug)}
                      sx={{ p: 2 }}
                      data-testid={`glossary-term-${term.slug}`}
                    >
                      <Typography variant="subtitle1">{term.label}</Typography>
                    </CardActionArea>
                  </Card>
                ))}
              </Box>
            </Box>
          ))}
        </Stack>
      )}
    </Box>
  );
}
