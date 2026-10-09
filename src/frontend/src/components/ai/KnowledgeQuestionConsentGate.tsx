import { useEffect, useId, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Link from '@mui/material/Link';
import { Link as RouterLink } from 'react-router-dom';
import Typography from '@mui/material/Typography';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import PrivacyTipIcon from '@mui/icons-material/PrivacyTip';

interface KnowledgeQuestionConsentGateProps {
  granting: boolean;
  error: string | null;
  onGrant: () => void;
  onDecline: () => void;
}

/**
 * REQ-031 / REQ-025 (#2175) — in-place consent for the KI page's knowledge question.
 *
 * Shown when the Full-mode route refuses with `403 CONSENT_REQUIRED` for the
 * purpose `ai_knowledge_question`. It says what leaves the installation (the
 * question text, to the language model the garden has configured), that no plant
 * data goes along, and where the consent is revoked; granting it re-sends the
 * question. Built like `IdentificationConsentGate`: accept on top on xs, decline
 * left / accept right from sm, 44px touch targets (UI-NFR-001 R-011).
 */
export default function KnowledgeQuestionConsentGate({
  granting,
  error,
  onGrant,
  onDecline,
}: KnowledgeQuestionConsentGateProps) {
  const { t } = useTranslation();
  const titleId = useId();
  const acceptRef = useRef<HTMLButtonElement>(null);

  // A failed grant leaves the gate open; focus goes back to the action that
  // failed, so a keyboard user can retry without hunting for it.
  useEffect(() => {
    if (error) acceptRef.current?.focus();
  }, [error]);

  const handleGrant = () => {
    // aria-disabled instead of `disabled` while granting: a disabled button drops
    // focus to <body>; the guard keeps a second click from granting twice.
    if (granting) return;
    onGrant();
  };

  return (
    <Box role="region" aria-labelledby={titleId} data-testid="ki-consent-gate" sx={{ py: 1 }}>
      <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center', mb: 1.5 }}>
        <PrivacyTipIcon color="primary" aria-hidden fontSize="medium" />
        <Typography variant="h6" component="h2" id={titleId}>
          {t('pages.kiAssistent.consent.title')}
        </Typography>
      </Box>

      <Typography variant="body2" sx={{ mb: 1 }}>
        {t('pages.kiAssistent.consent.body')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
        {t('pages.kiAssistent.consent.noPlantData')}
      </Typography>

      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1.5 }}>
        {t('pages.kiAssistent.consent.revoke')}{' '}
        <Link component={RouterLink} to="/privacy" variant="caption">
          {t('pages.kiAssistent.consent.privacyLink')}
        </Link>
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} data-testid="ki-consent-error">
          {error}
        </Alert>
      )}

      <Box
        sx={{
          display: 'flex',
          flexDirection: { xs: 'column-reverse', sm: 'row' },
          gap: 1,
          justifyContent: 'flex-end',
        }}
      >
        {/* UI-NFR-013: declining is as prominent as consenting. */}
        <Button
          variant="outlined"
          onClick={onDecline}
          data-testid="ki-consent-decline"
          sx={{ minHeight: 44 }}
        >
          {t('pages.kiAssistent.consent.decline')}
        </Button>
        <Button
          variant="contained"
          ref={acceptRef}
          onClick={handleGrant}
          aria-disabled={granting || undefined}
          // The gate replaces the answer area after a submit; focus lands on the
          // primary action so keyboard and screen-reader users notice it.
          autoFocus
          startIcon={granting ? <CircularProgress size={16} /> : undefined}
          data-testid="ki-consent-accept"
          sx={{ minHeight: 44 }}
        >
          {t('pages.kiAssistent.consent.accept')}
        </Button>
      </Box>
    </Box>
  );
}
