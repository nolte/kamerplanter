import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { server } from '@/test/mocks/server';
import { renderWithProviders } from '@/test/helpers';
import KIAssistentPage from '@/pages/ki-assistent/KIAssistentPage';

/**
 * REQ-031 / #2175 — the KI page asks through the route its mode provides: the
 * Light mode `/public/ai/ask`, the Full mode `/t/{slug}/ai/knowledge/ask`, which
 * is admitted by consent, garden switch and budget. A missing
 * `ai_knowledge_question` consent is offered in place and the question re-sent.
 */

const modeMock = vi.hoisted(() => ({ isLightMode: false, isFullMode: true }));
vi.mock('@/config/mode', () => ({
  get isLightMode() {
    return modeMock.isLightMode;
  },
  get isFullMode() {
    return modeMock.isFullMode;
  },
  KAMERPLANTER_MODE: 'full',
}));

// The chat drawer is not under test here and opens no conversation while closed.
vi.mock('@/components/ai/AiChatDrawer', () => ({ default: () => null }));

const TENANT_ANSWER = {
  answer: 'VPD ist das Dampfdruckdefizit.',
  question_type: 'factual',
  model: 'llama3',
  usage: { prompt_tokens: 10, completion_tokens: 5 },
  sources: [
    {
      source_key: 'kb-vpd',
      source_type: 'knowledge_guide',
      title: 'VPD-Grundlagen',
      content: '…',
      score: 0.91,
      metadata: {},
      language: 'de',
    },
  ],
};

const PUBLIC_ANSWER = {
  answer_text: 'Light-Antwort zu VPD.',
  sources: [],
  language: 'de',
  language_mismatch_warning: false,
  uses_tenant_data: false,
  uses_cloud_provider: false,
  confidence: 'high',
  model_name: 'llama3',
  provider_type: 'ollama',
};

function apiError(status: number, errorCode: string, message: string, details: unknown[] = []) {
  return HttpResponse.json(
    {
      error_id: 'e-1',
      error_code: errorCode,
      message,
      details,
      timestamp: '',
      path: '',
      method: '',
    },
    { status },
  );
}

const consentRequired = () =>
  apiError(
    403,
    'CONSENT_REQUIRED',
    "Consent for 'ai_knowledge_question' is required for this action.",
    [
      {
        field: 'consent',
        reason: "Grant consent for 'ai_knowledge_question' to use this feature.",
        code: 'CONSENT_REQUIRED',
      },
    ],
  );

async function ask(user: ReturnType<typeof userEvent.setup>, question = 'Was ist VPD?') {
  // The availability probe resolves first; asking before it would race the re-render.
  await waitFor(() => expect(screen.getByTestId('ki-ask-button')).toBeInTheDocument());
  await user.type(screen.getByLabelText('Deine Frage'), question);
  await user.click(screen.getByTestId('ki-ask-button'));
}

