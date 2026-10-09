import client, { tenantClient, getActiveTenantSlug } from '../client';
import { fetchAllPages } from '../paginate';
import { ApiError } from '../errors';
import { isLightMode } from '@/config/mode';
import type {
  AiConfidence,
  AiConversationSummary,
  AiExplainRequest,
  AiResponse,
  AiSourceRef,
  AiStatus,
  AiTipCard,
  AiTipListResponse,
  ApiErrorResponse,
  KnowledgeAskRequest,
  KnowledgeAskResponse,
} from '../types';

/**
 * REQ-031 KI-Assistent API layer.
 *
 * Tenant-scoped calls go through the tenant client (`/t/{slug}/ai/...`); the
 * Light-mode knowledge question goes through the plain client
 * (`/public/ai/ask`, Light system user, no tenant context — §5.3). The Full
 * mode asks `/t/{slug}/ai/knowledge/ask` (#2175).
 */

const LIGHT_MODE_SLUG = 'mein-garten';

/**
 * Stored context tip cards for a plant/run. Consent `ai_tenant_data_access`.
 *
 * A read: since #1461 it never generates, so an empty `tips` is a normal answer
 * meaning "nothing generated for this context yet". The whole response is
 * returned rather than just the array, because `refresh_available` is what tells
 * the caller whether they may do something about that.
 */
export async function getTips(
  contextType: string,
  contextKey: string,
): Promise<AiTipListResponse> {
  const { data } = await tenantClient.get<AiTipListResponse>('/ai/tips', {
    params: { context_type: contextType, context_key: contextKey },
  });
  return data;
}

/** Generate (or regenerate) the tips for a context. Requires grower. */
export async function refreshTips(
  contextType: string,
  contextKey: string,
  language = 'de',
): Promise<AiTipListResponse> {
  const { data } = await tenantClient.post<AiTipListResponse>('/ai/tips/refresh', null, {
    params: { context_type: contextType, context_key: contextKey, language },
  });
  return data;
}

export async function dismissTip(tipKey: string): Promise<void> {
  await tenantClient.post(`/ai/tips/${tipKey}/dismiss`);
}

export async function markTipActedOn(tipKey: string): Promise<void> {
  await tenantClient.post(`/ai/tips/${tipKey}/acted-on`);
}

/**
 * Today's stored daily tip for the dashboard, or `null`.
 *
 * A read: since #1461 it never generates, so `null` also covers "nothing
 * generated for today yet" — `refreshDailyTip` is what generates it.
 */
export async function getDailyTip(): Promise<AiTipCard | null> {
  const { data } = await tenantClient.get<AiTipCard | null>('/ai/daily-tip');
  return data;
}

/** Generate today's daily tip. Requires grower; idempotent for the day. */
export async function refreshDailyTip(language = 'de'): Promise<AiTipCard | null> {
  const { data } = await tenantClient.post<AiTipCard | null>('/ai/daily-tip/refresh', null, {
    params: { language },
  });
  return data;
}

export async function dismissDailyTip(): Promise<void> {
  await tenantClient.post('/ai/daily-tip/dismiss');
}

/** A "why?" explanation for a concrete recommendation. */
export async function explain(body: AiExplainRequest): Promise<AiResponse> {
  const { data } = await tenantClient.post<AiResponse>('/ai/explain', body);
  return data;
}

/**
 * Every conversation of the caller, most recent first. The route returns one bounded page since MT-035 (#2131); every page is read so
 * the list this feeds stays complete.
 */
export async function listConversations(): Promise<AiConversationSummary[]> {
  return fetchAllPages(async (offset, limit) => {
    const { data } = await tenantClient.get<AiConversationSummary[]>('/ai/conversations', {
      params: { offset, limit },
    });
    return data;
  });
}

export async function createConversation(
  contextType: 'plant_instance' | 'planting_run' | 'general' = 'general',
  contextKey?: string,
  language: 'de' | 'en' = 'de',
): Promise<AiConversationSummary> {
  const { data } = await tenantClient.post<AiConversationSummary>('/ai/conversations', {
    context_type: contextType,
    context_key: contextKey ?? null,
    language,
  });
  return data;
}

export async function deleteConversation(key: string): Promise<void> {
  await tenantClient.delete(`/ai/conversations/${key}`);
}

/** A single Server-Sent-Event frame parsed from the chat stream. */
export interface AiChatEvent {
  event: 'token' | 'done' | 'error';
  data: string;
}

/**
 * A chat request the backend refused without the JSON error envelope (e.g. the
 * per-minute rate limit, a proxy error page). Carries the HTTP status so the
 * caller can still tell a 429 apart.
 */
export class ChatStreamError extends Error {
  readonly statusCode: number;

  constructor(statusCode: number) {
    super(`chat_stream_failed_${statusCode}`);
    this.name = 'ChatStreamError';
    this.statusCode = statusCode;
  }
}

/**
 * The error of a refused chat request. The backend refuses before the stream
 * starts (consent, AI budget — #2110), with the same JSON envelope the axios
 * client turns into an {@link ApiError}; `fetch` does not, so it is done here.
 */
