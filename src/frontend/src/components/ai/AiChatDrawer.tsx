import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Drawer from '@mui/material/Drawer';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Alert from '@mui/material/Alert';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import SendIcon from '@mui/icons-material/Send';
import StopIcon from '@mui/icons-material/Stop';
import AIResponse from './AIResponse';
import { resolveAiErrorMessage } from './aiErrorMessage';
import { aiApi } from '@/api';
import type { AiConversationSummary, AiResponse as AiResponseData } from '@/api/types';

// UI-NFR-001 R-011: 48x48 touch target on mobile/tablet for the send/cancel
// icon button; R-013 allows the desktop reduction to a compact 32px.
const TOUCH_TARGET_SX = { minWidth: { xs: 48, sm: 32 }, minHeight: { xs: 48, sm: 32 } } as const;

export interface AiChatDrawerProps {
  open: boolean;
  onClose: () => void;
  /** Optional plant/run context to seed a context-aware conversation. */
  contextType?: 'plant_instance' | 'planting_run' | 'general';
  contextKey?: string;
}

interface ChatBubble {
  role: 'user' | 'assistant';
  text: string;
  meta?: AiResponseData;
}

/**
 * REQ-031 §6.5 — kontextbewusster Chat-Drawer mit SSE-Streaming.
 *
 * Startet lazy eine Konversation, streamt Antworten Token-fuer-Token und rendert
 * Assistant-Bubbles durch die `<AIResponse>`-Huelle. Online-only (UI-NFR-012).
 * Ein Fehlschlag beim Konversationsaufbau (KI deaktiviert / Consent fehlt)
 * wird als Alert mit Retry-Aktion angezeigt statt das Eingabefeld stumm
 * dauerhaft zu deaktivieren. Waehrend des Streamings ersetzt ein
 * Abbrechen-Button den Senden-Button.
 */
