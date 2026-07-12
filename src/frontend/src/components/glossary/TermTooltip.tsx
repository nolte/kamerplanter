import { type MouseEvent, type ReactNode, useCallback, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Popover from '@mui/material/Popover';
import Skeleton from '@mui/material/Skeleton';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import HelpOutlineIcon from '@mui/icons-material/HelpOutlined';
import AIResponse from '@/components/ai/AIResponse';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';
import { useGlossaryTerm } from '@/hooks/useGlossaryTerm';
import type { GlossaryExpertiseLevel } from '@/api/types';

export interface TermTooltipProps {
  /** Canonical glossary slug (e.g. "vpd", "ec", "karenzzeit"). */
  slug: string;
  /** Element rendered before the help icon (usually the term label). */
  children?: ReactNode;
  /** When true the trigger is the icon alone (e.g. inside a table header). */
  iconOnly?: boolean;
}

/**
 * REQ-035 §5.1 — `<TermTooltip>` (RAG-backed term explanation popover).
 *
 * Extends the static `<HelpTooltip>` foundation: clicking the question-mark icon
 * opens a MUI `Popover` that lazily fetches the Knowledge-Service explanation for
 * the term at the user's experience level, rendered through the mandatory
 * `<AIResponse>` shell. Related terms are clickable chips that push onto an
 * in-popover stack with a back button (§5.1 stack navigation).
 */
export default function TermTooltip({ slug, children, iconOnly }: TermTooltipProps) {
  const { t, i18n } = useTranslation();
  const { level } = useExpertiseLevel();

  const language = useMemo<'de' | 'en'>(
    () => (i18n.language.startsWith('en') ? 'en' : 'de'),
    [i18n.language],
  );
  const expertise = level as GlossaryExpertiseLevel;

  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  // Stack of slugs visited within the open popover (related-term navigation).
  const [stack, setStack] = useState<string[]>([]);
  const activeSlug = stack.length > 0 ? stack[stack.length - 1] : null;

  const open = Boolean(anchorEl);
  const { answer, loading, error } = useGlossaryTerm(open ? activeSlug : null, language, expertise);

  const handleOpen = useCallback(
    (event: MouseEvent<HTMLElement>) => {
      event.stopPropagation();
      setStack([slug]);
      setAnchorEl(event.currentTarget);
    },
    [slug],
  );

  const handleClose = useCallback(() => {
    setAnchorEl(null);
    setStack([]);
  }, []);

  const handleBack = useCallback(() => {
    setStack((current) => (current.length > 1 ? current.slice(0, -1) : current));
  }, []);

  const pushRelated = useCallback((relatedSlug: string) => {
    setStack((current) => [...current, relatedSlug]);
  }, []);

  const label = t('pages.glossary.tooltip.ariaOpen', { term: slug });

  return (
    <>
      <Box
        component="span"
        sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}
        data-testid={`term-tooltip-${slug}`}
      >
        {!iconOnly && children}
        <IconButton
          size="small"
          onClick={handleOpen}
          aria-label={label}
          data-testid={`term-tooltip-trigger-${slug}`}
          sx={{ p: '2px', color: 'primary.main' }}
        >
          <HelpOutlineIcon sx={{ fontSize: 16 }} />
        </IconButton>
      </Box>

      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        slotProps={{ paper: { sx: { maxWidth: 360, p: 2 } } }}
        data-testid="term-tooltip-popover"
      >
        <Stack direction="row" spacing={1} sx={{ mb: 1, alignItems: 'center' }}>
          {stack.length > 1 && (
            <IconButton
              size="small"
              onClick={handleBack}
              aria-label={t('pages.glossary.tooltip.back')}
              data-testid="term-tooltip-back"
            >
              <ArrowBackIcon fontSize="small" />
            </IconButton>
          )}
          <Typography variant="subtitle2" sx={{ fontWeight: 600, flexGrow: 1 }}>
            {answer?.long_label ?? activeSlug}
          </Typography>
        </Stack>

        {loading && (
          <Box data-testid="term-tooltip-loading">
            <Skeleton variant="text" width="90%" />
            <Skeleton variant="text" width="75%" />
            <Skeleton variant="text" width="60%" />
          </Box>
        )}

        {error && !loading && (
          <Typography variant="body2" color="error" data-testid="term-tooltip-error">
            {t('pages.glossary.tooltip.error')}
          </Typography>
        )}

        {answer && !loading && !error && (
          <AIResponse
            sources={answer.sources}
            modelName={answer.model_name}
            providerType={answer.provider_type}
            usesCloudProvider={answer.uses_cloud_provider}
            languageMismatchWarning={answer.language_mismatch_warning}
            data-testid="term-tooltip-response"
          >
            <Typography variant="body2">{answer.answer_text}</Typography>

            {answer.is_fallback && (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ display: 'block', mt: 0.5, fontStyle: 'italic' }}
                data-testid="term-tooltip-fallback-hint"
              >
                {t('pages.glossary.tooltip.fallbackHint')}
              </Typography>
            )}

            {answer.related_terms.length > 0 && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  {t('pages.glossary.tooltip.relatedTitle')}
                </Typography>
                <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                  {answer.related_terms.map((related) => (
                    <Chip
                      key={related.slug}
                      size="small"
                      label={related.label}
                      onClick={() => pushRelated(related.slug)}
                      data-testid={`term-tooltip-related-${related.slug}`}
                    />
                  ))}
                </Stack>
              </Box>
            )}
          </AIResponse>
        )}
      </Popover>
    </>
  );
}
