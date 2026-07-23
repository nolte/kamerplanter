import { useCallback, useState } from 'react';
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
import AIResponse from '@/components/ai/AIResponse';
import AiChatDrawer from '@/components/ai/AiChatDrawer';
import { resolveAiErrorMessage } from '@/components/ai/aiErrorMessage';
import { aiApi } from '@/api';
import { kamiKiAssistent } from '@/assets/brand/illustrations';
import { isLightMode } from '@/config/mode';
import type { AiResponse as AiResponseData } from '@/api/types';

/**
 * REQ-031 KI-Assistent — Wissens-Frage-Antwort-Seite.
 *
 * In beiden Modi verfuegbar: eine frei formulierte Wissensfrage geht ueber den
 * light-mode-faehigen `/public/ai/ask`-Pfad (kein Tenant-Kontext, §5.3) an die
 * Wissensbasis. Im Full-Modus zusaetzlich der kontextbewusste Chat-Drawer.
 */
export default function KIAssistentPage() {
  const { t, i18n } = useTranslation();
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<AiResponseData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chatOpen, setChatOpen] = useState(false);

  const language = i18n.language.startsWith('en') ? 'en' : 'de';

  const handleAsk = useCallback(async () => {
    const trimmed = question.trim();
    if (trimmed.length < 3 || loading) return;
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      const result = await aiApi.publicAsk(trimmed, language);
      setAnswer(result);
    } catch (err) {
      setError(resolveAiErrorMessage(err, t, t('pages.kiAssistent.error')));
    } finally {
      setLoading(false);
    }
  }, [question, loading, language, t]);

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
              disabled={loading || question.trim().length < 3}
              sx={{ minHeight: 48 }}
              data-testid="ki-ask-button"
            >
              {t('pages.kiAssistent.ask')}
            </Button>
          </Box>

          {!answer && !loading && !error && (
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