export default function AiChatDrawer({
  open,
  onClose,
  contextType = 'general',
  contextKey,
}: AiChatDrawerProps) {
  const { t, i18n } = useTranslation();
  const [conversation, setConversation] = useState<AiConversationSummary | null>(null);
  const [initError, setInitError] = useState<string | null>(null);
  const [initPending, setInitPending] = useState(false);
  const [bubbles, setBubbles] = useState<ChatBubble[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const language = i18n.language.startsWith('en') ? 'en' : 'de';

  // Bumped by the "retry" button in the init-error state so the conversation
  // can be (re-)created without closing and reopening the drawer.
  const [initRetryToken, setInitRetryToken] = useState(0);
  const retryInit = useCallback(() => setInitRetryToken((n) => n + 1), []);

  useEffect(() => {
    if (!open || conversation) return;
    let active = true;
    setInitPending(true);
    setInitError(null);
    aiApi
      .createConversation(contextType, contextKey, language)
      .then((created) => {
        if (active) setConversation(created);
      })
      .catch((err) => {
        // A silently-swallowed failure here would leave the input disabled
        // forever with no explanation (dead end) — surface it instead, with a
        // retry action, distinguishing "KI disabled"/"consent missing" from a
        // generic failure.
        if (active) setInitError(resolveAiErrorMessage(err, t, t('ai.chat.error')));
      })
      .finally(() => {
        if (active) setInitPending(false);
      });
    return () => {
      active = false;
    };
    // contextType/contextKey/language are stable inputs to this drawer
    // instance; re-run only on open, a successful reset (`conversation`
    // cleared) or an explicit retry.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, conversation, initRetryToken]);

  useEffect(
    () => () => {
      abortRef.current?.abort();
    },
    [],
  );

  const handleSend = useCallback(async () => {
    const message = input.trim();
    if (!message || !conversation?.key || streaming) return;
    setInput('');
    setBubbles((prev) => [...prev, { role: 'user', text: message }, { role: 'assistant', text: '' }]);
    setStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await aiApi.streamChatMessage(
        conversation.key,
        message,
        (event) => {
          if (event.event === 'token') {
            setBubbles((prev) => {
              const next = [...prev];
              const last = next[next.length - 1];
              if (last && last.role === 'assistant') next[next.length - 1] = { ...last, text: last.text + event.data };
              return next;
            });
          } else if (event.event === 'done') {
            try {
              const meta = JSON.parse(event.data) as AiResponseData;
              setBubbles((prev) => {
                const next = [...prev];
                const last = next[next.length - 1];
                if (last && last.role === 'assistant') {
                  next[next.length - 1] = { ...last, text: meta.answer_text, meta };
                }
                return next;
              });
            } catch {
              // Keep the streamed text if metadata parsing fails.
            }
          }
        },
        language,
        controller.signal,
      );
    } catch (err) {
      // A user-triggered abort (Stop button / drawer unmount) is not a
      // failure — only replace the placeholder with an error message when no
      // tokens arrived yet; a partially streamed answer is kept as-is either
      // way (REQ-031 §6.5 does not require discarding a partial answer).
      const aborted = err instanceof DOMException && err.name === 'AbortError';
      setBubbles((prev) => {
        const next = [...prev];
        const last = next[next.length - 1];
        if (last && last.role === 'assistant' && last.text === '') {
          next[next.length - 1] = {
            ...last,
            text: aborted ? t('ai.chat.aborted') : resolveAiErrorMessage(err, t, t('ai.chat.error')),
          };
        }
        return next;
      });
    } finally {
      setStreaming(false);
    }
  }, [input, conversation, streaming, language, t]);

  const handleCancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return (
    <Drawer anchor="right" open={open} onClose={onClose} data-testid="ai-chat-drawer">
      <Box
        sx={{ width: { xs: '100vw', sm: 420 }, height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}
        role="region"
        aria-label={t('ai.chat.title')}
      >
        <Typography variant="h6" gutterBottom>
          {t('ai.chat.title')}
        </Typography>

        {initError && (
          <Alert
            severity="warning"
            sx={{ mb: 2 }}
            data-testid="ai-chat-init-error"
            action={
              <Button color="inherit" size="small" onClick={retryInit} data-testid="ai-chat-init-retry">
                {t('ai.chat.retry')}
              </Button>
            }
          >
            {initError}
          </Alert>
        )}

        <Stack
          spacing={1.5}
          sx={{ flex: 1, overflowY: 'auto', mb: 2 }}
          aria-live="polite"
          aria-atomic="false"
        >
          {initPending && (
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }} data-testid="ai-chat-init-loading">
              <CircularProgress size={16} />
              <Typography variant="body2" color="text.secondary">
                {t('ai.chat.thinking')}
              </Typography>
            </Stack>
          )}
          {bubbles.length === 0 && !initPending && !initError && (
            <Typography variant="body2" color="text.secondary">
              {t('ai.chat.empty')}
            </Typography>
          )}
          {bubbles.map((bubble, index) =>
            bubble.role === 'user' ? (
              <Paper
                key={index}
                variant="outlined"
                sx={{ p: 1, alignSelf: 'flex-end', bgcolor: 'action.hover', maxWidth: '85%' }}
              >
                <Typography variant="body2">{bubble.text}</Typography>
              </Paper>
            ) : (
              <Paper key={index} variant="outlined" sx={{ p: 1, maxWidth: '95%' }}>
                {bubble.meta ? (
                  <AIResponse
                    sources={bubble.meta.sources}
                    modelName={bubble.meta.model_name}
                    providerType={bubble.meta.provider_type}
                    usesTenantData={bubble.meta.uses_tenant_data}
                    usesCloudProvider={bubble.meta.uses_cloud_provider}
                    confidence={bubble.meta.confidence}
                    languageMismatchWarning={bubble.meta.language_mismatch_warning}
                  >
                    <Typography variant="body2">{bubble.text}</Typography>
                  </AIResponse>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    {bubble.text || t('ai.chat.thinking')}
                  </Typography>
                )}
              </Paper>
            ),
          )}
        </Stack>

        <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-end' }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            size="small"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                void handleSend();
              }
            }}
            placeholder={t('ai.chat.placeholder')}
            label={t('ai.chat.inputLabel')}
            disabled={streaming || !conversation}
            data-testid="ai-chat-input"
          />
          {streaming ? (
            <IconButton
              color="error"
              onClick={handleCancel}
              aria-label={t('ai.chat.cancel')}
              data-testid="ai-chat-cancel"
              sx={TOUCH_TARGET_SX}
            >
              <StopIcon />
            </IconButton>
          ) : (
            <IconButton
              color="primary"
              onClick={() => void handleSend()}
              disabled={!input.trim() || !conversation}
              aria-label={t('ai.chat.send')}
              data-testid="ai-chat-send"
              sx={TOUCH_TARGET_SX}
            >
              <SendIcon />
            </IconButton>
          )}
        </Stack>
      </Box>
    </Drawer>
  );
}