async function chatStreamError(response: Response): Promise<Error> {
  try {
    const body: unknown = await response.json();
    if (
      typeof body === 'object' &&
      body !== null &&
      'error_id' in body &&
      'error_code' in body
    ) {
      return new ApiError(body as ApiErrorResponse, response.status);
    }
  } catch {
    // Not JSON — fall through to the status-only error.
  }
  return new ChatStreamError(response.status);
}

/**
 * Send a chat message and consume the SSE stream token-by-token (§5.4).
 *
 * Uses `fetch` with a streaming reader rather than axios, because axios does not
 * expose an incremental body reader in the browser. The tenant prefix is added
 * here explicitly (the axios tenant interceptor does not apply to `fetch`).
 */
export async function streamChatMessage(
  conversationKey: string,
  message: string,
  onEvent: (event: AiChatEvent) => void,
  language: 'de' | 'en' = 'de',
  signal?: AbortSignal,
): Promise<void> {
  const slug = isLightMode ? LIGHT_MODE_SLUG : getActiveTenantSlug();
  const url = `/api/v1/t/${slug}/ai/conversations/${conversationKey}/messages`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ message, language }),
    signal,
  });
  if (!response.ok) {
    throw await chatStreamError(response);
  }
  if (!response.body) {
    throw new ChatStreamError(response.status);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  // SSE frames are separated by a blank line; parse `event:`/`data:` per frame.
  const flush = (frame: string) => {
    let eventName: AiChatEvent['event'] = 'token';
    let data = '';
    for (const line of frame.split('\n')) {
      if (line.startsWith('event:')) eventName = line.slice(6).trim() as AiChatEvent['event'];
      else if (line.startsWith('data:')) data += line.slice(5).replace(/^ /, '');
    }
    if (data.length > 0 || eventName !== 'token') onEvent({ event: eventName, data });
  };

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let sep = buffer.indexOf('\n\n');
    while (sep !== -1) {
      flush(buffer.slice(0, sep));
      buffer = buffer.slice(sep + 2);
      sep = buffer.indexOf('\n\n');
    }
  }
  if (buffer.trim().length > 0) flush(buffer);
}

/**
 * Light-mode knowledge question — no tenant context (§5.3).
 *
 * The route is mounted in the Light mode only and is authenticated as the
 * Light system user there; the Full mode has no `/public/ai/*` (#2175) and asks
 * through {@link askTenantKnowledge} instead.
 */
export async function publicAsk(question: string, language: 'de' | 'en' = 'de'): Promise<AiResponse> {
  const { data } = await client.post<AiResponse>('/public/ai/ask', { question, language });
  return data;
}

/**
 * Full-mode knowledge question — `POST /t/{slug}/ai/knowledge/ask` (#2175).
 *
 * Admitted like every generating AI route: rank grower, the garden's AI switch,
 * the consent `ai_knowledge_question` (plus `ai_tenant_data_access` when
 * `context` is set) and the daily AI budget.
 */
export async function askTenantKnowledge(body: KnowledgeAskRequest): Promise<KnowledgeAskResponse> {
  const { data } = await tenantClient.post<KnowledgeAskResponse>('/ai/knowledge/ask', body);
  return data;
}

/**
 * What the KI page renders for an answer of either route.
 *
 * Narrower than {@link AiResponse} on purpose: the tenant route answers no
 * confidence, and inventing it would put a claim on the `<AIResponse>` badges
 * that nothing measured. Its provider type and cloud flag are passed through
 * when the server sends them (older servers do not). Absent fields fall back to
 * the component's defaults.
 */
export interface KnowledgeAnswer {
  answer_text: string;
  sources: AiSourceRef[];
  model_name: string;
  provider_type?: string;
  uses_tenant_data: boolean;
  uses_cloud_provider?: boolean;
  confidence?: AiConfidence;
  language_mismatch_warning?: boolean;
}

/**
 * Ask a free-form knowledge question through the route the mode provides.
 *
 * The single place the KI page's route is chosen: the Light mode asks
 * `/public/ai/ask`, the Full mode the tenant route — the public one does not
 * exist there. No plant context is sent, so the answer never uses tenant data.
 */
export async function askKnowledgeQuestion(
  question: string,
  language: 'de' | 'en' = 'de',
): Promise<KnowledgeAnswer> {
  if (isLightMode) {
    return publicAsk(question, language);
  }
  const data = await askTenantKnowledge({
    question,
    doc_language: 'all',
    prompt_language: language,
  });
  return {
    answer_text: data.answer,
    sources: data.sources.map((chunk) => ({
      source_key: chunk.source_key,
      source_type: chunk.source_type,
      title: chunk.title,
      score: chunk.score,
      language: chunk.language,
    })),
    model_name: data.model,
    provider_type: data.provider_type ?? undefined,
    uses_tenant_data: false,
    uses_cloud_provider: data.uses_cloud_provider ?? undefined,
  };
}

/**
 * GET /ai/status — public availability probe (issue #685).
 *
 * Reports whether AI features are enabled cluster-wide so the frontend can hide
 * the KI-Assistent nav entry and degrade its page. No auth/tenant context.
 */
export async function getAiStatus(): Promise<AiStatus> {
  const { data } = await client.get<AiStatus>('/ai/status');
  return data;
}
