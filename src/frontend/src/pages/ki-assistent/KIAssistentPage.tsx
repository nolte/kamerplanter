import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import CircularProgress from '@mui/material/CircularProgress';
import ChatIcon from '@mui/icons-material/Chat';
import PageTitle from '@/components/layout/PageTitle';
import EmptyState from '@/components/common/EmptyState';
import AIResponse from '@/components/ai/AIResponse';
import AiChatDrawer from '@/components/ai/AiChatDrawer';
import KnowledgeQuestionConsentGate from '@/components/ai/KnowledgeQuestionConsentGate';
import {
  consentPurposeOf,
  isConsentRequired,
  resolveAiErrorMessage,
} from '@/components/ai/aiErrorMessage';
import { aiApi } from '@/api';
import { grantConsent } from '@/api/endpoints/privacy';
import type { KnowledgeAnswer } from '@/api/endpoints/ai';
import { kamiKiAssistent } from '@/assets/brand/illustrations';
import { isLightMode } from '@/config/mode';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchAiStatus } from '@/store/slices/aiStatusSlice';

/** The consent purpose of the free-form knowledge question (#2175). */
const KNOWLEDGE_CONSENT_PURPOSE = 'ai_knowledge_question';

/**
 * REQ-031 KI-Assistent — Wissens-Frage-Antwort-Seite.
 *
 * In beiden Modi verfuegbar. Der Pfad haengt am Modus (`aiApi.askKnowledgeQuestion`):
 * im Light-Modus `/public/ai/ask` (System-User, kein Tenant-Kontext, §5.3), im
 * Full-Modus `/t/{slug}/ai/knowledge/ask` (#2175) — dort mit Rolle, KI-Schalter
 * des Gartens, Einwilligung `ai_knowledge_question` und Tagesbudget. Fehlt die
 * Einwilligung, bietet die Seite sie an Ort und Stelle an und stellt die Frage
 * nach der Erteilung erneut. Im Full-Modus zusaetzlich der kontextbewusste
 * Chat-Drawer.
 */
