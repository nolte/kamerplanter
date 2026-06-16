import { describe, it, expect } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';
import { listConsents, grantConsent, revokeConsent } from '@/api/endpoints/privacy';

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
});
