import client, { tenantClient, getActiveTenantSlug } from '../client';
import { isLightMode } from '@/config/mode';
import type {
  AiConversationSummary,
  AiExplainRequest,
  AiResponse,
  AiTipCard,
  AiTipListResponse,
} from '../types';

/**
 * REQ-031 KI-Assistent API layer.
 *
 * Tenant-scoped calls go through the tenant client (`/t/{slug}/ai/...`); the
 * light-mode public knowledge question goes through the plain client
 * (`/public/ai/ask`, no auth, no tenant context — §5.3).
 */

const LIGHT_MODE_SLUG = 'mein-garten';

/** Context tip cards for a plant/run. Consent `ai_tenant_data_access`. */
export async function getTips(
  contextType: string,
  contextKey: string,
  language = 'de',
): Promise<AiTipCard[]> {
  const { data } = await tenantClient.get<AiTipListResponse>('/ai/tips', {
    params: { context_type: contextType, context_key: contextKey, language },
  });
  return data.tips;
}

/** Force-regenerate the tips for a context. */
export async function refreshTips(
  contextType: string,
  contextKey: string,
  language = 'de',
): Promise<AiTipCard[]> {
  const { data } = await tenantClient.post<AiTipListResponse>('/ai/tips/refresh', null, {
    params: { context_type: contextType, context_key: contextKey, language },
  });
  return data.tips;
}

export async function dismissTip(tipKey: string): Promise<void> {
  await tenantClient.post(`/ai/tips/${tipKey}/dismiss`);
}

export async function markTipActedOn(tipKey: string): Promise<void> {
  await tenantClient.post(`/ai/tips/${tipKey}/acted-on`);
}

/** The single personalised daily tip for the dashboard (or `null`). */
export async function getDailyTip(language = 'de'): Promise<AiTipCard | null> {
  const { data } = await tenantClient.get<AiTipCard | null>('/ai/daily-tip', {
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

export async function listConversations(): Promise<AiConversationSummary[]> {
  const { data } = await tenantClient.get<AiConversationSummary[]>('/ai/conversations');
  return data;
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
  if (!response.ok || !response.body) {
    throw new Error(`chat_stream_failed_${response.status}`);
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

/** Light-mode public knowledge question — no auth, no tenant context (§5.3). */
export async function publicAsk(question: string, language: 'de' | 'en' = 'de'): Promise<AiResponse> {
  const { data } = await client.post<AiResponse>('/public/ai/ask', { question, language });
  return data;
}