describe('KIAssistentPage', () => {
  let publicCalls: number;
  let tenantBodies: unknown[];
  let tenantSlugs: string[];

  beforeEach(() => {
    i18n.changeLanguage('de');
    modeMock.isLightMode = false;
    modeMock.isFullMode = true;
    publicCalls = 0;
    tenantBodies = [];
    tenantSlugs = [];
    server.use(
      http.get('/api/v1/ai/status', () => HttpResponse.json({ available: true })),
      http.post('/api/v1/public/ai/ask', () => {
        publicCalls += 1;
        return HttpResponse.json(PUBLIC_ANSWER);
      }),
      http.post('/api/v1/t/:tenant/ai/knowledge/ask', async ({ request, params }) => {
        tenantSlugs.push(String(params.tenant));
        tenantBodies.push(await request.json());
        return HttpResponse.json(TENANT_ANSWER);
      }),
    );
  });

  describe('route per mode', () => {
    it('asks the tenant route in the Full mode and never /public/ai', async () => {
      const user = userEvent.setup();
      renderWithProviders(<KIAssistentPage />);

      await ask(user);

      expect(await screen.findByText('VPD ist das Dampfdruckdefizit.')).toBeInTheDocument();
      expect(publicCalls).toBe(0);
      expect(tenantSlugs).toEqual(['test-tenant']);
      // No plant context: the question alone, so only `ai_knowledge_question` applies.
      expect(tenantBodies).toEqual([
        { question: 'Was ist VPD?', doc_language: 'all', prompt_language: 'de' },
      ]);
      // The chunks are rendered as the answer's sources.
      expect(screen.getByTestId('ai-sources')).toHaveTextContent('1');
      expect(screen.queryByTestId('ai-tenant-data-indicator')).toBeNull();
    });

    it('asks /public/ai/ask in the Light mode and never the tenant route', async () => {
      modeMock.isLightMode = true;
      modeMock.isFullMode = false;
      const user = userEvent.setup();
      renderWithProviders(<KIAssistentPage />);

      await ask(user);

      expect(await screen.findByText('Light-Antwort zu VPD.')).toBeInTheDocument();
      expect(publicCalls).toBe(1);
      expect(tenantBodies).toHaveLength(0);
    });
  });

  describe('consent gate', () => {
    it('offers the consent in place on CONSENT_REQUIRED and re-sends after granting', async () => {
      const granted: unknown[] = [];
      let attempts = 0;
      server.use(
        http.post('/api/v1/t/:tenant/ai/knowledge/ask', () => {
          attempts += 1;
          return attempts === 1 ? consentRequired() : HttpResponse.json(TENANT_ANSWER);
        }),
        http.post('/api/v1/privacy/consents', async ({ request }) => {
          granted.push(await request.json());
          return HttpResponse.json(
            { purpose: 'ai_knowledge_question', granted: true },
            { status: 201 },
          );
        }),
      );
      const user = userEvent.setup();
      renderWithProviders(<KIAssistentPage />);

      await ask(user);

      const gate = await screen.findByTestId('ki-consent-gate');
      expect(gate).toHaveTextContent(/Wissensbasis/);
      expect(screen.getByRole('link', { name: 'Datenschutz-Einstellungen' })).toHaveAttribute(
        'href',
        '/privacy',
      );
      expect(screen.queryByTestId('ki-ask-error')).toBeNull();

      await user.click(screen.getByTestId('ki-consent-accept'));

      expect(await screen.findByText('VPD ist das Dampfdruckdefizit.')).toBeInTheDocument();
      expect(granted).toEqual([{ purpose: 'ai_knowledge_question' }]);
      expect(attempts).toBe(2);
      expect(screen.queryByTestId('ki-consent-gate')).toBeNull();
    });

    it('keeps the gate open with an error when granting fails, without re-sending', async () => {
      let attempts = 0;
      server.use(
        http.post('/api/v1/t/:tenant/ai/knowledge/ask', () => {
          attempts += 1;
          return consentRequired();
        }),
        http.post('/api/v1/privacy/consents', () => apiError(500, 'INTERNAL', 'boom')),
      );
      const user = userEvent.setup();
      renderWithProviders(<KIAssistentPage />);

      await ask(user);
      await user.click(await screen.findByTestId('ki-consent-accept'));

      expect(await screen.findByTestId('ki-consent-error')).toHaveTextContent(
        'Deine Einwilligung konnte nicht gespeichert werden.',
      );
      expect(screen.getByTestId('ki-consent-gate')).toBeInTheDocument();
      expect(attempts).toBe(1);
    });

    it('does not reopen the gate when the question is refused again after the grant', async () => {
      server.use(
        http.post('/api/v1/t/:tenant/ai/knowledge/ask', () => consentRequired()),
        http.post('/api/v1/privacy/consents', () =>
          HttpResponse.json({ purpose: 'ai_knowledge_question', granted: true }, { status: 201 }),
        ),
      );
      const user = userEvent.setup();
      renderWithProviders(<KIAssistentPage />);

      await ask(user);
      await user.click(await screen.findByTestId('ki-consent-accept'));

      expect(await screen.findByTestId('ki-ask-error')).toHaveTextContent(/trotzdem abgelehnt/);
      expect(screen.queryByTestId('ki-consent-gate')).toBeNull();
    });

    it('does not offer a grant for a different purpose', async () => {
      server.use(
        http.post('/api/v1/t/:tenant/ai/knowledge/ask', () =>
          apiError(
            403,
            'CONSENT_REQUIRED',
            "Consent for 'ai_cloud_processing' is required for this action.",
          ),
        ),
      );
      const user = userEvent.setup();
      renderWithProviders(<KIAssistentPage />);

      await ask(user);

      expect(await screen.findByTestId('ki-ask-error')).toHaveTextContent(/Cloud-KI-Anbieter/);
      expect(screen.queryByTestId('ki-consent-gate')).toBeNull();
    });

    it('closes the gate on decline and says why there is no answer', async () => {
      server.use(http.post('/api/v1/t/:tenant/ai/knowledge/ask', () => consentRequired()));
      const user = userEvent.setup();
      renderWithProviders(<KIAssistentPage />);

      await ask(user);
      await user.click(await screen.findByTestId('ki-consent-decline'));

      expect(screen.queryByTestId('ki-consent-gate')).toBeNull();
      expect(screen.getByTestId('ki-ask-error')).toHaveTextContent(/Ohne deine Einwilligung/);
    });
  });

  describe('admission errors', () => {
    it('explains a used-up personal AI budget (429 AI_BUDGET_EXCEEDED)', async () => {
      server.use(
        http.post('/api/v1/t/:tenant/ai/knowledge/ask', () =>
          apiError(429, 'AI_BUDGET_EXCEEDED', 'budget', [
            { field: null, reason: 'x', code: 'user_calls' },
          ]),
        ),
      );
      const user = userEvent.setup();
      renderWithProviders(<KIAssistentPage />);

      await ask(user);

      expect(await screen.findByTestId('ki-ask-error')).toHaveTextContent(/Tageskontingent/);
    });

    it('explains a garden with AI switched off (403 AI_DISABLED_FOR_TENANT)', async () => {
      server.use(
        http.post('/api/v1/t/:tenant/ai/knowledge/ask', () =>
          apiError(403, 'AI_DISABLED_FOR_TENANT', 'ai.disabled_for_tenant'),
        ),
      );
      const user = userEvent.setup();
      renderWithProviders(<KIAssistentPage />);

      await ask(user);

      const error = await screen.findByTestId('ki-ask-error');
      expect(error).toHaveTextContent(i18n.t('ai.errors.disabled'));
      expect(screen.queryByTestId('ki-consent-gate')).toBeNull();
    });

    it('falls back to the generic message for an unreachable knowledge service (502)', async () => {
      server.use(
        http.post('/api/v1/t/:tenant/ai/knowledge/ask', () =>
          apiError(502, 'EXTERNAL_SOURCE_ERROR', 'knowledge-service unavailable'),
        ),
      );
      const user = userEvent.setup();
      renderWithProviders(<KIAssistentPage />);

      await ask(user);

      await waitFor(() =>
        expect(screen.getByTestId('ki-ask-error')).toHaveTextContent(
          i18n.t('pages.kiAssistent.error'),
        ),
      );
    });
  });
});