export default function KIAssistentPage() {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  // Issue #685 — degrade to a clear "not configured" state when AI features are
  // disabled cluster-wide, instead of surfacing the guard's 404 as a generic
  // error. The probe runs at app start; refresh it here for direct navigation.
  const aiAvailable = useAppSelector((s) => s.aiStatus.available);
  useEffect(() => {
    void dispatch(fetchAiStatus());
  }, [dispatch]);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<KnowledgeAnswer | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  // The question the consent gate holds back; non-null while the gate is shown.
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [consentGranting, setConsentGranting] = useState(false);
  const [consentError, setConsentError] = useState<string | null>(null);

  const language = i18n.language.startsWith('en') ? 'en' : 'de';

  // `afterGrant` stops a loop: a refusal right after the grant is reported, not
  // answered with the same gate again.
  const submit = useCallback(
    async (trimmed: string, afterGrant: boolean) => {
      setLoading(true);
      setError(null);
      setAnswer(null);
      try {
        setAnswer(await aiApi.askKnowledgeQuestion(trimmed, language));
      } catch (err) {
        if (isConsentRequired(err)) {
          // The refusal names its purpose in the message only; an unnamed one is
          // this route's own purpose. Another purpose (e.g. the cloud provider's)
          // is not granted from here — the page cannot explain it.
          const purpose = consentPurposeOf(err) ?? KNOWLEDGE_CONSENT_PURPOSE;
          if (!isLightMode && !afterGrant && purpose === KNOWLEDGE_CONSENT_PURPOSE) {
            setConsentError(null);
            setPendingQuestion(trimmed);
            return;
          }
          setError(
            purpose === KNOWLEDGE_CONSENT_PURPOSE
              ? t('pages.kiAssistent.consent.stillMissing')
              : t('pages.kiAssistent.consent.otherPurpose'),
          );
          return;
        }
        setError(resolveAiErrorMessage(err, t, t('pages.kiAssistent.error')));
      } finally {
        setLoading(false);
      }
    },
    [language, t],
  );

  const handleAsk = useCallback(async () => {
    const trimmed = question.trim();
    if (trimmed.length < 3 || loading || consentGranting) return;
    setPendingQuestion(null);
    await submit(trimmed, false);
  }, [question, loading, consentGranting, submit]);

  const handleGrantConsent = useCallback(async () => {
    if (pendingQuestion === null) return;
    setConsentGranting(true);
    setConsentError(null);
    try {
      await grantConsent(KNOWLEDGE_CONSENT_PURPOSE);
    } catch {
      // The gate stays open with the failure — the question is not re-sent.
      setConsentError(t('pages.kiAssistent.consent.grantFailed'));
      setConsentGranting(false);
      return;
    }
    setConsentGranting(false);
    const retry = pendingQuestion;
    setPendingQuestion(null);
    await submit(retry, true);
  }, [pendingQuestion, submit, t]);

  const handleDeclineConsent = useCallback(() => {
    setPendingQuestion(null);
    setConsentError(null);
    setError(t('pages.kiAssistent.consent.declined'));
  }, [t]);

  const consentGateOpen = pendingQuestion !== null;

  if (aiAvailable === false) {
    return (
      <Box sx={{ p: { xs: 2, sm: 3 } }} data-testid="ki-assistent-page">
        <PageTitle title={t('pages.kiAssistent.title')} />
        <EmptyState
          message={t('pages.kiAssistent.notConfigured.title')}
          description={t('pages.kiAssistent.notConfigured.description')}
        />
      </Box>
    );
  }

  return (
    <Box sx={{ p: { xs: 2, sm: 3 } }} data-testid="ki-assistent-page">
      <PageTitle
        title={t('pages.kiAssistent.title')}
        action={
          !isLightMode ? (
            <Button
              variant="outlined"
              startIcon={<ChatIcon />}
              onClick={() => setChatOpen(true)}
              sx={{ minHeight: 48 }}
              data-testid="open-chat-button"
            >
              {t('pages.kiAssistent.openChat')}
            </Button>
          ) : undefined
        }
      />

      <Typography color="text.secondary" sx={{ mb: 2, maxWidth: 720 }}>
        {t('pages.kiAssistent.intro')}
      </Typography>

      <Paper variant="outlined" sx={{ p: 2, maxWidth: 720 }}>
        <Stack spacing={2}>
          <TextField
            fullWidth
            multiline
            minRows={2}
            maxRows={6}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
                event.preventDefault();
                void handleAsk();
              }
            }}
            label={t('pages.kiAssistent.questionLabel')}
            placeholder={t('pages.kiAssistent.questionPlaceholder')}
            helperText={t('pages.kiAssistent.questionHelp')}
            data-testid="ki-question-input"
          />
          <Box>
            <Button
              variant="contained"
              onClick={() => void handleAsk()}
              disabled={loading || consentGranting || question.trim().length < 3}
              sx={{ minHeight: 48 }}
              data-testid="ki-ask-button"
            >
              {t('pages.kiAssistent.ask')}
            </Button>
          </Box>

          {!answer && !loading && !error && !consentGateOpen && (
            <Box sx={{ display: 'flex', justifyContent: 'center', pt: 1 }}>
              <Box
                component="img"
                src={kamiKiAssistent}
                alt=""
                aria-hidden="true"
                sx={{ maxHeight: 150, maxWidth: '100%', objectFit: 'contain', opacity: 0.9 }}
              />
            </Box>
          )}

          {loading && (
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
              <CircularProgress size={20} />
              <Typography variant="body2" color="text.secondary">
                {t('ai.why.thinking')}
              </Typography>
            </Stack>
          )}

          {consentGateOpen && (
            <KnowledgeQuestionConsentGate
              granting={consentGranting}
              error={consentError}
              onGrant={() => void handleGrantConsent()}
              onDecline={handleDeclineConsent}
            />
          )}

          {error && (
            <Typography variant="body2" color="error" role="alert" data-testid="ki-ask-error">
              {error}
            </Typography>
          )}

          {answer && (
            <AIResponse
              sources={answer.sources}
              modelName={answer.model_name}
              providerType={answer.provider_type}
              usesTenantData={answer.uses_tenant_data}
              usesCloudProvider={answer.uses_cloud_provider}
              confidence={answer.confidence}
              languageMismatchWarning={answer.language_mismatch_warning}
            >
              <Typography variant="body2">{answer.answer_text}</Typography>
            </AIResponse>
          )}
        </Stack>
      </Paper>

      {!isLightMode && <AiChatDrawer open={chatOpen} onClose={() => setChatOpen(false)} />}
    </Box>
  );
}
