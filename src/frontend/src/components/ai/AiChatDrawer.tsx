import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Drawer from '@mui/material/Drawer';
import Box from '@mui/material/Box';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import SendIcon from '@mui/icons-material/Send';
import AIResponse from './AIResponse';
import { aiApi } from '@/api';
import type { AiConversationSummary, AiResponse as AiResponseData } from '@/api/types';

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
 */
export default function AiChatDrawer({
  open,
  onClose,
  contextType = 'general',
  contextKey,
}: AiChatDrawerProps) {
  const { t, i18n } = useTranslation();
  const [conversation, setConversation] = useState<AiConversationSummary | null>(null);
  const [bubbles, setBubbles] = useState<ChatBubble[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const language = i18n.language.startsWith('en') ? 'en' : 'de';

  useEffect(() => {
    if (!open || conversation) return;
    let active = true;
    aiApi
      .createConversation(contextType, contextKey, language)
      .then((created) => {
        if (active) setConversation(created);
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [open, conversation, contextType, contextKey, language]);

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
    } catch {
      setBubbles((prev) => {
        const next = [...prev];
        const last = next[next.length - 1];
        if (last && last.role === 'assistant' && last.text === '') {
          next[next.length - 1] = { ...last, text: t('ai.chat.error') };
        }
        return next;
      });
    } finally {
      setStreaming(false);
    }
  }, [input, conversation, streaming, language, t]);

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

        <Stack spacing={1.5} sx={{ flex: 1, overflowY: 'auto', mb: 2 }}>
          {bubbles.length === 0 && (
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
          <IconButton
            color="primary"
            onClick={() => void handleSend()}
            disabled={streaming || !input.trim() || !conversation}
            aria-label={t('ai.chat.send')}
            data-testid="ai-chat-send"
          >
            <SendIcon />
          </IconButton>
        </Stack>
      </Box>
    </Drawer>
  );
}
