import { describe, it, expect, afterEach, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import client, { ACCEPT_LANGUAGE_HEADER, requestLanguage, tenantClient } from '@/api/client';
import { server } from '../mocks/server';

/**
 * #2902 — the UI language travels as `Accept-Language` on every API request.
 *
 * The backend words some answers itself (species names of the care dashboard, the
 * plant grid, the sowing calendar, the bed plan, …) and resolves the language from this
 * header (`app/common/locale.py: get_request_locale`). The browser's own header is the
 * browser's preference, not the language picked in the app, so the client sets it from
 * `i18n` — read per request, so a language switch is followed by the next request.
 */
describe('API clients: Accept-Language', () => {
  let seen: string[] = [];

  beforeEach(async () => {
    seen = [];
    await i18n.changeLanguage('de');
    const record = ({ request }: { request: Request }) => {
      seen.push(request.headers.get(ACCEPT_LANGUAGE_HEADER) ?? '<none>');
      return HttpResponse.json({ ok: true });
    };
    server.use(
      http.get('/api/v1/language-probe', record),
      http.post('/api/v1/language-probe', record),
      http.get('/api/v1/t/test-tenant/language-probe', record),
    );
  });

  afterEach(async () => {
    await i18n.changeLanguage('de');
  });

  it('names the standard header the backend reads', () => {
    expect(ACCEPT_LANGUAGE_HEADER).toBe('Accept-Language');
  });

  it('sends the UI language on the global and the tenant client', async () => {
    await client.get('/language-probe');
    await client.post('/language-probe', { x: 1 });
    await tenantClient.get('/language-probe');

    expect(seen).toEqual(['de', 'de', 'de']);
  });

  it('follows a language switch on the very next request', async () => {
    await tenantClient.get('/language-probe');
    await i18n.changeLanguage('en');
    await tenantClient.get('/language-probe');
    await client.get('/language-probe');
    await i18n.changeLanguage('de');
    await tenantClient.get('/language-probe');

    expect(seen).toEqual(['de', 'en', 'en', 'de']);
  });

  it('sends the resolved language, not a regional tag the backend would have to reduce', async () => {
    // German on purpose: jsdom's XHR sends an English `Accept-Language` of its own, so only a
    // non-English expectation proves the header is the client's.
    await i18n.changeLanguage('de-AT');

    expect(requestLanguage()).toBe('de');
    await client.get('/language-probe');
    expect(seen).toEqual(['de']);
  });
});
