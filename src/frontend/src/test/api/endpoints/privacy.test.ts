import { describe, it, expect } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import {
  listConsents,
  grantConsent,
  revokeConsent,
  requestEmailChange,
  confirmEmailChange,
  revertEmailChange,
} from '@/api/endpoints/privacy';

/**
 * REQ-025 — privacy/consent self-service endpoint client tests.
 *
 * Verifies the three consent calls the plant-identification gate (REQ-029) relies
 * on map to the right HTTP verbs and paths and unwrap the response body.
 */

const RECORD = {
  purpose: 'plant_identification',
  label: 'Plant identification',
  description: '',
  legal_basis: 'consent',
  required: false,
  granted: true,
  granted_at: '2026-06-15T00:00:00Z',
  revoked_at: null,
};

describe('privacy endpoints', () => {
  it('lists all consent records', async () => {
    server.use(http.get('/api/v1/privacy/consents', () => HttpResponse.json([RECORD])));
    const result = await listConsents();
    expect(result).toHaveLength(1);
    expect(result[0].purpose).toBe('plant_identification');
  });

  it('grants consent for a purpose', async () => {
    let body: unknown = null;
    server.use(
      http.post('/api/v1/privacy/consents', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json(RECORD, { status: 201 });
      }),
    );
    const result = await grantConsent('plant_identification');
    expect(body).toEqual({ purpose: 'plant_identification' });
    expect(result.granted).toBe(true);
  });

  it('revokes consent for a purpose', async () => {
    let revokedPurpose: string | undefined;
    server.use(
      http.delete('/api/v1/privacy/consents/:purpose', ({ params }) => {
        revokedPurpose = params.purpose as string;
        return HttpResponse.json({ ...RECORD, granted: false, revoked_at: '2026-06-16T00:00:00Z' });
      }),
    );
    const result = await revokeConsent('plant_identification');
    expect(revokedPurpose).toBe('plant_identification');
    expect(result.granted).toBe(false);
  });

  it('requests an e-mail change with the step-up fields as given (#1848)', async () => {
    let body: unknown = null;
    server.use(
      http.post('/api/v1/privacy/email-change', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json(
          {
            key: 'ec-1',
            new_email: 'new@example.org',
            status: 'pending',
            requested_at: null,
            expires_at: '2026-09-27T00:00:00Z',
          },
          { status: 201 },
        );
      }),
    );
    const result = await requestEmailChange({ new_email: 'new@example.org', step_up_token: 'tkn' });
    expect(body).toEqual({ new_email: 'new@example.org', step_up_token: 'tkn' });
    expect(result.status).toBe('pending');
  });

  it('posts the token to the confirm and revert routes (#1848)', async () => {
    const seen: Array<{ path: string; body: unknown }> = [];
    server.use(
      http.post('/api/v1/privacy/email-change/confirm', async ({ request }) => {
        seen.push({ path: 'confirm', body: await request.json() });
        return HttpResponse.json({ message: 'updated' });
      }),
      http.post('/api/v1/privacy/email-change/revert', async ({ request }) => {
        seen.push({ path: 'revert', body: await request.json() });
        return HttpResponse.json({ message: 'restored' });
      }),
    );
    expect((await confirmEmailChange('c-tok')).message).toBe('updated');
    expect((await revertEmailChange('r-tok')).message).toBe('restored');
    expect(seen).toEqual([
      { path: 'confirm', body: { token: 'c-tok' } },
      { path: 'revert', body: { token: 'r-tok' } },
    ]);
  });
});
