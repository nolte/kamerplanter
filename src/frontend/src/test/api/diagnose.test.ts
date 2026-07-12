import { describe, it, expect, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { setActiveTenantSlug } from '@/api/client';
import * as api from '@/api/endpoints/diagnose';

const T = '/api/v1/t/:tenant/diagnosis';

describe('diagnose api endpoints', () => {
  beforeEach(() => {
    setActiveTenantSlug('test-tenant');
  });

  it('listSymptoms returns the catalogue and forwards the language param', async () => {
    let receivedLanguage: string | null = null;
    server.use(
      http.get(`${T}/symptoms`, ({ request }) => {
        receivedLanguage = new URL(request.url).searchParams.get('language');
        return HttpResponse.json({
          symptoms: [
            {
              slug: 'leaf_spots',
              category: 'leaf_shape_change',
              label: 'Spots on the leaves',
              common_causes_hint: 'Fungal.',
              applicable_phases: ['vegetative'],
            },
          ],
        });
      }),
    );

    const symptoms = await api.listSymptoms('en');
    expect(symptoms).toHaveLength(1);
    expect(symptoms[0].slug).toBe('leaf_spots');
    expect(receivedLanguage).toBe('en');
  });

  it('analyzeDiagnosis posts the request body and returns the result', async () => {
    let body: unknown = null;
    server.use(
      http.post(`${T}/analyze`, async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({
          candidates: [{ rank: 1, name: 'Spider mites', confidence: 0.8, confidence_level: 'high' }],
          answer_summary: 'x',
          sources: [],
          language: 'de',
          uses_tenant_data: true,
          uses_cloud_provider: false,
          confidence: 'high',
          model_name: 'gemma3:12b',
          provider_type: 'ollama',
          status: 'ok',
        });
      }),
    );

    const result = await api.analyzeDiagnosis({ symptom_slugs: ['webbing_on_leaves'], language: 'de' });
    expect(result.status).toBe('ok');
    expect(result.candidates[0].name).toBe('Spider mites');
    expect(body).toMatchObject({ symptom_slugs: ['webbing_on_leaves'], language: 'de' });
  });
});
